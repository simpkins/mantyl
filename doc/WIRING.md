# Key Matrix

For the main underlay, simply wire the rows and columns straight across.
This uses 6 rows (R0-R5), and 7 columns (C0-C6).

Numbering the rows from top to bottom, and the columns from outward to inward
(so both sides are symmetrical), the only keys that are unused on the main
underlay are C6R0, C6R1, C5R5, and C6R5

Right thumb (viewed from the bottom):

       C6R0  C7R0
 C7R2
       C6R1  C7R1
 C5R5
       C6R5  C7R5

Left thumb (viewed from the bottom):

 C7R0  C6R0
             C7R2
 C7R1  C6R1
             C5R5
 C7R5  C6R5


For the directional switch below the display, use columns 0-4 on row 6.

# I2C Connection

From the outside of the keyboard to inside, the pins are:

  GND SCL INT SDA VCC

Having GND on the outside hopefully makes it a little more likely that it has
contact first before other pins when connecting/disconnecting, if it ever
happens to be pulled off while powered on.

# SX1509 Connections

Notes to record which wires get connected to each of the SX1509 pins:

## Left

- 0
  - Row 0 from Main keypad
  - Row 0 from Thumb
- 1
  - Row 1 from Main keypad
  - Row 1 from Thumb
- 2
  - Row 2 from Main keypad
  - Row 2 from Thumb
- 3
  - Row 3 from Main keypad
- VC1
  - None (connected by on-board jumpers to VCC)
- 4
  - Row 4 from Main keypad
- 5
  - Row 5 from Main keypad
  - Row 5 from Thumb
- 6
  - Directional switch common pin
- 7

- 8
  - Column 0 from Main keypad
  - Directional switch 0
- 9
  - Column 1 from Main keypad
  - Directional switch 1
- 10
  - Column 2 from Main keypad
  - Directional switch 2
- 11
  - Column 3 from Main keypad
  - Directional switch 3
- VC2
  - None (connected by on-board jumpers to VCC)
- 12
  - Column 4 from Main keypad
  - Directional switch 4
- 13
  - Column 5 from Main keypad
  - Column 5 from Thumb
- 14
  - Column 6 from Main keypad
  - Column 6 from Thumb
- 15
  - Column 7 from Thumb

## Right

The right side is the same as the left, but without the directional switch.
