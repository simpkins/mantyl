// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "I2cDevice.h"

#include <utility>
#include <variant>

namespace mantyl {

class SX1509 {
public:
  SX1509(I2cMaster &bus, uint8_t addr) : dev_{bus, addr} {}
  explicit SX1509(I2cDevice &&device) : dev_{std::move(device)} {}

  [[nodiscard]] esp_err_t init();

private:
  // Register addresses
  enum Reg : uint8_t {
    // I/O pull up: 0 disabled, 1 enabled
    // (defaults to disabled for all I/Os)
    PullUpB = 0x06,
    PullUpA = 0x07,
    // I/O pull down: 0 disabled, 1 enabled
    // (defaults to disabled for all I/Os)
    PullDownB = 0x08,
    PullDownA = 0x09,
    // I/O open drain config: 0 is push-pull, 1 is open drain
    // (defaults to push-pull for all I/Os)
    OpenDrainB = 0x0a,
    OpenDrainA = 0x0b,
    // I/O direction: 1 is input, 0 is output
    // (defaults to input for all I/Os)
    DirB = 0x0e,
    DirA = 0x0f,
    IntrMaskA = 0x13,
    Clock = 0x1e,
    Misc = 0x1f,
    DebounceConfig = 0x22,
    DebounceEnableB = 0x23,
    DebounceEnableA = 0x24,
    KeyConfig1 = 0x25,
    KeyConfig2 = 0x26,
    KeyData1 = 0x27,
    KeyData2 = 0x28,
    Reset = 0x7d,
  };

  enum class ClockSource : uint8_t {
    Off = 0x00,
    External = 0x01,
    Internal2MHZ = 0x02,
  };
  enum class OscPinFuncion : uint8_t {
    Input = 0,
    Output = 1,
  };

  SX1509(SX1509 const &) = delete;
  SX1509 &operator=(SX1509 const &) = delete;

  /**
   * source:
   *   Source for fOSC frequency.
   *   - Internal2MHz: Internal 2Mhz clock
   *   - External: Driven from OSC pin.  pin_fn should be set to Input.
   *
   * led_divider (0x0 to 0x7):
   *   Controls frequency of clock for LED driver:
   *   - 0x0: off
   *   - otherwise: ClkX = fOSC / (2^(divider -1))
   *
   *   In other words:
   *   - 1: 2Mhz
   *   - 2: 1Mhz
   *   - 3: 500khz
   *   - 4: 250Khz
   *   - 5: 125Khz
   *   - 6: 62.5Khz
   *   - 7: 31.25Khz
   *
   * pin_fn:
   *   Controls if the OSC pin should be used as input (OSCIN, for use with an
   *   external clock source), or output (OSCOUT, to generate an external
   *   signal from the external clock).
   *
   * oscout_freq (0x0 to 0xf):
   *   Controls frequency of OSCOUT pin, if it is configured as an output.
   *   - 0x0: 0Hz, permanent 0 logic level
   *   - 0xf: 0Hz, permanent 1 logic level
   *   - otherwise: fOSCOUT = fOSC / (2^(oscout_freq-1))
   */
  bool configure_clock(ClockSource source,
                       uint8_t led_divider = 1,
                       OscPinFuncion pin_fn = OscPinFuncion::Input,
                       uint8_t oscout_freq = 0);

  bool prepare_read(uint8_t addr, uint8_t size);

  [[nodiscard]] esp_err_t
  write_data(uint8_t addr, const void *data, size_t size);
  [[nodiscard]] esp_err_t write_u8(uint8_t addr, uint8_t value) {
    return write_data(addr, &value, sizeof(value));
  }
  [[nodiscard]] esp_err_t write_u16(uint8_t addr, uint16_t value) {
    return write_data(addr, &value, sizeof(value));
  }

  esp_err_t read_data(uint8_t addr, void *data, size_t size);
  std::variant<uint16_t, esp_err_t> read_u16(uint8_t addr) {
      uint16_t value;
      auto rc = read_data(addr, &value, sizeof(value));
      if (rc == ESP_OK) {
        return value;
      }
      return rc;
  }

  I2cDevice dev_;
  bool keypad_configured_{false};
};

} // namespace mantyl
