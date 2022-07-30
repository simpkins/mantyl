// Copyright (c) 2022, Adam Simpkins

#include "config.h"
#include "sdkconfig.h"

#include "I2cMaster.h"
#include "SSD1306.h"
#include "SX1509.h"

#include <chrono>

#include <driver/i2c.h>
#include <esp_check.h>
#include <esp_chip_info.h>
#include <esp_flash.h>
#include <esp_log.h>
#include <esp_mac.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <stdio.h>
#include <tinyusb.h>

using namespace std::chrono_literals;

namespace mantyl {

static const char *LogTag = "mantyl.main";

void print_info() {
  /* Print chip information */
  esp_chip_info_t chip_info;
  uint32_t flash_size;
  esp_chip_info(&chip_info);
  ESP_LOGD(LogTag, "This is %s chip with %d CPU core(s), WiFi%s%s, ",
           CONFIG_IDF_TARGET, chip_info.cores,
           (chip_info.features & CHIP_FEATURE_BT) ? "/BT" : "",
           (chip_info.features & CHIP_FEATURE_BLE) ? "/BLE" : "");

  ESP_LOGD(LogTag, "silicon revision %d, ", chip_info.revision);
  if (esp_flash_get_size(NULL, &flash_size) != ESP_OK) {
    ESP_LOGD(LogTag, "Get flash size failed");
    return;
  }

  ESP_LOGD(LogTag, "%uMB %s flash\n", flash_size / (1024 * 1024),
           (chip_info.features & CHIP_FEATURE_EMB_FLASH) ? "embedded"
                                                         : "external");

  ESP_LOGD(LogTag, "Minimum free heap size: %d bytes\n",
           esp_get_minimum_free_heap_size());
}

class App {
public:
  esp_err_t init();
  esp_err_t test();
  esp_err_t init_usb();

private:
  I2cMaster i2c_{PinConfig::I2cSDA, PinConfig::I2cSCL};
  SSD1306 display_{i2c_, 0x3c, GPIO_NUM_38};
  SX1509 left_{i2c_, 0x3e};
  SX1509 right_{i2c_, 0x3f};
};

esp_err_t App::init() {
  return i2c_.init(I2cClockSpeed);
}

esp_err_t App::test() {
  ESP_LOGV(LogTag, "attempting left SX1509 init:");
  auto rc = left_.init();
  if (rc == ESP_OK) {
    ESP_LOGI(LogTag, "successfully initialized left key matrix");
  } else {
    ESP_LOGE(LogTag,
             "failed to initialize left key matrix: %d: %s",
             rc,
             esp_err_to_name(rc));
  }

  ESP_LOGV(LogTag, "attempting right SX1509 init:");
  rc = right_.init();
  if (rc == ESP_OK) {
    ESP_LOGI(LogTag, "successfully initialized right key matrix");
  } else {
    // Maybe the right key matrix is not connected.
    ESP_LOGE(LogTag,
             "failed to initialize right key matrix: %d: %s",
             rc,
             esp_err_to_name(rc));
  }

  ESP_LOGI(LogTag, "attempting display init:");
  rc = display_.init();
  if (rc == ESP_OK) {
    ESP_LOGI(LogTag, "successfully initialized display");
  } else {
    ESP_LOGE(LogTag,
             "failed to initialize display matrix: %d: %s",
             rc,
             esp_err_to_name(rc));
  }
  rc = display_.flush();
  if (rc == ESP_OK) {
    ESP_LOGI(LogTag, "successfully wrote to display");
  } else {
    ESP_LOGE(LogTag,
             "failed to perform display write: %d: %s",
             rc,
             esp_err_to_name(rc));
  }

  return ESP_OK;
}

static std::array<char, 14> serial_str = {};

static char hexlify(uint8_t n) {
  if (n < 10) {
    return '0' + n;
  }
  return 'a' + (n - 10);
}

esp_err_t init_serial_str() {
  std::array<uint8_t, 6> mac_bytes;
  auto rc = esp_read_mac(mac_bytes.data(), ESP_MAC_WIFI_STA);
  ESP_RETURN_ON_ERROR(rc, LogTag, "failed to get MAC");

  size_t out_idx = 0;
  for (size_t n = 0; n < mac_bytes.size(); ++n) {
    serial_str[out_idx] = hexlify((mac_bytes[n] >> 4) & 0xf);
    serial_str[out_idx + 1] = hexlify(mac_bytes[n] & 0xf);
    out_idx += 2;
    if (n == 2) {
      serial_str[out_idx] = '-';
      ++out_idx;
    }
  }
  serial_str[out_idx] = '\0';
  assert(out_idx + 1 == serial_str.size());

  return ESP_OK;
}

esp_err_t App::init_usb() {
  ESP_LOGI(LogTag, "USB initialization");

  tusb_desc_device_t usb_descriptor = {
      .bLength = sizeof(usb_descriptor),
      .bDescriptorType = TUSB_DESC_DEVICE,
      .bcdUSB = 0x0200, // USB version. 0x0200 means version 2.0
      .bDeviceClass = TUSB_CLASS_HID,
      .bDeviceSubClass = 1, // Boot
      .bDeviceProtocol = 1, // Keyboard
      .bMaxPacketSize0 = CFG_TUD_ENDPOINT0_SIZE,

      .idVendor = 0x303A, // Espressif's Vendor ID
      .idProduct = 0x9999,
      .bcdDevice = 0x0001, // Device FW version

      // String descriptor indices
      .iManufacturer = 0x01,
      .iProduct = 0x02,
      .iSerialNumber = 0x03,

      .bNumConfigurations = 0x01};

  tusb_desc_strarray_device_t descriptor_strings = {
      "\x09\x04",        // 0: is supported language is English (0x0409)
      "Adam Simpkins",   // 1: Manufacturer
      "Mantyl Keyboard", // 2: Product
      serial_str.data(),    // 3: Serial
  };

  tinyusb_config_t tusb_cfg = {
      .descriptor = &usb_descriptor,
      .string_descriptor = descriptor_strings,
      .external_phy = false,
      .configuration_descriptor = nullptr,
  };

  ESP_ERROR_CHECK(tinyusb_driver_install(&tusb_cfg));
  ESP_LOGI(LogTag, "USB initialization DONE");

  return ESP_OK;
}

void main() {
  printf("Hello world!\n");
  esp_log_level_set("mantyl.main", ESP_LOG_DEBUG);

  print_info();

  App app;
  ESP_ERROR_CHECK(app.init());
  app.test();
  // app.init_usb();

  for (int i = 10; i >= 0; i--) {
    printf("Restarting in %d seconds...\n", i);
    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }
  printf("Restarting now.\n");
  fflush(stdout);
  esp_restart();
}

} // namespace mantyl

extern "C" void app_main() {
  mantyl::main();
}
