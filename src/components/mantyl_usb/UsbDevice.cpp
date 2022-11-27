// Copyright (c) 2022, Adam Simpkins
#include "mantyl_usb/UsbDevice.h"

#include "mantyl_usb/CtrlOutTransfer.h"
#include "mantyl_usb/CtrlInTransfer.h"

#include <esp_log.h>

namespace {
const char *LogTag = "mantyl.usb.device";
}

namespace mantyl {

void UsbDevice::on_bus_reset() {
  ESP_LOGI(LogTag, "onbus_reset");
  impl_->on_reset();
}

void UsbDevice::on_enum_done(uint16_t max_ep0_packet_size) {
  ESP_LOGI(LogTag, "on_enum_done: max_ep0_packet_size=%d", max_ep0_packet_size);

  state_ = State::Default;
  config_id_ = 0;
  remote_wakeup_enabled_ = false;
  max_packet_size_ = max_ep0_packet_size;
  fail_control_transfer();

  impl_->on_enumerated(max_ep0_packet_size);
}

void UsbDevice::on_suspend() {
  ESP_LOGI(LogTag, "on_suspend");
  state_ |= StateFlag::Suspended;
  // Do not invoke the on_suspend() callback for suspend events that occur
  // before the first reset has been seen.  The bus suspend state can be seen
  // when first attached to the bus, but this generally isn't really relevant
  // or worth distinguishing from the normal uninitialized state.
  if ((state_ & StateMask::Mask) != State::Uninit) {
    impl_->on_suspend();
  }
}

void UsbDevice::on_resume() {
  if ((state_ & StateFlag::Suspended) != StateFlag::Suspended) {
    return;
  }
  ESP_LOGI(LogTag, "on_resume");
  state_ &= ~StateFlag::Suspended;
  if ((state_ & StateMask::Mask) != State::Uninit) {
    impl_->on_wakeup();
  }
}

void UsbDevice::on_setup_received(const SetupPacket& packet) {
  // Ignore any packets until we have seen a reset.
  if ((state_ & StateMask::Mask) == State::Uninit) {
    ESP_LOGW(LogTag, "ignoring USB setup packet before reset seen");
    return;
  }

  // Process control request
  process_setup_packet(packet);
}

void UsbDevice::fail_control_transfer() {
  auto old_ctrl_status = ctrl_status_;
  ctrl_status_ = CtrlStatus::None;

  // Increment ctrl_transfer_generation_, to ensure that any future attempts to
  // use an outstanding CtrlOutTransfer or CtrlInTransfer object will fail.
  // This is needed in case we are in a pending transaction waiting on the
  // device implementation to initiate the next phase of send or receive.
  // (It's possible that the generation number could loop around and become
  // valid again, but this seems unlikely to be an issue in practice.)
  ++ctrl_transfer_generation_;

  if (old_ctrl_status == CtrlStatus::InData) {
    auto *cb = ctrl_state_.in.callback;
    ctrl_state_.in.reset();
    if (cb) {
      cb->in_send_error(UsbError::Reset);
    }
  } else if (old_ctrl_status == CtrlStatus::OutData) {
    auto *cb = ctrl_state_.out.callback;
    ctrl_state_.out.reset();
    if (cb) {
      cb->out_recv_error(UsbError::Reset);
    }
  }
}

void UsbDevice::process_setup_packet(const SetupPacket& packet) {
  ESP_LOGI(LogTag,
           "USB: SETUP received: request_type=0x%04x request=0x%04x "
           "value=0x%06x index=0x%06x length=0x%06x",
           packet.request_type,
           packet.request,
           packet.value,
           packet.index,
           packet.length);

  if (ctrl_status_ != CtrlStatus::None) {
    // It's unexpected to receive a new SETUP packet if we think there is
    // a control transfer still in progress.  Terminate the control transfer
    // we think is still in progress.
    fail_control_transfer();
    // Continue through and process this SETUP packet.
  }

  if (packet.request_type == 0) {
    // Direction: Out (host to device)
    // Type: Standard request type
    // Recipient: Device
    process_std_device_out_request(packet, start_ctrl_out());
    return;
  } else if (packet.request_type == 0x80) {
    // Direction: In (device to host)
    // Type: Standard request type
    // Recipient: Device
    process_std_device_in_request(packet, start_ctrl_in(packet.length));
    return;
  }

  const auto recipient = packet.get_recipient();
  if (packet.get_direction() == Direction::Out) {
    auto xfer = start_ctrl_out();
    if (recipient == SetupRecipient::Device) {
      process_non_std_device_out_request(packet, std::move(xfer));
    } else if (recipient == SetupRecipient::Interface) {
      const uint8_t num = (packet.index & 0xf);
      impl_->handle_ep0_interface_out(num, packet, std::move(xfer));
    } else if (recipient == SetupRecipient::Endpoint) {
      const uint8_t num = (packet.index & 0xf);
      impl_->handle_ep0_endpoint_out(num, packet, std::move(xfer));
    } else {
      xfer.stall();
    }
  } else {
    auto xfer = start_ctrl_in(packet.length);
    if (recipient == SetupRecipient::Device) {
      process_non_std_device_in_request(packet, std::move(xfer));
    } else if (recipient == SetupRecipient::Interface) {
      const uint8_t num = (packet.index & 0xff);
      impl_->handle_ep0_interface_in(num, packet, std::move(xfer));
    } else if (recipient == SetupRecipient::Endpoint) {
      const uint8_t num = (packet.index & 0xf);
      impl_->handle_ep0_endpoint_in(num, packet, std::move(xfer));
    } else {
      xfer.stall();
    }
  }
}

void UsbDevice::process_std_device_out_request(const SetupPacket &packet,
                                               CtrlOutTransfer &&xfer) {
  const auto std_req_type = packet.get_std_request();
  if (std_req_type == StdRequestType::SetAddress) {
    const uint8_t address = packet.value;
    ESP_LOGI(LogTag, "USB: set address: %u", packet.value);
    state_ = State::Address;
    set_address(address);
    xfer.ack();
  } else if (std_req_type == StdRequestType::SetConfiguration) {
    process_set_configuration(packet, std::move(xfer));
  } else if (std_req_type == StdRequestType::SetFeature) {
    process_device_set_feature(packet, std::move(xfer));
  } else if (std_req_type == StdRequestType::ClearFeature) {
    process_device_clear_feature(packet, std::move(xfer));
  }
}

void UsbDevice::process_std_device_in_request(const SetupPacket &packet,
                                              CtrlInTransfer &&xfer) {
  const auto std_req_type = packet.get_std_request();
  if (std_req_type == StdRequestType::GetDescriptor) {
    return process_get_descriptor(packet, std::move(xfer));
  } else if (std_req_type == StdRequestType::GetConfiguration) {
    ESP_LOGI(LogTag, "USB: get configuration");
    // The response packet we send points at our config_id_ member variable.
    // We shouldn't be able to receive a new SetConfiguration packet while we
    // are responding to this GetConfiguration packet, so config_id_ generally
    // should not be able to change while we are trying to transmit this
    // response.
    return xfer.send_response_async(&config_id_, sizeof(config_id_));
  } else if (std_req_type == StdRequestType::GetStatus) {
    ESP_LOGI(LogTag, "USB: GetStatus");
    // We put the response into in_place_buf_
    const bool self_powered = impl_->is_self_powered();
    in_place_buf_[0] =
        (remote_wakeup_enabled_ ? 0x02 : 0x00) | (self_powered ? 0x01 : 0x00);
    in_place_buf_[1] = 0;
    return xfer.send_response_async(in_place_buf_.data(), in_place_buf_.size());
  } else {
    ESP_LOGW(LogTag, "USB: unhandled standard device request");
    xfer.stall();
  }
}

void UsbDevice::process_non_std_device_out_request(const SetupPacket &packet,
                                                   CtrlOutTransfer &&xfer) {
  const auto req_type = packet.get_request_type();
  if (req_type == SetupReqType::Class) {
    impl_->handle_ep0_class_out(packet, std::move(xfer));
  } else if (req_type == SetupReqType::Vendor) {
    impl_->handle_ep0_vendor_out(packet, std::move(xfer));
  } else {
    ESP_LOGW(LogTag, "unknown request type in device setup OUT request");
    xfer.stall();
  }
}

void UsbDevice::process_non_std_device_in_request(const SetupPacket &packet,
                                                  CtrlInTransfer &&xfer) {
  const auto req_type = packet.get_request_type();
  if (req_type == SetupReqType::Class) {
    impl_->handle_ep0_class_in(packet, std::move(xfer));
  } else if (req_type == SetupReqType::Vendor) {
    impl_->handle_ep0_vendor_in(packet, std::move(xfer));
  } else {
    ESP_LOGW(LogTag, "unknown request type in device setup IN request");
    xfer.stall();
  }
}

void UsbDevice::process_set_configuration(const SetupPacket &packet, CtrlOutTransfer&& xfer) {
  if (state_ != State::Address && state_ != State::Configured) {
    xfer.stall();
    return;
  }

  const auto config_id = (packet.value & 0xff);
  ESP_LOGI(LogTag, "USB: set configuration: %u", config_id);
  if (config_id_ == config_id) {
    // nothing new to do
  } else if (config_id == 0) {
    config_id_ = 0;
    state_ = State::Address;
    impl_->on_unconfigured();
  } else {
    config_id_ = config_id;
    state_ = State::Configured;
    if (!impl_->on_configured(config_id)) {
      // If a SetConfiguration request is received with an invalid config
      // ID, the USB spec does not really indicates we should generate a
      // Request Error, but doesn't really say what state we should be in
      // afterwards if we were previously in the Configured state.
      // We choose to reset back to the Address state here.  Most likely
      // something has gone wrong and the host will probably reset us
      // anyway.
      config_id_ = 0;
      state_ = State::Address;
      xfer.stall();
      return;
    }
  }
  xfer.ack();
}

void UsbDevice::process_device_set_feature(const SetupPacket &packet,
                                           CtrlOutTransfer &&xfer) {
  ESP_LOGI(LogTag,
           "USB: SetFeature for device, feature=%u, index=%u",
           packet.value,
           packet.index);
  const auto feature = static_cast<FeatureSelector>(packet.value);
  if (feature == FeatureSelector::TestMode) {
    // We don't currently support test mode.
    // The USB spec requires this support for high speed devices.
    // Currently we only run on ESP32S2/S3 devices, which are full speed,
    // and do not support high speed.
    xfer.stall();
    return;
  }

  if (state_ != State::Address && state_ != State::Configured) {
    xfer.stall();
    return;
  }

  if (feature == FeatureSelector::RemoteWakeup) {
    remote_wakeup_enabled_ = true;
    xfer.ack();
    return;
  }

  xfer.stall();
  return;
}

void UsbDevice::process_device_clear_feature(const SetupPacket &packet,
                                             CtrlOutTransfer &&xfer) {
  ESP_LOGI(LogTag, "USB: ClearFeature for device, feature=%u", packet.value);
  if (state_ != State::Address && state_ != State::Configured) {
    xfer.stall();
    return;
  }
  const auto feature = static_cast<FeatureSelector>(packet.value);
  if (feature == FeatureSelector::RemoteWakeup) {
    remote_wakeup_enabled_ = false;
    xfer.stall();
    return;
  }
  // No other feature type is supported for devices
  // FeatureSelector::TestMode cannot be cleared using ClearFeature
  xfer.stall();
}

void UsbDevice::process_get_descriptor(const SetupPacket &packet,
                                       CtrlInTransfer &&xfer) {
  ESP_LOGI(LogTag,
           "USB: get descriptor: value=0x%x index=%u",
           packet.value,
           packet.index);
  auto desc = impl_->get_descriptor(packet.value, packet.index);
  if (!desc.has_value()) {
    // No descriptor with this ID.
    ESP_LOGW(LogTag,
             "USB: query for unknown descriptor: value=0x%x index=%u",
             packet.value,
             packet.index);
    return xfer.stall();
  }

  return xfer.send_response_async(*desc);
}

CtrlOutTransfer UsbDevice::start_ctrl_out() {
  assert(ctrl_status_ == CtrlStatus::None);
  ctrl_status_ = CtrlStatus::OutData;
  return CtrlOutTransfer(this);
}

CtrlInTransfer UsbDevice::start_ctrl_in(uint16_t length) {
  assert(ctrl_status_ == CtrlStatus::None);
  ctrl_status_ = CtrlStatus::InData;
  return CtrlInTransfer(this, length);
}

void UsbDevice::stall_ctrl_transfer() {
  if (ctrl_status_ == CtrlStatus::InData) {
    ctrl_state_.in.reset();
  } else if (ctrl_status_ == CtrlStatus::OutData) {
    ctrl_state_.out.reset();
  }
  ctrl_status_ = CtrlStatus::None;
  stall_in_endpoint(0);
  stall_out_endpoint(0);
}

void UsbDevice::ctrl_out_ack() {
  if (ctrl_status_ != CtrlStatus::OutData) {
    ESP_LOGE(LogTag,
             "unexpected state when attempting to ack control OUT transfer: %d",
             static_cast<int>(ctrl_status_));
    return;
  }

  // Perform the status phase of an OUT transfer by sending a 0-length IN
  // packet.
  ctrl_status_ = CtrlStatus::OutStatus;
  start_in_send(0, nullptr, 0);
}

bool UsbDevice::start_ctrl_in_transfer(buf_view buf) {
  if (ctrl_status_ != CtrlStatus::InData) {
    ESP_LOGE(LogTag,
             "unexpected state when starting control IN transfer: %d",
             static_cast<int>(ctrl_status_));
    return false;
  }
  ctrl_state_.in.buf = buf;
  send_next_ctrl_in_packet();
  return true;
}

void UsbDevice::send_next_ctrl_in_packet() {
  auto &buf = ctrl_state_.in.buf;
  if (buf.size() > 0) {
    // Send next data packet
    const auto len =
        std::min(static_cast<size_t>(max_packet_size_), buf.size());
    ESP_LOGI(LogTag,
             "USB: send control data len=%lu",
             static_cast<unsigned long>(len));
    const auto next_packet = buf.substr(0, len);
    buf = buf.substr(len);
    start_in_send(0, next_packet.data(), next_packet.size());
  } else {
    // No data left to send.
    // Inform the callback that we have sent all data.
    ctrl_state_.in.buf = buf_view{};
    auto* cb = ctrl_state_.in.callback;
    ctrl_state_.in.callback = nullptr;
    if (cb) {
      // TODO: refactor how we handle the max length for IN transfers,
      // so that we can track this properly even if the device performs
      // multiple separate sends.
      uint16_t max_length_remaining = 0;
      cb->in_send_successful(CtrlInTransfer(this, max_length_remaining));
    } else {
      // If there is no callback, automatically send the final zero-length OUT
      // packet to indicate that the full IN transfer is complete.
      ESP_LOGI(LogTag, "USB: send control status packet");
      ctrl_status_ = CtrlStatus::InStatus;
      start_out_read(0, nullptr, 0);
    }
  }
}

void UsbDevice::ctrl_in_transfer_complete() {
  if (ctrl_status_ == CtrlStatus::OutStatus) {
    // We finished sending the STATUS packet of an OUT transfer.
    ctrl_status_ = CtrlStatus::None;
  } else if (ctrl_status_ == CtrlStatus::InData) {
    send_next_ctrl_in_packet();
  } else {
    ESP_LOGE(
        LogTag,
        "in_transfer_complete() called when no control transfer in progress");
  }
}

void UsbDevice::ctrl_out_transfer_complete() {
  if (ctrl_status_ == CtrlStatus::InStatus) {
    ctrl_status_ = CtrlStatus::None;
  } else {
    ESP_LOGE(LogTag,
             "out_transfer_complete() called in unexpected control "
             "transfer state %u",
             static_cast<int>(ctrl_status_));
  }
}

void UsbDevice::on_in_transfer_complete(uint8_t endpoint_num,
                                        uint32_t xferred_bytes) {
  if (endpoint_num == 0) {
    ctrl_in_transfer_complete();
    return;
  }

  // TODO
}

void UsbDevice::on_out_transfer_complete(uint8_t endpoint_num,
                                         uint32_t xferred_bytes) {
  if (endpoint_num == 0) {
    ctrl_out_transfer_complete();
    return;
  }

  // TODO
}

void UsbDevice::on_in_transfer_failed(uint8_t endpoint_num) {
}

} // namespace mantyl
