#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

from . import cad
from . import blender_util
from . import screw_holes

import bpy
from typing import Tuple


def oled_cutout(wall_thickness: float = 4.0) -> bpy.types.Object:
    front_y = -0.1
    back_y = wall_thickness + 0.2

    # The display is not centered on the PCB face.
    # Make the display centered, and the PCB offset a little bit.
    display_offset = (2.5 * 0.5) - 0.1

    display_w = 30.3
    display_h = 12.2
    display_thickness = 1.53

    pcb_w = 33.5
    pcb_h = 21.8
    pcb_thickness = 1.57
    pcb_tolerance = 0.5

    display_x_r = display_w * 0.5
    display_h_r = display_h * 0.5
    display_cutout = blender_util.range_cube(
        (-display_x_r, display_x_r),
        (front_y, display_thickness),
        # Give a little more room on the top, since the top sags a little
        # even when printing with supports
        (-display_h_r, display_h_r + 0.2),
        name="oled_cutout",
    )

    pcb_x_r = (pcb_w + pcb_tolerance) * 0.5
    pcb_h_r = (pcb_h + pcb_tolerance) * 0.5
    pcb_cutout = blender_util.range_cube(
        (-pcb_x_r + display_offset, pcb_x_r + display_offset),
        (display_thickness, back_y),
        # Give a little more room on the top, since the top sags a little
        # even when printing with supports
        (-pcb_h_r, pcb_h_r + 0.2),
    )
    blender_util.union(display_cutout, pcb_cutout)

    header_cutout_w = 18.0
    header_cutout = blender_util.range_cube(
        (
            header_cutout_w * -0.5 + display_offset,
            header_cutout_w * 0.5 + display_offset,
        ),
        (1.0, display_thickness),
        (-pcb_h_r, -display_h_r + 4.0),
    )
    blender_util.union(display_cutout, header_cutout)

    qt_cutout_h = 9
    qt_cutout_w = 3
    qt_cable_cutout = blender_util.range_cube(
        (-pcb_x_r + display_offset, -pcb_x_r + display_offset - qt_cutout_w),
        (display_thickness, back_y),
        (qt_cutout_h * -0.5, qt_cutout_h * 0.5),
    )
    blender_util.union(display_cutout, qt_cable_cutout)

    oled_cutout_x = 1.0
    mesh = cad.Mesh()
    f_bl = mesh.add_xyz(display_x_r, 0.4, -display_h_r)
    f_tl = mesh.add_xyz(display_x_r, 0.4, display_h_r - 2.0)
    b_bl = mesh.add_xyz(display_x_r, back_y, -display_h_r)
    b_tl = mesh.add_xyz(display_x_r, back_y, display_h_r - 2.0)

    f_br = mesh.add_xyz(
        pcb_x_r + display_offset + oled_cutout_x,
        display_thickness,
        -display_h_r,
    )
    f_tr = mesh.add_xyz(
        pcb_x_r + display_offset + oled_cutout_x,
        display_thickness,
        display_h_r - 2.0,
    )
    b_br = mesh.add_xyz(
        pcb_x_r + display_offset + oled_cutout_x, back_y, -display_h_r
    )
    b_tr = mesh.add_xyz(
        pcb_x_r + display_offset + oled_cutout_x, back_y, display_h_r - 2.0
    )

    mesh.add_quad(f_tl, f_bl, b_bl, b_tl)
    mesh.add_quad(b_tr, b_tl, b_bl, b_br)
    mesh.add_quad(f_tr, b_tr, b_br, f_br)
    mesh.add_quad(f_tl, f_tr, f_br, f_bl)
    mesh.add_quad(f_tl, b_tl, b_tr, f_tr)
    mesh.add_quad(f_bl, f_br, b_br, b_bl)
    oled_cable_cutout = blender_util.new_mesh_obj("oled_cable_cutout", mesh)
    blender_util.union(display_cutout, oled_cable_cutout)

    return display_cutout


