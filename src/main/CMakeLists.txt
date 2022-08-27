idf_component_register(
  SRCS "App.cpp" "Keyboard.cpp" "Keypad.cpp" "main.cpp" "UI.cpp" "UsbDevice.cpp"
  INCLUDE_DIRS ""
  REQUIRES
    "tinyusb" "sx1509" "ssd1306" "i2c_cpp" "mantyl_util"
    "spi_flash" "log" "usb"
)
