// Copyright (c) 2022, Adam Simpkins
#include "SX1509.h"

#include <esp_check.h>

namespace {
const char *LogTag = "mantyl.sx1509";
}

namespace mantyl {

esp_err_t SX1509::init() {
  // Send software reset sequence
  auto rc = write_u8(Reg::Reset, 0x12);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "failed to reset SX1509 at %u", dev_.address());
  rc = write_u8(Reg::Reset, 0x34);
  ESP_RETURN_ON_ERROR(
      rc, LogTag, "failed to reset SX1509 (2) at %u", dev_.address());

  // Read from some config registers with known default values
  // to verify that we can successfully communicate with the device.
  // This should return 0xff00
  const auto test_regs = read_u16(Reg::IntrMaskA);
  if (test_regs.index() == 1) {
    ESP_LOGD(LogTag, "error reading from SX1509: %d", std::get<0>(test_regs));
    return std::get<1>(test_regs);
  }
  if (std::get<0>(test_regs) != 0xff00) {
    ESP_LOGE(LogTag,
             "unexpected data read initializing SX1509: %#0x",
             std::get<0>(test_regs));
    return ESP_ERR_INVALID_RESPONSE;
  }

#if 0
  // Configure the clock; use 2Mhz internal clock,
  // and keep I/O frequency at 2Mhz
  return configure_clock(ClockSource::Internal2MHZ);
#endif
  return rc;
}

esp_err_t SX1509::write_data(uint8_t addr, const void *data, size_t size) {
  // 2 transactions: the register address write, followed by the data write
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

  rc = i2c_master_write_byte(cmd, dev_.address() << 1 | I2C_MASTER_WRITE, true);
  if (rc != ESP_OK) {
    goto err;
  }

  rc = i2c_master_write_byte(cmd, addr, true);
  if (rc != ESP_OK) {
    goto err;
  }

  rc = i2c_master_write(cmd, static_cast<const uint8_t *>(data), size, true);
  if (rc != ESP_OK) {
    goto err;
  }

  rc = i2c_master_stop(cmd);
  if (rc != ESP_OK) {
    goto err;
  }

  rc = i2c_master_cmd_begin(dev_.bus().port(), cmd, 1000 / portTICK_PERIOD_MS);
  goto done;

err:

done:
  i2c_cmd_link_delete_static(cmd);
  free(buf);
  return rc;
}

esp_err_t SX1509::read_data(uint8_t addr, void *data, size_t size) {
#if 0
  // 2 transactions: the register address write, followed by the data read
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
  rc = i2c_master_write_byte(
      cmd, (dev_.address() << 1) | I2C_MASTER_WRITE, true);
  if (rc != ESP_OK) {
    goto err;
  }
  rc = i2c_master_write_byte(cmd, addr, true);
  if (rc != ESP_OK) {
      goto err;
  }

  rc = i2c_master_start(cmd);
  if (rc != ESP_OK) {
      goto err;
  }
  rc = i2c_master_read(
      cmd, static_cast<uint8_t *>(data), size, I2C_MASTER_LAST_NACK);
  if (rc != ESP_OK) {
      goto err;
  }
  rc = i2c_master_stop(cmd);
  if (rc != ESP_OK) {
      goto err;
  }

  rc = i2c_master_cmd_begin(dev_.bus().port(), cmd, 1000 / portTICK_PERIOD_MS);
  goto done;

err:

done:
  i2c_cmd_link_delete_static(cmd);
  free(buf);
  return rc;
#else
  return dev_.bus().write_read(
      dev_.address(), &addr, 1, data, size, std::chrono ::milliseconds(1000));
#endif
}

} // namespace mantyl
