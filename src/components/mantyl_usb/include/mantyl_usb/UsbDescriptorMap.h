// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <optional>
#include <string_view>

namespace mantyl {

using buf_view = std::basic_string_view<uint8_t>;

class UsbDescriptorMap {
public:
  std::optional<buf_view> find_descriptor(uint16_t value, uint16_t index);

private:
};

} // namespace mantyl
