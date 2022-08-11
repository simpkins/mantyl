// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "SX1509.h"

#include <array>

namespace mantyl {

class Keypad {
public:
  Keypad(I2cMaster &bus, uint8_t addr, gpio_num_t int_pin, uint8_t rows, uint8_t columns)
      : sx1509_{bus, addr, int_pin}, rows_{rows}, columns_{columns} {}

  [[nodiscard]] esp_err_t init();

  void scan();
  void on_interrupt();
  void on_timeout();

  gpio_num_t interrupt_pin() const {
    return sx1509_.interrupt_pin();
  }

private:
  Keypad(Keypad const &) = delete;
  Keypad &operator=(Keypad const &) = delete;

  /**
   * Get the row index from the result of SX1509::read_keypad()
   */
  static int8_t get_row(uint16_t value);

  void update_row(uint8_t row, uint8_t cols);

  static constexpr uint8_t kMaxRows = 8;
  static constexpr uint8_t kMaxCols = 8;

  SX1509 sx1509_;
  const uint8_t rows_{0};
  const uint8_t columns_{0};
  bool initialized_{false};
  uint8_t last_row_seen_{0};
  std::array<uint8_t, kMaxRows> pressed_keys_{};

  uint16_t last_key_{0};
  esp_err_t last_err_{ESP_OK};
  uint64_t counter_{0};
  uint64_t same_count_{0};
  uint64_t noint_count_{0};
};

} // namespace mantyl
