// Copyright (c) 2022, Adam Simpkins
#include "mantyl_usb/CtrlOutTransfer.h"

#include "mantyl_usb/UsbDevice.h"

#include <esp_log.h>

namespace {
const char *LogTag = "mantyl.usb.ctrl_out_xfer";
}

namespace mantyl {

void CtrlOutTransfer::ack() {
  usb_->ctrl_out_ack();
  usb_ = nullptr;
}

void CtrlOutTransfer::stall() {
  ESP_LOGW(LogTag, "unhandled USB Setup OUT transfer");
  usb_->stall_ctrl_transfer();
  usb_ = nullptr;
}

void CtrlOutTransfer::destroy() {
  if (!usb_) {
      return;
  }

  ESP_LOGW(LogTag,
           "no response generated for to USB Setup OUT transfer: generating "
           "STALL condition");
  usb_->stall_ctrl_transfer();
}

} // namespace mantyl
