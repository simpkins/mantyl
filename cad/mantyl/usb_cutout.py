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
    return Cutout().apply(wall, z_off=15.0)


class Cutout:
    z_tolerance = 0.45
    xy_tolerance = 0.2
    cutout_h = 11.67 + z_tolerance
    cutout_w = 6.3 + xy_tolerance

    wall_thickness = 4.0
    stem_depth = 8.4
    full_depth = 14.0

    # total length with a feather connected to the USB connector
    total_len = 67.10

    stem_stop_w = 5.0

    # Adafruit feather spec:
    # https://learn.adafruit.com/adafruit-feather/feather-specification
    feather_h = 22.86
    feather_l = 50.8
    feather_thickness = 1.03
    feather_hole_x_dist = 45.72  # 1.8"
    feather_hole_z_dist = 17.78  # 0.7"
    feather_hole_r = 1.27  # 0.05"

    feather_y_offset = 8.2

    def apply(self, wall: bpy.types.Object, z_off: float) -> None:
        self.apply_cutout_and_screws(wall, z_off)
        self.apply_feather_supports(wall, z_off)

    def apply_cutout_and_screws(
        self, wall: bpy.types.Object, z_off: float
    ) -> None:
        # Just to ensure all of the pieces connect if we apply it at an angle,
        # add a small section of wall to attach everything to before applying it
        # to the actual wall.
        wall_block = blender_util.range_cube(
            (-5, 10),
            (3.0, 4.0),
            (z_off - 15.0, z_off + 15.0),
            name="usb_cutout",
        )

        # A block to prevent the USB connector from being pulled through the wall
        stop_d = self.stem_depth - self.wall_thickness
        stop_x_off = (self.cutout_w * 0.5) + 0.5
        stem_stop = blender_util.range_cube(
            (stop_x_off, stop_x_off + self.stem_stop_w),
            (self.wall_thickness * 0.5, self.wall_thickness + stop_d),
            (z_off - (self.cutout_h * 0.5), z_off + (self.cutout_h * 0.5)),
        )
        blender_util.union(wall_block, stem_stop)

        # Add screw stand-offs above and below, so we can screw a backplate
        # to hold the connector in the wall.
        standoff_d = self.full_depth - self.wall_thickness - 1.0
        for z in (-10, 10):
            screw_hole = screw_holes.unc6_32_screw_standoff(h=standoff_d)
            with blender_util.TransformContext(screw_hole) as ctx:
                ctx.rotate(-90, "X")
                ctx.translate(0, self.wall_thickness - 0.1, z_off + z)
            blender_util.union(wall_block, screw_hole)

        # The cutout for the connector
        cutout_d = self.wall_thickness + 1.0
        cutout = blender_util.cube(self.cutout_w, cutout_d, self.cutout_h)
        with blender_util.TransformContext(cutout) as ctx:
            ctx.translate(0, cutout_d * 0.5, z_off)

        # Now apply everything to the actual wall
        blender_util.union(wall, wall_block)
        blender_util.difference(wall, cutout)

    def apply_feather_supports(
        self, wall: bpy.types.Object, z_off: float
    ) -> None:
        left_end = (self.cutout_w * -0.5) + self.total_len
        right_end = left_end - self.feather_l
        bottom = z_off - (self.feather_h * 0.5)
        top = z_off + (self.feather_h * 0.5)

        screw_overlap_x = 4.0
        screw_overlap_z = 4.0
        screw_extend_y = 3.0

        y_range = (
            self.wall_thickness - 1.0,
            self.feather_y_offset + self.feather_thickness + screw_extend_y,
        )

        def cut_slot(obj: bpy.types.Object) -> None:
            cutout = blender_util.range_cube(
                (right_end - 0.3, left_end + 20),
                (
                    self.feather_y_offset - 0.3,
                    self.feather_y_offset + self.feather_thickness + 0.25,
                ),
                (bottom - 0.1, top + 0.4),
            )
            blender_util.difference(obj, cutout)

        left_support = blender_util.range_cube(
            (left_end - screw_overlap_x, left_end + 2.0),
            y_range,
            (bottom - 3, bottom + screw_overlap_z),
        )
        cut_slot(left_support)
        blender_util.union(wall, left_support)

        right_bottom_support = blender_util.range_cube(
            (right_end - 2.0, right_end + screw_overlap_x),
            y_range,
            (bottom - 3, bottom + screw_overlap_z),
        )
        cut_slot(right_bottom_support)
        blender_util.union(wall, right_bottom_support)

        right_top_support = blender_util.range_cube(
            (right_end - 2.0, right_end + screw_overlap_x),
            y_range,
            (top - screw_overlap_z, top + 3),
        )
        cut_slot(right_top_support)
        blender_util.union(wall, right_top_support)

    def feather(self) -> bpy.types.Object:
        f = blender_util.cube(
            self.feather_l, self.feather_thickness, self.feather_h
        )

        # The FeatherS3 that I am using only has holes at 3 corners
        hole_positions = [
            (self.feather_hole_x_dist * 0.5, self.feather_hole_z_dist * -0.5),
            (self.feather_hole_x_dist * -0.5, self.feather_hole_z_dist * 0.5),
            (self.feather_hole_x_dist * -0.5, self.feather_hole_z_dist * -0.5),
        ]
        for (x, z) in hole_positions:
            hole = blender_util.cylinder(
                r=self.feather_hole_r, h=self.feather_thickness * 2.0
            )
            with blender_util.TransformContext(hole) as ctx:
                ctx.rotate(-90, "X")
                ctx.translate(x, 0.0, z)
            blender_util.difference(f, hole)
        return f


def test() -> bpy.types.Object:
    wall = blender_util.range_cube(
        (-5, 70), (0.0, 4.0), (0.0, 30.0), name="wall"
    )
    c = Cutout()
    c.apply(wall, z_off=15.0)

    show_feather = False
    if show_feather:
        f = c.feather()
        x_off = ((c.feather_l + c.cutout_w) * -0.5) + c.total_len
        y_off = (c.feather_thickness * 0.5) + c.feather_y_offset
        with blender_util.TransformContext(f) as ctx:
            ctx.translate(x_off, y_off, 15)

    return wall
