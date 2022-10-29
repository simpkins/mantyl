// Copyright (c) 2022, Adam Simpkins
#include "mantyl_usb/Esp32UsbDevice.h"

#include <esp_check.h>
#include <esp_log.h>
#include <esp_private/usb_phy.h>
#include <soc/periph_defs.h>
#include <soc/usb_periph.h>

#include <atomic>
#include <cstring>

namespace {
const char *LogTag = "mantyl.usb.esp32";

inline void set_bits(volatile uint32_t &value, uint32_t bits) {
  value = (value | bits);
}
inline void clear_bits(volatile uint32_t &value, uint32_t bits) {
  value = (value & ~bits);
}

template<class... Ts> struct overloaded : Ts... { using Ts::operator()...; };
template<class... Ts> overloaded(Ts...) -> overloaded<Ts...>;

} // namespace

namespace mantyl {

Esp32UsbDevice::~Esp32UsbDevice() {
  if (interrupt_handle_) {
    esp_intr_free(interrupt_handle_);
  }
  if (phy_) {
    usb_del_phy(phy_);
  }
}

void Esp32UsbDevice::loop() {
  int n = 0;
  while (true) {
    static constexpr TickType_t max_wait = pdMS_TO_TICKS(1000);
    Event event;
    if (xQueueReceive(event_queue_, &event, max_wait) == pdTRUE) {
      printf("got event: %d\n", static_cast<int>(event.index()));
      handle_event(event);
    }
    printf("tick %d\n", n);
    ++n;
  }
}

void Esp32UsbDevice::handle_event(Event& event) {
  std::visit(
      overloaded{
          [this](UninitializedEvent &) {
            // this shouldn't be possible
            ESP_EARLY_LOGE(LogTag, "unexpected USB uninitialized event");
          },
          [this](BusResetEvent &) { on_bus_reset(); },
          [this](BusEnumDone &ev) { on_enum_done(ev.max_ep0_packet_size); },
          [this](SuspendEvent &) { on_suspend(); },
          [this](ResumeEvent &) { on_resume(); },
          [this](SetupPacket &packet) { on_setup_received(packet); },
          [this](InXferCompleteEvent &event) {
            on_in_transfer_complete(event.endpoint_num, event.total_length);
          },
          [this](InXferFailedEvent &event) {
            on_in_transfer_failed(event.endpoint_num);
          },
          [this](OutXferCompleteEvent &event) {
            on_out_transfer_complete(event.endpoint_num, event.total_length);
          },
      },
      event);
}

void Esp32UsbDevice::send_event_from_isr(const Event& event) {
  BaseType_t higher_prio_task_woken;
  BaseType_t res =
      xQueueSendToBackFromISR(event_queue_, &event, &higher_prio_task_woken);
  if (higher_prio_task_woken) {
    portYIELD_FROM_ISR();
  }

  if (res != pdPASS) {
    ESP_EARLY_LOGW(LogTag, "USB event queue full; unable to send event");
  }
}

esp_err_t Esp32UsbDevice::init(PhyType phy_type) {
  ESP_LOGI(LogTag, "USB device init");

  event_queue_ = xQueueCreateStatic(
      kMaxEventQueueSize, sizeof(Event), queue_buffer_.data(), &queue_storage_);

  const auto err = init_phy(phy_type);
  if (err != ESP_OK) {
    return err;
  }

  // The ESP32-S3 technical reference manual doesn't seem to document the USB
  // registers terrible well, at least as far as I can find.  The soc/usb_reg.h
  // has a few comments documenting some of the behavior.
  //
  // This initialization logic was largely adapted from the ESP DCD code in
  // TinyUSB.

  // Ensure the data line pull-up is disabled as we perform initialization.
  set_bits(usb_->dctl, USB_SFTDISCON_M);

  // During initialization, send a stall on receipt of
  // any non-zero length OUT packet.  Also set speed.
  set_bits(usb_->dcfg, USB_NZSTSOUTHSHK_M | Speed::Full48Mhz);

  // Configure AHB interrupts:
  // - enable interrupt when TxFIFO is empty
  // - global interrupts enable flag
  set_bits(usb_->gahbcfg, USB_NPTXFEMPLVL_M | USB_GLBLLNTRMSK_M);
  // USB configuration:
  // - Force device mode (rather than OTG)
  set_bits(usb_->gusbcfg, USB_FORCEDEVMODE_M);
  // OTG configuration:
  // - disable overrides
  clear_bits(usb_->gotgctl,
             USB_BVALIDOVVAL_M | USB_BVALIDOVEN_M | USB_VBVALIDOVVAL_M);

  // Configure all endpoints to NAK
  all_endpoints_nak();

  // Interrupt configuration
  usb_->gintmsk = 0;          // mask all interrupts
  usb_->gotgint = 0xffffffff; // clear OTG interrupts
                              // (even though we leave OTG interrupts disabled)
  usb_->gintsts = 0xffffffff; // clear pending interrupts
  usb_->gintmsk = USB_MODEMISMSK_M | USB_RXFLVIMSK_M | USB_ERLYSUSPMSK_M |
                 USB_USBSUSPMSK_M | USB_USBRSTMSK_M | USB_ENUMDONEMSK_M |
                 USB_RESETDETMSK_M | USB_DISCONNINTMSK_M;

  ESP_RETURN_ON_ERROR(
      enable_interrupts(), LogTag, "error enabling USB interrupts");

  // Enable the data line pull-up to connect to the bus.
  clear_bits(usb_->dctl, USB_SFTDISCON_M);

  return ESP_OK;
}

esp_err_t Esp32UsbDevice::init_phy(PhyType phy_type) {
  usb_phy_gpio_conf_t gpio_conf = {
      .vp_io_num = USBPHY_VP_NUM,
      .vm_io_num = USBPHY_VM_NUM,
      .rcv_io_num = USBPHY_RCV_NUM,
      .oen_io_num = USBPHY_OEN_NUM,
      .vpo_io_num = USBPHY_VPO_NUM,
      .vmo_io_num = USBPHY_VMO_NUM,
  };
  usb_phy_config_t phy_conf = {
      .controller = USB_PHY_CTRL_OTG,
      .target = phy_type == PhyType::External ? USB_PHY_TARGET_EXT
                                              : USB_PHY_TARGET_INT,
      .otg_mode = USB_OTG_MODE_DEVICE,
      .otg_speed = USB_PHY_SPEED_UNDEFINED,
      .gpio_conf = phy_type == PhyType::External ? &gpio_conf : nullptr,
  };
  ESP_RETURN_ON_ERROR(
      usb_new_phy(&phy_conf, &phy_), LogTag, "error configuring USB PHY");
  return ESP_OK;
}

esp_err_t Esp32UsbDevice::enable_interrupts() {
  return esp_intr_alloc(ETS_USB_INTR_SOURCE,
                        ESP_INTR_FLAG_LOWMED,
                        Esp32UsbDevice::static_interrupt_handler,
                        this,
                        &interrupt_handle_);
}

void Esp32UsbDevice::all_endpoints_nak() {
  for (int ep_num = 0; ep_num < USB_OUT_EP_NUM; ++ep_num) {
    set_bits(usb_->out_ep_reg[ep_num].doepctl, USB_DO_SNAK0_M);
  }
}

void Esp32UsbDevice::static_interrupt_handler(void *arg) {
  auto *usb = static_cast<Esp32UsbDevice *>(arg);
  usb->interrupt_handler();
}

void Esp32UsbDevice::interrupt_handler() {
  const uint32_t mask = usb_->gintmsk;
  const uint32_t int_status = usb_->gintsts & mask;
  static std::atomic<unsigned int> s_intr_count;
  auto intr_count = s_intr_count.fetch_add(1);
  ESP_EARLY_LOGI(LogTag,
                 "USB interrupt %u: 0x%02" PRIx32 " 0x%02" PRIx32,
                 intr_count,
                 mask,
                 int_status);

  // Check int_status for all of the interrupt bits that we need to handle.
  // As we process each interrupt, set that bit in gintsts to clear the
  // interrupt.  Do this before sending the event back to the main task, as
  // send_event_from_isr() may yield back to another higher priority task
  // before returning.

  if (int_status & (USB_USBRST_M | USB_RESETDET_M)) {
    // USB_USBRST_M indicates a reset.
    // USB_RESETDET_M indicates a reset detected while in suspend mode.
    //
    // These two tend to be asserted together when first initializing the bus
    // as a device.
    ESP_EARLY_LOGI(LogTag, "USB int: reset");
    usb_->gintsts = USB_USBRST_M | USB_RESETDET_M;
    allocated_fifos_ = 1;
    bus_reset();
  }

  if (int_status & USB_ENUMDONE_M) {
    usb_->gintsts = USB_ENUMDONE_M;
    enum_done();
  }

  if (int_status & USB_ERLYSUSPMSK_M) {
    ESP_EARLY_LOGI(LogTag, "USB int: early suspend");
    usb_->gintsts = USB_ERLYSUSPMSK_M;
  }

  if (int_status & USB_USBSUSP_M) {
    ESP_EARLY_LOGI(LogTag, "USB int: suspend");
    usb_->gintsts = USB_USBSUSP_M;
    send_event_from_isr<SuspendEvent>();
  }

  if (int_status & USB_WKUPINT_M) {
    ESP_EARLY_LOGI(LogTag, "USB int: resume");
    usb_->gintsts = USB_WKUPINT_M;
    send_event_from_isr<ResumeEvent>();
  }

  if (int_status & USB_SOF_M) {
    // Start of frame.
    //
    // We only enable SOF interupts to detect when the bus has resumed after we
    // have triggered a remote wakeup.  Re-disable SOF interrupts, and then
    // send a resume event to the main event handler.
    ESP_EARLY_LOGI(LogTag, "USB int: start of frame");
    usb_->gintsts = USB_SOF_M;
    clear_bits(usb_->gintmsk, USB_SOFMSK_M);
    send_event_from_isr<ResumeEvent>();
  }

  if (int_status & USB_RXFLVI_M) {
    ESP_EARLY_LOGI(LogTag, "USB int: rx");
    // No need to update usb_->gintsts to indicate we have handled the
    // interrupt; this will be cleared when we read from the fifo.

    // Disable the RXFLVL interrupt while reading data from the FIFO
    clear_bits(usb_->gintmsk, USB_RXFLVIMSK_M);
    read_rx_fifo();
    set_bits(usb_->gintmsk, USB_RXFLVIMSK_M);
  }

  if (int_status & USB_OEPINT_M) {
    // OUT endpoint interrupt
    ESP_EARLY_LOGI(LogTag, "USB int: OUT endpoint");
    // No need to update usb_->gintsts to indicate we have handled the
    // interrupt; handle_out_endpoint_intr() will update the endpoint doepint
    // register instead.
    handle_out_endpoint_intr();
  }

  if (int_status & USB_IEPINT_M) {
    // IN endpoint interrupt
    ESP_EARLY_LOGI(LogTag, "USB int: IN endpoint");
    // No need to update usb_->gintsts to indicate we have handled the
    // interrupt; handle_in_endpoint_intr() will update the endpoint diepint
    // register instead.
    handle_in_endpoint_intr();
  }

  // Clear other interrupt bits that we do not handle.
  usb_->gintsts = USB_CURMOD_INT_M | USB_MODEMIS_M | USB_NPTXFEMP_M |
                  USB_GINNAKEFF_M | USB_GOUTNAKEFF | USB_ERLYSUSP_M |
                  USB_ISOOUTDROP_M | USB_EOPF_M | USB_EPMIS_M |
                  USB_INCOMPISOIN_M | USB_INCOMPIP_M | USB_FETSUSP_M |
                  USB_PTXFEMP_M;
  ESP_EARLY_LOGI(LogTag, "USB interrupt %u done", intr_count);
}

void Esp32UsbDevice::bus_reset() {
  all_endpoints_nak();

  // clear the device address
  clear_bits(usb_->dcfg, USB_DEVADDR_M);

  usb_->daintmsk = USB_OUTEPMSK0_M | USB_INEPMSK0_M;
  usb_->doepmsk = USB_SETUPMSK_M | USB_XFERCOMPLMSK;
  usb_->diepmsk = USB_TIMEOUTMSK_M | USB_DI_XFERCOMPLMSK_M;

  // The Espressif tinyusb code uses 52 for the shared RX fifo size.
  // Note that this is 52 4-byte words, or 208 bytes total.
  //
  // They reference the "USB Data FIFOs" section of the reference manual,
  // also the technical reference manual copy I have (v1.0, which was just
  // released a few weeks ago) does not appear to explicitly document the RX
  // FIFO size recommendations that they reference.
  set_bits(usb_->grstctl, 0x10 << USB_TXFNUM_S); // fifo 0x10,
  set_bits(usb_->grstctl, USB_TXFFLSH_M);        // Flush fifo
  usb_->grxfsiz = 52;

  // Control IN uses FIFO 0 with 64 bytes ( 16 32-bit word )
  usb_->gnptxfsiz = (16 << USB_NPTXFDEP_S) | (usb_->grxfsiz & 0x0000ffffUL);

  // Ready to receive SETUP packet.
  set_bits(usb_->out_ep_reg[0].doeptsiz, USB_SUPCNT0_M);

  set_bits(usb_->gintmsk, USB_IEPINTMSK_M | USB_OEPINTMSK_M);

  send_event_from_isr<BusResetEvent>();
}

void Esp32UsbDevice::enum_done() {
  // The Device Status register (DSTS_REG) contains the enumerated speed
  // We pretty much always expect this to be Speed::Full48Mhz
  uint32_t enum_spd = (usb_->dsts >> USB_ENUMSPD_S) & (USB_ENUMSPD_V);
  ESP_EARLY_LOGI(LogTag, "USB int: enumeration done; speed=%d", enum_spd);

  uint16_t max_ep0_packet_size;
  if (enum_spd == Speed::Full48Mhz) {
    // Max packet size is 64 bytes
    clear_bits(usb_->in_ep_reg[0].diepctl, USB_D_MPS0_V);
    max_ep0_packet_size = 64;
  } else {
    // Max packet size is 8 bits
    set_bits(usb_->in_ep_reg[0].diepctl, USB_D_MPS0_V);
    max_ep0_packet_size = 8;
  }
  // Clear the stall bit
  clear_bits(usb_->in_ep_reg[0].diepctl, USB_D_STALL0_M);

  xfer_status_[0].out.max_size = max_ep0_packet_size;
  xfer_status_[0].in.max_size = max_ep0_packet_size;
  send_event_from_isr<BusEnumDone>(max_ep0_packet_size);
}

void Esp32UsbDevice::read_rx_fifo() {
  // USB_PKTSTS values from the comments in soc/usb_reg.h
  enum Pktsts : uint32_t {
    GlobalOutNak = 1,
    PktReceived = 2,
    TxComplete = 3,
    SetupComplete = 4,
    DataToggleError = 5, // host mode only
    SetupReceived = 6,
    ChannelHalted = 7, // host mode only
  };

  uint32_t const ctl_word = usb_->grxstsp;
  uint8_t const pktsts = (ctl_word & USB_PKTSTS_M) >> USB_PKTSTS_S;
  switch (pktsts) {
  case Pktsts::GlobalOutNak:
    ESP_EARLY_LOGI(LogTag, "USB RX: Global OUT NAK");
    break;
  case Pktsts::PktReceived: {
    uint8_t const endpoint_num = (ctl_word & USB_CHNUM_M) >> USB_CHNUM_S;
    uint16_t const byte_count = (ctl_word & USB_BCNT_M) >> USB_BCNT_S;
    ESP_EARLY_LOGI(LogTag, "USB RX: OUT packet received; size=%u", byte_count);
    receive_packet(endpoint_num, byte_count);
    break;
  }
  case Pktsts::TxComplete:
    // OUT packet done
    ESP_EARLY_LOGI(LogTag, "USB RX: OUT packet done");
    break;
  case Pktsts::SetupComplete: {
    // Setup OUT packet received.  After this we should receive an OUT endpoint
    // interrupt with the SETUP bit set.  We generate an event to handle the
    // SetupPacket there.
    uint8_t const endpoint_num = (ctl_word & USB_CHNUM_M) >> USB_CHNUM_S;
    ESP_EARLY_LOGI(LogTag, "USB RX: setup done");
    // Set the USB_SUPCNT0_M bits in the doeptsiz register, to indicate that
    // we can receive up to 3 DATA packets in this setup transfer.
    set_bits(usb_->out_ep_reg[endpoint_num].doeptsiz, USB_SUPCNT0_M);
    break;
  }
  case Pktsts::SetupReceived: {
    // We should receive a SetupComplete interrupt after SetupReceived.
    // We simply store the setup packet data here.
    volatile uint32_t *rx_fifo = usb_->fifo[0];
    setup_packet_.u32[0] = (*rx_fifo);
    setup_packet_.u32[1] = (*rx_fifo);
    ESP_EARLY_LOGI(LogTag,
                   "USB RX: setup packet: 0x%08x 0x%08x",
                   setup_packet_.u32[0],
                   setup_packet_.u32[1]);
    break;
  }
  default:
    ESP_EARLY_LOGE(LogTag, "USB RX: unexpected pktsts value: %x", pktsts);
    break;
  }
}

void Esp32UsbDevice::receive_packet(uint8_t endpoint_num, uint16_t packet_size) {
  // TODO: do this work in the main task rather than the interrupt handler?
  auto *xfer = &xfer_status_[endpoint_num].out;
  // All OUT transfers are performed using FIFO 0.
  volatile uint32_t *rx_fifo = usb_->fifo[0];

  // We can read up to the smaller of:
  // - the remaining size until the buffer is full
  // - the maximum transfer size for this endpoint
  // - or the packet_size argument
  //
  // TODO: If bufsize_left is less than packet_size, the host may have sent a
  // full packet but we are not able to read all of it.  I haven't played
  // around with how the ESP32 behaves in this case, but I think it will mess
  // up the current code's detection of end of transmission.  We probably
  // should require that start_out_read() always be called with a buffer size
  // that is a multiple of the maximum endpoint packet size.
  const uint16_t bufsize_left = xfer->buffer_size - xfer->received_bytes;
  uint16_t read_size =
      std::min(std::min(bufsize_left, xfer->max_size), packet_size);

  uint8_t *out_ptr = (xfer->buffer + xfer->received_bytes);
  uint8_t *const end = out_ptr + read_size;
  // Read 32-bit words at a time from the FIFO
  // Copy into out_ptr with memcmp, since out_ptr may not be word-aligned.
  while (out_ptr + 4 < end) {
    const uint32_t tmp = (*rx_fifo);
    memcpy(out_ptr, &tmp, 4);
    out_ptr += 4;
  }
  if (out_ptr < end) {
    const uint32_t tmp = (*rx_fifo);
    memcpy(out_ptr, &tmp, end - out_ptr);
  }

  xfer->received_bytes = end - xfer->buffer;

  // An OUT packet with a length less than the maximum endpoint packet size
  // always indicates the end of a transfer.
  xfer->recv_complete = (packet_size < xfer->max_size) ||
                        (xfer->received_bytes == xfer->buffer_size);
}

bool Esp32UsbDevice::transmit_packet(uint8_t endpoint_num, uint8_t fifo_num) {
  // TODO: do this work in the main task rather than the interrupt handler?
  ESP_EARLY_LOGI(LogTag, "USB: transmit_packet");

  auto &xfer = xfer_status_[endpoint_num].in;
  volatile usb_in_endpoint_t *in_ep = &usb_->in_ep_reg[endpoint_num];
  volatile uint32_t *tx_fifo = usb_->fifo[fifo_num];

  // soc/usb_reg.h documents the transfer size (USB_D_XFERSIZE0) only being
  // 8 bits wide, but it seems like it is actually 19 bits wide.
  uint16_t remaining = (in_ep->dieptsiz >> USB_D_XFERSIZE0_S) & 0x7FFFFU;
  uint16_t bytes_already_sent = xfer.size - remaining;
  uint16_t pkt_xfer_size = std::min(remaining, xfer.max_size);

  // Copy to the FIFO in 4-byte chunks
  uint16_t n = 0;
  const uint8_t *base = xfer.buffer + bytes_already_sent;
  for (/**/; n + 4 <= pkt_xfer_size; n += 4) {
    // Copy the data into a temporary uint32_t first before writing it to the
    // fifo.  This is needed since base[n] may not be 4-byte aligned,
    // and also to honor C/C++ strict aliasing rules.
    uint32_t u32 = base[n] | (base[n + 1] << 8) | (base[n + 2] << 16) |
                   (base[n + 3] << 24);
    ESP_EARLY_LOGI(LogTag, "USB tx: write 4");
    (*tx_fifo) = u32;
  }

  // Handle any remaining partial data
  if (n < pkt_xfer_size) {
    ESP_EARLY_LOGI(LogTag, "USB tx: write %d", pkt_xfer_size - n);
    uint32_t u32 = 0;
    u32 |= base[n];
    ++n;
    if (n < pkt_xfer_size) {
      u32 |= (base[n] << 8);
    }
    ++n;
    if (n < pkt_xfer_size) {
      u32 |= (base[n] << 16);
    }

    (*tx_fifo) = u32;
  }

  // Return true if we have written all data,
  // or false if more data is left to write.
  return (n == remaining);
}

void Esp32UsbDevice::handle_out_endpoint_intr() {
  for (uint8_t epnum = 0; epnum < USB_OUT_EP_NUM; ++epnum) {
    if (usb_->daint & (1 << (16 + epnum))) {
      handle_out_intr(epnum);
    }
  }
}

void Esp32UsbDevice::handle_in_endpoint_intr() {
  for (uint8_t epnum = 0; epnum < USB_IN_EP_NUM; ++epnum) {
    if (usb_->daint & (1 << epnum)) {
      handle_in_intr(epnum);
    }
  }
}

void Esp32UsbDevice::handle_out_intr(uint8_t epnum) {
  // Setup OUT transfer done.
  // This should presumably only happen for endpoint 0.
  if ((usb_->out_ep_reg[epnum].doepint & USB_SETUP0_M)) {
    ESP_EARLY_LOGI(LogTag, "USB: OUT SETUP received on EP%u", epnum);
    // Clear the interrupt bits
    usb_->out_ep_reg[epnum].doepint = USB_STUPPKTRCVD0_M | USB_SETUP0_M;
    send_event_from_isr<SetupPacket>(setup_packet_.setup);
  }

  // OUT transfer complete (one packet received)
  if (usb_->out_ep_reg[epnum].doepint & USB_XFERCOMPL0_M) {
    ESP_EARLY_LOGI(LogTag, "USB: OUT transfer complete on EP%u", epnum);
    // Clear the interrupt bit
    usb_->out_ep_reg[epnum].doepint = USB_XFERCOMPL0_M;

    auto &xfer = xfer_status_[epnum].out;
    // Transfer complete if short packet or total length is received
    if (xfer.recv_complete) {
      send_event_from_isr<OutXferCompleteEvent>(epnum, xfer.received_bytes);
    } else {
      // Schedule another packet to be received.
      set_bits(usb_->out_ep_reg[epnum].doeptsiz,
               USB_PKTCNT0_M |
                   ((xfer.max_size & USB_XFERSIZE0_V) << USB_XFERSIZE0_S));
      set_bits(usb_->out_ep_reg[epnum].doepctl, USB_EPENA0_M | USB_CNAK0_M);
    }
  }
}

void Esp32UsbDevice::handle_in_intr(uint8_t epnum) {
  ESP_EARLY_LOGI(LogTag, "USB IN interrupt: EP%u", epnum);
  // IN transfer complete
  if (usb_->in_ep_reg[epnum].diepint & USB_D_XFERCOMPL0_M) {
    ESP_EARLY_LOGI(LogTag, "USB: IN transfer complete on EP%u", epnum);
    usb_->in_ep_reg[epnum].diepint = USB_D_XFERCOMPL0_M;
    auto *xfer = &xfer_status_[epnum].in;
    send_event_from_isr<InXferCompleteEvent>(epnum, xfer->size);
  }

  // FIFO empty
  if (usb_->in_ep_reg[epnum].diepint & USB_D_TXFEMP0_M) {
    ESP_EARLY_LOGI(LogTag, "USB IN FIFO empty: EP%u", epnum);
    usb_->in_ep_reg[epnum].diepint = USB_D_TXFEMP0_M;
    const bool all_sent = transmit_packet(epnum, epnum);
    // Turn off the FIFO empty interrupt if all bytes have been written
    if (all_sent) {
      ESP_EARLY_LOGI(LogTag, "USB: clear fifo empty interrupt");
      clear_bits(usb_->dtknqr4_fifoemptymsk, 1 << epnum);
    }
  }

  // Transfer timeout
  if (usb_->in_ep_reg[epnum].diepint & USB_D_TIMEOUT0_M) {
    ESP_EARLY_LOGW(LogTag, "USB IN transfer timeout on EP%u", epnum);
    // Clear interrupt or endpoint will hang.
    usb_->in_ep_reg[epnum].diepint = USB_D_TIMEOUT0_M;
    send_event_from_isr<InXferFailedEvent>(epnum);
  }
}

void Esp32UsbDevice::set_address(uint8_t address) {
  set_bits(usb_->dcfg, (address & USB_DEVADDR_V) << USB_DEVADDR_S);
}

void Esp32UsbDevice::stall_in_endpoint(uint8_t endpoint_num) {
  usb_in_endpoint_t *in_ep = &(usb_->in_ep_reg[0]);

  if ((endpoint_num == 0) || !(in_ep[endpoint_num].diepctl & USB_D_EPENA1_M)) {
    // For endpoint 0 and other endpoints that are already disabled,
    // just set the NAK and STALL flags.
    set_bits(in_ep[endpoint_num].diepctl, USB_DI_SNAK1_M | USB_D_STALL1_M);
  } else {
    // Set USB_DI_SNAK1_M to NAK transfers.
    set_bits(in_ep[endpoint_num].diepctl, USB_DI_SNAK1_M);
    while ((in_ep[endpoint_num].diepint & USB_DI_SNAK1_M) == 0) {
      // Busy loop until we observe the USB_DI_SNAK1_M interrupt flag.
      // TODO: It would ideally be nicer to make this API asynchronous, and
      // finish the operation in the interrupt handler rather than busy
      // looping.
    }

    // Disable the endpoint and also set the STALL flag.
    // NAK is also still set.
    set_bits(in_ep[endpoint_num].diepctl,
             USB_DI_SNAK1_M | USB_D_STALL1_M | USB_D_EPDIS1_M);
    while ((in_ep[endpoint_num].diepint & USB_D_EPDISBLD0_M) == 0) {
      // Busy loop until we observe the USB_D_EPDISBLD0_M interrupt flag.
    }
    // Clear the USB_D_EPDISBLD0_M interrupt.
    in_ep[endpoint_num].diepint = USB_D_EPDISBLD0_M;
  }

  // Flush the transmit FIFO.
  uint8_t const fifo_num =
      ((in_ep[endpoint_num].diepctl >> USB_D_TXFNUM1_S) & USB_D_TXFNUM1_V);
  set_bits(usb_->grstctl, fifo_num << USB_TXFNUM_S);
  set_bits(usb_->grstctl, USB_TXFFLSH_M);
  while ((usb_->grstctl & USB_TXFFLSH_M) != 0) {
    // Busy loop until the FIFO has been cleared.
  }
}

void Esp32UsbDevice::stall_out_endpoint(uint8_t endpoint_num) {
  usb_out_endpoint_t *out_ep = &(usb_->out_ep_reg[0]);

  // Only disable currently enabled non-control endpoint
  if ((endpoint_num == 0) || !(out_ep[endpoint_num].doepctl & USB_EPENA0_M)) {
    // For endpoint 0 and other endpoints that are already disabled,
    // just set the STALL flag.
    set_bits(out_ep[endpoint_num].doepctl, USB_STALL0_M);
  } else {
    // Enable the Global NAK flag.
    set_bits(usb_->dctl, USB_SGOUTNAK_M);
    while ((usb_->gintsts & USB_GOUTNAKEFF_M) == 0) {
      // Busy loop until we have seen the USB_GOUTNAKEFF_M interrupt.
      // TODO: It would ideally be nicer to make this API asynchronous, and
      // finish the operation in the interrupt handler rather than busy
      // looping.
    }

    // Disable the endpoint, and set the STALL flag.
    set_bits(out_ep[endpoint_num].doepctl, USB_STALL0_M | USB_EPDIS0_M);
    while ((out_ep[endpoint_num].doepint & USB_EPDISBLD0_M) == 0) {
      // Busy loop until we have seen the endpoint disabled interrupt.
    }
    out_ep[endpoint_num].doepint = USB_EPDISBLD0_M;

    // Clear the Global NAK flag to allow other OUT endpoints to continue
    // functioning.
    set_bits(usb_->dctl, USB_CGOUTNAK_M);
  }
}

void Esp32UsbDevice::clear_in_stall(uint8_t endpoint_num) {
  usb_in_endpoint_t *in_ep = &(usb_->in_ep_reg[0]);
  clear_bits(in_ep[endpoint_num].diepctl, USB_D_STALL1_M);

  // Reset the DATA0/1 toggle bit to DATA0 after a stall on interrupt and bulk
  // transfer endpoints.
  const auto eptype = static_cast<EndpointType>(
      (in_ep[endpoint_num].diepctl & USB_D_EPTYPE1_M) >> USB_D_EPTYPE1_S);
  if (eptype == EndpointType::Interrupt || eptype == EndpointType::Bulk) {
    set_bits(in_ep[endpoint_num].diepctl, USB_DI_SETD0PID1_M);
  }
}

void Esp32UsbDevice::clear_out_stall(uint8_t endpoint_num) {
  usb_out_endpoint_t *out_ep = &(usb_->out_ep_reg[0]);
  clear_bits(out_ep[endpoint_num].doepctl, USB_STALL1_M);

  // Reset the DATA0/1 toggle bit to DATA0 after a stall on interrupt and bulk
  // transfer endpoints.
  const auto eptype = static_cast<EndpointType>(
      (out_ep[endpoint_num].doepctl & USB_EPTYPE1_M) >> USB_EPTYPE1_S);
  if (eptype == EndpointType::Interrupt || eptype == EndpointType::Bulk) {
    set_bits(out_ep[endpoint_num].doepctl, USB_DO_SETD0PID1_M);
  }
}

void Esp32UsbDevice::start_in_send(uint8_t endpoint_num,
                                   const uint8_t *buffer,
                                   uint16_t size) {
  // TODO: Keep track of endpoint busy status, and reject a new transfer if
  // one is already in progress.  Or perhaps queue it?
  auto &xfer = xfer_status_[endpoint_num].in;
  xfer.buffer = buffer;
  xfer.size = size;

  // For a 0-byte message we still need 1 packet.
  // Otherwise compute the number of packets needed.
  const uint16_t num_packets = size == 0 ? 1 : 1 + ((size - 1) / xfer.max_size);

  ESP_EARLY_LOGI(LogTag,
                 "USB IN transfer EP%u, %u bytes in %u packets",
                 endpoint_num,
                 size,
                 num_packets);

  // Schedule the transfer
  // Set dieptsiz so we will get a transfer complete interrupt when done.
  usb_->in_ep_reg[endpoint_num].dieptsiz =
      (num_packets << USB_D_PKTCNT0_S) | (size << USB_D_XFERSIZE0_S);
  // Enable the endpoint, and clear the NAK bit.
  set_bits(usb_->in_ep_reg[endpoint_num].diepctl,
           USB_D_EPENA1_M | USB_D_CNAK1_M);

  // If we have data to send, enable the fifo empty interrupt to
  // notify us when we can put data in the fifo.
  if (size != 0) {
    set_bits(usb_->dtknqr4_fifoemptymsk, 1 << endpoint_num);
  }
}

void Esp32UsbDevice::start_out_read(uint8_t endpoint_num,
                                    uint8_t *buffer,
                                    uint16_t buffer_size) {
  auto &xfer = xfer_status_[endpoint_num].out;
  xfer.buffer = buffer;
  xfer.buffer_size = buffer_size;
  xfer.received_bytes = 0;
  xfer.recv_complete = false;

  ESP_EARLY_LOGI(LogTag,
                 "Prepare for USB OUT receive EP%u, up to %u bytes",
                 endpoint_num,
                 buffer_size);

  // Schedule the OUT transfer.
  // Each complete packet will trigger an XFRC interrupt.
  set_bits(usb_->out_ep_reg[endpoint_num].doeptsiz,
           USB_PKTCNT0_M |
               ((xfer.max_size & USB_XFERSIZE0_V) << USB_XFERSIZE0_S));
  set_bits(usb_->out_ep_reg[endpoint_num].doepctl, USB_EPENA0_M | USB_CNAK0_M);
}

uint8_t Esp32UsbDevice::get_free_fifo() {
  if (allocated_fifos_ < kMaxInFIFOs) {
    return allocated_fifos_++;
  }
  return 0;
}

void Esp32UsbDevice::close_all_endpoints() {
  usb_out_endpoint_t *out_ep = &(usb_->out_ep_reg[0]);
  usb_in_endpoint_t *in_ep = &(usb_->in_ep_reg[0]);

  // Disable non-control interrupt
  usb_->daintmsk = USB_OUTEPMSK0_M | USB_INEPMSK0_M;

  for (uint8_t n = 1; n < xfer_status_.size(); n++) {
    // disable OUT endpoint
    out_ep[n].doepctl = 0;
    xfer_status_[n].out.max_size = 0;

    // disable IN endpoint
    in_ep[n].diepctl = 0;
    xfer_status_[n].in.max_size = 0;
  }

  allocated_fifos_ = 1;
}

} // namespace mantyl
