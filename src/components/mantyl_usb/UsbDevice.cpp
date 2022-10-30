// Copyright (c) 2022, Adam Simpkins
#include "mantyl_usb/UsbDevice.h"

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

  ctrl_transfer_.reset(max_ep0_packet_size);
  state_ = State::Default;
  config_id_ = 0;
  remote_wakeup_enabled_ = false;
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

  ESP_LOGI(LogTag, "on_setup_received");
  ESP_LOGI(LogTag, "on_setup_received2");

  // Process control request
  if (!process_setup_packet(packet)) {
    ESP_LOGW(LogTag,
             "unhandled SETUP packet: request_type=0x%04x request=0x%04x "
             "walue=0x%06x index=0x%06x length=0x%06x\n",
             packet.request_type,
             packet.request,
             packet.value,
             packet.index,
             packet.length);
    ctrl_transfer_.send_request_error(*this);
  }
}

bool UsbDevice::process_setup_packet(const SetupPacket& packet) {
  ESP_LOGI(LogTag,
           "USB: SETUP received: request_type=0x%04x request=0x%04x "
           "value=0x%06x index=0x%06x length=0x%06x",
           packet.request_type,
           packet.request,
           packet.value,
           packet.index,
           packet.length);

  if (packet.request_type == 0) {
    // Direction: Out (host to device)
    // Type: Standard request type
    // Recipient: Device
    return process_std_device_out_request(packet);
  } else if (packet.request_type == 0x80) {
    // Direction: In (device to host)
    // Type: Standard request type
    // Recipient: Device
    return process_std_device_in_request(packet);
  }

  const auto recipient = packet.get_recipient();
  if (recipient == SetupRecipient::Device) {
    if (packet.get_direction() == Direction::Out) {
      return process_non_std_device_out_request(packet);
    } else {
      return process_non_std_device_in_request(packet);
    }
  } else if (recipient == SetupRecipient::Interface) {
#if 0
    const uint8_t num = (packet.index & 0xff);
    for (const auto &iface : interfaces_) {
      if (iface && iface->get_number() == num) {
        handled = iface->handle_setup_packet(&packet);
        break;
      }
    }
#endif
  } else if (recipient == SetupRecipient::Endpoint) {
#if 0
    for (const auto &ep : endpoints_) {
      const uint8_t num = (packet.index & 0xf);
      if (ep && ep->get_number() == num) {
        handled = ep->handle_setup_packet(&packet);
        break;
      }
    }
#endif
  }

  return false;
}

bool UsbDevice::process_std_device_out_request(const SetupPacket &packet) {
  const auto std_req_type = packet.get_std_request();
  if (std_req_type == StdRequestType::SetAddress) {
    const uint8_t address = packet.value;
    ESP_LOGI(LogTag, "USB: set address: %u", packet.value);
    state_ = State::Address;
    set_address(address);
    return ctrl_transfer_.ack_out_transfer(*this);
  } else if (std_req_type == StdRequestType::SetConfiguration) {
    return process_set_configuration(packet);
  } else if (std_req_type == StdRequestType::SetFeature) {
    return process_device_set_feature(packet);
  } else if (std_req_type == StdRequestType::ClearFeature) {
    return process_device_clear_feature(packet);
  }
  return false;
}

bool UsbDevice::process_std_device_in_request(const SetupPacket &packet) {
  const auto std_req_type = packet.get_std_request();
  if (std_req_type == StdRequestType::GetDescriptor) {
    return process_get_descriptor(packet);
  } else if (std_req_type == StdRequestType::GetConfiguration) {
    ESP_LOGI(LogTag, "USB: get configuration");
    // The response packet we send points at our config_id_ member variable.
    // We shouldn't be able to receive a new SetConfiguration packet while we
    // are responding to this GetConfiguration packet, so config_id_ generally
    // should not be able to change while we are trying to transmit this
    // response.
    buf_view response(&config_id_, sizeof(config_id_));
    return send_ctrl_in(packet, response);
  } else if (std_req_type == StdRequestType::GetStatus) {
    ESP_LOGW(LogTag, "USB: GetStatus");
    // We put the response into the ControlTransfer::in_place_buf_
    const bool self_powered = impl_->is_self_powered();
    ctrl_transfer_.in_place_buf_[0] =
        (remote_wakeup_enabled_ ? 0x02 : 0x00) | (self_powered ? 0x01 : 0x00);
    ctrl_transfer_.in_place_buf_[1] = 0;
    return send_ctrl_in(packet,
                        buf_view(ctrl_transfer_.in_place_buf_.data(),
                                 ctrl_transfer_.in_place_buf_.size()));
  }
  return false;
}

bool UsbDevice::process_non_std_device_out_request(const SetupPacket &packet) {
  const auto req_type = packet.get_request_type();
  if (req_type == SetupReqType::Class) {
    // TODO: let impl_ handle this.
    // For now just hack this up to support HID

    if (packet.request == 0x0a) {
        // HID SetIdle
      return ctrl_transfer_.ack_out_transfer(*this);
    }
  }

  return false;
}

bool UsbDevice::process_non_std_device_in_request(const SetupPacket &packet) {
  const auto req_type = packet.get_request_type();
  if (req_type == SetupReqType::Class) {
    // TODO: let impl_ handle this.
  }

  // TODO
  return false;
}

