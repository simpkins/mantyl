#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

import math
from typing import List, Optional, Tuple

from bpycad import blender_util
from bpycad import cad
from bpycad.blender_util import difference, new_mesh_obj, union
from mantyl.keyboard import Keyboard


class Foot:
    inner_r = 6.5
    outer_r: float = inner_r + 2.0
    recess_h = 1.75
    base_h = 3.0
    top_h = 15.0

    fn = 48
    num_layers = 1

    def __init__(
        self,
        wall_center: cad.Point,
        wall_left: cad.Point,
        wall_right: cad.Point,
        wall_recess: float = 0.0,
    ) -> None:
        assert abs(wall_center.z) < 1e-14, f"bad Z value: {wall_left.z}"
        assert abs(wall_left.z) < 1e-14, f"bad Z value: {wall_left.z}"
        assert abs(wall_right.z) < 1e-14, f"bad Z value: {wall_left.z}"

        self.mesh = cad.Mesh()

        self.wall_dist: float = (
            self.outer_r - (self.outer_r - self.inner_r) - wall_recess
        )

        zunit = cad.Point(0.0, 0.0, 1.0)
        self.rwall = cad.Plane(wall_center, wall_right + zunit, wall_right)
        self.lwall = cad.Plane(wall_center, wall_left, wall_left + zunit)
        self.rnorm: cad.Point = self.rwall.normal()
        self.lnorm: cad.Point = self.lwall.normal()

        # The center should be wall_dist distance away from both the left and
        # right walls.
        rcenter_plane = self.rwall.shifted_along_normal(self.wall_dist)
        lcenter_plane = self.lwall.shifted_along_normal(self.wall_dist)
        centerp = rcenter_plane.intersect_line(
            lcenter_plane.p0, lcenter_plane.p1
        )
        if centerp is None:
            # The left and right walls are parallel
            centerp = wall_center + self.rnorm * self.wall_dist
        self.center: cad.MeshPoint = self.mesh.add_point(centerp)
        self.top: cad.MeshPoint = self.mesh.add_xyz(
            wall_center.x, wall_center.y, self.top_h
        )

        self.rvec: cad.Point = (wall_right - wall_center).unit()
        self.lvec: cad.Point = (wall_left - wall_center).unit()

        # Move our foot wall slightly into the user's specified wall,
        # just to ensure that blender sees them overlapping when it performs
        # the union.
        self.overlap = 0.1
        wc_r = self.rwall.shifted_along_normal(-self.overlap)
        wc_l = self.lwall.shifted_along_normal(-self.overlap)
        wc = wc_r.intersect_line(wc_l.p0, wc_l.p1)
        if wc is None:
            # The left and right walls are parallel
            self.wall_center: cad.Point = (
                wall_center + self.rnorm * -self.overlap
            )
        else:
            self.wall_center = wc

        self.neg_mesh: cad.Mesh = cad.cylinder(
            r=self.inner_r, h=self.recess_h * 2, fn=self.fn
        )
        self.neg_mesh.translate(centerp.x, centerp.y, 0.0)
        self._gen()

        self.pos: bpy.types.Object = new_mesh_obj(f"foot.pos", self.mesh)
        self.neg: bpy.types.Object = new_mesh_obj(f"foot.neg", self.neg_mesh)

    def _gen(self) -> None:
        layers: List[List[cad.MeshPoint]] = []
        # The base layer is at 100%
        layers.append(self._gen_layer(0.0, 1.0))

        # Subsequent layers taper to the point
        # At the moment we are just doing a simple linear taper,
        # so the number of layers doesn't really matter.  We potentially could
        # do a non-linear taper in the future.
        layer_spacing = (self.top_h - self.base_h) / self.num_layers
        for n in range(self.num_layers):
            layer_h = self.base_h + layer_spacing * n
            layer_pct = 1.0 - n * (1.0 / self.num_layers)
            layers.append(self._gen_layer(layer_h, layer_pct))

        for layer_idx in range(1, len(layers)):
            l0 = layers[layer_idx - 1]
            l1 = layers[layer_idx]
            for p_idx, p in enumerate(l0):
                self.mesh.add_quad(p, l1[p_idx], l1[p_idx - 1], l0[p_idx - 1])

        # The final top layer is triangles
        top_layer = layers[-1]
        for p_idx, p in enumerate(top_layer):
            self.mesh.add_tri(p, self.top, top_layer[p_idx - 1])

        # Add the bottom
        bottom_layer = layers[0]
        for p_idx, p in enumerate(bottom_layer):
            self.mesh.add_tri(self.center, p, bottom_layer[p_idx - 1])

    def _gen_layer(self, h: float, pct: float) -> List[cad.MeshPoint]:
        """Compute the perimeter points for one Z-layer of the mesh."""
        points: List[cad.Point] = []
        rotation = math.radians(360.0)
        r = self.outer_r

        # The point near self.wall_center
        pc = cad.Point(self.wall_center.x, self.wall_center.y, h)

        # Compute the points near the left and right walls
        r_pos = (
            self.center.point
            - (self.rnorm * (self.wall_dist + self.overlap))
            + (self.rvec * r)
        )
        pr = cad.Point(r_pos.x, r_pos.y, h)
        l_pos = (
            self.center.point
            - (self.lnorm * (self.wall_dist + self.overlap))
            + (self.lvec * r)
        )
        pl = cad.Point(l_pos.x, l_pos.y, h)
        center_idx: Optional[int] = None
        prev_included = False

        prev_angle = (rotation / self.fn) * -1
        prev_x = self.center.x + math.sin(prev_angle) * r
        prev_y = self.center.y + math.cos(prev_angle) * r
        half_pi = math.pi * 0.5
        for n in range(self.fn):
            angle = (rotation / self.fn) * n
            x = self.center.x + math.sin(angle) * r
            y = self.center.y + math.cos(angle) * r

            # Compute the normal of this perimeter segment
            normal = cad.Point(y - prev_y, prev_x - x, 0.0).unit()

            # Compute the angle between this perimeter segment and the
            # left and right wall normals
            rang = math.acos(normal.x * self.rnorm.x + normal.y * self.rnorm.y)
            lang = math.acos(normal.x * self.lnorm.x + normal.y * self.lnorm.y)

            # Only include potions of the circle that are facing towards both
            # the left and right walls.
            include = (lang >= half_pi) and (rang >= half_pi)
            if include:
                points.append(cad.Point(x, y, h))
            elif prev_included:
                assert center_idx is None
                points.append(pl)
                center_idx = len(points)
                points.append(pc)
                points.append(pr)

            prev_x = x
            prev_y = y
            prev_included = include

        if center_idx is None:
            assert prev_included
            points.append(pl)
            center_idx = len(points)
            points.append(pc)
            points.append(pr)

        # Scale all points back to the center by pct
        mesh_points: List[cad.MeshPoint] = []
        for idx, p in enumerate(points):
            if idx == center_idx:
                mesh_points.append(self.mesh.add_point(p))
                continue
            vec = p - pc
            adjusted = pc + vec * pct
            mesh_points.append(self.mesh.add_point(adjusted))

        return mesh_points


