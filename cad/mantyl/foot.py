#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

import math
from typing import List, Tuple

import mantyl.cad as cad
from mantyl.blender_util import difference, new_mesh_obj, union
from mantyl.keyboard import Keyboard


class Foot:
    inner_r = 6.5
    outer_r = inner_r + 2.0
    recess_h = 2.75
    base_h = 3.0
    top_h = 15.0

    @classmethod
    def foot_mesh_pos(cls, phase: float) -> cad.Mesh:
        mesh = cad.Mesh()
        l_orig = mesh.add_point(cad.Point(0.0, 0.0, 0.0))
        top = mesh.add_point(cad.Point(-cls.outer_r, 0.0, cls.top_h))

        lower_points: List[cad.MeshPoint] = []
        upper_points: List[cad.MeshPoint] = []

        fn = 24
        for n in range(fn):
            angle = ((360.0 / fn) * n) + phase
            rad = math.radians(angle)

            x = math.sin(rad) * cls.outer_r
            y = math.cos(rad) * cls.outer_r

            pl = mesh.add_point(cad.Point(x, y, 0.0))
            pu = mesh.add_point(cad.Point(x, y, cls.base_h))
            lower_points.append(pl)
            upper_points.append(pu)

        for idx in range(len(lower_points)):
            if idx + 1 == len(lower_points):
                l_next = lower_points[0]
                u_next = upper_points[0]
            else:
                l_next = lower_points[idx + 1]
                u_next = upper_points[idx + 1]

            mesh.add_tri(l_orig, l_next, lower_points[idx])
            mesh.add_tri(top, upper_points[idx], u_next)
            mesh.add_quad(u_next, upper_points[idx], lower_points[idx], l_next)

        return mesh

    @classmethod
    def foot_mesh_neg(cls, phase: float) -> cad.Mesh:
        bottom_h = -1.0

        mesh = cad.Mesh()
        l_orig = mesh.add_point(cad.Point(0.0, 0.0, bottom_h))
        u_orig = mesh.add_point(cad.Point(0.0, 0.0, cls.recess_h))

        lower_points: List[cad.MeshPoint] = []
        upper_points: List[cad.MeshPoint] = []

        fn = 24
        for n in range(fn):
            angle = ((360.0 / fn) * n) + phase
            rad = math.radians(angle)

            x = math.sin(rad) * cls.inner_r
            y = math.cos(rad) * cls.inner_r

            pl = mesh.add_point(cad.Point(x, y, bottom_h))
            pu = mesh.add_point(cad.Point(x, y, cls.recess_h))
            lower_points.append(pl)
            upper_points.append(pu)

        for idx in range(len(lower_points)):
            if idx + 1 == len(lower_points):
                l_next = lower_points[0]
                u_next = upper_points[0]
            else:
                l_next = lower_points[idx + 1]
                u_next = upper_points[idx + 1]

            mesh.add_tri(l_orig, l_next, lower_points[idx])
            mesh.add_tri(u_orig, upper_points[idx], u_next)
            mesh.add_quad(u_next, upper_points[idx], lower_points[idx], l_next)

        return mesh


def foot_meshes(
    x: float, y: float, angle: float, phase: float
) -> Tuple[cad.Mesh, cad.Mesh]:
    neg_mesh = Foot.foot_mesh_neg(phase)
    pos_mesh = Foot.foot_mesh_pos(phase)
    pos_mesh.translate(Foot.outer_r, 0.0, 0.0)
    neg_mesh.translate(Foot.outer_r, 0.0, 0.0)
    pos_mesh.rotate(0.0, 0.0, angle)
    neg_mesh.rotate(0.0, 0.0, angle)
    pos_mesh.translate(x, y, 0.0)
    neg_mesh.translate(x, y, 0.0)

    return pos_mesh, neg_mesh


def gen_foot(
    name: str, x: float, y: float, angle: float, phase: float
) -> Tuple[bpy.types.Object, bpy.types.Object]:
    pos_mesh, neg_mesh = foot_meshes(x, y, angle, phase)

    neg = new_mesh_obj(f"{name}_neg", neg_mesh)
    foot = new_mesh_obj(name, pos_mesh)
    return foot, neg


