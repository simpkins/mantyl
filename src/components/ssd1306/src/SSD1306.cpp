// Copyright (c) 2022, Adam Simpkins
#include "SSD1306.h"

#include "mantyl_literals.h"

#include <esp_check.h>
#include <string.h>

namespace {
const char *LogTag = "mantyl.ssd1306";
}

namespace mantyl {

SSD1306::SSD1306(I2cMaster &bus, uint8_t addr) : SSD1306{I2cDevice{bus, addr}} {}
SSD1306::SSD1306(I2cDevice &&device)
    : dev_{std::move(device)}, buffer_{new uint8_t[buffer_size()]} {
  memset(buffer_.get(), 0x00, buffer_size());
}

esp_err_t SSD1306::init() {
  // Settings for an Adafruit 128x32 display
  const uint8_t charge_pump = external_vcc_ ? 0x10_u8 : 0x14_u8;
  const uint8_t precharge = external_vcc_ ? 0x22_u8 : 0xf1_u8;

  auto rc =
      send_commands(Command::DisplayOff,
                    Command::SetDisplayClockDiv,
                    0x80_u8, // reset oscillator frequence and divide ratio
                    Command::SetMultiplex);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(1) error initializing SSD1306 %u", dev_.address());

  rc = send_commands(static_cast<uint8_t>(height_ - 1));
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(2) error initializing SSD1306 %u", dev_.address());

  rc = send_commands(Command::SetDisplayOffset,
                     0x0_u8,
                     static_cast<uint8_t>(Command::SetStartLine | 0x0),
                     Command::ChargePump);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(3) error initializing SSD1306 %u", dev_.address());
  rc = send_commands(charge_pump);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "(4) error initializing SSD1306 %u", dev_.address());

  rc = send_commands(
                     Command::SetMemoryMode,
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

  rc = send_commands(Command::SetVComDetect,
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
