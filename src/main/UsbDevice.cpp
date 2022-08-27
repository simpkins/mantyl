// Copyright (c) 2022, Adam Simpkins
#include "UsbDevice.h"

#include "App.h"

#include <esp_check.h>
#include <esp_log.h>
#include <esp_mac.h>
#include <tusb_cdc_acm.h>
#include <tusb_console.h>

namespace {
const char *LogTag = "mantyl.usb";

mantyl::UsbDevice* get_usb_dev() {
  auto* app = mantyl::App::get();
  if (!app) {
    return nullptr;
  }
  return &app->usb();
}

char hexlify(uint8_t n) {
  if (n < 10) {
    return '0' + n;
  }
  return 'a' + (n - 10);
}

void on_cdc_rx(int itf, cdcacm_event_t *event) {
  static_cast<void>(event);
  auto usb_dev = get_usb_dev();
  if (!usb_dev) {
    return;
  }

  // Call tinyusb_cdcacm_read() whenever there is data to read, to stop the
  // esp-idf code from logging warnings about its rx buffer filling up.
  std::vector<uint8_t> buf;
  buf.resize(64);
  while (true) {
    size_t rx_size = 0;
    auto rc = tinyusb_cdcacm_read(static_cast<tinyusb_cdcacm_itf_t>(itf),
                                  buf.data(),
                                  buf.size(),
                                  &rx_size);
    if (rc == ESP_OK) {
      if (rx_size == 0) {
        break;
      }
      // Simply ignore the data for now.
    } else if (rc == ESP_ERR_NO_MEM) {
      // This simply indicates that there isn't actually any data to read right
      // now.
    } else {
      ESP_LOGE(LogTag, "CDC read error: %d", rc);
      break;
    }
  }
}

void on_cdc_line_state_change(int itf, cdcacm_event_t *event) {
  static_cast<void>(itf);
  auto usb_dev = get_usb_dev();
  if (!usb_dev) {
    return;
  }

  const auto& data = event->line_state_changed_data;
  ESP_LOGI(
      LogTag, "CDC line state changed: dtr=%d, rts=%d", data.dtr, data.rts);
}

} // namespace

