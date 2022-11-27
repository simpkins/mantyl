// Copyright (c) 2022, Adam Simpkins

#include "mantyl_readline.h"
#include "mantyl_usb/CtrlInTransfer.h"
#include "mantyl_usb/CtrlOutTransfer.h"
#include "mantyl_usb/Descriptors.h"
#include "mantyl_usb/Esp32UsbDevice.h"
#include "mantyl_usb/StaticDescriptorMap.h"
#include "mantyl_usb/UsbDescriptorMap.h"
#include "mantyl_usb/hid.h"

#include <esp_check.h>
#include <esp_log.h>

#include <memory>

using namespace mantyl;

namespace {
const char *LogTag = "mantyl.test";
}

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

constexpr auto make_intf0_descriptor_map() {
  std::array<uint8_t, 63> keyboard_hid_report_desc{
      0x05, 0x01, 0x09, 0x06, 0xa1, 0x01, 0x75, 0x01, 0x95, 0x08, 0x05,
      0x07, 0x19, 0xe0, 0x29, 0xe7, 0x15, 0x00, 0x25, 0x01, 0x81, 0x02,
      0x95, 0x01, 0x75, 0x08, 0x81, 0x03, 0x95, 0x05, 0x75, 0x01, 0x05,
      0x08, 0x19, 0x01, 0x29, 0x05, 0x91, 0x02, 0x95, 0x01, 0x75, 0x03,
      0x91, 0x03, 0x95, 0x06, 0x75, 0x08, 0x15, 0x00, 0x25, 0x91, 0x05,
      0x07, 0x19, 0x00, 0x29, 0x91, 0x81, 0x00, 0xc0,
  };
  return StaticDescriptorMap<0, 0>().add_descriptor_raw(
      0x2200, 0, keyboard_hid_report_desc);
}

} // namespace

class TestDevice : protected UsbDeviceImpl {
public:
  constexpr explicit TestDevice(UsbDevice* usb) : usb_{usb} {
    usb_->setImpl(this);
  }

  bool init_serial() {
    auto serial_buffer = descriptors_.get_string_descriptor_buffer(
        kSerialStrIndex, Language::English_US);
    if (!serial_buffer) {
      return false;
    }

    return Esp32UsbDevice::update_serial_number(*serial_buffer);
  }

  esp_err_t init() {
    init_serial();
    return usb_->init();
  }
  void loop() {
    return usb_->loop();
  }

  std::optional<buf_view> get_descriptor(uint16_t value,
                                         uint16_t index) override {
    return descriptors_.get_descriptor(value, index);
  }
  uint8_t on_enumerated(uint8_t size) override {
    descriptors_.update_ep0_max_packet_size(size);
    return size;
  }
  void on_suspend() override {}
  bool on_configured(uint8_t config_id) override {
    return true;
  }

  void handle_ep0_interface_in(uint8_t interface,
                               const SetupPacket &packet,
                               CtrlInTransfer &&xfer) override {
    if (interface == 0) {
      if (packet.get_request_type() == SetupReqType::Standard) {
        return handle_std_in_request(packet, std::move(xfer));
      } else if (packet.get_request_type() == SetupReqType::Class) {
        return handle_hid_in_request(packet, std::move(xfer));
      } else {
        ESP_LOGW(
            LogTag,
            "unsupported setup request type for IN request to interface %d",
            interface);
        return xfer.stall();
      }
    }

    ESP_LOGW(LogTag, "control IN request to unknown interface %d", interface);
    return xfer.stall();
  }

  void handle_ep0_interface_out(uint8_t interface,
                                const SetupPacket &packet,
                                CtrlOutTransfer &&xfer) override {
    if (interface == 0) {
      if (packet.get_request_type() == SetupReqType::Class) {
        handle_hid_out_request(packet, std::move(xfer));
      } else {
        ESP_LOGW(
            LogTag,
            "unsupported setup request type for OUT request to interface %d",
            interface);
      }
    } else {
      ESP_LOGW(
          LogTag, "control OUT request to unknown interface %d", interface);
    }
  }

  void handle_std_in_request(const SetupPacket &packet, CtrlInTransfer &&xfer) {
    const auto std_req_type = packet.get_std_request();
    if (std_req_type == StdRequestType::GetDescriptor) {
      handle_intf0_get_descriptor(packet, std::move(xfer));
    } else {
      ESP_LOGW(LogTag, "unhandled standard interface IN request");
      xfer.stall();
    }
  }

  void handle_intf0_get_descriptor(const SetupPacket &packet,
                                   CtrlInTransfer &&xfer) {
    ESP_LOGI(LogTag,
             "USB: get interface descriptor: value=0x%x index=%u",
             packet.value,
             packet.index);
    auto desc =
        interface0_descriptors_.get_descriptor(packet.value, packet.index);
    if (!desc.has_value()) {
      // No descriptor with this ID.
      ESP_LOGW(
          LogTag,
          "USB: query for unknown interface descriptor: value=0x%x index=%u",
          packet.value,
          packet.index);
      return xfer.stall();
    }

    return xfer.send_response_async(*desc);
  }

