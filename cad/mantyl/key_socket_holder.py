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


class TopClip:
    thickness = 1.0
    socket_h = 2.0

    lip_bottom_h = socket_h + 0.05
    lip_tip_bottom_h = socket_h + 0.134
    lip_tip_top_h = lip_tip_bottom_h + 0.1
    lip_top_h = 2.55

    top_z = -thickness
    bottom_z = -thickness - socket_h
    lip_bottom_z = -thickness - socket_h - 0.55

    arc_x = 0.4
    arc_r = 1.8
    edge_y = -2.8

    left_x = -5.3
    mid0_x = arc_x - 0.2

    def __init__(self, mesh: cad.Mesh) -> None:
        self.mesh = mesh
        self.b_arc_points: List[cad.MeshPoint] = []
        self.t_arc_points: List[cad.MeshPoint] = []

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

        right_x = 7.7
        right_y = self.edge_y + self.arc_r
        self.r_tl = self.mesh.add_xyz(right_x, 0.0, self.top_z)
        self.r_tr = self.mesh.add_xyz(right_x, right_y, self.top_z)
        self.r_mr = self.mesh.add_xyz(right_x, right_y, self.bottom_z)
        self.r_ml = self.mesh.add_xyz(right_x, 0, self.bottom_z)

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
    thickness = 1.0
    socket_h = 2.0

    diode_x = 8.0
    diode_y = -6.55

    diode_w = 2.0
    diode_h = 3.9

    top_z = -thickness
    bottom_z = -thickness - socket_h
    lip_bottom_z = -thickness - socket_h - 0.55

    left_x = -5.3
    l_y = -7.0
    r_y = -9.0

    def __init__(self, mesh: cad.Mesh) -> None:
        self.mesh = mesh
        self.b_arc_points: List[cad.MeshPoint] = []
        self.t_arc_points: List[cad.MeshPoint] = []

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

        m_x = self.diode_x - (self.diode_w * 0.5)
        m1_y = self.diode_y - (self.diode_h * 0.5)
        m2_y = self.diode_y + (self.diode_h * 0.5)
        m1 = self.mesh.add_xyz(m_x, m1_y, self.bottom_z)
        t1 = self.mesh.add_xyz(m_x, m1_y, self.top_z)
        m2 = self.mesh.add_xyz(m_x, m2_y, self.bottom_z)
        t2 = self.mesh.add_xyz(m_x, m2_y, self.top_z)

        for n in range(8):
            self.mesh.add_tri(
                self.m0_mr, self.b_arc_points[n + 1], self.b_arc_points[n]
            )
            self.mesh.add_tri(
                self.m0_tr, self.t_arc_points[n], self.t_arc_points[n + 1]
            )

        for n in range(8, 16):
            self.mesh.add_tri(
                m1, self.b_arc_points[n + 1], self.b_arc_points[n]
            )
            self.mesh.add_tri(
                t1, self.t_arc_points[n], self.t_arc_points[n + 1]
            )

        for n in range(16, len(self.b_arc_points) - 1):
            self.mesh.add_tri(
                m2, self.b_arc_points[n + 1], self.b_arc_points[n]
            )
            self.mesh.add_tri(
                t2, self.t_arc_points[n], self.t_arc_points[n + 1]
            )

        self.mesh.add_tri(self.m0_mr, m1, self.b_arc_points[8])
        self.mesh.add_tri(self.m0_tr, self.t_arc_points[8], t1)
        self.mesh.add_tri(m1, m2, self.b_arc_points[16])
        self.mesh.add_tri(t1, self.t_arc_points[16], t2)

        br0 = self.mesh.add_xyz(self.diode_x - 0.3, self.r_y, self.bottom_z)
        tr0 = self.mesh.add_xyz(self.diode_x - 0.3, self.r_y, self.top_z)
        br1 = self.mesh.add_xyz(self.diode_x - 0.3, m1_y, self.bottom_z)
        tr1 = self.mesh.add_xyz(self.diode_x - 0.3, m1_y, self.top_z)

        br2 = self.mesh.add_xyz(self.diode_x - 0.3, m2_y, self.bottom_z)
        tr2 = self.mesh.add_xyz(self.diode_x - 0.3, m2_y, self.top_z)

        l2_y = self.diode_y + (self.diode_h * 0.5) + 0.5
        br3 = self.mesh.add_xyz(self.diode_x - 0.3, l2_y, self.bottom_z)
        tr3 = self.mesh.add_xyz(self.diode_x - 0.3, l2_y, self.top_z)

        br4 = self.mesh.add_xyz(self.b_arc_points[-1].x, l2_y, self.bottom_z)
        tr4 = self.mesh.add_xyz(self.t_arc_points[-1].x, l2_y, self.top_z)

        self.mesh.add_tri(br0, m1, self.m0_mr)
        self.mesh.add_tri(tr0, self.m0_tr, t1)
        self.mesh.add_tri(br0, br1, m1)
        self.mesh.add_tri(tr0, t1, tr1)

        self.mesh.add_quad(br0, self.m0_mr, self.m0_tr, tr0)
        self.mesh.add_quad(br1, br0, tr0, tr1)

        self.mesh.add_quad(m1, br1, tr1, t1)
        self.mesh.add_quad(m2, m1, t1, t2)

        self.mesh.add_quad(br2, m2, t2, tr2)
        self.mesh.add_quad(br3, br2, tr2, tr3)
        self.mesh.add_quad(br4, br3, tr3, tr4)
        self.mesh.add_quad(
            self.b_arc_points[-1], br4, tr4, self.t_arc_points[-1]
        )

        self.mesh.add_tri(self.b_arc_points[-1], m2, br4)
        self.mesh.add_tri(self.t_arc_points[-1], tr4, t2)
        self.mesh.add_tri(br4, m2, br3)
        self.mesh.add_tri(tr4, tr3, t2)
        self.mesh.add_tri(m2, br2, br3)
        self.mesh.add_tri(t2, tr3, tr2)

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


class SocketHolder:
    def top_clip(self) -> bpy.types.Object:
        mesh = cad.Mesh()
        top = TopClip(mesh)
        top.gen()

        return blender_util.new_mesh_obj("clip_top", mesh)

    def bottom_clip(self) -> bpy.types.Object:
        mesh = cad.Mesh()
        top = BottomClip(mesh)
        top.gen()

        return blender_util.new_mesh_obj("clip_bottom", mesh)


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


def socket_holder_obj() -> bpy.types.Object:
    width = 11.7
    height = 18.0
    thickness = 1.0

    left_x = -5.3

    # Base
    obj = blender_cube(width, height, thickness, name="socket_holder")
    with blender_util.TransformContext(obj) as ctx:
        ctx.translate(left_x + (width * 0.5), 0, -thickness * 0.5)

    top_clip = SocketHolder().top_clip()
    blender_util.union(obj, top_clip)
    bottom_clip = SocketHolder().bottom_clip()
    blender_util.union(obj, bottom_clip)

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


def socket_holder() -> bpy.types.Object:
    obj = socket_holder_obj()
    bpy.context.view_layer.objects.active = obj
