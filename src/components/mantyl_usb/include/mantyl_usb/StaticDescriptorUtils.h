// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "mantyl_usb/usb_types.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string_view>

namespace mantyl {

class InterfaceDescriptor;

using buf_view = std::basic_string_view<uint8_t>;

namespace detail {
struct StaticDescriptorMapEntry {
  uint16_t value;
  uint16_t index;
  uint16_t offset;
  uint16_t length;
};

std::optional<buf_view>
find_usb_descriptor(uint16_t value,
                    uint16_t index,
                    const uint8_t *data,
                    size_t data_size,
                    const StaticDescriptorMapEntry *entries,
                    size_t num_entries);

std::optional<std::pair<uint8_t *, size_t>>
find_usb_descriptor_mutable(uint16_t value,
                            uint16_t index,
                            uint8_t *data,
                            size_t data_size,
                            const StaticDescriptorMapEntry *entries,
                            size_t num_entries);

bool update_ep0_max_packet_size(uint8_t max_packet_size,
                                uint8_t *data,
                                size_t data_size,
                                const StaticDescriptorMapEntry *entries,
                                size_t num_entries);

[[nodiscard]] constexpr bool
fill_string_descriptor(uint8_t *buf, size_t buflen, std::string_view str) {
  // buf[0] will be filled at the end, once we know the output length
  buf[1] = static_cast<uint8_t>(DescriptorType::String);
  size_t in_idx = 0;
  size_t out_idx = 2;
  while (in_idx < str.size()) {
    if (out_idx + 1 >= buflen) {
      return false; // output buffer size too small
    }

    // Translate UTF-8 input to UTF-16 LE
    if (str[in_idx] < 0x80) {
      buf[out_idx] = str[in_idx];
      buf[out_idx + 1] = '\0';
      ++in_idx;
      out_idx += 2;
    } else {
      uint32_t c;
      if ((str[in_idx] & 0xe0) == 0xc0) {
        // 2-byte UTF-8 value
        if (in_idx + 1 >= str.size()) {
          return false; // truncated UTF-8 data
        }
        if ((str[in_idx + 1] & 0xc0) != 0x80) {
          return false; // invalid UTF-8
        }
        c = ((str[in_idx] & 0x1f) << 6) | (str[in_idx + 1] & 0x3f);
        in_idx += 2;
      } else if ((str[in_idx] & 0xf0) == 0xe0) {
        // 3-byte UTF-8 value
        if (in_idx + 2 >= str.size()) {
          return false; // truncated UTF-8 data
        }
        if ((str[in_idx + 1] & 0xc0) != 0x80) {
          return false; // invalid UTF-8
        }
        if ((str[in_idx + 2] & 0xc0) != 0x80) {
          return false; // invalid UTF-8
        }
        c = ((str[in_idx] & 0x1f) << 12) |
            ((str[in_idx + 1] & 0x3f) << 6) | (str[in_idx + 2] & 0x3f);
        in_idx += 3;
      } else if ((str[in_idx] & 0xf8) == 0xf0) {
        // 4-byte UTF-8 value
        if (in_idx + 3 >= str.size()) {
          return false; // truncated UTF-8 data
        }
        if ((str[in_idx + 1] & 0xc0) != 0x80) {
          return false; // invalid UTF-8
        }
        if ((str[in_idx + 2] & 0xc0) != 0x80) {
          return false; // invalid UTF-8
        }
        if ((str[in_idx + 3] & 0xc0) != 0x80) {
          return false; // invalid UTF-8
        }
        c = ((str[in_idx] & 0x1f) << 18) | ((str[in_idx + 1] & 0x3f) << 12) |
            ((str[in_idx + 2] & 0x3f) << 6) | (str[in_idx + 3] & 0x3f);
        in_idx += 4;
      } else {
        return false; // Invalid UTF-8 value
      }

      // Write the output char
      if (c > 0xffff) {
        // We do not support code points that require encoding using more than
        // 2 output bytes.  (This would make compile-time length calculation
        // trickier.)
        return false;
      }
      buf[out_idx] = (c & 0xff);
      buf[out_idx] = ((c >> 8) & 0xff);
      out_idx += 2;
    }
  }

  // The first byte of the descriptor is the length
  buf[0] = out_idx;

  // If there were multibyte characters in the input,
  // we will have leftover room at the end of the output.
  // Just fill it with 0s.
  for (size_t n = out_idx; n < buflen; ++n) {
    buf[n] = 0;
  }

  return true;
}

template <size_t N>
constexpr std::array<uint8_t, N * 2>
make_string_descriptor(const char (&str)[N]) {
  std::array<uint8_t, N * 2> out;
  if (N == 0 || str[N - 1] != '\0') {
    abort(); // the input string must be nul terminated
  }
  if (!fill_string_descriptor(out.data(), out.size(), str)) {
    abort();
  }
  return out;
}

constexpr void fill_lang_descriptor(uint8_t* desc, Language lang) {
  desc[0] = static_cast<uint16_t>(lang) & 0xff;
  desc[1] = (static_cast<uint16_t>(lang) >> 8) & 0xff;
}

template <typename... LangIDs>
constexpr void
fill_lang_descriptor(uint8_t *desc, Language lang, LangIDs... rest) {
  desc[0] = static_cast<uint16_t>(lang) & 0xff;
  desc[1] = (static_cast<uint16_t>(lang) >> 8) & 0xff;
  fill_lang_descriptor(desc + 2, rest...);
}

template<typename Descriptor>
constexpr bool is_interface_descriptor(const Descriptor& desc) {
  return false;
}

constexpr bool is_interface_descriptor(const mantyl::InterfaceDescriptor&) {
  return true;
}

template <size_t N>
constexpr bool is_interface_descriptor(const std::array<uint8_t, N> &desc) {
  return ((N > 1) &&
          desc[1] == static_cast<uint8_t>(DescriptorType::Interface));
}

template <typename Descriptor>
class DescriptorTraits {
public:
  static constexpr uint16_t size = Descriptor::kSize;

  static constexpr void serialize_into(uint8_t *buf, const Descriptor &desc) {
    return desc.serialize_into(buf);
  }
};

template <size_t N>
class DescriptorTraits<std::array<uint8_t, N>> {
public:
  static constexpr uint16_t size = N;

  static constexpr void serialize_into(uint8_t *buf,
                                       const std::array<uint8_t, N> &desc) {
    for (size_t n = 0; n < N; ++n) {
      buf[n] = desc[n];
    }
  }
};

template <typename Descriptor>
constexpr void serialize_descriptors(uint8_t *buf, const Descriptor &desc) {
  DescriptorTraits<Descriptor>::serialize_into(buf, desc);
}

template <typename Descriptor, typename... Rest>
constexpr void serialize_descriptors(uint8_t *buf,
                                     const Descriptor &desc,
                                     const Rest &... rest) {
  DescriptorTraits<Descriptor>::serialize_into(buf, desc);
  serialize_descriptors(buf + DescriptorTraits<Descriptor>::size, rest...);
}

} // namespace detail
} // namespace mantyl
