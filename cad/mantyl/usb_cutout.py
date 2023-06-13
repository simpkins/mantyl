#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

from . import blender_util
from . import cad
from . import screw_holes

import bpy


class Cutout:
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

    z_tolerance = 0.45
    xy_tolerance = 0.2
    cutout_h: float = 11.67 + z_tolerance
    cutout_w: float = 6.3 + xy_tolerance

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

    def apply(
        self,
        wall: bpy.types.Object,
        p1: cad.Point,
        p2: cad.Point,
        mirror_x: bool = False,
        flip: bool = False,
        x: float = 0.0,
        z: float = 0.0,
    ) -> None:
        pos = self.generate_positive_shape(flip=flip)

        # The cutout for the connector
        cutout_d = self.wall_thickness + 1.0
        cutout = blender_util.cube(self.cutout_w, cutout_d, self.cutout_h)
        with blender_util.TransformContext(cutout) as ctx:
            ctx.translate(0, cutout_d * 0.5, 0.0)

        if mirror_x or flip:
            with blender_util.TransformContext(
                pos
            ) as ctx1, blender_util.TransformContext(cutout) as ctx2:
                if mirror_x:
                    ctx1.mirror_x()
                    ctx2.mirror_x()
                if flip:
                    ctx1.rotate(180, "Y")
                    ctx2.rotate(180, "Y")

        # Now apply everything to the actual wall
        blender_util.apply_to_wall(pos, p1, p2, x=x, z=z)
        blender_util.apply_to_wall(cutout, p1, p2, x=x, z=z)
        blender_util.union(wall, pos)
        blender_util.difference(wall, cutout)

    def generate_positive_shape(self, flip: bool) -> bpy.types.Object:
        # A block to prevent the USB connector from being pulled through the
        # wall
        stop_d = self.stem_depth - self.wall_thickness
        stop_x_off = (self.cutout_w * 0.5) + 0.5
        pos = blender_util.range_cube(
            (stop_x_off, stop_x_off + self.stem_stop_w),
            (self.wall_thickness * 0.5, self.wall_thickness + stop_d),
            (self.cutout_h * -0.5, self.cutout_h * 0.5),
            name="usb_cutout",
        )

        # Add screw stand-offs above and below, so we can screw a backplate
        # to hold the connector in the wall.
        standoff_d = self.full_depth - self.wall_thickness - 1.0
        for z in (-10, 10):
            screw_hole = screw_holes.unc6_32_screw_standoff(h=standoff_d)
            with blender_util.TransformContext(screw_hole) as ctx:
                ctx.rotate(-90, "X")
                ctx.translate(0, self.wall_thickness - 0.1, z)
            blender_util.union(pos, screw_hole)

        self.add_feather_supports(pos, flip=flip)
        return pos

    def add_feather_supports(self, pos: bpy.types.Object, flip: bool) -> None:
        left_end: float = (self.cutout_w * -0.5) + self.total_len
        right_end: float = left_end - self.feather_l
        top: float = self.feather_h * 0.5
        bottom: float = -top

        screw_overlap_x = 4.0
        screw_overlap_z = 4.0
        screw_extend_y = 3.0

        y_range = (
            self.wall_thickness - 1.0,
            self.feather_y_offset + self.feather_thickness + screw_extend_y,
        )

        def cut_slot(obj: bpy.types.Object) -> None:
            if flip:
                z_range = (bottom - 0.3, top + 0.1)
            else:
                z_range = (bottom - 0.1, top + 0.3)

            cutout = blender_util.range_cube(
                (right_end - 0.3, left_end + 20),
                (
                    self.feather_y_offset - 0.3,
                    self.feather_y_offset + self.feather_thickness + 0.25,
                ),
                z_range,
            )
            blender_util.difference(obj, cutout)

        right_bottom_support = blender_util.range_cube(
            (right_end - 2.0, right_end + screw_overlap_x),
            y_range,
            (bottom - 3, bottom + screw_overlap_z),
        )
        cut_slot(right_bottom_support)
        blender_util.union(pos, right_bottom_support)

        right_top_support = blender_util.range_cube(
            (right_end - 2.0, right_end + screw_overlap_x),
            y_range,
            (top - screw_overlap_z, top + 3),
        )
        cut_slot(right_top_support)
        blender_util.union(pos, right_top_support)

        if flip:
            # When flipping, the bottom becomes the top.
            # We want to put a support on the actual bottom at the back, not
            # the top.  However, there is no screw hole on this side, and the
            # antenna is in the way instead, so use a very small z overlap
            left_overlap_z = 0.8
            left_bottom_support = blender_util.range_cube(
                (left_end - screw_overlap_x, left_end + 2.0),
                y_range,
                (top - left_overlap_z, top + 3.0),
            )
            cut_slot(left_bottom_support)
            blender_util.union(pos, left_bottom_support)

            # Add a screw standoff at the top
            wall_offset = self.wall_thickness - 1.0
            standoff_h = self.feather_y_offset - wall_offset - 0.3
            standoff = screw_holes.screw_standoff(
                h=standoff_h, hole_h=standoff_h - 0.3, outer_d=5, hole_d=2.15
            )
            with blender_util.TransformContext(standoff) as ctx:
                ctx.rotate(-90, "X")

                standoff_x = (
                    left_end
                    - (self.feather_l - self.feather_hole_x_dist) * 0.5
                )
                standoff_z = self.feather_hole_z_dist * -0.5
                ctx.translate(standoff_x, wall_offset, standoff_z)
            blender_util.union(pos, standoff)
        else:
            left_support = blender_util.range_cube(
                (left_end - screw_overlap_x, left_end + 2.0),
                y_range,
                (bottom - 3, bottom + screw_overlap_z),
            )
            cut_slot(left_support)
            blender_util.union(pos, left_support)

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

    def backplate(self) -> bpy.types.Object:
        corner_r = 3.5
        backplate = blender_util.range_cube(
            (0, 8.75), (0, 3.0), (-10 - corner_r, 10 + corner_r)
        )
        section = blender_util.range_cube((-corner_r, 0), (0, 3.0), (-10, 10))
        blender_util.union(backplate, section)

        standoff_d = self.full_depth - self.wall_thickness - 1.0
        for z in (-10, 10):
            ring = blender_util.cylinder(r=corner_r, h=3.0)
            with blender_util.TransformContext(ring) as ctx:
                ctx.rotate(-90, "X")
                ctx.translate(0, 1.5, z)
            blender_util.union(backplate, ring)

            hole = blender_util.cylinder(r=2.0, h=20.0)
            with blender_util.TransformContext(hole) as ctx:
                ctx.rotate(-90, "X")
                ctx.translate(0, 0, z)
            blender_util.difference(backplate, hole)

        return backplate


