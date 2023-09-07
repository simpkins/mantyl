#!/usr/bin/python3 -tt
#
# Copyright (c) 2023, Adam Simpkins
#

from __future__ import annotations

from bpycad import cad
from bpycad import blender_util
from bpycad.export_stl import ObjectGenerator

import bmesh
import bpy

from typing import Dict, List, Optional, Tuple


class CoverClip:
    # The thickness of the "spring" handle
    clip_thickness = 2.0
    # The gap between the front and back sides of the clip
    clip_gap = 4.0
    # The height of the clip, above the floor
    clip_height = 25
    # The dimensions of the triangular protrusion that clips into the wall
    clip_protrusion = 3.0
    protrusion_h = 8.0

    clip_back_y: float = clip_thickness * 2 + clip_gap

    # Type 1 base parameters
    # The type 1 base is designed to slot into a simple cut-out in an acrylic
    # cover.
    #
    # The gap between the handle and the surrounding floor (on each side)
    t1_handle_gap = 1.0
    # The thickness of the inner vertical walls in the base
    t1_wall_thickness = 2.0
    # How much the clip extends over the floor on each side
    t1_lip_x = 4
    t1_lip_y = 4
    # The Z-axis thickness of the lower type 1 base lip supporting the cover
    t1_bottom_thickness = 1.5
    t1_top_thickness = 1.5

    # Type 2 base parameters
    # The type 2 base is designed to slide into a slot in a 3d-printed cover.
    t2_wing_width = 3
    t2_wing_length = 8
    t2_tail_length = 4
    # The Z-axis separation between the wings and tail
    t2_wing_clearance = 0.1

    def __init__(
        self,
        width: float,
        handle_depth: float = 2.0,
        cover_thickness: float = 3.0,
        wall_clearance: float = 1.0,
    ) -> None:
        self.clip_width = width
        self.handle_depth = handle_depth
        self.cover_thickness = cover_thickness
        self.wall_clearance = wall_clearance

    def gen_type1(self, name: str = "clip") -> bpy.types.Object:
        """Generate a type 1 clip.

        This is designed to fit into a very simple slot in the cover.
        """
        xmax = (
            (0.5 * self.clip_width)
            + self.t1_handle_gap
            + self.t1_wall_thickness
            + self.t1_lip_x
        )
        xmin = -xmax
        ymin = self.wall_clearance
        ymax = self.clip_back_y + self.t1_wall_thickness + self.t1_lip_y
        zmin = -self.t1_bottom_thickness
        zmax = self.cover_thickness + self.t1_top_thickness
        base = blender_util.range_cube(
            (xmin, xmax), (ymin, ymax), (zmin, zmax), name=name
        )

        groove_xmax = (self.clip_width * 0.5) + self.t1_handle_gap
        groove_xmin = -groove_xmax
        groove_ymin = ymin - 0.1
        groove_ymax = self.clip_back_y + 0.01
        groove_zmin = zmin - 0.1
        groove_zmax = zmax + 0.1
        groove = blender_util.range_cube(
            (groove_xmin, groove_xmax),
            (groove_ymin, groove_ymax),
            (groove_zmin, groove_zmax),
        )
        blender_util.difference(base, groove)

        floor = self._gen_floor_t1()
        blender_util.difference(base, floor)

        handle = self._gen_handle(base_zmin=zmin, base_zmax=zmax)
        blender_util.union(base, handle)
        return base

    def _gen_floor_t1(self) -> bpy.types.Object:
        floor = blender_util.range_cube(
            (-40, 40), (0, 40), (0, self.cover_thickness)
        )

        xmax = (
            (self.clip_width * 0.5)
            + self.t1_handle_gap
            + self.t1_wall_thickness
        )
        xmin = -xmax
        ymax = self.clip_back_y + self.t1_wall_thickness
        groove = blender_util.range_cube(
            (xmin, xmax), (-0.1, ymax), (-0.1, self.cover_thickness + 0.1)
        )
        blender_util.difference(floor, groove)
        return floor

    def gen_type2(self, name: str = "clip") -> bpy.types.Object:
        """Generate a type 2 clip.

        This is lower-profile than the type 1 clip, and the top and bottom are
        even with the cover itself.  However, it requires a slightly more
        complicated slot in the cover.
        """
        base = blender_util.range_cube(
            (self.clip_width * -0.5, self.clip_width * 0.5),
            (self.clip_back_y - 0.01, self.clip_back_y + self.t2_wing_length),
            (0, self.cover_thickness),
            name=name,
        )

        wing_xmax = (self.clip_width * 0.5) + self.t2_wing_width
        wing_xmin = -wing_xmax
        wings = blender_util.range_cube(
            (wing_xmin, wing_xmax),
            (self.clip_back_y, self.clip_back_y + self.t2_wing_length),
            (0, (self.cover_thickness - self.t2_wing_clearance) * 0.5),
        )
        blender_util.union(base, wings)

        tail = blender_util.range_cube(
            (self.clip_width * -0.5, self.clip_width * 0.5),
            (
                self.clip_back_y,
                self.clip_back_y + self.t2_wing_length + self.t2_tail_length,
            ),
            (
                (self.cover_thickness + self.t2_wing_clearance) * 0.5,
                self.cover_thickness,
            ),
        )
        blender_util.union(base, tail)

        handle = self._gen_handle(
            base_zmin=0.0, base_zmax=self.cover_thickness
        )
        blender_util.union(base, handle)
        return base

    def _gen_handle(
        self, base_zmin: float, base_zmax: float
    ) -> bpy.types.Object:
        # Front wall of the clip
        clip_inner_r = self.clip_gap * 0.5
        clip_outer_r = clip_inner_r + self.clip_thickness
        ztop = self.cover_thickness + self.clip_height - clip_outer_r
        obj = blender_util.range_cube(
            (self.clip_width * -0.5, self.clip_width * 0.5),
            (0, self.clip_thickness),
            (-self.handle_depth, ztop + 0.1),
        )

        # The clip lip
        lip = self._gen_protrusion()
        blender_util.union(obj, lip)

        # A small indentation to make it easier to grab the clip
        grip_slot = blender_util.range_cube(
            (self.clip_width * -0.5 - 0.1, self.clip_width * 0.5 + 0.1),
            (-0.1, 0.3),
            (-self.handle_depth - 0.1, -0.75),
        )
        blender_util.difference(obj, grip_slot)

        # Upper radius
        u_outer_c = blender_util.cylinder(
            r=clip_outer_r, h=self.clip_width, rotation=180.0
        )
        u_inner_c = blender_util.cylinder(
            r=clip_inner_r, h=self.clip_width + 0.5
        )
        blender_util.difference(u_outer_c, u_inner_c)
        with blender_util.TransformContext(u_outer_c) as ctx:
            ctx.rotate(-90, "Y")
            ctx.translate(0, clip_outer_r, ztop)

        blender_util.union(obj, u_outer_c)

        # Back wall of clip
        clip_back_ymax = self.clip_back_y
        clip_back_ymin = self.clip_back_y - self.clip_thickness
        back = blender_util.range_cube(
            (self.clip_width * -0.5, self.clip_width * 0.5),
            (clip_back_ymin, self.clip_back_y),
            (self.clip_thickness + base_zmin - 0.1, ztop + 0.1),
        )
        blender_util.union(obj, back)

        # Lower radius of back wall
        lower_c = blender_util.cylinder(
            r=self.clip_thickness, h=self.clip_width, rotation=90.0
        )
        with blender_util.TransformContext(lower_c) as ctx:
            ctx.rotate(180, "Z")
            ctx.rotate(-90, "Y")
            ctx.translate(0, self.clip_back_y, self.clip_thickness + base_zmin)
        blender_util.union(obj, lower_c)

        # Upper radius where the clip handle attaches to the base
        attach_radius = self._gen_attach_radius(base_zmax)
        blender_util.union(obj, attach_radius)
        return obj

    def _gen_attach_radius(self, h: float) -> bpy.types.Object:
        # Radius attaching the back of the clip to the top of the base
        attach_radius = 3.0
        block = blender_util.range_cube(
            (0.01, attach_radius),
            (0.01, attach_radius),
            (self.clip_width * -0.5, self.clip_width * 0.5),
        )
        l_inner_c = blender_util.cylinder(
            r=attach_radius, h=self.clip_width, rotation=90.0
        )
        blender_util.difference(block, l_inner_c)
        with blender_util.TransformContext(block) as ctx:
            ctx.rotate(180, "Z")
            ctx.rotate(-90, "Y")
            ctx.translate(
                0,
                attach_radius + self.clip_back_y - 0.01,
                attach_radius + h - 0.01,
            )
        return block

    def _gen_protrusion(self) -> bpy.types.Object:
        lip = cad.Mesh()
        lip_yz = [
            (-self.clip_protrusion, 0.0),
            (0.1, 0.0),
            (0.1, self.protrusion_h),
        ]
        lip_points: List[Tuple[cad.MeshPoint, cad.MeshPoint]] = []
        for y, z in lip_yz:
            b = lip.add_xyz(self.clip_width * -0.5, y, z)
            t = lip.add_xyz(self.clip_width * 0.5, y, z)
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
    # pyre-fixme[16]: blender type stubs are inaccurate
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
    mesh.add_face(reversed(bottom_points))
    mesh.add_face(top_points)
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
    edges: List[cad.Line2D] = []
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
        remaining_edges: List[cad.Line2D] = []
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
    # pyre-fixme[16]: blender type stubs are incomplete
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
    c = CoverClip(width=10)
    return c.gen_type2()


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
    clip_width: float = 10.0,
    clearance: float = 1.0,
    ground_clearance: float = 2.0,
) -> bpy.types.Object:
    """
    Add a slot to an object wall for the cover to clip into.
    """
    tolerance = 0.2
    length = clip_width + 2.0

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
    obj: bpy.types.Object, clearance: float = 1.0, height: float = 3.0
) -> bpy.types.Object:
    """
    Generate a bottom cover for the specified object.

    The object should have a perimeter of walls that touch the ground plane
    (z == 0).  The interior of these walls will be detected and a bottom cover
    will be produced.

    - clearance specifies the desired XY clearance between the walls and the
      cover.
    - height specifies the height of the cover

    The cover object returned will have its bottom at Z == 0, and its top at
    z == height.
    """
    # pyre-fixme[20]: blender type stubs are inaccurate
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    try:
        return gen_cover_impl(bm, clearance=clearance, height=height)
    finally:
        bm.free()


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
        self.clip_width = 10.0

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
            clip_width=self.clip_width,
            clearance=self.clearance,
            ground_clearance=self.ground_clearance,
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
            self.obj, clearance=self.clearance, height=self.thickness
        )

        for tf in self.clip_transforms:
            clip_slot = self._gen_cover_clip_slot(self.clip_width)
            with blender_util.TransformContext(clip_slot) as ctx:
                ctx.transform(tf)

            blender_util.difference(cover, clip_slot)

        return cover

    def _gen_cover_clip_slot(self, width: float) -> bpy.types.Object:
        y_tolerance = 0.2
        x_tolerance = 0.1

        wings_xmax = (
            (self.clip_width + x_tolerance) * 0.5
        ) + CoverClip.t2_wing_width
        wings_xmin = -wings_xmax
        zmid = self.thickness * 0.5
        wings_y = (
            CoverClip.clip_back_y + CoverClip.t2_wing_length + y_tolerance
        )
        wings = blender_util.range_cube(
            (wings_xmin, wings_xmax), (0, wings_y), (-0.1, zmid)
        )

        tail_xmax = (self.clip_width + x_tolerance) * 0.5
        tail_xmin = -tail_xmax
        tail_y = wings_y + CoverClip.t2_tail_length
        tail = blender_util.range_cube(
            (tail_xmin, tail_xmax), (0.0, tail_y), (zmid, self.thickness + 0.1)
        )
        blender_util.union(wings, tail)

        entry_y = CoverClip.clip_back_y + y_tolerance
        entry = blender_util.range_cube(
            (wings_xmin, wings_xmax),
            (0.0, entry_y),
            (-0.1, self.thickness + 0.1),
        )
        blender_util.union(wings, entry)
        return wings

    def gen_clip(self, width: Optional[float] = None) -> bpy.types.Object:
        if width is None:
            width = self.clip_width
        handle_depth = self.ground_clearance * 0.75
        c = CoverClip(
            width=width,
            handle_depth=handle_depth,
            wall_clearance=self.clearance,
            cover_thickness=self.thickness,
        )
        return c.gen_type2()


