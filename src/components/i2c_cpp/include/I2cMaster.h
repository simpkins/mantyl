// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <driver/i2c.h>
#include <esp_err.h>

#include <chrono>
#include <type_traits>

namespace mantyl {

class I2cMaster {
public:
  I2cMaster(int sda, int scl, int port = 0)
      : port_{port}, sda_{sda}, scl_{scl} {}

  int port() const {
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

private:
  I2cMaster(I2cMaster const &) = delete;
  I2cMaster &operator=(I2cMaster const &) = delete;

  int port_{0};
  int sda_{0};
  int scl_{0};
};

} // namespace mantyl
