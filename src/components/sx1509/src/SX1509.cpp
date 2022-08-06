// Copyright (c) 2022, Adam Simpkins
#include "SX1509.h"

#include "mantyl_literals.h"

#include <esp_check.h>
#include <endian.h>

namespace {
const char *LogTag = "mantyl.sx1509";
}

namespace mantyl {

esp_err_t SX1509::init() {
  if (reset_pin_ >= 0) {
    gpio_config_t io_conf = {
        .pin_bit_mask = 1ULL << reset_pin_,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    auto rc = gpio_config(&io_conf);
    ESP_RETURN_ON_ERROR(rc, LogTag, "failed to configure SX1509 reset pin");

    gpio_set_level(reset_pin_, 0);
    // Minimum reset low pulse width is 3us, according to the datasheet
    vTaskDelay(pdMS_TO_TICKS(1));
    gpio_set_level(reset_pin_, 1);
    vTaskDelay(pdMS_TO_TICKS(10));
  } else {
    // Send software reset sequence
    auto rc = write_u8(Reg::Reset, 0x12);
    ESP_RETURN_ON_ERROR(
        rc, LogTag, "failed to reset SX1509 at %u", dev_.address());
    rc = write_u8(Reg::Reset, 0x34);
    ESP_RETURN_ON_ERROR(
        rc, LogTag, "failed to reset SX1509 (2) at %u", dev_.address());
  }

  if (int_pin_ >= 0) {
    gpio_config_t io_conf = {
        .pin_bit_mask = 1ULL << int_pin_,
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    auto rc = gpio_config(&io_conf);
    ESP_RETURN_ON_ERROR(rc, LogTag, "failed to configure SX1509 interrupt pin");
  }

  // Read from some config registers with known default values
  // to verify that we can successfully communicate with the device.
  // This should return 0xff00
  const auto test_regs = read_u16be(Reg::IntrMaskA);
  if (test_regs.has_error()) {
    ESP_LOGD(LogTag, "error reading from SX1509: %d", test_regs.error());
    return test_regs.error();
  }
  if (test_regs.value() != 0xff00) {
    ESP_LOGE(LogTag,
             "unexpected data read initializing SX1509: %#0x",
             test_regs.value());
    return ESP_ERR_INVALID_RESPONSE;
  }

  // Configure the clock; use 2Mhz internal clock,
  // and keep I/O frequency at 2Mhz
  auto rc = configure_clock(ClockSource::Internal2MHZ);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "failed to configure SX1509 (%u) clock", dev_.address());

  initialized_ = true;
  return ESP_OK;
}

SX1509::~SX1509() {
  if (reset_pin_ >= 0) {
    gpio_reset_pin(reset_pin_);
  }
  if (int_pin_ >= 0) {
    gpio_reset_pin(int_pin_);
  }
}

Result<uint16_t> SX1509::read_keypad() {
  if (!keypad_configured_) {
    return make_error<uint16_t>(ESP_ERR_INVALID_STATE);
  }

  const auto value = read_u16be(Reg::KeyData1);
  if (!value.has_value()) {
    return value;
  }
  // The data returned by the SX1509 is a bitmask, with one bit per row
  // and one bit per column.  The row and column that was detected as a key
  // press are set to 0 and all other bits are set to 1.  Invert this so that
  // the pressed row & column are 1 and all other bits are 0.
  return make_result<uint16_t>(0xffff ^ value.value());
}

int SX1509::read_int() {
  if (int_pin_ >= 0) {
    return gpio_get_level(int_pin_);
  }
  return -1;
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

  const uint8_t reg_misc = (led_divider & 0b111) << 4;
  rc = write_u8(Reg::Misc, reg_misc);
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

esp_err_t SX1509::configure_keypad(uint8_t rows, uint8_t columns) {
  if (!initialized_) {
    return ESP_ERR_INVALID_STATE;
  }

  // Set bank A to output and B to input
  const uint16_t dir_bits = 0xff00;
  auto rc = write_u16be(Reg::DirB, dir_bits);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to configure keypad I/O directions");

  // Configure bank A as open drain
  rc = write_u8(Reg::OpenDrainA, 0xff_u8);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to configure keypad open drain");

  // Enable pull-up on bank B
  rc = write_u8(Reg::PullUpB, 0xff_u8);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to configure keypad pull-ups");

  // Configure debounce.  With the default 2MHz internal oscillator:
  // 0: .5ms    4: 8ms
  // 1: 1ms     5: 16ms
  // 2: 2ms     6: 32ms
  // 3: 4ms     7: 64ms
  rc = write_u8(Reg::DebounceConfig, 0);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to configure keypad debounce time");
  // Enable debounce on all of the pins
  rc = write_u16be(Reg::DebounceEnableB, 0xffff);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to enable keypad debounce");

  // Auto sleep time:
  // 0: 0ff     4: 1s
  // 1: 128ms   5: 2s
  // 2: 256ms   6: 4s
  // 3: 512ms   7: 8s
  const auto auto_sleep_config = 1_u8;
  // Scan time per row:
  // (must be higher than debounce time)
  // 0: 1ms    4: 16ms
  // 1: 2ms    5: 32ms
  // 2: 4ms    6: 64ms
  // 3: 8ms    7: 128ms
  const auto scan_time_config = 0_u8;
  const auto key_config1 = (auto_sleep_config << 4) | scan_time_config;
  rc = write_u8(Reg::KeyConfig1, key_config1);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to write keypad config1");

  const auto num_row_bits = rows == 1 ? 1 : (rows - 1);
  const auto num_col_bits = (columns - 1);
  const auto key_config2 = (num_row_bits << 3) | num_col_bits;
  rc = write_u8(Reg::KeyConfig2, key_config2);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to write keypad config2");

  keypad_configured_ = true;
  return ESP_OK;
}

} // namespace mantyl