class TestObjectsGenerator(ObjectGenerator):
    object_names = ["test_cover_clip", "test_cover_walls", "test_cover"]

    def generate_objects(self) -> Dict[str, bpy.types.Object]:
        objects = TestObjects()
        return {
            "test_cover_clip": objects.clip,
            "test_cover_walls": objects.walls,
            "test_cover": objects.cover,
        }


class TestObjects:
    def __init__(self) -> None:
        print("Generating cover test objects...")
        self.x = 40
        self.y = 40

        mesh = cad.Mesh()
        height = 10.0
        points = [
            (-self.x, self.y),
            (self.x, self.y),
            (self.x, -self.y),
            (-self.x, -self.y),
        ]
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
        self.walls: bpy.types.Object = blender_util.new_mesh_obj("walls", bm)

        self.cb = CoverBuilder(self.walls)
        self.cb.add_clip(in_bot[0], in_bot[1])
        self.cb.add_clip(in_bot[2], in_bot[3])

        self.cb.add_stop(10, in_bot[0], in_bot[1], -15)
        self.cb.add_stop(10, in_bot[0], in_bot[1], 15)
        self.cb.add_stop(10, in_bot[2], in_bot[3], -15)
        self.cb.add_stop(10, in_bot[2], in_bot[3], 15)

        self.cover: bpy.types.Object = self.cb.gen_cover()
        self.clip: bpy.types.Object = self.cb.gen_clip()

        # Lay the clip on its side for printing
        with blender_util.TransformContext(self.clip) as ctx:
            ctx.rotate(90, "Y")


def test() -> None:
    from mathutils import Euler
    import math

    test_objects = TestObjects()
    cb = test_objects.cb

    test_objects.cover.location = (0, 0, cb.ground_clearance)

    # pyre-fixme[16]: blender type stubs are incomplete
    clip2 = bpy.data.objects.new("clip2", test_objects.clip.data)
    # pyre-fixme[16]: blender type stubs are incomplete
    bpy.context.collection.objects.link(clip2)
    # pyre-fixme[6]: blender type stubs are incomplete
    clip2.rotation_euler = Euler((0, math.pi * -0.5, math.pi), "XYZ")
    clip2.location = (0.0, test_objects.y, cb.ground_clearance)

    test_objects.clip.location = (0.0, -test_objects.y, cb.ground_clearance)
    # pyre-fixme[6, 8]: blender type stubs are incomplete
    test_objects.clip.rotation_euler = Euler((0, math.pi * -0.5, 0), "XYZ")
