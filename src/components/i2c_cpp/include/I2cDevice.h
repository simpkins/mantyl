// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "I2cMaster.h"

namespace mantyl {

class I2cDevice {
public:
  I2cDevice(I2cMaster &bus, uint8_t addr) : bus_{&bus}, addr_{addr} {}
  I2cDevice(I2cDevice &&) = default;
  I2cDevice &operator=(I2cDevice &&) = default;

  uint8_t address() const {
      return addr_;
  }
  I2cMaster& bus() {
      return *bus_;
  }

  [[nodiscard]] esp_err_t write(const void *write_buffer,
                                size_t write_size,
                                std::chrono::milliseconds timeout) {
    return bus_->write(addr_, write_buffer, write_size, timeout);
  }

  template <typename IntType>
  [[nodiscard]] esp_err_t
  // write_int(std::enable_if_t<std::is_arithmetic_v<IntType>, IntType> value,
  write_int(IntType value,
            std::chrono::milliseconds timeout) {
    return write(&value, sizeof(value), timeout);
  }
  [[nodiscard]] esp_err_t write_u8(uint8_t value,
                                   std::chrono::milliseconds timeout) {
    return write_int(value, timeout);
  }
  [[nodiscard]] esp_err_t write_u16(uint16_t value,
                                    std::chrono::milliseconds timeout) {
    return write_int(value, timeout);
  }
  [[nodiscard]] esp_err_t write_u32(uint32_t value,
                                    std::chrono::milliseconds timeout) {
    return write_int(value, timeout);
  }

private:
  I2cMaster *bus_;
  uint8_t addr_{0};
};

} // namespace mantyl
