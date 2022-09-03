// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "Keypad.h"

#include <array>
#include <cstdint>

namespace mantyl {

class Keymap;

class Keyboard {
public:
  Keyboard(I2cMaster &i2c_left, I2cMaster &i2c_right, const Keymap& keymap);

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

  /**
   * Set the current Keymap.
   *
   * Note that the Keyboard stores a reference to the Keymap, and does not make
   * a copy.  The caller must ensure that the Keymap is valid for the lifetime
   * of the Keyboard object.
   */
  void set_keymap(const Keymap &keymap) {
    keymap_ = &keymap;
  }

  bool should_boot_in_debug_mode();

  std::chrono::milliseconds tick(std::chrono::steady_clock::time_point now);

  void generate_report(std::array<uint8_t, 6> &keycodes, uint8_t &modifiers);

private:
  Keyboard(Keyboard const &) = delete;
  Keyboard &operator=(Keyboard const &) = delete;

  void send_hid_report();

  void on_key_press(bool is_left, uint8_t row, uint8_t col);
  void on_key_release(bool is_left, uint8_t row, uint8_t col);
  void on_key_change(bool is_left, uint8_t row, uint8_t col, bool press);

  const Keymap* keymap_{nullptr};
  Keypad left_;
  Keypad right_;
  bool need_to_send_report_{false};
};

} // namespace mantyl
