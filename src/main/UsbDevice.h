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
  ~UsbDevice();

  static UsbDevice* get() {
      return singleton_;
  }

  [[nodiscard]] esp_err_t init();

  void on_hid_set_report(uint8_t instance,
                         uint8_t report_id,
                         hid_report_type_t report_type,
                         uint8_t const *buffer,
                         uint16_t bufsize);
  uint16_t on_hid_get_report(uint8_t instance,
                             uint8_t report_id,
                             hid_report_type_t report_type,
                             uint8_t *buffer,
                             uint16_t reqlen);
  uint8_t const *get_hid_report_descriptor(uint8_t instance);

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
  void init_hid_report_descriptors();

  static UsbDevice* singleton_;

  static constexpr uint8_t kbd_interface_num_{0};
  static constexpr uint8_t cdc_interface_num_{1};
  static constexpr uint8_t cdc_data_interface_num_{2};
  static constexpr uint8_t kbd_report_id_{1};

  static constexpr uint8_t kbd_endpoint_addr_{1};
  static constexpr uint8_t cdc_notif_endpoint_addr_{2};
  static constexpr uint8_t cdc_data_endpoint_addr_{3};

  // Descriptors
  std::array<char, 14> serial_;
  std::vector<const char*> strings_;
  std::vector<uint8_t> config_desc_;
  tusb_desc_device_t device_desc_;
  std::vector<uint8_t> keyboard_report_desc_;
};

} // namespace mantyl
