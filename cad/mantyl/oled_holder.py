#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

from . import cad
from . import blender_util

import bpy
from typing import Tuple


def oled_holder_parts(wall_thickness: float = 4.0) -> bpy.types.Object:
    front_y = -0.1
    back_y = wall_thickness + 0.2

    # The display is not centered on the PCB face.
    # Make the display centered, and the PCB offset a little bit.
    display_offset = 2.5 * 0.5

    display_w = 30
    display_h = 12.2
    display_thickness = 1.53 + 0.1

    pcb_w = 33.5
    pcb_h = 21.8
    pcb_thickness = 1.57
    pcb_tolerance = 0.5

    display_x_r = display_w * 0.5
    display_h_r = display_h * 0.5
    display_cutout = blender_util.range_cube(
        (-display_x_r, display_x_r),
        (front_y, display_thickness),
        (-display_h_r, display_h_r),
        name = "oled_cutout",
    )

    pcb_x_r = (pcb_w + pcb_tolerance) * 0.5
    pcb_h_r = (pcb_h + pcb_tolerance) * 0.5
    pcb_cutout = blender_util.range_cube(
        (-pcb_x_r + display_offset, pcb_x_r + display_offset),
        (display_thickness, back_y),
        (-pcb_h_r, pcb_h_r),
    )
    blender_util.union(display_cutout, pcb_cutout)

    header_cutout_w = 18.0
    header_cutout = blender_util.range_cube(
        (
            header_cutout_w * -0.5 + display_offset,
            header_cutout_w * 0.5 + display_offset,
        ),
        (1.0, display_thickness),
        (-pcb_h_r + 0.25, -pcb_h_r + 0.25 + 4.0),
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
    f_bl = mesh.add_xyz(display_x_r, 0.2, -display_h_r)
    f_tl = mesh.add_xyz(display_x_r, 0.2, display_h_r - 2.0)
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
        pcb_x_r + display_offset + oled_cutout_x,
        back_y,
        display_h_r - 2.0,
    )

    mesh.add_quad(f_tl, f_bl, b_bl, b_tl)
    mesh.add_quad(b_tr, b_tl, b_bl, b_br)
    mesh.add_quad(f_tr, b_tr, b_br, f_br)
    mesh.add_quad(f_tl, f_tr, f_br, f_bl)
    mesh.add_quad(f_tl, b_tl, b_tr, f_tr)
    mesh.add_quad(f_bl, f_br, b_br, b_bl)
    oled_cable_cutout = blender_util.new_mesh_obj("oled_cable_cutout", mesh)
    blender_util.union(display_cutout, oled_cable_cutout)

    # At the moment, don't bother with studs for the PCB screw holes
    return display_cutout

    stud_positions = [
        (-14.0, -8.325),
        (14.0, -8.325),
        (14.0, 8.175),
        (-14.0, 8.175),
    ]
    stud_r = 1.25 * 0.85
    for (x, z) in stud_positions:
        stud_h = back_y - display_thickness
        stud = blender_util.cylinder(r=stud_r, h=stud_h, fn=32)
        with blender_util.TransformContext(stud) as ctx:
            ctx.rotate(90, "X")
            ctx.translate(x, (stud_h * 0.5) + display_thickness, z)

        blender_util.difference(display_cutout, stud)

    return display_cutout


def test() -> bpy.types.Object:
    wall = blender_util.range_cube((-25, 25), (0.0, 4.0), (-20.0, 20.0))
    neg = oled_holder_parts(4.0)
    blender_util.difference(wall, neg)

    return wall
