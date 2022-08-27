// Copyright (c) 2022, Adam Simpkins
#include "UsbDevice.h"

#include "App.h"

#include <esp_check.h>
#include <esp_log.h>
#include <esp_mac.h>
#include <esp_private/usb_phy.h>

namespace {
const char *LogTag = "mantyl.usb";
usb_phy_handle_t usb_phy_handle;
TaskHandle_t tusb_task_handle;

constexpr configSTACK_DEPTH_TYPE usb_task_stack_size = 4096;
constexpr UBaseType_t usb_task_priority = 5;

mantyl::UsbDevice* get_usb_dev() {
  auto* app = mantyl::App::get();
  if (!app) {
    return nullptr;
  }
  return &app->usb();
}

/**
 * @brief This top level thread processes all usb events and invokes callbacks
 */
void tusb_device_task(void *arg)
{
  auto *usb = static_cast<mantyl::UsbDevice *>(arg);
  ESP_LOGD(LogTag, "tinyusb task started");
  while (true) {
    tud_task();
    if (tud_cdc_connected() && tud_cdc_available()) {
      usb->cdc_task();
    }
  }
}

esp_err_t tusb_run_task(mantyl::UsbDevice* usb) {
  // Sanity check.  Not actually thread-safe
  ESP_RETURN_ON_FALSE(!tusb_task_handle,
                      ESP_ERR_INVALID_STATE,
                      LogTag,
                      "TinyUSB main task already started");
  xTaskCreate(tusb_device_task,
              "TinyUSB",
              usb_task_stack_size,
              usb,
              usb_task_priority,
              &tusb_task_handle);
  ESP_RETURN_ON_FALSE(
      tusb_task_handle, ESP_FAIL, LogTag, "create TinyUSB main task failed");
  return ESP_OK;
}

esp_err_t tusb_stop_task() {
  ESP_RETURN_ON_FALSE(tusb_task_handle,
                      ESP_ERR_INVALID_STATE,
                      LogTag,
                      "TinyUSB main task not started yet");
  vTaskDelete(tusb_task_handle);
  tusb_task_handle = nullptr;
  return ESP_OK;
}

esp_err_t tinyusb_driver_install(mantyl::UsbDevice* usb) {
  // Configure USB PHY
  usb_phy_config_t phy_conf = {
      .controller = USB_PHY_CTRL_OTG,
      .target = USB_PHY_TARGET_INT,
      .otg_mode = USB_OTG_MODE_DEVICE,
      .otg_speed = USB_PHY_SPEED_UNDEFINED,
      .gpio_conf = {},
  };
  ESP_RETURN_ON_ERROR(usb_new_phy(&phy_conf, &usb_phy_handle),
                      LogTag,
                      "Install USB PHY failed");
  // Yielding after usb_new_phy() and before tusb_init() appears to be
  // required for some reason.
  vTaskDelay(10);

  ESP_RETURN_ON_FALSE(
      tusb_init(), ESP_FAIL, LogTag, "Init TinyUSB stack failed");
  ESP_RETURN_ON_ERROR(tusb_run_task(usb), LogTag, "Run TinyUSB task failed");
  ESP_LOGI(LogTag, "TinyUSB Driver installed");
  return ESP_OK;
}

esp_err_t tinyusb_driver_uninstall() {
  usb_del_phy(usb_phy_handle);
  return ESP_OK;
}

char16_t hexlify_utf16(uint8_t n) {
  if (n < 10) {
    return u'0' + n;
  }
  return u'a' + (n - 10);
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
                   .idProduct = 0x9998,
                   .bcdDevice = 0x0001, // Device FW version
                   // String descriptor indices
                   .iManufacturer = add_string_literal(u"Adam Simpkins"),
                   .iProduct = add_string_literal(u"Mantyl Keyboard"),
                   .iSerialNumber = 0,
                   .bNumConfigurations = 1} {
  log_buffer_.resize(256);
}

UsbDevice::~UsbDevice() {
  if (tusb_task_handle) {
    tusb_stop_task();
  }
  if (usb_phy_handle) {
    tinyusb_driver_uninstall();
  }
}

esp_err_t UsbDevice::init() {
  ESP_LOGI(LogTag, "USB initialization");

  device_desc_.iSerialNumber = add_serial_descriptor();
  init_config_desc(true);

  ESP_ERROR_CHECK(tinyusb_driver_install(this));
  ESP_LOGI(LogTag, "USB initialization DONE");

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

uint16_t const *UsbDevice::get_string_descriptor(uint8_t index,
                                                 uint16_t langid) const {
  static_cast<void>(langid);

  if (index >= string_offsets_.size()) {
    return nullptr;
  }
  auto offset = string_offsets_[index];
  return string_data_.data() + offset;
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

uint8_t UsbDevice::add_string_literal(std::u16string_view str) {
  const auto index = string_offsets_.size();
  const auto offset = string_data_.size();
  string_offsets_.push_back(offset);

  string_data_.reserve(string_data_.size() + 1 + str.size());
  // The first byte is the descriptor length (bLength)
  // The second byte is the descriptor type (bDescriptorType): TUSB_DESC_STRING
  string_data_.push_back(
      tu_htole16((TUSB_DESC_STRING << 8) | (2 * str.size() + 2)));
  for (char16_t c : str) {
    string_data_.push_back(tu_htole16(c));
  }

  return index;
}

uint8_t UsbDevice::add_serial_descriptor() {
  std::array<uint8_t, 6> mac_bytes;
  auto rc = esp_read_mac(mac_bytes.data(), ESP_MAC_WIFI_STA);
  if (rc != ESP_OK) {
    ESP_LOGW(LogTag, "failed to get MAC: %d", rc);
    return 0;
  }

  std::array<char16_t, 14> serial;
  size_t out_idx = 0;
  for (size_t n = 0; n < mac_bytes.size(); ++n) {
    serial[out_idx] = hexlify_utf16((mac_bytes[n] >> 4) & 0xf);
    serial[out_idx + 1] = hexlify_utf16(mac_bytes[n] & 0xf);
    out_idx += 2;
    if (n == 2) {
      serial[out_idx] = u'-';
      ++out_idx;
    }
  }
  serial[out_idx] = '\0';
  assert(out_idx + 1 == serial.size());

  return ESP_OK;
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
    device_desc_.idProduct = 0x9992;
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
  add_u8(add_string_literal(u"main"));                     // iConfiguration
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
  add_u8(add_string_literal(u"Mantyl Keyboard")); // iInterface

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
    add_u8(add_string_literal(u"Mantyl Debug Console")); // iInterface

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
    add_u8(add_string_literal(u"Mantyl Debug Console Data")); // iInterface

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

void UsbDevice::cdc_task() {
    std::array<uint8_t, 64> buf;

  // read and echo back
  uint32_t count = tud_cdc_read(buf.data(), buf.size());
  if (count > 0) {
    ESP_LOGI(LogTag, "read %" PRIu32 " bytes from CDC", count);
  }
#if 0
  for (uint32_t i = 0; i < count; i++) {
    tud_cdc_write_char(buf[i]);
    if (buf[i] == '\r')
      tud_cdc_write_char('\n');
  }

  tud_cdc_write_flush();
#endif
}

void UsbDevice::debug_log(const char *format, va_list ap) {
  std::lock_guard<std::mutex> lock(log_mutex_);
  size_t len_remaining = log_buffer_.size() - log_length_;
  auto bytes_formatted =
      vsnprintf(log_buffer_.data() + log_length_, len_remaining, format, ap);
  if (bytes_formatted >= len_remaining) {
    log_length_ = log_buffer_.size();
  } else {
    log_length_ += bytes_formatted;
  }

  for (size_t n = 0; n < log_length_; ++n) {
    bool eom = false;
    if (log_buffer_[n] == '\r') {
      log_buffer_[n] = '\0';
      if (n + 1 < log_length_ && log_buffer_[n + 1] == '\n') {
        ++n;
      }
      eom = true;
    } else if (log_buffer_[n] == '\n') {
      log_buffer_[n] = '\0';
      eom = true;
    }

    if (eom) {
      if (log_buffer_[0] != '\0') {
        ESP_LOGI("tinyusb", "%s", log_buffer_.data());
      }
      if (n < log_length_) {
        log_length_ -= n;
        memmove(log_buffer_.data(), log_buffer_.data() + n, log_length_);
      } else {
        log_length_ = 0;
      }
    }
  }
}

} // namespace mantyl

extern "C" {

uint8_t const *tud_descriptor_device_cb() {
  auto usb_dev = get_usb_dev();
  if (!usb_dev) {
    return nullptr;
  }

  return usb_dev->get_device_descriptor();
}

uint8_t const *tud_descriptor_configuration_cb(uint8_t index) {
  auto usb_dev = get_usb_dev();
  if (!usb_dev) {
    return nullptr;
  }

  return usb_dev->get_config_descriptor(index);
}

uint16_t const *tud_descriptor_string_cb(uint8_t index, uint16_t langid) {
  auto usb_dev = get_usb_dev();
  if (!usb_dev) {
    return nullptr;
  }

  return usb_dev->get_string_descriptor(index, langid);
}

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

// Invoked when cdc when line state changed e.g connected/disconnected
void tud_cdc_line_state_cb(uint8_t itf, bool dtr, bool rts) {
  ESP_LOGD(LogTag, "CDC line state cb");
  static_cast<void>(itf);

  // connected
  if (dtr && rts) {
    // print initial message when connected
    tud_cdc_write_str("\r\nUSB CDC MSC device example\r\n");
  }
}

// Invoked when CDC interface received data from host
void tud_cdc_rx_cb(uint8_t itf) {
  ESP_LOGI(LogTag, "CDC rx cb");
  static_cast<void>(itf);
}

extern int mantyl_tusb_logf(const char *format, ...) {
  auto usb_dev = get_usb_dev();
  if (!usb_dev) {
    return 0;
  }

  va_list ap;
  va_start(ap, format);
  usb_dev->debug_log(format, ap);
  va_end(ap);
}

} // extern "C"
