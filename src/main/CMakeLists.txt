idf_component_register(
  SRCS
    "keyboard/Keyboard.cpp"
    "keyboard/KeymapDB.cpp"
    "keyboard/Keypad.cpp"
    "ui/UI.cpp"
    "App.cpp"
    "main.cpp"
    "UsbDevice.cpp"
  INCLUDE_DIRS "${CMAKE_CURRENT_SOURCE_DIR}"
  REQUIRES
    "tinyusb" "sx1509" "ssd1306" "i2c_cpp" "mantyl_util"
    "spi_flash" "log" "usb"
)
