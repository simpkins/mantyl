// Copyright (c) 2022, Adam Simpkins
#include "mantyl_usb/CtrlInTransfer.h"

#include "mantyl_usb/UsbDevice.h"

#include <esp_log.h>

namespace {
const char *LogTag = "mantyl.usb.ctrl_in_xfer";
}

namespace mantyl {

void CtrlInTransfer::send_response_async(const void* buf, uint16_t size) {
  auto response_len = std::min(max_length_, size);
  auto result = usb_->ctrl_transfer_.start_transfer(
      *usb_, buf_view(static_cast<const uint8_t *>(buf), response_len));
  static_cast<void>(result);
  usb_ = nullptr;
}

void CtrlInTransfer::stall() {
  ESP_LOGW(LogTag, "unhandled USB Setup IN transfer");
  usb_->ctrl_transfer_.send_request_error(*usb_);
  usb_ = nullptr;
}

void CtrlInTransfer::destroy() {
  if (!usb_) {
      return;
  }

  ESP_LOGW(LogTag,
           "no response generated for to USB Setup IN transfer: generating "
           "STALL condition");
  usb_->ctrl_transfer_.send_request_error(*usb_);
}

} // namespace mantyl
