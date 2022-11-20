// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "mantyl_usb/usb_types.h"

#include <array>
#include <cstdint>
#include <optional>
#include <string_view>

namespace mantyl {

using buf_view = std::basic_string_view<uint8_t>;
class CtrlInTransfer;
class CtrlOutTransfer;

/**
 * UsbDeviceImpl defines the API that USB devices implement.
 *
 * When a device is plugged into the bus, the typical order of events will be:
 * - on_reset()
 * - on_enumerated() once USB speed has been negotiated
 * - some number of get_descriptor() queries triggered by the host to query the
 *   device type, available configurations, and other information
 * - on_configured() when the host selects a device configuration to use.
 *
 * After this, additional get_descriptor() calls may occur, as well as other
 * USB events interacting with the various configured endpoints and interfaces.
 */
class UsbDeviceImpl {
public:
  virtual ~UsbDeviceImpl() {}

  /**
   * Return the given USB descriptor.
   *
   * The returned buffer must remain valid for the lifetime of the UsbDevice,
   * or until the UsbDevice is disconnected.
   */
  virtual std::optional<buf_view> get_descriptor(uint16_t value,
                                                 uint16_t index) = 0;

  /**
   * on_reset() will be called when a reset state is detected on the bus.
   *
   * Implementations do not necessarily need to take any action on this event,
   * and the default implementation is a no-op.
   *
   * After a reset, on_enumerated() will be called once the device has been
   * re-enumerated on the bus.
   */
  virtual void on_reset() {}

  /**
   * Called once the device has been enumerated on the bus, and the USB speed
   * has been selected.
   *
   * Receives as input the maximum allowed packet size for endpoint 0, which is
   * based on the selected speed.
   *
   * The implementation may select a lower actual maximum packet size for
   * endpoint 0, and should return the selected size.  The implementation must
   * ensure that the bMaxPacketSize field in the device descriptor returned by
   * get_descriptor() matches this value.  Implementations may want to update
   * their device descriptor contents when on_enumerated() is called.
   */
  virtual uint8_t on_enumerated(uint8_t max_ep0_size) = 0;

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

  /**
   * on_wakeup() will be called once activity is resumed on the bus after as
   * suspend event.
   */
  virtual void on_wakeup() {}

  /**
   * on_configured() will be called once the host selects a device
   * configuration to use.
   *
   * The implementation should return true on success, or false if this is an
   * invalid configuration ID.
   */
  virtual bool on_configured(uint8_t config_id) = 0;
  virtual void on_unconfigured() {}

  /**
   * Returns true if the device is currently self powered.
   *
   * This is called when the host sends a GET_STATUS request to query the
   * status of the device.
   */
  virtual bool is_self_powered() {
    return false;
  }

  virtual void handle_ep0_interface_in(uint8_t interface,
                                       const SetupPacket &packet,
                                       CtrlInTransfer &&xfer) = 0;
  virtual void handle_ep0_interface_out(uint8_t interface,
                                        const SetupPacket &packet,
                                        CtrlOutTransfer &&xfer) = 0;
  virtual void handle_ep0_endpoint_in(uint8_t endpoint,
                                      const SetupPacket &packet,
                                      CtrlInTransfer &&xfer) = 0;
  virtual void handle_ep0_endpoint_out(uint8_t endpoint,
                                       const SetupPacket &packet,
                                       CtrlOutTransfer &&xfer) = 0;

  virtual void handle_ep0_class_in(const SetupPacket &packet,
                                   CtrlInTransfer &&xfer) {}
  virtual void handle_ep0_class_out(const SetupPacket &packet,
                                    CtrlOutTransfer &&xfer) {}
  virtual void handle_ep0_vendor_in(const SetupPacket &packet,
                                    CtrlInTransfer &&xfer) {}
  virtual void handle_ep0_vendor_out(const SetupPacket &packet,
                                     CtrlOutTransfer &&xfer) {}
};

class UsbDevice {
public:
  explicit constexpr UsbDevice(UsbDeviceImpl* impl) : impl_{impl} {}

  bool is_remote_wakeup_enabled() const {
    return remote_wakeup_enabled_;
  }

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
  void on_bus_reset();
  void on_enum_done(uint16_t max_ep0_packet_size);
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
  friend class CtrlInTransfer;
  friend class CtrlOutTransfer;
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
    // A small buffer for generating responses to some standard control
    // transfer requests.
    std::array<uint8_t, 2> in_place_buf_{};
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

  void process_setup_packet(const SetupPacket &packet);
  void process_std_device_in_request(const SetupPacket &packet,
                                     CtrlInTransfer &&xfer);
  void process_std_device_out_request(const SetupPacket &packet,
                                      CtrlOutTransfer &&xfer);
  void process_non_std_device_in_request(const SetupPacket &packet,
                                         CtrlInTransfer &&xfer);
  void process_non_std_device_out_request(const SetupPacket &packet,
                                          CtrlOutTransfer &&xfer);
  void process_set_configuration(const SetupPacket &packet,
                                 CtrlOutTransfer &&xfer);
  void process_device_set_feature(const SetupPacket &packet,
                                  CtrlOutTransfer &&xfer);
  void process_device_clear_feature(const SetupPacket &packet,
                                    CtrlOutTransfer &&xfer);
  void process_get_descriptor(const SetupPacket &packet, CtrlInTransfer &&xfer);
  [[nodiscard]] bool send_ctrl_in(const SetupPacket &packet, buf_view buf);

  // All state is only accessed from within the USB task,
  // so we do not need any synchronization.
  State state_{State::Uninit};
  UsbDeviceImpl *impl_{nullptr};

  // Endpoint 0 status
  ControlTransfer ctrl_transfer_;
  uint8_t config_id_{0};
  bool remote_wakeup_enabled_{false};
};

} // namespace mantyl
