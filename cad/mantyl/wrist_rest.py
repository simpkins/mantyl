#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy
from typing import Dict, List, Optional, Sequence, Tuple

from bcad import cad
from bcad import blender_util
from .foot import add_foot
from .keyboard import Keyboard
from .screw_holes import gen_screw_hole

import math


class WristRestSimple:
    def __init__(self, kbd: Keyboard) -> None:
        self.depth = 70.0
        self.back_z_drop = 14
        self.mesh = cad.Mesh()
        self.kbd = kbd

        self.beveler = blender_util.Beveler()
        self.bevel_width = 8.0

        self.wall_thickness = 4.0

        self.gen_top_face()
        self.gen_thumb_connect()
        self.gen_inner_faces()
        self.gen_ground_faces()
        self.mark_bevels()

    def gen(self) -> bpy.types.Object:
        blend_mesh = blender_util.blender_mesh("wrist_rest_mesh", self.mesh)
        obj = blender_util.new_mesh_obj("wrist_rest", blend_mesh)

        self.beveler.apply_bevels(obj, width=self.bevel_width)

        self.add_feet(obj)
        self.add_screw_holes(obj)
        return obj

    def _bevel_edge(
        self, p0: cad.MeshPoint, p1: cad.MeshPoint, weight: float = 1.0
    ) -> None:
        self.beveler.bevel_edge(p0, p1, weight)

    def gen_top_face(self) -> None:
        fl = self.kbd.front_wall[1].out1
        fr = self.kbd.front_wall[-1].out1
        # Define the plane for the top face
        self.top_plane = cad.Plane(
            fl.point + cad.Point(0, 0, 5),
            fr.point,
            cad.Point(fr.x, fr.y - self.depth, fr.z - self.back_z_drop),
        )

        def top_point(p: cad.MeshPoint) -> cad.MeshPoint:
            return self.mesh.add_xyz(
                p.x, p.y, self.top_plane.z_intersect(p.x, p.y)
            )

        r_offset = 40

        self.bottom_tl = self.mesh.add_xyz(fl.x, fl.y, 0)
        self.bottom_tr = self.mesh.add_xyz(fr.x + r_offset, fr.y, 0)
        self.bottom_bl = self.mesh.add_xyz(fl.x, fl.y - self.depth, 0)
        self.bottom_br = self.mesh.add_xyz(
            fr.x + r_offset, fr.y - self.depth, 0
        )

        self.top_tl = top_point(self.bottom_tl)
        self.top_tr = top_point(self.bottom_tr)
        self.top_bl = top_point(self.bottom_bl)
        self.top_br = top_point(self.bottom_br)

        self.mesh.add_quad(self.top_tl, self.top_tr, self.top_br, self.top_bl)

        self.mesh.add_quad(
            self.top_bl, self.top_br, self.bottom_br, self.bottom_bl
        )
        self.mesh.add_quad(
            self.top_br, self.top_tr, self.bottom_tr, self.bottom_br
        )
        self.mesh.add_quad(
            self.top_tr, self.top_tl, self.bottom_tl, self.bottom_tr
        )

    def gen_thumb_connect(self) -> None:
        self.corner_tr = self.mesh.add_point(self.kbd.thumb_br_connect.point)
        self.corner_tl = self.mesh.add_point(self.kbd.thumb_wall[0].out1.point)
        self.mesh.add_tri(self.top_tl, self.top_bl, self.corner_tr)
        self.mesh.add_tri(self.corner_tl, self.corner_tr, self.top_bl)

        self.corner_bottom_tr = self.mesh.add_xyz(
            self.corner_tr.x, self.corner_tr.y, 0.0
        )
        self.corner_bottom_tl = self.mesh.add_xyz(
            self.corner_tl.x, self.corner_tl.y, 0.0
        )

        self.mesh.add_quad(
            self.top_tl, self.corner_tr, self.corner_bottom_tr, self.bottom_tl
        )
        self.mesh.add_quad(
            self.corner_tr,
            self.corner_tl,
            self.corner_bottom_tl,
            self.corner_bottom_tr,
        )
        self.mesh.add_quad(
            self.corner_tl, self.top_bl, self.bottom_bl, self.corner_bottom_tl
        )

    def gen_inner_faces(self) -> None:
        ground_plane = cad.Plane(
            cad.Point(0.0, 0.0, 0.0),
            cad.Point(1.0, 0.0, 0.0),
            cad.Point(0.0, 1.0, 0.0),
        )

        # Vertical wall planes, outer and inner
        vout_t = cad.Plane(
            self.top_tl.point, self.top_tr.point, self.bottom_tr.point
        )
        vin_t = vout_t.shifted_along_normal(self.wall_thickness)
        vout_r = cad.Plane(
            self.top_tr.point, self.top_br.point, self.bottom_br.point
        )
        vin_r = vout_r.shifted_along_normal(self.wall_thickness)
        vout_b = cad.Plane(
            self.top_br.point, self.top_bl.point, self.bottom_br.point
        )
        vin_b = vout_b.shifted_along_normal(self.wall_thickness)

        vout_thumb_b = cad.Plane(
            self.top_bl.point, self.corner_tl.point, self.bottom_bl.point
        )
        vin_thumb_b = vout_thumb_b.shifted_along_normal(self.wall_thickness)
        vout_thumb_t = cad.Plane(
            self.corner_tl.point,
            self.corner_tr.point,
            self.corner_bottom_tr.point,
        )
        vin_thumb_t = vout_thumb_t.shifted_along_normal(self.wall_thickness)

        # Top planes
        top_in_plane = self.top_plane.shifted_along_normal(
            -self.wall_thickness
        )
        top_thumb_l = cad.Plane(
            self.corner_tr.point, self.corner_tl.point, self.top_bl.point
        )
        top_in_thumb_l = top_thumb_l.shifted_along_normal(self.wall_thickness)
        top_thumb_r = cad.Plane(
            self.corner_tr.point, self.top_bl.point, self.top_tl.point
        )
        top_in_thumb_r = top_thumb_r.shifted_along_normal(self.wall_thickness)

        def intersect3(
            p0: cad.Plane, p1: cad.Plane, p2: cad.Plane
        ) -> cad.MeshPoint:
            """Create a MeshPoint at the intersection point of 3 planes."""
            line = p0.intersect_plane(p1)
            if line is None:
                raise Exception("planes a parallel")
            point = p2.intersect_line(line[0], line[1])
            if point is None:
                raise Exception("planes a parallel")
            return self.mesh.add_point(point)

        # Add the inner wall points
        self.in_top_tr = intersect3(vin_t, vin_r, top_in_plane)
        self.in_bottom_tr = intersect3(vin_t, vin_r, ground_plane)
        self.in_top_br = intersect3(vin_b, vin_r, top_in_plane)
        self.in_bottom_br = intersect3(ground_plane, vin_b, vin_r)

        self.in_bottom_bl = intersect3(vin_b, vin_thumb_b, ground_plane)
        self.in_top_bl = intersect3(vin_b, vin_thumb_b, top_in_plane)
        self.in_top_tl = intersect3(vin_t, top_in_thumb_r, top_in_plane)
        self.in_bottom_tl = self.mesh.add_xyz(
            self.in_top_tl.x, self.in_top_tl.y, 0.0
        )

        self.thumb_in_bottom_tl = intersect3(vin_t, vin_thumb_t, ground_plane)
        self.thumb_in_top_tl = intersect3(vin_t, vin_thumb_t, top_in_thumb_l)

        self.thumb_in_bottom_l = intersect3(
            vin_thumb_t, vin_thumb_b, ground_plane
        )
        self.thumb_in_top_l = intersect3(
            vin_thumb_t, vin_thumb_b, top_in_thumb_l
        )

        # Top inner wall
        self.mesh.add_quad(
            self.in_top_tr, self.in_top_tl, self.in_top_bl, self.in_top_br
        )

        # Inner right wall
        self.mesh.add_quad(
            self.in_top_tr,
            self.in_top_br,
            self.in_bottom_br,
            self.in_bottom_tr,
        )
        # Inner bottom wall
        self.mesh.add_quad(
            self.in_top_br,
            self.in_top_bl,
            self.in_bottom_bl,
            self.in_bottom_br,
        )
        # Inner top wall
        self.mesh.add_quad(
            self.in_top_tl,
            self.in_top_tr,
            self.in_bottom_tr,
            self.in_bottom_tl,
        )
        self.mesh.add_quad(
            self.in_top_tl,
            self.in_bottom_tl,
            self.thumb_in_bottom_tl,
            self.thumb_in_top_tl,
        )

        # Inner thumb top wall
        self.mesh.add_quad(
            self.thumb_in_top_l,
            self.thumb_in_top_tl,
            self.thumb_in_bottom_tl,
            self.thumb_in_bottom_l,
        )
        # Inner thumb bottom wall
        self.mesh.add_quad(
            self.in_top_bl,
            self.thumb_in_top_l,
            self.thumb_in_bottom_l,
            self.in_bottom_bl,
        )

        # Thumb top undersides
        self.mesh.add_tri(self.in_top_tl, self.thumb_in_top_tl, self.in_top_bl)
        self.mesh.add_tri(
            self.thumb_in_top_tl, self.thumb_in_top_l, self.in_top_bl
        )

    def gen_ground_faces(self) -> None:
        self.mesh.add_quad(
            self.thumb_in_bottom_tl,
            self.in_bottom_tl,
            self.bottom_tl,
            self.corner_bottom_tr,
        )
        self.mesh.add_quad(
            self.in_bottom_tl,
            self.in_bottom_tr,
            self.bottom_tr,
            self.bottom_tl,
        )
        self.mesh.add_quad(
            self.in_bottom_tr,
            self.in_bottom_br,
            self.bottom_br,
            self.bottom_tr,
        )
        self.mesh.add_quad(
            self.in_bottom_br,
            self.in_bottom_bl,
            self.bottom_bl,
            self.bottom_br,
        )
        self.mesh.add_quad(
            self.in_bottom_bl,
            self.thumb_in_bottom_l,
            self.corner_bottom_tl,
            self.bottom_bl,
        )
        self.mesh.add_quad(
            self.thumb_in_bottom_l,
            self.thumb_in_bottom_tl,
            self.corner_bottom_tr,
            self.corner_bottom_tl,
        )

    def mark_bevels(self) -> None:
        w_main = 0.5
        w_inner = 0.25

        self._bevel_edge(self.corner_tr, self.top_bl, w_main)
        self._bevel_edge(self.corner_tl, self.top_bl, w_main)
        self._bevel_edge(self.top_tl, self.top_bl, 1.0)
        self._bevel_edge(self.top_bl, self.bottom_bl, w_main)
        self._bevel_edge(self.top_bl, self.top_br, w_main)
        self._bevel_edge(self.top_br, self.top_tr, w_main)
        self._bevel_edge(self.top_br, self.bottom_br, w_main)
        self._bevel_edge(self.top_tr, self.bottom_tr, w_main)
        self._bevel_edge(self.top_tl, self.top_tr, w_main)

        # self._bevel_edge(self.in_top_tr, self.in_bottom_tr, w_inner)
        # self._bevel_edge(self.in_top_br, self.in_bottom_br, w_inner)
        # self._bevel_edge(self.in_top_bl, self.in_bottom_bl, w_inner)
        self._bevel_edge(self.in_top_bl, self.thumb_in_top_tl, w_inner)
        self._bevel_edge(self.thumb_in_bottom_l, self.thumb_in_top_l, w_inner)
        # self._bevel_edge(self.thumb_in_bottom_tl, self.thumb_in_top_tl, w_inner)

        self._bevel_edge(self.corner_tl, self.corner_tr, 0.1)
        self._bevel_edge(self.corner_tr, self.top_tl, 0.1)
        self._bevel_edge(self.corner_tl, self.corner_bottom_tl, 0.25)
        self._bevel_edge(self.corner_tr, self.corner_bottom_tr, 0.1)

    def add_feet(self, obj: bpy.types.Object) -> None:
        add_foot(
            obj, self.in_bottom_bl.x - 1.5, self.in_bottom_bl.y - 1.5, 60, 0
        )
        add_foot(
            obj, self.in_bottom_br.x + 1.0, self.in_bottom_br.y - 1.0, 135, 2
        )
        add_foot(
            obj, self.in_bottom_tr.x + 1.0, self.in_bottom_tr.y + 1.0, 225, 3
        )
        add_foot(
            obj,
            self.thumb_in_bottom_tl.x - 1.5,
            self.thumb_in_bottom_tl.y + 2.0,
            -65,
            2.5,
        )

    def add_screw_holes(self, obj: bpy.types.Object) -> None:
        def add_screw_hole(x: float, z: float) -> None:
            screw_hole = gen_screw_hole(self.wall_thickness)
            blender_util.apply_to_wall(
                screw_hole, self.kbd.fr.out2, self.kbd.fl.out2, x=x, z=z
            )
            blender_util.difference(obj, screw_hole)

        x_spacing = 45
        add_screw_hole(x=x_spacing * -0.5, z=8)
        add_screw_hole(x=x_spacing * 0.5, z=8)
        add_screw_hole(x=x_spacing * -0.5, z=22)
        add_screw_hole(x=x_spacing * 0.5, z=22)


