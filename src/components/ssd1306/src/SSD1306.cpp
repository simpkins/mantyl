// Copyright (c) 2022, Adam Simpkins
#include "SSD1306.h"

#include "mantyl_literals.h"

#include <driver/gpio.h>
#include <esp_check.h>
#include <string.h>

namespace {
const char *LogTag = "mantyl.ssd1306";

struct font_char_info {
    uint8_t width;
    const uint8_t* data;
};

using Font = std::array<font_char_info, 256>;

const uint8_t font_data_A[] = {0x7e, 0x11, 0x11, 0x11, 0x7e};
const uint8_t font_data_B[] = {0x7f, 0x49, 0x49, 0x49, 0x36};
const uint8_t font_data_C[] = {0x3e, 0x41, 0x41, 0x41, 0x22};
const uint8_t font_data_D[] = {0x7f, 0x41, 0x41, 0x41, 0x3e};
const uint8_t font_data_E[] = {0x7f, 0x49, 0x49, 0x49, 0x49};
const uint8_t font_data_F[] = {0x7f, 0x09, 0x09, 0x09, 0x09};
const uint8_t font_data_G[] = {0x3e, 0x41, 0x49, 0x49, 0x7a};
const uint8_t font_data_H[] = {0x7f, 0x08, 0x08, 0x08, 0x7f};
const uint8_t font_data_I[] = {0x41, 0x41, 0x7f, 0x41, 0x41};
const uint8_t font_data_J[] = {0x30, 0x40, 0x40, 0x40, 0x3f};
const uint8_t font_data_K[] = {0x7f, 0x08, 0x14, 0x22, 0x41};
const uint8_t font_data_L[] = {0x7f, 0x40, 0x40, 0x40, 0x40};
const uint8_t font_data_M[] = {0x7f, 0x02, 0x04, 0x02, 0x7f};
const uint8_t font_data_N[] = {0x7f, 0x02, 0x04, 0x08, 0x7f};
const uint8_t font_data_O[] = {0x3e, 0x41, 0x41, 0x41, 0x3e};
const uint8_t font_data_P[] = {0x7f, 0x09, 0x09, 0x09, 0x06};
const uint8_t font_data_Q[] = {0x3e, 0x41, 0x51, 0x21, 0x5e};
const uint8_t font_data_R[] = {0x7f, 0x09, 0x19, 0x29, 0x46};
const uint8_t font_data_S[] = {0x26, 0x49, 0x49, 0x49, 0x32};
const uint8_t font_data_T[] = {0x01, 0x01, 0x7f, 0x01, 0x01};
const uint8_t font_data_U[] = {0x3f, 0x40, 0x40, 0x40, 0x3f};
const uint8_t font_data_V[] = {0x3f, 0x20, 0x40, 0x20, 0x3f};
const uint8_t font_data_W[] = {0x3f, 0x40, 0x3c, 0x40, 0x3f};
const uint8_t font_data_X[] = {0x63, 0x14, 0x08, 0x14, 0x63};
const uint8_t font_data_Y[] = {0x07, 0x08, 0x70, 0x08, 0x07};
const uint8_t font_data_Z[] = {0x61, 0x51, 0x49, 0x45, 0x43};

constexpr Font make_font() {
    Font font = {};
    font['A'] = font_char_info{sizeof(font_data_A), font_data_A};
    font['B'] = font_char_info{sizeof(font_data_B), font_data_B};
    font['C'] = font_char_info{sizeof(font_data_C), font_data_C};
    font['D'] = font_char_info{sizeof(font_data_D), font_data_D};
    font['E'] = font_char_info{sizeof(font_data_E), font_data_E};
    font['F'] = font_char_info{sizeof(font_data_F), font_data_F};
    font['G'] = font_char_info{sizeof(font_data_G), font_data_G};
    font['H'] = font_char_info{sizeof(font_data_H), font_data_H};
    font['I'] = font_char_info{sizeof(font_data_I), font_data_I};
    font['J'] = font_char_info{sizeof(font_data_J), font_data_J};
    font['K'] = font_char_info{sizeof(font_data_K), font_data_K};
    font['L'] = font_char_info{sizeof(font_data_L), font_data_L};
    font['M'] = font_char_info{sizeof(font_data_M), font_data_M};
    font['N'] = font_char_info{sizeof(font_data_N), font_data_N};
    font['O'] = font_char_info{sizeof(font_data_O), font_data_O};
    font['P'] = font_char_info{sizeof(font_data_P), font_data_P};
    font['Q'] = font_char_info{sizeof(font_data_Q), font_data_Q};
    font['R'] = font_char_info{sizeof(font_data_R), font_data_R};
    font['S'] = font_char_info{sizeof(font_data_S), font_data_S};
    font['T'] = font_char_info{sizeof(font_data_T), font_data_T};
    font['U'] = font_char_info{sizeof(font_data_U), font_data_U};
    font['V'] = font_char_info{sizeof(font_data_V), font_data_V};
    font['W'] = font_char_info{sizeof(font_data_W), font_data_W};
    font['X'] = font_char_info{sizeof(font_data_X), font_data_X};
    font['Y'] = font_char_info{sizeof(font_data_Y), font_data_Y};
    font['Z'] = font_char_info{sizeof(font_data_Z), font_data_Z};
    return font;
}

Font font = make_font();
}

namespace mantyl {

SSD1306::SSD1306(I2cMaster &bus, uint8_t addr, gpio_num_t reset_pin)
    : SSD1306{I2cDevice{bus, addr}, reset_pin} {}
SSD1306::SSD1306(I2cDevice &&device, gpio_num_t reset_pin)
    : dev_{std::move(device)},
      reset_pin_{reset_pin},
      buffer_{new uint8_t[buffer_size()]} {
  memset(buffer_.get(), 0x00, buffer_size());

  size_t offset = 0;
  const char* const str = "ABCDEFGHIJKLMNOPQRSTU";
  for (const char* p = str; *p != '\0'; ++p) {
    const char c = *p;
    memcpy(buffer_.get() + offset, font[c].data, font[c].width);
    offset += font[c].width + 1;
  }

  offset = 128;
  const char* const str2 = "VWXYZ";
  for (const char* p = str2; *p != '\0'; ++p) {
    const char c = *p;
    memcpy(buffer_.get() + offset, font[c].data, font[c].width);
    offset += font[c].width + 1;
  }
}

SSD1306::~SSD1306() {
  if (reset_pin_ >= 0) {
    gpio_reset_pin(reset_pin_);
  }
}

esp_err_t SSD1306::init() {
  // Settings for an Adafruit 128x32 display
  const uint8_t charge_pump = external_vcc_ ? 0x10_u8 : 0x14_u8;
  const uint8_t precharge = external_vcc_ ? 0x22_u8 : 0xf1_u8;

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
                     com_pin_flags_,
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

  return ESP_OK;
}

esp_err_t SSD1306::flush() {
  uint8_t const page_end = (height_ + 7) / 8;
  uint8_t const col_end = width_ - 1;
  auto rc = send_commands(Command::SetPageAddr,
                     0_u8,     // start
                     page_end, // end
                     Command::SetColumnAddr,
                     0_u8,   // start
                     col_end // end
                     );
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
