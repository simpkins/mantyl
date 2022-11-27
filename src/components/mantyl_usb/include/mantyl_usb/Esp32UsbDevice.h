// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "mantyl_usb/UsbDevice.h"

#include <array>
#include <cstdint>
#include <variant>

#include <esp_err.h>
#include <esp_intr_alloc.h>
#include <esp_private/usb_phy.h>
#include <soc/usb_struct.h>
#include <soc/usb_types.h>

#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>

namespace mantyl {

class StringDescriptorBuffer;

class Esp32UsbDevice : public UsbDevice {
public:
  enum class PhyType {
    Internal,
    External,
  };

  static constexpr uint8_t kSerialDescriptorCapacity = 38;
  static constexpr std::string_view kDefaultSerial = "00:00:00::00:00:00";

  explicit constexpr Esp32UsbDevice(UsbDeviceImpl *impl, usb_dev_t *usb = &USB0)
      : UsbDevice(impl), usb_{usb} {}
  explicit constexpr Esp32UsbDevice(usb_dev_t *usb = &USB0)
      : UsbDevice(), usb_{usb} {}
  ~Esp32UsbDevice();

  [[nodiscard]] bool init() override;
  [[nodiscard]] esp_err_t esp32_init(PhyType phy_type = PhyType::Internal);

  void loop() override;

  /**
   * Fill in a string descriptor buffer using information from the ESP32
   * MAC address.
   *
   * The string descriptor capacity should be at least
   * kSerialDescriptorCapacity.
   */
  static bool update_serial_number(StringDescriptorBuffer& descriptor);

private:
  struct UninitializedEvent {};
  struct BusResetEvent {};
  struct BusEnumDone {
    explicit BusEnumDone(uint8_t max_pkt_size)
        : max_ep0_packet_size{max_pkt_size} {}

    uint16_t max_ep0_packet_size{0};
  };
  struct SuspendEvent {};
  struct ResumeEvent {};
  struct InXferCompleteEvent {
    InXferCompleteEvent(uint8_t epnum, uint16_t len)
        : endpoint_num{epnum}, total_length{len} {}

    uint8_t endpoint_num{0};
    uint16_t total_length{0};
  };
  struct InXferFailedEvent {
    explicit InXferFailedEvent(uint8_t epnum) : endpoint_num{epnum} {}

    uint8_t endpoint_num{0};
  };
  struct OutXferCompleteEvent {
    OutXferCompleteEvent(uint8_t epnum, uint16_t len)
        : endpoint_num{epnum}, total_length{len} {}

    uint8_t endpoint_num{0};
    uint16_t total_length{0};
  };
  using Event = std::variant<UninitializedEvent,
                             BusResetEvent,
                             BusEnumDone,
                             SuspendEvent,
                             ResumeEvent,
                             SetupPacket,
                             InXferCompleteEvent,
                             InXferFailedEvent,
                             OutXferCompleteEvent>;
  static_assert(std::is_trivially_copyable_v<Event>,
                "Event must be trivially copyable");

  // Speed bits used by the dcfg and dsts registers.
  // These unfortunately are not defined in soc/usb_reg.h
  enum Speed : uint32_t {
    High30Mhz = 0,
    Full30Mhz = 1,
    Low6Mhz = 2,
    Full48Mhz = 3,
  };

  struct OutTransferInfo {
    uint8_t *buffer{nullptr};
    uint16_t buffer_size{0};
    uint16_t received_bytes{0};
    uint16_t max_size{0};
    bool recv_complete{false};
  };
  struct InTransferInfo {
    const uint8_t *buffer{nullptr};
    uint16_t size{0};
    uint16_t max_size{0};
  };
  struct EndpointTransferInfo {
    OutTransferInfo out;
    InTransferInfo in;
  };
  static constexpr uint8_t kEndpointInAddr = 0x80;
  static constexpr uint8_t kMaxEventQueueSize = 32;
  // The maximum number of FIFOs for IN endpoints
  static constexpr uint8_t kMaxInFIFOs = 5;
  // The size of each IN FIFO, in bytes
  static constexpr uint16_t kInFIFOSize = 1024;

  // The interrupt handler maintains a pointer to the Esp32UsbDevice object,
  // so we cannot be copied or moved.
  Esp32UsbDevice(const Esp32UsbDevice&) = delete;
  Esp32UsbDevice& operator=(const Esp32UsbDevice&) = delete;

  [[nodiscard]] esp_err_t init_phy(PhyType phy_type);

  void handle_event(Event& event);
  void send_event_from_isr(const Event& event);
  template <typename T, typename... Args>
  void send_event_from_isr(Args &&... args) {
    Event e{std::in_place_type<T>, std::forward<Args>(args)...};
    send_event_from_isr(e);
  }

  [[nodiscard]] esp_err_t enable_interrupts();
  static void static_interrupt_handler(void *arg);
  void interrupt_handler();
  void bus_reset();
  void enum_done();

  void read_rx_fifo();
  void receive_packet(uint8_t endpoint_num, uint16_t packet_size);

  /**
   * Write pending IN packet data to the fifo.
   *
   * Returns true if all data to transfer has been written, or false if more
   * data still needs to be written in the future.
   */
  bool transmit_packet(uint8_t endpoint_num, uint8_t fifo_num);

  void handle_out_endpoint_intr();
  void handle_in_endpoint_intr();
  void handle_out_intr(uint8_t endpoint_num);
  void handle_in_intr(uint8_t endpoint_num);

  void set_address(uint8_t address) override;
  void stall_in_endpoint(uint8_t endpoint_num) override;
  void stall_out_endpoint(uint8_t endpoint_num) override;
  void clear_in_stall(uint8_t endpoint_num) override;
  void clear_out_stall(uint8_t endpoint_num) override;

  void start_in_send(uint8_t endpoint_num,
                     const uint8_t *buffer,
                     uint16_t size) override;
  void start_out_read(uint8_t endpoint_num,
                      uint8_t *buffer,
                      uint16_t buffer_size) override;

  // Set the NAK bit on all endpoints
  void all_endpoints_nak();

  uint8_t get_free_fifo();
  void close_all_endpoints() override;

  usb_dev_t* usb_ = nullptr;
  usb_phy_handle_t phy_ = nullptr;
  intr_handle_t interrupt_handle_ = nullptr;
  uint8_t allocated_fifos_ = 1; // FIFO0 is always in use
  std::array<EndpointTransferInfo, USB_OUT_EP_NUM> xfer_status_;
  union {
    std::array<uint32_t, 2> u32;
    SetupPacket setup;
  } setup_packet_ = {};

  StaticQueue_t queue_storage_ = {};
  QueueHandle_t event_queue_ = nullptr;
  std::array<uint8_t, sizeof(Event) * kMaxEventQueueSize> queue_buffer_ = {};
};

} // namespace mantyl
