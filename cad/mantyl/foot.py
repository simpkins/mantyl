#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

import math
from typing import List, Tuple

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

    @classmethod
    def foot_mesh_pos(cls, phase: float) -> cad.Mesh:
        mesh = cad.Mesh()
        l_orig = mesh.add_point(cad.Point(0.0, 0.0, 0.0))
        top = mesh.add_point(cad.Point(-cls.outer_r, 0.0, cls.top_h))

        lower_points: List[cad.MeshPoint] = []
        upper_points: List[cad.MeshPoint] = []

        fn = 24
        for n in range(fn):
            angle = ((360.0 / fn) * n) + phase
            rad = math.radians(angle)

            x = math.sin(rad) * cls.outer_r
            y = math.cos(rad) * cls.outer_r

            pl = mesh.add_point(cad.Point(x, y, 0.0))
            pu = mesh.add_point(cad.Point(x, y, cls.base_h))
            lower_points.append(pl)
            upper_points.append(pu)

        for idx in range(len(lower_points)):
            if idx + 1 == len(lower_points):
                l_next = lower_points[0]
                u_next = upper_points[0]
            else:
                l_next = lower_points[idx + 1]
                u_next = upper_points[idx + 1]

            mesh.add_tri(l_orig, l_next, lower_points[idx])
            mesh.add_tri(top, upper_points[idx], u_next)
            mesh.add_quad(u_next, upper_points[idx], lower_points[idx], l_next)

        return mesh

    @classmethod
    def foot_mesh_neg(cls, phase: float) -> cad.Mesh:
        bottom_h = -1.0

        mesh = cad.Mesh()
        l_orig = mesh.add_point(cad.Point(0.0, 0.0, bottom_h))
        u_orig = mesh.add_point(cad.Point(0.0, 0.0, cls.recess_h))

        lower_points: List[cad.MeshPoint] = []
        upper_points: List[cad.MeshPoint] = []

        fn = 24
        for n in range(fn):
            angle = ((360.0 / fn) * n) + phase
            rad = math.radians(angle)

            x = math.sin(rad) * cls.inner_r
            y = math.cos(rad) * cls.inner_r

            pl = mesh.add_point(cad.Point(x, y, bottom_h))
            pu = mesh.add_point(cad.Point(x, y, cls.recess_h))
            lower_points.append(pl)
            upper_points.append(pu)

        for idx in range(len(lower_points)):
            if idx + 1 == len(lower_points):
                l_next = lower_points[0]
                u_next = upper_points[0]
            else:
                l_next = lower_points[idx + 1]
                u_next = upper_points[idx + 1]

            mesh.add_tri(l_orig, l_next, lower_points[idx])
            mesh.add_tri(u_orig, upper_points[idx], u_next)
            mesh.add_quad(u_next, upper_points[idx], lower_points[idx], l_next)

        return mesh


def foot_meshes(
    x: float, y: float, angle: float, phase: float
) -> Tuple[cad.Mesh, cad.Mesh]:
    neg_mesh = Foot.foot_mesh_neg(phase)
    pos_mesh = Foot.foot_mesh_pos(phase)
    pos_mesh.translate(Foot.outer_r, 0.0, 0.0)
    neg_mesh.translate(Foot.outer_r, 0.0, 0.0)
    pos_mesh.rotate(0.0, 0.0, angle)
    neg_mesh.rotate(0.0, 0.0, angle)
    pos_mesh.translate(x, y, 0.0)
    neg_mesh.translate(x, y, 0.0)

    return pos_mesh, neg_mesh


def gen_foot(
    name: str, x: float, y: float, angle: float, phase: float
) -> Tuple[bpy.types.Object, bpy.types.Object]:
    pos_mesh, neg_mesh = foot_meshes(x, y, angle, phase)

    neg = new_mesh_obj(f"{name}_neg", neg_mesh)
    foot = new_mesh_obj(name, pos_mesh)
    return foot, neg


def add_foot(
    kbd_obj: bpy.types.Object,
    x: float,
    y: float,
    angle: float,
    phase: float = 0.0,
    dbg: bool = False,
) -> None:
    """
    Add a foot to the keyboard object.

    (x, y) control the location.  The top of the foot will be at this location.
    angle controls the direction the foot is pointing.

    The phase parameter allows slightly rotating the angles at which the
    cylindrical vertices of the foot are placed.  This doesn't change the
    general shape of the foot or the direction it is pointing, but simply
    allows rotating the location of the vertices slightly.  This helps tweak
    the vertices to prevent blender from generating intersecting faces when
    performing the boolean union and difference, which can happen if the
    intersection points lie close to an existing vertex.  I set this parameter
    experimentally for each foot: Blender's 3D-Print tool can highlight
    intersecting edges.  When any were present on a foot, I tweaked its phase
    until blender no longer generates intersecting geometry on that foot.
    (Disabling the bevel on the interior corners would also have probably
    helped eliminate this bad geometry, but using this phase parameter allows
    keeping the bevel.)
    """
    pos, neg = gen_foot("foot", x, y, angle, phase)
    union(kbd_obj, pos)
    difference(kbd_obj, neg, apply_mod=not dbg)