def add_foot(
    kbd_obj: bpy.types.Object,
    center: cad.MeshPoint,
    left: cad.MeshPoint,
    right: cad.MeshPoint,
    wall_recess: float = 2.0,
) -> None:
    """Add a foot to an object.

    The center, left, and right parameters specify points on the wall where
    the foot should be placed.  Center is the point on the wall where the foot
    should be centered, and left and right should be points along the walls to
    the left and right of the foot.
    """
    foot = Foot(center.point, left.point, right.point, wall_recess=wall_recess)
    union(kbd_obj, foot.pos)
    difference(kbd_obj, foot.neg)


def add_feet(kbd: Keyboard, kbd_obj: bpy.types.Object) -> None:
    # Back right foot
    add_foot(
        kbd_obj,
        kbd.br.in3,
        kbd.back_wall[1].in3,
        kbd.right_wall[-2].in3,
        wall_recess=2.1,
    )

    # Back left foot
    add_foot(kbd_obj, kbd.bl.in3, kbd.left_wall[0].in3, kbd.back_wall[-2].in3)

    # Front right foot
    add_foot(
        kbd_obj,
        kbd.fr.in3,
        kbd.right_wall[0].in3,
        kbd.front_wall[-2].in3,
        wall_recess=2.1,
    )

    # Thumb bottom left foot
    add_foot(
        kbd_obj,
        kbd.thumb_wall[3].in2,
        kbd.thumb_wall[2].in2,
        kbd.thumb_wall[4].in2,
    )

    # Thumb top left foot
    add_foot(
        kbd_obj,
        kbd.thumb_wall[8].in2,
        kbd.thumb_wall[7].in2,
        kbd.thumb_wall[9].in2,
    )


def test() -> bpy.types.Object:
    wall_center = cad.Point(0, 0, 0)
    wall_left = cad.Point(30, 0, 0)
    wall_right = cad.Point(0, 30, 0)

    foot = Foot(wall_center, wall_left, wall_right)
    obj = new_mesh_obj(f"foot", foot.mesh)
    neg_obj = new_mesh_obj(f"foot.neg", foot.neg_mesh)
    blender_util.difference(obj, neg_obj)
    return obj
