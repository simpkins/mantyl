// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "SX1509.h"

#include <array>
#include <chrono>
#include <functional>
#include <string>
#include <string_view>

namespace mantyl {

class Keypad {
public:
  static constexpr uint8_t kMaxRows = 8;
  static constexpr uint8_t kMaxCols = 8;
  using PressedBitmap = std::array<uint8_t, kMaxRows>;
  using Callback = std::function<void(uint8_t, uint8_t)>;

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

  PressedBitmap get_pressed() const {
    return pressed_keys_;
  }

  void set_callbacks(Callback &&press_fn, Callback &&release_fn) {
    press_callback_ = std::move(press_fn);
    release_callback_ = std::move(release_fn);
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

  std::string name_;
  SX1509 sx1509_;
  const uint8_t rows_{0};
  const uint8_t columns_{0};
  bool initialized_{false};
  uint8_t last_row_seen_{0};
  PressedBitmap pressed_keys_{};
  Callback press_callback_;
  Callback release_callback_;

  uint16_t num_pressed_{0};
  std::chrono::steady_clock::time_point last_scan_detected_{};
};

} // namespace mantyl
