// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "SX1509.h"

#include <array>
#include <chrono>
#include <string>
#include <string_view>

namespace mantyl {

class Keypad {
public:
  Keypad(std::string_view name, I2cMaster &bus, uint8_t addr, gpio_num_t int_pin, uint8_t rows, uint8_t columns)
      : name_{name}, sx1509_{bus, addr, int_pin}, rows_{rows}, columns_{columns} {}

  [[nodiscard]] esp_err_t init();

  std::chrono::milliseconds tick(std::chrono::steady_clock::time_point now);

  gpio_num_t interrupt_pin() const {
    return sx1509_.interrupt_pin();
  }

  /**
   * Perform a check to see if the SX1509 is currently asserting the
   * interrupt pin.
   */
  bool is_interrupt_asserted();

  uint16_t num_pressed() const {
    return num_pressed_;
  }

private:
  Keypad(Keypad const &) = delete;
  Keypad &operator=(Keypad const &) = delete;

  [[nodiscard]] esp_err_t init_common();

  /**
   * Get the row index from the result of SX1509::read_keypad()
   */
  static int8_t get_row(uint16_t value);
  static constexpr std::chrono::milliseconds kReinitTimeout{60 * 1000};
  static constexpr std::chrono::milliseconds kReleaseTimeout{50};

  std::chrono::milliseconds on_interrupt();
  void all_released();

  void update_row(uint8_t row, uint8_t cols);

  static constexpr uint8_t kMaxRows = 8;
  static constexpr uint8_t kMaxCols = 8;

  std::string name_;
  SX1509 sx1509_;
  const uint8_t rows_{0};
  const uint8_t columns_{0};
  bool initialized_{false};
  uint8_t last_row_seen_{0};
  std::array<uint8_t, kMaxRows> pressed_keys_{};

  uint16_t num_pressed_{0};
  std::chrono::steady_clock::time_point last_scan_detected_{};
};

} // namespace mantyl