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

    with blender_util.TransformContext(obj) as ctx:
        ctx.translate(0.0, (d * -0.5) + y_off, (h * 0.5) + 2.0)

    return obj


def left_bracket() -> bpy.types.Object:
    y_face = -5.0

    left = blender_util.range_cube((-12, -21), (1.0, y_face), (0.0, 30.0))
    wall_gap = blender_util.range_cube((-11, -22), (2.0, -1.0), (-1.0, 24.0))
    blender_util.difference(left, wall_gap)

    y_off = -2.0 + 0.2
    w = 36.2 + 0.4
    h = 26 + 0.4
    d = 1.57 + 0.4
    board_slot = blender_util.cube(w, d, h)
    with blender_util.TransformContext(board_slot) as ctx:
        ctx.translate(0.0, (d * -0.5) + y_off, (h * 0.5) + 2.0)
    blender_util.difference(left, board_slot)

    cutout = cad.Mesh()
    points = [
              (-18.0, 24.0),
              (-12.0, 29.0),
              (-12.0, -.0),
              (-15.0, -1.0),
              (-15.0, 1.0),
              (-18.0, 6.0),
              ]
    front = []
    back = []
    for (x, z) in points:
        front.append(cutout.add_xyz(x, y_face - 1.0, z))
        back.append(cutout.add_xyz(x, 2.0, z))

    cutout.faces.append(tuple(f.index for f in front))
    cutout.faces.append(tuple(reversed([b.index for b in back])))
    for idx in range(len(front)):
        cutout.add_quad(back[idx - 1], back[idx], front[idx], front[idx - 1])

    cutout_obj = blender_util.new_mesh_obj("cutout", cutout)
    blender_util.difference(left, cutout_obj)
    return left


def sx1509_holder() -> bpy.types.Object:
    left = left_bracket()
    right = left_bracket()
    with blender_util.TransformContext(right) as ctx:
        ctx.mirror_x()

    blender_util.union(left, right)
    return left


def test(show_breakout: bool = False) -> bpy.types.Object:
    if show_breakout:
        breakout = sx1509_breakout()
        with blender_util.TransformContext(breakout) as ctx:
            ctx.translate(0.0, 0.0, 3.0)

    wall = blender_util.range_cube((-25, 25), (0, 4), (0, 38))
    holder = sx1509_holder()
    with blender_util.TransformContext(holder) as ctx:
        ctx.translate(0.0, 0.0, 3.0)

    blender_util.union(wall, holder)

    return wall
