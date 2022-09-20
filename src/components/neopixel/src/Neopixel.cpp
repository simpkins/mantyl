// Copyright (c) 2022, Adam Simpkins
#include "Neopixel.h"

#include <cmath>
#include <esp_check.h>
#include <esp_log.h>

namespace {
const char *LogTag = "mantyl.neopixel";
} // namespace

namespace mantyl {

NeopixelChainImpl::NeopixelChainImpl() {}

NeopixelChainImpl::~NeopixelChainImpl() {
  if (bytes_encoder_) {
    rmt_del_encoder(bytes_encoder_);
  }
  if (copy_encoder_) {
    rmt_del_encoder(copy_encoder_);
  }
}

esp_err_t NeopixelChainImpl::init(gpio_num_t gpio) {
  ESP_LOGD(LogTag, "Initialize Neopixel LED chain");
  rmt_tx_channel_config_t channel_config = {
      .gpio_num = gpio,
      .clk_src = RMT_CLK_SRC_DEFAULT,
      .resolution_hz = kResolutionHZ,
      // increasing the block size can reduce LED flickering
      .mem_block_symbols = 64,
      // the number of transactions that can be pending in the background
      .trans_queue_depth = 4,
      .flags = {},
  };
  ESP_RETURN_ON_ERROR(rmt_new_tx_channel(&channel_config, &channel_),
                      LogTag,
                      "failed to create LED RMT TX channel");
  ESP_RETURN_ON_ERROR(
      init_encoder(), LogTag, "failed to initialized LED strip encoder");
  ESP_RETURN_ON_ERROR(
      rmt_enable(channel_), LogTag, "failed to enable LED TX channel");

  return ESP_OK;
}

esp_err_t NeopixelChainImpl::transmit(const void *payload, size_t size) {
  return rmt_transmit(channel_, &encoder_, payload, size, &tx_config_);
}

size_t NeopixelChainImpl::encode_callback(rmt_encoder_t *encoder,
                                          rmt_channel_handle_t channel,
                                          const void *primary_data,
                                          size_t data_size,
                                          rmt_encode_state_t *ret_state) {
  NeopixelChainImpl *chain =
      __containerof(encoder, NeopixelChainImpl, encoder_);

  size_t encoded_symbols = 0;
  if (chain->state_ == TxState::RGB) {
    rmt_encode_state_t byte_send_state;
    const rmt_encoder_handle_t bytes_encoder = chain->bytes_encoder_;
    encoded_symbols += bytes_encoder->encode(
        bytes_encoder, channel, primary_data, data_size, &byte_send_state);
    if (byte_send_state & RMT_ENCODING_COMPLETE) {
      // Switch to sending the reset after we finish sending the RGB data.
      chain->state_ = TxState::Reset;
    }
    if (byte_send_state & RMT_ENCODING_MEM_FULL) {
      *ret_state = RMT_ENCODING_MEM_FULL;
      return encoded_symbols;
    }
    // Fall through to send the reset sequence
  }

  // Sending reset sequence
  const rmt_encoder_handle_t copy_encoder = chain->copy_encoder_;
  encoded_symbols += copy_encoder->encode(copy_encoder,
                                          channel,
                                          &chain->reset_code_,
                                          sizeof(chain->reset_code_),
                                          ret_state);
  if (*ret_state & RMT_ENCODING_COMPLETE) {
    // Reset back to ready to send RGB data
    chain->state_ = TxState::RGB;
  }
  return encoded_symbols;
}

esp_err_t NeopixelChainImpl::del_callback(rmt_encoder_t *encoder) {
  // We do all of the cleanup in the destructor.
  // This function shouldn't ever get called anyway.
  return ESP_OK;
}

esp_err_t NeopixelChainImpl::reset_callback(rmt_encoder_t *encoder) {
  NeopixelChainImpl *chain =
      __containerof(encoder, NeopixelChainImpl, encoder_);
  rmt_encoder_reset(chain->bytes_encoder_);
  rmt_encoder_reset(chain->copy_encoder_);
  chain->state_ = TxState::RGB;
  return ESP_OK;
}

esp_err_t NeopixelChainImpl::init_encoder() {
  encoder_.encode = encode_callback;
  encoder_.del = del_callback;
  encoder_.reset = reset_callback;

  rmt_bytes_encoder_config_t bytes_encoder_config = {};
  // 0 bit:
  // - High for 0.4us, low for 0.8us
  //   The WS2812 datasheet says .35us high / .7us low, but
  //   https://learn.adafruit.com/adafruit-neopixel-uberguide/advanced-coding
  //   recommends .4us / .8us
  bytes_encoder_config.bit0.level0 = 1;
  bytes_encoder_config.bit0.duration0 = us_to_rmt_ticks(0.4);
  bytes_encoder_config.bit0.level1 = 0;
  bytes_encoder_config.bit0.duration1 = us_to_rmt_ticks(0.8);
  // 1 bit:
  // - High for 0.85us, low for 0.45us
  //   The WS2812 datasheet says .8us high / .6us low, but
  //   https://learn.adafruit.com/adafruit-neopixel-uberguide/advanced-coding
  //   recommends .85us / .45us
  bytes_encoder_config.bit1.level0 = 1;
  bytes_encoder_config.bit1.duration0 = us_to_rmt_ticks(0.85);
  bytes_encoder_config.bit1.level1 = 0;
  bytes_encoder_config.bit1.duration1 = us_to_rmt_ticks(0.45);
  bytes_encoder_config.flags.msb_first = 1;
  ESP_RETURN_ON_ERROR(
      rmt_new_bytes_encoder(&bytes_encoder_config, &bytes_encoder_),
      LogTag,
      "create bytes encoder failed");
  rmt_copy_encoder_config_t copy_encoder_config = {};
  ESP_RETURN_ON_ERROR(
      rmt_new_copy_encoder(&copy_encoder_config, &copy_encoder_),
      LogTag,
      "create copy encoder failed");

  // The reset duration is 50us.  Send two 25us 0 bits.
  const uint32_t reset_ticks = us_to_rmt_ticks(25);
  reset_code_.level0 = 0;
  reset_code_.duration0 = reset_ticks;
  reset_code_.level1 = 0;
  reset_code_.duration1 = reset_ticks;
  return ESP_OK;
}

std::tuple<float, float, float>
NeopixelChainImpl::hsv2rgb(float h, float s, float v) {
  // clamp hue to [0.0, 360.0)
  h = fmodf(h, 360.0);

  if (s < 0) {
    return {v, v, v};
  }
  if (v < 0) {
    return {0.0, 0.0, 0.0};
  }
  // clamp s and v to 1.0
  s = std::min(1.0f, s);
  v = std::min(1.0f, v);

  const auto hh = h / 60.0;
  const auto i = static_cast<int>(hh);
  const auto ff = hh - i;

  const auto p = v * (1.0 - s);
  const auto q = v * (1.0 - (s * ff));
  const auto t = v * (1.0 - (s * (1.0 - ff)));

  switch (i) {
  case 0:
    return {v, t, p};
  case 1:
    return {q, v, p};
  case 2:
    return {p, v, t};
  case 3:
    return {p, q, v};
  case 4:
    return {t, p, v};
  default:
    return {v, p, q};
  }
}

} // namespace mantyl