def hat_cutout(
    wall_thickness: float = 4.0
) -> Tuple[bpy.types.Object, bpy.types.Object]:
    front_y = -0.2
    back_y = wall_thickness + 0.2

    base_w = 12.8
    base_h = 12.8

    hole_w = 9.5
    hole_h = 9.5
    cutout = blender_util.cylinder(r=hole_w * 0.5, h=wall_thickness + 1, fn=64)
    with blender_util.TransformContext(cutout) as ctx:
        ctx.rotate(90, "X")
        ctx.translate(0.0, wall_thickness * 0.5, 0.0)

    full_d = 12.0
    protrude_d = 3.0
    nub_d = 7.0
    pos_d = full_d - protrude_d - 1.0

    pos_w = base_w + 4.0
    pos_h = base_h + 4.0
    pos = blender_util.range_cube(
        (pos_w * -0.5, pos_w * 0.5), (0.5, pos_d), (-9.0, base_h * 0.5)
    )

    pos_w = base_w + 4.0
    pos_h = base_h + 4.0
    base_cutout = blender_util.range_cube(
        (base_w * -0.5, base_w * 0.5),
        (nub_d - protrude_d, pos_d + 1.0),
        (base_h * -0.5, base_h * 0.5),
    )
    blender_util.union(cutout, base_cutout)

    return pos, cutout


def apply_oled_holder(
    wall: bpy.types.Object,
    p1: cad.Point,
    p2: cad.Point,
    mirror_x: bool = False,
) -> None:
    oled_neg = oled_cutout(4.0)
    if mirror_x:
        with blender_util.TransformContext(oled_neg) as ctx:
            ctx.mirror_x()
    blender_util.apply_to_wall(oled_neg, p1, p2, x=0.0, z=27.0)
    blender_util.difference(wall, oled_neg)

    hat_pos, hat_neg = hat_cutout()
    blender_util.apply_to_wall(hat_pos, p1, p2, x=0.0, z=9.0)
    blender_util.apply_to_wall(hat_neg, p1, p2, x=0.0, z=9.0)
    blender_util.union(wall, hat_pos)
    blender_util.difference(wall, hat_neg)


