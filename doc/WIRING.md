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


For the hat switch use columns 0-4 on row 6.

# I2C Connection

From the outside of the keyboard to inside, the pins are:

  GND SCL VCC SDA INT

Having GND on the outside hopefully makes it a little more likely that it has
contact first before other pins when connecting/disconnecting, if it ever
happens to be pulled off while powered on.
