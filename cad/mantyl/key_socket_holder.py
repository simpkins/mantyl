#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

import enum
import math
from typing import Callable, List, Tuple

from . import blender_util, cad


def blender_cube(
    x: float, y: float, z: float, name: str = "cube"
) -> bpy.types.Object:
    mesh = cad.cube(x, y, z)
    return blender_util.new_mesh_obj(name, mesh)


def blender_range_cube(
    x_range: Tuple[float, float],
    y_range: Tuple[float, float],
    z_range: Tuple[float, float],
    name: str = "cube",
) -> bpy.types.Object:
    mesh = cad.range_cube(x_range, y_range, z_range)
    return blender_util.new_mesh_obj(name, mesh)


def blender_cylinder(
    r: float,
    h: float,
    fn: int = 24,
    rotation: float = 360.0,
    name: str = "cylinder",
) -> bpy.types.Object:
    mesh = cad.cylinder(r, h, fn=fn, rotation=rotation)
    return blender_util.new_mesh_obj(name, mesh)


class SocketParams:
    thickness = 1.0
    socket_h = 2.0

    full_size = 17.4
    x_left = -full_size * 0.5
    x_right = full_size * 0.5
    x_mid_left = -5.3
    x_mid_right = 6.2
    y_top = full_size * 0.5
    y_bottom = -full_size * 0.5
    z_top = 0.0
    z_bottom = -thickness

    z_clip_top = -thickness
    z_clip_bottom = -thickness - socket_h

    lip_bottom_h = socket_h + 0.05
    lip_tip_bottom_h = socket_h + 0.134
    lip_tip_top_h = lip_tip_bottom_h + 0.1
    lip_top_h = 2.55
    lip_bottom_z = -thickness - socket_h - 0.55

    diode_x = 8.0
    diode_y = -6.55

    diode_w = 2.1
    diode_h = 3.9

    def assign_params_to(self, obj) -> None:
        for name in dir(SocketParams):
            if name.startswith("__"):
                continue
            setattr(obj, name, getattr(self, name))


