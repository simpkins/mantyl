# Printing

I printed everything on a Prusa MK3S.

## Shells & Thumb Underlays

I printed these with PLA.  The shells require support; I just used simple PLA
supports that break away.

## Underlays

Prusaslicer did not do a very good job generating supports for these, so I
used the Cura slicer.  It's tree support functionality does a good job adding
supports for this part, and they broke away fairly easily, despite the fact
that this part is somewhat thin and fragile.

## SX1509 Clips

I printed these out of TPU, since I had some available from a previous project.
I was concerned that the clips would be more likely to break with PLA.


# Wiring

For wiring the keyboard, I used 28 gauge Soderon 155 from TEMCo.  This wire
does not need to be stripped prior to soldering, which saves time since there
are a lot of keys to solder.  It has a nylon insulation that will melt and act
as flux when soldering.  Note that it requires a minimum temperature of 390 C.

# Rows and Columns

The diodes can be installed in either direction, as long as you are consistent
throughout.

For my boards, I assembled the diodes with the anode connected to the switch,
and the cathode connected to the row wire.  I connected the rows to bank A of
the SX1509 (pins 1-7) and the columns to Bank B (pins 8-15).  Bank A therefore
needs to be configured as open drain, and bank B as pull-up.
