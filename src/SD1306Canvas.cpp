// Copyright (c) 2022, Adam Simpkins
#include "SD1306Canvas.h"

namespace mtl {

SD1306Canvas::SD1306Canvas(uint8_t w, uint8_t h)
    : Adafruit_GFX(w, h), buffer_{new uint8_t[buffer_size()]} {}

SD1306Canvas::~SD1306Canvas() = default;

bool SD1306Canvas::get_pixel(uint8_t x, uint8_t y) const {
  if (x >= width() || y >= height()) {
    return false;
  }
  const auto [idx, mask] = get_pixel_idx(x, y);
  return (buffer_[idx] & mask);
}

void SD1306Canvas::drawPixel(int16_t x, int16_t y, uint16_t color) {
  if (x >= width() || y >= height() || x < 0 || y < 0) {
    return;
  }
  const auto [idx, mask] = get_pixel_idx(x, y);
  if (color) {
    buffer_[idx] |= mask;
  } else {
    buffer_[idx] &= ~mask;
  }
}

void SD1306Canvas::fillScreen(uint16_t color) {
  memset(buffer_.get(), color ? 0xff : 0, buffer_size());
}

void SD1306Canvas::drawFastVLine(int16_t x, int16_t y, int16_t h, uint16_t color) {
  // If h is negative, draw upwards from the (x, y) coordinates
  if (h < 0) {
    y -= h;
    h = -h;
  }
  // Clip top
  if (y < 0) {
    h += y;
    y = 0;
  }
  if (h <= 0 || y >= height()) {
    // Off-screen vertically
    return;
  }
  if (x < 0 || x >= width()) {
    // Off-screen horizontally
    return;
  }
  // Clip bottom
  if (y + h > height()) {
      h = height() - y;
  }

  drawFastRawVLine(x, y, h, color);
}

void SD1306Canvas::drawFastHLine(int16_t x, int16_t y, int16_t w, uint16_t color) {
  // If h is negative, draw backwards from the (x, y) coordinates
  if (w < 0) {
    x -= w;
    w = -w;
  }
  // Clip left
  if (x < 0) {
    w += x;
    x = 0;
  }
  if (w <= 0 || x >= width()) {
    // Off-screen horizontally
    return;
  }
  if (y < 0 || y >= width()) {
    // Off-screen vertically
    return;
  }
  // Clip bottom
  if (x + w > width()) {
      w = width() - x;
  }

  drawFastRawHLine(x, y, w, color);
}

void SD1306Canvas::drawFastRawVLine(int16_t x, int16_t y, int16_t h, uint16_t color) {
  uint16_t idx = x + (y / 8) * width();
  uint8_t bit_pos = (y & 7);

  while (true) {
    uint8_t byte_mask = 0xff >> (7 - bit_pos);
    if (h <= bit_pos) {
      const uint8_t sub = bit_pos - h + 1;
      byte_mask &= 0xff & (0xff << sub);
    }

    if (color) {
      buffer_[idx] |= byte_mask;
    } else {
      buffer_[idx] &= ~byte_mask;
    }

    if (h <= bit_pos + 1) {
      return;
    }
    h -= bit_pos + 1;

    idx += width();
    bit_pos = 7;
  }
}

void SD1306Canvas::drawFastRawHLine(int16_t x, int16_t y, int16_t w, uint16_t color) {
  const auto [idx, mask] = get_pixel_idx(x, y);
  if (color) {
    for (size_t n = 0; n < w; ++n) {
      buffer_[idx + n] |= mask;
    }
  } else {
    for (size_t n = 0; n < w; ++n) {
      buffer_[idx + n] &= ~mask;
    }
  }
}

} // namespace mtl
