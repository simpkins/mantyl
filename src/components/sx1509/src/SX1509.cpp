// Copyright (c) 2022, Adam Simpkins
#include "SX1509.h"

#include <esp_check.h>
#include <endian.h>

namespace {
const char *LogTag = "mantyl.sx1509";
}

namespace mantyl {

esp_err_t SX1509::init() {
  // Send software reset sequence
  auto rc = write_u8(Reg::Reset, 0x12);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "failed to reset SX1509 at %u", dev_.address());
  rc = write_u8(Reg::Reset, 0x34);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "failed to reset SX1509 (2) at %u", dev_.address());

  // Read from some config registers with known default values
  // to verify that we can successfully communicate with the device.
  // This should return 0xff00
  const auto test_regs = read_u16(Reg::IntrMaskA);
  if (test_regs.has_error()) {
    ESP_LOGD(LogTag, "error reading from SX1509: %d", test_regs.error());
    return test_regs.error();
  }
  if (be16toh(test_regs.value()) != 0xff00) {
    ESP_LOGE(LogTag,
             "unexpected data read initializing SX1509: %#0x",
             test_regs.value());
    return ESP_ERR_INVALID_RESPONSE;
  }

  // Configure the clock; use 2Mhz internal clock,
  // and keep I/O frequency at 2Mhz
  rc = configure_clock(ClockSource::Internal2MHZ);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "failed to configure SX1509 (%u) clock", dev_.address());

  initialized_ = true;
  return ESP_OK;
}

Result<uint16_t> SX1509::read_keypad() {
  if (!initialized_) {
    return make_error<uint16_t>(ESP_ERR_INVALID_STATE);
  }

  const auto value = read_u16(Reg::KeyData1);
  if (!value.has_value()) {
    return value;
  }
  return make_result<uint16_t>(0xffff ^ value.value());
}

esp_err_t SX1509::configure_clock(ClockSource source,
                                  uint8_t led_divider,
                                  OscPinFuncion pin_fn,
                                  uint8_t oscout_freq) {
  const uint8_t reg_clock = ((static_cast<uint8_t>(source) & 0x3) << 5) |
                            ((static_cast<uint8_t>(pin_fn) & 0x1) << 4) |
                            (oscout_freq & 0xf);
  auto rc = write_u8(Reg::Clock, reg_clock);
  ESP_RETURN_ON_ERROR(rc, LogTag, "error updating SX1509 Reg::Clock");

  const auto reg_misc = read_u8(Reg::Misc);
  if (!reg_misc.has_value()) {
    return reg_misc.error();
  }
  const uint8_t new_reg_misc =
      ((reg_misc.value() & ~(0b111 << 4)) | ((led_divider & 0b111) << 4));
  rc = write_u8(Reg::Misc, new_reg_misc);
  ESP_RETURN_ON_ERROR(rc, LogTag, "error updating SX1509 Reg::Misc");

  return ESP_OK;
}

esp_err_t SX1509::write_data(uint8_t addr, const void *data, size_t size) {
  return dev_.bus().write2(dev_.address(),
                           &addr,
                           sizeof(addr),
                           data,
                           size,
                           std::chrono::milliseconds(1000));
}

esp_err_t SX1509::read_data(uint8_t addr, void *data, size_t size) {
  return dev_.bus().write_read(
      dev_.address(), &addr, 1, data, size, std::chrono ::milliseconds(1000));
}

} // namespace mantyl
