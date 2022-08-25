// Copyright (c) 2022, Adam Simpkins
#include "UsbDevice.h"

#include <esp_check.h>
#include <esp_log.h>
#include <esp_mac.h>
#include <tinyusb.h>

namespace {
const char *LogTag = "mantyl.usb";
}

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
                   .idProduct = 0x9999,
                   .bcdDevice = 0x0001, // Device FW version
                   // String descriptor indices
                   .iManufacturer = add_string_literal("Adam Simpkins"),
                   .iProduct = add_string_literal("Mantyl Keyboard"),
                   .iSerialNumber = 0,
                   .bNumConfigurations = 1} {}

esp_err_t UsbDevice::init() {
  ESP_LOGI(LogTag, "USB initialization");

  strings_.reserve(6);
  auto rc = init_serial();
  if (rc != ESP_OK) {
      return rc;
  }
  device_desc_.iSerialNumber = add_string_literal(serial_.data());

  init_config_desc(false);

  tinyusb_config_t tusb_cfg = {
      .descriptor = &device_desc_,
      .string_descriptor = strings_.data(),
      .external_phy = false,
      .configuration_descriptor = config_desc_.data(),
  };

  ESP_ERROR_CHECK(tinyusb_driver_install(&tusb_cfg));
  ESP_LOGI(LogTag, "USB initialization DONE");

  return ESP_OK;
}

uint8_t UsbDevice::add_string_literal(const char *str) {
  const auto index = strings_.size();
  strings_.push_back(str);
  return index;
}

static char hexlify(uint8_t n) {
  if (n < 10) {
    return '0' + n;
  }
  return 'a' + (n - 10);
}

esp_err_t UsbDevice::init_serial() {
  std::array<uint8_t, 6> mac_bytes;
  auto rc = esp_read_mac(mac_bytes.data(), ESP_MAC_WIFI_STA);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to get MAC");

  size_t out_idx = 0;
  for (size_t n = 0; n < mac_bytes.size(); ++n) {
    serial_[out_idx] = hexlify((mac_bytes[n] >> 4) & 0xf);
    serial_[out_idx + 1] = hexlify(mac_bytes[n] & 0xf);
    out_idx += 2;
    if (n == 2) {
      serial_[out_idx] = '-';
      ++out_idx;
    }
  }
  serial_[out_idx] = '\0';
  assert(out_idx + 1 == serial_.size());

  return ESP_OK;
}

void UsbDevice::init_config_desc(bool debug) {
  // In theory we could expose 2 separate configurations, one which is purely a
  // HID device, and one which is HID+CDC for debugging.  However, this would
  // require custom driver logic on the host to select which configuration to
  // use if we want to switch between them.
  //
  // Additionally, the esp-idf tinyusb_driver_install() code does not currently
  // support multiple configurations.

  size_t size = TUD_CONFIG_DESC_LEN + TUD_HID_DESC_LEN;
  uint8_t num_interfaces = 1;
  if (debug) {
    ++num_interfaces;
    size += TUD_CDC_DESC_LEN;
  }

  // In practice the keyboard briefly draws around 65mA during boot, and
  // generally tends to use less than 50mA.
  constexpr int max_power_milliamps = 100;

  constexpr uint8_t endpoint_addr_hid = 1;
  // Polling interval for the HID endpoint, in USB frames
  constexpr uint8_t hid_polling_interval = 10;

  size_t idx = 0;
  auto add_u8 = [&](uint8_t value) {
    config_desc_[idx] = value;
    ++idx;
  };
  auto add_u16 = [&](uint8_t value) {
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
  add_u8(9); // bLength
  add_u8(TUSB_DESC_INTERFACE); // bDescriptorType
  add_u8(0); // bInterfaceNumber
  add_u8(0); // bAlternateSetting
  add_u8(1); // bNumEndpoints
  if (debug) {
    add_u8(TUSB_CLASS_MISC);           // bInterfaceClass
    add_u8(MISC_SUBCLASS_COMMON);      // bInterfaceSubClass
    add_u8(MISC_PROTOCOL_IAD);         // bInterfaceProtocol
  } else {
    add_u8(TUSB_CLASS_HID);            // bInterfaceClass
    add_u8(HID_SUBCLASS_BOOT);         // bInterfaceSubClass
    add_u8(HID_ITF_PROTOCOL_KEYBOARD); // bInterfaceProtocol
  }
  add_u8(add_string_literal("Mantyl Keyboard")); // iInterface

  // HID Descriptor
  add_u8(9); // bLength
  add_u8(HID_DESC_TYPE_HID); // bDescriptorType
  add_u8(0x11); // bcdHID LSB
  add_u8(0x01); // bcdHID MSB
  add_u8(0x0); // bCountryCode
  add_u8(0x01); // bNumDescriptors
  add_u8(HID_DESC_TYPE_REPORT); // bDescriptorType
  add_u16(hid_report_desc.size()); // wDescriptorLength

  // HID Endpoint Descriptor
  add_u8(7); // bLength
  add_u8(TUSB_DESC_ENDPOINT); // bDescriptorType
  add_u8(0x80 | endpoint_addr_hid); // bEndpointAddress
  add_u8(TUSB_XFER_INTERRUPT); // bmAttributes
  add_u16(hid_max_packet_size); // wMaxPacketSize
  add_u8(hid_polling_interval); // bInterval

  if (debug) {
    // Interface Association Descriptor
    add_u8(8);
  }

#if 0
  config_desc_[34] = 8; // bLength
  config_desc_[10] = TUSB_DESC_INTERFACE; // bDescriptorType
  config_desc_[11] = 0; // bInterfaceNumber
  config_desc_[12] = 0; // bAlternateSetting
  config_desc_[13] = 1; // bNumEndpoints
  config_desc_[14] = TUSB_CLASS_HID; // bInterfaceClass
  config_desc_[15] = HID_SUBCLASS_BOOT; // bInterfaceSubClass
  config_desc_[16] = HID_ITF_PROTOCOL_KEYBOARD; // bInterfaceProtocol
  config_desc_[17] = add_string_literal("Mantyl Keyboard"); // iInterface

  /* Interface Associate */\
  8, TUSB_DESC_INTERFACE_ASSOCIATION, _itfnum, 2, TUSB_CLASS_CDC, CDC_COMM_SUBCLASS_ABSTRACT_CONTROL_MODEL, CDC_COMM_PROTOCOL_NONE, 0,\

    TUD_CDC_DESCRIPTOR(ITF_NUM_CDC, 4, 0x80 | EPNUM_0_CDC_NOTIF, 8, EPNUM_0_CDC, 0x80 | EPNUM_0_CDC, CFG_TUD_CDC_EP_BUFSIZE),
  }
#endif
}

} // namespace mantyl
