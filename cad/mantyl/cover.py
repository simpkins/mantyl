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
    # The thickness of the bottom cover
    floor_thickness = 3.0
    floor_tolerance = 0.1

    # The gap between the walls and the floor
    floor_wall_gap = 2

    # The thickness of the "spring" handle
    clip_thickness = 2.0
    clip_width = 10
    # The height of the clip, above the floor
    clip_height = 25
    # The length that the clip handle extends below the floor
    handle_len = 2.05
    # The gap between the front and back sides of the clip
    clip_gap = 4.0

    # The dimensions of the triangular protrusion that clips into the wall
    clip_protrusion = 3.0
    protrusion_h = 8.0

    # The gap between the handle and the surrounding floor (on each side)
    handle_gap = 3.0
    base_inner_thickness = 2.0
    base_z_thickness = 2.0

    # How much the clip extends over the floor
    base_lip_x = 4
    base_lip_y = 4

    def __init__(self) -> None:
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


def gen_cover_impl(
    bm: bmesh.types.BMesh, clearance: float, height: float
) -> bpy.types.Object:
    loop = find_inner_wall_edge_loop(bm)
    ensure_edge_loop_direction(loop)
    shrunk = shrink_edge_loop(loop, clearance=clearance)

    mesh = cad.Mesh()
    bottom_points = [mesh.add_xyz(p.x, p.y, 0.0) for p in shrunk]
    top_points = [mesh.add_xyz(p.x, p.y, height) for p in shrunk]
    mesh.faces.append([p.index for p in reversed(bottom_points)])
    mesh.faces.append([p.index for p in top_points])
    for idx in range(len(bottom_points)):
        mesh.add_quad(
            bottom_points[idx],
            top_points[idx],
            top_points[idx - 1],
            bottom_points[idx - 1],
        )
    blend_mesh = blender_util.blender_mesh(f"cover_mesh", mesh)
    return blender_util.new_mesh_obj("cover", blend_mesh)


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

    # Now compute the new intersection points for the edges.
    # We may have to repeat this process if it initially produces non-manifold
    # results.
    while True:
        # Compute where the newly shifted edges intersect.
        points: List[cad.Point2D] = []
        for idx, e in enumerate(edges):
            next_edge = edges[(idx + 1) % len(edges)]
            isect = e.intersect(next_edge)
            if isect is None:
                # e and next_edge are parallel.  In this case we just want to use
                # the ending point from e, which is already shifted along the
                # shared normal by the clearance.
                isect = e.p1
            points.append(isect)

        # By shifting the edges inwards, it is possible that we have now created
        # non-manifold geometry, where some corners poked through other edges.
        # This can happen on interior beveled corners, if the beveled edges shrunk
        # to nothing and need to be removed entirely.
        #
        # Walk through the edges and remove ones that shrunk to a negative size.
        remaining_edges: List[Line2D] = []
        for idx, orig_edge in enumerate(edges):
            new_edge = cad.Line2D(points[idx - 1], points[idx])
            if orig_edge.p0.x == orig_edge.p1.x:
                orig_cmp = (orig_edge.p0.y, orig_edge.p1.y)
                new_cmp = (new_edge.p0.y, new_edge.p1.y)
            else:
                orig_cmp = (orig_edge.p0.x, orig_edge.p1.x)
                new_cmp = (new_edge.p0.x, new_edge.p1.x)

            shrunk_to_zero = False
            if orig_cmp[0] < orig_cmp[1]:
                if new_cmp[0] >= new_cmp[1]:
                    shrunk_to_zero = True
            else:
                if new_cmp[0] <= new_cmp[1]:
                    shrunk_to_zero = True

            if not shrunk_to_zero:
                remaining_edges.append(orig_edge)

        if len(remaining_edges) != len(edges):
            # Some edges had to be removed.
            # Repeat the loop with these edges removed
            edges = remaining_edges
            continue

        # We are all done if no edges were removed
        break

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


