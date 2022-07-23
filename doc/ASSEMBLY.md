# Printing

I printed everything with PLA on a Prusa MK3S.

## Supports

Most of these parts have a lot of overhangs, and require supports.  I printed
breakaway supports, and was actually pleasantly surprised at how well this
worked, and that it was relatively straightforward to remove the supports
afterwards.

I sliced most of the models using Prusaslicer.  To make the supports easier to
remove, I printed with a 0.2mm Z contact distance for the supports, and a 100%
XY contact distance (as a function of the external perimeter width).  I used 2
top support interface layers, and 0 bottom interface layers.  I also expanded
the support pattern spacing to 3mm, just to reduce the amount of support
material printed.

I wasn't able to get Prusaslicer to avoid printing supports inside the screw
standoffs--even with support blockers, it still ends up generating supports
inside the screw hole if it needs to support something else above the screw
standoff.  In practice, this wasn't a big deal; the support material inside the
screw holes is not very much, and could be removed carefully with a drill bit.

## Underlays

Prusaslicer did not do a great job generating supports for the main underlays
that hold the switch sockets, so I sliced these using the Cura slicer.  It's
tree support functionality does a good job adding supports for this part, and
they broke away fairly easily, despite the fact that this part is somewhat thin
and fragile.


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
the SX1509 (pins 0-7) and the columns to Bank B (pins 8-15).  Bank A therefore
needs to be configured as open drain, and bank B as pull-up.