  void handle_hid_in_request(const SetupPacket &packet, CtrlInTransfer &&xfer) {
    ESP_LOGW(LogTag, "unhandled HID interface IN request");
    xfer.stall();
  }

  void handle_hid_out_request(const SetupPacket &packet,
                              CtrlOutTransfer &&xfer) {
    auto request = static_cast<HidRequest>(packet.request);

    if (request == HidRequest::SetIdle) {
      const uint8_t duration = (packet.request >> 8) & 0xff;
      const uint8_t report_id = packet.request & 0xff;
      ESP_LOGI(LogTag,
               "Set HID Idle period for report %d to %d",
               report_id,
               duration);
      xfer.ack();
    } else if (request == HidRequest::SetReport) {
      // Start reading the SET_REPORT data.
      set_report_xfer_.start(std::move(xfer));
      return;
    } else {
      ESP_LOGW(LogTag, "unhandled HID interface OUT request");
    }
  }

  void handle_ep0_endpoint_in(uint8_t endpoint,
                              const SetupPacket &packet,
                              CtrlInTransfer &&xfer) override {
    ESP_LOGW(LogTag, "unhandled endpoint IN request");
    xfer.stall();
  }
  void handle_ep0_endpoint_out(uint8_t endpoint,
                               const SetupPacket &packet,
                               CtrlOutTransfer &&xfer) override {
    ESP_LOGW(LogTag, "unhandled endpoint OUT request");
    xfer.stall();
  }

private:
  class SetReportTransfer {
  public:
    constexpr explicit SetReportTransfer(TestDevice *device)
        : device_{device} {}

    void start(CtrlOutTransfer&& xfer) {
      // TODO
      ESP_LOGE(LogTag, "todo: implement SET_REPORT code");
      xfer.stall();
    }

    void reset();

#if 0
  void on_set_report_complete(CtrlOutTransfer &&xfer, size_t size_read) {
    ESP_LOGI(LogTag, "received SET_REPORT data");
    xfer.ack();
    set_report_xfer_.reset();
  }
#endif

#if 0
      // For keyboards, the report is generally to set the LEDs.
      if (packet.length > set_report_buffer_.size()) {
        ESP_LOGE(
            LogTag, "too large HID SET_REPORT received: %d", request.length);
        xfer.stall();
        return;
      }

      std::move(xfer).recv(set_report_buffer_.data(),
                           set_report_buffer_.size(),
                           on_set_report_complete);
#endif

  private:
    CtrlOutTransfer xfer_;
    TestDevice* device_;
  };

  UsbDevice *usb_{nullptr};
  decltype(make_descriptor_map()) descriptors_ = make_descriptor_map();
  decltype(make_intf0_descriptor_map()) interface0_descriptors_ =
      make_intf0_descriptor_map();

  SetReportTransfer set_report_xfer_{this};
};

class Esp32TestDevice : public TestDevice {
public:
  constexpr Esp32TestDevice() : TestDevice(&esp32_usb_) {}

private:
  Esp32UsbDevice esp32_usb_{this};
};

class MockUsbDevice : public UsbDevice {
public:
  [[nodiscard]] bool init() override {
    // TODO
    return true;
  }

  void loop() override {
    // TODO
  }

private:
  void set_address(uint8_t address) override {
    // TODO
  }
  void stall_in_endpoint(uint8_t endpoint_num) override {
    // TODO
  }
  void stall_out_endpoint(uint8_t endpoint_num) override {
    // TODO
  }
  void clear_in_stall(uint8_t endpoint_num) override {
    // TODO
  }
  void clear_out_stall(uint8_t endpoint_num) override {
    // TODO
  }
  void start_in_send(uint8_t endpoint_num,
                     const uint8_t *buffer,
                     uint16_t size) override {
    // TODO
  }
  void start_out_read(uint8_t endpoint_num,
                      uint8_t *buffer,
                      uint16_t buffer_size) override {
    // TODO
  }
  void close_all_endpoints() override {
    // TODO
  }
};

} // namespace mantyl

namespace {

constinit Esp32TestDevice usb;

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

void dump_descriptors() {
  printf("USB Descriptors:\n");
  dump_desc(0x100, 0);
  dump_desc(0x200, 0);
  dump_desc(0x300, 0);
  dump_desc(0x301, 0x0409);
  dump_desc(0x302, 0x0409);
  dump_desc(0x303, 0x0409);
}

void run_test() {
  printf("Running tests:\n");

  auto mock_usb = std::make_unique<MockUsbDevice>();
  auto usb = std::make_unique<TestDevice>(mock_usb.get());

  usb->init();

  printf("Tests done\n");
}

} // namespace

extern "C" void app_main() {
  if (!usb.init_serial()) {
    ESP_LOGE(LogTag, "failed to initialize serial number");
  }
  dump_descriptors();
  run_test();

  while (true) {
    auto value = mantyl::readline("test> ");
    ESP_LOGI(LogTag, "line: \"%s\"", value.c_str());
    if (value == "test") {
      run_test();
    } else if (value == "desc") {
      dump_descriptors();
    } else if (value == "usb") {
      run_usb();
    }
  }
}
