// Copyright (c) 2022, Adam Simpkins
#include "mantyl_usb/UsbDescriptorMap.h"

#include "mantyl_usb/usb_types.h"

#include <array>

namespace mantyl {

namespace {
constexpr std::array<uint8_t, 18> s_device_descriptor{{
    0x12, // length
    0x01, // descriptor type: device
    0x00, 0x02, // USB version
    0x00, // class
    0x00, // subclass
    0x00, // protocol
    0x40, // endpoint 0 size
    0xc0, 0x16, // vendor ID (little-endian)
    0xff, 0x03, // device ID (little-endian)
    0x00, 0x01, // dev version
    0x01, // manufacturer str index
    0x02, // product str index
    0x03, // serial str index
    0x01, // num configs
}};

constexpr std::array<uint8_t, 59> s_config_descriptor{{
    0x09, // descriptor length
    static_cast<uint8_t>(DescriptorType::Config),
    0x3b, 0x00, // total length
    0x02, // num interfaces
    0x01, // configuration value
    0x00, // index of string descriptor describing this config
    0x85, // attributes: remote wakeup
    0x32, // max power, in 2mA units
    0x09, // interface 0 descriptor length
    static_cast<uint8_t>(DescriptorType::Interface),
    0x00, // interface number
    0x00, // alternate setting
    0x01, // number of endpoints
    0x03, // interface class
    0x01, // interface subclass
    0x01, // interface protocol
    0x00, // index of string descriptor describing this interface
    0x09, // descriptor length
    static_cast<uint8_t>(DescriptorType::Hid),
    0x11,
    0x01,
    0x00,
    0x01,
    0x22,
    0x3f,
    0x00,
    0x07, // descriptor length
    static_cast<uint8_t>(DescriptorType::Endpoint),
    0x81, // endpoint address
    0x03, // endpoint attributes: interrupt
    0x08, 0x00, // max packet size
    0x0a, // interval
    0x09, // descriptor length
    static_cast<uint8_t>(DescriptorType::Interface),
    0x01, // interface number
    0x00, // alternate setting
    0x01, // number of endpoints
    0x03, // interface class
    0x00, // interface subclass
    0x00, // interface protocol
    0x00, // index of string descriptor describing this interface
    0x09, // descriptor length
    static_cast<uint8_t>(DescriptorType::Hid),
    0x11,
    0x01,
    0x00,
    0x01,
    0x22,
    0x1b,
    0x00,
    0x07, // descriptor length
    static_cast<uint8_t>(DescriptorType::Endpoint),
    0x82, // endpoint address
    0x03, // endpoint attributes: interrupt
    0x20, 0x00, // max packet size
    0x01, // interval
}};

constexpr std::array<uint8_t, 63> s_kbd_hid_report{{
    0x05, 0x01, 0x09, 0x06, 0xa1, 0x01, 0x75, 0x01, 0x95, 0x08, 0x05,
    0x07, 0x19, 0xe0, 0x29, 0xe7, 0x15, 0x00, 0x25, 0x01, 0x81, 0x02,
    0x95, 0x01, 0x75, 0x08, 0x81, 0x03, 0x95, 0x05, 0x75, 0x01, 0x05,
    0x08, 0x19, 0x01, 0x29, 0x05, 0x91, 0x02, 0x95, 0x01, 0x75, 0x03,
    0x91, 0x03, 0x95, 0x06, 0x75, 0x08, 0x15, 0x00, 0x25, 0x91, 0x05,
    0x07, 0x19, 0x00, 0x29, 0x91, 0x81, 0x00, 0xc0,
}};

constexpr std::array<uint8_t, 63> s_dbg_hid_report{{
    0x06, 0x31, 0xff, 0x09, 0x74, 0xa1, 0x53, 0x75, 0x08,
    0x15, 0x00, 0x26, 0xff, 0x00, 0x95, 0x20, 0x09, 0x75,
    0x81, 0x02, 0x09, 0x76, 0x95, 0x01, 0xb1, 0x00, 0xc0,
}};

constexpr std::array<uint8_t, 4> s_language_ids{{
    4,
    static_cast<uint8_t>(DescriptorType::String),
    0x09,
    0x04,
}};

constexpr std::array<uint8_t, 18> s_manufacturer{{
    18,
    static_cast<uint8_t>(DescriptorType::String),
    0x53, 0x00, 0x69, 0x00, 0x6d, 0x00, 0x70, 0x00,
    0x6b, 0x00, 0x69, 0x00, 0x6e, 0x00, 0x73, 0x00,
}};

constexpr std::array<uint8_t, 24> s_product{{
    24,
    static_cast<uint8_t>(DescriptorType::String),
    0x4b, 0x00, 0x65, 0x00, 0x79, 0x00, 0x62, 0x00,
    0x6f, 0x00, 0x61, 0x00, 0x72, 0x00, 0x64, 0x00,
    0x20, 0x00, 0x76, 0x00, 0x32, 0x00,
}};

constexpr std::array<uint8_t, 20> s_serial{{
    20,
    static_cast<uint8_t>(DescriptorType::String),
    0x4b, 0x00, 0x42, 0x00, 0x44, 0x00, 0x32, 0x00,
    0x2d, 0x00, 0x30, 0x00, 0x30, 0x00, 0x30, 0x00,
    0x32, 0x00,
}};

constexpr uint16_t desc_value(DescriptorType type, uint8_t index) {
  return (static_cast<uint16_t>(type) << 8) | index;
}
}

std::optional<buf_view> UsbDescriptorMap::get_descriptor(uint16_t value,
                                                         uint16_t index) {
  const auto language_id = index;

  if (value == desc_value(DescriptorType::Device, 0) &&
      language_id == 0) {
    return buf_view(s_device_descriptor.data(), s_device_descriptor.size());
  } else if (value == desc_value(DescriptorType::Config, 0) &&
             language_id == 0) {
    return buf_view(s_config_descriptor.data(), s_config_descriptor.size());
  } else if (value == desc_value(DescriptorType::HidReport, 0) &&
             language_id == 0) {
    return buf_view(s_kbd_hid_report.data(), s_kbd_hid_report.size());
  } else if (value == desc_value(DescriptorType::HidReport, 1) &&
             language_id == 0) {
    return buf_view(s_dbg_hid_report.data(), s_dbg_hid_report.size());
  } else if (value == desc_value(DescriptorType::String, 0) &&
             language_id == 0) {
    return buf_view(s_language_ids.data(), s_language_ids.size());
  } else if (value == desc_value(DescriptorType::String, 1) &&
             language_id == 0x0409) {
    return buf_view(s_manufacturer.data(), s_manufacturer.size());
  } else if (value == desc_value(DescriptorType::String, 2) &&
             language_id == 0x0409) {
    return buf_view(s_product.data(), s_product.size());
  } else if (value == desc_value(DescriptorType::String, 3) &&
             language_id == 0x0409) {
    return buf_view(s_serial.data(), s_serial.size());
  }

  return std::nullopt;
}

} // namespace mantyl
