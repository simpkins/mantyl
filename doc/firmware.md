The firmware requires the ESP-IDF to build.  During development I have been
using the latest github master branch, which is currently in beta for the v5.0
release.

# eFuse Settings

The `USB_PHY_SEL` eFuse needs to be burned in order to have the device behave
purely as a USB keyboard.  Without this setting when the chip powers on it
first enables the USB Serial/JTAG functionality, and will enumerate as a USB
serial device before it fully boots and changes configuration to a USB HID
device.  This behavior can be undesirable in many circumstances, so burning the
`USB_PHY_SEL` eFuse is recommended.  e.g., when plugged into the keyboard port
of USB KVM switches, some KVM switches will power cycle the port if anything
other than a keyboard is plugged in.