class Backplate:
    standoff_d = 4.25
    standoff_h = 6

    y_front = standoff_h - 0.1
    y_back = standoff_h + 2.0
    base_y_range = (y_front, y_back)

    display_offset = 2.5 * 0.5
    base_w = 33

    stud_positions = [
        (-14.0, -8.325),
        (14.0, -8.325),
        (14.0, 8.175),
        (-14.0, 8.175),
    ]

    screw_hole_r = 4.25 * 0.5
    screw_plate_r = 4.5

    # The OLED display is centered at Z=0
    # The directional hat button is centered at Z=hat_z
    hat_z = 9.0 - 27.0

    z_top = 11.0

    bottom_screw_x = (-12.0, 12.0)

    def __init__(self, left: bool) -> None:
        self.left = left

        self.x_left = self.base_w * -0.5
        self.x_right = (self.base_w * 0.5) + self.display_offset

        if left:
            self.top_screw_x = self.x_right - self.screw_plate_r
        else:
            self.top_screw_x = self.x_left + self.screw_plate_r
        self.top_screw_z = self.z_top + 3.25

        self.screw_positions = [
            (self.top_screw_x, self.top_screw_z),
            (self.bottom_screw_x[0], self.hat_z),
            (self.bottom_screw_x[1], self.hat_z),
        ]

    def gen_backplate(self) -> bpy.types.Object:
        z_bottom = self.hat_z

        # Central base plate
        base_x_range = (self.x_left, self.x_right)
        base_z_range = (z_bottom, self.z_top)
        base = blender_util.range_cube(
            base_x_range, self.base_y_range, base_z_range,
            name="oled_backplate",
        )

        # Standoffs to hold OLED PCB
        standoff_y = self.standoff_h * 0.5
        for x, z in self.stud_positions:
            standoff = blender_util.cylinder(
                r=self.standoff_d * 0.5, h=self.standoff_h
            )
            with blender_util.TransformContext(standoff) as ctx:
                ctx.rotate(90, "X")
                ctx.translate(x + self.display_offset, standoff_y, z)
            blender_util.union(base, standoff)

        if self.left:
            # Bevel the corner opposite the top screw hole
            # This provides more clearance between it and the thumb keys
            center_x = (self.stud_positions[3][0] + self.display_offset)
            r = center_x - self.x_left
            center_z = self.z_top - r

            stud_cutout = blender_util.range_cube(
                (self.x_left, center_x),
                self.base_y_range,
                (center_z, self.z_top),
            )
            blender_util.difference(base, stud_cutout)
            stud_circle = self.base_cyl(r=r, x=center_x, z=center_z)
            blender_util.union(base, stud_circle)
        else:
            # Bevel the corner opposite the top screw hole
            # This provides more clearance between it and the thumb keys
            center_x = (self.stud_positions[2][0] + self.display_offset)
            r = self.x_right - center_x
            center_z = self.z_top - r

            stud_cutout = blender_util.range_cube(
                (center_x, self.x_right),
                self.base_y_range,
                (center_z, self.z_top),
            )
            blender_util.difference(base, stud_cutout)
            stud_circle = self.base_cyl(r=r, x=center_x, z=center_z)
            blender_util.union(base, stud_circle)

        # Top screw plate
        top_plate_square = blender_util.range_cube(
            (
                self.top_screw_x - self.screw_plate_r,
                self.top_screw_x + self.screw_plate_r,
            ),
            self.base_y_range,
            (self.z_top, self.top_screw_z),
        )
        blender_util.union(base, top_plate_square)
        top_plate_cyl = self.base_cyl(
            r=self.screw_plate_r, x=self.top_screw_x, z=self.top_screw_z
        )
        blender_util.union(base, top_plate_cyl)
        top_screw_hole = self.base_cyl(
            r=self.screw_hole_r,
            thick_factor=1.5,
            x=self.top_screw_x,
            z=self.top_screw_z,
        )
        blender_util.difference(base, top_screw_hole)

        # Bottom square plate
        bottom_plate = blender_util.range_cube(
            (self.bottom_screw_x[0], self.bottom_screw_x[1]),
            self.base_y_range,
            (z_bottom - 7.5, z_bottom),
        )
        blender_util.union(base, bottom_plate)

        # Bottom screw holes
        for x in self.bottom_screw_x:
            screw_plate = self.base_cyl(
                r=self.screw_plate_r, x=x, z=self.hat_z
            )
            blender_util.union(base, screw_plate)
            screw_hole = self.base_cyl(
                r=self.screw_hole_r, x=x, z=self.hat_z, thick_factor=1.5
            )
            blender_util.difference(base, screw_hole)

        # Holes for the directional hat pins
        x_pin_width = 10.5
        for x_pin_off in (x_pin_width * -0.5, x_pin_width * 0.5):
            pin_hole = blender_util.range_cube(
                (x_pin_off - 1, x_pin_off + 1),
                (self.y_front - 1.0, self.y_back + 1.0),
                (self.hat_z - 4.5, self.hat_z + 4.5),
            )
            blender_util.difference(base, pin_hole)

        y_offset = 3.3
        with blender_util.TransformContext(base) as ctx:
            ctx.translate(0.0, y_offset, 0.0)
        return base

    def base_cyl(
        self, r: float, x: float, z: float, thick_factor: float = 1.0,
        name: str = "cylinder"
    ) -> bpy.types.Object:
        thickness = (self.y_back - self.y_front) * thick_factor
        cyl = blender_util.cylinder(r=r, h=thickness, name=name)
        with blender_util.TransformContext(cyl) as ctx:
            ctx.rotate(90, "X")
            ctx.translate(x, (self.y_back + self.y_front) * 0.5, z)
        return cyl


def oled_backplate_left() -> bpy.types.Object:
    return Backplate(left=True).gen_backplate()


def test() -> bpy.types.Object:
    wall = blender_util.range_cube(
        (-22, 22), (0.0, 4.0), (0.0, 45.0), name="wall"
    )
    apply_oled_holder(
        wall, cad.Point(0.0, 0.0, -25), cad.Point(0.0, 0.0, 25.0)
    )

    backplate = Backplate(left=True)
    show_backplate = True
    if show_backplate:
        backplate_obj = backplate.gen_backplate()
        with blender_util.TransformContext(backplate_obj) as ctx:
            ctx.translate(0, 0, 27.0)

    for (x, z) in backplate.screw_positions:
        standoff = screw_holes.unc6_32_screw_standoff()
        with blender_util.TransformContext(standoff) as ctx:
            ctx.rotate(-90, "X")
            ctx.translate(x, 4.0, z + 27.0)

    return wall
