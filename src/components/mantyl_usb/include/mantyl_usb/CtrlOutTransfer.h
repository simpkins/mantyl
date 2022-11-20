// Copyright (c) 2022, Adam Simpkins
#pragma once

namespace mantyl {

class UsbDevice;

class CtrlOutTransfer {
public:
  explicit CtrlOutTransfer(UsbDevice *usb = nullptr) : usb_{usb} {}
  ~CtrlOutTransfer() {
    destroy();
  }

  CtrlOutTransfer(CtrlOutTransfer &&other) noexcept : usb_{other.usb_} {
    other.usb_ = nullptr;
  }
  CtrlOutTransfer& operator=(CtrlOutTransfer&& other) {
    destroy();
    usb_ = other.usb_;
    other.usb_ = nullptr;
    return *this;
  }

  void ack();
  void stall();

private:
  void destroy();

  UsbDevice* usb_{nullptr};
};

} // namespace mantyl
