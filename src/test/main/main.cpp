// Copyright (c) 2022, Adam Simpkins

#include "MockUsbDevice.h"

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

#include <optional>
#include <memory>
#include <vector>
#include <type_traits>

using namespace mantyl;

namespace {
const char *LogTag = "mantyl.test";
}

namespace mantyl {

namespace {

constexpr uint8_t kManufacturerStringIndex = 1;
constexpr uint8_t kProductStrIndex = 2;
constexpr uint8_t kSerialStrIndex = 3;

constexpr auto make_keyboard_hid_report_desc() {
  return std::array<uint8_t, 63>{
      0x05, 0x01, 0x09, 0x06, 0xa1, 0x01, 0x75, 0x01, 0x95, 0x08, 0x05,
      0x07, 0x19, 0xe0, 0x29, 0xe7, 0x15, 0x00, 0x25, 0x01, 0x81, 0x02,
      0x95, 0x01, 0x75, 0x08, 0x81, 0x03, 0x95, 0x05, 0x75, 0x01, 0x05,
      0x08, 0x19, 0x01, 0x29, 0x05, 0x91, 0x02, 0x95, 0x01, 0x75, 0x03,
      0x91, 0x03, 0x95, 0x06, 0x75, 0x08, 0x15, 0x00, 0x25, 0x91, 0x05,
      0x07, 0x19, 0x00, 0x29, 0x91, 0x81, 0x00, 0xc0,
  };
}

constexpr auto make_intf0_descriptor_map() {
  return StaticDescriptorMap<0, 0>().add_descriptor_raw(
      0x2200, 0, make_keyboard_hid_report_desc());
}

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
      static_cast<uint8_t>(DescriptorType::HidReport), // Class descriptor type
      make_keyboard_hid_report_desc().size(), // Total size of report descriptor
      0x00,                                   // Optional descriptor type
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

