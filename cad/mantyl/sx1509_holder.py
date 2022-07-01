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


def extrude_face(
    points: List[Tuple[float, float]], y_front: float, y_back: float
) -> cad.Mesh:
    front = []
    back = []
    mesh = cad.Mesh()
    for (x, z) in points:
        front.append(mesh.add_xyz(x, y_front, z))
        back.append(mesh.add_xyz(x, y_back, z))

    mesh.faces.append(tuple(f.index for f in front))
    mesh.faces.append(tuple(reversed([b.index for b in back])))
    for idx in range(len(front)):
        mesh.add_quad(back[idx - 1], back[idx], front[idx], front[idx - 1])

    return mesh


def right_bracket() -> bpy.types.Object:
    y_face = -6.0
    y_back = -1.0

    points = [
        (12.0, 30.0),
        (21.0, 30.0),
        (21.0, 0.0),
        (21.0, -2.0),
        (20.0, -2.0),
        (16.0, 0.0),
        (16.0, 1.0),
        (18.0, 6.0),
        (18.0, 24.0),
        (12.0, 29.0),
    ]
    mesh = extrude_face(points, y_face, y_back)
    bracket = blender_util.new_mesh_obj("bracket", mesh)

    y_off = (y_face + y_back) * 0.5
    w = 36.2 + 0.4
    h = 26 + 0.4
    d = 1.57 + 0.4
    board_slot = blender_util.cube(w, d, h)
    with blender_util.TransformContext(board_slot) as ctx:
        ctx.translate(0.0, y_off, (h * 0.5) + 2.0)
    blender_util.difference(bracket, board_slot)

    return bracket


def sx1509_holder() -> bpy.types.Object:
    holder = blender_util.range_cube((-21.0, 21.0), (-1.0, 0.0), (22.0, 30.0))

    right = right_bracket()
    left = right_bracket()
    with blender_util.TransformContext(left) as ctx:
        ctx.mirror_x()

    blender_util.union(holder, left)
    blender_util.union(holder, right)
    return holder


def upside_down() -> bpy.types.Object:
    # The holder is easier to print upside down
    holder = sx1509_holder()
    with blender_util.TransformContext(holder) as ctx:
        ctx.rotate(180.0, "Y")
        ctx.translate(0.0, 0.0, 30.0)

    return holder


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
