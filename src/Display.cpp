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
                     static_cast<uint8_t>(canvas_.height() - 1),
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
                     Command::DisplayOn)) {
    return false;
  }

  return true;
}

void Display::clearDisplayBuffer() {
  canvas_.fillScreen(0);
}

bool Display::draw_pixel(uint16_t x, uint16_t y, bool on) {
  if (x >= canvas_.width()) {
    return false;
  }
  if (y >= canvas_.height()) {
    return false;
  }
  canvas_.drawPixel(x, y, on ? 1 : 0);
  return true;
}

bool Display::get_pixel(uint16_t x, uint16_t y) const {
  if (x >= canvas_.width()) {
    throw std::range_error("x out of bounds");
  }
  if (y >= canvas_.height()) {
    throw std::range_error("y out of bounds");
  }
  return canvas_.get_pixel(x, y);
}

bool Display::flush() {
  uint8_t const page_end = (canvas_.height() + 7) / 8;
  uint8_t const col_end = canvas_.width() - 1;
  if (!send_commands(Command::SetPageAddr,
                     0_u8,     // start
                     page_end, // end
                     Command::SetColumnAddr,
                     0_u8,   // start
                     col_end // end
                     )) {
    return false;
  }

  auto count = canvas_.buffer_size();
  const uint8_t *ptr = canvas_.get_buffer();

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
