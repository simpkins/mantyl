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

std::optional<std::pair<uint8_t *, size_t>>
find_usb_descriptor_mutable(uint16_t value,
                            uint16_t index,
                            uint8_t *data,
                            size_t data_size,
                            const StaticDescriptorMapEntry *entries,
                            size_t num_entries) {
  for (size_t n = 0; n < num_entries; ++n) {
    if (entries[n].value == value && entries[n].index == index) {
      return std::make_pair<uint8_t *, size_t>(data + entries[n].offset,
                                               entries[n].length);
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
  auto desc = find_usb_descriptor_mutable(
      dev_desc_value, 0, data, data_size, entries, num_entries);
  if (!desc || desc->second != DeviceDescriptor::kSize) {
    return false;
  }

  desc->first[7] = max_packet_size;
  return true;
}

} // namespace detail
} // namespace mantyl
