#!/usr/bin/python3 -tt
#
# Copyright (c) 2023, Adam Simpkins
#

from bpycad import cad
from bpycad import blender_util

import bpy

import math
from typing import List, Tuple


class CoverClip:
    def __init__(self) -> None:
        # The thickness of the bottom cover
        self.floor_thickness = 3.175
        self.floor_tolerance = 0.4

        # The gap between the walls and the floor
        self.floor_wall_gap = 2

        # The thickness of the "spring" handle
        self.clip_thickness = 2.0
        self.clip_width = 20
        # The height of the clip, above the floor
        self.clip_height = 25
        # The length that the clip handle extends below the floor
        self.handle_len = 4.0
        # The gap between the front and back sides of the clip
        self.clip_gap = 8.0

        # The dimensions of the triangular protrusion that clips into the wall
        self.clip_protrusion = 2.0
        self.protrusion_h = 4.0

        # The gap between the handle and the surrounding floor (on each side)
        self.handle_gap = 3.0
        self.base_inner_thickness = 3.0
        self.base_lip_x = 10
        self.base_lip_y = 10
        self.base_z_thickness = 3.0

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

    def gen(self, name: str = "clip") -> bpy.types.Object:
        clip = self._gen_clip()
        base = self._gen_base(name)
        blender_util.union(base, clip)
        return base

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
        xmax = self.clip_back_x + self.base_inner_thickness + self.base_lip_y
        base = blender_util.range_cube(
            (xmin, xmax), (ymin, ymax), (zmin, zmax), name=name
        )
        floor = self._gen_floor()
        blender_util.difference(base, floor)

        groove_xmax = self.clip_back_x - 0.01
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

        c_xmax = self.clip_back_x + self.base_inner_thickness
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
            (-self.handle_len, ymax + 0.1),
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

        # Lower radius
        lower_outer_r = self.total_base_thickness
        clip_back_xmax = 2 * clip_outer_r
        clip_back_xmin = clip_back_xmax - self.clip_thickness
        l_outer_c = blender_util.cylinder(
            r=lower_outer_r, h=self.clip_width, rotation=90.0
        )

        base_ymin = -0.5 * self.total_base_thickness
        self.clip_back_x = clip_back_xmin + lower_outer_r
        with blender_util.TransformContext(l_outer_c) as ctx:
            ctx.rotate(180, "Z")
            ctx.translate(
                self.clip_back_x,
                lower_outer_r + base_ymin,
                0,
            )

        # Back wall of clip
        clip_back_ymin = lower_outer_r + base_ymin - 0.1
        back = blender_util.range_cube(
            (clip_back_xmin, clip_back_xmax),
            (clip_back_ymin, ymax + 0.1),
            (self.clip_width * -0.5, self.clip_width * 0.5),
        )
        blender_util.union(obj, back)
        blender_util.union(obj, l_outer_c)

        # Upper radius of back wall
        lower_inner_r = lower_outer_r * 0.75
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
        ymin = self.floor_thickness * -0.5
        lip_xy = [
            (-self.clip_protrusion, ymin),
            (0.1, ymin),
            (0.1, ymin + self.protrusion_h),
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


def cover_clip() -> bpy.types.Object:
    return CoverClip().gen()
