// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <hal/i2c_types.h>

namespace mantyl {

enum : uint32_t {
  I2cClockSpeed = 400000,
};

enum PinConfig : int {
  I2cSDA = 8,
  I2cSCL = 9,
};

} // namespace mantyl
