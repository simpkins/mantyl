// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "usb/usb_types.h"
#include "usb/UsbDescriptorMap.h"

#include <cstdint>
#include <string_view>

namespace mantyl {

class UsbDevice {
public:
  class StateCallback {
  public:
    virtual ~StateCallback() {}

    /**
     * on_suspend() will be invoked when the USB bus is suspended.
     *
     * The USB spec requires that devices actually enter a suspend state within
     * 10ms, and draw no more than the suspend current.  The suspend current
     * is:
     * - 500 uA for low-power devices
     * - 2.5 mA for high-power devices that support remote-wakeup
     */
    virtual void on_suspend() = 0;
    virtual void on_wakeup() {}

    virtual void on_reset() {}
    virtual bool on_configured(uint8_t config_id) = 0;
    virtual void on_unconfigured() {}

#if 0
    // Handle a Class or Vendor request to the device on endpoint 0
    virtual void handle_device_in_request(SetupPacket& packet) = 0;
    virtual void handle_device_out_request(SetupPacket& packet) = 0;
#endif
  };

  UsbDevice();

protected:
  // Figure 9-1 in the USB 2.0 spec lists the various device states.
  //
  // We do not distinguish between unattached/attached/powered here.
  // The Uninit state captures all of these.
  enum class State : uint8_t {
    Uninit = 0, // Has not seen a bus reset yet
    Default = 1, // has been reset, but no address assigned yet
    Address = 2, // address assigned, but not configured
    Configured = 3,
  };
  // Suspended is a bit flag that can be ANDed with any of the
  // other states.
  enum class StateFlag : uint8_t {
    Suspended = 0x10,
  };
  enum class StateMask : uint8_t {
    Mask = 0x0f,
  };

  friend State &operator|=(State &s, StateFlag flag) {
    s = static_cast<State>(static_cast<uint8_t>(s) |
                           static_cast<uint8_t>(flag));
    return s;
  }
  friend State &operator&=(State &s, StateFlag flag) {
    s = static_cast<State>(static_cast<uint8_t>(s) &
                           static_cast<uint8_t>(flag));
    return s;
  }
  friend StateFlag operator&(State s, StateFlag flag) {
    return static_cast<StateFlag>(static_cast<uint8_t>(s) &
                                  static_cast<uint8_t>(flag));
  }
  friend StateFlag operator~(StateFlag flag) {
    return static_cast<StateFlag>(~static_cast<uint8_t>(flag));
  }
  friend State operator&(State s, StateMask mask) {
    return static_cast<State>(static_cast<uint8_t>(s) &
                              static_cast<uint8_t>(mask));
  }

  // Event handler functions to be invoked by subclasses.
  // These must not be invoked from within an interrupt.
  void on_bus_reset(uint16_t max_ep0_packet_size);
  void on_suspend();
  void on_resume();
  void on_setup_received(const SetupPacket& packet);
  void on_in_transfer_complete(uint8_t endpoint_num, uint32_t xferred_bytes);
  void on_in_transfer_failed(uint8_t endpoint_num);
  void on_out_transfer_complete(uint8_t endpoint_num, uint32_t xferred_bytes);

  // Methods that must be implemented by subclasses.
  virtual void stall_in_endpoint(uint8_t endpoint_num) = 0;
  virtual void stall_out_endpoint(uint8_t endpoint_num) = 0;
  virtual void clear_in_stall(uint8_t endpoint_num) = 0;
  virtual void clear_out_stall(uint8_t endpoint_num) = 0;
  virtual void close_all_endpoints() = 0;

private:
  using buf_view = std::basic_string_view<uint8_t>;
  class ControlTransfer {
  public:
    enum Status {
      None,
      InData,
      InStatus,
      OutData,
      OutStatus,
    };

    void reset(uint16_t max_packet_size);

    void send_request_error(UsbDevice& usb);
    [[nodiscard]] bool ack_out_transfer(UsbDevice& usb);
    [[nodiscard]] bool start_transfer(UsbDevice& usb, buf_view buf);
    void send_next_in_packet(UsbDevice& usb);
    void in_transfer_complete(UsbDevice& usb);
    void out_transfer_complete(UsbDevice& usb);

    uint16_t max_packet_size_{0};
    Status status_{Status::None};
    buf_view buf_;
  };

  UsbDevice(UsbDevice const &) = delete;
  UsbDevice &operator=(UsbDevice const &) = delete;

  /**
   * Set the address.
   *
   * Called when handling a SetAddress SETUP packet.
   *
   * This must be implemented by subclasses.
   */
  virtual void set_address(uint8_t address) = 0;

  virtual void
  start_in_send(uint8_t endpoint_num, const uint8_t *buffer, uint16_t size) = 0;
  virtual void start_out_read(uint8_t endpoint_num,
                              uint8_t *buffer,
                              uint16_t buffer_size) = 0;

  [[nodiscard]] bool process_setup_packet(const SetupPacket &packet);
  [[nodiscard]] bool process_std_device_in_request(const SetupPacket &packet);
  [[nodiscard]] bool process_std_device_out_request(const SetupPacket &packet);
  [[nodiscard]] bool
  process_non_std_device_in_request(const SetupPacket &packet);
  [[nodiscard]] bool
  process_non_std_device_out_request(const SetupPacket &packet);
  [[nodiscard]] bool process_set_configuration(const SetupPacket &packet);
  [[nodiscard]] bool process_device_set_feature(const SetupPacket &packet);
  [[nodiscard]] bool process_device_clear_feature(const SetupPacket &packet);
  [[nodiscard]] bool process_get_descriptor(const SetupPacket &packet);
  [[nodiscard]] bool send_ctrl_in(const SetupPacket &packet, buf_view buf);

  // All state is only accessed from within the USB task,
  // so we do not need any synchronization.
  State state_{State::Uninit};
  StateCallback *state_callback_{nullptr};
  UsbDescriptorMap descriptors_;

  // Endpoint 0 status
  ControlTransfer ctrl_transfer_;
  uint8_t config_id_{0};
  bool remote_wakeup_enabled_{false};
};

} // namespace mantyl