  bool init() {
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

} // namespace mantyl

namespace {

constinit Esp32TestDevice usb;

void run_usb() {
  if (!usb.init()) {
    ESP_LOGE(LogTag, "failed to initialize USB");
    return;
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
  MockUsbDevice::dump_hex(desc->data(), desc->size());
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

bool test_hid_init() {
  printf("Testing HID device initialization:\n");

  auto mock_usb = std::make_unique<MockUsbDevice>();
  auto usb = std::make_unique<TestDevice>(mock_usb.get());

  usb->init();

  // Get the device descriptor
  SetupPacket get_config_desc;
  get_config_desc.request_type = 0x80;
  get_config_desc.request = 6; // StdRequestType::GetDescriptor
  get_config_desc.value = 0x0100; // Device
  get_config_desc.index = 0;
  get_config_desc.length = 64;
  mock_usb->on_setup_received(get_config_desc);

  // The GetDescriptor packet should trigger the device to send the response
  if (!mock_usb->check_events(
          __FILE__, __LINE__, [&mock_usb](const MockUsbDevice::InSend &event) {
            if (event.endpoint != 0) {
              return false;
            }
            if (event.size != 18) {
              ESP_LOGE(LogTag,
                       "unexpected device descriptor buffer size: %u",
                       event.size);
              return false;
            }
            const auto* buf = event.buffer;
            if (buf[0] != 18) {
              ESP_LOGE(
                  LogTag, "unexpected device descriptor size: %u", buf[0]);
              return false;
            }
            if (buf[1] != static_cast<uint8_t>(DescriptorType::Device)) {
              ESP_LOGE(
                  LogTag, "unexpected device descriptor type: %u", buf[1]);
              MockUsbDevice::dump_hex(event.buffer, event.size);
              return false;
            }

            mock_usb->on_in_transfer_complete(0, event.size);
            return true;
          })) {
    return false;
  }

  if (!mock_usb->check_events(
          __FILE__, __LINE__, [&mock_usb](const MockUsbDevice::OutRecv &event) {
            if (event.endpoint != 0 || event.size != 0) {
              return false;
            }
            mock_usb->on_out_transfer_complete(0, 0);
            return true;
          })) {
    return false;
  }

  if (!mock_usb->check_no_events(__FILE__, __LINE__)) {
    return false;
  }

  // Linux seems to perform another reset and enumeration after getting the
  // device descriptor.

  // Set the address
  SetupPacket set_addr;
  set_addr.request_type = 0x00;
  set_addr.request = 5; // StdRequestType::SetAddress
  set_addr.value = 123; // Address
  set_addr.index = 0;
  set_addr.length = 0;
  mock_usb->on_setup_received(set_addr);

  if (!mock_usb->check_events(__FILE__,
                              __LINE__,
                              [](const MockUsbDevice::SetAddress &set_addr,
                                 const MockUsbDevice::InSend &ack) {
                                return set_addr.address == 123 &&
                                       ack.endpoint == 0 && ack.size == 0;
                              })) {
    return false;
  }

  // Linux also sends here:
  // - get device descriptor again
  // - get descriptor; value = 0x600 (DeviceQualifier)
  // - get descriptor; value = 0x600 (DeviceQualifier)
  // - get descriptor; value = 0x600 (DeviceQualifier)  (repeated 3x)

  // Get the configuration descriptor.
  // Initially only get the first 9 bytes (the length of just the config
  // descriptor itself).
  SetupPacket get_conf_desc;
  get_conf_desc.request_type = 0x80;
  get_conf_desc.request = 6; // StdRequestType::GetDescriptor
  get_conf_desc.value = 0x0200; // Configuration
  get_conf_desc.index = 0;
  get_conf_desc.length = 9; // ConfigDescriptor::kSize;
  mock_usb->on_setup_received(get_conf_desc);

  uint16_t total_conf_desc_size = 0;
  if (!mock_usb->check_in_transfer(
          __FILE__,
          __LINE__,
          0,
          [&total_conf_desc_size](const uint8_t *buf, uint16_t size) {
            if (size != 9 || buf[0] != 9 || buf[1] != 2) {
              return false;
            }
            total_conf_desc_size =
                buf[2] | (static_cast<uint16_t>(buf[3]) << 8);
            return true;
          })) {
    return false;
  }
  printf("config descriptor length: %u\n", total_conf_desc_size);

  // Now get the full config descriptor
  get_conf_desc.length = total_conf_desc_size;
  mock_usb->on_setup_received(get_conf_desc);
  uint16_t hid_report_desc_size = 0;
  if (!mock_usb->check_in_transfer(
          __FILE__, __LINE__, 0, [&](const uint8_t *buf, uint16_t size) {
            if (size != total_conf_desc_size || buf[0] != 9 || buf[1] != 2) {
              return false;
            }

            // TODO: parse the HID report descriptor out of the config
            // descriptor
            hid_report_desc_size = make_keyboard_hid_report_desc().size();

            return true;
          })) {
    return false;
  }

  // Linux host now gets the string descriptors:
  // the language IDs, followed by the product, vendor, and serial string
  // descriptors listed in the config descriptor.
  // - get descriptor: value = 0x300, index=0, length=0xff
  // - get descriptor: value = 0x302, index=0x0409, length=0xff
  // - get descriptor: value = 0x301, index=0x0409, length=0xff
  // - get descriptor: value = 0x303, index=0x0409, length=0xff

  // Set the configuration
  SetupPacket set_conf;
  set_conf.request_type = 0x00;
  set_conf.request = 9; // StdRequestType::SetConfiguration
  set_conf.value = 1;
  set_conf.index = 0;
  set_conf.length = 0;
  mock_usb->on_setup_received(set_conf);
  if (!mock_usb->check_events(
          __FILE__, __LINE__, [](const MockUsbDevice::InSend &ack) {
            return ack.endpoint == 0 && ack.size == 0;
          })) {
    return false;
  }

  // Linux appears to get the serial number again here.
  // - get descriptor: value = 0x303, index=0x0409, length=0xff

  // HID set idle: req_type=0x21, req=0x0a, value=0, index=0, len=0
  SetupPacket set_idle;
  set_idle.request_type = 0x21;
  set_idle.request = 0x0a; // HidRequest::SetIdle
  set_idle.value = 0;
  set_idle.index = 0;
  set_idle.length = 0;
  mock_usb->on_setup_received(set_idle);
  if (!mock_usb->check_events(
          __FILE__, __LINE__, [](const MockUsbDevice::InSend &ack) {
            return ack.endpoint == 0 && ack.size == 0;
          })) {
    return false;
  }

  // Now a GetDescriptor request to the HID interface to get the HID descriptor
  SetupPacket get_hid_desc;
  get_hid_desc.request_type = 0x81;
  get_hid_desc.request = 6; // StdRequestType::GetDescriptor
  get_hid_desc.value = 0x2200; // HidReport
  get_hid_desc.index = 0;
  get_hid_desc.length = hid_report_desc_size;
  mock_usb->on_setup_received(get_hid_desc);
  if (!mock_usb->check_in_transfer(
          __FILE__, __LINE__, 0, [&](const uint8_t *buf, uint16_t size) {
            return size == hid_report_desc_size;
          })) {
    return false;
  }

  // Now a SetReport request to send the keyboard LED states
  SetupPacket set_leds;
  set_leds.request_type = 0x21;
  set_leds.request = 0x09; // HidRequest::SetReport
  set_leds.value = 0x0200;
  set_leds.index = 0;
  set_leds.length = 1;
  mock_usb->on_setup_received(set_leds);
  uint8_t led_state = 0;
  if (!mock_usb->drive_out_transfer(
          __FILE__, __LINE__, 0, &led_state, sizeof(led_state))) {
    return false;
  }

  printf("HID Device Initialization test successful\n");
  return true;
}

bool run_tests() {
  printf("Running tests:\n");

  if (!test_hid_init()) {
    ESP_LOGE(LogTag, "failed HID device initialization test");
  }

  printf("Tests finished\n");
  return true;
}

} // namespace

extern "C" void app_main() {
  if (!usb.init_serial()) {
    ESP_LOGE(LogTag, "failed to initialize serial number");
  }
  dump_descriptors();
  run_tests();

  while (true) {
    auto value = mantyl::readline("test> ");
    ESP_LOGI(LogTag, "line: \"%s\"", value.c_str());
    if (value == "test") {
      run_tests();
    } else if (value == "desc") {
      dump_descriptors();
    } else if (value == "usb") {
      run_usb();
    }
  }
}
