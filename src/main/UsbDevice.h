// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <esp_err.h>
#include <tusb.h>

#include <array>
#include <vector>

namespace mantyl {

class UsbDevice {
public:
  UsbDevice();

  [[nodiscard]] esp_err_t init();

private:
  UsbDevice(UsbDevice const &) = delete;
  UsbDevice &operator=(UsbDevice const &) = delete;

  [[nodiscard]] esp_err_t init_serial();

  /**
   * Add a string literal to the string descriptors.
   *
   * The string data must remain valid for as long as the UsbDevice object
   * (hence this is normally only suitable for string literals).
   * Returns the descriptor index.
   */
  uint8_t add_string_literal(const char *str);

  void init_config_desc(bool debug);

  // Descriptors
  std::array<char, 14> serial_;
  std::vector<const char*> strings_;
  std::vector<uint8_t> config_desc_;
  tusb_desc_device_t device_desc_;
};

} // namespace mantyl
