#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

from . import blender_util
from . import screw_holes

import bpy


def apply_usb_cutout(wall: bpy.types.Object) -> None:
    """
    A cut-out that fits some cheap, small USB-C right-angle connectors I found:
    https://www.amazon.com/AGVEE-Degree-Angled-Adapter-Converter/dp/B09FJTTZWY

    Other possible options I considered:
    * USB-C keystone jacks are readily available.  However, these would stick
      out much more inside the keyboard, and would require a cable from the
      keystone jack to the microcontroller.
    * There are also some simple standalone USB-C sockets:
      https://www.adafruit.com/product/4396
      This still requires designing a bracket to hold it in place, and
      soldering a cable to it to connect the microcontroller.
    """
    cutout_h = 11.67
    cutout_w = 6.3

    wall_thickness = 4.0
    stem_depth = 8.5
    full_depth = 14.0

    z_off = 20.0

    # Just to ensure all of the pieces connect if we apply it at an angle,
    # add a small section of wall to attach everything to before applying it
    # to the actual wall.
    wall_block = blender_util.range_cube(
        (-22, 22), (0.0, 4.0), (0.0, 45.0), name="usb_cutout"
    )

    # A block to prevent the USB connector from being pulled through the wall
    stop_w = 5.0
    stop_d = stem_depth - wall_thickness
    stop_x_off = (cutout_w * 0.5) + 0.5
    stem_stop = blender_util.range_cube(
        (stop_x_off, stop_x_off + stop_w),
        (wall_thickness * 0.5, wall_thickness + stop_d),
        (z_off - (cutout_h * 0.5), z_off + (cutout_h * 0.5))
    )
    blender_util.union(wall_block, stem_stop)

    # Add screw stand-offs above and below, so we can screw a backplate
    # to hold the connector in the wall.
    standoff_d = full_depth - wall_thickness - 1.0
    for z in (-10, 10):
        screw_hole = screw_holes.unc6_32_screw_standoff(h=standoff_d)
        with blender_util.TransformContext(screw_hole) as ctx:
            ctx.rotate(-90, "X")
            ctx.translate(0, wall_thickness - 0.1, z_off + z)
        blender_util.union(wall_block, screw_hole)

    # The cutout for the connector
    cutout_d = wall_thickness + 1.0
    cutout = blender_util.cube(cutout_w, cutout_d, cutout_h)
    with blender_util.TransformContext(cutout) as ctx:
        ctx.translate(0, cutout_d * 0.5, z_off)

    # Now apply everything to the actual wall
    blender_util.union(wall, wall_block)
    blender_util.difference(wall, cutout)


def test() -> bpy.types.Object:
    wall = blender_util.range_cube(
        (-22, 22), (0.0, 4.0), (0.0, 45.0), name="wall"
    )
    apply_usb_cutout(wall)

    return wall
