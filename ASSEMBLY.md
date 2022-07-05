I printed everything with PLA, on a Prusa MK3S.  Most parts require support,
and I just used detachable PLA support.  On Prusaslicer I did increase the
default support Z distance slightly to make it a bit easier to detach.

- Underlay

  I printed this using the Ultimaker Cura slicer, with tree supports.
  Cura does a much better job generating supports for this model than
  Prusaslicer.


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