namespace mantyl {

UsbDevice::UsbDevice()
    : device_desc_{.bLength = sizeof(device_desc_),
                   .bDescriptorType = TUSB_DESC_DEVICE,
                   .bcdUSB = 0x0200, // USB version. 0x0200 means version 2.0
                   .bDeviceClass = TUSB_CLASS_HID,
                   .bDeviceSubClass = 1, // Boot
                   .bDeviceProtocol = 1, // Keyboard
                   .bMaxPacketSize0 = CFG_TUD_ENDPOINT0_SIZE,
                   .idVendor = 0x303A, // Espressif's Vendor ID
                   .idProduct = 0x9990,
                   .bcdDevice = 0x0001, // Device FW version
                   // String descriptor indices
                   .iManufacturer = add_string_literal("Adam Simpkins"),
                   .iProduct = add_string_literal("Mantyl Keyboard"),
                   .iSerialNumber = 0,
                   .bNumConfigurations = 1} {}

UsbDevice::~UsbDevice() = default;

esp_err_t UsbDevice::init() {
  ESP_LOGI(LogTag, "USB initialization");

  bool enable_cdc = true;

  device_desc_.iSerialNumber = add_serial_descriptor();
  init_config_desc(enable_cdc);

  tinyusb_config_t config{
      .device_descriptor = &device_desc_,
      .string_descriptor = strings_.data(),
      .external_phy = false,
      .configuration_descriptor = config_desc_.data(),
  };
  ESP_ERROR_CHECK(tinyusb_driver_install(&config));
  ESP_LOGI(LogTag, "USB initialization DONE");

  if (enable_cdc) {
    tinyusb_config_cdcacm_t acm_cfg = {.usb_dev = TINYUSB_USBDEV_0,
                                       .cdc_port = TINYUSB_CDC_ACM_0,
                                       .rx_unread_buf_sz = 64,
                                       .callback_rx = on_cdc_rx,
                                       .callback_rx_wanted_char = nullptr,
                                       .callback_line_state_changed =
                                           on_cdc_line_state_change,
                                       .callback_line_coding_changed = nullptr};
    ESP_ERROR_CHECK(tusb_cdc_acm_init(&acm_cfg));
    esp_tusb_init_console(TINYUSB_CDC_ACM_0);
  }

  return ESP_OK;
}

uint8_t const *UsbDevice::get_device_descriptor() const {
  // This is not a violation of C++ strict aliasing rules, since they
  // explicitly allow access via char pointers.
  return reinterpret_cast<uint8_t const *>(&device_desc_);
}

uint8_t const *UsbDevice::get_config_descriptor(uint8_t index) const {
  // We only have a single configuration.
  // In theory we could expose 2 separate configurations, one which is purely a
  // HID device, and one which is HID+CDC for debugging.  However, this would
  // require custom driver logic on the host to select which configuration to
  // use if we want to switch between them.
  static_cast<void>(index);

  return config_desc_.data();
}

uint8_t const *UsbDevice::get_hid_report_descriptor(uint8_t instance) {
  static_cast<void>(instance);
  return keyboard_report_desc_.data();
}

uint16_t UsbDevice::on_hid_get_report(uint8_t instance,
                                      uint8_t report_id,
                                      hid_report_type_t report_type,
                                      uint8_t *buffer,
                                      uint16_t reqlen) {
  static_cast<void>(report_id);

  if (instance == kbd_interface_num_) {
    if (reqlen < 8) {
      // Report size is 8; can't return a report if reqlen is less than that.
      return 0;
    }

    // TODO: return the keyboard report
    static_cast<void>(report_type);
    memset(buffer, 0, 8);
    return 8;
  }

  return 0;
}

void UsbDevice::on_hid_set_report(uint8_t instance,
                                  uint8_t report_id,
                                  hid_report_type_t report_type,
                                  uint8_t const *buffer,
                                  uint16_t bufsize) {
  static_cast<void>(report_id);

  // Keyboard interface
  if (instance == kbd_interface_num_) {
    // Set keyboard LED e.g Capslock, Numlock etc...
    if (report_type == HID_REPORT_TYPE_OUTPUT) {
      // bufsize should be (at least) 1
      if (bufsize < 1) {
        return;
      }

      const uint8_t kbd_leds = buffer[0];
      printf("new LED value: %#04x\n", kbd_leds);
    }
  }
}

uint8_t UsbDevice::add_string_literal(const char* str) {
  const auto index = strings_.size();
  if (index >= 0xff) {
    return 0;
  }
  strings_.push_back(str);
  return index;
}

uint8_t UsbDevice::add_serial_descriptor() {
  std::array<uint8_t, 6> mac_bytes;
  auto rc = esp_read_mac(mac_bytes.data(), ESP_MAC_WIFI_STA);
  if (rc != ESP_OK) {
    ESP_LOGW(LogTag, "failed to get MAC: %d", rc);
    return 0;
  }

  size_t out_idx = 0;
  for (size_t n = 0; n < mac_bytes.size(); ++n) {
    serial_[out_idx] = hexlify((mac_bytes[n] >> 4) & 0xf);
    serial_[out_idx + 1] = hexlify(mac_bytes[n] & 0xf);
    out_idx += 2;
    if (n == 2) {
      serial_[out_idx] = u'-';
      ++out_idx;
    }
  }
  serial_[out_idx] = '\0';
  assert(out_idx + 1 == serial_.size());

  return add_string_literal(serial_.data());
}

void UsbDevice::init_config_desc(bool debug) {
  size_t size = TUD_CONFIG_DESC_LEN + TUD_HID_DESC_LEN;
  uint8_t num_interfaces = 1;
  if (debug) {
    num_interfaces += 2;
    size += TUD_CDC_DESC_LEN;

    // Change the product number when enabling the debug interface.
    // USB Hosts will generally cache the descriptors for a given
    // (vendor ID + product ID), so if we want to use a different product ID
    // when for the alternate descriptor contents.
    device_desc_.idProduct = 0x9991;
    device_desc_.bDeviceClass = TUSB_CLASS_MISC;
    device_desc_.bDeviceSubClass = MISC_SUBCLASS_COMMON;
    device_desc_.bDeviceProtocol = MISC_PROTOCOL_IAD;
  }

  // In practice the keyboard briefly draws around 65mA during boot, and
  // generally tends to use less than 50mA.
  constexpr int max_power_milliamps = 100;

  // Polling interval for the HID endpoint, in USB frames
  constexpr uint8_t kbd_polling_interval = 10;
  constexpr uint8_t kbd_max_packet_size = 8;

  size_t idx = 0;
  auto add_u8 = [&](uint8_t value) {
    config_desc_[idx] = value;
    ++idx;
  };
  auto add_u16 = [&](uint16_t value) {
    config_desc_[idx] = (value & 0xff);
    config_desc_[idx + 1] = ((value >> 8) & 0xff);
    idx += 2;
  };

  config_desc_.resize(size);
  add_u8(TUD_CONFIG_DESC_LEN);     // bLength
  add_u8(TUSB_DESC_CONFIGURATION); // bDescriptorType
  add_u16(size);                   // wTotalLength
  add_u8(num_interfaces); // bNumInterfaces
  add_u8(1);              // bConfigurationValue
  add_u8(add_string_literal("main"));                     // iConfiguration
  add_u8(TU_BIT(7) | TUSB_DESC_CONFIG_ATT_REMOTE_WAKEUP); // bmAttributes
  add_u8(max_power_milliamps / 2);                        // bMaxPower

  // HID Interface Descriptor
  add_u8(9);                   // bLength
  add_u8(TUSB_DESC_INTERFACE); // bDescriptorType
  add_u8(kbd_interface_num_);  // bInterfaceNumber
  add_u8(0);                   // bAlternateSetting
  add_u8(1);                   // bNumEndpoints
  add_u8(TUSB_CLASS_HID);      // bInterfaceClass
  add_u8(HID_SUBCLASS_BOOT);   // bInterfaceSubClass
  add_u8(HID_ITF_PROTOCOL_KEYBOARD);             // bInterfaceProtocol
  add_u8(add_string_literal("Mantyl Keyboard")); // iInterface

  init_hid_report_descriptors();

  // HID Descriptor
  add_u8(9);                             // bLength
  add_u8(HID_DESC_TYPE_HID);             // bDescriptorType
  add_u8(0x11);                          // bcdHID LSB
  add_u8(0x01);                          // bcdHID MSB
  add_u8(0x0);                           // bCountryCode
  add_u8(0x01);                          // bNumDescriptors
  add_u8(HID_DESC_TYPE_REPORT);          // bDescriptorType
  add_u16(keyboard_report_desc_.size()); // wDescriptorLength

  // HID Endpoint Descriptor
  add_u8(7); // bLength
  add_u8(TUSB_DESC_ENDPOINT);        // bDescriptorType
  add_u8(0x80 | kbd_endpoint_addr_); // bEndpointAddress
  add_u8(TUSB_XFER_INTERRUPT);       // bmAttributes
  add_u16(kbd_max_packet_size);      // wMaxPacketSize
  add_u8(kbd_polling_interval);      // bInterval

  if (debug) {
    // Interface Association Descriptor
    add_u8(8);                                        // bLength
    add_u8(TUSB_DESC_INTERFACE_ASSOCIATION);          // bDescriptorType
    add_u8(cdc_interface_num_);                       // bFirstInterface
    add_u8(2);                                        // bInterfaceCount
    add_u8(TUSB_CLASS_CDC);                           // bFunctionClass
    add_u8(CDC_COMM_SUBCLASS_ABSTRACT_CONTROL_MODEL); // bFunctionSubClass
    add_u8(CDC_COMM_PROTOCOL_NONE);                   // bFunctionProtocol
    add_u8(0);                                        // iFunction

    // CDC Control Interface
    add_u8(9);                   // bLength
    add_u8(TUSB_DESC_INTERFACE); // bDescriptorType
    add_u8(cdc_interface_num_);  // bInterfaceNumber
    add_u8(0);                   // bAlternateSetting
    add_u8(1);                   // bNumEndpoints
    add_u8(TUSB_CLASS_CDC);      // bInterfaceClass
    add_u8(CDC_COMM_SUBCLASS_ABSTRACT_CONTROL_MODEL); // bInterfaceSubClass
    add_u8(CDC_COMM_PROTOCOL_NONE);                   // bInterfaceProtocol
    add_u8(add_string_literal("Mantyl Debug Console")); // iInterface

    // CDC Header Functional Descriptor
    add_u8(5);                      // bLength
    add_u8(TUSB_DESC_CS_INTERFACE); // bDescriptorType
    add_u8(CDC_FUNC_DESC_HEADER);   // bDescriptorSubType
    add_u16(0x0120);                // bcdCDC

    // CDC Call Management Functional Descriptor
    add_u8(5);                      // bLength
    add_u8(TUSB_DESC_CS_INTERFACE); // bDescriptorType
    add_u8(CDC_FUNC_DESC_CALL_MANAGEMENT);   // bDescriptorSubType
    add_u8(0);                               // bmCapabilities
    add_u8(cdc_data_interface_num_);         // bDataInterface

    // CDC Abstract Control Management
    add_u8(4);                      // bLength
    add_u8(TUSB_DESC_CS_INTERFACE); // bDescriptorType
    add_u8(CDC_FUNC_DESC_ABSTRACT_CONTROL_MANAGEMENT); // bDescriptorSubType
    add_u8(2);                                         // bmCapabilities

    // CDC Union
    add_u8(5);                       // bLength
    add_u8(TUSB_DESC_CS_INTERFACE);  // bDescriptorType
    add_u8(CDC_FUNC_DESC_UNION);     // bDescriptorSubType
    add_u8(cdc_interface_num_);      // bControlInterface
    add_u8(cdc_data_interface_num_); // bSubordinateInterface0

    // Notification endpoint
    add_u8(7);                        // bLength
    add_u8(TUSB_DESC_ENDPOINT);       // bDescriptorType
    add_u8(0x80 | cdc_notif_endpoint_addr_); // bEndpointAddress
    add_u8(TUSB_XFER_INTERRUPT);             // bmAttributes
    add_u16(8);                              // wMaxPacketSize
    add_u8(16);                              // bInterval

    // CDC Data Interface
    add_u8(9);                             // bLength
    add_u8(TUSB_DESC_INTERFACE);           // bDescriptorType
    add_u8(cdc_data_interface_num_);       // bInterfaceNumber
    add_u8(0);                             // bAlternateSetting
    add_u8(2);                             // bNumEndpoints
    add_u8(TUSB_CLASS_CDC_DATA);           // bInterfaceClass
    add_u8(0);      // bInterfaceSubClass
    add_u8(0);         // bInterfaceProtocol
    add_u8(add_string_literal("Mantyl Debug Console Data")); // iInterface

    // Data Out Endpoint
    add_u8(7);                       // bLength
    add_u8(TUSB_DESC_ENDPOINT);      // bDescriptorType
    add_u8(cdc_data_endpoint_addr_); // bEndpointAddress
    add_u8(TUSB_XFER_BULK);          // bmAttributes
    add_u16(CFG_TUD_CDC_EP_BUFSIZE); // wMaxPacketSize
    add_u8(0);                       // bInterval

    // Data In Endpoint
    add_u8(7);                              // bLength
    add_u8(TUSB_DESC_ENDPOINT);             // bDescriptorType
    add_u8(0x80 | cdc_data_endpoint_addr_); // bEndpointAddress
    add_u8(TUSB_XFER_BULK);                 // bmAttributes
    add_u16(CFG_TUD_CDC_EP_BUFSIZE);        // wMaxPacketSize
    add_u8(0);                              // bInterval
  }
}

void UsbDevice::init_hid_report_descriptors() {
  keyboard_report_desc_ = std::vector<uint8_t>{
      TUD_HID_REPORT_DESC_KEYBOARD(HID_REPORT_ID(kbd_report_id_))};
}

} // namespace mantyl

extern "C" {

uint16_t tud_hid_get_report_cb(uint8_t instance,
                               uint8_t report_id,
                               hid_report_type_t report_type,
                               uint8_t *buffer,
                               uint16_t reqlen) {
  auto usb_dev = get_usb_dev();
  if (!usb_dev) {
    return 0;
  }

  return usb_dev->on_hid_get_report(
      instance, report_id, report_type, buffer, reqlen);
}

void tud_hid_set_report_cb(uint8_t instance,
                                      uint8_t report_id,
                                      hid_report_type_t report_type,
                                      uint8_t const *buffer,
                                      uint16_t bufsize) {
  auto usb_dev = get_usb_dev();
  if (!usb_dev) {
    return;
  }

  usb_dev->on_hid_set_report(instance, report_id, report_type, buffer, bufsize);
}

uint8_t const *tud_hid_descriptor_report_cb(uint8_t instance) {
  auto usb_dev = get_usb_dev();
  if (!usb_dev) {
    return nullptr;
  }

  return usb_dev->get_hid_report_descriptor(instance);
}

} // extern "C"
