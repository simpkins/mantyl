// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <array>
#include <cstdint>

namespace mantyl {

class Keypad;

class Keyboard {
public:
  Keyboard(Keypad* left, Keypad* right);

  void send_report();

private:
  Keyboard(Keyboard const &) = delete;
  Keyboard &operator=(Keyboard const &) = delete;

  uint8_t lookup_keycode(bool left, uint8_t row, uint8_t col) const;

  Keypad* left_{nullptr};
  Keypad* right_{nullptr};

  // The USB boot keyboard protocol can only track up to
  // 6 pressed keys at a time.
  std::array<uint8_t, 6> keycodes_;
  uint8_t modifiers_;
};

} // namespace mantyl
