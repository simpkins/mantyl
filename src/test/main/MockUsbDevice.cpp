// Copyright (c) 2022, Adam Simpkins
#include "MockUsbDevice.h"

#include <esp_err.h>
#include <esp_log.h>

#include <array>
#include <cstdio>
#include <cstring>

namespace {
const char *LogTag = "mantyl.test.mock_usb";
}

namespace mantyl {

std::string MockUsbDevice::SetAddress::describe() const {
  std::array<char, 128> buf;
  snprintf(buf.data(), buf.size(), "SetAddress(%d)", address);
  return std::string(buf.data());
}

std::string MockUsbDevice::InStall::describe() const {
  std::array<char, 128> buf;
  snprintf(buf.data(), buf.size(), "InStall(%d)", endpoint);
  return std::string(buf.data());
}

std::string MockUsbDevice::OutStall::describe() const {
  std::array<char, 128> buf;
  snprintf(buf.data(), buf.size(), "OutStall(%d)", endpoint);
  return std::string(buf.data());
}

std::string MockUsbDevice::ClearInStall::describe() const {
  std::array<char, 128> buf;
  snprintf(buf.data(), buf.size(), "ClearInStall(%d)", endpoint);
  return std::string(buf.data());
}

std::string MockUsbDevice::ClearOutStall::describe() const {
  std::array<char, 128> buf;
  snprintf(buf.data(), buf.size(), "ClearOutStall(%d)", endpoint);
  return std::string(buf.data());
}

std::string MockUsbDevice::InSend::describe() const {
  std::array<char, 128> buf;
  snprintf(
      buf.data(), buf.size(), "InSend(%d, %p, %u)", endpoint, buffer, size);
  return std::string(buf.data());
}

std::string MockUsbDevice::OutRecv::describe() const {
  std::array<char, 128> buf;
  snprintf(
      buf.data(), buf.size(), "OutRecv(%d, %p, %u)", endpoint, buffer, size);
  return std::string(buf.data());
}

std::string MockUsbDevice::CloseAllEndpoints::describe() const {
  return "CloseAllEndpoints()";
}

std::vector<MockUsbDevice::Event> MockUsbDevice::extract_events() {
  std::vector<Event> events;
  events.swap(events_);
  return events;
}

bool MockUsbDevice::check_no_events(const char* file, int line) {
  const auto events = extract_events();
  if (events.size() != 0) {
    return dump_unexpected_events(file, line, events, "too many events");
  }
  return true;
}

bool MockUsbDevice::check_in_transfer(
    const char *file,
    int line,
    uint8_t endpoint_num,
    const std::function<bool(const uint8_t *buf, uint16_t size)> &check_fn) {
  std::vector<uint8_t> received_data;

  while(true) {
    const auto events = extract_events();
    if (events.size() != 1) {
      return dump_unexpected_events(
          file,
          line,
          events,
          "unexpected number of events received during IN transfer");
    }

    const auto* in = std::get_if<InSend>(&events[0]);
    if (in) {
      if (in->endpoint != endpoint_num) {
        return dump_unexpected_events(
            file,
            line,
            events,
            "received IN packet for unexpected endpoint during IN transfer");
      }

      // TODO: It would perhaps be good to check that the received data is
      // either a multiple of the max packet size, or is the final chunk of
      // data before the zero-length OUT packet.

      // Append the data to received_data
      auto current_end = received_data.size();
      received_data.resize(current_end + in->size);
      memcpy(received_data.data() + current_end, in->buffer, in->size);

      // Call on_in_transfer_complete() to inform the device that this data
      // has been sent successfully.
      on_in_transfer_complete(in->endpoint, in->size);
      continue;
    }

    const auto* out = std::get_if<OutRecv>(&events[0]);
    if (out) {
      if (out->endpoint != endpoint_num) {
        return dump_unexpected_events(
            file,
            line,
            events,
            "received OUT packet for unexpected endpoint during IN transfer");
      }
      if (out->size != 0) {
        return dump_unexpected_events(
            file, line, events, "non-zero OUT packet during IN transfer");
      }
      on_out_transfer_complete(out->endpoint, out->size);
      break;
    }

    return dump_unexpected_events(
        file, line, events, "unexpected event received during IN transfer");
  }

  if (!check_fn(received_data.data(), received_data.size())) {
    ESP_LOGE(LogTag, "%s:%d: unexpected IN data contents", file, line);
    dump_hex(received_data.data(), received_data.size());
    return false;
  }
  return true;
}

bool MockUsbDevice::drive_out_transfer(const char *file,
                        int line,
                        uint8_t endpoint_num,
                        const uint8_t *buffer,
                        uint16_t size) {
  // Note: the UsbDevice currently requires the caller to give us a buffer big
  // enough for the full transfer.  Maybe in the future it would be nice to
  // allow it to make multiple sequential calls to fill in separate buffers in
  // somewhat of a streaming fashion.

  return check_events(file, line, [&](const OutRecv &event) {
    if (event.endpoint != endpoint_num) {
      return false;
    }

    auto data_size = std::min(size, event.size);
    memcpy(event.buffer, buffer, data_size);
    on_out_transfer_complete(endpoint_num, data_size);
    return true;
  });
}

void MockUsbDevice::dump_hex(const uint8_t* buf, uint16_t size) {
  auto p = buf;
  size_t bytes_left = size;
  while (bytes_left > 8) {
    printf("- %02x %02x %02x %02x %02x %02x %02x %02x\n",
           p[0],
           p[1],
           p[2],
           p[3],
           p[4],
           p[5],
           p[6],
           p[7]);
    p += 8;
    bytes_left -= 8;
  }
  if (bytes_left > 0) {
    printf("-");
    while (bytes_left > 0) {
      printf(" %02x", p[0]);
      ++p;
      --bytes_left;
    }
    printf("\n");
  }
}

bool MockUsbDevice::dump_unexpected_events(
    const char *file,
    int line,
    const std::vector<MockUsbDevice::Event> events,
    const char *msg) {
  ESP_LOGE(LogTag, "%s:%d: unexpected events: %s:", file, line, msg);
  for (const auto& event: events) {
    std::visit([](auto &&e) { ESP_LOGE(LogTag, "- %s", e.describe().c_str()); },
               event);
  }

  return false;
}

} // namespace mantyl
