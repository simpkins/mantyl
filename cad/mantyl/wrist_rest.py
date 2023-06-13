#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy
from typing import Dict, Tuple

from . import cad
from . import blender_util
from .foot import add_foot
from .keyboard import Keyboard
from .screw_holes import gen_screw_hole


class WristRest:
    def __init__(self, kbd: Keyboard) -> None:
        self.depth = 70.0
        self.back_z_drop = 14
        self.mesh = cad.Mesh()
        self.kbd = kbd

        self._bevel_edges: Dict[Tuple[int, int], float] = {}

        self.wall_thickness = 4.0

        self.gen_top_face()
        self.gen_thumb_connect()
        self.gen_inner_faces()
        self.gen_ground_faces()
        self.mark_bevels()

    def gen(self) -> bpy.types.Object:
        blend_mesh = blender_util.blender_mesh("wrist_rest_mesh", self.mesh)

        # Set bevel weights on the edges
        edge_weights = self._get_bevel_weights(blend_mesh.edges)
        blend_mesh.use_customdata_edge_bevel = True
        for edge_idx, weight in edge_weights.items():
            # pyre-fixme[16]
            e = blend_mesh.edges[edge_idx]
            e.bevel_weight = weight

        obj = blender_util.new_mesh_obj("wrist_rest", blend_mesh)

        # Add a bevel modifier
        # pyre-fixme[16]
        bevel = obj.modifiers.new(name="BevelCorners", type="BEVEL")
        bevel.width = self.bevel_width
        bevel.limit_method = "WEIGHT"
        bevel.segments = 8

        # Apply the bevel modifier
        apply_bevel = True
        if apply_bevel:
            bpy.ops.object.modifier_apply(modifier=bevel.name)

            # Enter edit mode
            bpy.ops.object.mode_set(mode="EDIT")

            # Merge vertices that are close together
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.remove_doubles()
            bpy.ops.mesh.select_all(action="DESELECT")

        bpy.ops.object.mode_set(mode="OBJECT")
        self.add_feet(obj)
        self.add_screw_holes(obj)
        return obj

    def _get_bevel_weights(self, edges) -> Dict[int, float]:
        results: Dict[int, float] = {}
        for idx, e in enumerate(edges):
            v0 = e.vertices[0]
            v1 = e.vertices[1]
            if v0 < v1:
                key = v0, v1
            else:
                key = v1, v0

            weight = self._bevel_edges.get(key, 0.0)
            if weight > 0.0:
                results[idx] = weight

        return results

    def _bevel_edge(
        self, p0: cad.MeshPoint, p1: cad.MeshPoint, weight: float = 1.0
    ) -> None:
        """Mark that a vertex is along an edge to be beveled."""
        if p0.index < p1.index:
            key = p0.index, p1.index
        else:
            key = p1.index, p0.index
        self._bevel_edges[key] = weight

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
        self.bevel_width = 8.0
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


def right() -> bpy.types.Object:
    kbd = Keyboard()
    kbd.gen_mesh()
    return WristRest(kbd).gen()


def left() -> bpy.types.Object:
    obj = right()
    with blender_util.TransformContext(obj) as ctx:
        ctx.mirror_x()
    return obj


def test() -> bpy.types.Object:
    return right()
