#!/usr/bin/python3 -tt
#
# Copyright (c) 2023, Adam Simpkins
#

from __future__ import annotations

from bpycad import cad
from bpycad import blender_util

import bmesh
import bpy

from typing import Dict, List, Tuple


class CoverClip:
    def __init__(self) -> None:
        # The thickness of the bottom cover
        self.floor_thickness = 3.0
        self.floor_tolerance = 0.1

        # The gap between the walls and the floor
        self.floor_wall_gap = 2

        # The thickness of the "spring" handle
        self.clip_thickness = 2.0
        self.clip_width = 10
        # The height of the clip, above the floor
        self.clip_height = 25
        # The length that the clip handle extends below the floor
        self.handle_len = 2.05
        # The gap between the front and back sides of the clip
        self.clip_gap = 4.0

        # The dimensions of the triangular protrusion that clips into the wall
        self.clip_protrusion = 4.0
        self.protrusion_h = 8.0

        # The gap between the handle and the surrounding floor (on each side)
        self.handle_gap = 3.0
        self.base_inner_thickness = 2.0
        self.base_z_thickness = 2.0

        # How much the clip extends over the floor
        self.base_lip_x = 4
        self.base_lip_y = 4

        self.total_base_thickness: float = (
            self.floor_thickness
            + self.floor_tolerance
            + (2 * self.base_z_thickness)
        )

        # The length of the base (perpendicular to the wall)
        self.base_len = 40

        # The very back X coordinate of where the clip attaches to the base
        # This will be computed later, in _gen_clip()
        self.clip_back_x = 0.0
        self.clip_back_xmin = 0.0

        self.protrusion_ymin = (
            self.floor_thickness + self.floor_tolerance
        ) * -0.5

    def gen(self, name: str = "clip") -> bpy.types.Object:
        clip = self._gen_clip()
        base = self._gen_base(name)
        blender_util.union(base, clip, dissolve_angle=0.1)
        return clip

    def _gen_base(self, name: str) -> bpy.types.Object:
        w = self.handle_gap + self.base_inner_thickness + self.base_lip_x
        zmax = (
            (0.5 * self.clip_width)
            + self.handle_gap
            + self.base_inner_thickness
            + self.base_lip_x
        )
        zmin = -zmax

        ymax = 0.5 * self.total_base_thickness
        ymin = -ymax

        xmin = self.floor_wall_gap
        xmax = (
            self.clip_back_xmin + self.base_inner_thickness + self.base_lip_y
        )
        base = blender_util.range_cube(
            (xmin, xmax), (ymin, ymax), (zmin, zmax), name=name
        )
        floor = self._gen_floor()
        blender_util.difference(base, floor)

        groove_xmax = self.clip_back_xmin - 0.01
        groove_zmax = (0.5 * self.clip_width) + self.handle_gap
        groove_zmin = -groove_zmax
        groove = blender_util.range_cube(
            (xmin - 0.1, groove_xmax),
            (ymin - 0.1, ymax + 0.1),
            (groove_zmin, groove_zmax),
        )

        blender_util.difference(base, groove)
        return base

    def _gen_floor(self) -> bpy.types.Object:
        # In reality xmin would be self.floor_wall_gap,
        # but since we are planning to use this object to subtract from the
        # base, we want it to extend further rather than lining up exactly with
        # the edge.
        xmin = 0
        ymax = 0.5 * (self.floor_thickness + self.floor_tolerance)
        ymin = -ymax
        obj = blender_util.range_cube(
            (xmin, 1000), (ymin, ymax), (-1000, 1000)
        )

        c_xmax = self.clip_back_xmin + self.base_inner_thickness
        c_zmax = (
            (self.clip_width * 0.5)
            + self.handle_gap
            + self.base_inner_thickness
        )
        c_zmin = -c_zmax
        cutout = blender_util.range_cube(
            (xmin - 0.5, c_xmax), (ymin - 0.5, ymax + 0.5), (c_zmin, c_zmax)
        )
        blender_util.difference(obj, cutout)
        return obj

    def _gen_clip(self) -> bpy.types.Object:
        # Front wall of the clip
        clip_inner_r = self.clip_gap * 0.5
        clip_outer_r = clip_inner_r + self.clip_thickness
        ymax = self.floor_thickness * 0.5 + self.clip_height - clip_outer_r
        obj = blender_util.range_cube(
            (0, self.clip_thickness),
            (self.protrusion_ymin - self.handle_len, ymax + 0.1),
            (self.clip_width * -0.5, self.clip_width * 0.5),
        )
        lip = self._gen_protrusion()
        blender_util.union(obj, lip)

        # Upper radius
        u_outer_c = blender_util.cylinder(
            r=clip_outer_r, h=self.clip_width, rotation=180.0
        )
        u_inner_c = blender_util.cylinder(
            r=clip_inner_r, h=self.clip_width + 0.5
        )
        blender_util.difference(u_outer_c, u_inner_c)
        with blender_util.TransformContext(u_outer_c) as ctx:
            ctx.rotate(90, "Z")
            ctx.translate(clip_outer_r, ymax, 0)

        blender_util.union(obj, u_outer_c)

        # Back wall of clip
        clip_back_xmax = 2 * clip_outer_r
        self.clip_back_xmin = clip_back_xmax - self.clip_thickness
        clip_back_ymin = (self.total_base_thickness * 0.5) - 0.1
        back = blender_util.range_cube(
            (self.clip_back_xmin, clip_back_xmax),
            (clip_back_ymin, ymax + 0.1),
            (self.clip_width * -0.5, self.clip_width * 0.5),
        )
        blender_util.union(obj, back)

        # Upper radius of back wall
        lower_inner_r = self.total_base_thickness * 0.5
        block = blender_util.range_cube(
            (clip_back_xmax - 0.1, clip_back_xmax + lower_inner_r - 0.1),
            (clip_back_ymin - 0.1, clip_back_ymin + lower_inner_r - 0.1),
            (self.clip_width * -0.5, self.clip_width * 0.5),
        )
        l_inner_c = blender_util.cylinder(
            r=lower_inner_r, h=self.clip_width, rotation=90.0
        )
        with blender_util.TransformContext(l_inner_c) as ctx:
            ctx.rotate(180, "Z")
            ctx.translate(
                clip_back_xmax + lower_inner_r,
                clip_back_ymin + lower_inner_r,
                0,
            )
        blender_util.difference(block, l_inner_c)
        blender_util.union(obj, block)

        return obj

    def _gen_protrusion(self) -> bpy.types.Object:
        lip = cad.Mesh()
        lip_xy = [
            (-self.clip_protrusion, self.protrusion_ymin),
            (0.1, self.protrusion_ymin),
            (0.1, self.protrusion_ymin + self.protrusion_h),
        ]
        lip_points: List[Tuple[cad.MeshPoint, cad.MeshPoint]] = []
        for x, y in lip_xy:
            b = lip.add_xyz(x, y, self.clip_width * -0.5)
            t = lip.add_xyz(x, y, self.clip_width * 0.5)
            lip_points.append((b, t))

        lip.add_tri(lip_points[0][0], lip_points[1][0], lip_points[2][0])
        lip.add_tri(lip_points[0][1], lip_points[2][1], lip_points[1][1])
        lip.add_quad(
            lip_points[0][0],
            lip_points[0][1],
            lip_points[1][1],
            lip_points[1][0],
        )
        lip.add_quad(
            lip_points[1][0],
            lip_points[1][1],
            lip_points[2][1],
            lip_points[2][0],
        )
        lip.add_quad(
            lip_points[2][0],
            lip_points[2][1],
            lip_points[0][1],
            lip_points[0][0],
        )

        bmesh = blender_util.blender_mesh(f"lip_mesh", lip)
        return blender_util.new_mesh_obj("lip", bmesh)


