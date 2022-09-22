// Copyright (c) 2022, Adam Simpkins
#pragma once

#include <array>
#include <tuple>

#include <esp_err.h>
#include <hal/gpio_hal.h>
#include <driver/rmt_tx.h>

namespace mantyl {

class NeopixelChainImpl {
public:
  NeopixelChainImpl();
  ~NeopixelChainImpl();

  esp_err_t init(gpio_num_t gpio);

  esp_err_t transmit(const void* payload, size_t size);

  /**
   * Convert an HSV value to RGB.
   *
   * h should be in the range [0, 360)
   * s and v should be in the range [0.0, 1.0)
   *
   * Returns R, G, B values in the range [0.0, 1.0)
   */
  static std::tuple<float, float, float>
  hsv2rgb(float h, float s, float v);

private:
  enum TxState{
      RGB,
      Reset,
  };

  NeopixelChainImpl(NeopixelChainImpl const &) = delete;
  NeopixelChainImpl &operator=(NeopixelChainImpl const &) = delete;

  esp_err_t init_encoder();
  static size_t encode_callback(rmt_encoder_t *encoder,
                                     rmt_channel_handle_t channel,
                                     const void *primary_data,
                                     size_t data_size,
                                     rmt_encode_state_t *ret_state);
  static esp_err_t del_callback(rmt_encoder_t *encoder);
  static esp_err_t reset_callback(rmt_encoder_t *encoder);

  // 10MHz resolution, 1 tick = 0.1us
  static constexpr uint32_t kResolutionHZ = 10000000;

  constexpr unsigned int us_to_rmt_ticks(float us) {
    return us * kResolutionHZ / 1000000;
  }

  rmt_channel_handle_t channel_{nullptr};
  rmt_transmit_config_t tx_config_{};

  rmt_encoder_t encoder_{};
  rmt_encoder_t *bytes_encoder_{nullptr};
  rmt_encoder_t *copy_encoder_{nullptr};
  TxState state_{TxState::RGB};
  rmt_symbol_word_t reset_code_{};
};

template<size_t N>
class NeopixelChain {
public:
  static constexpr size_t kNumPixels = N;

  NeopixelChain() = default;

  esp_err_t init(gpio_num_t gpio) {
    return impl_.init(gpio);
  }

  esp_err_t transmit() {
    return impl_.transmit(pixels_.data(), pixels_.size());
  }

  void set_rgb(size_t idx, uint8_t r, uint8_t g, uint8_t b) {
    const auto offset = idx * 3;
    pixels_[offset] = g;
    pixels_[offset + 1] = r;
    pixels_[offset + 2] = b;
  }
  void set_hsv(size_t idx, float h, float s, float v) {
    const auto rgb = NeopixelChainImpl::hsv2rgb(h, s, v);
    set_rgb(idx,
            std::get<0>(rgb) * 255,
            std::get<1>(rgb) * 255,
            std::get<2>(rgb) * 255);
  }

private:
  NeopixelChainImpl impl_;
  std::array<uint8_t, 3 * kNumPixels> pixels_;
};

template<size_t N>
class RGBWChain {
public:
  static constexpr size_t kNumPixels = N;

  RGBWChain() = default;

  esp_err_t init(gpio_num_t gpio) {
    return impl_.init(gpio);
  }

  esp_err_t transmit() {
    return impl_.transmit(pixels_.data(), pixels_.size());
  }

  void set_rgbw(size_t idx, uint8_t r, uint8_t g, uint8_t b, uint8_t w) {
    const auto offset = idx * 3;
    pixels_[offset] = g;
    pixels_[offset + 1] = r;
    pixels_[offset + 2] = b;
    pixels_[offset + 3] = w;
  }
  void set_hsvw(size_t idx, float h, float s, float v, uint8_t w) {
    const auto rgb = NeopixelChainImpl::hsv2rgb(h, s, v);
    set_rgbw(idx,
            std::get<0>(rgb) * 255,
            std::get<1>(rgb) * 255,
            std::get<2>(rgb) * 255,
            w);
  }

private:
  NeopixelChainImpl impl_;
  std::array<uint8_t, 4 * kNumPixels> pixels_;
};

} // namespace mantyl
