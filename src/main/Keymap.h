// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <array>
#include <cstdint>
#include <string>

namespace mantyl {

struct KeyInfo {
  uint8_t key{};
  uint8_t modifiers{};
};

class Keymap {
public:
  static constexpr size_t kNumKeys = 96;
  using Array = std::array<KeyInfo, kNumKeys>;

  Keymap(std::string_view name, const Array &keys) : name_{name}, keys_{keys} {}

  KeyInfo get_key(bool left, uint8_t row, uint8_t col) const {
    if (row > 5) {
      return KeyInfo{};
    }
    size_t idx = (left ? 0 : 48) + (row * 8) + col;
    return keys_[idx];
  }

private:
  Keymap(Keymap const &) = delete;
  Keymap &operator=(Keymap const &) = delete;

  std::string name_;
  std::array<KeyInfo, 96> keys_;
};

} // namespace mantyl