class TopClip:
    arc_x = 0.4
    arc_r = 1.8
    edge_y = -2.8

    mid0_x = arc_x - 0.2

    def __init__(self, mesh: cad.Mesh) -> None:
        self.mesh = mesh
        self.b_arc_points: List[cad.MeshPoint] = []
        self.t_arc_points: List[cad.MeshPoint] = []

        SocketParams().assign_params_to(self)
        self.top_z = self.z_clip_top
        self.bottom_z = self.z_clip_bottom

    def gen(self) -> None:
        self.gen_arc()
        self.gen_block()
        self.gen_lip()

    def gen_arc(self) -> None:
        self.b_center = self.mesh.add_xyz(
            self.arc_x, self.edge_y + self.arc_r, self.bottom_z
        )
        self.t_center = self.mesh.add_xyz(
            self.arc_x, self.edge_y + self.arc_r, self.top_z
        )

        fn = 24
        for n in range(fn + 1):
            angle = (math.radians(90) / fn) * n
            angle_x = math.sin(angle) * self.arc_r
            angle_y = math.cos(angle) * -self.arc_r

            self.b_arc_points.append(
                self.mesh.add_xyz(
                    self.b_center.x + angle_x,
                    self.b_center.y + angle_y,
                    self.bottom_z,
                )
            )
            self.t_arc_points.append(
                self.mesh.add_xyz(
                    self.b_center.x + angle_x,
                    self.b_center.y + angle_y,
                    self.top_z,
                )
            )

        for n in range(1, len(self.b_arc_points)):
            # bottom triangle
            self.mesh.add_tri(
                self.b_center, self.b_arc_points[n - 1], self.b_arc_points[n]
            )
            # vertical face
            self.mesh.add_quad(
                self.b_arc_points[n - 1],
                self.t_arc_points[n - 1],
                self.t_arc_points[n],
                self.b_arc_points[n],
            )
            # top triangle
            self.mesh.add_tri(
                self.t_center, self.t_arc_points[n], self.t_arc_points[n - 1]
            )

    def gen_block(self) -> None:
        self.l_tl = self.mesh.add_xyz(self.x_mid_left, 0.0, self.top_z)
        self.l_tr = self.mesh.add_xyz(self.x_mid_left, self.edge_y, self.top_z)
        self.l_mr = self.mesh.add_xyz(
            self.x_mid_left, self.edge_y, self.bottom_z
        )
        self.l_ml = self.mesh.add_xyz(self.x_mid_left, 0, self.bottom_z)

        self.m0_tl = self.mesh.add_xyz(self.mid0_x, 0.0, self.top_z)
        self.m0_tr = self.mesh.add_xyz(self.mid0_x, self.edge_y, self.top_z)
        self.m0_mr = self.mesh.add_xyz(self.mid0_x, self.edge_y, self.bottom_z)
        self.m0_ml = self.mesh.add_xyz(self.mid0_x, 0, self.bottom_z)

        # left face
        self.mesh.add_quad(self.l_tl, self.l_tr, self.l_mr, self.l_ml)
        # "top" face (on Y axis)
        self.mesh.add_quad(self.m0_tl, self.l_tl, self.l_ml, self.m0_ml)
        # "bottom" face (on Y axis)
        self.mesh.add_quad(self.l_tr, self.m0_tr, self.m0_mr, self.l_mr)
        self.mesh.add_quad(
            self.m0_tr, self.t_arc_points[0], self.b_arc_points[0], self.m0_mr
        )

        right_y = self.edge_y + self.arc_r
        self.r_tl = self.mesh.add_xyz(self.x_mid_right, 0.0, self.top_z)
        self.r_tr = self.mesh.add_xyz(self.x_mid_right, right_y, self.top_z)
        self.r_mr = self.mesh.add_xyz(self.x_mid_right, right_y, self.bottom_z)
        self.r_ml = self.mesh.add_xyz(self.x_mid_right, 0, self.bottom_z)

        # right face
        self.mesh.add_quad(self.r_tr, self.r_tl, self.r_ml, self.r_mr)
        # "bottom" face (on Y axis)
        self.mesh.add_quad(
            self.t_arc_points[-1], self.r_tr, self.r_mr, self.b_arc_points[-1]
        )

        # "top" face (on Y axis)
        self.m1_tl = self.mesh.add_xyz(self.arc_x, 0.0, self.top_z)
        self.m1_ml = self.mesh.add_xyz(self.arc_x, 0, self.bottom_z)
        self.m2_tl = self.mesh.add_xyz(
            self.arc_x + self.arc_r, 0.0, self.top_z
        )
        self.m2_ml = self.mesh.add_xyz(
            self.arc_x + self.arc_r, 0, self.bottom_z
        )
        self.mesh.add_quad(self.r_tl, self.m2_tl, self.m2_ml, self.r_ml)
        self.mesh.add_quad(self.m2_tl, self.m1_tl, self.m1_ml, self.m2_ml)
        self.mesh.add_quad(self.m1_tl, self.m0_tl, self.m0_ml, self.m1_ml)

        # bottom face (on Z axis)
        self.mesh.add_quad(
            self.r_ml, self.m2_ml, self.b_arc_points[-1], self.r_mr
        )
        self.mesh.add_quad(
            self.m2_ml, self.m1_ml, self.b_center, self.b_arc_points[-1]
        )
        self.mesh.add_tri(self.m1_ml, self.m0_ml, self.b_center)
        self.mesh.add_tri(self.b_center, self.m0_ml, self.m0_mr)
        self.mesh.add_tri(self.b_center, self.m0_mr, self.b_arc_points[0])

        # top face (on Z axis)
        self.mesh.add_quad(
            self.r_tr, self.t_arc_points[-1], self.m2_tl, self.r_tl
        )
        self.mesh.add_quad(
            self.t_arc_points[-1], self.t_center, self.m1_tl, self.m2_tl
        )
        self.mesh.add_tri(self.t_center, self.t_arc_points[0], self.m0_tr)
        self.mesh.add_tri(self.t_center, self.m0_tr, self.m0_tl)
        self.mesh.add_tri(self.t_center, self.m0_tl, self.m1_tl)
        self.mesh.add_quad(self.m0_tr, self.l_tr, self.l_tl, self.m0_tl)

    def gen_lip(self) -> None:
        lip_protrusion = 0.1
        lip_bottom_recess = 0.28

        lip_bottom_y = self.edge_y + lip_bottom_recess
        self.m0_br = self.mesh.add_xyz(
            self.mid0_x, lip_bottom_y, self.lip_bottom_z
        )
        self.m0_bl = self.mesh.add_xyz(self.mid0_x, 0, self.lip_bottom_z)
        self.l_br = self.mesh.add_xyz(
            self.x_mid_left, lip_bottom_y, self.lip_bottom_z
        )
        self.l_bl = self.mesh.add_xyz(self.x_mid_left, 0, self.lip_bottom_z)

        self.mesh.add_quad(self.l_bl, self.l_br, self.m0_br, self.m0_bl)
        self.mesh.add_quad(self.m0_ml, self.l_ml, self.l_bl, self.m0_bl)
        self.mesh.add_quad(self.l_ml, self.l_mr, self.l_br, self.l_bl)

        self.l_lip0 = self.mesh.add_xyz(
            self.x_mid_left, self.edge_y, self.bottom_z - 0.05
        )
        self.l_lip1 = self.mesh.add_xyz(
            self.x_mid_left, self.edge_y - lip_protrusion, self.bottom_z - 0.13
        )
        self.l_lip2 = self.mesh.add_xyz(
            self.x_mid_left, self.edge_y - lip_protrusion, self.bottom_z - 0.23
        )
        self.mesh.add_tri(self.l_br, self.l_mr, self.l_lip0)
        self.mesh.add_tri(self.l_br, self.l_lip0, self.l_lip1)
        self.mesh.add_tri(self.l_br, self.l_lip1, self.l_lip2)

        self.m0_lip0 = self.mesh.add_xyz(
            self.mid0_x, self.edge_y, self.bottom_z - 0.05
        )
        self.m0_lip1 = self.mesh.add_xyz(
            self.mid0_x, self.edge_y - 0.1, self.bottom_z - 0.13
        )
        self.m0_lip2 = self.mesh.add_xyz(
            self.mid0_x, self.edge_y - 0.1, self.bottom_z - 0.23
        )

        self.mesh.add_quad(self.l_mr, self.m0_mr, self.m0_lip0, self.l_lip0)
        self.mesh.add_quad(
            self.l_lip0, self.m0_lip0, self.m0_lip1, self.l_lip1
        )
        self.mesh.add_quad(
            self.l_lip1, self.m0_lip1, self.m0_lip2, self.l_lip2
        )
        self.mesh.add_quad(self.l_lip2, self.m0_lip2, self.m0_br, self.l_br)

        self.mesh.add_quad(self.m0_mr, self.m0_ml, self.m0_bl, self.m0_br)
        self.mesh.add_tri(self.m0_br, self.m0_lip0, self.m0_mr)
        self.mesh.add_tri(self.m0_br, self.m0_lip1, self.m0_lip0)
        self.mesh.add_tri(self.m0_br, self.m0_lip2, self.m0_lip1)


