// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "mantyl_usb/UsbDevice.h"

#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <tuple>
#include <variant>
#include <vector>

namespace mantyl {

/**
 * A UsbDevice that is not actually connected to real hardware,
 * but can be manually controlled by unit test code.
 */
class MockUsbDevice : public UsbDevice {
public:
  struct SetAddress {
    uint8_t address{0};

    std::string describe() const;
  };
  struct InStall {
    uint8_t endpoint{0};

    std::string describe() const;
  };
  struct OutStall {
    uint8_t endpoint{0};

    std::string describe() const;
  };
  struct ClearInStall {
    uint8_t endpoint{0};

    std::string describe() const;
  };
  struct ClearOutStall {
    uint8_t endpoint{0};

    std::string describe() const;
  };
  struct InSend {
    uint8_t endpoint{0};
    const uint8_t *buffer{nullptr};
    uint16_t size{0};

    std::string describe() const;
  };
  struct OutRecv {
    uint8_t endpoint{0};
    uint8_t *buffer{nullptr};
    uint16_t size{0};

    std::string describe() const;
  };
  struct CloseAllEndpoints {
    std::string describe() const;
  };

  using Event = std::variant<SetAddress,
                             InStall,
                             OutStall,
                             ClearInStall,
                             ClearOutStall,
                             InSend,
                             OutRecv,
                             CloseAllEndpoints>;

  [[nodiscard]] bool init() override {
    // It potentially would be better to trigger these events from within the
    // loop() call after init() returns.
    on_bus_reset();
    on_enum_done(64);
    return true;
  }

  void loop() override {
    // TODO
  }

  const std::vector<Event> &get_events() const {
    return events_;
  }

  std::vector<Event> extract_events();

  using UsbDevice::on_setup_received;
  using UsbDevice::on_in_transfer_complete;
  using UsbDevice::on_in_transfer_failed;
  using UsbDevice::on_out_transfer_complete;

  /**
   * Check that we have received a specific set of events.
   *
   * The check_fn argument should be a function that accepts a series of event
   * objects.  This function will check that exactly those event types have
   * been received, then call check_fn with the event objects as arguments to
   * allow it to check the specific event contents.
   *
   * This function will clear the event list before returning, so that
   * subsequent calls to check_events() or check_no_events() do not see the
   * events that have already been checked.
   */
  template <typename Fn>
  bool check_events(const char* file, int line, Fn&& check_fn);

  /**
   * Check that no events have been received.
   */
  bool check_no_events(const char* file, int line);

  /**
   * Check an IN transfer.
   *
   * This ensures that IN data packets are seen, followed by a 0-length OUT
   * status packet.  The check function is then called with the data that was
   * received.
   *
   * This function handles making the on_in_transfer_complete() calls after
   * each transfer from the device.
   */
  bool check_in_transfer(
      const char *file,
      int line,
      uint8_t endpoint_num,
      const std::function<bool(const uint8_t* buf, uint16_t size)> &check_fn);

  /**
   * Drive the events to send data to the device in an OUT transfer.
   *
   * Returns false if the device does not make the expected calls to receive
   * the data.
   */
  bool drive_out_transfer(
      const char *file,
      int line,
      uint8_t endpoint_num,
      const uint8_t* buffer,
      uint16_t size);

  static void dump_hex(const uint8_t *buf, uint16_t size);

  static bool
  dump_unexpected_events(const char *file,
                         int line,
                         const std::vector<MockUsbDevice::Event> events,
                         const char *msg);

private:
  static constexpr uint8_t kMaxEndpoints = 8;

  void set_address(uint8_t address) override {
    events_.emplace_back(SetAddress{address});
  }
  void stall_in_endpoint(uint8_t endpoint_num) override {
    events_.emplace_back(InStall{endpoint_num});
  }
  void stall_out_endpoint(uint8_t endpoint_num) override {
    events_.emplace_back(OutStall{endpoint_num});
  }
  void clear_in_stall(uint8_t endpoint_num) override {
    events_.emplace_back(ClearInStall{endpoint_num});
  }
  void clear_out_stall(uint8_t endpoint_num) override {
    events_.emplace_back(ClearOutStall{endpoint_num});
  }
  void start_in_send(uint8_t endpoint_num,
                     const uint8_t *buffer,
                     uint16_t size) override {
    events_.emplace_back(InSend{endpoint_num, buffer, size});
  }
  void start_out_read(uint8_t endpoint_num,
                      uint8_t *buffer,
                      uint16_t buffer_size) override {
    events_.emplace_back(OutRecv{endpoint_num, buffer, buffer_size});
  }
  void close_all_endpoints() override {
    events_.emplace_back(CloseAllEndpoints{});
  }

  std::vector<Event> events_;
};

namespace detail {
template<typename T>
using remove_cv_ref = std::remove_cv_t<std::remove_reference_t<T>>;

template <typename T>
std::optional<std::tuple<const remove_cv_ref<T> &>>
parse_events(const std::vector<MockUsbDevice::Event> &events, size_t start) {
  if (events.size() != start + 1) {
    return std::nullopt;
  }

  const auto *event = std::get_if<remove_cv_ref<T>>(&events[start]);
  if (!event) {
    return std::nullopt;
  }
  return std::tuple<T>(*event);
}

template <typename T, typename U, typename... Args>
std::optional<std::tuple<const remove_cv_ref<T> &, const remove_cv_ref<U> &, const Args &...>>
parse_events(const std::vector<MockUsbDevice::Event> &events, size_t start) {
  if (events.size() <= start) {
    return std::nullopt;
  }

  const auto *event = std::get_if<remove_cv_ref<T>>(&events[start]);
  if (!event) {
    return std::nullopt;
  }
  const auto rest = parse_events<U, Args...>(events, start + 1);
  if (!rest.has_value()) {
    return std::nullopt;
  }
  return std::tuple_cat(std::tuple<T>(*event), *rest);
}

template <typename T>
class CheckFunctionTraits
    : public CheckFunctionTraits<decltype(&T::operator())> {};

template<typename ReturnType, typename... Args>
class CheckFunctionTraits<ReturnType(Args...)> {
public:
 static std::optional<std::tuple<const MockUsbDevice::SetAddress&, const MockUsbDevice::InSend&>>
 parse(const std::vector<MockUsbDevice::Event> &events) {
   return parse_events<Args...>(events, 0);
 }
};

template<typename ClassType, typename ReturnType, typename... Args>
class CheckFunctionTraits<ReturnType(ClassType::*)(Args...) const> {
public:
  static std::optional<std::tuple<const Args &...>>
  parse(const std::vector<MockUsbDevice::Event> &events) {
    return parse_events<Args...>(events, 0);
  }
};

} // namespace detail

template <typename Fn>
bool MockUsbDevice::check_events(const char *file, int line, Fn &&check_fn) {
  const auto events = extract_events();
  const auto check_args = detail::CheckFunctionTraits<Fn>::parse(events);
  if (!check_args.has_value()) {
    return dump_unexpected_events(file, line, events, "unexpected events");
  }

  if (!std::apply(check_fn, check_args.value())) {
    return dump_unexpected_events(
        file, line, events, "unexpected event details");
  }

  return true;
}

} // namespace mantyl