def add_foot_v2(
    kbd_obj: bpy.types.Object,
    center: cad.MeshPoint,
    left: cad.MeshPoint,
    right: cad.MeshPoint,
    wall_recess=2.0,
) -> None:
    foot = FootV2(
        center.point, left.point, right.point, wall_recess=wall_recess
    )
    union(kbd_obj, foot.pos)
    difference(kbd_obj, foot.neg)


def add_feet(kbd: Keyboard, kbd_obj: bpy.types.Object) -> None:
    # Back right foot
    add_foot_v2(
        kbd_obj,
        kbd.br.in3,
        kbd.back_wall[1].in3,
        kbd.right_wall[-2].in3,
        wall_recess=2.1,
    )

    # Back left foot
    add_foot_v2(
        kbd_obj,
        kbd.bl.in3,
        kbd.left_wall[0].in3,
        kbd.back_wall[-2].in3,
    )

    # Front right foot
    add_foot_v2(
        kbd_obj,
        kbd.fr.in3,
        kbd.right_wall[0].in3,
        kbd.front_wall[-2].in3,
        wall_recess=2.1,
    )

    # Thumb bottom left foot
    add_foot_v2(
        kbd_obj,
        kbd.thumb_wall[3].in2,
        kbd.thumb_wall[2].in2,
        kbd.thumb_wall[4].in2,
    )

    # Thumb top left foot
    add_foot_v2(
        kbd_obj,
        kbd.thumb_wall[8].in2,
        kbd.thumb_wall[7].in2,
        kbd.thumb_wall[9].in2,
    )


class FootV2:
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
        assert wall_center.z == 0
        assert wall_left.z == 0
        assert wall_right.z == 0

        self.mesh = cad.Mesh()

        self.wall_dist = (
            self.outer_r - (self.outer_r - self.inner_r) - wall_recess
        )

        zunit = cad.Point(0.0, 0.0, 1.0)
        self.rwall = cad.Plane(wall_center, wall_right + zunit, wall_right)
        self.lwall = cad.Plane(wall_center, wall_left, wall_left + zunit)
        self.rnorm = self.rwall.normal()
        self.lnorm = self.lwall.normal()

        # The center should be wall_dist distance away from both the left and
        # right walls.
        rcenter_plane = self.rwall.shifted_along_normal(self.wall_dist)
        lcenter_plane = self.lwall.shifted_along_normal(self.wall_dist)
        centerp = rcenter_plane.intersect_line(
            lcenter_plane.p0, lcenter_plane.p1
        )
        assert centerp is not None, "walls are parallel"
        self.center = self.mesh.add_point(centerp)
        self.top = self.mesh.add_xyz(wall_center.x, wall_center.y, self.top_h)

        self.rvec = (wall_right - wall_center).unit()
        self.lvec = (wall_left - wall_center).unit()

        # Move our foot wall slightly into the user's specified wall,
        # just to ensure that blender sees them overlapping when it performs
        # the union.
        self.overlap = 0.1
        wc_r = self.rwall.shifted_along_normal(-self.overlap)
        wc_l = self.lwall.shifted_along_normal(-self.overlap)
        self.wall_center = wc_r.intersect_line(wc_l.p0, wc_l.p1)

        self.neg_mesh = cad.cylinder(
            r=self.inner_r, h=self.recess_h * 2, fn=self.fn
        )
        self.neg_mesh.translate(centerp.x, centerp.y, 0.0)
        self._gen()

        self.pos = new_mesh_obj(f"foot.pos", self.mesh)
        self.neg = new_mesh_obj(f"foot.neg", self.neg_mesh)

    def _gen(self) -> None:
        layers: List[cad.MeshPoint] = []
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


def test() -> bpy.types.Object:
    wall_center = cad.Point(0, 0, 0)
    wall_left = cad.Point(30, 0, 0)
    wall_right = cad.Point(0, 30, 0)

    foot = FootV2(wall_center, wall_left, wall_right)
    obj = new_mesh_obj(f"foot", foot.mesh)
    neg_obj = new_mesh_obj(f"foot.neg", foot.neg_mesh)
    blender_util.difference(obj, neg_obj)
    return obj