def add_stop(
    obj: bpy.types.Object,
    length: float,
    p1: cad.Point,
    p2: cad.Point,
    x: float = 0.0,
    ground_clearance: float = 2.0,
    cover_height: float = 3.0,
) -> None:
    """
    Add a block to an object to prevent the cover from being pushed upwards
    into the object interior
    """
    bottom = ground_clearance + cover_height
    top = bottom + cover_height

    stop = blender_util.range_cube(
        (length * -0.5, length * 0.5), (-0.1, 4.0), (bottom, top)
    )
    blender_util.apply_to_wall(stop, p2, p1, x=-x)
    blender_util.union(obj, stop)


def generate_clip_hole(
    clearance: float = 1.0, ground_clearance: float = 2.0
) -> bpy.types.Object:
    """
    Add a slot to an object wall for the cover to clip into.
    """
    tolerance = 0.2
    length = CoverClip.clip_width + 2.0

    bottom_z = ground_clearance - tolerance
    mid_z = bottom_z + 0.4
    top_z = ground_clearance + CoverClip.protrusion_h + tolerance

    front_y = clearance
    back_y = front_y - (CoverClip.clip_protrusion + tolerance)

    mesh = cad.Mesh()
    bottom = []
    mid = []
    top = []

    # Generate the mesh points, to match the clip protrusion
    mx = length * -0.5
    my = back_y
    bottom.append(mesh.add_xyz(mx, my, bottom_z))
    mid.append(mesh.add_xyz(mx, my, mid_z))
    top.append(mesh.add_xyz(mx, front_y, top_z))

    mx = length * 0.5
    bottom.append(mesh.add_xyz(mx, my, bottom_z))
    mid.append(mesh.add_xyz(mx, my, mid_z))
    top.append(mesh.add_xyz(mx, front_y, top_z))

    my = front_y + 0.1
    bottom.append(mesh.add_xyz(mx, my, bottom_z))
    mid.append(mesh.add_xyz(mx, my, mid_z))
    top.append(mesh.add_xyz(mx, my, top_z))

    mx = length * -0.5
    bottom.append(mesh.add_xyz(mx, my, bottom_z))
    mid.append(mesh.add_xyz(mx, my, mid_z))
    top.append(mesh.add_xyz(mx, my, top_z))

    # Generate the mesh faces
    mesh.add_quad(bottom[0], bottom[1], bottom[2], bottom[3])
    mesh.add_quad(top[3], top[2], top[1], top[0])
    for idx in range(4):
        mesh.add_quad(bottom[idx], bottom[idx - 1], mid[idx - 1], mid[idx])
        mesh.add_quad(mid[idx], mid[idx - 1], top[idx - 1], top[idx])

    bm = blender_util.blender_mesh(f"slot_mesh", mesh)
    return blender_util.new_mesh_obj("slot", bm)


def add_clip_hole(
    obj: bpy.types.Object,
    p1: cad.Point,
    p2: cad.Point,
    x: float = 0.0,
    # These parameters should match those used for gen_cover()
    clearance: float = 1.0,
    ground_clearance: float = 2.0,
) -> None:
    """
    Add a slot to an object wall for the cover to clip into.
    """
    slot = generate_clip_hole(
        clearance=clearance, ground_clearance=ground_clearance
    )
    blender_util.apply_to_wall(slot, p2, p1, x=-x)
    blender_util.difference(obj, slot)