def is_on_ground(face: bmesh.types.BMFace) -> bool:
    for v in face.verts:
        if v.co.z >= 1e-14:
            return False
    return True


def gen_cover_impl(bm: bmesh.types.BMesh) -> bpy.types.Object:
    loop = find_inner_wall_edge_loop(bm)
    ensure_edge_loop_direction(loop)
    shrunk = shrink_edge_loop(loop, clearance=1.0)

    mesh = cad.Mesh()
    mesh_points = [mesh.add_xyz(p.x, p.y, 0.0) for p in shrunk]
    mesh.faces.append([p.index for p in mesh_points])
    blend_mesh = blender_util.blender_mesh(f"cover_mesh", mesh)
    obj = blender_util.new_mesh_obj("cover", blend_mesh)


def ensure_edge_loop_direction(loop: List[cad.Point2D]) -> None:
    # Determine if the loop is clockwise or counter-clockwise
    angle_sum = 0.0
    for idx, p in enumerate(loop):
        prev = loop[idx - 1]
        prev2 = loop[idx - 2]
        l0 = cad.Line2D(prev2, prev)
        l1 = cad.Line2D(prev, p)
        angle_sum += l0.angle_full(l1)

    # angle_sum should be 360 degrees, either positive or negative
    # depending on whether our loop is clockwise or counterclockwise.
    # If it is negative, flip the direction so we are always consistent.
    if angle_sum > 0:
        loop.reverse()