class BottomClip:
    l_y = -7.0
    r_y = -8.5

    def __init__(self, mesh: cad.Mesh) -> None:
        self.mesh = mesh
        self.b_arc_points: List[cad.MeshPoint] = []
        self.t_arc_points: List[cad.MeshPoint] = []

        SocketParams().assign_params_to(self)
        self.top_z = self.z_clip_top
        self.bottom_z = self.z_clip_bottom

    def gen(self) -> None:
        self.gen_arc()
        self.gen_block()
        self.gen_lip()

    def gen_arc(self) -> None:
        arc_r = 2.0
        center_x = 4.2
        center_y = -5.0

        fn = 24
        for n in range(fn + 1):
            angle = (math.radians(90) / fn) * n
            angle_x = math.sin(angle) * arc_r
            angle_y = math.cos(angle) * -arc_r

            self.b_arc_points.append(
                self.mesh.add_xyz(
                    center_x + angle_x, center_y + angle_y, self.bottom_z
                )
            )
            self.t_arc_points.append(
                self.mesh.add_xyz(
                    center_x + angle_x, center_y + angle_y, self.top_z
                )
            )

        for n in range(1, len(self.b_arc_points)):
            # vertical face
            self.mesh.add_quad(
                self.b_arc_points[n - 1],
                self.b_arc_points[n],
                self.t_arc_points[n],
                self.t_arc_points[n - 1],
            )

    def gen_block(self) -> None:
        self.l_tl = self.mesh.add_xyz(self.x_mid_left, self.l_y, self.top_z)
        self.l_tr = self.mesh.add_xyz(self.x_mid_left, self.r_y, self.top_z)
        self.l_mr = self.mesh.add_xyz(self.x_mid_left, self.r_y, self.bottom_z)
        self.l_ml = self.mesh.add_xyz(self.x_mid_left, self.l_y, self.bottom_z)

        mid0_x = self.b_arc_points[0].x
        self.m0_tr = self.mesh.add_xyz(mid0_x, self.r_y, self.top_z)
        self.m0_mr = self.mesh.add_xyz(mid0_x, self.r_y, self.bottom_z)

        self.mesh.add_quad(self.l_tl, self.l_tr, self.l_mr, self.l_ml)
        self.mesh.add_quad(
            self.l_ml, self.b_arc_points[0], self.t_arc_points[0], self.l_tl
        )

        self.mesh.add_quad(self.l_tr, self.m0_tr, self.m0_mr, self.l_mr)

        r_x = self.b_arc_points[-1].x + 0.6
        self.r_mr = self.mesh.add_xyz(r_x, self.r_y, self.bottom_z)
        self.r_tr = self.mesh.add_xyz(r_x, self.r_y, self.top_z)

        b_y = self.b_arc_points[-1].y
        self.r_ml = self.mesh.add_xyz(r_x, b_y, self.bottom_z)
        self.r_tl = self.mesh.add_xyz(r_x, b_y, self.top_z)

        for n in range(8):
            self.mesh.add_tri(
                self.m0_mr, self.b_arc_points[n + 1], self.b_arc_points[n]
            )
            self.mesh.add_tri(
                self.m0_tr, self.t_arc_points[n], self.t_arc_points[n + 1]
            )

        for n in range(8, 16):
            self.mesh.add_tri(
                self.r_mr, self.b_arc_points[n + 1], self.b_arc_points[n]
            )
            self.mesh.add_tri(
                self.r_tr, self.t_arc_points[n], self.t_arc_points[n + 1]
            )

        for n in range(16, len(self.b_arc_points) - 1):
            self.mesh.add_tri(
                self.r_ml, self.b_arc_points[n + 1], self.b_arc_points[n]
            )
            self.mesh.add_tri(
                self.r_tl, self.t_arc_points[n], self.t_arc_points[n + 1]
            )

        self.mesh.add_tri(self.m0_mr, self.r_mr, self.b_arc_points[8])
        self.mesh.add_tri(self.m0_tr, self.t_arc_points[8], self.r_tr)
        self.mesh.add_tri(self.r_mr, self.r_ml, self.b_arc_points[16])
        self.mesh.add_tri(self.r_tr, self.t_arc_points[16], self.r_tl)

        self.mesh.add_quad(
            self.b_arc_points[-1], self.r_ml, self.r_tl, self.t_arc_points[-1]
        )
        self.mesh.add_quad(self.r_ml, self.r_mr, self.r_tr, self.r_tl)
        self.mesh.add_quad(self.r_mr, self.m0_mr, self.m0_tr, self.r_tr)

        # Remaining missing top face
        self.mesh.add_quad(
            self.l_tl, self.t_arc_points[0], self.m0_tr, self.l_tr
        )

    def gen_lip(self) -> None:
        lip_protrusion = 0.1
        lip_bottom_recess = 0.28

        lip_bottom_y = self.l_y - lip_bottom_recess
        self.l_bl = self.mesh.add_xyz(
            self.x_mid_left, lip_bottom_y, self.lip_bottom_z
        )
        self.l_br = self.mesh.add_xyz(
            self.x_mid_left, self.r_y, self.lip_bottom_z
        )

        self.mesh.add_quad(self.l_br, self.l_bl, self.l_ml, self.l_mr)

        mid0_x = self.b_arc_points[0].x
        self.m_bl = self.mesh.add_xyz(mid0_x, lip_bottom_y, self.lip_bottom_z)
        self.m_br = self.mesh.add_xyz(mid0_x, self.r_y, self.lip_bottom_z)

        self.mesh.add_quad(self.l_bl, self.l_br, self.m_br, self.m_bl)
        self.mesh.add_quad(self.m0_mr, self.m_br, self.l_br, self.l_mr)

        self.l_lip0 = self.mesh.add_xyz(
            self.x_mid_left, self.l_y, self.bottom_z - 0.05
        )
        self.l_lip1 = self.mesh.add_xyz(
            self.x_mid_left, self.l_y + lip_protrusion, self.bottom_z - 0.13
        )
        self.l_lip2 = self.mesh.add_xyz(
            self.x_mid_left, self.l_y + lip_protrusion, self.bottom_z - 0.23
        )
        self.mesh.add_tri(self.l_bl, self.l_lip0, self.l_ml)
        self.mesh.add_tri(self.l_bl, self.l_lip1, self.l_lip0)
        self.mesh.add_tri(self.l_bl, self.l_lip2, self.l_lip1)

        self.m_lip0 = self.mesh.add_xyz(mid0_x, self.l_y, self.bottom_z - 0.05)
        self.m_lip1 = self.mesh.add_xyz(
            mid0_x, self.l_y + lip_protrusion, self.bottom_z - 0.13
        )
        self.m_lip2 = self.mesh.add_xyz(
            mid0_x, self.l_y + lip_protrusion, self.bottom_z - 0.23
        )
        self.mesh.add_tri(self.m_bl, self.b_arc_points[0], self.m_lip0)
        self.mesh.add_tri(self.m_bl, self.m_lip0, self.m_lip1)
        self.mesh.add_tri(self.m_bl, self.m_lip1, self.m_lip2)
        self.mesh.add_quad(
            self.m_bl, self.m_br, self.m0_mr, self.b_arc_points[0]
        )

        self.mesh.add_quad(
            self.l_lip0, self.m_lip0, self.b_arc_points[0], self.l_ml
        )
        self.mesh.add_quad(self.l_lip1, self.m_lip1, self.m_lip0, self.l_lip0)
        self.mesh.add_quad(self.l_lip2, self.m_lip2, self.m_lip1, self.l_lip1)
        self.mesh.add_quad(self.l_bl, self.m_bl, self.m_lip2, self.l_lip2)


