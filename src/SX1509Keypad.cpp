// Copyright (c) 2022, Adam Simpkins

#include "SX1509Keypad.h"

#include "literals.h"

#include <HardwareSerial.h>

namespace mtl {

SX1509Keypad::SX1509Keypad(TwoWire *wire, uint8_t addr)
    : wire_{wire}, dev_addr_{addr} {}

bool SX1509Keypad::begin() {
  // Send software reset sequence
  if (!write_u8(Reg::Reset, 0x12) || !write_u8(Reg::Reset, 0x34)) {
    Serial.println("error resetting SX1509");
  }

  // Read from some config registers with known default values
  // to verify that we can successfully communicate with the device.
  // This should return 0xff00
  const auto testRegisters = read_u16(Reg::IntrMaskA);
  if (testRegisters != 0xff00) {
    Serial.println("error initializing SX1509");
    return false;
  }

  // Configure the clock; use 2Mhz internal clock,
  // and keep I/O frequency at 2Mhz
  return configure_clock(ClockSource::Internal2MHZ);
}

bool SX1509Keypad::configure_keypad(uint8_t rows, uint8_t columns) {
  // Set bank B to output and A to input
  const uint16_t dir_bits = 0xff00;
  if (!write_u16(Reg::DirB, dir_bits)) {
    Serial.println("failed to configure keypad I/O directions");
    return false;
  }

  // Configure bank A as open drain
  if (!write_u8(Reg::OpenDrainA, 0xff_u8)) {
    Serial.println("failed to configure keypad open drain");
    return false;
  }

  // Enable pull-up on bank B
  if (!write_u8(Reg::PullUpB, 0xff_u8)) {
    Serial.println("failed to configure keypad pull-ups");
    return false;
  }

  // Configure debounce.  With the default 2MHz internal oscillator:
  // 0: .5ms    4: 8ms
  // 1: 1ms     5: 16ms
  // 2: 2ms     6: 32ms
  // 3: 4ms     7: 64ms
  if (!write_u8(Reg::DebounceConfig, 0)) {
    Serial.println("failed to configure keypad debounce time");
    return false;
  }
  // Enable debounce on all of the pins
  if (!write_u16(Reg::DebounceEnableB, 0xffff)) {
    Serial.println("failed to enable keypad debounce");
    return false;
  }

  // Auto sleep time:
  // 0: 0ff     4: 1s
  // 1: 128ms   5: 2s
  // 2: 256ms   6: 4s
  // 3: 512ms   7: 8s
  const auto auto_sleep_config = 0_u8;
  // Scan time per row:
  // (must be higher than debounce time)
  // 0: 1ms    4: 16ms
  // 1: 2ms    5: 32ms
  // 2: 4ms    6: 64ms
  // 3: 8ms    7: 128ms
  const auto scan_time_config = 0_u8;
  const auto key_config1 = (auto_sleep_config << 4) | scan_time_config;
  if (!write_u8(Reg::KeyConfig1, key_config1)) {
    Serial.println("failed to write keypad config1");
    return false;
  }

  const auto num_row_bits = rows == 1 ? 1 : (rows - 1);
  const auto num_col_bits = (columns - 1);
  const auto key_config2 = (num_row_bits << 3) | num_col_bits;
  if (!write_u8(Reg::KeyConfig2, key_config2)) {
    Serial.println("failed to write keypad config2");
    return false;
  }

  keypad_configured_ = true;
  return true;
}

uint16_t SX1509Keypad::read_keypad() {
  if (!keypad_configured_) {
    return 0;
  }

  const auto value = read_u16(Reg::KeyData1);
  if (!value.has_value()) {
    return 0;
  }
  return 0xffff ^ value.value();
}

bool SX1509Keypad::configure_clock(ClockSource source,
                                   uint8_t led_divider,
                                   OscPinFuncion pin_fn,
                                   uint8_t oscout_freq) {
  const uint8_t reg_clock = ((static_cast<uint8_t>(source) & 0x3) << 5) |
                            ((static_cast<uint8_t>(pin_fn) & 0x1) << 4) |
                            (oscout_freq & 0xf);
  if (!write_u8(Reg::Clock, reg_clock)) {
    Serial.println("error updating SX1509 Reg::Clock");
    return false;
  }

  const auto reg_misc = read_u8(Reg::Misc);
  if (!reg_misc.has_value()) {
    return false;
  }
  const uint8_t new_reg_misc =
      ((reg_misc.value() & ~(0b111 << 4)) | ((led_divider & 0b111) << 4));
  if (!write_u8(Reg::Misc, new_reg_misc)) {
    Serial.println("error updating SX1509 Reg::Misc");
    return false;
  }
  return true;
}

bool SX1509Keypad::prepare_read(uint8_t addr, uint8_t size) {
  wire_->beginTransmission(dev_addr_);
  wire_->write(addr);
  if (wire_->endTransmission() != 0) {
    Serial.println("error writing read address to SX1509");
    return false;
  }

  const auto bytes_received = wire_->requestFrom(dev_addr_, size);
  if (bytes_received != size) {
    Serial.println("received fewer bytes than desired from SX1509");
    return false;
  }
  return true;
}

std::optional<uint8_t> SX1509Keypad::read_u8(uint8_t addr) {
  if (!prepare_read(addr, 1)) {
    return std::nullopt;
  }
  return (wire_->read() & 0xff);
}

std::optional<uint16_t> SX1509Keypad::read_u16(uint8_t addr) {
  if (!prepare_read(addr, 2)) {
    return std::nullopt;
  }
  const auto msb = (wire_->read() & 0xff);
  const auto lsb = (wire_->read() & 0xff);
  return (msb << 8) | lsb;
}

bool SX1509Keypad::write_u8(uint8_t addr, uint8_t value) {
  wire_->beginTransmission(dev_addr_);
  const bool result = wire_->write(addr) && wire_->write(value);
  if (wire_->endTransmission() != 0) {
    return false;
  }
  return result;
}

bool SX1509Keypad::write_u16(uint8_t addr, uint16_t value) {
  wire_->beginTransmission(dev_addr_);
  const bool result = wire_->write(addr) && wire_->write((value >> 8) & 0xff) &&
                      wire_->write(value & 0xff);
  if (wire_->endTransmission() != 0) {
    return false;
  }
  return result;
}

} // namespace mtl
