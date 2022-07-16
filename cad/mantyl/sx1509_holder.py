#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

from . import blender_util
from . import cad
from . import screw_holes


def sx1509_breakout() -> bpy.types.Object:
    y_off = -2.0

    w = 36.2
    h = 26
    d = 1.57

    obj = blender_util.cube(w, d, h, name="sx1509")

    def hole(x: float, z: float) -> bpy.types.Object:
        hole = blender_util.cylinder(h=2, r=3.302 / 2, fn=30)
        with blender_util.TransformContext(hole) as ctx:
            ctx.rotate(90.0, "X")
            ctx.translate(x, 0.0, z)

        return hole

    blender_util.difference(obj, hole(15.367, 10.287))
    blender_util.difference(obj, hole(-15.367, 10.287))
    blender_util.difference(obj, hole(-15.367, -10.287))
    blender_util.difference(obj, hole(15.367, -10.287))

    return obj


def clip_pin() -> bpy.types.Object:
    hole_d = 3.302

    base_r = 2.2
    base_h = 3.0

    mid_r = 1.55
    mid_h = 2.0

    top_r = 2.0
    top_h = 2.5

    base = blender_util.cylinder(r=base_r, h=base_h)
    with blender_util.TransformContext(base) as ctx:
        ctx.translate(0.0, 0.0, base_h * 0.5)

    mid = blender_util.cylinder(r=mid_r, h=mid_h)
    with blender_util.TransformContext(mid) as ctx:
        ctx.translate(0.0, 0.0, base_h + (mid_h * 0.5))
    blender_util.union(base, mid)

    top = blender_util.cone(r=top_r, h=top_h)
    with blender_util.TransformContext(top) as ctx:
        ctx.translate(0.0, 0.0, base_h + mid_h + (top_h * 0.5))
    blender_util.union(base, top)

    top_invert = blender_util.cone(r=top_r, h=top_h)
    with blender_util.TransformContext(top_invert) as ctx:
        ctx.rotate(180.0, "X")
        ctx.translate(0.0, 0.0, base_h + mid_h - (top_h * 0.5))
    blender_util.union(base, top_invert)

    cutout = blender_util.range_cube(
        (-base_r * 2, base_r * 2),
        (-0.3, 0.3),
        (base_h + mid_h - 1.0, base_h + mid_h + top_h + 1.0),
    )
    blender_util.difference(base, cutout)

    return base


def sx1509_clip_holder() -> bpy.types.Object:
    """
    A holder with clips that push through the holes in the SX1509 board.
    This does not require screws.  However, it works a little better if printed
    with TPU, then heat-welded to the shell.  If printed in PLA then the clips
    are more likely to break.
    """
    x = 10.287
    y = 15.367

    tl = clip_pin()
    tr = clip_pin()
    bl = clip_pin()
    br = clip_pin()
    with blender_util.TransformContext(tl) as ctx:
        ctx.translate(-x, y, 0.0)
    with blender_util.TransformContext(tr) as ctx:
        ctx.translate(x, y, 0.0)
    with blender_util.TransformContext(bl) as ctx:
        ctx.translate(-x, -y, 0.0)
    with blender_util.TransformContext(br) as ctx:
        ctx.translate(x, -y, 0.0)

    # Print a very thin base layer.  This does not need to be very substantial,
    # it exists just to hold the clips in place and to provide slightly more
    # surface area to glue it to the keyboard wall.
    # .45mm is enough for 3 layers if printing with .15mm layers.
    base_h = 0.45
    base_x = x + 2.5
    base_y = y + 2.5
    base = blender_util.range_cube(
        (-base_x, base_x), (-base_y, base_y), (0.0, base_h)
    )

    blender_util.union(base, tl)
    blender_util.union(base, tr)
    blender_util.union(base, bl)
    blender_util.union(base, br)
    return base


def apply_screw_holder(
    wall: bpy.types.Object,
    p1: cad.Point,
    p2: cad.Point,
    x: float = 0.0,
    z: float = 0.0,
) -> None:
    """
    A holder with screw standoffs for the SX1509 board.
    """
    hole_x = 15.367
    hole_z = 10.287

    screw_hole_d = 3.3

    # Set the hole up for a 1/4" #3 machine screw
    hole_d = 2.5
    outer_d = 4.5
    h = 5.5
    hole_h = h

    for x_mul in (-1, 1):
        for z_mul in (-1, 1):
            standoff = screw_holes.screw_standoff(
                h=h, hole_h=hole_h, outer_d=outer_d, hole_d=hole_d
            )

            with blender_util.TransformContext(standoff) as ctx:
                ctx.rotate(-90, "X")
                ctx.translate(hole_x * x_mul, -0.1, hole_z * z_mul)

            blender_util.apply_to_wall(standoff, p1, p2, x, z)
            blender_util.union(wall, standoff)


def test_clip_holder(show_breakout: bool = True) -> bpy.types.Object:
    if show_breakout:
        breakout = sx1509_breakout()

    holder = sx1509_clip_holder()
    with blender_util.TransformContext(holder) as ctx:
        ctx.rotate(90, "Z")
        ctx.rotate(90, "X")
        ctx.translate(0.0, 3.81, 0.0)


def test_screw_holder(show_breakout: bool = True) -> bpy.types.Object:
    show_breakout=False
    if show_breakout:
        breakout = sx1509_breakout()
        with blender_util.TransformContext(breakout) as ctx:
            ctx.translate(0, 9, 0)

    wall = blender_util.range_cube(
        (-22, 22), (0.0, 4.0), (-15, 15), name="wall"
    )

    holder = apply_screw_holder(wall, cad.Point(-1, 4, 0), cad.Point(1, 4, 0))
