#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

import math
from typing import List

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
    r_y = -8.7

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
        self.top_y = self.diode_y - (self.diode_h * 0.5) - self.top_wall_thickness
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

    def base_plate(self) -> bpy.types.Object:
        params = SocketParams()
        full_size = 17.4

        x_bottom_right = 6.8

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
        left = blender_range_cube(
            (params.x_left, params.x_mid_left),
            (y_left_bottom, y_left_top),
            z_range,
            name="left",
        )
        blender_util.union(obj, left)
        top = blender_range_cube(
            (params.x_mid_left, params.x_mid_right),
            (y_left_top, params.y_top),
            z_range,
            name="top",
        )
        blender_util.union(obj, top)
        right = blender_range_cube(
            (params.x_mid_right, params.x_right),
            (y_right_bottom, y_right_top),
            z_range,
            name="right",
        )
        blender_util.union(obj, right)
        bottom = blender_range_cube(
            (params.x_mid_left, params.x_mid_right),
            (params.y_bottom, y_left_bottom),
            z_range,
            name="bottom",
        )
        blender_util.union(obj, bottom)
        bottom_right = blender_range_cube(
            (params.x_mid_right, x_bottom_right),
            (params.y_bottom, y_bottom_right_top),
            z_range,
            name="bottom_right",
        )
        blender_util.union(obj, bottom_right)
        return obj

    def wire_holder_tower(self, x: float, y: float) -> bpy.types.Object:
        base_r_x = 1.5
        base_r_y = 0.80
        base_h = 0.5
        w = 0.8
        d = 0.8
        lip_d = 0.3
        h = 1.0
        lip_h = 0.5
        params = SocketParams()

        z_base = params.z_bottom - base_h

        base = blender_range_cube((x - base_r_x, x + base_r_x), (y - base_r_y, y + base_r_y), (params.z_bottom, z_base))

        # Middle tower
        r_x = w * 0.5
        tower = blender_range_cube((x - r_x, x + r_x), (y - base_r_y, y - base_r_y + d), (z_base, z_base - h))
        blender_util.union(base, tower)
        top = blender_range_cube((x - r_x, x + r_x), (y - base_r_y, y - base_r_y + d + lip_d), (z_base - h, z_base - h - lip_h))
        blender_util.union(base, top)

        # Left tower
        tower = blender_range_cube((x - base_r_x, x - base_r_x + w), (y + base_r_y - d, y + base_r_y), (z_base, z_base - h))
        blender_util.union(base, tower)
        top = blender_range_cube((x - base_r_x, x - base_r_x + w), (y + base_r_y - d - lip_d, y + base_r_y), (z_base - h, z_base - h - lip_h))
        blender_util.union(base, top)

        # Right tower
        tower = blender_range_cube((x + base_r_x - w, x + base_r_x), (y + base_r_y - d, y + base_r_y), (z_base, z_base - h))
        blender_util.union(base, tower)
        top = blender_range_cube((x + base_r_x - w, x + base_r_x), (y + base_r_y - d - lip_d, y + base_r_y), (z_base - h, z_base - h - lip_h))
        blender_util.union(base, top)

        return base

    def wire_holders(self, obj: bpy.types.Object) -> None:
        bottom_tower = self.wire_holder_tower(-1.75, 4.0)
        blender_util.union(obj, bottom_tower)

        right_tower = self.wire_holder_tower(0.0, 0.0)
        with blender_util.TransformContext(right_tower) as ctx:
            ctx.rotate(90, "Z")
            ctx.translate(7.3, 2.0, 0.0)
        blender_util.union(obj, right_tower)

    def gen(self) -> bpy.types.Object:
        params = SocketParams()
        thickness = params.thickness

        # Base
        obj = self.base_plate()

        top_clip = self.top_clip()
        blender_util.union(obj, top_clip)
        bottom_clip = self.bottom_clip()
        blender_util.union(obj, bottom_clip)
        diode_clip_right = self.diode_clip_right()
        blender_util.union(obj, diode_clip_right)
        diode_clip_left = self.diode_clip_left()
        blender_util.union(obj, diode_clip_left)

        self.wire_holders(obj)

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
        # in the keyboard grid.
        self.top_points: List[MeshPoint] = []
        self.bottom_points: List[MeshPoint] = []
        self.left_points: List[MeshPoint] = []
        self.right_points: List[MeshPoint] = []

    def close_bottom_face(self) -> None:
        top, bottom = self._split_top_bottom(self.bottom_points)
        top.sort(key=lambda mp: mp.x)
        bottom.sort(key=lambda mp: mp.x)
        self._close_face(top, bottom)

    def close_top_face(self) -> None:
        top, bottom = self._split_top_bottom(self.top_points)
        top.sort(key=lambda mp: -mp.x)
        bottom.sort(key=lambda mp: -mp.x)
        self._close_face(top, bottom)

    def close_left_face(self) -> None:
        top, bottom = self._split_top_bottom(self.left_points)
        top.sort(key=lambda mp: -mp.y)
        bottom.sort(key=lambda mp: -mp.y)
        self._close_face(top, bottom)

    def close_right_face(self) -> None:
        top, bottom = self._split_top_bottom(self.right_points)
        top.sort(key=lambda mp: mp.y)
        bottom.sort(key=lambda mp: mp.y)
        self._close_face(top, bottom)

    def _split_top_bottom(self, points: List[MeshPoint]) -> Tuple[List[MeshPoint], List[MeshPoint]]:
        tol = 0.00001
        params = SocketParams()
        top: List[MeshPoint] = []
        bottom: List[MeshPoint] = []
        for p in points:
            if math.isclose(p.z, params.z_top, abs_tol=tol):
                top.append(p)
            else:
                assert math.isclose(p.z, params.z_bottom, abs_tol=tol)
                bottom.append(p)

        return top, bottom

    def _close_face(self, top: List[MeshPoint], bottom: List[MeshPoint]) -> None:
        for idx in range(1, len(bottom)):
            self.mesh.add_tri(top[0], bottom[idx], bottom[idx - 1])
        for idx in range(1, len(top)):
            self.mesh.add_tri(top[idx - 1], top[idx], bottom[-1])


