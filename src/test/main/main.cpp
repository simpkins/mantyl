// Copyright (c) 2022, Adam Simpkins

#include "mantyl_usb/Esp32UsbDevice.h"
#include "mantyl_usb/Descriptors.h"
#include "mantyl_usb/UsbDescriptorMap.h"
#include "mantyl_usb/StaticDescriptorMap.h"

#include <esp_check.h>
#include <esp_log.h>

using namespace mantyl;

namespace mantyl {

namespace {

constexpr auto make_descriptor_map() {
  uint8_t string_index = 0;
  const uint8_t mfgr_index = ++string_index;
  const uint8_t product_index = ++string_index;
  const uint8_t serial_index = ++string_index;

  DeviceDescriptor dev;
  dev.vendor_id = 0x6666; // Prototype product vendor ID
  dev.product_id = 0x1235;
  dev.set_device_version(0, 2);
  dev.manufacturer_str_index = mfgr_index;
  dev.product_str_index = product_index;
  dev.serial_str_index = serial_index;

  InterfaceDescriptor keyboard_itf(0, UsbClass::Hid);
  keyboard_itf.num_endpoints = 1;
  keyboard_itf.subclass = 1;
  keyboard_itf.protocol = 1;

  EndpointDescriptor ep1(EndpointAddress(EndpointNumber(1), Direction::In),
                         EndpointAttributes(EndpointType::Interrupt));
  ep1.interval = 10;
  ep1.max_packet_size = 8;

  return StaticDescriptorMap<0, 0>()
      .add_device_descriptor(dev)
      .add_language_ids(Language::English_US)
      .add_string(mfgr_index, "Adam Simpkins", Language::English_US)
      .add_string(product_index, "Mantyl Keyboard", Language::English_US)
      .add_string(serial_index, "00:00:00::00:00:00", Language::English_US)
      .add_config_descriptor(1, 0, keyboard_itf, ep1);
}

constinit auto map = make_descriptor_map();
} // namespace

class TestDevice : UsbDeviceImpl {
public:
  constexpr TestDevice() = default;

  esp_err_t init() {
    // TODO: Update the serial number
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
  decltype(make_descriptor_map()) descriptors_ = make_descriptor_map();
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