def shrink_edge_loop(
    loop: List[cad.Point2D], clearance: float
) -> List[cad.Point2D]:
    # Shift all of the edges inwards by the specified clearance amount
    edges: List[Line2D] = []
    for idx, p in enumerate(loop):
        prev = loop[idx - 1]
        edge = cad.Line2D(prev, p)
        with_clearance = edge.shifted_along_normal(clearance)
        edges.append(with_clearance)

    # Compute where the newly shifted edges intersect.
    #
    # TODO: For concave corners, if the clearance is large this can cause
    # some edges to disappear entirely.  We need to handle this case
    # properly, rather than letting some edges end up backwards when the
    # clearance is large.
    points: List[cad.Point2D] = []
    for idx, e in enumerate(edges):
        prev = edges[idx - 1]
        isect = e.intersect(prev)
        if isect is None:
            # e and prev are parallel.  In this case we just want to use the
            # starting point from e, which is already shifted along the shared
            # normal by the clearance.
            print(f"flat: {idx}")
            isect = e.p0
        else:
            print(f"non-flat: {idx}")
        points.append(isect)

    return points


def find_inner_wall_edge_loop(bm: bmesh.types.BMesh) -> List[cad.Point2D]:
    # Identify all faces on the ground, and all edges that connect a face on
    # the ground to a face not on the ground.
    ground_faces = []
    ground_loop_edges = {}
    for f in bm.faces:
        if not is_on_ground(f):
            continue

        ground_faces.append(f)
        for e in f.edges:
            other_faces = [
                other_f for other_f in e.link_faces if other_f.index != f.index
            ]
            if len(other_faces) == 1 and not is_on_ground(other_faces[0]):
                ground_loop_edges[e.index] = e

    # Group the ground edges into edge loops
    edge_loops = []
    while ground_loop_edges:
        start_idx = next(iter(ground_loop_edges))
        start = ground_loop_edges.pop(start_idx)
        loop = []
        edge_loops.append(loop)

        cur = start
        v = cur.verts[0]
        loop.append((v, cur))

        while True:
            for e in v.link_edges:
                other = ground_loop_edges.pop(e.index, None)
                if other is not None:
                    cur = other
                    v = (
                        other.verts[1]
                        if other.verts[0].index == v.index
                        else other.verts[0]
                    )
                    loop.append((v, other))
                    break
            else:
                break

    # We generally expect to find 1 outside edge loop, 1 inside edge loop,
    # and possibly several smaller loops for foot wells.
    loop_lengths = []
    for loop in edge_loops:
        edge_len = 0
        for v, e in loop:
            edge_len += e.calc_length()

        if edge_len < 45:
            # Ignore small loops.
            # (The foot wells currently have a length of 40.8)
            continue
        else:
            loop_lengths.append((edge_len, loop))

    # We should now have one loop for the outer edge of the wall,
    # and one loop for the inner edge.
    if len(loop_lengths) != 2:
        raise Exception(
            "unable to determine object walls in order to "
            "compute the bottom cover"
        )

    # The longer loop is the outer edge.  We want the inner edge.
    loop_lengths.sort()

    points: List[cad.Point2D] = []
    for v, e in loop_lengths[0][1]:
        points.append(cad.Point2D(v.co.x, v.co.y))

    return points


def cover_clip() -> bpy.types.Object:
    return CoverClip().gen()


def gen_cover(obj: bpy.types.Object) -> bpy.types.Object:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    try:
        gen_cover_impl(bm)
    finally:
        bm.free()
