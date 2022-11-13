// Copyright (c) 2022, Adam Simpkins
#include "mantyl_readline.h"

#include <esp_rom_uart.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

namespace mantyl {

void putc_raw(char c) {
  esp_rom_uart_tx_one_char(static_cast<uint8_t>(c));
}

void putc(char c) {
  if (c == '\n') {
    putc_raw('\r');
    putc_raw('\n');
  } else {
    putc_raw(c);
  }
}

void puts(std::string_view str) {
  for (auto c : str) {
    putc(c);
  }
}

std::string readline(std::string_view prompt) {
  puts(prompt);

  std::string value;
  while (true) {
    uint8_t c;
    auto rc = esp_rom_uart_rx_one_char(&c);
    if (rc != 0) {
      vTaskDelay(pdMS_TO_TICKS(10));
      continue;
    }

    if (c == '\r' || c == '\n') {
      // Receiving a newline is uncommon; terminals will typically send \r
      // instead when enter is pressed.
      //
      // Echo an extra space before the CRLF.  For some reason without this
      // the CRLF only printed by my terminal as a CR.
      putc_raw(' ');
      putc_raw('\r');
      putc_raw('\n');
      return value;
    } else if (c == '\b') {
      // Backspace
      if (!value.empty()) {
        putc_raw('\b');
        putc_raw(' ');
        putc_raw('\b');
        value.erase(value.end() - 1);
      }
    } else if (c == 0x15) {
      // Ctrl-U
      if (value.size() > 0) {
        for (size_t n = 0; n < value.size(); ++n) {
          putc_raw('\b');
        }
        for (size_t n = 0; n < value.size(); ++n) {
          putc_raw(' ');
        }
        for (size_t n = 0; n < value.size(); ++n) {
          putc_raw('\b');
        }
        value.clear();
      }
    } else if (c == 0x1b) {
      // TODO: Handle various escape sequences
      // Home: 27 91 49 126
      // Delete: 27 91 51 126
      // End: 27 91 52 126
      // Left: 27 91 68
      // Right: 27 91 67
      // Up: 27 91 65
      // Down: 27 91 66
    } else {
      putc_raw(c);
      value.push_back(static_cast<char>(c));
    }
  }
}

} // namespace mantyl
