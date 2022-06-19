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

    left_x = -5.3

    top_z = -thickness
    bottom_z = -thickness - socket_h

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
    right_x = 6.2

    def __init__(self, mesh: cad.Mesh) -> None:
        self.mesh = mesh
        self.b_arc_points: List[cad.MeshPoint] = []
        self.t_arc_points: List[cad.MeshPoint] = []

        SocketParams().assign_params_to(self)

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
        self.l_tl = self.mesh.add_xyz(self.left_x, 0.0, self.top_z)
        self.l_tr = self.mesh.add_xyz(self.left_x, self.edge_y, self.top_z)
        self.l_mr = self.mesh.add_xyz(self.left_x, self.edge_y, self.bottom_z)
        self.l_ml = self.mesh.add_xyz(self.left_x, 0, self.bottom_z)

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
        self.r_tl = self.mesh.add_xyz(self.right_x, 0.0, self.top_z)
        self.r_tr = self.mesh.add_xyz(self.right_x, right_y, self.top_z)
        self.r_mr = self.mesh.add_xyz(self.right_x, right_y, self.bottom_z)
        self.r_ml = self.mesh.add_xyz(self.right_x, 0, self.bottom_z)

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
            self.left_x, lip_bottom_y, self.lip_bottom_z
        )
        self.l_bl = self.mesh.add_xyz(self.left_x, 0, self.lip_bottom_z)

        self.mesh.add_quad(self.l_bl, self.l_br, self.m0_br, self.m0_bl)
        self.mesh.add_quad(self.m0_ml, self.l_ml, self.l_bl, self.m0_bl)
        self.mesh.add_quad(self.l_ml, self.l_mr, self.l_br, self.l_bl)

        self.l_lip0 = self.mesh.add_xyz(
            self.left_x, self.edge_y, self.bottom_z - 0.05
        )
        self.l_lip1 = self.mesh.add_xyz(
            self.left_x, self.edge_y - lip_protrusion, self.bottom_z - 0.13
        )
        self.l_lip2 = self.mesh.add_xyz(
            self.left_x, self.edge_y - lip_protrusion, self.bottom_z - 0.23
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
                    center_x + angle_x,
                    center_y + angle_y,
                    self.bottom_z,
                )
            )
            self.t_arc_points.append(
                self.mesh.add_xyz(
                    center_x + angle_x,
                    center_y + angle_y,
                    self.top_z,
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
        self.l_tl = self.mesh.add_xyz(self.left_x, self.l_y, self.top_z)
        self.l_tr = self.mesh.add_xyz(self.left_x, self.r_y, self.top_z)
        self.l_mr = self.mesh.add_xyz(self.left_x, self.r_y, self.bottom_z)
        self.l_ml = self.mesh.add_xyz(self.left_x, self.l_y, self.bottom_z)

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
            self.left_x, lip_bottom_y, self.lip_bottom_z
        )
        self.l_br = self.mesh.add_xyz(self.left_x, self.r_y, self.lip_bottom_z)

        self.mesh.add_quad(self.l_br, self.l_bl, self.l_ml, self.l_mr)

        mid0_x = self.b_arc_points[0].x
        self.m_bl = self.mesh.add_xyz(mid0_x, lip_bottom_y, self.lip_bottom_z)
        self.m_br = self.mesh.add_xyz(mid0_x, self.r_y, self.lip_bottom_z)

        self.mesh.add_quad(self.l_bl, self.l_br, self.m_br, self.m_bl)
        self.mesh.add_quad(self.m0_mr, self.m_br, self.l_br, self.l_mr)

        self.l_lip0 = self.mesh.add_xyz(
            self.left_x, self.l_y, self.bottom_z - 0.05
        )
        self.l_lip1 = self.mesh.add_xyz(
            self.left_x, self.l_y + lip_protrusion, self.bottom_z - 0.13
        )
        self.l_lip2 = self.mesh.add_xyz(
            self.left_x, self.l_y + lip_protrusion, self.bottom_z - 0.23
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

        self.diode_x = -6.35
        self.diode_y = 0.5
        self.top_y = self.diode_y - (self.diode_h * 0.5) - 0.5
        self.right_x = self.diode_x + 1.9

    def gen(self) -> None:
        m1_y = self.diode_y - (self.diode_h * 0.5)
        m2_y = self.diode_y + (self.diode_h * 0.5)
        b_y = m2_y + 0.5
        m_x = self.diode_x + (self.diode_w * 0.5)
        left_x = self.diode_x + 0.3

        b_tl = self.mesh.add_xyz(left_x, self.top_y, self.bottom_z)
        t_tl = self.mesh.add_xyz(left_x, self.top_y, self.top_z)

        b_l0 = self.mesh.add_xyz(left_x, m1_y, self.bottom_z)
        t_l0 = self.mesh.add_xyz(left_x, m1_y, self.top_z)

        b_l1 = self.mesh.add_xyz(m_x, m1_y, self.bottom_z)
        t_l1 = self.mesh.add_xyz(m_x, m1_y, self.top_z)

        b_l2 = self.mesh.add_xyz(m_x, m2_y, self.bottom_z)
        t_l2 = self.mesh.add_xyz(m_x, m2_y, self.top_z)

        b_l3 = self.mesh.add_xyz(left_x, m2_y, self.bottom_z)
        t_l3 = self.mesh.add_xyz(left_x, m2_y, self.top_z)

        b_tr = self.mesh.add_xyz(self.right_x, self.top_y, self.bottom_z)
        t_tr = self.mesh.add_xyz(self.right_x, self.top_y, self.top_z)

        b_br = self.mesh.add_xyz(self.right_x, b_y, self.bottom_z)
        t_br = self.mesh.add_xyz(self.right_x, b_y, self.top_z)

        b_bl = self.mesh.add_xyz(left_x, b_y, self.bottom_z)
        t_bl = self.mesh.add_xyz(left_x, b_y, self.top_z)

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


class SocketHolder:
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
        dz = -params.thickness * 0.5
        full_size = 17.4

        w = 14.9
        h = 6
        obj = blender_cube(w, h, params.thickness, name="socket_holder")
        with blender_util.TransformContext(obj) as ctx:
            dx = (-full_size * 0.5) + (w * 0.5)
            dy = -2.8 + (h * 0.5)
            ctx.translate(dx, dy, dz)

        w = 11.5
        vert = blender_cube(w, full_size, params.thickness, name="vert")
        with blender_util.TransformContext(vert) as ctx:
            dx = -5.3 + (w * 0.5)
            ctx.translate(dx, 0, -params.thickness * 0.5)

        w = 0.6
        h = 3.7
        upper_r = blender_cube(w, h, params.thickness, name="upper_right")
        with blender_util.TransformContext(upper_r) as ctx:
            dx = 6.2 + (w * 0.5)
            dy = (-full_size * 0.5) + (h * 0.5)
            ctx.translate(dx, dy, -params.thickness * 0.5)

        h = 6
        horiz = blender_cube(full_size, h, params.thickness, name="horiz")
        with blender_util.TransformContext(horiz) as ctx:
            dy = -1 + (h * 0.5)
            ctx.translate(0, dy, -params.thickness * 0.5)

        blender_util.union(obj, vert)
        blender_util.union(obj, upper_r)
        blender_util.union(obj, horiz)

        return obj


def clip_bottom_main() -> bpy.types.Object:
    thickness = 1.0
    socket_h = 2.0

    lip_bottom_h = socket_h + 0.05
    lip_tip_bottom_h = socket_h + 0.134
    lip_tip_top_h = lip_tip_bottom_h + 0.1
    lip_top_h = 2.55

    left_x = -5.3
    right_x = 0.4

    mesh = cad.Mesh()
    points = [
        (-2.5233, lip_top_h),
        (0, lip_top_h),
        (0, -0.1),
        (-2.8, -0.1),
        (-2.8, lip_bottom_h),
        (-2.9, lip_tip_bottom_h),
        (-2.9, lip_tip_top_h),
    ]

    left_points: List[cad.MeshPoint] = []
    right_points: List[cad.MeshPoint] = []
    for (y, z) in points:
        l = mesh.add_xyz(left_x, y, -thickness - z)
        left_points.append(l)
        r = mesh.add_xyz(right_x, y, -thickness - z)
        right_points.append(r)

    for idx in range(len(left_points) - 2):
        mesh.add_tri(
            left_points[0], left_points[idx + 1], left_points[idx + 2]
        )
        mesh.add_tri(
            right_points[0], right_points[idx + 2], right_points[idx + 1]
        )

    for idx in range(len(left_points)):
        next_idx = idx + 1
        if next_idx >= len(left_points):
            next_idx = 0
        mesh.add_quad(
            right_points[idx],
            right_points[next_idx],
            left_points[next_idx],
            left_points[idx],
        )

    obj = blender_util.new_mesh_obj("clip_bottom", mesh)

    cyl_h = 2.0
    cyl = blender_cylinder(r=1.8, h=cyl_h, fn=23, rotation=90.0)
    with blender_util.TransformContext(cyl) as ctx:
        # ctx.rotate(-90.0, "Z")
        ctx.rotate(180.0, "X")
        ctx.translate(0.4, -1.0, -1.0 - cyl_h * 0.5)

    blender_util.union(obj, cyl)
    return obj


def socket_holder() -> bpy.types.Object:
    thickness = SocketParams.thickness

    left_x = -5.3

    # Base
    obj = SocketHolder().base_plate()

    top_clip = SocketHolder().top_clip()
    blender_util.union(obj, top_clip)
    bottom_clip = SocketHolder().bottom_clip()
    blender_util.union(obj, bottom_clip)
    diode_clip_right = SocketHolder().diode_clip_right()
    blender_util.union(obj, diode_clip_right)
    diode_clip_left = SocketHolder().diode_clip_left()
    blender_util.union(obj, diode_clip_left)

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


class SocketHolder2:
    """
    Logic to lay out the socket holder.

    This seems unfortunately labor-intensive and manual.  I first created this
    using union and difference operators, which was much simpler, but proved
    problematic when trying to combine around 50 of them into a connected grid.
    Blender tended to produced bad results when processing unions of many of
    them.  Manually constructing the faces was much more reliable.
    """
    z_top = 0.0
    z_bottom = -1.0

    y0 = 8.7
    y1 = 5
    y2 = 2.95
    y3 = -1
    y4 = -1.95
    y5 = -2.8
    y6 = -5
    y7 = -7.0
    y8 = -8.7

    x0 = -8.7
    x1 = -5.3
    x2 = 6.2
    x3 = 6.8
    x4 = 8.7
    main_hole_r = 2.1
    switch_hole_r = 1.6
    right_hole_x = 3.65
    right_hole_y = -2.7
    left_hole_x = -2.7
    left_hole_y = -5.2

    diode_x = -6.35
    diode_y = 0.5

    diode_w = 2.1
    diode_h = 3.9
    diode_outer_w = 3.8
    diode_outer_h = 4.9

    def __init__(self, mesh: cad.Mesh, transform: cad.Transform) -> None:
        self.mesh = mesh
        self.transform = transform

    def add_xyz(self, x: float, y: float, z: float) -> MeshPoint:
        p = cad.Point(x, y, z).transform(self.transform)
        return self.mesh.add_point(p)

    def gen(self) -> None:
        # Generate points for the holes
        # fn for the main hole must be divisible by 4
        self.main_hole_top, self.main_hole_bottom = self.gen_hole_points(self.main_hole_r, 0.0, 0.0, fn=100)
        self.right_hole_top, self.right_hole_bottom = self.gen_hole_points(self.switch_hole_r, self.right_hole_x, self.right_hole_y, fn=85)
        self.left_hole_top, self.left_hole_bottom = self.gen_hole_points(self.switch_hole_r, self.left_hole_x, self.left_hole_y, fn=85)

        self.gen_upper_surface()
        self.gen_side_faces()
        self.gen_diode_holder()
        self.gen_bottom_clip()
        self.gen_lower_surface()

        # Faces needed only if not connected to other sockets
        self.gen_top_face()
        self.gen_left_face()
        self.gen_bottom_face()
        self.gen_right_face()

    def gen_upper_surface(self) -> None:
        # top face point naming is grid-based.  tCR, where C is the column
        # number, R is the row number

        self.t10 = self.add_xyz(self.x1, self.y0, self.z_top)
        self.t20 = self.add_xyz(self.x2, self.y0, self.z_top)
        self.t11 = self.add_xyz(self.x1, self.y1, self.z_top)
        self.t21 = self.add_xyz(self.x2, self.y1, self.z_top)

        self.mesh.add_quad(self.t10, self.t20, self.t21, self.t11)

        self.t01 = self.add_xyz(self.x0, self.y1, self.z_top)
        self.t05 = self.add_xyz(self.x0, self.y5, self.z_top)
        self.t15 = self.add_xyz(self.x1, self.y5, self.z_top)

        self.mesh.add_quad(self.t01, self.t11, self.t15, self.t05)

        self.t21 = self.add_xyz(self.x2, self.y1, self.z_top)
        self.t41 = self.add_xyz(self.x4, self.y1, self.z_top)
        self.t23 = self.add_xyz(self.x2, self.y3, self.z_top)
        self.t43 = self.add_xyz(self.x4, self.y3, self.z_top)

        self.mesh.add_quad(self.t21, self.t41, self.t43, self.t23)

        self.t26 = self.add_xyz(self.x2, self.y6, self.z_top)
        self.t36 = self.add_xyz(self.x3, self.y6, self.z_top)
        self.t28 = self.add_xyz(self.x2, self.y8, self.z_top)
        self.t38 = self.add_xyz(self.x3, self.y8, self.z_top)

        self.mesh.add_quad(self.t26, self.t36, self.t38, self.t28)

        # Points from main hole to top-right corner
        main_top_right_end = int(len(self.main_hole_top) * 0.25)
        for n in range(0, main_top_right_end):
            self.mesh.add_tri(self.t21, self.main_hole_top[n + 1], self.main_hole_top[n])

        self.mesh.add_tri(self.t21, self.right_hole_top[0], self.main_hole_top[main_top_right_end])

        # Points from right hole to top-right corner
        right_top_right_0 = int(len(self.right_hole_top) * 0.15)
        for n in range(0, right_top_right_0):
            self.mesh.add_tri(self.t21, self.right_hole_top[n + 1], self.right_hole_top[n])

        # Points from right hole to mid right
        right_top_right_1 = int(len(self.right_hole_top) * 0.25)
        for n in range(right_top_right_0, right_top_right_1):
            self.mesh.add_tri(self.t23, self.right_hole_top[n + 1], self.right_hole_top[n])

        self.mesh.add_tri(self.t21, self.t23, self.right_hole_top[right_top_right_0])

        # Points from right hole to bottom right corner
        right_bottom = int(len(self.right_hole_top) * 0.5)
        for n in range(right_top_right_1, right_bottom):
            self.mesh.add_tri(self.t26, self.right_hole_top[n + 1], self.right_hole_top[n])

        self.mesh.add_tri(self.t23, self.t26, self.right_hole_top[right_top_right_1])
        self.mesh.add_tri(self.right_hole_top[right_bottom], self.t26, self.t28)

        self.t_mid = self.add_xyz(0, -7.5, self.z_top)
        self.t18 = self.add_xyz(self.x1, self.y8, self.z_top)

        # Points from right hole to mid point
        right_left = int(len(self.right_hole_top) * 0.75)
        for n in range(right_bottom, right_left):
            self.mesh.add_tri(self.t_mid, self.right_hole_top[n + 1], self.right_hole_top[n])

        # triangles between main hole and right hole
        n_right = len(self.right_hole_top) - 1
        n_main = main_top_right_end
        self.mesh.add_tri(self.main_hole_top[n_main], self.right_hole_top[0], self.right_hole_top[n_right])
        while n_right > right_left:
            self.mesh.add_tri(self.main_hole_top[n_main], self.right_hole_top[n_right], self.main_hole_top[n_main + 1])
            self.mesh.add_tri(self.main_hole_top[n_main + 1], self.right_hole_top[n_right], self.right_hole_top[n_right - 1])
            n_main += 1
            n_right -= 1

        self.mesh.add_tri(self.main_hole_top[n_main], self.right_hole_top[right_left], self.t_mid)
        self.mesh.add_tri(self.right_hole_top[right_bottom], self.t28, self.t_mid)

        self.mesh.add_tri(self.t18, self.t_mid, self.t28)

        # triangles between main hole and left hole
        left_right = int(len(self.left_hole_top) * 0.25)
        n_left = left_right
        main_left = int(len(self.main_hole_top) * 0.75)
        self.mesh.add_tri(self.left_hole_top[n_left], self.main_hole_top[n_main], self.t_mid)
        while n_main < main_left:
            self.mesh.add_tri(self.main_hole_top[n_main], self.left_hole_top[n_left], self.main_hole_top[n_main + 1])
            self.mesh.add_tri(self.main_hole_top[n_main + 1], self.left_hole_top[n_left], self.left_hole_top[n_left - 1])
            n_main += 1
            n_left -= 1
            if n_left < 0:
                n_left += len(self.left_hole_top)

        self.mesh.add_tri(self.t15, self.main_hole_top[n_main], self.left_hole_top[n_left])
        self.mesh.add_tri(self.t15, self.t11, self.main_hole_top[n_main])

        # Points from main hole to top_left
        for n in range(n_main, len(self.main_hole_top) - 1):
            self.mesh.add_tri(self.t11, self.main_hole_top[n + 1], self.main_hole_top[n])
        self.mesh.add_tri(self.t11, self.main_hole_top[0], self.main_hole_top[n])

        self.mesh.add_tri(self.t11, self.t21, self.main_hole_top[0])

        # Points from left hole to left mid
        left_left = int(len(self.left_hole_top) * 0.75)
        for n in range(left_left, n_left):
            self.mesh.add_tri(self.t15, self.left_hole_top[n + 1], self.left_hole_top[n])

        self.mesh.add_tri(self.t18, self.t15, self.left_hole_top[left_left])

        # Points from left hole to left bottom
        left_bottom = int(len(self.left_hole_top) * 0.5)
        for n in range(left_bottom, left_left):
            self.mesh.add_tri(self.t18, self.left_hole_top[n + 1], self.left_hole_top[n])

        self.mesh.add_tri(self.t18, self.left_hole_top[left_bottom], self.t_mid)

        # Points from left hole to mid
        for n in range(left_right, left_bottom):
            self.mesh.add_tri(self.t_mid, self.left_hole_top[n + 1], self.left_hole_top[n])

    def gen_hole_points(self, r: float, x: float, y: float, fn: int) -> None:
        top_points: List[cad.MeshPoint] = []
        bottom_points: List[cad.MeshPoint] = []
        two_pi = math.pi * 2.0
        for n in range(fn):
            angle = (two_pi / fn) * n
            circle_x = (math.sin(angle) * r) + x
            circle_y = (math.cos(angle) * r) + y

            t = self.add_xyz(circle_x, circle_y, self.z_top)
            b = self.add_xyz(circle_x, circle_y, self.z_bottom)

            top_points.append(t)
            bottom_points.append(b)

        return top_points, bottom_points

    def gen_top_face(self) -> None:
        # Generate the top face needed if we are not connected to another
        # socket above.
        self.mesh.add_quad(self.t20, self.t10, self.b10, self.b20)

    def gen_left_face(self) -> None:
        # Generate the left face needed if we are not connected to another
        # socket to the left.
        self.mesh.add_quad(self.t01, self.t05, self.b05, self.b01)

    def gen_bottom_face(self) -> None:
        # Generate the bottom face needed if we are not connected to another
        # socket below.
        self.mesh.add_quad(self.t18, self.t28, self.b28, self.b18)
        self.mesh.add_quad(self.t28, self.t38, self.b38, self.b28)

    def gen_right_face(self) -> None:
        # Generate the right face needed if we are not connected to another
        # socket to the right.
        self.mesh.add_quad(self.t43, self.t41, self.b41, self.b43)

    def gen_side_faces(self) -> None:
        self.b10 = self.add_xyz(self.x1, self.y0, self.z_bottom)
        self.b20 = self.add_xyz(self.x2, self.y0, self.z_bottom)
        self.b11 = self.add_xyz(self.x1, self.y1, self.z_bottom)
        self.b21 = self.add_xyz(self.x2, self.y1, self.z_bottom)

        self.mesh.add_quad(self.t10, self.t11, self.b11, self.b10)

        self.b01 = self.add_xyz(self.x0, self.y1, self.z_bottom)
        self.b05 = self.add_xyz(self.x0, self.y5, self.z_bottom)
        self.b15 = self.add_xyz(self.x1, self.y5, self.z_bottom)

        self.mesh.add_quad(self.t11, self.t01, self.b01, self.b11)
        self.mesh.add_quad(self.t05, self.t15, self.b15, self.b05)

        self.b17 = self.add_xyz(self.x1, self.y7, self.z_bottom)
        self.b18 = self.add_xyz(self.x1, self.y8, self.z_bottom)
        self.mesh.add_quad(self.t15, self.t18, self.b17, self.b15)
        self.mesh.add_tri(self.b18, self.b17, self.t18)

        self.b26 = self.add_xyz(self.x2, self.y6, self.z_bottom)
        self.b36 = self.add_xyz(self.x3, self.y6, self.z_bottom)
        self.b28 = self.add_xyz(self.x2, self.y8, self.z_bottom)
        self.b38 = self.add_xyz(self.x3, self.y8, self.z_bottom)
        self.mesh.add_quad(self.t38, self.t36, self.b36, self.b38)
        self.mesh.add_quad(self.t36, self.t26, self.b26, self.b36)

        self.b23 = self.add_xyz(self.x2, self.y3, self.z_bottom)
        self.mesh.add_quad(self.t26, self.t23, self.b23, self.b26)
        self.b43 = self.add_xyz(self.x4, self.y3, self.z_bottom)
        self.mesh.add_quad(self.t23, self.t43, self.b43, self.b23)

        self.b21 = self.add_xyz(self.x2, self.y1, self.z_bottom)
        self.b41 = self.add_xyz(self.x4, self.y1, self.z_bottom)

        self.mesh.add_quad(self.t41, self.t21, self.b21, self.b41)

        self.b20 = self.add_xyz(self.x2, self.y0, self.z_bottom)
        self.mesh.add_quad(self.t21, self.t20, self.b20, self.b21)

    def gen_diode_holder(self) -> None:
        self.z_diode_bottom = -3.0
        wire_gap_width = 0.6

        # top outer top left
        self.diode_totl = self.add_xyz(self.diode_x + (self.diode_outer_w * 0.5), self.diode_y + (self.diode_outer_h * 0.5), self.z_bottom)
        # top outer mid left
        self.diode_toml = self.add_xyz(self.diode_x + (self.diode_outer_w * 0.5), 0.0, self.z_bottom)
        # top outer top mid-left
        self.diode_totml = self.add_xyz(self.diode_x + (wire_gap_width * 0.5), self.diode_y + (self.diode_outer_h * 0.5), self.z_bottom)
        self.diode_totmr = self.add_xyz(self.diode_x - (wire_gap_width * 0.5), self.diode_y + (self.diode_outer_h * 0.5), self.z_bottom)
        self.diode_totr = self.add_xyz(self.diode_x - (self.diode_outer_w * 0.5), self.diode_y + (self.diode_outer_h * 0.5), self.z_bottom)
        self.diode_tobr = self.add_xyz(self.diode_x - (self.diode_outer_w * 0.5), self.diode_y - (self.diode_outer_h * 0.5), self.z_bottom)
        self.diode_tobmr = self.add_xyz(self.diode_x - (wire_gap_width * 0.5), self.diode_y - (self.diode_outer_h * 0.5), self.z_bottom)
        self.diode_tobml = self.add_xyz(self.diode_x + (wire_gap_width * 0.5), self.diode_y - (self.diode_outer_h * 0.5), self.z_bottom)
        # Note, the outer bottom left is actually at the same x location as
        # the inner bottom leftj
        self.diode_tobl = self.add_xyz(self.diode_x + (self.diode_w * 0.5), self.diode_y - (self.diode_outer_h * 0.5), self.z_bottom)
        self.diode_tibmr = self.add_xyz(self.diode_x - (wire_gap_width * 0.5), self.diode_y - (self.diode_h * 0.5), self.z_bottom)
        self.diode_tibml = self.add_xyz(self.diode_x + (wire_gap_width * 0.5), self.diode_y - (self.diode_h * 0.5), self.z_bottom)
        self.diode_tibl = self.add_xyz(self.diode_x + (self.diode_w * 0.5), self.diode_y - (self.diode_h * 0.5), self.z_bottom)
        self.diode_tibr = self.add_xyz(self.diode_x - (self.diode_w * 0.5), self.diode_y - (self.diode_h * 0.5), self.z_bottom)
        self.diode_titr = self.add_xyz(self.diode_x - (self.diode_w * 0.5), self.diode_y + (self.diode_h * 0.5), self.z_bottom)

        self.diode_titml = self.add_xyz(self.diode_x + (wire_gap_width * 0.5), self.diode_y + (self.diode_h * 0.5), self.z_bottom)
        self.diode_titmr = self.add_xyz(self.diode_x - (wire_gap_width * 0.5), self.diode_y + (self.diode_h * 0.5), self.z_bottom)
        self.diode_titl = self.add_xyz(self.diode_x + (self.diode_w * 0.5), self.diode_y + (self.diode_h * 0.5), self.z_bottom)
        self.diode_timl = self.add_xyz(self.diode_x + (self.diode_w * 0.5), 0.0, self.z_bottom)

        self.diode_botl = self.add_xyz(self.diode_x + (self.diode_outer_w * 0.5), self.diode_y + (self.diode_outer_h * 0.5), self.z_diode_bottom)
        self.diode_boml = self.add_xyz(self.diode_x + (self.diode_outer_w * 0.5), 0, self.z_diode_bottom)
        self.diode_botml = self.add_xyz(self.diode_x + (wire_gap_width * 0.5), self.diode_y + (self.diode_outer_h * 0.5), self.z_diode_bottom)
        self.diode_botmr = self.add_xyz(self.diode_x - (wire_gap_width * 0.5), self.diode_y + (self.diode_outer_h * 0.5), self.z_diode_bottom)
        self.diode_botr = self.add_xyz(self.diode_x - (self.diode_outer_w * 0.5), self.diode_y + (self.diode_outer_h * 0.5), self.z_diode_bottom)
        self.diode_bobr = self.add_xyz(self.diode_x - (self.diode_outer_w * 0.5), self.diode_y - (self.diode_outer_h * 0.5), self.z_diode_bottom)
        self.diode_bobmr = self.add_xyz(self.diode_x - (wire_gap_width * 0.5), self.diode_y - (self.diode_outer_h * 0.5), self.z_diode_bottom)
        self.diode_bobml = self.add_xyz(self.diode_x + (wire_gap_width * 0.5), self.diode_y - (self.diode_outer_h * 0.5), self.z_diode_bottom)
        self.diode_bobl = self.add_xyz(self.diode_x + (self.diode_w * 0.5), self.diode_y - (self.diode_outer_h * 0.5), self.z_diode_bottom)
        self.diode_bibmr = self.add_xyz(self.diode_x - (wire_gap_width * 0.5), self.diode_y - (self.diode_h * 0.5), self.z_diode_bottom)
        self.diode_bibml = self.add_xyz(self.diode_x + (wire_gap_width * 0.5), self.diode_y - (self.diode_h * 0.5), self.z_diode_bottom)
        self.diode_bibl = self.add_xyz(self.diode_x + (self.diode_w * 0.5), self.diode_y - (self.diode_h * 0.5), self.z_diode_bottom)
        self.diode_bibr = self.add_xyz(self.diode_x - (self.diode_w * 0.5), self.diode_y - (self.diode_h * 0.5), self.z_diode_bottom)
        self.diode_bitr = self.add_xyz(self.diode_x - (self.diode_w * 0.5), self.diode_y + (self.diode_h * 0.5), self.z_diode_bottom)

        self.diode_bitml = self.add_xyz(self.diode_x + (wire_gap_width * 0.5), self.diode_y + (self.diode_h * 0.5), self.z_diode_bottom)
        self.diode_bitmr = self.add_xyz(self.diode_x - (wire_gap_width * 0.5), self.diode_y + (self.diode_h * 0.5), self.z_diode_bottom)
        self.diode_bitl = self.add_xyz(self.diode_x + (self.diode_w * 0.5), self.diode_y + (self.diode_h * 0.5), self.z_diode_bottom)
        self.diode_biml = self.add_xyz(self.diode_x + (self.diode_w * 0.5), 0.0, self.z_diode_bottom)

        # Vertical walls on left top side
        self.mesh.add_quad(self.diode_totl, self.diode_botl, self.diode_boml, self.diode_toml)
        self.mesh.add_quad(self.diode_totl, self.diode_totml, self.diode_botml, self.diode_botl)
        self.mesh.add_quad(self.diode_bitml, self.diode_botml, self.diode_totml, self.diode_titml)
        self.mesh.add_quad(self.diode_bitl, self.diode_bitml, self.diode_titml, self.diode_titl)
        self.mesh.add_quad(self.diode_biml, self.diode_bitl, self.diode_titl, self.diode_timl)
        # Bottom walls on left top side
        self.mesh.add_quad(self.diode_boml, self.diode_botl, self.diode_bitl, self.diode_biml)
        self.mesh.add_quad(self.diode_botl, self.diode_botml, self.diode_bitml, self.diode_bitl)

        # Vertical walls on left bottom side
        self.mesh.add_quad(self.diode_bibml, self.diode_bibl, self.diode_tibl, self.diode_tibml)
        self.mesh.add_quad(self.diode_bobml, self.diode_bibml, self.diode_tibml, self.diode_tobml)
        self.mesh.add_quad(self.diode_bobl, self.diode_bobml, self.diode_tobml, self.diode_tobl)
        self.mesh.add_quad(self.diode_bibl, self.diode_biml, self.diode_timl, self.diode_tibl)
        # Bottom wall on left bottom side
        self.mesh.add_quad(self.diode_bobl, self.diode_bibl, self.diode_bibml, self.diode_bobml)

        # Vertical walls on right side
        self.mesh.add_quad(self.diode_botr, self.diode_botmr, self.diode_totmr, self.diode_totr)
        self.mesh.add_quad(self.diode_bobr, self.diode_botr, self.diode_totr, self.diode_tobr)
        self.mesh.add_quad(self.diode_bobmr, self.diode_bobr, self.diode_tobr, self.diode_tobmr)
        self.mesh.add_quad(self.diode_bibmr, self.diode_bobmr, self.diode_tobmr, self.diode_tibmr)
        self.mesh.add_quad(self.diode_bibr, self.diode_bibmr, self.diode_tibmr, self.diode_tibr)
        self.mesh.add_quad(self.diode_bitr, self.diode_bibr, self.diode_tibr, self.diode_titr)
        self.mesh.add_quad(self.diode_bitmr, self.diode_bitr, self.diode_titr, self.diode_titmr)
        self.mesh.add_quad(self.diode_botmr, self.diode_bitmr, self.diode_titmr, self.diode_totmr)
        # Bottom walls on right side
        self.mesh.add_quad(self.diode_botmr, self.diode_botr, self.diode_bitr, self.diode_bitmr)
        self.mesh.add_quad(self.diode_botr, self.diode_bobr, self.diode_bibr, self.diode_bitr)
        self.mesh.add_quad(self.diode_bibmr, self.diode_bibr, self.diode_bobr, self.diode_bobmr)

    def gen_bottom_clip(self) -> None:
        self.z_clip_bottom = -3.55
        self.z_clip_lower_bottom = -3.0
        self.z_clip_lip_base = -3.05
        self.z_clip_lip_top = -3.13
        self.z_clip_lip_bottom = -3.23

        self.cb18 = self.add_xyz(self.x1, self.y8, self.z_clip_bottom)
        self.c17_0 = self.add_xyz(self.x1, self.y7, self.z_clip_lower_bottom)
        self.c17_1 = self.add_xyz(self.x1, self.y7, self.z_clip_lip_base)
        self.c17_2 = self.add_xyz(self.x1, self.y7 + 0.1, self.z_clip_lip_top)
        self.c17_3 = self.add_xyz(self.x1, self.y7 + 0.1, self.z_clip_lip_bottom)
        self.cb17 = self.add_xyz(self.x1, -7.28, self.z_clip_bottom)
        self.mesh.add_quad(self.cb18, self.c17_0, self.b17, self.b18)
        self.mesh.add_tri(self.cb18, self.c17_1, self.c17_0)
        self.mesh.add_tri(self.cb18, self.cb17, self.c17_1)
        self.mesh.add_tri(self.cb17, self.c17_3, self.c17_2)
        self.mesh.add_tri(self.cb17, self.c17_2, self.c17_1)

        x_end = 4.2
        self.bx7 = self.add_xyz(x_end, self.y7, self.z_bottom)
        self.cx7_0 = self.add_xyz(x_end, self.y7, self.z_clip_lower_bottom)
        self.cx7_1 = self.add_xyz(x_end, self.y7, self.z_clip_lip_base)
        self.cx7_2 = self.add_xyz(x_end, self.y7 + 0.1, self.z_clip_lip_top)
        self.cx7_3 = self.add_xyz(x_end, self.y7 + 0.1, self.z_clip_lip_bottom)
        self.cbx7 = self.add_xyz(x_end, -7.28, self.z_clip_bottom)
        self.cbx8 = self.add_xyz(x_end, self.y8, self.z_clip_bottom)
        self.mesh.add_quad(self.c17_1, self.cx7_1, self.cx7_0, self.c17_0)
        self.mesh.add_quad(self.c17_0, self.cx7_0, self.bx7, self.b17)
        self.mesh.add_quad(self.c17_2, self.cx7_2, self.cx7_1, self.c17_1)
        self.mesh.add_quad(self.c17_3, self.cx7_3, self.cx7_2, self.c17_2)
        self.mesh.add_quad(self.cb17, self.cbx7, self.cx7_3, self.c17_3)
        self.mesh.add_quad(self.cb18, self.cbx8, self.cbx7, self.cb17)

        # bottom vertical face
        self.cx8_0 = self.add_xyz(x_end, self.y8, self.z_clip_lower_bottom)
        self.c38_0 = self.add_xyz(self.x3, self.y8, self.z_clip_lower_bottom)
        self.mesh.add_tri(self.b18, self.b38, self.cx8_0)
        self.mesh.add_tri(self.c38_0, self.cx8_0, self.b38)
        self.mesh.add_quad(self.cbx8, self.cb18, self.b18, self.cx8_0)

        self.mesh.add_quad(self.cx7_1, self.cbx8, self.cx8_0, self.cx7_0)
        self.mesh.add_tri(self.cbx7, self.cbx8, self.cx7_1)
        self.mesh.add_tri(self.cbx7, self.cx7_1, self.cx7_2)
        self.mesh.add_tri(self.cbx7, self.cx7_2, self.cx7_3)

        self.mesh.add_tri(self.cx7_0, self.cx8_0, self.c38_0)

    def gen_lower_surface(self) -> None:
        self.mesh.add_quad(self.b20, self.b10, self.b11, self.b21)

        self.b22_5 = self.add_xyz(self.x2, self.y3 + 1.0, self.z_bottom)
        self.mesh.add_quad(self.b41, self.b21, self.b22_5, self.b43)
        self.mesh.add_tri(self.b43, self.b22_5, self.b23)

        main_right = int(len(self.main_hole_bottom) * 0.25)
        self.mesh.add_tri(self.b21, self.main_hole_bottom[main_right], self.b22_5)

        # Points from the main hole to the top right
        for n in range(0, main_right):
            self.mesh.add_tri(self.b21, self.main_hole_bottom[n], self.main_hole_bottom[n + 1])

        self.mesh.add_tri(self.b21, self.b01, self.main_hole_bottom[0])

        main_left = int(len(self.main_hole_bottom) * 0.75)
        # Points from the main hole to the top right
        for n in range(main_left, len(self.main_hole_bottom) - 1):
            self.mesh.add_tri(self.diode_totl, self.main_hole_bottom[n], self.main_hole_bottom[n + 1])
        self.mesh.add_tri(self.diode_totl, self.main_hole_bottom[-1], self.main_hole_bottom[0])
        self.mesh.add_tri(self.diode_totl, self.main_hole_bottom[0], self.b01)

        self.mesh.add_tri(self.diode_totl, self.diode_toml, self.main_hole_bottom[main_left])
        self.mesh.add_tri(self.b01, self.diode_totml, self.diode_totl)
        self.mesh.add_tri(self.b01, self.diode_totmr, self.diode_totml)
        self.mesh.add_tri(self.b01, self.diode_totr, self.diode_totmr)
        self.mesh.add_quad(self.b01, self.b05, self.diode_tobr, self.diode_totr)

        self.mesh.add_quad(self.b05, self.b15, self.diode_tobmr, self.diode_tobr)
        self.mesh.add_tri(self.b15, self.diode_tobml, self.diode_tobmr)
        self.mesh.add_tri(self.b15, self.diode_tobl, self.diode_tobml)

        self.mesh.add_quad(self.diode_totml, self.diode_totmr, self.diode_titmr, self.diode_titml)
        self.mesh.add_quad(self.diode_tibml, self.diode_tibmr, self.diode_tobmr, self.diode_tobml)
        self.mesh.add_tri(self.diode_timl, self.diode_titl, self.diode_titml)
        self.mesh.add_tri(self.diode_timl, self.diode_titml, self.diode_titr)
        self.mesh.add_tri(self.diode_timl, self.diode_titr, self.diode_tibr)
        self.mesh.add_tri(self.diode_timl, self.diode_tibr, self.diode_tibmr)
        self.mesh.add_tri(self.diode_timl, self.diode_tibmr, self.diode_tibml)
        self.mesh.add_tri(self.diode_timl, self.diode_tibml, self.diode_tibl)


def socket_holder2() -> bpy.types.Object:
    mesh = cad.Mesh()
    transform = cad.Transform()
    SocketHolder2(mesh, transform).gen()
    return blender_util.new_mesh_obj("socket_holder2", mesh)