class DiodeClip:
    def __init__(self, mesh: cad.Mesh) -> None:
        self.mesh = mesh
        SocketParams().assign_params_to(self)

        self.top_wall_thickness = 0.75
        self.diode_x = -6.35
        self.diode_y = 0.5
        self.top_y = (
            self.diode_y - (self.diode_h * 0.5) - self.top_wall_thickness
        )
        self.right_x = self.diode_x + 1.9
        self.top_z = self.z_clip_top
        self.bottom_z = self.z_clip_bottom

    def gen(self) -> None:
        m1_y = self.diode_y - (self.diode_h * 0.5)
        m2_y = self.diode_y + (self.diode_h * 0.5)
        b_y = m2_y + self.top_wall_thickness
        m_x = self.diode_x + (self.diode_w * 0.5)
        x_mid_left = self.diode_x + 0.3

        b_tl = self.mesh.add_xyz(x_mid_left, self.top_y, self.bottom_z)
        t_tl = self.mesh.add_xyz(x_mid_left, self.top_y, self.top_z)

        b_l0 = self.mesh.add_xyz(x_mid_left, m1_y, self.bottom_z)
        t_l0 = self.mesh.add_xyz(x_mid_left, m1_y, self.top_z)

        b_l1 = self.mesh.add_xyz(m_x, m1_y, self.bottom_z)
        t_l1 = self.mesh.add_xyz(m_x, m1_y, self.top_z)

        b_l2 = self.mesh.add_xyz(m_x, m2_y, self.bottom_z)
        t_l2 = self.mesh.add_xyz(m_x, m2_y, self.top_z)

        b_l3 = self.mesh.add_xyz(x_mid_left, m2_y, self.bottom_z)
        t_l3 = self.mesh.add_xyz(x_mid_left, m2_y, self.top_z)

        b_tr = self.mesh.add_xyz(self.right_x, self.top_y, self.bottom_z)
        t_tr = self.mesh.add_xyz(self.right_x, self.top_y, self.top_z)

        b_br = self.mesh.add_xyz(self.right_x, b_y, self.bottom_z)
        t_br = self.mesh.add_xyz(self.right_x, b_y, self.top_z)

        b_bl = self.mesh.add_xyz(x_mid_left, b_y, self.bottom_z)
        t_bl = self.mesh.add_xyz(x_mid_left, b_y, self.top_z)

        # Vertical walls
        self.mesh.add_quad(b_tl, b_l0, t_l0, t_tl)
        self.mesh.add_quad(b_tr, b_tl, t_tl, t_tr)
        self.mesh.add_quad(b_br, b_tr, t_tr, t_br)
        self.mesh.add_quad(b_bl, b_br, t_br, t_bl)
        self.mesh.add_quad(b_l3, b_bl, t_bl, t_l3)
        self.mesh.add_quad(b_l2, b_l3, t_l3, t_l2)
        self.mesh.add_quad(b_l1, b_l2, t_l2, t_l1)
        self.mesh.add_quad(b_l0, b_l1, t_l1, t_l0)

        # Top and bottom
        self.mesh.add_quad(b_tl, b_tr, b_l1, b_l0)
        self.mesh.add_quad(t_l0, t_l1, t_tr, t_tl)

        self.mesh.add_quad(b_l1, b_tr, b_br, b_l2)
        self.mesh.add_quad(t_l2, t_br, t_tr, t_l1)

        self.mesh.add_quad(b_l2, b_br, b_bl, b_l3)
        self.mesh.add_quad(t_l3, t_bl, t_br, t_l2)