def gen_cover(
    obj: bpy.types.Object,
    clearance: float = 1.0,
    height: float = 3.0,
    ground_clearance: float = 2.0,
) -> bpy.types.Object:
    """
    Generate a bottom cover for the specified object.

    The object should have a perimeter of walls that touch the ground plane
    (z == 0).  The interior of these walls will be detected and a bottom cover
    will be produced.

    - clearance specifies the desired XY clearance between the walls and the
      cover.
    - height specifies the height of the cover
    - ground_clearance specifies how far off the ground the cover mesh should
      be raised.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    try:
        cover = gen_cover_impl(bm, clearance=clearance, height=height)
    finally:
        bm.free()

    # Raise the cover off the ground slightly
    with blender_util.TransformContext(cover) as ctx:
        ctx.translate(0, 0, ground_clearance)

    return cover


class CoverBuilder:
    def __init__(
        self,
        obj: bpy.types.Object,
        # The distance between the object walls and the cover
        clearance: float = 1.0,
        # The distance between the bottom of the cover and the ground
        ground_clearance: float = 2.0,
        # The Z-axis thickness of the cover
        thickness: float = 3.0,
    ) -> None:
        self.obj = obj
        self.clearance = clearance
        self.ground_clearance = ground_clearance
        self.thickness = thickness

        self.clip_transforms: List[cad.Transform] = []

    def add_clip(self, p1: cad.Point, p2: cad.Point, x: float = 0.0) -> None:
        """Add a clip to the cover.

        This adds a slot for the clip to the object, and a space for the slot
        to the cover.

        p1 and p2 should be points on the inner wall of the object.
        The clip will be centered between these two points.  The x parameter
        can be used to apply an additional offset rather than having the object
        perfectly centered.
        """
        tf = blender_util.apply_to_wall_transform(p2, p1, x=-x)
        slot = generate_clip_hole(
            clearance=self.clearance, ground_clearance=self.ground_clearance
        )
        with blender_util.TransformContext(slot) as ctx:
            ctx.transform(tf)
        blender_util.difference(self.obj, slot)

        # Record this clip location so we can use it when generating the cover
        self.clip_transforms.append(tf)

    def add_stop(
        self, length: float, p1: cad.Point, p2: cad.Point, x: float = 0.0
    ) -> None:
        add_stop(
            self.obj,
            length,
            p1,
            p2,
            x=x,
            ground_clearance=self.ground_clearance,
            cover_height=self.thickness,
        )

    def gen_cover(self) -> bpy.types.Object:
        cover = gen_cover(
            self.obj,
            clearance=self.clearance,
            height=self.thickness,
            ground_clearance=self.ground_clearance,
        )

        for tf in self.clip_transforms:
            clip_slot = self._gen_cover_clip_slot()
            with blender_util.TransformContext(clip_slot) as ctx:
                ctx.transform(tf)

            blender_util.difference(cover, clip_slot)

        return cover

    def _gen_cover_clip_slot(self) -> None:
        xmax = (CoverClip.clip_width * 0.5) + 3 + 0.1
        xmin = -xmax
        zmid = self.ground_clearance + (self.thickness * 0.5)
        y = (self.clearance + 4)
        c = blender_util.range_cube((xmin, xmax), (0, y), (0, zmid))

        xmax = (CoverClip.clip_width * 0.5) + 0.1
        xmin = -xmax
        y = (self.clearance + 7)
        c2 = blender_util.range_cube(
            (xmin, xmax),
            (0, y),
            (zmid - 0.1, self.ground_clearance + self.thickness + 1.0),
        )
        blender_util.union(c, c2)
        return c


def test() -> None:
    mesh = cad.Mesh()
    height = 10.0
    points = [(-40, 30), (40, 30), (40, -30), (-40, -30)]
    in_bot = []
    out_bot = []
    in_top = []
    out_top = []
    for x, y in points:
        out_x = x * (1 + abs(4 / x))
        out_y = y * (1 + abs(4 / y))
        in_bot.append(mesh.add_xyz(x, y, 0.0))
        out_bot.append(mesh.add_xyz(out_x, out_y, 0.0))
        in_top.append(mesh.add_xyz(x, y, height))
        out_top.append(mesh.add_xyz(out_x, out_y, height))

    for idx in range(len(points)):
        mesh.add_quad(
            in_bot[idx], out_bot[idx], out_bot[idx - 1], in_bot[idx - 1]
        )
        mesh.add_quad(
            in_top[idx], in_top[idx - 1], out_top[idx - 1], out_top[idx]
        )
        mesh.add_quad(
            in_top[idx], in_bot[idx], in_bot[idx - 1], in_top[idx - 1]
        )
        mesh.add_quad(
            out_top[idx], out_top[idx - 1], out_bot[idx - 1], out_bot[idx]
        )

    bm = blender_util.blender_mesh(f"walls_mesh", mesh)
    walls = blender_util.new_mesh_obj("walls", bm)

    cb = CoverBuilder(walls)
    cb.add_clip(in_bot[0], in_bot[1])
    cb.add_clip(in_bot[2], in_bot[3])

    cb.add_stop(10, in_bot[0], in_bot[1], -15)
    cb.add_stop(10, in_bot[0], in_bot[1], 15)
    cb.add_stop(10, in_bot[2], in_bot[3], -15)
    cb.add_stop(10, in_bot[2], in_bot[3], 15)

    cover = cb.gen_cover()