class SocketHolderBuilder:
    def __init__(self) -> None:
        self.points: List[cad.Point] = []
        self.faces: List[Tuple[int, int, int]] = []

        # Points around the faces that may connect to neighboring socket
        # holders in the keyboard grid.
        self.bottom_points: Set[int] = set()
        self.top_points: Set[int] = set()
        self.left_points: Set[int] = set()
        self.right_points: Set[int] = set()

        params = SocketParams()

        # Blender doesn't seem to do great when trying to use boolean union
        # operators to join together many different socket holders in a complex
        # grid.  At some point it seems to fail and produces missing faces.
        #
        # Therefore we just use blender's boolean operators to produce a single
        # socket, then we create our own cad.Mesh object from this, and
        # manually create the explicit faces we want to connect them in a grid.
        obj = SocketHolderGenerator().gen()
        tol = 0.00001
        with blender_util.TransformContext(obj) as ctx:
            ctx.triangulate()
            for v in ctx.bmesh.verts:
                self.points.append(cad.Point(v.co.x, v.co.y, v.co.z))

                if math.isclose(v.co.y, params.y_bottom, abs_tol=tol):
                    if (
                        v.co.x >= (params.x_mid_left - tol)
                        and v.co.x <= (params.x_mid_right + tol)
                        and v.co.z >= (params.z_bottom - tol)
                    ):
                        self.bottom_points.add(v.index)
                if math.isclose(v.co.y, params.y_top, abs_tol=tol):
                    self.top_points.add(v.index)
                if math.isclose(v.co.x, params.x_left, abs_tol=tol):
                    self.left_points.add(v.index)
                if math.isclose(v.co.x, params.x_right, abs_tol=tol):
                    self.right_points.add(v.index)

            for f in ctx.bmesh.faces:
                assert len(f.verts) == 3
                # BMesh faces list the vertices in counter-clockwise order,
                # we want clockwise
                indices = (
                    f.verts[2].index,
                    f.verts[1].index,
                    f.verts[0].index,
                )
                if all(idx in self.bottom_points for idx in indices):
                    continue
                elif all(idx in self.top_points for idx in indices):
                    continue
                elif all(idx in self.left_points for idx in indices):
                    continue
                elif all(idx in self.right_points for idx in indices):
                    continue
                else:
                    self.faces.append(indices)

        bpy.data.objects.remove(obj)

    def gen(self, mesh: cad.Mesh, tf: cad.Transform) -> SocketHolder:
        holder = SocketHolder(mesh)
        mesh_points: List[cad.MeshPoint] = []
        for p in self.points:
            mp = mesh.add_point(p.transform(tf))
            mesh_points.append(mp)

        for f in self.faces:
            mesh.add_tri(
                mesh_points[f[0]], mesh_points[f[1]], mesh_points[f[2]]
            )

        for idx in self.bottom_points:
            holder.bottom_points.append(mesh_points[idx])
        for idx in self.top_points:
            holder.top_points.append(mesh_points[idx])
        for idx in self.left_points:
            holder.left_points.append(mesh_points[idx])
        for idx in self.right_points:
            holder.right_points.append(mesh_points[idx])

        return holder


def cad_socket_holder() -> bpy.types.Object:
    """
    Return the original socket holder object that we generate, before turning
    it into a cad.Mesh.
    """
    return SocketHolderGenerator().gen()


def socket_holder() -> bpy.types.Object:
    mesh = cad.Mesh()
    builder = SocketHolderBuilder()
    holder = builder.gen(mesh, cad.Transform())
    holder.close_bottom_face()
    holder.close_top_face()
    holder.close_left_face()
    holder.close_right_face()
    return blender_util.new_mesh_obj("socket_holder", mesh)
