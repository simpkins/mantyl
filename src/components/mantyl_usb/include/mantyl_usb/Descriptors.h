// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "mantyl_usb/usb_types.h"
#include "mantyl_usb/StaticDescriptorUtils.h"

#include <array>
#include <cstdint>
#include <cstdlib>

namespace mantyl {

constexpr uint8_t bcd_encode(uint8_t x) {
  if (x > 99) {
    abort(); // Cannot represent values with more than 2 decimal digits
  }
  const auto low_digit = x % 10;
  const auto high_digit = x / 10;
  return (high_digit << 4) | (low_digit);
}

/**
 * DeviceDescriptor contains the fields in an USB device descriptor.
 *
 * Note that the DeviceDescriptor class is not intended to be copied laid out
 * in memory exactly as the descriptor is transmitted on the wire.  Instead it
 * has serialize() and deserialize() methods to convert it to the byte array to
 * be transmitted on the wire.
 */
class DeviceDescriptor {
public:
  static constexpr size_t kSize = 18;

  constexpr DeviceDescriptor() = default;
  constexpr DeviceDescriptor(uint16_t vendor, uint16_t product)
      : vendor_id(vendor), product_id(product) {}

  constexpr void set_device_version(uint8_t major, uint8_t minor) {
    device_version_bcd = (bcd_encode(major) << 8) | bcd_encode(minor);
  }
  constexpr void set_usb_version(uint8_t major, uint8_t minor) {
    // Note that USB version 1.1 is encoded as 0x0110.  (The minor version is
    // effectively treated as "10" rather than "01".)
    if (minor < 10) {
      minor *= 10;
    }
    usb_version_bcd = (bcd_encode(major) << 8) | bcd_encode(minor);
  }

  uint16_t usb_version_bcd{0x200};
  uint8_t  device_class{0};
  uint8_t  subclass{0};
  uint8_t  protocol{0};
  uint8_t  ep0_max_packet_size{64};

  uint16_t vendor_id{0};
  uint16_t product_id{0};
  uint16_t device_version_bcd{0};
  uint8_t  manufacturer_str_index{0};
  uint8_t  product_str_index{0};
  uint8_t  serial_str_index{0};

  uint8_t  num_configurations{1};

  constexpr std::array<uint8_t, kSize> serialize() const {
    return std::array<uint8_t, kSize>{{
        kSize, // length
        static_cast<uint8_t>(DescriptorType::Device),
        static_cast<uint8_t>(usb_version_bcd & 0xff),
        static_cast<uint8_t>((usb_version_bcd >> 8) & 0xff),
        device_class,
        subclass,
        protocol,
        ep0_max_packet_size,
        static_cast<uint8_t>(vendor_id & 0xff),
        static_cast<uint8_t>((vendor_id >> 8) & 0xff),
        static_cast<uint8_t>(product_id & 0xff),
        static_cast<uint8_t>((product_id >> 8) & 0xff),
        static_cast<uint8_t>(device_version_bcd & 0xff),
        static_cast<uint8_t>((device_version_bcd >> 8) & 0xff),
        manufacturer_str_index,
        product_str_index,
        serial_str_index,
        num_configurations,
    }};
  }

  // Update the ep0_max_packet_size field in an existing serialized descriptor
  static void update_ep0_max_size(std::array<uint8_t, kSize> data,
                                  uint8_t max_size) {
    data[8] = max_size;
  }
  // Update the serial string descriptor index in an existing serialized
  // descriptor
  static void update_serial_index(std::array<uint8_t, kSize> data,
                                  uint8_t index) {
    data[17] = index;
  }
};

class ConfigDescriptor {
public:
  // This is the size of just the ConfigDescriptor by itself,
  // without the associated interface, endpoint, and other class or vendor
  // specific descriptors.
  static constexpr size_t kSize = 9;

  explicit constexpr ConfigDescriptor(uint8_t id) : id{id} {}

  uint8_t id = 0;
  uint8_t total_length = 0;
  uint8_t num_interfaces = 0;
  uint8_t string_index = 0;
  ConfigAttr attributes = ConfigAttr::None;
  UsbMilliamps max_power{0};

  constexpr void serialize_into(uint8_t* buf) const {
    buf[0] = kSize;
    buf[1] = static_cast<uint8_t>(DescriptorType::Config);
    buf[2] = total_length & 0xff;
    buf[3] = (total_length >> 8) & 0xff;
    buf[4] = num_interfaces;
    buf[5] = id;
    buf[6] = string_index;
    buf[7] = 0x80 | static_cast<uint8_t>(attributes);
    buf[8] = max_power.value_in_2ma();
  }

  template <typename... SubDescriptors>
  static constexpr uint16_t compute_total_size() {
    return kSize + (detail::DescriptorTraits<SubDescriptors>::size + ...);
  }

  template <typename SubDesc, typename... Rest>
  static constexpr uint8_t count_num_interfaces(const SubDesc &desc,
                                              Rest... rest) {
    return (detail::is_interface_descriptor(desc) ? 1 : 0) +
           count_num_interfaces(rest...);
  }
  static constexpr uint8_t count_num_interfaces() {
    return 0;
  }
};

class InterfaceDescriptor {
public:
  static constexpr size_t kSize = 9;

  constexpr InterfaceDescriptor(uint8_t idx, UsbClass itf_class)
      : index(idx), interface_class(itf_class) {}

  uint8_t index = 0;
  uint8_t alternate_setting = 0;
  uint8_t num_endpoints = 0;
  UsbClass interface_class = UsbClass::PerInterface;
  uint8_t subclass = 0;
  uint8_t protocol = 0;
  uint8_t string_index = 0;

  constexpr void serialize_into(uint8_t* buf) const {
    buf[0] = kSize;
    buf[1] = static_cast<uint8_t>(DescriptorType::Interface);
    buf[2] = index;
    buf[3] = alternate_setting;
    buf[4] = num_endpoints;
    buf[5] = static_cast<uint8_t>(interface_class);
    buf[6] = subclass;
    buf[7] = protocol;
    buf[8] = string_index;
  }
};

class EndpointDescriptor {
public:
  static constexpr size_t kSize = 7;

  constexpr EndpointDescriptor(EndpointAddress addr, EndpointAttributes attr)
      : address(addr), attributes(attr) {}

  EndpointAddress address;
  EndpointAttributes attributes;
  uint16_t max_packet_size{64};
  uint8_t interval{1};

  constexpr void serialize_into(uint8_t* buf) const {
    buf[0] = kSize;
    buf[1] = static_cast<uint8_t>(DescriptorType::Endpoint);
    buf[2] = address.value();
    buf[3] = attributes.value();
    buf[4] = max_packet_size & 0xff;
    buf[5] = (max_packet_size >> 8) & 0xff;
    buf[6] = interval;
  }
};

class StringDescriptorBuffer {
public:
  StringDescriptorBuffer(uint8_t *data, uint16_t capacity)
      : data_{data}, capacity_{capacity} {}

  /**
   * Return the capacity, in bytes.
   *
   * This includes the 2 bytes required for the descriptor size and type.
   */
  uint16_t capacity() const {
    return capacity_;
  }

  /**
   * Return the descriptor size, in bytes.
   *
   * Note that this return the descriptor size bytes, not the string length in
   * Unicode characters.
   *
   * The return value includes the 2 bytes required for the descriptor size and
   * type.
   */
  uint8_t size() const {
    return data_[0];
  }

  const uint8_t* data() const {
    return data_;
  }

  uint8_t* data() {
    return data_;
  }

private:
  uint8_t *data_{nullptr};
  uint16_t capacity_{0};
};

} // namespace mantyl
