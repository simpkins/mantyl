// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <Wire.h>
#include <Adafruit_GFX.h>

#include <array>
#include <cstdint>
#include <memory>
#include <type_traits>
#include <utility>

#define USE_GFX_CANVAS 0

namespace mtl {

/**
 * Code for an SSD1306 display.
 *
 * Adafruit provides an Arduino library for this (Adafruit_SSD1306), however it
 * does not perform error checking of the I2C I/O, so I decided to just
 * implement my own code for this.
 */
class Display {
public:
  static constexpr uint8_t kScreenWidth = 128;
  static constexpr uint8_t kScreenHeight = 32;
  static constexpr uint32_t kBusFrequency = 400000UL;

  static Display adafruit128x32(TwoWire* wire, uint8_t addr);

  [[nodiscard]] bool begin();
  void clearDisplayBuffer();

  [[nodiscard]] bool draw_pixel(uint16_t x, uint16_t y, bool on);
  bool get_pixel(uint16_t x, uint16_t y) const;

  [[nodiscard]] bool flush();

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

  Display(TwoWire *wire,
          uint8_t addr,
          uint8_t width,
          uint8_t height,
          bool external_vcc,
          uint8_t com_pin_flags,
          uint8_t contrast)
      : wire_{wire}, addr_{addr}, width_{width}, height_{height},
        external_vcc_{external_vcc}, com_pin_flags_{com_pin_flags},
        contrast_{contrast},
#if USE_GFX_CANVAS
        // The SSD1306 stores 1 column of data in each byte, and GFXcanvas1
        // expects 1 row in each byte, so transpose rows and columns
        canvas_{height, width}
#else
        buffer_{new uint8_t[buffer_size()]}
#endif
  {
    clearDisplayBuffer();
  }

  Display(Display const &) = delete;
  Display &operator=(Display const &) = delete;

  size_t buffer_size() const { return width_ * ((height_ + 7) / 8); }

  [[nodiscard]] bool send_command_chunk(const uint8_t *data, size_t n);
  [[nodiscard]] bool send_commands(const uint8_t *data, size_t n);

  template <typename... Args>
  [[nodiscard]] bool send_commands(uint8_t cmd, Args... rest) {
      std::array<uint8_t, sizeof...(Args) + 1> data = {cmd, rest...};
      return send_commands(data.data(), data.size());
  }

  std::pair<uint32_t, uint8_t> get_pixel_idx(uint16_t x, uint16_t y) const {
    // The caller is responsible for checking x and y bounds
    const auto idx = x + (y / 8) * width_;
    uint8_t bit = (1 << (y & 7));
    return std::make_pair(idx, bit);
  }

  TwoWire *wire_{nullptr};
  uint8_t addr_{0};
  uint8_t width_{128};
  uint8_t height_{32};
  bool external_vcc_{false};
  uint8_t com_pin_flags_{0};
  uint8_t contrast_{0};
#if USE_GFX_CANVAS
  GFXcanvas1 canvas_;
#else
  std::unique_ptr<uint8_t[]> buffer_;
#endif
};

} // namespace mtl
