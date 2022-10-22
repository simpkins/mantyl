idf_component_register(
  SRCS
    "keyboard/Keyboard.cpp"
    "keyboard/KeymapDB.cpp"
    "keyboard/Keypad.cpp"
    "ui/MainMenu.cpp"
    "ui/Menu.cpp"
    "ui/UI.cpp"
    "ui/UIMode.cpp"
    "usb/Esp32UsbDevice.cpp"
    "usb/UsbDevice.cpp"
    "usb/UsbDescriptorMap.cpp"
    "App.cpp"
    "main.cpp"
  INCLUDE_DIRS "${CMAKE_CURRENT_SOURCE_DIR}"
  REQUIRES
    "tinyusb" "sx1509" "ssd1306" "i2c_cpp" "mantyl_util"
    "spi_flash" "log" "usb"
    "esp_app_format"
)