def add_foot(
    kbd_obj: bpy.types.Object,
    x: float,
    y: float,
    angle: float,
    phase: float = 0.0,
    dbg: bool = False,
) -> Tuple[bpy.types.Object, bpy.types.Object]:
    """
    Add a foot to the keyboard object.

    (x, y) control the location.  The top of the foot will be at this location.
    angle controls the direction the foot is pointing.

    The phase parameter allows slightly rotating the angles at which the
    cylindrical vertices of the foot are placed.  This doesn't change the
    general shape of the foot or the direction it is pointing, but simply
    allows rotating the location of the vertices slightly.  This helps tweak
    the vertices to prevent blender from generating intersecting faces when
    performing the boolean union and difference, which can happen if the
    intersection points lie close to an existing vertex.  I set this parameter
    experimentally for each foot: Blender's 3D-Print tool can highlight
    intersecting edges.  When any were present on a foot, I tweaked its phase
    until blender no longer generates intersecting geometry on that foot.
    (Disabling the bevel on the interior corners would also have probably
    helped eliminate this bad geometry, but using this phase parameter allows
    keeping the bevel.)
    """
    pos, neg = gen_foot("foot", x, y, angle, phase)
    union(kbd_obj, pos)
    difference(kbd_obj, neg, apply_mod=not dbg)


def _get_foot_angle(x: float, y: float) -> float:
    # if x and y are both positive
    if x == 0.0:
        if y > 0.0:
            return 90
        return -90

    if x > 0.0:
        return math.degrees(math.atan(y / x))
    else:
        return 180.0 + math.degrees(math.atan(y / x))


def add_feet(kbd: Keyboard, kbd_obj: bpy.types.Object) -> None:
    # When placing the foot angled 45 degrees in a right angle corner, we want
    # to add this amount to the x and y directions so that it is tangent to the
    # walls
    off_45 = math.sqrt(
        ((math.sqrt((Foot.outer_r ** 2) * 2) - Foot.outer_r) ** 2) / 2
    )

    # Back right foot
    add_foot(
        kbd_obj,
        kbd.br.out3.x - off_45 - 0.3,
        kbd.br.out3.y - off_45 - 0.3,
        -135.0,
        1.5,
    )

    # Back left foot
    add_foot(
        kbd_obj, kbd.bl.out3.x + 0.3, kbd.bl.out3.y - off_45 - 0.3, -45.0, 5.0
    )

    # Front right foot
    add_foot(
        kbd_obj,
        kbd.fr.out3.x - off_45 - 0.2,
        kbd.fr.out3.y + off_45 + 0.2,
        135.0,
        0.0,
    )

    # Thumb bottom left foot
    # First compute the rotation angle
    dir1 = (kbd.thumb_tl.out2.point - kbd.thumb_bl.out2.point).unit()
    dir2 = (kbd.thumb_br.out2.point - kbd.thumb_bl.out2.point).unit()
    mid_dir = dir1 + dir2
    angle = _get_foot_angle(mid_dir.x, mid_dir.y)
    f = 3.3
    add_foot(
        kbd_obj,
        kbd.thumb_bl.out2.x + (mid_dir.x * f),
        kbd.thumb_bl.out2.y + (mid_dir.y * f),
        angle,
        7.0,
    )

    # Thumb top left foot
    # First compute the rotation angle
    dir1 = (kbd.thumb_tr.out2.point - kbd.thumb_tl.out2.point).unit()
    dir2 = (kbd.thumb_bl.out2.point - kbd.thumb_tl.out2.point).unit()
    mid_dir = dir1 + dir2
    angle = _get_foot_angle(mid_dir.x, mid_dir.y)
    f = 2.4
    add_foot(
        kbd_obj,
        kbd.thumb_tl.out2.x + (mid_dir.x * f),
        kbd.thumb_tl.out2.y + (mid_dir.y * f),
        angle,
    )
