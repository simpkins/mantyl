// Copyright (c) 2022, Adam Simpkins
#include "mantyl_usb/CtrlOutTransfer.h"

#include "mantyl_usb/UsbDevice.h"

#include <esp_log.h>

namespace {
const char *LogTag = "mantyl.usb.ctrl_out_xfer";
}

namespace mantyl {

void CtrlOutTransfer::ack() {
  auto result = usb_->ctrl_transfer_.ack_out_transfer(*usb_);
  static_cast<void>(result);
  usb_ = nullptr;
}

void CtrlOutTransfer::stall() {
  usb_->ctrl_transfer_.send_request_error(*usb_);
  usb_ = nullptr;
}

void CtrlOutTransfer::destroy() {
  if (usb_) {
    ESP_LOGW(LogTag,
             "no response generated for to USB Setup OUT transfer: generating "
             "STALL condition");
    stall();
  }
}

} // namespace mantyl
