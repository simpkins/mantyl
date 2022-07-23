// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "I2cDevice.h"

#include <array>
#include <memory>
#include <utility>

namespace mantyl {

/**
 * A driver for an SSD1036 OLED controller
 *
 * Note that the ESP-IDF does come with an SSD1306 implementation if we did
 * want to use that: esp_lcd_new_panel_ssd1306().  However, it does not appear
 * to have a way to configure timeouts and handle the display not being
 * present.
 */
class SSD1306 {
public:
  SSD1306(I2cMaster &bus, uint8_t addr);
  explicit SSD1306(I2cDevice &&device);

  [[nodiscard]] esp_err_t init();
  [[nodiscard]] esp_err_t flush();

private:
  enum Command : uint8_t {
      SetMemoryMode = 0x20,
      SetColumnAddr = 0x21,
      SetPageAddr = 0x22,
      ScrollRight = 0x26,
      ScrollLeft = 0x27,
      ScrollVerticalRight = 0x29,
      ScrollVerticalLeft = 0x2a,
      DeactivateScroll = 0x2e,
      ActivateScroll = 0x2f,
      SetStartLine = 0x40,
      SetContrast = 0x81,
      ChargePump = 0x8d,
      SegRemap = 0xa0,
      DisplayAllOn_RAM = 0xa4,
      DisplayAllOn = 0xa5,
      NormalDisplay = 0xa6,
      InvertDisplay = 0x7,
      SetVerticalScrollArea = 0xa3,
      SetMultiplex = 0xa8,
      DisplayOff = 0xae,
      DisplayOn = 0xaf,
      SetStartPage0 = 0xb0,
      SetStartPage1 = 0xb1,
      SetStartPage2 = 0xb2,
      SetStartPage3 = 0xb3,
      SetStartPage4 = 0xb4,
      SetStartPage5 = 0xb5,
      SetStartPage6 = 0xb6,
      SetStartPage7 = 0xb7,
      ComScanInc = 0xc0,
      ComScanDec = 0xc8,
      SetDisplayOffset = 0xd3,
      SetDisplayClockDiv = 0xd5,
      SetPrecharge = 0xd9,
      SetComPins = 0xda,
      SetVComDetect = 0xd8,
  };

  SSD1306(SSD1306 const &) = delete;
  SSD1306 &operator=(SSD1306 const &) = delete;

  [[nodiscard]] esp_err_t send_commands(const uint8_t *data, size_t n);

  template <typename... Args>
  [[nodiscard]] esp_err_t send_commands(uint8_t cmd, Args... rest) {
      std::array<uint8_t, sizeof...(Args) + 1> data = {cmd, rest...};
      return send_commands(data.data(), data.size());
  }

  size_t buffer_size() const {
    return width_ * ((height_ + 7) / 8);
  }

  I2cDevice dev_;
  bool external_vcc_{false};
  uint8_t com_pin_flags_{0};
  uint8_t contrast_{0};
  uint8_t width_{128};
  uint8_t height_{32};
  std::unique_ptr<uint8_t[]> buffer_;
};

} // namespace mantyl
