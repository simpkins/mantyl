// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "mantyl_usb/usb_types.h"
#include "mantyl_usb/StaticDescriptorUtils.h"

#include <array>
#include <cstdint>
#include <limits>
#include <optional>
#include <string_view>
#include <type_traits>

namespace mantyl {

using buf_view = std::basic_string_view<uint8_t>;

/**
 * A class for constructing a USB descriptor map at compile time.
 *
 * This allows you to create a StaticDescriptorMap at compile time and store it
 * with static storage lifetime.
 */
template<uint16_t NumDescriptors, size_t DataLength>
class StaticDescriptorMap {
public:
  static constexpr uint16_t num_descriptors = NumDescriptors;

  /**
   * Default constructor.
   *
   * Only valid for empty maps.
   */
  template <typename T = int>
  constexpr StaticDescriptorMap(
      std::enable_if_t<NumDescriptors == 0 && DataLength == 0, T> = 0) {}

  /**
   * Create a new StaticDescriptorMap composed of this map plus a new
   * descriptor.
   */
  template <size_t DescLen>
  constexpr StaticDescriptorMap<NumDescriptors + 1, DataLength + DescLen>
  add_descriptor(uint16_t value,
                 uint16_t index,
                 std::array<uint8_t, DescLen> desc) {
    return StaticDescriptorMap<NumDescriptors + 1, DataLength + DescLen>(*this, value, index, desc);
  }

  /**
   * Add a string descriptor with a specified index.
   */
  template <size_t N>
  constexpr StaticDescriptorMap<NumDescriptors + 1, DataLength + 2 + N * 2>
  add_string(uint8_t index, const char (&str)[N], uint16_t language = 0) {
    return add_descriptor((static_cast<uint16_t>(DescriptorType::String) << 8) |
                              index,
                          language,
                          detail::make_string_descriptor<N>(str));
  }

  std::optional<buf_view> find_descriptor(uint16_t value, uint16_t index) {
    return detail::find_usb_descriptor(
        value, index, data_.data(), data_.size(), index_.data(), index_.size());
  }

private:
  template <uint16_t X, size_t Y>
  friend class StaticDescriptorMap;

  template <size_t DescLen>
  constexpr StaticDescriptorMap(
      const StaticDescriptorMap<NumDescriptors - 1, DataLength - DescLen> &other,
      uint16_t value,
      uint16_t index,
      std::array<uint8_t, DescLen> desc) {
    // StaticDescriptorMapEntry use uint16_t to store the offset.
    // Make sure the total descriptor length fits in this data type.
    static_assert(DataLength <=
                      std::numeric_limits<decltype(index_[0].offset)>::max(),
                  "descriptor data is to large");

    for (size_t n = 0; n < other.data_.size(); ++n) {
      data_[n] = other.data_[n];
    }
    for (size_t n = 0; n < desc.size(); ++n) {
      data_[other.data_.size() + n] = desc[n];
    }

    for (size_t n = 0; n < other.num_descriptors; ++n) {
      index_[n] = other.index_[n];
      if (index_[n].value == value && index_[n].index == index) {
          abort(); // Duplicate descriptor ID
      }
    }
    index_[other.num_descriptors].value = value;
    index_[other.num_descriptors].index = index;
    index_[other.num_descriptors].offset = other.data_.size();
    index_[other.num_descriptors].length = desc.size();
  }

  std::array<detail::StaticDescriptorMapEntry, NumDescriptors> index_;
  std::array<uint8_t, DataLength> data_;
};

} // namespace mantyl
