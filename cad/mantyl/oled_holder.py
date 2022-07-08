#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

from . import blender_util

import bpy
from typing import Tuple


def oled_holder_parts(
    wall_thickness: float
) -> Tuple[bpy.types.Object, bpy.types.Object]:
    display_w = 32.5
    display_h = 12.2
    extra_thickness = 0.1
    display_thickness = 1.53 + extra_thickness

    pcb_w = 33.5
    pcb_h = 21.8
    pcb_thickness = 1.57
    pcb_tolerance = 0.5

    qt_cable_h = 9
    qt_cable_cutout_w = 3

    display_cutout = blender_util.cube(display_w, display_thickness, display_h)
    with blender_util.TransformContext(display_cutout) as ctx:
        ctx.translate(0, (display_thickness - extra_thickness) / 2, 0)
    pcb_cutout = blender_util.cube(
        pcb_w + pcb_tolerance, wall_thickness, pcb_h + pcb_tolerance
    )
    with blender_util.TransformContext(pcb_cutout) as ctx:
        ctx.translate(0, (wall_thickness / 2) + display_thickness - 0.1, 0)
    qt_cable_cutout = blender_util.cube(
        qt_cable_cutout_w + extra_thickness, wall_thickness, qt_cable_h
    )
    with blender_util.TransformContext(qt_cable_cutout) as ctx:
        ctx.translate(
            -(qt_cable_cutout_w + pcb_w) / 2,
            (wall_thickness / 2) + display_thickness - 0.1,
            0,
        )

    header_cutout = blender_util.cube(18, wall_thickness, 4)
    with blender_util.TransformContext(header_cutout) as ctx:
        ctx.translate(0, (wall_thickness / 2) + 0.8, 2 + (-pcb_h / 2))

    cutin_w = 2.5
    cutin_h = 2.0
    cutin_thickness = display_thickness - 0.1
    cable_cutin = blender_util.cube(cutin_w, cutin_thickness, cutin_h)
    with blender_util.TransformContext(cable_cutin) as ctx:
        ctx.translate(
            (display_w - cutin_w) / 2,
            cutin_thickness / 2,
            (display_h - cutin_h) / 2.0,
        )

    oled_cable_h = display_h - cutin_h
    oled_cable_cutout_w = 2
    oled_cable_cutout = blender_util.cube(
        oled_cable_cutout_w + extra_thickness,
        wall_thickness + extra_thickness,
        oled_cable_h,
    )
    oled_cable_cutout_diff = blender_util.cube(
        10, 2, oled_cable_h + extra_thickness
    )
    with blender_util.TransformContext(oled_cable_cutout_diff) as ctx:
        ctx.translate(0, -1, 0)
        ctx.rotate(15, "Z")
        ctx.translate(-1, 1 + (-(2 + wall_thickness) / 2), 0)
    blender_util.difference(oled_cable_cutout, oled_cable_cutout_diff)
    with blender_util.TransformContext(oled_cable_cutout) as ctx:
        ctx.translate(
            (oled_cable_cutout_w + display_w) / 2,
            (wall_thickness + extra_thickness) / 2,
            -(cutin_h / 2),
        )

    if False:
        stud = (
            standoff_stud(d=2.5)
            .rotate(-90, 0, 0)
            .translate(0, display_thickness - 0.01, 0)
        )
        postive_parts = [
            stud.translate(-14.0, 0, -8.325),
            stud.translate(14.0, 0, -8.325),
            stud.translate(14.0, 0, 8.175),
            stud.translate(-14.0, 0, 8.175),
            cable_cutin,
        ]
        pos = Shape.union(postive_parts)
    else:
        pos = cable_cutin

    neg = display_cutout
    blender_util.union(neg, pcb_cutout)
    blender_util.union(neg, qt_cable_cutout)
    blender_util.union(neg, oled_cable_cutout)
    blender_util.union(neg, header_cutout)

    return neg, pos


def test() -> bpy.types.Object:
    wall = blender_util.range_cube((-25, 25), (0.0, 4.0), (0.0, 40.0))
    neg, pos = oled_holder_parts(4.0)

    with blender_util.TransformContext(neg) as ctx:
        ctx.translate(0, 0, 20)
    with blender_util.TransformContext(pos) as ctx:
        ctx.translate(0, 0, 20)

    blender_util.difference(wall, neg)
    blender_util.union(wall, pos)

    return wall
