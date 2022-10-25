idf_component_register(
  SRCS
    "App.cpp"
    "Keyboard.cpp"
    "main.cpp"
  INCLUDE_DIRS "${CMAKE_CURRENT_SOURCE_DIR}"
  REQUIRES
    "sx1509" "ssd1306" "i2c_cpp" "mantyl_util" "mantyl_usb" "mantyl"
    "spi_flash" "log" "usb"
)
