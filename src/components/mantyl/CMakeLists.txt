set(component_srcs
    "keyboard/KeymapDB.cpp"
    "keyboard/Keypad.cpp"
    "ui/MainMenu.cpp"
    "ui/Menu.cpp"
    "ui/UI.cpp"
    "ui/UIMode.cpp"
)

idf_component_register(
    SRCS "${component_srcs}"
    INCLUDE_DIRS "."
    PRIV_INCLUDE_DIRS ""
    PRIV_REQUIRES ""
    REQUIRES
        "mantyl_usb" "ssd1306" "sx1509"
        "esp_app_format"
)
