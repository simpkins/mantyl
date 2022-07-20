// Copyright (c) 2022, Adam Simpkins

#include "I2cMaster.h"

#include <esp_check.h>

namespace {
const char *LogTag = "mantyl.i2c";
}

namespace mantyl {

esp_err_t I2cMaster::init(int clock_speed) {
  i2c_config_t conf = {};
  conf.mode = I2C_MODE_MASTER;
  conf.sda_io_num = sda_;
  conf.scl_io_num = scl_;
  conf.sda_pullup_en = GPIO_PULLUP_ENABLE;
  conf.scl_pullup_en = GPIO_PULLUP_ENABLE;
  conf.master.clk_speed = clock_speed;

  auto rc = i2c_driver_install(port_,
                               conf.mode,
                               /*slv_rx_buf_len=*/0,
                               /*slv_tx_buf_len=*/0,
                               /*intr_alloc_flags=*/0);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to initialize I2C driver: %d", rc);

  i2c_param_config(port_, &conf);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to configure I2C bus: %d", rc);
  return ESP_OK;
}

esp_err_t I2cMaster::write(uint8_t device_address,
                           const void *write_buffer,
                           size_t write_size,
                           std::chrono::milliseconds timeout) {
  return i2c_master_write_to_device(
      port_,
      device_address,
      reinterpret_cast<const uint8_t *>(write_buffer),
      write_size,
      timeout.count() / portTICK_PERIOD_MS);
}

esp_err_t I2cMaster::read(uint8_t device_address,
                          void *read_buffer,
                          size_t read_size,
                          std::chrono::milliseconds timeout) {
  return i2c_master_read_from_device(port_,
                                     device_address,
                                     reinterpret_cast<uint8_t *>(read_buffer),
                                     read_size,
                                     timeout.count() / portTICK_PERIOD_MS);
}

esp_err_t I2cMaster::write_read(uint8_t device_address,
                                const void *write_buffer,
                                size_t write_size,
                                void *read_buffer,
                                size_t read_size,
                                std::chrono::milliseconds timeout) {
  return i2c_master_write_read_device(
      port_,
      device_address,
      reinterpret_cast<const uint8_t *>(write_buffer),
      write_size,
      reinterpret_cast<uint8_t *>(read_buffer),
      read_size,
      timeout.count() / portTICK_PERIOD_MS);
}

esp_err_t I2cMaster::write2(uint8_t device_address,
                            const void *write1_buffer,
                            size_t write1_size,
                            const void *write2_buffer,
                            size_t write2_size,
                            std::chrono::milliseconds timeout) {
  // 2 transactions
  // I2C_LINK_RECOMMENDED_SIZE already takes into account space for the start,
  // stop, and device address write.
  const auto bufsize = I2C_LINK_RECOMMENDED_SIZE(2);

  auto* buf = static_cast<uint8_t*>(malloc(bufsize));
  if (buf == nullptr) {
    return ESP_ERR_NO_MEM;
  }
  i2c_cmd_handle_t cmd = i2c_cmd_link_create_static(buf, bufsize);
  auto rc = i2c_master_start(cmd);
  if (rc != ESP_OK) {
    goto err;
  }

  rc = i2c_master_write_byte(cmd, device_address << 1 | I2C_MASTER_WRITE, true);
  if (rc != ESP_OK) {
    goto err;
  }

  rc = i2c_master_write(
      cmd, static_cast<const uint8_t *>(write1_buffer), write1_size, true);
  if (rc != ESP_OK) {
    goto err;
  }

  rc = i2c_master_write(
      cmd, static_cast<const uint8_t *>(write2_buffer), write2_size, true);
  if (rc != ESP_OK) {
    goto err;
  }

  rc = i2c_master_stop(cmd);
  if (rc != ESP_OK) {
    goto err;
  }

  rc = i2c_master_cmd_begin(port_, cmd, timeout.count() / portTICK_PERIOD_MS);
  goto done;

err:

done:
  i2c_cmd_link_delete_static(cmd);
  free(buf);
  return rc;
}

} // namespace mantyl
