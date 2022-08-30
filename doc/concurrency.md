Some notes on tasks and concurrency in the firmware:

# Tasks

- main task
  All I2C communication is performed from this task.  This handles reading key
  information from the SX1509 chips, and updating the SSD1306 display.

  We also call tud_hid_keyboard_report() from this task when a key is pressed.
  We perform all USB HID interrupt transfers from this task.

- USB task
  This task runs the TinyUSB `tud_task()`

  We perform all USB control transfers from this task.
  (Note that USB HID interrupt transfers are performed from the main task.)

# I2C Access

All I2C access is performed from the main task.

# USB Access

All HID transfers are performed from the main task.
All control transfers are performed from the USB task.

CDC transfers performed by the esp-idf `tusb_console` code may be performed
from any task, but are always done with a lock held.  Separate locks are used
for the in and out endpoints for receive and transmit operations.
