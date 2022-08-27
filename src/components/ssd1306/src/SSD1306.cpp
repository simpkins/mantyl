// Copyright (c) 2022, Adam Simpkins
#include "SSD1306.h"

#include "mantyl_literals.h"
#include "font.h"

#include <driver/gpio.h>
#include <esp_check.h>
#include <string.h>

namespace {
const char *LogTag = "mantyl.ssd1306";
} // namespace

namespace mantyl {

SSD1306::SSD1306(I2cMaster &bus, uint8_t addr, gpio_num_t reset_pin)
    : SSD1306{I2cDevice{bus, addr}, reset_pin} {}
SSD1306::SSD1306(I2cDevice &&device, gpio_num_t reset_pin)
    : dev_{std::move(device)},
      reset_pin_{reset_pin},
      buffer_{new uint8_t[buffer_size()]} {
  memset(buffer_.get(), 0x00, buffer_size());
}

SSD1306::~SSD1306() {
  if (reset_pin_ >= 0) {
    gpio_reset_pin(reset_pin_);
  }
}

esp_err_t SSD1306::init() {
  // Settings for an Adafruit 128x32 display
  const bool external_vcc = false;
  const uint8_t com_pin_flags = 0x02;
  const uint8_t charge_pump = external_vcc ? 0x10_u8 : 0x14_u8;
  const uint8_t precharge = external_vcc ? 0x22_u8 : 0xf1_u8;

  esp_err_t rc;

  if (reset_pin_ >= 0) {
    gpio_config_t io_conf = {
        .pin_bit_mask = 1ULL << reset_pin_,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    rc = gpio_config(&io_conf);
    ESP_RETURN_ON_ERROR(rc, LogTag, "failed to configure SSD1306 reset pin");

    gpio_set_level(reset_pin_, 0);
    // Minimum reset low pulse width is 3us, according to the datasheet
    vTaskDelay(pdMS_TO_TICKS(1));
    gpio_set_level(reset_pin_, 1);
    vTaskDelay(pdMS_TO_TICKS(10));
  }

  rc = send_commands(Command::DisplayOff);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(0) error initializing SSD1306 %u", dev_.address());
  rc = send_commands(Command::SetDisplayClockDiv,
                     0x80_u8); // reset oscillator frequency and divide ratio
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(1) error initializing SSD1306 %u", dev_.address());

  rc = send_commands(Command::SetMultiplex, static_cast<uint8_t>(height_ - 1));
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(2) error initializing SSD1306 %u", dev_.address());

  rc = send_commands(Command::SetDisplayOffset,
                     0x0_u8,
                     static_cast<uint8_t>(Command::SetStartLine | 0x0));
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(3) error initializing SSD1306 %u", dev_.address());
  rc = send_commands(Command::ChargePump, charge_pump);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(4) error initializing SSD1306 %u", dev_.address());

  rc = send_commands(Command::SetMemoryMode,
                     0x00_u8, // horizontal addressing mode
                     static_cast<uint8_t>(Command::SegRemap | 0x1),
                     Command::ComScanDec);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(5) error initializing SSD1306 %u", dev_.address());

  rc = send_commands(Command::SetComPins,
                     com_pin_flags,
                     Command::SetContrast,
                     contrast_,
                     Command::SetPrecharge,
                     precharge);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(6) error initializing SSD1306 %u", dev_.address());

  rc = send_commands(Command::SetVComDeselect,
                     0x40_u8,
                     Command::DisplayAllOn_RAM,
                     Command::NormalDisplay,
                     Command::DeactivateScroll,
                     Command::DisplayOn);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(7) error initializing SSD1306 %u", dev_.address());

  initialized_ = true;
  return ESP_OK;
}

esp_err_t SSD1306::flush() {
  if (!initialized_) {
    return ESP_ERR_INVALID_STATE;
  }

  uint8_t const page_end = (height_ + 7) / 8;
  uint8_t const col_end = width_ - 1;
  auto rc = send_commands(Command::SetPageAddr,
                          0_u8,     // start
                          page_end, // end
                          Command::SetColumnAddr,
                          0_u8,     // start
                          col_end); // end
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "error setting mem address on SSD1306 %u", dev_.address());

  uint8_t cmd = 0x40;
  rc = dev_.bus().write2(dev_.address(),
                         &cmd,
                         sizeof(cmd),
                         buffer_.get(),
                         buffer_size(),
                         std::chrono::milliseconds(1000));
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "error writing draw buffer to SSD1306 %u", dev_.address());

  return ESP_OK;
}

SSD1306::WriteResult SSD1306::write_text(std::string_view str, OffsetRange range) {
  auto px_offset = range.first;
  bool first = true;
  size_t char_idx = 0;
  while (char_idx < str.size()) {
    const char c = str[char_idx];
    const auto &glyph = Font6x8::lookupGlyph(c);
    const size_t px_end = px_offset + glyph.width + (first ? 0 : 1);
    if (px_end >= range.second) {
      break;
    }
    ++char_idx;
    if (first) {
      first = false;
    } else {
      // Add space between characters
      buffer_[px_offset] = 0;
      ++px_offset;
    }
    memcpy(buffer_.get() + px_offset, glyph.data, glyph.width);
    px_offset += glyph.width;
  }

  return WriteResult{px_offset, char_idx};
}

bool SSD1306::write_centered(std::string_view str, OffsetRange range) {
  const size_t width = Font6x8::computeWidth(str);
  const size_t range_width = range.second - range.first;
  if (width == range_width) {
    write_text(str, range);
    return true;
  } else if (width > range_width) {
    const auto result = write_text(str, range);
    memset(buffer_.get() + result.px_end, 0, range.second - result.px_end);
    return false;
  } else {
    const size_t extra_start_offset = (range_width - width) / 2;
    memset(buffer_.get() + range.first, 0, extra_start_offset);
    const auto result =
        write_text(str, {range.first + extra_start_offset, range.second});
    memset(buffer_.get() + result.px_end, 0, range.second - result.px_end);
    return true;
  }
}

void SSD1306::clear() {
  memset(buffer_.get(), 0x00, buffer_size());
}

esp_err_t SSD1306::set_contrast(uint8_t contrast) {
  if (!initialized_) {
    return ESP_ERR_INVALID_STATE;
  }
  if (contrast == contrast_) {
    return ESP_OK;
  }
  contrast_ = contrast;

  return send_commands(Command::SetContrast, contrast_);
}

esp_err_t SSD1306::display_on() {
  if (!initialized_) {
    return ESP_ERR_INVALID_STATE;
  }
  return send_commands(Command::DisplayOn);
}

esp_err_t SSD1306::display_off() {
  if (!initialized_) {
    return ESP_ERR_INVALID_STATE;
  }
  return send_commands(Command::DisplayOff);
}

esp_err_t SSD1306::send_commands(const uint8_t *data, size_t n) {
  const uint8_t cmd_start = 0;
  return dev_.bus().write2(dev_.address(),
                           &cmd_start,
                           sizeof(cmd_start),
                           data,
                           n,
                           std::chrono::milliseconds(1000));
}

} // namespace mantyl
