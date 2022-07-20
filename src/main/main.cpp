// Copyright (c) 2022, Adam Simpkins

#include "config.h"
#include "sdkconfig.h"

#include "I2cMaster.h"
#include "SSD1306.h"
#include "SX1509.h"

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

class App {
public:
  esp_err_t init();
  esp_err_t test();

private:
  I2cMaster i2c_{PinConfig::I2cSDA, PinConfig::I2cSCL};
  SSD1306 display_{i2c_, 0x3c};
  SX1509 left_{i2c_, 0x3e};
  SX1509 right_{i2c_, 0x3f};
};

esp_err_t App::init() {
  return i2c_.init(I2cClockSpeed);
}

esp_err_t App::test() {
  ESP_LOGV(LogTag, "attempting left SX1509 init:");
  auto rc = left_.init();
  if (rc == ESP_OK) {
    ESP_LOGI(LogTag, "successfully initialized left key matrix");
  } else {
    ESP_LOGE(LogTag,
             "failed to initialize left key matrix: %d: %s",
             rc,
             esp_err_to_name(rc));
  }

  ESP_LOGV(LogTag, "attempting right SX1509 init:");
  rc = right_.init();
  if (rc == ESP_OK) {
    ESP_LOGI(LogTag, "successfully initialized right key matrix");
  } else {
    // Maybe the right key matrix is not connected.
    ESP_LOGE(LogTag,
             "failed to initialize right key matrix: %d: %s",
             rc,
             esp_err_to_name(rc));
  }

  ESP_LOGI(LogTag, "attempting display init:");
  rc = display_.init();
  if (rc == ESP_OK) {
    ESP_LOGI(LogTag, "successfully initialized display");
  } else {
    ESP_LOGE(LogTag,
             "failed to initialize display matrix: %d: %s",
             rc,
             esp_err_to_name(rc));
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