def backplate() -> bpy.types.Object:
    return Cutout().backplate()


def test() -> bpy.types.Object:
    left_side = True
    z_offset = 15.0

    wall = blender_util.range_cube(
        (-5, 70), (0.0, 4.0), (0.0, 30.0), name="wall"
    )
    c = Cutout()
    c.apply(
        wall,
        p1=cad.Point(-1, 0, 0),
        p2=cad.Point(1, 0, 0),
        mirror_x=left_side,
        flip=left_side,
        x=0.0,
        z=z_offset,
    )

    show_feather = True
    if show_feather:
        f = c.feather()
        x_off = ((c.feather_l + c.cutout_w) * -0.5) + c.total_len
        y_off = (c.feather_thickness * 0.5) + c.feather_y_offset
        with blender_util.TransformContext(f) as ctx:
            ctx.translate(x_off, y_off, 0)
            if left_side:
                ctx.rotate(180, "Y")
            ctx.translate(0, 0, z_offset)

    if left_side:
        with blender_util.TransformContext(wall) as ctx:
            ctx.mirror_x()

    backplate = c.backplate()
    with blender_util.TransformContext(backplate) as ctx:
        if left_side:
            ctx.rotate(180, "Y")
        ctx.translate(0, c.full_depth, z_offset)

    return wall
