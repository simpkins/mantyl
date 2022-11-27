// Copyright (c) 2022, Adam Simpkins
#include "MockUsbDevice.h"

#include <esp_err.h>
#include <esp_log.h>

#include <array>
#include <cstdio>

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