def right_simple() -> bpy.types.Object:
    kbd = Keyboard()
    kbd.gen_mesh()
    return WristRestSimple(kbd).gen()


def right(kbd: Optional[Keyboard] = None) -> bpy.types.Object:
    if kbd is None:
        kbd = Keyboard()
        kbd.gen_mesh()

    holder = PadHolder(kbd)
    blend_mesh = blender_util.blender_mesh("wrist_rest_mesh", holder.mesh)
    obj = blender_util.new_mesh_obj("wrist_rest", blend_mesh)
    holder.beveler.apply_bevels(obj)

    return obj


def left() -> bpy.types.Object:
    obj = right()
    with blender_util.TransformContext(obj) as ctx:
        ctx.mirror_x()
    return obj


BASE_THICKNESS = 1.0


class PadSegment:
    inner_h = 4.0
    lip_w = 3.5
    lip_h = 2.5
    outer_w = 4.0

    def __init__(self, mesh, x: float, y: float, z: float) -> None:
        # Bottom outer corner of inset
        self.p1 = mesh.add_xyz(x, y, z)
        # Top outer corner of inset
        self.p2 = mesh.add_xyz(x, y, z + self.inner_h)

        p = cad.Point(x, y, z)
        lip_vec = p.unit() * self.lip_w
        in_p = p - lip_vec
        out_vec = p.unit() * self.outer_w
        out_p = p + out_vec

        top_z = z + self.inner_h + self.lip_h

        # Bottom corner of lip
        self.p3 = mesh.add_xyz(in_p.x, in_p.y, z + self.inner_h)
        # Top corner of lip
        self.p4 = mesh.add_xyz(in_p.x, in_p.y, top_z)
        # Top outer corner of lip
        self.p5 = mesh.add_xyz(out_p.x, out_p.y, top_z)
        # Bottom outer corner of lip
        self.p6 = mesh.add_xyz(out_p.x, out_p.y, z)

        # Lower outer corner of base for test print
        # self.p7 = mesh.add_xyz(out_p.x, out_p.y, z - BASE_THICKNESS)

    def gen_faces(
        self, bcenter: MeshPoint, prev: PadSegment, base_center: MeshPoint
    ) -> None:
        mesh = bcenter.mesh

        # Upper lip to hole the wrist rest pad
        mesh.add_tri(bcenter, prev.p1, self.p1)
        mesh.add_quad(self.p1, prev.p1, prev.p2, self.p2)
        mesh.add_quad(self.p2, prev.p2, prev.p3, self.p3)
        mesh.add_quad(self.p3, prev.p3, prev.p4, self.p4)
        mesh.add_quad(self.p4, prev.p4, prev.p5, self.p5)
        mesh.add_quad(self.p5, prev.p5, prev.p6, self.p6)

        # Base segment
        mesh.add_quad(self.p6, prev.p6, prev.p7, self.p7)
        # mesh.add_tri(self.p7, prev.p7, base_center)


