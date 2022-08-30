// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "Keypad.h"

#include <array>
#include <cstdint>

namespace mantyl {

class Keyboard {
public:
  Keyboard(I2cMaster &i2c_left, I2cMaster &i2c_right);

  /**
   * Initialize the keypads.
   *
   * This method is called from the main task, before the keyboard task has
   * started.
   */
  [[nodiscard]] esp_err_t early_init();

  /**
   * Perform additional initialization from the keyboard task, when it first
   * starts.
   */
  [[nodiscard]] esp_err_t kbd_task_init();

  bool should_boot_in_debug_mode();

  std::chrono::milliseconds tick(std::chrono::steady_clock::time_point now);

  void send_report();
  void generate_report(std::array<uint8_t, 6> &keycodes, uint8_t &modifiers);

private:
  Keyboard(Keyboard const &) = delete;
  Keyboard &operator=(Keyboard const &) = delete;

  uint8_t lookup_keycode(bool left, uint8_t row, uint8_t col) const;

  Keypad left_;
  Keypad right_;
};

} // namespace mantyl