class SocketHolderGenerator:
    def top_clip(self) -> bpy.types.Object:
        mesh = cad.Mesh()
        TopClip(mesh).gen()
        return blender_util.new_mesh_obj("clip_top", mesh)

    def bottom_clip(self) -> bpy.types.Object:
        mesh = cad.Mesh()
        BottomClip(mesh).gen()
        return blender_util.new_mesh_obj("clip_bottom", mesh)

    def diode_clip_right(self) -> bpy.types.Object:
        mesh = cad.Mesh()
        DiodeClip(mesh).gen()
        return blender_util.new_mesh_obj("clip_diode", mesh)

    def diode_clip_left(self) -> bpy.types.Object:
        mesh = cad.Mesh()
        clip = DiodeClip(mesh)
        clip.gen()
        obj = blender_util.new_mesh_obj("clip_diode", mesh)
        with blender_util.TransformContext(obj) as ctx:
            ctx.rotate(180, "Z", center=(clip.diode_x, clip.diode_y, 0.0))
        return obj

    def base_plate(self, type: SocketType) -> bpy.types.Object:
        params = SocketParams()

        x_bottom_right = 6.8

        if type == SocketType.SMALL_TOP:
            y_left_top = 3.5
        else:
            y_left_top = 5.0
        y_left_bottom = -2.8
        y_right_top = 5.0
        y_right_bottom = -1.0
        y_bottom_right_top = -5.0

        z_range = (params.z_bottom, params.z_top)

        obj = blender_range_cube(
            (params.x_mid_left, params.x_mid_right),
            (y_left_bottom, y_left_top),
            z_range,
            name="socket_holder",
        )

        z_edge_range = (params.z_bottom - 1.0, params.z_top)
        bottom = blender_range_cube(
            (params.x_mid_left, params.x_mid_right),
            (params.y_bottom + 1.7, y_left_bottom),
            z_range,
            name="bottom",
        )
        blender_util.union(obj, bottom)
        bottom_right = blender_range_cube(
            (params.x_mid_right, x_bottom_right),
            (params.y_bottom + 1.7, y_bottom_right_top),
            z_range,
            name="bottom_right",
        )
        blender_util.union(obj, bottom_right)
        bottom_edge = blender_range_cube(
            (params.x_mid_left, x_bottom_right),
            (params.y_bottom, params.y_bottom + 1.7),
            z_edge_range,
            name="bottom",
        )
        blender_util.union(obj, bottom_edge)

        if type == SocketType.SMALL_TOP:
            return obj

        if type == SocketType.LEFT:
            left = blender_range_cube(
                (params.x_left + 2.0, params.x_mid_left),
                (y_left_bottom, y_left_top),
                z_range,
                name="left",
            )
            blender_util.union(obj, left)
        elif type != SocketType.LEFT:
            left = blender_range_cube(
                (params.x_left + 1.0, params.x_mid_left),
                (y_left_bottom, y_left_top),
                z_range,
                name="left",
            )
            blender_util.union(obj, left)
            left_edge = blender_range_cube(
                (params.x_left, params.x_left + 1.0),
                (y_left_bottom, y_left_top),
                z_edge_range,
                name="left_edge",
            )
            blender_util.union(obj, left_edge)

        if type != SocketType.TOP:
            top = blender_range_cube(
                (params.x_mid_left, params.x_mid_right),
                (y_left_top, params.y_top - 3.0),
                z_range,
                name="top",
            )
            blender_util.union(obj, top)
            top_edge = blender_range_cube(
                (params.x_mid_left, params.x_mid_right),
                (params.y_top - 3.0, params.y_top),
                z_edge_range,
                name="top_edge",
            )
            blender_util.union(obj, top_edge)

        if type != SocketType.RIGHT:
            right = blender_range_cube(
                (params.x_mid_right, params.x_right - 1.0),
                (y_right_bottom, y_right_top),
                z_range,
                name="right",
            )
            blender_util.union(obj, right)
            right_edge = blender_range_cube(
                (params.x_right - 1.0, params.x_right),
                (y_right_bottom, y_right_top),
                z_edge_range,
                name="right_edge",
            )
            blender_util.union(obj, right_edge)

        return obj

    def wire_holder_tower(self, x: float, y: float) -> bpy.types.Object:
        base_r_x = 1.5
        base_r_y = 0.80
        base_h = 0.75
        w = 1.10
        d = 0.8
        h = 1.25
        params = SocketParams()

        z_base = params.z_bottom - base_h

        base = blender_range_cube(
            (x - base_r_x, x + base_r_x),
            (y - base_r_y, y + base_r_y),
            (params.z_bottom, z_base),
        )

        # Left tower
        tower = blender_range_cube(
            (x - base_r_x, x - base_r_x + w),
            (y - base_r_y, y - base_r_y + d),
            (z_base, z_base - h),
        )
        blender_util.union(base, tower)

        # Right tower
        tower = blender_range_cube(
            (x + base_r_x - w, x + base_r_x),
            (y + base_r_y - d, y + base_r_y),
            (z_base, z_base - h),
        )
        blender_util.union(base, tower)

        return base

    def wire_holders(self, obj: bpy.types.Object, type: SocketType) -> None:
        bottom_tower = self.wire_holder_tower(-1.75, 4.0)
        blender_util.union(obj, bottom_tower)

        if type != SocketType.RIGHT:
            right_tower = self.wire_holder_tower(0.0, 0.0)
            with blender_util.TransformContext(right_tower) as ctx:
                ctx.rotate(90, "Z")
                ctx.translate(7.3, 2.0, 0.0)
            blender_util.union(obj, right_tower)

    def gen(self, type: SocketType) -> bpy.types.Object:
        params = SocketParams()
        thickness = params.thickness

        # Base
        obj = self.base_plate(type)

        top_clip = self.top_clip()
        blender_util.union(obj, top_clip)
        bottom_clip = self.bottom_clip()
        blender_util.union(obj, bottom_clip)
        if type != SocketType.SMALL_TOP:
            diode_clip_right = self.diode_clip_right()
            blender_util.union(obj, diode_clip_right)
            if type != SocketType.LEFT:
                diode_clip_left = self.diode_clip_left()
                blender_util.union(obj, diode_clip_left)
            self.wire_holders(obj, type)

        # Cut-outs for the switch legs
        leg_r_cutout = blender_cylinder(r=1.6, h=8, fn=85)
        with blender_util.TransformContext(leg_r_cutout) as ctx:
            ctx.translate(3.65, -2.7, -thickness)
        blender_util.difference(obj, leg_r_cutout)

        leg_l_cutout = blender_cylinder(r=1.6, h=8, fn=85)
        with blender_util.TransformContext(leg_l_cutout) as ctx:
            ctx.translate(-2.7, -5.2, -thickness)
        blender_util.difference(obj, leg_l_cutout)

        # Cut-out for the switch stabilizer
        main_cutout = blender_cylinder(r=2.1, h=8, fn=98)
        with blender_util.TransformContext(main_cutout) as ctx:
            ctx.translate(0, 0, -thickness)
        blender_util.difference(obj, main_cutout)

        return obj