class PadHolder:
    """
    A wrist rest designed to hold a Belkin WaveRest wrist pad (F8E244).

    I've been using these gel pads for 15+ years and fortunately they continue
    to be easily available to purchase.
    """
    def __init__(self, kbd: Keyboard) -> None:
        self.mesh = cad.Mesh()
        self.beveler = blender_util.Beveler()
        self.kbd = kbd

        self.segments_per_quadrant = 40

        # These parameters control the tilt angle of the top plane
        # The front edge will drop according to the front wall of the keyboard.
        # The right edge will drop according to these run/rise parameters.
        right_edge_rise = 1.0
        right_edge_run = 5.0

        # Define the plane for the top face
        # (the bottom of the wrist pad holder).
        fl = self.kbd.front_wall[1].out1
        fr = self.kbd.front_wall[-1].out1
        self.top_plane = cad.Plane(
            fl.point + cad.Point(0, 0, 5),
            fr.point,
            cad.Point(fr.x, fr.y - right_edge_run, fr.z - right_edge_rise),
        )

        self.segments: List[PadSegment] = []

        self.gen_upper_segments()
        self.align_pad_holder()
        self.base_center = self.mesh.add_xyz(
            self.top_center.x, self.top_center.y, 0.0
        )
        self.gen_base()
        self.gen_faces()

    def align_pad_holder(self) -> None:
        # Rotate the pad slightly around the Z axis
        self.mesh.rotate(0.0, 0.0, 4.0)
        # Rotate around the X and Y axes to align with our desired top plane
        r = self.top_plane.rotation_off_z()
        self.mesh.rotate(r.x, r.y, 0.0)

        # Translate to the desired location
        x_offset = 51
        y_offset = -94
        z_off = self.top_plane.z_intersect(x_offset, y_offset)
        self.mesh.translate(x_offset, y_offset, z_off)

    def gen_upper_segments(self) -> None:
        perim = self.gen_perim()
        self.top_center = self.mesh.add_xyz(0.0, 0.0, 0.0)

        for x, y in perim:
            self.segments.append(PadSegment(self.mesh, x, y, 0.0))

    def gen_faces(self) -> None:
        for idx, seg in enumerate(self.segments):
            prev = self.segments[idx - 1]
            seg.gen_faces(self.top_center, prev, self.base_center)
            self.beveler.bevel_edge(seg.p5, prev.p5, 1.0)

    def gen_perim(self) -> List[float, float]:
        # Control points for a cubic bezier cube
        # for each quadrant.
        top = cad.Point(0.0, 29.5)
        top_cp_out = cad.Point(18.0, 29.5)
        right_cp_in = cad.Point(68.0, 53)
        right = cad.Point(71.5, 0.0)
        right_cp_out = cad.Point(71.0, -19.0)
        bottom_cp_in = cad.Point(55.0, -45.0)
        bottom = cad.Point(0.0, -47.5)

        # The left side is a mirror of the right side
        bottom_cp_out = bottom_cp_in.mirror_x()
        left_cp_in = right_cp_out.mirror_x()
        left = right.mirror_x()
        left_cp_out = right_cp_in.mirror_x()
        top_cp_in = top_cp_out.mirror_x()

        quadrants = [
            (top, top_cp_out, right_cp_in, right),
            (right, right_cp_out, bottom_cp_in, bottom),
            (bottom, bottom_cp_out, left_cp_in, left),
            (left, left_cp_out, top_cp_in, top),
        ]

        npoints = self.segments_per_quadrant

        perim: List[Tuple[float, float]] = []
        for ctrl_pts in quadrants:
            for idx, pt in enumerate(cad.bezier(npoints, *ctrl_pts)):
                if idx == 0:
                    # The start point is the same as the end of the previous quadrant
                    continue
                perim.append((pt.x, pt.y))

        return perim

    def tweak_front_face(self) -> None:
        # Make p6 drop directly down from p5.
        # It was previously calculated before applying the top plane rotation,
        # so it drops down in the rotated plane.  However, it looks nicer to
        # drop down vertically after rotation.  We leave the z height alone.
        for segment in self.segments:
            segment.p6.point.x = segment.p5.x
            segment.p6.point.y = segment.p5.y

        # Adjust the front edge of the pad holder to make it flush with the
        # front edge of the keyboard section.
        kbd_fr = self.kbd.fr.out1
        left_idx = self.segments_per_quadrant * 3
        fr_idx = None
        for idx, segment in enumerate(self.segments):
            if segment.p5.x < self.segments[left_idx].p5.x:
                left_idx = idx
            if fr_idx is None and segment.p5.x >= kbd_fr.x:
                fr_idx = idx - 1

        # Make the front left corner extend out to meet where the keyboard
        # thumb section joins the main body
        self.segments[left_idx].p6.point.x = self.kbd.bu0.x
        self.segments[left_idx].p6.point.y = self.kbd.bu0.y
        self.segments[left_idx].p6.point.z = self.kbd.bu0.z

        # On the right hand side, adjust the point just before the end of the
        # keyboard to align exactly with the right side of the keyboard.
        self.segments[fr_idx].p6.point.x = kbd_fr.x
        self.segments[fr_idx].p6.point.y = kbd_fr.y

        # Tweaks to the front edge that interfaces with the keyboard
        front_indices = list(range(left_idx + 1, len(self.segments))) + list(
            range(fr_idx + 1)
        )
        for idx in front_indices:
            # Adjust the front edge of the pad holder to make it flush with the
            # front edge of the keyboard section.
            seg = self.segments[idx]
            seg.p6.point.y = kbd_fr.y

            # Make the p6 Z rise gradually from the thumb connector
            x_pct = (seg.p6.x - self.kbd.bu0.x) / (kbd_fr.x - self.kbd.bu0.x)
            z_off = 0.0
            # z_off = 10 * (1.0 - (x_pct ** 2))
            #z_off = 10 * (1.0 - (x_pct ** 3))
            z_off = -(1 / ((-6.0 * (x_pct ** 2)) - .075) )
            seg.p6.point.z -= z_off

            # Apply a minor bevel on the front face above the keyboard
            if x_pct > 0.18:
                prev = self.segments[idx - 1]
                self.beveler.bevel_edge(seg.p6, prev.p6, 0.5)

        self.beveler.bevel_edge(
            self.segments[left_idx].p6, self.segments[left_idx].p5
        )

    def gen_base(self) -> None:
        self.tweak_front_face()
        for segment in self.segments:
            segment.p7 = self.mesh.add_xyz(segment.p6.x, segment.p6.y, 0.0)


def load_reference_image() -> None:
    import math
    from pathlib import Path

    img = Path(__file__).parent.parent / "reference" / "wrist_rest.jpg"
    bpy.ops.object.load_reference_image(filepath=str(img))
    scale = 56.5

    obj = bpy.context.active_object
    obj.name = "reference"
    obj.scale.x = scale
    obj.scale.y = scale
    obj.scale.z = scale
    obj.rotation_euler = [0, 0, math.radians(-89.3)]
    obj.location.x -= 14.8
    obj.location.y += 7


def test() -> None:
    # load_reference_image()
    right()
