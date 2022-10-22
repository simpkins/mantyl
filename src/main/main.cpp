// Copyright (c) 2022, Adam Simpkins

#include "config.h"
#include "sdkconfig.h"

#include "App.h"

#include <esp_chip_info.h>
#include <esp_flash.h>
#include <esp_log.h>

namespace {
const char *LogTag = "mantyl.main";
}

namespace mantyl {

void print_info() {
  /* Print chip information */
  esp_chip_info_t chip_info;
  uint32_t flash_size;
  esp_chip_info(&chip_info);
  ESP_LOGD(LogTag, "Running on %s chip with %d CPU core(s), WiFi%s%s, ",
           CONFIG_IDF_TARGET, chip_info.cores,
           (chip_info.features & CHIP_FEATURE_BT) ? "/BT" : "",
           (chip_info.features & CHIP_FEATURE_BLE) ? "/BLE" : "");

  ESP_LOGD(LogTag, "silicon revision %d, ", chip_info.revision);
  if (esp_flash_get_size(NULL, &flash_size) != ESP_OK) {
    ESP_LOGD(LogTag, "Get flash size failed");
    return;
  }

  ESP_LOGD(LogTag, "%luMB %s flash", flash_size / (1024 * 1024),
           (chip_info.features & CHIP_FEATURE_EMB_FLASH) ? "embedded"
                                                         : "external");

  ESP_LOGD(LogTag, "Minimum free heap size: %" PRIu32 " bytes",
           esp_get_minimum_free_heap_size());
}

} // namespace mantyl

extern "C" void app_main() {
  esp_log_level_set("mantyl.main", ESP_LOG_DEBUG);

  mantyl::print_info();

  // TODO: move the App to a static storage variable, so it does not take
  // up room on the stack
  mantyl::App app;
  app.main();
  ESP_LOGW(LogTag, "main task exiting");
}