class SocketHolder:
    def __init__(self, mesh: cad.Mesh) -> None:
        self.mesh = mesh
        # Points for the faces that may connect to adjacent holders
        # in the keyboard grid.  These are split by the points on the top and
        # bottom of the face.  Within each set of top and bottom, the points
        # are sorted from left to right when looking at the front of the face.
        self.top_points: Tuple[List[MeshPoint], List[MeshPoint]] = []
        self.bottom_points: Tuple[List[MeshPoint], List[MeshPoint]] = []
        self.left_points: Tuple[List[MeshPoint], List[MeshPoint]] = []
        self.right_points: Tuple[List[MeshPoint], List[MeshPoint]] = []

    def close_bottom_face(self) -> None:
        self._close_face(self.bottom_points)

    def close_top_face(self) -> None:
        self._close_face(self.top_points)

    def close_left_face(self) -> None:
        self._close_face(self.left_points)

    def close_right_face(self) -> None:
        self._close_face(self.right_points)

    def _close_face(
        self, points: Tuple[List[MeshPoint], List[MeshPoint]]
    ) -> None:
        top, bottom = points
        for idx in range(1, len(bottom)):
            self.mesh.add_tri(top[0], bottom[idx], bottom[idx - 1])
        for idx in range(1, len(top)):
            self.mesh.add_tri(top[idx - 1], top[idx], bottom[-1])

    def join_bottom(self, other: SocketHolder) -> None:
        """Connect this SocketHolder to one below it."""
        # left side face
        left_tl = self.bottom_points[0][0]
        left_bl = self.bottom_points[1][0]
        left_tr = other.top_points[0][-1]
        left_br = other.top_points[1][-1]
        self.mesh.add_quad(left_tl, left_tr, left_br, left_bl)

        # right side face
        right_tl = other.top_points[0][0]
        right_bl = other.top_points[1][0]
        right_tr = self.bottom_points[0][-1]
        right_br = self.bottom_points[1][-1]
        self.mesh.add_quad(right_tl, right_tr, right_br, right_bl)

        # bottom face
        for n in range(0, len(other.top_points[1]) - 1):
            self.mesh.add_tri(
                self.bottom_points[1][0],
                other.top_points[1][n + 1],
                other.top_points[1][n],
            )
        for n in range(0, len(self.bottom_points[1]) - 1):
            self.mesh.add_tri(
                other.top_points[1][0],
                self.bottom_points[1][n + 1],
                self.bottom_points[1][n],
            )

        # top face
        for n in range(0, len(other.top_points[0]) - 1):
            self.mesh.add_tri(
                self.bottom_points[0][0],
                other.top_points[0][n],
                other.top_points[0][n + 1],
            )
        for n in range(0, len(self.bottom_points[0]) - 1):
            self.mesh.add_tri(
                other.top_points[0][0],
                self.bottom_points[0][n],
                self.bottom_points[0][n + 1],
            )

    def join_right(self, other: SocketHolder) -> None:
        """Connect this SocketHolder to one to its right."""
        # lower vertical face
        bottom_tl = self.right_points[0][0]
        bottom_bl = self.right_points[1][0]
        bottom_tr = other.left_points[0][-1]
        bottom_br = other.left_points[1][-1]
        self.mesh.add_quad(bottom_tl, bottom_tr, bottom_br, bottom_bl)

        # upper vertical face
        top_tl = other.left_points[0][0]
        top_bl = other.left_points[1][0]
        top_tr = self.right_points[0][-1]
        top_br = self.right_points[1][-1]
        self.mesh.add_quad(top_tl, top_tr, top_br, top_bl)

        # bottom face
        assert len(self.right_points[1]) == 2
        assert len(other.left_points[1]) == 2
        self.mesh.add_quad(
            self.right_points[1][0],
            other.left_points[1][1],
            other.left_points[1][0],
            self.right_points[1][1],
        )

        # top face
        assert len(self.right_points[0]) == 2
        assert len(other.left_points[0]) == 2
        self.mesh.add_quad(
            self.right_points[0][0],
            self.right_points[0][1],
            other.left_points[0][0],
            other.left_points[0][1],
        )


