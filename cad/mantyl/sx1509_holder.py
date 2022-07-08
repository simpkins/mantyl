#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

from . import blender_util
from . import cad


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


def sx1509_holder() -> bpy.types.Object:
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


def test(show_breakout: bool = True) -> bpy.types.Object:
    if show_breakout:
        breakout = sx1509_breakout()

    holder = sx1509_holder()
    with blender_util.TransformContext(holder) as ctx:
        ctx.rotate(90, "Z")
        ctx.rotate(90, "X")
        ctx.translate(0.0, 3.81, 0.0)
