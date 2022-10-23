// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <driver/i2c.h>
#include <esp_err.h>

#include <chrono>
#include <type_traits>

namespace mantyl {

class I2cMaster {
public:
  constexpr I2cMaster(int sda, int scl, i2c_port_t port = I2C_NUM_0)
      : port_{port}, sda_{sda}, scl_{scl} {}

  i2c_port_t port() const {
    return port_;
  }

  esp_err_t init(int clock_speed);

  esp_err_t write(uint8_t device_address,
                  const void *write_buffer,
                  size_t write_size,
                  std::chrono::milliseconds timeout);

  esp_err_t read(uint8_t device_address,
                 void *read_buffer,
                 size_t read_size,
                 std::chrono::milliseconds timeout);

  /**
   * Perform a write followed by a read, without releasing the bus in between.
   */
  esp_err_t write_read(uint8_t device_address, const void *write_buffer,
                       size_t write_size, void *read_buffer,
                       size_t read_size, std::chrono::milliseconds timeout);

  /**
   * Write data that is non-contiguous in memory
   */
  esp_err_t write2(uint8_t device_address,
                   const void *write1_buffer,
                   size_t write1_size,
                   const void *write2_buffer,
                   size_t write2_size,
                   std::chrono::milliseconds timeout);

private:
  I2cMaster(I2cMaster const &) = delete;
  I2cMaster &operator=(I2cMaster const &) = delete;

  const i2c_port_t port_{I2C_NUM_0};
  const int sda_{0};
  const int scl_{0};
};

} // namespace mantyl
