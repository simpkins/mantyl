// Copyright (c) 2022, Adam Simpkins
#include "Display.h"

#include <array>
#include <stdexcept>

namespace mtl {

// Custom literal for an explicit uint8_t value (rather than int)
constexpr uint8_t operator"" _u8(unsigned long long int value) {
  if (value > 0xff) {
    throw std::range_error("invalid uint8_t literal");
  }
  return value;
}

Display Display::adafruit128x32(TwoWire* wire, uint8_t addr) {
  return Display(wire,
                 addr,
                 128,
                 32,
                 /*external_vcc=*/false,
                 /*com_pins=*/0x02_u8,
                 /*contrast=*/0x8f_u8);
}

bool Display::begin() {
  wire_->begin();
  wire_->setClock(kBusFrequency);

  // Settings for an Adafruit 128x32 display
  const uint8_t charge_pump = external_vcc_ ? 0x10_u8 : 0x14_u8;
  const uint8_t precharge = external_vcc_ ? 0x22_u8 : 0xf1_u8;

  if (!send_commands(Command::DisplayOff,
                     Command::SetDisplayClockDiv,
                     0x80_u8, // reset oscillator frequence and divide ratio
                     Command::SetMultiplex,
                     static_cast<uint8_t>(height_ - 1),
                     Command::SetDisplayOffset,
                     0x0_u8,
                     static_cast<uint8_t>(Command::SetStartLine | 0x0),
                     Command::ChargePump,
                     charge_pump,
#if USE_GFX_CANVAS
                     Command::SetMemoryMode,
                     0x01_u8, // vertical addressing mode
#else
                     Command::SetMemoryMode,
                     0x00_u8, // horizontal addressing mode
#endif
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
                     Command::DisplayOn)) {
    return false;
  }

  return true;
}

void Display::clearDisplayBuffer() {
#if USE_GFX_CANVAS
  canvas_.fillScreen(0);
#else
  memset(buffer_.get(), 0, buffer_size());
#endif
}

bool Display::draw_pixel(uint16_t x, uint16_t y, bool on) {
  if (x >= width_) {
    return false;
  }
  if (y >= height_) {
    return false;
  }
#if USE_GFX_CANVAS
  canvas_.drawPixel(y, x, on ? 1 : 0);
#else
  const auto [idx, bit] = get_pixel_idx(x, y);
  if (on) {
    buffer_[idx] |= bit;
  } else {
    buffer_[idx] &= ~bit;
  }
#endif
  return true;
}

bool Display::get_pixel(uint16_t x, uint16_t y) const {
  if (x >= width_) {
    throw std::range_error("x out of bounds");
  }
  if (y >= height_) {
    throw std::range_error("y out of bounds");
  }
#if USE_GFX_CANVAS
  return canvas_.getPixel(y, x);
#else
  const auto [idx, bit] = get_pixel_idx(x, y);
  return (buffer_[idx] & bit);
#endif
}

bool Display::flush() {
  uint8_t const page_end = (height_ + 7) / 8;
  uint8_t const col_end = width_ - 1;
  if (!send_commands(Command::SetPageAddr,
                     0_u8,     // start
                     page_end, // end
                     Command::SetColumnAddr,
                     0_u8,   // start
                     col_end // end
                     )) {
    return false;
  }

  auto count = buffer_size();
#if USE_GFX_CANVAS
  const uint8_t *ptr = canvas_.getBuffer();
#else
  const uint8_t *ptr = buffer_.get();
#endif

  while (count > 0) {
    wire_->beginTransmission(addr_);
    wire_->write(0x40_u8);
    const auto write_len =
        std::min(count, static_cast<size_t>(I2C_BUFFER_LENGTH - 1));
    wire_->write(ptr, write_len);
    if (wire_->endTransmission() != 0) {
      return false;
    }
    ptr += write_len;
    count -= write_len;
  }
  return true;
}

bool Display::send_command_chunk(const uint8_t *data, size_t n) {
  wire_->beginTransmission(addr_);
  wire_->write(0x00_u8);
  wire_->write(data, n);
  return (wire_->endTransmission() == 0);
}

bool Display::send_commands(const uint8_t *data, size_t n) {
  while (n > I2C_BUFFER_LENGTH) {
    if(!send_command_chunk(data, I2C_BUFFER_LENGTH)) {
      return false;
    }
    data += I2C_BUFFER_LENGTH;
    n -= I2C_BUFFER_LENGTH;
  }
  return send_command_chunk(data, n);
}

} // namespace mtl
