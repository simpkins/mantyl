// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "mantyl_usb/Descriptors.h"
#include "mantyl_usb/StaticDescriptorUtils.h"
#include "mantyl_usb/usb_types.h"

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
   * Add the device descriptor.
   */
  constexpr StaticDescriptorMap<NumDescriptors + 1,
                                DataLength + DeviceDescriptor::kSize>
  add_device_descriptor(const DeviceDescriptor &dev) {
    return add_descriptor(DescriptorType::Device, dev.serialize());
  }

  /**
   * Create a new StaticDescriptorMap composed of this map plus a new
   * descriptor.
   */
  template <size_t DescLen>
  constexpr StaticDescriptorMap<NumDescriptors + 1, DataLength + DescLen>
  add_descriptor(DescriptorType type,
                 const std::array<uint8_t, DescLen>& desc,
                 uint8_t desc_index = 0) {
    return add_descriptor_raw(
        (static_cast<uint16_t>(type) << 8) | desc_index, 0, desc);
  }

  /**
   * Add the descriptor that contains the list of supported language IDs
   */
  template <typename... LangIDs>
  constexpr StaticDescriptorMap<NumDescriptors + 1,
                                DataLength + 4 + (2 * sizeof...(LangIDs))>
  add_language_ids(Language lang, LangIDs... rest) {
    std::array<uint8_t, 4 + (2 * sizeof...(LangIDs))> desc;
    desc[0] = 4 + (2 * sizeof...(LangIDs));
    desc[1] = static_cast<uint8_t>(DescriptorType::String);
    detail::fill_lang_descriptor(desc.data() + 2, lang, rest...);
    return add_descriptor_raw(
        (static_cast<uint16_t>(DescriptorType::String) << 8), 0, desc);
  }

  /**
   * Add a configuration descriptor, and its associated interface, endpoint,
   * and class/vendor specific descriptors.
   */
  template <typename... SubDescriptors>
  constexpr StaticDescriptorMap<
      NumDescriptors + 1,
      DataLength + ConfigDescriptor::compute_total_size<SubDescriptors...>()>
  add_config_descriptor(ConfigAttr attributes,
                        UsbMilliamps max_power,
                        uint8_t string_index,
                        SubDescriptors... sub) {
    // TODO: it would be nice to do some compile-time validation of the config
    // descriptor:
    // - The interface numbers should be correct 0-based indexes of each
    //   interface.
    // - The number of endpoints listed in each interface should match the
    //   number of endpoint descriptors.
    auto cfg_index = count_num_config_descriptors();
    std::array<uint8_t,
               ConfigDescriptor::compute_total_size<SubDescriptors...>()>
        full_desc;
    ConfigDescriptor config_desc(cfg_index + 1);
    config_desc.total_length =
        ConfigDescriptor::compute_total_size<SubDescriptors...>();
    config_desc.string_index = string_index;
    config_desc.num_interfaces =
        ConfigDescriptor::count_num_interfaces(sub...);
    config_desc.attributes = attributes;
    config_desc.max_power = max_power;
    detail::serialize_descriptors(full_desc.data(), config_desc, sub...);
    return add_descriptor_raw(
        (static_cast<uint16_t>(DescriptorType::Config) << 8) | cfg_index,
        0,
        full_desc);
  }

  template <size_t DescLen>
  constexpr StaticDescriptorMap<NumDescriptors + 1, DataLength + DescLen>
  add_descriptor_raw(uint16_t value,
                     uint16_t index,
                     std::array<uint8_t, DescLen> desc) {
    return StaticDescriptorMap<NumDescriptors + 1, DataLength + DescLen>(
        *this, value, index, desc);
  }

  /**
   * Add a string descriptor with a specified index.
   */
  template <size_t N>
  constexpr StaticDescriptorMap<NumDescriptors + 1, DataLength + N * 2>
  add_string(uint8_t index, const char (&str)[N], Language language) {
    return add_descriptor_raw(
        (static_cast<uint16_t>(DescriptorType::String) << 8) | index,
        static_cast<uint16_t>(language),
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
      const std::array<uint8_t, DescLen>& desc) {
    // StaticDescriptorMapEntry use uint16_t to store the offset.
    // Make sure the total descriptor length fits in this data type.
    static_assert(DataLength <=
                      std::numeric_limits<decltype(index_[0].offset)>::max(),
                  "descriptor data is to large");
    if (desc[1] != (value >> 8)) {
      abort(); // descriptor type mismatch
    }

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

  constexpr uint8_t count_num_config_descriptors() {
    uint8_t count = 0;
    for (const auto &entry : index_) {
      if ((entry.value >> 8) == static_cast<uint8_t>(DescriptorType::Config)) {
        ++count;
      }
    }
    return count;
  }

  std::array<detail::StaticDescriptorMapEntry, NumDescriptors> index_;
  std::array<uint8_t, DataLength> data_;
};

} // namespace mantyl
