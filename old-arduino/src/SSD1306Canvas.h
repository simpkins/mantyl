// Copyright (c) 2022, Adam Simpkins
#pragma once

#include "Adafruit_GFX.h"

#include <cstdint>
#include <memory>
#include <utility>

namespace mtl {

/**
 * An Adafruit_GFX implementation that writes to an in-memory buffer
 * compatible with the SD1306.
 *
 * This is very similar to GFXcanvas1, except the GFXcanvas1 stores data
 * by rows.  The SD1306 stores data column-wise: each byte is one chunk of
 * column data, 8 rows high.
 */
class SSD1306Canvas : public Adafruit_GFX {
public:
  SSD1306Canvas(uint8_t w, uint8_t h);
  ~SSD1306Canvas();

  bool get_pixel(uint8_t x, uint8_t y) const;

  uint8_t *get_buffer(void) const {
    return buffer_.get();
  }

  size_t buffer_size() const {
    return width() * ((height() + 7) / 8);
  }

  void drawPixel(int16_t x, int16_t y, uint16_t color) override;
  void fillScreen(uint16_t color) override;
  void drawFastVLine(int16_t x, int16_t y, int16_t h, uint16_t color) override;
  void drawFastHLine(int16_t x, int16_t y, int16_t w, uint16_t color) override;

private:
  void drawFastRawVLine(int16_t x, int16_t y, int16_t h, uint16_t color);
  void drawFastRawHLine(int16_t x, int16_t y, int16_t w, uint16_t color);

  std::pair<uint32_t, uint8_t> get_pixel_idx(uint16_t x, uint16_t y) const {
    // The caller is responsible for checking x and y bounds
    const auto idx = x + (y / 8) * width();
    uint8_t mask = (1 << (y & 7));
    return std::make_pair(idx, mask);
  }

  std::unique_ptr<uint8_t[]> buffer_;
};

} // namespace mtl
