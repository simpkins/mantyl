// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "mantyl_usb/usb_types.h"

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

} // namespace mantyl
