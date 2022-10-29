// Copyright (c) 2022, Adam Simpkins

#include "mantyl_usb/Esp32UsbDevice.h"

#include <esp_check.h>
#include <esp_log.h>

using namespace mantyl;

namespace {
const char *LogTag = "mantyl.test";

constinit Esp32UsbDevice usb;
}

extern "C" void app_main() {
  ESP_LOGI(LogTag, "main task starting");

  const auto usb_rc = usb.init();
  if (usb_rc != ESP_OK) {
    ESP_LOGE(LogTag, "failed to initialize USB: %d", usb_rc);
  }
  ESP_LOGI(LogTag, "USB initialization DONE");

  usb.loop();
  ESP_LOGI(LogTag, "main task exiting");
}
