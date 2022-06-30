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


class I2cCutout:
    wall_thickness = 4.0
    # Make the front and back stick out 1mm past the wall, just to avoid
    # coincident faces when doing the boolean difference with the wall.
    back_y = wall_thickness + 1.0
    face_y = -1.0

    # If printing the holder face down, h = 4.5 is a good value.
    # However, if printing vertically with support needed to hold up the top
    # of the opening, then this value needs to be a little bit bigger.
    h = 4.75
    d = 4.05
    w = 20.5

    flange_d = 2.25
    flange_offset = 0.90

    nub_y = wall_thickness - (flange_d + flange_offset)
    nub_z = 0.75
    nub_x = 0.55

    @classmethod
    def main(cls) -> bpy.types.Object:
        """
        A cutout for the 5-pin magnetic connector I am using for the I2C
        connection: https://www.adafruit.com/product/5413
        """
        mesh = cad.Mesh()

        core_r = cls.h / 2.0
        half_h = cls.h * 0.5
        half_w = cls.w * 0.5
        left_face_points: List[MeshPoint] = []
        left_inner_points: List[MeshPoint] = []
        right_face_points: List[MeshPoint] = []
        right_inner_points: List[MeshPoint] = []

        right_orig = mesh.add_xyz(half_w - half_h, cls.face_y, 0.0)
        left_orig = mesh.add_xyz(-(half_w - half_h), cls.face_y, 0.0)

        inner_tl = mesh.add_xyz(-half_w, cls.flange_d, half_h)
        inner_tr = mesh.add_xyz(half_w, cls.flange_d, half_h)
        back_tl = mesh.add_xyz(-half_w, cls.back_y, half_h)
        back_tr = mesh.add_xyz(half_w, cls.back_y, half_h)

        inner_bl = mesh.add_xyz(-half_w, cls.flange_d, -half_h)
        inner_br = mesh.add_xyz(half_w, cls.flange_d, -half_h)
        back_bl = mesh.add_xyz(-half_w, cls.back_y, -half_h)
        back_br = mesh.add_xyz(half_w, cls.back_y, -half_h)

        back_tlo = mesh.add_xyz(left_orig.x, cls.back_y, half_h)
        back_tro = mesh.add_xyz(right_orig.x, cls.back_y, half_h)
        back_blo = mesh.add_xyz(left_orig.x, cls.back_y, -half_h)
        back_bro = mesh.add_xyz(right_orig.x, cls.back_y, -half_h)

        fn = 16
        for n in range(fn + 1):
            angle = (180.0 / fn) * n
            rad = math.radians(angle)

            x = math.sin(rad) * core_r
            z = math.cos(rad) * core_r
            right_face_points.append(
                mesh.add_xyz(right_orig.x + x, cls.face_y, z)
            )
            right_inner_points.append(
                mesh.add_xyz(right_orig.x + x, cls.flange_d, z)
            )
            left_face_points.append(
                mesh.add_xyz(left_orig.x - x, cls.face_y, z)
            )
            left_inner_points.append(
                mesh.add_xyz(left_orig.x - x, cls.flange_d, z)
            )

        for idx in range(1, len(right_face_points)):
            prev = idx - 1
            mesh.add_quad(
                right_inner_points[prev],
                right_inner_points[idx],
                right_face_points[idx],
                right_face_points[prev],
            )
            mesh.add_tri(
                right_orig, right_face_points[prev], right_face_points[idx]
            )
            mesh.add_quad(
                left_face_points[prev],
                left_face_points[idx],
                left_inner_points[idx],
                left_inner_points[prev],
            )
            mesh.add_tri(
                left_orig, left_face_points[idx], left_face_points[prev]
            )

            if idx < (len(right_face_points) / 2):
                left_corner = inner_tl
                right_corner = inner_tr
            else:
                left_corner = inner_bl
                right_corner = inner_br
            mesh.add_tri(
                left_corner, left_inner_points[prev], left_inner_points[idx]
            )
            mesh.add_tri(
                right_corner, right_inner_points[idx], right_inner_points[prev]
            )

        # Front face
        mesh.add_quad(
            left_face_points[0], right_face_points[0], right_orig, left_orig
        )
        mesh.add_quad(
            left_orig, right_orig, right_face_points[-1], left_face_points[-1]
        )
        # Cylinder cutout top
        mesh.add_quad(
            left_inner_points[0],
            right_inner_points[0],
            right_face_points[0],
            left_face_points[0],
        )
        # Cylinder cutout bottom
        mesh.add_quad(
            left_face_points[-1],
            right_face_points[-1],
            right_inner_points[-1],
            left_inner_points[-1],
        )

        # Back outer wall
        left_inner_mid = left_inner_points[len(left_inner_points) // 2]
        mesh.add_tri(back_tl, inner_tl, left_inner_mid)
        mesh.add_tri(back_bl, left_inner_mid, inner_bl)
        mesh.add_tri(back_tl, left_inner_mid, back_bl)

        right_inner_mid = right_inner_points[len(right_inner_points) // 2]
        mesh.add_tri(back_tr, right_inner_mid, inner_tr)
        mesh.add_tri(back_br, inner_br, right_inner_mid)
        mesh.add_tri(back_tr, back_br, right_inner_mid)

        mesh.add_quad(back_tl, back_tlo, left_inner_points[0], inner_tl)
        mesh.add_quad(
            back_tlo, back_tro, right_inner_points[0], left_inner_points[0]
        )
        mesh.add_quad(back_tro, back_tr, inner_tr, right_inner_points[0])

        mesh.add_quad(inner_bl, left_inner_points[-1], back_blo, back_bl)
        mesh.add_quad(
            left_inner_points[-1], right_inner_points[-1], back_bro, back_blo
        )
        mesh.add_quad(right_inner_points[-1], inner_br, back_br, back_bro)

        # Back face wall
        mesh.add_quad(back_tr, back_tro, back_bro, back_br)
        mesh.add_quad(back_tro, back_tlo, back_blo, back_bro)
        mesh.add_quad(back_tlo, back_tl, back_bl, back_blo)

        return blender_util.new_mesh_obj("i2c_cutout", mesh)

    @classmethod
    def nub(
        cls, x: float, y: float, z: float, mirror_x: bool = False
    ) -> bpy.types.Object:
        t = 0.01  # extra tolerance to avoid coincident faces

        nub_mesh = cad.Mesh()
        b0 = nub_mesh.add_xyz(t, 0.0, -t)
        b1 = nub_mesh.add_xyz(-cls.nub_x, 0.0, -t)
        b2 = nub_mesh.add_xyz(t, cls.nub_y, -t)

        t0 = nub_mesh.add_xyz(t, 0.0, cls.nub_z + t)
        t1 = nub_mesh.add_xyz(-cls.nub_x, 0.0, cls.nub_z + t)
        t2 = nub_mesh.add_xyz(t, cls.nub_y, cls.nub_z + t)

        nub_mesh.add_tri(b0, b2, b1)
        nub_mesh.add_tri(t0, t1, t2)
        nub_mesh.add_quad(t1, b1, b2, t2)
        nub_mesh.add_quad(t2, b2, b0, t0)
        nub_mesh.add_quad(t0, b0, b1, t1)

        if mirror_x:
            nub_mesh.mirror_x()

        nub_mesh.translate(x, y, z)
        return blender_util.new_mesh_obj("i2c_cutout_nub", nub_mesh)

    @classmethod
    def gen(cls) -> bpy.types.Object:
        main = cls.main()

        nub_tr = cls.nub(
            cls.w * 0.5,
            cls.flange_d + cls.flange_offset,
            cls.h * 0.5 - cls.nub_z,
        )
        blender_util.difference(main, nub_tr)

        nub_br = cls.nub(
            cls.w * 0.5, cls.flange_d + cls.flange_offset, cls.h * -0.5
        )
        blender_util.difference(main, nub_br)

        nub_tl = cls.nub(
            -cls.w * 0.5,
            cls.flange_d + cls.flange_offset,
            cls.h * 0.5 - cls.nub_z,
            mirror_x=True,
        )
        blender_util.difference(main, nub_tl)

        nub_bl = cls.nub(
            -cls.w * 0.5,
            cls.flange_d + cls.flange_offset,
            cls.h * -0.5,
            mirror_x=True,
        )
        blender_util.difference(main, nub_bl)
        return main


def add_i2c_connector(kbd: Keyboard, kbd_obj: bpy.types.Object) -> None:
    i2c_cutout = I2cCutout.gen()

    x_off = 0.0
    z_off = 5 + I2cCutout.h * 0.5
    blender_util.apply_to_wall(
        i2c_cutout, kbd.thumb_tr_connect, kbd.thumb_tl.out2, x=x_off, z=z_off
    )

    blender_util.difference(kbd_obj, i2c_cutout)


def test() -> None:
    wall = blender_util.range_cube((-15, 15), (0, 4), (0, 10))
    i2c_cutout = I2cCutout.gen()
    blender_util.apply_to_wall(
        i2c_cutout, cad.Point(-10, 0, 0), cad.Point(10, 0, 0), x=0.0, z=5.0
    )
    blender_util.difference(wall, i2c_cutout)