class SocketType(enum.IntEnum):
    NORMAL = 0
    SMALL_TOP = 1
    TOP = 2
    LEFT = 3
    RIGHT = 4


class SocketHolderBuilder:
    def __init__(self, type: SocketType = SocketType.NORMAL) -> None:
        self.points: List[cad.Point] = []
        self.faces: List[Tuple[int, int, int]] = []

        # Points around the faces that may connect to neighboring socket
        # holders in the keyboard grid.  Each list is split into 2 tuples of
        # the top and bottom points.  Among the top and bottom points, these
        # are sorted from left to right when looking at the face's front.
        self.bottom_points: Tuple[List[int], List[int]] = ([], [])
        self.top_points: Tuple[List[int], List[int]] = ([], [])
        self.left_points: Tuple[List[int], List[int]] = ([], [])
        self.right_points: Tuple[List[int], List[int]] = ([], [])

        # Sets of the face points, before splitting and sorting
        bottom_point_set: Set[int] = set()
        top_point_set: Set[int] = set()
        left_point_set: Set[int] = set()
        right_point_set: Set[int] = set()

        params = SocketParams()

        # Blender doesn't seem to do great when trying to use boolean union
        # operators to join together many different socket holders in a complex
        # grid.  At some point it seems to fail and produces missing faces.
        #
        # Therefore we just use blender's boolean operators to produce a single
        # socket, then we create our own cad.Mesh object from this, and
        # manually create the explicit faces we want to connect them in a grid.
        obj = SocketHolderGenerator().gen(type)
        tol = 0.00001
        with blender_util.TransformContext(obj) as ctx:
            ctx.triangulate()
            for v in ctx.bmesh.verts:
                self.points.append(cad.Point(v.co.x, v.co.y, v.co.z))

                if math.isclose(v.co.y, params.y_bottom, abs_tol=tol):
                    bottom_point_set.add(v.index)
                if math.isclose(v.co.y, params.y_top, abs_tol=tol):
                    top_point_set.add(v.index)
                if math.isclose(v.co.x, params.x_left, abs_tol=tol):
                    left_point_set.add(v.index)
                if math.isclose(v.co.x, params.x_right, abs_tol=tol):
                    right_point_set.add(v.index)

            for f in ctx.bmesh.faces:
                assert len(f.verts) == 3
                # BMesh faces list the vertices in counter-clockwise order,
                # we want clockwise
                indices = (
                    f.verts[2].index,
                    f.verts[1].index,
                    f.verts[0].index,
                )
                if all(idx in bottom_point_set for idx in indices):
                    continue
                elif all(idx in top_point_set for idx in indices):
                    continue
                elif all(idx in left_point_set for idx in indices):
                    continue
                elif all(idx in right_point_set for idx in indices):
                    continue
                else:
                    self.faces.append(indices)

        self.bottom_points = self._split_top_bottom(
            bottom_point_set, lambda idx: self.points[idx].x
        )
        self.top_points = self._split_top_bottom(
            top_point_set, lambda idx: -self.points[idx].x
        )
        self.left_points = self._split_top_bottom(
            left_point_set, lambda idx: -self.points[idx].y
        )
        self.right_points = self._split_top_bottom(
            right_point_set, lambda idx: self.points[idx].y
        )

        bpy.data.objects.remove(obj)

    def _split_top_bottom(
        self, points: Set[int], sort_key: Callable[[int], float]
    ) -> Tuple[List[int], List[int]]:
        params = SocketParams()
        z_edge_bottom = params.z_bottom - 1.0

        tol = 0.00001
        top: List[int] = []
        bottom: List[int] = []
        for idx in points:
            p = self.points[idx]
            if math.isclose(p.z, params.z_top, abs_tol=tol):
                top.append(idx)
            else:
                assert math.isclose(p.z, z_edge_bottom, abs_tol=tol)
                bottom.append(idx)

        top.sort(key=sort_key)
        bottom.sort(key=sort_key)

        return top, bottom

    def gen(
        self, mesh: cad.Mesh, tf: cad.Transform, flip: bool = False
    ) -> SocketHolder:
        if flip:
            tf = cad.Transform().rotate(0.0, 0.0, 180.0).transform(tf)

        holder = SocketHolder(mesh)
        mesh_points: List[cad.MeshPoint] = []
        for p in self.points:
            mp = mesh.add_point(p.transform(tf))
            mesh_points.append(mp)

        for f in self.faces:
            mesh.add_tri(
                mesh_points[f[0]], mesh_points[f[1]], mesh_points[f[2]]
            )

        def to_mp(indices: List[int]) -> List[MeshPoint]:
            return [mesh_points[idx] for idx in indices]

        def to_mesh_points(
            indices: Tuple[List[int], List[int]]
        ) -> Tuple[List[MeshPoint], List[MeshPoint]]:
            return to_mp(indices[0]), to_mp(indices[1])

        holder.bottom_points = to_mesh_points(self.bottom_points)
        holder.top_points = to_mesh_points(self.top_points)
        holder.left_points = to_mesh_points(self.left_points)
        holder.right_points = to_mesh_points(self.right_points)

        if flip:
            holder.top_points, holder.bottom_points = (
                holder.bottom_points,
                holder.top_points,
            )
            holder.left_points, holder.right_points = (
                holder.right_points,
                holder.left_points,
            )

        return holder


def cad_socket_holder(type: SocketType = SocketType.NORMAL) -> bpy.types.Object:
    """
    Return the original socket holder object that we generate, before turning
    it into a cad.Mesh.
    """
    return SocketHolderGenerator().gen(type)


def socket_holder(flip: bool = False) -> bpy.types.Object:
    mesh = cad.Mesh()
    builder = SocketHolderBuilder()
    holder = builder.gen(mesh, cad.Transform(), flip=flip)
    holder.close_bottom_face()
    holder.close_top_face()
    holder.close_left_face()
    holder.close_right_face()
    return blender_util.new_mesh_obj("socket_holder", mesh)
