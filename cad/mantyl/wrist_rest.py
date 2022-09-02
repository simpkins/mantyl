#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

from . import cad
from . import blender_util
from .keyboard import Keyboard


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
        self.mark_bevels()

    def gen(self) -> bpy.types.Object:
        blend_mesh = blender_util.blender_mesh("wrist_rest_mesh", self.mesh)

        # Set bevel weights on the edges
        edge_weights = self._get_bevel_weights(blend_mesh.edges)
        blend_mesh.use_customdata_edge_bevel = True
        for edge_idx, weight in edge_weights.items():
            e = blend_mesh.edges[edge_idx]
            e.bevel_weight = weight

        obj = blender_util.new_mesh_obj("wrist_rest", blend_mesh)
        return obj

        # Add a bevel modifier
        bevel = obj.modifiers.new(name="BevelCorners", type="BEVEL")
        bevel.width = 4.0
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
        self, p0: MeshPoint, p1: MeshPoint, weight: float = 1.0
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
        top_plane = (
            fl.point + cad.Point(0, 0, 5),
            fr.point,
            cad.Point(fr.x, fr.y - self.depth, fr.z - self.back_z_drop),
        )

        inner_top_offset = cad.plane_normal(top_plane) * -4.0
        top_inner_plane = (
            top_plane[0] + inner_top_offset,
            top_plane[1] + inner_top_offset,
            top_plane[2] + inner_top_offset,
        )

        def top_z(
            x: float, y: float, plane: Tuple[cad.Point, cad.Point, cad.Point]
        ) -> float:
            line = (cad.Point(x, y, 0.0), cad.Point(x, y, 1.0))
            intersect = cad.intersect_line_and_plane(line, plane)
            return intersect.z

        def top_point(p: cad.MeshPoint) -> cad.MeshPoint:
            return self.mesh.add_xyz(p.x, p.y, top_z(p.x, p.y, top_plane))

        def top_inner_point(p: cad.MeshPoint) -> cad.MeshPoint:
            return self.mesh.add_xyz(
                p.x, p.y, top_z(p.x, p.y, top_inner_plane)
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

        self.bottom_inner_tl = self.mesh.add_xyz(
            fl.x, fl.y - self.wall_thickness, 0.0
        )
        self.bottom_inner_tr = self.mesh.add_xyz(
            fr.x + r_offset - self.wall_thickness,
            fl.y - self.wall_thickness,
            0.0,
        )
        self.bottom_inner_bl = self.mesh.add_xyz(
            fl.x, fl.y - self.depth + self.wall_thickness, 0.0
        )
        self.bottom_inner_br = self.mesh.add_xyz(
            fr.x + r_offset - self.wall_thickness,
            fl.y - self.depth + self.wall_thickness,
            0.0,
        )

        self.top_inner_tl = top_inner_point(self.bottom_inner_tl)
        self.top_inner_tr = top_inner_point(self.bottom_inner_tr)
        self.top_inner_bl = top_inner_point(self.bottom_inner_bl)
        self.top_inner_br = top_inner_point(self.bottom_inner_br)

        self.mesh.add_quad(
            self.top_bl, self.top_br, self.bottom_br, self.bottom_bl
        )
        self.mesh.add_quad(
            self.top_br, self.top_tr, self.bottom_tr, self.bottom_br
        )
        self.mesh.add_quad(
            self.top_tr, self.top_tl, self.bottom_tl, self.bottom_tr
        )

        self.mesh.add_quad(
            self.top_inner_bl,
            self.top_inner_br,
            self.top_inner_tr,
            self.top_inner_tl,
        )

        self.mesh.add_quad(
            self.top_inner_tl,
            self.top_inner_tr,
            self.bottom_inner_tr,
            self.bottom_inner_tl,
        )
        self.mesh.add_quad(
            self.top_inner_tr,
            self.top_inner_br,
            self.bottom_inner_br,
            self.bottom_inner_tr,
        )
        self.mesh.add_quad(
            self.top_inner_br,
            self.top_inner_bl,
            self.bottom_inner_bl,
            self.bottom_inner_br,
        )

    def gen_thumb_connect(self) -> None:
        self.corner_tr = self.mesh.add_point(self.kbd.thumb_br_connect.point)
        self.corner_tl = self.mesh.add_point(self.kbd.thumb_wall[0].out1.point)
        self.mesh.add_tri(self.top_tl, self.top_bl, self.corner_tr)
        self.mesh.add_tri(self.corner_tl, self.corner_tr, self.top_bl)

        corner_bottom_tr = self.mesh.add_xyz(
            self.corner_tr.x, self.corner_tr.y, 0.0
        )
        corner_bottom_tl = self.mesh.add_xyz(
            self.corner_tl.x, self.corner_tl.y, 0.0
        )

        self.mesh.add_quad(
            self.top_tl, self.corner_tr, corner_bottom_tr, self.bottom_tl
        )
        self.mesh.add_quad(
            self.corner_tr, self.corner_tl, corner_bottom_tl, corner_bottom_tr
        )
        self.mesh.add_quad(
            self.corner_tl, self.top_bl, self.bottom_bl, corner_bottom_tl
        )

    def mark_bevels(self) -> None:
        self._bevel_edge(self.corner_tr, self.top_bl, 1.0)
        self._bevel_edge(self.corner_tl, self.top_bl, 1.0)
        self._bevel_edge(self.top_tl, self.top_bl, 1.0)
        self._bevel_edge(self.top_bl, self.bottom_bl, 1.0)
        self._bevel_edge(self.top_bl, self.top_br, 1.0)
        self._bevel_edge(self.top_br, self.top_tr, 1.0)
        self._bevel_edge(self.top_br, self.bottom_br, 1.0)
        self._bevel_edge(self.top_tr, self.bottom_tr, 1.0)

        self._bevel_edge(self.top_inner_tr, self.bottom_inner_tr, 0.5)
        self._bevel_edge(self.top_inner_br, self.bottom_inner_br, 0.5)


def right(kbd: Keyboard) -> bpy.types.Object:
    return WristRest(kbd).gen()


def left(kbd: Keyboard) -> bpy.types.Object:
    obj = WristRest(kbd).gen()
    with blender_util.TransformContext(obj) as ctx:
        ctx.mirror_x()
    return obj


def test() -> bpy.types.Object:
    kbd = Keyboard()
    kbd.gen_mesh()
    return right(kbd)
