// Copyright (c) 2022, Adam Simpkins
#include "SSD1306.h"

#include "mantyl_literals.h"

#include <esp_check.h>

namespace {
const char *LogTag = "mantyl.ssd1306";
}

namespace mantyl {

esp_err_t SSD1306::init() {
  // Settings for an Adafruit 128x32 display
  const uint8_t charge_pump = external_vcc_ ? 0x10_u8 : 0x14_u8;
  const uint8_t precharge = external_vcc_ ? 0x22_u8 : 0xf1_u8;

  const auto rc =
      send_commands(Command::DisplayOff,
                    Command::SetDisplayClockDiv,
                    0x80_u8, // reset oscillator frequence and divide ratio
                    Command::SetMultiplex,
                    static_cast<uint8_t>(height_ - 1),
                    Command::SetDisplayOffset,
                    0x0_u8,
                    static_cast<uint8_t>(Command::SetStartLine | 0x0),
                    Command::ChargePump,
                    charge_pump,
                    Command::SetMemoryMode,
                    0x00_u8, // horizontal addressing mode
                    static_cast<uint8_t>(Command::SegRemap | 0x1),
                    Command::ComScanDec,
                    Command::SetComPins,
                    com_pin_flags_,
                    Command::SetContrast,
                    contrast_,
                    Command::SetPrecharge,
                    precharge,
                    Command::SetVComDetect,
                    0x40_u8,
                    Command::DisplayAllOn_RAM,
                    Command::NormalDisplay,
                    Command::DeactivateScroll,
                    Command::DisplayOn);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "error initializing SSD1306 %u", dev_.address());

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
