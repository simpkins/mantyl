// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <cstdint>

namespace mantyl {

enum class SetupRecipient : uint8_t {
    Device = 0,
    Interface = 1,
    Endpoint = 2,
    Other = 3,
};

enum class SetupReqType : uint8_t {
  Standard = 0x00,
  Class = 0x20,
  Vendor = 0x40,
  Reserved = 0x60,
};

enum class StdRequestType : uint8_t {
    GetStatus = 0,
    ClearFeature = 1,
    SetFeature = 3,
    SetAddress = 5,
    GetDescriptor = 6,
    GetConfiguration = 8,
    SetConfiguration = 9,
    GetInterface = 10,
    SetInterface = 11,
};

enum class DescriptorType : uint8_t {
    Device = 1,
    Config = 2,
    String = 3,
    Interface = 4,
    Endpoint = 5,
    DeviceQualifier = 6,
    OtherSpeedConfig = 7,
    InterfacePower = 8,

    Hid = 0x21,
    HidReport = 0x22,
    HidPhyDescriptor = 0x23,
};

enum class FeatureSelector {
  EndpointHalt = 0, // Only valid for SetupRecipient::Endpoint
  RemoteWakeup = 1, // Only valid for SetupRecipient::Device
  TestMode = 2,     // Only valid for SetupRecipient::Device
};

/**
 * Endpoint type bits,
 * as used in the bmAttributes field of the endpoint descriptor.
 */
enum class EndpointType : uint8_t {
  Control = 0,
  Isochronous = 1,
  Bulk = 2,
  Interrupt = 3,
};

enum class Direction : uint8_t {
  Out = 0,
  In = 0x80,
};

class EndpointNumber {
public:
  explicit constexpr EndpointNumber(uint8_t number) : number_(number) {}

  constexpr uint8_t value() const {
    return number_;
  }

private:
  uint8_t number_;
};

class EndpointAddress {
public:
  explicit constexpr EndpointAddress(uint8_t address) : address_(address) {}
  explicit constexpr EndpointAddress(EndpointNumber num, Direction dir)
      : address_(num.value() | static_cast<uint8_t>(dir)) {}

  constexpr Direction direction() const {
    return static_cast<Direction>(address_ & 0x80);
  }
  constexpr EndpointNumber number() const {
    return EndpointNumber(address_ & 0x7f);
  }

  constexpr uint8_t value() const {
    return address_;
  }

private:
  const uint8_t address_;
};

enum class InterfaceClass : uint8_t {
  Hid = 3,
};

struct SetupPacket{
  SetupReqType get_request_type() const {
    static constexpr uint8_t kSetupReqTypeMask = 0x60;
    return static_cast<SetupReqType>(request_type & kSetupReqTypeMask);
  }
  Direction get_direction() const {
    return (request_type & 0x80) ? Direction::In : Direction::Out;
  }
  SetupRecipient get_recipient() const {
    return static_cast<SetupRecipient>(request_type & 0x1f);
  }

  // Should only be called if get_request_type() return s
  // SetupReqType::Standard
  StdRequestType get_std_request() const {
    return static_cast<StdRequestType>(request);
  }

  uint8_t request_type;
  uint8_t request;
  uint16_t value;
  uint16_t index;
  uint16_t length;
};

} // namespace mantyl