bool UsbDevice::process_set_configuration(const SetupPacket &packet) {
  if (state_ != State::Address && state_ != State::Configured) {
    return false;
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
      ctrl_transfer_.send_request_error(*this);
      return true;
    }
  }
  return ctrl_transfer_.ack_out_transfer(*this);
}

bool UsbDevice::process_device_set_feature(const SetupPacket &packet) {
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
    return false;
  }

  if (state_ != State::Address && state_ != State::Configured) {
    return false;
  }

  if (feature == FeatureSelector::RemoteWakeup) {
    remote_wakeup_enabled_ = true;
    return ctrl_transfer_.ack_out_transfer(*this);
  }

  return false;
}

bool UsbDevice::process_device_clear_feature(const SetupPacket &packet) {
  ESP_LOGI(LogTag, "USB: ClearFeature for device, feature=%u", packet.value);
  if (state_ != State::Address && state_ != State::Configured) {
    return false;
  }
  const auto feature = static_cast<FeatureSelector>(packet.value);
  if (feature == FeatureSelector::RemoteWakeup) {
    remote_wakeup_enabled_ = false;
    return ctrl_transfer_.ack_out_transfer(*this);
  }
  // No other feature type is supported for devices
  // FeatureSelector::TestMode cannot be cleared using ClearFeature
  return false;
}

bool UsbDevice::process_get_descriptor(const SetupPacket &packet) {
  ESP_LOGI(LogTag,
           "USB: get descriptor: value=0x%x index=%u",
           packet.value,
           packet.index);
  auto desc = impl_->get_descriptor(packet.value, packet.index);
  if (!desc.has_value()) {
    // No descriptor with this ID.
    ctrl_transfer_.send_request_error(*this);
    return true;
  }

  return send_ctrl_in(packet, *desc);
}

bool UsbDevice::send_ctrl_in(const SetupPacket& setup, buf_view buf) {
  auto response_len =
      std::min(setup.length, static_cast<uint16_t>(buf.size()));
  buf = buf.substr(0, response_len);
  return ctrl_transfer_.start_transfer(*this, buf);
}

void UsbDevice::ControlTransfer::send_request_error(UsbDevice& usb) {
  usb.stall_in_endpoint(0);
  usb.stall_out_endpoint(0);
}

bool UsbDevice::ControlTransfer::ack_out_transfer(UsbDevice& usb) {
  if (status_ != Status::None) {
    ESP_LOGE(LogTag,
             "cannot ack control out: "
             "an EP0 transfer is already in progress!");
    return false;
  }

  // Perform the status phase of an OUT transfer by sending a 0-length IN
  // packet.
  status_ = Status::OutStatus;
  usb.start_in_send(0, nullptr, 0);
  return true;
}

bool UsbDevice::ControlTransfer::start_transfer(UsbDevice& usb, buf_view buf) {
  if (status_ != Status::None) {
    ESP_LOGE(LogTag, "an EP0 control transfer is already in progress!");
    return false;
  }
  buf_ = buf;
  status_ = Status::InData;
  send_next_in_packet(usb);
  return true;
}

void UsbDevice::ControlTransfer::send_next_in_packet(UsbDevice& usb) {
  if (buf_.size() > 0) {
    // Send next data packet
    const auto len =
        std::min(static_cast<size_t>(max_packet_size_), buf_.size());
    ESP_LOGI(LogTag,
             "USB: send control data len=%lu",
             static_cast<unsigned long>(len));
    const auto next_packet = buf_.substr(0, len);
    buf_ = buf_.substr(len);
    usb.start_in_send(0, next_packet.data(), next_packet.size());
  } else {
    // No data left.  Send the final zero-length OUT packet.
    ESP_LOGI(LogTag, "USB: send control status packet");
    status_ = Status::InStatus;
    usb.start_out_read(0, nullptr, 0);
  }
}

void UsbDevice::ControlTransfer::in_transfer_complete(UsbDevice& usb) {
  if (status_ == Status::OutStatus) {
    // We finished sending the STATUS packet of an OUT transfer.
    status_ = Status::None;
  } else if (status_ == Status::InData) {
    send_next_in_packet(usb);
  } else {
    ESP_LOGE(
        LogTag,
        "in_transfer_complete() called when no control transfer in progress");
  }
}

void UsbDevice::ControlTransfer::out_transfer_complete(UsbDevice& usb) {
  if (status_ == Status::InStatus) {
    buf_ = buf_view{};
    status_ = Status::None;
  } else {
    ESP_LOGE(LogTag,
             "out_transfer_complete() called in unexpected control "
             "transfer state %u",
             static_cast<int>(status_));
  }
}

void UsbDevice::ControlTransfer::reset(uint16_t max_packet_size) {
  max_packet_size_ = max_packet_size;
  buf_ = buf_view{};
  status_ = Status::None;
}

void UsbDevice::on_in_transfer_complete(uint8_t endpoint_num,
                                        uint32_t xferred_bytes) {
  if (endpoint_num == 0) {
    ctrl_transfer_.in_transfer_complete(*this);
    return;
  }

  // TODO
}

void UsbDevice::on_out_transfer_complete(uint8_t endpoint_num,
                                         uint32_t xferred_bytes) {
  if (endpoint_num == 0) {
    ctrl_transfer_.out_transfer_complete(*this);
    return;
  }

  // TODO
}

void UsbDevice::on_in_transfer_failed(uint8_t endpoint_num) {
}

} // namespace mantyl
