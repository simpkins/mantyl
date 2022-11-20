// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <cstdint>
#include <string_view>

namespace mantyl {

class UsbDevice;
using buf_view = std::basic_string_view<uint8_t>;

class CtrlInTransfer {
public:
  CtrlInTransfer() = default;
  explicit CtrlInTransfer(UsbDevice *usb, uint16_t max_length)
      : usb_{usb}, max_length_{max_length} {}
  ~CtrlInTransfer() {
    destroy();
  }

  CtrlInTransfer(CtrlInTransfer &&other) noexcept
      : usb_{other.usb_}, max_length_{other.max_length_} {
    other.usb_ = nullptr;
  }

  CtrlInTransfer &operator=(CtrlInTransfer &&other) noexcept {
    destroy();
    usb_ = other.usb_;
    max_length_ = other.max_length_;
    other.usb_ = nullptr;
    return *this;
  }

  /**
   * Send the specified response.
   *
   * Note that the response may not be completely sent by the time
   * send_response_async() returns.  The caller must ensure that the buffer
   * lives for as long as it takes to send the response.  (This currently means
   * that the caller's buffer must live for at least as long as the UsbDevice
   * object, as we currently don't provide another mechanism to be notified
   * when the send is complete.)
   */
  void send_response_async(const void* buf, uint16_t size);
  void send_response_async(buf_view buf) {
    send_response_async(buf.data(), buf.size());
  }

  void stall();

private:
  void destroy();

  UsbDevice* usb_{nullptr};
  uint16_t max_length_{0};
};

} // namespace mantyl
