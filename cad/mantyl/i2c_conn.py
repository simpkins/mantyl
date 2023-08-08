#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

import math
from typing import List

from bpycad import blender_util
from bpycad import cad
from bpycad.cad import MeshPoint
from .keyboard import Keyboard


class I2cCutout:
    wall_thickness = 4.0
    # Make the front and back stick out 1mm past the wall, just to avoid
    # coincident faces when doing the boolean difference with the wall.
    back_y: float = wall_thickness + 1.0
    face_y: float = -1.0

    # If printing the holder face down, h = 4.5 is a good value.
    # However, if printing vertically with support needed to hold up the top
    # of the opening, then this value needs to be a little bit bigger.
    h = 4.75
    d = 4.05
    w = 20.5

    flange_d = 2.25
    flange_offset = 0.90

    nub_y: float = wall_thickness - (flange_d + flange_offset)
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


class CableCap:
    h = 4.50
    w = 20.5

    face_y = 0.0
    flange_d = 2.15
    flange_thickness = 1.0

    # The depth of the back wall of the inner cavity.
    cavity_d = 7.00
    flange_back_d: float = flange_d + flange_thickness
    conn_back_d = 4.0
    bulge_d = 4.0
    back_d = 8.5

    @classmethod
    def gen(cls) -> bpy.types.Object:
        main = cls.gen_main_mesh()

        cable_d = 5.4

        strain_relief = blender_util.cylinder(r=2.3, h=5, r2=3)
        with blender_util.TransformContext(strain_relief) as ctx:
            ctx.rotate(90, "Y")
            ctx.translate((cls.w * 0.5) + 2.8, cable_d, 0)

        cable_hole = blender_util.cylinder(r=1.8, h=10)
        with blender_util.TransformContext(cable_hole) as ctx:
            ctx.rotate(90, "Y")
            ctx.translate((cls.w * 0.5) + 3, cable_d, 0)

        blender_util.union(main, strain_relief)
        blender_util.difference(main, cable_hole)

        if False:
            with blender_util.TransformContext(main) as ctx:
                ctx.translate(0, -cls.back_d, 0)
                ctx.rotate(-90, "X")
        return main

    @classmethod
    def gen_main_mesh(cls) -> bpy.types.Object:
        mesh = cad.Mesh()
        hide_back = False

        core_r = cls.h / 2.0
        outer_r = core_r + 1.0
        half_h = cls.h * 0.5
        half_w = cls.w * 0.5

        flange_r = core_r
        cavity_r = core_r + 0.25

        bulge_r = core_r + 2.0
        back_r = 3.5

        left_face_points: List[MeshPoint] = []
        left_outer_face_points: List[MeshPoint] = []
        left_inner_points: List[MeshPoint] = []
        right_face_points: List[MeshPoint] = []
        right_outer_face_points: List[MeshPoint] = []
        right_inner_points: List[MeshPoint] = []

        left_back_points: List[MeshPoint] = []
        right_back_points: List[MeshPoint] = []

        right_bulge_points: List[MeshPoint] = []
        left_bulge_points: List[MeshPoint] = []

        right_orig = cad.Point(half_w - half_h, cls.face_y, 0.0)
        left_orig = cad.Point(-(half_w - half_h), cls.face_y, 0.0)

        right_back_orig = mesh.add_xyz(half_w - half_h, cls.back_d, 0.0)
        left_back_orig = mesh.add_xyz(-(half_w - half_h), cls.back_d, 0.0)

        right_flange_back_points: List[MeshPoint] = []
        right_conn_back_points: List[MeshPoint] = []
        left_flange_back_points: List[MeshPoint] = []
        left_conn_back_points: List[MeshPoint] = []

        fn = 16
        for n in range(fn + 1):
            angle = (180.0 / fn) * n
            rad = math.radians(angle)

            x = math.sin(rad) * core_r
            z = math.cos(rad) * core_r
            outer_x = math.sin(rad) * outer_r
            outer_z = math.cos(rad) * outer_r
            bulge_x = math.sin(rad) * bulge_r
            bulge_z = math.cos(rad) * bulge_r
            back_x = math.sin(rad) * back_r
            back_z = math.cos(rad) * back_r

            right_face_points.append(
                mesh.add_xyz(right_orig.x + x, cls.face_y, z)
            )
            right_outer_face_points.append(
                mesh.add_xyz(right_orig.x + outer_x, cls.face_y, outer_z)
            )
            right_inner_points.append(
                mesh.add_xyz(right_orig.x + x, cls.flange_d, z)
            )
            right_bulge_points.append(
                mesh.add_xyz(right_orig.x + bulge_x, cls.bulge_d, bulge_z)
            )

            left_face_points.append(
                mesh.add_xyz(left_orig.x - x, cls.face_y, z)
            )
            left_outer_face_points.append(
                mesh.add_xyz(left_orig.x - outer_x, cls.face_y, outer_z)
            )
            left_inner_points.append(
                mesh.add_xyz(left_orig.x - x, cls.flange_d, z)
            )
            left_bulge_points.append(
                mesh.add_xyz(left_orig.x - bulge_x, cls.bulge_d, bulge_z)
            )

            right_back_points.append(
                mesh.add_xyz(right_orig.x + back_x, cls.back_d, back_z)
            )
            left_back_points.append(
                mesh.add_xyz(left_orig.x - back_x, cls.back_d, back_z)
            )

            right_flange_back_points.append(
                mesh.add_xyz(right_orig.x + x, cls.flange_back_d, z)
            )
            right_conn_back_points.append(
                mesh.add_xyz(right_orig.x + x, cls.conn_back_d, z)
            )
            left_flange_back_points.append(
                mesh.add_xyz(left_orig.x - x, cls.flange_back_d, z)
            )
            left_conn_back_points.append(
                mesh.add_xyz(left_orig.x - x, cls.conn_back_d, z)
            )

        flange_tr = mesh.add_xyz(
            right_orig.x + flange_r, cls.flange_d, right_orig.z + flange_r
        )
        flange_br = mesh.add_xyz(
            right_orig.x + flange_r, cls.flange_d, right_orig.z - flange_r
        )
        flange_back_tr = mesh.add_xyz(
            right_orig.x + flange_r, cls.flange_back_d, right_orig.z + flange_r
        )
        flange_back_br = mesh.add_xyz(
            right_orig.x + flange_r, cls.flange_back_d, right_orig.z - flange_r
        )

        flange_tl = mesh.add_xyz(
            left_orig.x - flange_r, cls.flange_d, left_orig.z + flange_r
        )
        flange_bl = mesh.add_xyz(
            left_orig.x - flange_r, cls.flange_d, left_orig.z - flange_r
        )
        flange_back_tl = mesh.add_xyz(
            left_orig.x - flange_r, cls.flange_back_d, left_orig.z + flange_r
        )
        flange_back_bl = mesh.add_xyz(
            left_orig.x - flange_r, cls.flange_back_d, left_orig.z - flange_r
        )

        mesh.add_quad(
            flange_tr,
            right_inner_points[len(right_inner_points) // 2],
            right_flange_back_points[len(right_flange_back_points) // 2],
            flange_back_tr,
        )
        mesh.add_quad(
            right_flange_back_points[len(right_flange_back_points) // 2],
            right_inner_points[len(right_inner_points) // 2],
            flange_br,
            flange_back_br,
        )
        mesh.add_quad(
            flange_tl,
            flange_back_tl,
            left_flange_back_points[len(left_flange_back_points) // 2],
            left_inner_points[len(left_inner_points) // 2],
        )
        mesh.add_quad(
            left_inner_points[len(left_inner_points) // 2],
            left_flange_back_points[len(left_flange_back_points) // 2],
            flange_back_bl,
            flange_bl,
        )

        conn_back_tr = mesh.add_xyz(
            right_orig.x + cavity_r, cls.conn_back_d, left_orig.z + cavity_r
        )
        conn_back_br = mesh.add_xyz(
            right_orig.x + cavity_r, cls.conn_back_d, left_orig.z - cavity_r
        )
        conn_back_tl = mesh.add_xyz(
            left_orig.x - cavity_r, cls.conn_back_d, left_orig.z + cavity_r
        )
        conn_back_bl = mesh.add_xyz(
            left_orig.x - cavity_r, cls.conn_back_d, left_orig.z - cavity_r
        )
        cavity_tr = mesh.add_xyz(
            right_orig.x + cavity_r, cls.cavity_d, left_orig.z + cavity_r
        )
        cavity_br = mesh.add_xyz(
            right_orig.x + cavity_r, cls.cavity_d, left_orig.z - cavity_r
        )
        cavity_tl = mesh.add_xyz(
            left_orig.x - cavity_r, cls.cavity_d, left_orig.z + cavity_r
        )
        cavity_bl = mesh.add_xyz(
            left_orig.x - cavity_r, cls.cavity_d, left_orig.z - cavity_r
        )

        for idx in range(1, len(right_face_points)):
            mesh.add_quad(
                right_face_points[idx - 1],
                right_outer_face_points[idx - 1],
                right_outer_face_points[idx],
                right_face_points[idx],
            )
            mesh.add_quad(
                left_outer_face_points[idx - 1],
                left_face_points[idx - 1],
                left_face_points[idx],
                left_outer_face_points[idx],
            )
            mesh.add_quad(
                right_inner_points[idx],
                right_inner_points[idx - 1],
                right_face_points[idx - 1],
                right_face_points[idx],
            )
            mesh.add_quad(
                left_face_points[idx],
                left_face_points[idx - 1],
                left_inner_points[idx - 1],
                left_inner_points[idx],
            )

            mesh.add_quad(
                right_conn_back_points[idx],
                right_conn_back_points[idx - 1],
                right_flange_back_points[idx - 1],
                right_flange_back_points[idx],
            )
            mesh.add_quad(
                left_conn_back_points[idx - 1],
                left_conn_back_points[idx],
                left_flange_back_points[idx],
                left_flange_back_points[idx - 1],
            )

            mesh.add_quad(
                right_outer_face_points[idx - 1],
                right_bulge_points[idx - 1],
                right_bulge_points[idx],
                right_outer_face_points[idx],
            )
            mesh.add_quad(
                left_bulge_points[idx - 1],
                left_outer_face_points[idx - 1],
                left_outer_face_points[idx],
                left_bulge_points[idx],
            )
            mesh.add_quad(
                right_bulge_points[idx - 1],
                right_back_points[idx - 1],
                right_back_points[idx],
                right_bulge_points[idx],
            )
            mesh.add_quad(
                left_back_points[idx - 1],
                left_bulge_points[idx - 1],
                left_bulge_points[idx],
                left_back_points[idx],
            )

            if idx < (len(right_face_points) / 2):
                mesh.add_tri(
                    right_inner_points[idx],
                    flange_tr,
                    right_inner_points[idx - 1],
                )
                mesh.add_tri(
                    left_inner_points[idx - 1],
                    flange_tl,
                    left_inner_points[idx],
                )

                mesh.add_tri(
                    right_flange_back_points[idx],
                    right_flange_back_points[idx - 1],
                    flange_back_tr,
                )
                mesh.add_tri(
                    right_conn_back_points[idx - 1],
                    right_conn_back_points[idx],
                    conn_back_tr,
                )

                mesh.add_tri(
                    left_flange_back_points[idx - 1],
                    left_flange_back_points[idx],
                    flange_back_tl,
                )
                mesh.add_tri(
                    left_conn_back_points[idx],
                    left_conn_back_points[idx - 1],
                    conn_back_tl,
                )
            else:
                mesh.add_tri(
                    right_inner_points[idx],
                    flange_br,
                    right_inner_points[idx - 1],
                )
                mesh.add_tri(
                    left_inner_points[idx - 1],
                    flange_bl,
                    left_inner_points[idx],
                )

                mesh.add_tri(
                    right_flange_back_points[idx],
                    right_flange_back_points[idx - 1],
                    flange_back_br,
                )
                mesh.add_tri(
                    right_conn_back_points[idx - 1],
                    right_conn_back_points[idx],
                    conn_back_br,
                )

                mesh.add_tri(
                    left_flange_back_points[idx - 1],
                    left_flange_back_points[idx],
                    flange_back_bl,
                )
                mesh.add_tri(
                    left_conn_back_points[idx],
                    left_conn_back_points[idx - 1],
                    conn_back_bl,
                )

            if not hide_back:
                mesh.add_tri(
                    right_back_points[idx - 1],
                    right_back_orig,
                    right_back_points[idx],
                )
                mesh.add_tri(
                    left_back_points[idx],
                    left_back_orig,
                    left_back_points[idx - 1],
                )

        if cavity_r > core_r:
            mesh.add_tri(
                conn_back_tl,
                conn_back_bl,
                left_conn_back_points[len(right_face_points) // 2],
            )
            mesh.add_tri(
                conn_back_tr,
                right_conn_back_points[len(right_face_points) // 2],
                conn_back_br,
            )
            mesh.add_quad(
                conn_back_tr,
                conn_back_tl,
                left_conn_back_points[0],
                right_conn_back_points[0],
            )
            mesh.add_quad(
                right_conn_back_points[-1],
                left_conn_back_points[-1],
                conn_back_bl,
                conn_back_br,
            )

        mesh.add_quad(
            flange_back_tr,
            right_flange_back_points[0],
            right_inner_points[0],
            flange_tr,
        )
        mesh.add_quad(
            right_flange_back_points[0],
            left_flange_back_points[0],
            left_inner_points[0],
            right_inner_points[0],
        )
        mesh.add_quad(
            left_flange_back_points[0],
            flange_back_tl,
            flange_tl,
            left_inner_points[0],
        )
        mesh.add_quad(
            flange_br,
            right_inner_points[-1],
            right_flange_back_points[-1],
            flange_back_br,
        )
        mesh.add_quad(
            right_inner_points[-1],
            left_inner_points[-1],
            left_flange_back_points[-1],
            right_flange_back_points[-1],
        )
        mesh.add_quad(
            left_inner_points[-1],
            flange_bl,
            flange_back_bl,
            left_flange_back_points[-1],
        )

        mesh.add_quad(
            right_conn_back_points[0],
            left_conn_back_points[0],
            left_flange_back_points[0],
            right_flange_back_points[0],
        )
        mesh.add_quad(
            right_flange_back_points[-1],
            left_flange_back_points[-1],
            left_conn_back_points[-1],
            right_conn_back_points[-1],
        )

        mesh.add_quad(cavity_tr, cavity_tl, conn_back_tl, conn_back_tr)
        mesh.add_quad(cavity_br, cavity_tr, conn_back_tr, conn_back_br)
        mesh.add_quad(conn_back_bl, conn_back_tl, cavity_tl, cavity_bl)
        mesh.add_quad(conn_back_br, conn_back_bl, cavity_bl, cavity_br)

        if not hide_back:
            mesh.add_quad(cavity_tl, cavity_tr, cavity_br, cavity_bl)
            mesh.add_quad(
                right_back_points[0],
                left_back_points[0],
                left_back_orig,
                right_back_orig,
            )
            mesh.add_quad(
                right_back_orig,
                left_back_orig,
                left_back_points[-1],
                right_back_points[-1],
            )

        mesh.add_quad(
            left_face_points[0],
            left_outer_face_points[0],
            right_outer_face_points[0],
            right_face_points[0],
        )
        mesh.add_quad(
            left_outer_face_points[-1],
            left_face_points[-1],
            right_face_points[-1],
            right_outer_face_points[-1],
        )
        mesh.add_quad(
            left_face_points[-1],
            left_inner_points[-1],
            right_inner_points[-1],
            right_face_points[-1],
        )
        mesh.add_quad(
            left_inner_points[0],
            left_face_points[0],
            right_face_points[0],
            right_inner_points[0],
        )
        mesh.add_quad(
            left_outer_face_points[0],
            left_bulge_points[0],
            right_bulge_points[0],
            right_outer_face_points[0],
        )
        mesh.add_quad(
            left_bulge_points[-1],
            left_outer_face_points[-1],
            right_outer_face_points[-1],
            right_bulge_points[-1],
        )

        mesh.add_quad(
            right_bulge_points[0],
            left_bulge_points[0],
            left_back_points[0],
            right_back_points[0],
        )
        mesh.add_quad(
            left_bulge_points[-1],
            right_bulge_points[-1],
            right_back_points[-1],
            left_back_points[-1],
        )

        return blender_util.new_mesh_obj("i2c_cutout", mesh)


def add_i2c_connector(kbd: Keyboard, kbd_obj: bpy.types.Object) -> None:
    i2c_cutout = I2cCutout.gen()

    x_off = 0.0
    z_off = 5 + I2cCutout.h * 0.5
    blender_util.apply_to_wall(
        i2c_cutout,
        kbd.thumb_tr_connect.point,
        kbd.thumb_tl.out2,
        x=x_off,
        z=z_off,
    )

    blender_util.difference(kbd_obj, i2c_cutout)


def test() -> bpy.types.Object:
    wall = blender_util.range_cube((-15, 15), (0, 4), (0, 10))
    i2c_cutout = I2cCutout.gen()
    blender_util.apply_to_wall(
        i2c_cutout, cad.Point(-10, 0, 0), cad.Point(10, 0, 0), x=0.0, z=5.0
    )
    blender_util.difference(wall, i2c_cutout)
    return wall


def cable_cap_test() -> bpy.types.Object:
    return CableCap.gen()


def cable_cap() -> bpy.types.Object:
    cap = CableCap.gen()
    with blender_util.TransformContext(cap) as ctx:
        ctx.translate(0, -CableCap.back_d, 0)
        ctx.rotate(-90, "X")

    return cap
