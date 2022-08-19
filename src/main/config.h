// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <hal/i2c_types.h>

namespace mantyl {

enum : uint32_t {
  I2cClockSpeed = 400000,
};

enum PinConfig : int {
  LeftI2cSDA = 8,
  LeftI2cSCL = 9,
  RightI2cSDA = 7,
  RightI2cSCL = 10,
};

} // namespace mantyl
