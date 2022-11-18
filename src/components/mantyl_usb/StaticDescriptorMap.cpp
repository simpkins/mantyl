// Copyright (c) 2022, Adam Simpkins
#include "mantyl_usb/StaticDescriptorMap.h"

namespace mantyl {
namespace detail {

std::optional<buf_view>
find_usb_descriptor(uint16_t value,
                    uint16_t index,
                    const uint8_t *data,
                    size_t data_size,
                    const StaticDescriptorMapEntry *entries,
                    size_t num_entries) {
  for (size_t n = 0; n < num_entries; ++n) {
    if (entries[n].value == value && entries[n].index == index) {
      return buf_view(data + entries[n].offset, entries[n].length);
    }
  }

  return std::nullopt;
}

bool update_ep0_max_packet_size(uint8_t max_packet_size,
                                uint8_t *data,
                                size_t data_size,
                                const StaticDescriptorMapEntry *entries,
                                size_t num_entries) {
  const uint16_t dev_desc_value = static_cast<uint16_t>(DescriptorType::Device)
                                  << 8;

  // Find the device descriptor
  for (size_t n = 0; n < num_entries; ++n) {
    if (entries[n].value == dev_desc_value && entries[n].index == 0) {
      // This is the device descriptor.
      if (entries[n].length != DeviceDescriptor::kSize) {
        // Unexpected size for device descriptor
        return false;
      }

      uint8_t* desc = data + entries[n].offset;
      desc[7] = max_packet_size;
      return true;
    }
  }

  return false;
}

} // namespace detail
} // namespace mantyl
