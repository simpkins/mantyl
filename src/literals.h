// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <cstdint>
#include <stdexcept>

namespace mtl {

// Custom literal for an explicit uint8_t value (rather than int)
constexpr uint8_t operator"" _u8(unsigned long long int value) {
  if (value > 0xff) {
    throw std::range_error("invalid uint8_t literal");
  }
  return value;
}

} // namespace mtl
