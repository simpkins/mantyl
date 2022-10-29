// Copyright (c) 2022, Adam Simpkins

#include "mantyl_usb/Esp32UsbDevice.h"
#include "mantyl_usb/UsbDescriptorMap.h"

#include <esp_check.h>
#include <esp_log.h>

using namespace mantyl;

namespace mantyl {

class TestDevice : UsbDeviceImpl {
public:
  constexpr TestDevice() = default;

  esp_err_t init() {
    return usb_.init();
  }
  void loop() {
    return usb_.loop();
  }

  std::optional<buf_view> get_descriptor(uint16_t value,
                                         uint16_t index) override {
    return descriptors_.find_descriptor(value, index);
  }
  uint8_t on_enumerated(uint8_t size) override {
      // TODO: update the device descriptor
      return size;
  }
  void on_suspend() override {}
  bool on_configured(uint8_t config_id) override {
    return true;
  }

private:
  Esp32UsbDevice usb_{this};
  UsbDescriptorMap descriptors_;
};

} // namespace mantyl

namespace {
const char *LogTag = "mantyl.test";

constinit TestDevice usb;
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
