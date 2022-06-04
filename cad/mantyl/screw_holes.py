#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

import math
from typing import List

import mantyl.cad as cad
from mantyl.blender_util import apply_to_wall, difference, new_mesh_obj
from mantyl.keyboard import Keyboard


def gen_screw_hole(kbd: Keyboard) -> bpy.types.Object:
    # Big enough to fit a US #6 screw
    mesh = cad.Mesh()
    front_y = -1.0
    back_y = kbd.wall_thickness + 1.0

    front_center = mesh.add_xyz(0.0, front_y, 0.0)
    back_center = mesh.add_xyz(0.0, back_y, 0.0)
    front_points: List[MeshPoint] = []
    back_points: List[MeshPoint] = []

    r = 1.9
    fn = 24
    for n in range(fn):
        angle = (360.0 / fn) * n
        rad = math.radians(angle)

        circle_x = math.sin(rad) * r
        circle_z = math.cos(rad) * r

        front_points.append(mesh.add_xyz(circle_x, front_y, circle_z))
        back_points.append(mesh.add_xyz(circle_x, back_y, circle_z))

    for idx, fp in enumerate(front_points):
        # Note: this intentionally wraps around to -1 when idx == 0
        prev_f = front_points[idx - 1]
        prev_b = back_points[idx - 1]

        mesh.add_tri(front_center, prev_f, fp)
        mesh.add_tri(back_center, back_points[idx], prev_b)
        mesh.add_quad(prev_f, prev_b, back_points[idx], fp)

    return new_mesh_obj("screw_hole", mesh)


def add_screw_hole(
    kbd: Keyboard, kbd_obj: bpy.types.Object, x: float, z: float
) -> None:
    screw_hole = gen_screw_hole(kbd)
    apply_to_wall(screw_hole, kbd.fl.out2, kbd.fr.out2, x=x, z=z)
    difference(kbd_obj, screw_hole)


def add_screw_holes(kbd: Keyboard, kbd_obj: bpy.types.Object) -> None:
    x_spacing = 40
    add_screw_hole(kbd, kbd_obj, x=-x_spacing * 0.5, z=10)
    add_screw_hole(kbd, kbd_obj, x=x_spacing * 0.5, z=10)
    add_screw_hole(kbd, kbd_obj, x=-x_spacing * 0.5, z=25)
    add_screw_hole(kbd, kbd_obj, x=x_spacing * 0.5, z=25)

    # An extra screw hole on the thumb section
    if False:
        screw_hole = gen_screw_hole(kbd)
        apply_to_wall(
            screw_hole, kbd.thumb_bl.out2, kbd.thumb_br_connect, x=30, z=10
        )
        difference(kbd_obj, screw_hole)
