#!/usr/bin/python3 -tt
#
# Copyright (c) 2023, Adam Simpkins
#

from __future__ import annotations

import bpy
from typing import List, Tuple

from bpycad import blender_util
from bpycad.cad import Mesh, MeshPoint, Plane, Point, Transform
from .keyboard import Keyboard, KeyHole


# pyre-fixme[13]: pyre complains that various members are uninitialized, since
#   they are initialized in a helper method and not directly in __init__()
class NumpadSection:
    kp1: KeyHole
    kp2: KeyHole
    kp3: KeyHole
    kp4: KeyHole
    kp5: KeyHole
    kp6: KeyHole
    kp7: KeyHole
    kp8: KeyHole
    kp9: KeyHole
    kp0: KeyHole
    kp_enter: KeyHole
    kp_extra: KeyHole
    kp_slash: KeyHole
    kp_star: KeyHole
    kp_plus: KeyHole
    kp_minus: KeyHole
    kp_dot: KeyHole
    tl: Tuple[MeshPoint, MeshPoint]
    tr: Tuple[MeshPoint, MeshPoint]
    bl: Tuple[MeshPoint, MeshPoint]
    br: Tuple[MeshPoint, MeshPoint]
    u_tl: MeshPoint
    u_tr: MeshPoint
    u_bl: MeshPoint
    u_br: MeshPoint
    l_tl: MeshPoint
    l_tr: MeshPoint
    l_bl: MeshPoint
    l_br: MeshPoint
    tr_wall: MeshPoint
    tl_wall: MeshPoint
    perim: List[Tuple[MeshPoint, MeshPoint]]
    perim_floor: List[Tuple[MeshPoint, MeshPoint]]

    wall_thickness: float = 4.0

    def __init__(self, rkbd: Keyboard, lkbd: Keyboard) -> None:
        self.mesh = Mesh()
        self.key_size = 19.0
        self._beveler = blender_util.Beveler()
        self.gen_mesh(rkbd, lkbd)

    def _make_key(self, x_offset: float, y_offset: float) -> KeyHole:
        x_off_mm = x_offset * self.key_size
        y_off_mm = y_offset * self.key_size
        kh = KeyHole(self.mesh, Transform().translate(x_off_mm, y_off_mm, 0.0))
        kh.inner_walls()
        return kh

    def gen_mesh(self, rkbd: Keyboard, lkbd: Keyboard) -> None:
        self._init_keys()
        self._init_corners()
        self._join_keys()
        self._border_faces()

        self.plate_tf = (
            Transform().rotate(12.0, 0.0, 0.0).translate(-9.5, 15.0, 70.0)
        )
        self.mesh.transform(self.plate_tf)

        self.add_walls(rkbd, lkbd)
        self.add_bevels()

    def gen_keycaps(self) -> None:
        keys1 = [
            self.kp1,
            self.kp2,
            self.kp3,
            self.kp4,
            self.kp5,
            self.kp6,
            self.kp7,
            self.kp8,
            self.kp9,
            self.kp_extra,
            self.kp_slash,
            self.kp_star,
            self.kp_minus,
            self.kp_dot,
        ]
        for k in keys1:
            k.dsa_keycap(transform=self.plate_tf)

        self.kp_plus.dsa_keycap(yratio=2.0, transform=self.plate_tf)
        self.kp_enter.dsa_keycap(yratio=2.0, transform=self.plate_tf)
        self.kp0.dsa_keycap(xratio=2.0, transform=self.plate_tf)

    def _init_keys(self) -> None:
        self.kp1 = self._make_key(-1, -1)
        self.kp2 = self._make_key(0, -1)
        self.kp3 = self._make_key(1, -1)
        self.kp4 = self._make_key(-1, 0)
        self.kp5 = self._make_key(0, 0)
        self.kp6 = self._make_key(1, 0)
        self.kp7 = self._make_key(-1, 1)
        self.kp8 = self._make_key(0, 1)
        self.kp9 = self._make_key(1, 1)

        self.kp_extra = self._make_key(-1, 2)
        self.kp_slash = self._make_key(0, 2)
        self.kp_star = self._make_key(1, 2)
        self.kp_minus = self._make_key(2, 2)

        self.kp0 = self._make_key(-0.5, -2)
        self.kp_dot = self._make_key(1, -2)

        self.kp_plus = self._make_key(2, 0.5)
        self.kp_enter = self._make_key(2, -1.5)

    def _init_corners(self) -> None:
        border_width_x = 2
        border_width_y = 2

        left_x = self.kp_extra.u_tl.x - border_width_x
        right_x = self.kp_minus.u_tr.x + border_width_x
        top_y = self.kp_extra.u_tl.y + border_width_y
        bottom_y = self.kp0.u_bl.y - border_width_y
        upper_z = self.kp1.u_tl.z
        lower_z = self.kp1.l_tl.z

        self.u_tl = self.mesh.add_xyz(left_x, top_y, upper_z)
        self.u_tr = self.mesh.add_xyz(right_x, top_y, upper_z)
        self.u_bl = self.mesh.add_xyz(left_x, bottom_y, upper_z)
        self.u_br = self.mesh.add_xyz(right_x, bottom_y, upper_z)
        self.l_tl = self.mesh.add_xyz(left_x, top_y, lower_z)
        self.l_tr = self.mesh.add_xyz(right_x, top_y, lower_z)
        # Move the lower bottom corners in slightly, to avoid them being
        # to close to the inner walls
        self.l_bl = self.mesh.add_xyz(left_x + 1.5, bottom_y + 1.5, lower_z)
        self.l_br = self.mesh.add_xyz(right_x - 1.5, bottom_y + 1.5, lower_z)

        self.tl = (self.u_tl, self.l_tl)
        self.tr = (self.u_tr, self.l_tr)
        self.bl = (self.u_bl, self.l_bl)
        self.br = (self.u_br, self.l_br)

        top_y2 = top_y + 5.067
        self.tr_wall = self.mesh.add_xyz(right_x, top_y2, upper_z - 0.75)
        self.tl_wall = self.mesh.add_xyz(left_x, top_y2, upper_z - 0.75)

    def _join_keys(self) -> None:
        self.kp_extra.join_bottom(self.kp7)
        self.kp_slash.join_bottom(self.kp8)
        self.kp_star.join_bottom(self.kp9)
        self.kp7.join_bottom(self.kp4)
        self.kp4.join_bottom(self.kp1)
        self.kp8.join_bottom(self.kp5)
        self.kp5.join_bottom(self.kp2)
        self.kp9.join_bottom(self.kp6)
        self.kp6.join_bottom(self.kp3)

        self.kp_extra.join_right(self.kp_slash)
        self.kp_slash.join_right(self.kp_star)
        self.kp_star.join_right(self.kp_minus)
        self.kp7.join_right(self.kp8)
        self.kp8.join_right(self.kp9)
        self.kp4.join_right(self.kp5)
        self.kp5.join_right(self.kp6)
        self.kp1.join_right(self.kp2)
        self.kp2.join_right(self.kp3)

        KeyHole.join_corner(self.kp_extra, self.kp_slash, self.kp8, self.kp7)
        KeyHole.join_corner(self.kp_slash, self.kp_star, self.kp9, self.kp8)
        KeyHole.join_corner(self.kp7, self.kp8, self.kp5, self.kp4)
        KeyHole.join_corner(self.kp8, self.kp9, self.kp6, self.kp5)
        KeyHole.join_corner(self.kp4, self.kp5, self.kp2, self.kp1)
        KeyHole.join_corner(self.kp5, self.kp6, self.kp3, self.kp2)

        self.kp_minus.join_bottom(self.kp_plus)
        self.kp_plus.join_bottom(self.kp_enter)
        self.kp9.join_right(self.kp_plus)
        self.kp_dot.join_right(self.kp_enter)

        self.kp0.join_right(self.kp_dot)
        self.kp2.join_bottom(self.kp0)
        self.kp3.join_bottom(self.kp_dot)
        KeyHole.join_corner(self.kp2, self.kp3, self.kp_dot, self.kp0)

        KeyHole.join_corner(
            self.kp_star, self.kp_minus, self.kp_plus, self.kp9
        )

        self._fan(
            self.kp_plus.bl,
            [
                self.kp9.br,
                self.kp6.tr,
                self.kp6.br,
                self.kp3.tr,
                self.kp3.br,
                self.kp_dot.tr,
                self.kp_enter.tl,
            ],
        )

        self._fan(self.kp0.tl, [self.kp2.bl, self.kp1.br, self.kp1.bl])

    def _border_faces(self) -> None:
        quad = self.mesh.add_quad
        tri = self.mesh.add_tri

        # Top
        self._fan(
            self.tl,
            [
                self.kp_extra.tl,
                self.kp_extra.tr,
                self.kp_slash.tl,
                self.kp_slash.tr,
                self.kp_star.tl,
            ],
        )
        self._fan(
            self.tr,
            [
                self.tl,
                self.kp_star.tl,
                self.kp_star.tr,
                self.kp_minus.tl,
                self.kp_minus.tr,
            ],
        )

        # Right
        self._fan(
            self.tr,
            [
                self.kp_minus.tr,
                self.kp_minus.br,
                self.kp_plus.tr,
                self.kp_plus.br,
            ],
        )
        self._fan(
            self.br,
            [self.tr, self.kp_plus.br, self.kp_enter.tr, self.kp_enter.br],
        )

        # Bottom
        self._fan(
            self.br,
            [
                self.kp_enter.br,
                self.kp_enter.bl,
                self.kp_dot.br,
                self.kp_dot.bl,
            ],
        )
        self._fan(self.bl, [self.br, self.kp_dot.bl, self.kp0.br, self.kp0.bl])

        # Left
        self._fan(
            self.bl,
            [
                self.kp0.bl,
                self.kp0.tl,
                self.kp1.bl,
                self.kp1.tl,
                self.kp4.bl,
                self.kp4.tl,
            ],
        )
        self._fan(
            self.tl,
            [
                self.bl,
                self.kp4.tl,
                self.kp7.bl,
                self.kp7.tl,
                self.kp_extra.bl,
                self.kp_extra.tl,
            ],
        )

    def _fan(
        self,
        p: Tuple[MeshPoint, MeshPoint],
        l: List[Tuple[MeshPoint, MeshPoint]],
    ) -> None:
        tri = self.mesh.add_tri

        for idx in range(len(l) - 1):
            tri(p[0], l[idx + 1][0], l[idx][0])
            tri(p[1], l[idx][1], l[idx + 1][1])

    def _wall_quad(
        self,
        p0: Tuple[MeshPoint, MeshPoint],
        p1: Tuple[MeshPoint, MeshPoint],
        p2: Tuple[MeshPoint, MeshPoint],
        p3: Tuple[MeshPoint, MeshPoint],
    ) -> None:
        self.mesh.add_quad(p0[0], p1[0], p2[0], p3[0])
        self.mesh.add_quad(p3[1], p2[1], p1[1], p0[1])

    def _inner_floor_point(
        self, pt: MeshPoint, lneighbor: MeshPoint, rneighbor: MeshPoint
    ) -> MeshPoint:
        high_pt = Point(pt.x, pt.y, pt.z + 1.0)
        lplane = Plane(pt.point, high_pt, lneighbor.point)
        lplane = lplane.shifted_along_normal(self.wall_thickness)
        rplane = Plane(high_pt, pt.point, rneighbor.point)
        rplane = rplane.shifted_along_normal(self.wall_thickness)

        intersect_result = lplane.intersect_plane(rplane)
        assert intersect_result is not None, "walls are parallel"
        p0, p1 = intersect_result
        return self.mesh.add_xyz(p0.x, p0.y, 0.0)

    def _inner_perim_point(
        self,
        floor_pt: MeshPoint,
        outer_wall: Tuple[MeshPoint, MeshPoint, MeshPoint],
    ) -> MeshPoint:
        plane = Plane(
            outer_wall[0].point, outer_wall[1].point, outer_wall[2].point
        )
        plane = plane.shifted_along_normal(-self.wall_thickness)

        z = plane.z_intersect(floor_pt.x, floor_pt.y)
        return self.mesh.add_xyz(floor_pt.x, floor_pt.y, z)

    def compute_perimiters(self, rkbd: Keyboard, lkbd: Keyboard) -> None:
        # Outer perimeter, right side
        rperim_out = [
            self.mesh.add_xyz(
                rkbd.thumb_tl.out1.x,
                rkbd.thumb_tl.out1.y,
                rkbd.thumb_tl.out1.z - 0.85,
            ),
            # We are skipping rkbd.thumb_tr.out1 since it is in a straight line
            # between thumb_tl.out1 and thumb_bu4, and including it makes it
            # harder to do bevels cleanly.
            self.mesh.add_point(rkbd.thumb_bu4),
            self.mesh.add_point(rkbd.left_wall[8].out2),
            # Similar to above, we skip rkbd.left_wall[7] and left_wall[6]
            self.mesh.add_point(rkbd.left_wall[5].out2),
            self.mesh.add_point(rkbd.left_wall[4].out2),
            self.mesh.add_point(rkbd.left_wall[3].out2),
            self.mesh.add_point(rkbd.left_wall[2].out2),
            self.mesh.add_point(rkbd.left_wall[1].out2),
            self.mesh.add_point(rkbd.left_wall[0].out2),
            self.mesh.add_point(rkbd.bl.out2),
            self.tr_wall,
        ]

        # Outer perimeter, left side
        # Mirrored from right side
        lperim_out = [
            self.mesh.add_xyz(-rp.x, rp.y, rp.z) for rp in rperim_out
        ]

        # Outer floor points, right side
        rperim_floor_out = [
            self.mesh.add_xyz(rp.x, rp.y, 0) for rp in rperim_out
        ]
        lperim_floor_out = [
            self.mesh.add_xyz(lp.x, lp.y, 0) for lp in lperim_out
        ]

        # Inner floor points, right side
        rperim_floor_in = [
            self._inner_floor_point(
                rperim_floor_out[0], lperim_floor_out[0], rperim_floor_out[1]
            )
        ]
        for idx in range(1, len(rperim_floor_out) - 1):
            rperim_floor_in.append(
                self._inner_floor_point(
                    rperim_floor_out[idx],
                    rperim_floor_out[idx - 1],
                    rperim_floor_out[idx + 1],
                )
            )
        rperim_floor_in.append(
            self._inner_floor_point(
                rperim_floor_out[-1],
                rperim_floor_out[-2],
                lperim_floor_out[-1],
            )
        )
        lperim_floor_in = [
            self.mesh.add_xyz(-rp.x, rp.y, rp.z) for rp in rperim_floor_in
        ]

        # Inner perimeter points
        rperim_in = [
            self._inner_perim_point(
                rperim_floor_in[0], (lperim_out[0], self.br[0], rperim_out[0])
            ),
            self._inner_perim_point(
                rperim_floor_in[1], (self.br[0], rperim_out[2], rperim_out[1])
            ),
            self._inner_perim_point(
                rperim_floor_in[2], (self.br[0], rperim_out[3], rperim_out[2])
            ),
            self._inner_perim_point(
                rperim_floor_in[3], (self.br[0], self.tr[0], rperim_out[2])
            ),
            self._inner_perim_point(
                rperim_floor_in[4], (self.br[0], self.tr[0], rperim_out[2])
            ),
            self._inner_perim_point(
                rperim_floor_in[5], (self.tr[0], rperim_out[5], rperim_out[4])
            ),
            self._inner_perim_point(
                rperim_floor_in[6], (self.tr[0], rperim_out[6], rperim_out[5])
            ),
            self._inner_perim_point(
                rperim_floor_in[7], (self.tr[0], rperim_out[7], rperim_out[6])
            ),
            self._inner_perim_point(
                rperim_floor_in[8], (self.tr[0], rperim_out[8], rperim_out[7])
            ),
            self._inner_perim_point(
                rperim_floor_in[9], (self.tr[0], rperim_out[9], rperim_out[8])
            ),
            self._inner_perim_point(
                rperim_floor_in[10],
                (self.tr[0], rperim_out[10], rperim_out[9]),
            ),
        ]
        lperim_in = [self.mesh.add_xyz(-rp.x, rp.y, rp.z) for rp in rperim_in]

        rperim = list(zip(rperim_out, rperim_in))
        lperim = list(zip(lperim_out, lperim_in))
        rperim_floor = list(zip(rperim_floor_out, rperim_floor_in))
        lperim_floor = list(zip(lperim_floor_out, lperim_floor_in))

        self.perim = rperim + list(reversed(lperim))
        self.perim_floor = rperim_floor + list(reversed(lperim_floor))

    def add_walls(self, rkbd: Keyboard, lkbd: Keyboard) -> None:
        self.compute_perimiters(rkbd, lkbd)

        # Top perimeter faces
        self._fan(self.br, self.perim[0:4] + [self.tr])
        self._fan(self.tr, self.perim[3:9])
        self._wall_quad(self.tr, self.perim[10], self.perim[9], self.perim[8])
        self._wall_quad(self.perim[10], self.tr, self.tl, self.perim[11])
        self._wall_quad(
            self.tl, self.perim[13], self.perim[12], self.perim[11]
        )
        self._fan(self.tl, self.perim[13:19])
        self._fan(self.bl, [self.tl] + self.perim[18:])
        self._wall_quad(self.perim[0], self.perim[-1], self.bl, self.br)

        # Vertical wall faces
        for idx in range(len(self.perim)):
            self._wall_quad(
                self.perim[idx - 1],
                self.perim[idx],
                self.perim_floor[idx],
                self.perim_floor[idx - 1],
            )

        # Wall bottom faces
        for idx in range(len(self.perim_floor)):
            self.mesh.add_quad(
                self.perim_floor[idx - 1][0],
                self.perim_floor[idx][0],
                self.perim_floor[idx][1],
                self.perim_floor[idx - 1][1],
            )

    def add_bevels(self) -> None:
        # bevel_joins controls whether we bevel the edges where
        # the separately printed sections of the keyboard join.
        bevel_joins = False

        # Outer perimeter wall bevels
        perim_bevels = [
            (0, 1.0),
            (1, 1.0),
            (2, 1.0),
            (3, 0.5),
            (4, 0.2),
            (5, 1.0),
        ]
        if bevel_joins:
            perim_bevels.append((9, 0.5))

        for (idx, weight) in perim_bevels:
            mirror = len(self.perim_floor) - 1 - idx
            self._bevel_edge(
                self.perim_floor[idx][0], self.perim[idx][0], weight
            )
            self._bevel_edge(
                self.perim_floor[mirror][0], self.perim[mirror][0], weight
            )

        # Inner perimeter wall bevels
        iperim_bevels = [
            (0, 0.5),
            (1, 0.5),
            (2, 0.5),
            (4, 1.0),
            (5, 1.0),
            (9, 1.0),
        ]
        for (idx, weight) in iperim_bevels:
            mirror = len(self.perim_floor) - 1 - idx
            self._bevel_edge(
                self.perim_floor[idx][1], self.perim[idx][1], weight
            )
            self._bevel_edge(
                self.perim_floor[mirror][1], self.perim[mirror][1], weight
            )

        # Top face bevels
        bottom_bevels = [(0, 1.0), (1, 0.4), (2, 0.5), (3, 0.7)]
        for (idx, weight) in bottom_bevels:
            mirror = len(self.perim) - 1 - idx
            self._bevel_edge(self.br[0], self.perim[idx][0], weight)
            self._bevel_edge(self.bl[0], self.perim[mirror][0], weight)

        top_bevels = [(3, 0.7), (4, 1.0), (5, 1.0), (8, 1.0)]
        for (idx, weight) in top_bevels:
            mirror = len(self.perim) - 1 - idx
            self._bevel_edge(self.tr[0], self.perim[idx][0], weight)
            self._bevel_edge(self.tl[0], self.perim[mirror][0], weight)

        self._bevel_edge(self.bl[0], self.br[0], 0.5)

        # Applying bevels to the left and right sides of the numpad plate
        # unfortunately results in thin/intersecting faces, presumably since
        # we already have some pretty thin faces here to start with.
        # This area doesn't really have a very steep gradient, so just leave it
        # unbeveled.
        #
        # self._bevel_edge(self.br[0], self.tr[0], 0.5)
        # self._bevel_edge(self.bl[0], self.tl[0], 0.5)

        # Perimeter corner bevels
        if bevel_joins:
            for idx in range(len(self.perim)):
                self._bevel_edge(self.perim[idx - 1][0], self.perim[idx][0], 0.6)
        else:
            # Even with bevel_joins disabled, we still bevel a few of the front
            # edges that are near the thumb section and aren't fully aligned
            # with the thumb section edges.
            self._bevel_edge(self.perim[0][0], self.perim[1][0], 0.6)
            self._bevel_edge(self.perim[-1][0], self.perim[-2][0], 0.6)
            self._bevel_edge(self.perim[1][0], self.perim[2][0], 0.6)
            self._bevel_edge(self.perim[-2][0], self.perim[-3][0], 0.6)

        # Heavier edge bevels on the front and back edges
        self._bevel_edge(self.perim[-1][0], self.perim[0][0], 1.0)
        self._bevel_edge(self.perim[9][0], self.perim[10][0], 1.0)
        self._bevel_edge(self.perim[10][0], self.perim[11][0], 1.0)
        self._bevel_edge(self.perim[11][0], self.perim[12][0], 1.0)

    def _bevel_edge(
        self, p0: MeshPoint, p1: MeshPoint, weight: float = 1.0
    ) -> None:
        self._beveler.bevel_edge(p0, p1, weight)

    def apply_bevels(self, obj: bpy.types.Object) -> None:
        return self._beveler.apply_bevels(obj)

    def gen_object(self, name: str = "numpad") -> bpy.types.Object:
        bmesh = blender_util.blender_mesh(f"{name}_mesh", self.mesh)
        obj = blender_util.new_mesh_obj(name, bmesh)
        self.apply_bevels(obj)

        return obj
