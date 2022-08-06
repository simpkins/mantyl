// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "SX1509.h"

namespace mantyl {

class Keypad {
public:
  Keypad(I2cMaster &bus, uint8_t addr, gpio_num_t int_pin, uint8_t rows, uint8_t columns)
      : sx1509_{bus, addr, int_pin}, rows_{rows}, columns_{columns} {}

  [[nodiscard]] esp_err_t init();

  void scan();

private:
  Keypad(Keypad const &) = delete;
  Keypad &operator=(Keypad const &) = delete;

  static uint8_t gen_key_index(uint16_t value);

  SX1509 sx1509_;
  const uint8_t rows_{0};
  const uint8_t columns_{0};
  bool initialized_{false};
  uint8_t peeked_key_{0};
  uint64_t pressed_keys_{0};

  uint16_t last_key_{0};
  esp_err_t last_err_{ESP_OK};
  uint64_t counter_{0};
  uint64_t same_count_{0};
  uint64_t noint_count_{0};
};

} // namespace mantyl
