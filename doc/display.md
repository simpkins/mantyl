Notes on the UI for the OLED display.

# Menu Tree

- Select Keymap
  - List of keymaps
- Edit Keymap
- Debug
  - Key presses
  - USB Events (e.g., suspend & resume)
- Settings
  - Set Owner contact info
  - Screensaver
    - Off
    - Clock
  - WiFi
    - SSID
    - Password
- Owner
  - Owner contact info
- System Info
  - Firmware Version
  - Build Date


# Edit Keymap Operation

- Step 1: Press a physical key
- Step 2: Define a key for it
  - Can either press another physical key, and we will use it's value from the
    default keymap.
  - Or select from a menu on the OLED.
- Step 3: Confirm
  - Either hit enter, or right on the directional switch.

The confirm option is to make menu selection easier.  Can press as physical key
to jump to that key in the menu, then navigate from there.


# Clock

Get time from NTP.  It would be nice if we could get this from the computer
over USB, but there is no standard interface for this, so we would need custom
drivers.  Using NTP over WiFi is more straightforward to configure.

The SSD1306 supports automatic scrolling, so we could use that in clock
screensaver mode.
