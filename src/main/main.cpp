// Copyright (c) 2022, Adam Simpkins

#include "config.h"
#include "sdkconfig.h"

#include <chrono>

#include <stdio.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <esp_check.h>
#include <esp_log.h>
#include <esp_chip_info.h>
#include <esp_flash.h>
#include <driver/i2c.h>

using namespace std::chrono_literals;

namespace mantyl {

static const char *LogTag = "mantyl.main";

void print_info() {
  /* Print chip information */
  esp_chip_info_t chip_info;
  uint32_t flash_size;
  esp_chip_info(&chip_info);
  ESP_LOGD(LogTag, "This is %s chip with %d CPU core(s), WiFi%s%s, ",
           CONFIG_IDF_TARGET, chip_info.cores,
           (chip_info.features & CHIP_FEATURE_BT) ? "/BT" : "",
           (chip_info.features & CHIP_FEATURE_BLE) ? "/BLE" : "");

  ESP_LOGD(LogTag, "silicon revision %d, ", chip_info.revision);
  if (esp_flash_get_size(NULL, &flash_size) != ESP_OK) {
    ESP_LOGD(LogTag, "Get flash size failed");
    return;
  }

  ESP_LOGD(LogTag, "%uMB %s flash\n", flash_size / (1024 * 1024),
           (chip_info.features & CHIP_FEATURE_EMB_FLASH) ? "embedded"
                                                         : "external");

  ESP_LOGD(LogTag, "Minimum free heap size: %d bytes\n",
           esp_get_minimum_free_heap_size());
}

class I2cMaster {
public:
  I2cMaster(int sda, int scl, int port = 0)
      : port_{port}, sda_{sda}, scl_{scl} {}

  esp_err_t init() {
    i2c_config_t conf = {};
    conf.mode = I2C_MODE_MASTER;
    conf.sda_io_num = sda_;
    conf.scl_io_num = scl_;
    conf.sda_pullup_en = GPIO_PULLUP_ENABLE;
    conf.scl_pullup_en = GPIO_PULLUP_ENABLE;
    conf.master.clk_speed = I2cClockSpeed;

    auto rc = i2c_driver_install(port_, conf.mode, /*slv_rx_buf_len=*/0,
                                 /*slv_tx_buf_len=*/0, /*intr_alloc_flags=*/0);
    ESP_RETURN_ON_ERROR(rc, LogTag, "failed to initialize I2C driver: %d", rc);

    i2c_param_config(port_, &conf);
    ESP_RETURN_ON_ERROR(rc, LogTag, "failed to configure I2C bus: %d", rc);
    return ESP_OK;
  }

  esp_err_t write(i2c_port_t i2c_num, uint8_t device_address,
                  const void *write_buffer, size_t write_size,
                  std::chrono::milliseconds timeout) {
    return i2c_master_write_to_device(
        port_, device_address, reinterpret_cast<const uint8_t *>(write_buffer),
        write_size, timeout.count() / portTICK_PERIOD_MS);
  }

  esp_err_t read(i2c_port_t i2c_num, uint8_t device_address,
                  void *read_buffer, size_t read_size,
                  std::chrono::milliseconds timeout) {
    return i2c_master_read_from_device(
        port_, device_address, reinterpret_cast<uint8_t *>(read_buffer), read_size,
        timeout.count() / portTICK_PERIOD_MS);
  }

  /**
   * Perform a write followed by a read, without releasing the bus in between.
   */
  esp_err_t write_read(uint8_t device_address, const void *write_buffer,
                       size_t write_size, void *read_buffer,
                       size_t read_size, std::chrono::milliseconds timeout) {
    return i2c_master_write_read_device(
        port_, device_address, reinterpret_cast<const uint8_t *>(write_buffer),
        write_size, reinterpret_cast<uint8_t *>(read_buffer), read_size,
        timeout.count() / portTICK_PERIOD_MS);
  }

private:
  int port_{0};
  int sda_{0};
  int scl_{0};
};

class App {
public:
  esp_err_t init();
  esp_err_t test();

private:
  I2cMaster i2c_{PinConfig::I2cSDA, PinConfig::I2cSCL};
};

esp_err_t App::init() {
  return i2c_.init();
}

esp_err_t App::test() {
  static constexpr uint8_t kScreenAddress = 0x3c;
  static constexpr uint8_t kSX1509AddressLeft = 0x3e;
  static constexpr uint8_t kSX1509AddressRight = 0x3f;

  printf("attempting left SX1509 read:\n");
  uint8_t reg_addr = 0x13;
  uint8_t data[2];
  auto rc = i2c_.write_read(kSX1509AddressLeft, &reg_addr, 1, data, 2, 1000ms);
  if (rc == ESP_OK) {
    printf("read success: %#0x, %#0x\n", data[0], data[1]);
  } else {
    printf("read failure: %d: %s\n", rc, esp_err_to_name(rc));
  }

  printf("attempting right SX1509 read:\n");
  rc = i2c_.write_read(kSX1509AddressRight, &reg_addr, 1, data, 2, 1000ms);
  if (rc == ESP_OK) {
    printf("read success: %#0x, %#0x\n", data[0], data[1]);
  } else {
    printf("read failure: %d: %s\n", rc, esp_err_to_name(rc));
  }

  return ESP_OK;
}

void main() {
  printf("Hello world!\n");
  esp_log_level_set("mantyl.main", ESP_LOG_DEBUG);

  print_info();

  App app;
  ESP_ERROR_CHECK(app.init());
  app.test();

  for (int i = 10; i >= 0; i--) {
    printf("Restarting in %d seconds...\n", i);
    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }
  printf("Restarting now.\n");
  fflush(stdout);
  esp_restart();
}

} // namespace mantyl

extern "C" void app_main() {
  mantyl::main();
}
