// Copyright (c) 2022, Adam Simpkins

#include "mantyl_usb/Esp32UsbDevice.h"
#include "mantyl_usb/Descriptors.h"
#include "mantyl_usb/UsbDescriptorMap.h"
#include "mantyl_usb/StaticDescriptorMap.h"
#include "mantyl_readline.h"

#include <esp_check.h>
#include <esp_log.h>

using namespace mantyl;

namespace mantyl {

namespace {

constexpr uint8_t kManufacturerStringIndex = 1;
constexpr uint8_t kProductStrIndex = 2;
constexpr uint8_t kSerialStrIndex = 3;

constexpr auto make_descriptor_map() {
  DeviceDescriptor dev;
  dev.vendor_id = 0x6666; // Prototype product vendor ID
  dev.product_id = 0x1235;
  dev.set_device_version(0, 2);
  dev.manufacturer_str_index = kManufacturerStringIndex;
  dev.product_str_index = kProductStrIndex;
  dev.serial_str_index = kSerialStrIndex;

  InterfaceDescriptor keyboard_itf(0, UsbClass::Hid);
  keyboard_itf.num_endpoints = 1;
  keyboard_itf.subclass = 1;
  keyboard_itf.protocol = 1;

  EndpointDescriptor ep1(EndpointAddress(EndpointNumber(1), Direction::In),
                         EndpointAttributes(EndpointType::Interrupt));
  ep1.interval = 10;
  ep1.max_packet_size = 8;

  std::array<uint8_t, 9> keyboard_hid_desc{
      0x09, // length
      0x21, // descriptor type
      0x11, // HID minor version (BCD)
      0x01, // HID major version (BCD)
      0x00, // Country code
      0x01, // Number of class descriptors
      0x22, // Class descriptor type
      0x3f, // Total size of report descriptor
      0x00, // Optional descriptor type
  };

  return StaticDescriptorMap<0, 0>()
      .add_device_descriptor(dev)
      .add_language_ids(Language::English_US)
      .add_string(
          kManufacturerStringIndex, "Adam Simpkins", Language::English_US)
      .add_string(kProductStrIndex, "Mantyl Keyboard", Language::English_US)
      .add_string(kSerialStrIndex, "00:00:00::00:00:00", Language::English_US)
      .add_config_descriptor(ConfigAttr::RemoteWakeup,
                             UsbMilliamps(50),
                             0,
                             keyboard_itf,
                             keyboard_hid_desc,
                             ep1);
}

} // namespace

class TestDevice : UsbDeviceImpl {
public:
  constexpr TestDevice() = default;

  bool init_serial() {
    auto serial_buffer = descriptors_.get_string_descriptor_buffer(
        kSerialStrIndex, Language::English_US);
    if (!serial_buffer) {
      return false;
    }

    return usb_.update_serial_number(*serial_buffer);
  }

  esp_err_t init() {
    init_serial();
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
    descriptors_.update_ep0_max_packet_size(size);
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

using namespace mantyl;

const char *LogTag = "mantyl.test";

constinit TestDevice usb;

void run_usb() {
  const auto usb_rc = usb.init();
  if (usb_rc != ESP_OK) {
    ESP_LOGE(LogTag, "failed to initialize USB: %d", usb_rc);
  }
  ESP_LOGI(LogTag, "USB initialization DONE");

  usb.loop();
}

void dump_desc(uint16_t value, uint16_t index) {
  printf("Descriptor %#x  %#x:\n", value, index);
  auto desc = usb.get_descriptor(value, index);
  if (!desc.has_value()) {
    printf("- none\n");
    return;
  }

  printf("- size: %d\n", desc->size());
  auto p = desc->data();
  size_t bytes_left = desc->size();
  while (bytes_left > 8) {
    printf("- %02x %02x %02x %02x %02x %02x %02x %02x\n",
           p[0],
           p[1],
           p[2],
           p[3],
           p[4],
           p[5],
           p[6],
           p[7]);
    p += 8;
    bytes_left -= 8;
  }
  if (bytes_left > 0) {
    printf("-");
    while (bytes_left > 0) {
      printf(" %02x", p[0]);
      ++p;
      --bytes_left;
    }
    printf("\n");
  }
}

void run_test() {
  printf("running tests:\n");
  dump_desc(0x100, 0);
  dump_desc(0x200, 0);
  dump_desc(0x300, 0);
  dump_desc(0x301, 0x0409);
  dump_desc(0x302, 0x0409);
  dump_desc(0x303, 0x0409);
}

} // namespace

extern "C" void app_main() {
  if (!usb.init_serial()) {
    ESP_LOGE(LogTag, "failed to initialize serial number");
  }
  run_test();

  while (true) {
    auto value = mantyl::readline("test> ");
    ESP_LOGI(LogTag, "line: \"%s\"", value.c_str());
    if (value == "test") {
      run_test();
    } else if (value == "usb") {
      run_usb();
    }
  }
}
