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

} // namespace detail
} // namespace mantyl
