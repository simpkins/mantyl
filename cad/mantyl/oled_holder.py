#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

from . import cad
from . import blender_util

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

    full_d = 13.0
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


def oled_backplate(left: bool = True) -> bpy.types.Object:
    z_offset = 0.0
    y_offset = 3.3

    standoff_d = 4.25
    standoff_h = 6

    screw_hole_r = 4.75 * 0.5

    display_offset = 2.5 * 0.5
    base_w = 33
    base_h = 22
    base_y_range = (standoff_h - 0.1, standoff_h + 2.0)
    base = blender_util.range_cube(
        ((base_w * -0.5) + display_offset, (base_w * 0.5) + display_offset),
        base_y_range,
        (base_h * -0.5, base_h * 0.5),
    )

    stud_positions = [
        (-14.0, -8.325),
        (14.0, -8.325),
        (14.0, 8.175),
        (-14.0, 8.175),
    ]
    standoff_y = standoff_h * 0.5
    for x, z in stud_positions:
        standoff = blender_util.cylinder(r=standoff_d * 0.5, h=standoff_h)
        with blender_util.TransformContext(standoff) as ctx:
            ctx.rotate(90, "X")
            ctx.translate(x + display_offset, standoff_y, z)

        blender_util.union(base, standoff)

    if left:
        top_plate_offset = 13.75
    else:
        top_plate_offset = -11.25
    top_screw_plate = blender_util.range_cube(
        (-4.0 + top_plate_offset, 4.0 + top_plate_offset),
        base_y_range,
        (base_h * 0.5, (base_h * 0.5) + 6.5),
    )
    screw_hole = blender_util.cylinder(r=screw_hole_r, h=4)
    with blender_util.TransformContext(screw_hole) as ctx:
        ctx.rotate(90, "X")
        ctx.translate(
            top_plate_offset, 2 + standoff_h - 0.2, (base_h * 0.5) + 3.0
        )
    blender_util.union(base, top_screw_plate)
    blender_util.difference(base, screw_hole)

    bottom_plate = blender_util.range_cube(
        (-16.0 + display_offset, 15.0 + display_offset),
        base_y_range,
        ((base_h * -0.5) - 12, (base_h * -0.5)),
    )
    blender_util.union(base, bottom_plate)

    bottom_plate2 = blender_util.range_cube(
        (-8, 8), base_y_range, (((base_h * -0.5) - 15), (base_h * -0.5) - 12)
    )
    blender_util.union(base, bottom_plate2)

    y_pin_off = 9 - 27
    for x_pin_off in (10.3 * -0.5, 10.3 * 0.5):
        pin_hole = blender_util.range_cube(
            (x_pin_off - 0.5, x_pin_off + 0.5),
            (base_y_range[0] - 1.0, base_y_range[1] + 1.0),
            (y_pin_off - 4.5, y_pin_off + 4.5),
        )
        blender_util.difference(base, pin_hole)

    screw_hole_l = blender_util.cylinder(r=screw_hole_r, h=4)
    with blender_util.TransformContext(screw_hole_l) as ctx:
        ctx.rotate(90, "X")
        ctx.translate(12.0, 2 + standoff_h - 0.2, (base_h * -0.5) - 7.5)
    blender_util.difference(base, screw_hole_l)
    screw_hole_r = blender_util.cylinder(r=screw_hole_r, h=4)
    with blender_util.TransformContext(screw_hole_r) as ctx:
        ctx.rotate(90, "X")
        ctx.translate(-11.5, 2 + standoff_h - 0.2, (base_h * -0.5) - 7.5)
    blender_util.difference(base, screw_hole_r)

    with blender_util.TransformContext(base) as ctx:
        ctx.translate(0.0, y_offset, z_offset)
    return base


def oled_backplate_left() -> bpy.types.Object:
    return oled_backplate(left=True)


def screw_standoff() -> bpy.types.Object:
    fn=64
    d = 5.5
    hole_d = 3.25
    h = 4.5

    standoff = blender_util.cylinder(r=d * 0.5, h=h, fn=fn)
    hole = blender_util.cylinder(r=hole_d * 0.5, h=h, fn=fn)
    blender_util.difference(standoff, hole)
    with blender_util.TransformContext(standoff) as ctx:
        ctx.translate(0.0, 0.0, h * 0.5)
    return standoff


def test() -> bpy.types.Object:
    wall = blender_util.range_cube((-22, 22), (0.0, 4.0), (0.0, 45.0))
    apply_oled_holder(
        wall, cad.Point(0.0, 0.0, -25), cad.Point(0.0, 0.0, 25.0)
    )

    show_backplate = True
    if show_backplate:
        backplate = oled_backplate(left=True)
        with blender_util.TransformContext(backplate) as ctx:
            ctx.translate(0, 0, 27.0)

    standoff_positions = [(12.0, 8.5), (-11.5, 8.5), (13.75, 41.0)]
    for (x, z) in standoff_positions:
        standoff = screw_standoff()
        with blender_util.TransformContext(standoff) as ctx:
            ctx.rotate(-90, "X")
            ctx.translate(x, 4.0, z)

    return wall
