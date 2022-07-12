#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

import math
from typing import List

from . import blender_util
from . import cad
from .keyboard import Keyboard


def screw_standoff(
    h: float, hole_h: float, outer_d: float, hole_d: float
) -> bpy.types.Object:
    """
    A stand-off designed to fit a 1/4" #6-32 UNC screw.
    """
    fn = 64

    r = outer_d * 0.5
    standoff = blender_util.cylinder(r=r, h=h, fn=fn, name="screw_standoff")
    hole = blender_util.cylinder(r=hole_d * 0.5, h=h, fn=fn)
    blender_util.difference(standoff, hole)
    with blender_util.TransformContext(standoff) as ctx:
        ctx.translate(0.0, 0.0, h * 0.5)

    base_h = h - hole_h
    base = blender_util.cylinder(r=r, h=base_h, fn=fn)
    with blender_util.TransformContext(base) as ctx:
        ctx.translate(0.0, 0.0, base_h * 0.5)
    blender_util.union(standoff, base)

    return standoff


def unc6_32_screw_standoff(
    h: float = 4.5, hole_h=4.2, outer_d: float = 6.0
) -> bpy.types.Object:
    """
    A stand-off designed to fit a 1/4" #6-32 UNC screw.
    """
    # hole_h is less than 1/4" since the screw also has to fit a couple mm
    # through a backplate
    return screw_standoff(h=h, hole_h=hole_h, outer_d=outer_d, hole_d=3.25)


def gen_screw_hole(wall_thickness: float) -> bpy.types.Object:
    """
    Create a hole for a wall, big enough to fit a US #6 screw.
    """
    mesh = cad.Mesh()
    front_y = -1.0
    back_y = wall_thickness + 1.0

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

    return blender_util.new_mesh_obj("screw_hole", mesh)


def add_screw_hole(
    kbd: Keyboard, kbd_obj: bpy.types.Object, x: float, z: float
) -> None:
    screw_hole = gen_screw_hole(kbd.wall_thickness)
    blender_util.apply_to_wall(screw_hole, kbd.fl.out2, kbd.fr.out2, x=x, z=z)
    blender_util.difference(kbd_obj, screw_hole)


def add_screw_holes(kbd: Keyboard, kbd_obj: bpy.types.Object) -> None:
    x_spacing = 45
    x_offset = 0
    add_screw_hole(kbd, kbd_obj, x=x_offset - (x_spacing * 0.5), z=8)
    add_screw_hole(kbd, kbd_obj, x=x_offset + (x_spacing * 0.5), z=8)
    add_screw_hole(kbd, kbd_obj, x=x_offset - (x_spacing * 0.5), z=22)
    add_screw_hole(kbd, kbd_obj, x=x_offset + (x_spacing * 0.5), z=22)

    # An extra screw hole on the thumb section
    if False:
        screw_hole = gen_screw_hole(kbd.wall_thickness)
        blender_util.apply_to_wall(
            screw_hole, kbd.thumb_bl.out2, kbd.thumb_br_connect, x=30, z=10
        )
        blender_util.difference(kbd_obj, screw_hole)
