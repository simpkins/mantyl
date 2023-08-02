#!/usr/bin/python3 -tt
#
# Copyright (c) 2023, Adam Simpkins
#

from __future__ import annotations

import bpy
from typing import List, Tuple

from bcad import blender_util
from bcad.cad import Mesh, MeshPoint, Transform
from .keyboard import KeyHole


# pyre-fixme[13]: pyre complains that various members are uninitialized, since
#   they are initialized in a helper method and not directly in __init__()
class NumpadPlate:
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

    def __init__(self) -> None:
        self.mesh = Mesh()
        self.key_size = 19.0
        self.gen_mesh()

    def _make_key(self, x_offset: float, y_offset: float) -> KeyHole:
        x_off_mm = x_offset * self.key_size
        y_off_mm = y_offset * self.key_size
        kh = KeyHole(self.mesh, Transform().translate(x_off_mm, y_off_mm, 0.0))
        kh.inner_walls()
        return kh

    def gen_mesh(self) -> None:
        self._init_keys()
        self._init_corners()
        self._join_keys()
        self._border_faces()

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
        self.l_bl = self.mesh.add_xyz(left_x, bottom_y, lower_z)
        self.l_br = self.mesh.add_xyz(right_x, bottom_y, lower_z)

        self.tl = (self.u_tl, self.l_tl)
        self.tr = (self.u_tr, self.l_tr)
        self.bl = (self.u_bl, self.l_bl)
        self.br = (self.u_br, self.l_br)

        top_y2 = top_y + 5.2265
        self.tr2 = (
            self.mesh.add_xyz(right_x, top_y2, upper_z),
            self.mesh.add_xyz(right_x, top_y2, lower_z),
        )
        self.tl2 = (
            self.mesh.add_xyz(left_x, top_y2, upper_z),
            self.mesh.add_xyz(left_x, top_y2, lower_z),
        )
        self.tr2 = self.tr2

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

        self._fan(self.kp1.bl, [self.kp0.tl, self.kp1.br])

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
                self.tr,
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

    def add_walls(self, rkbd: Keyboard, lkbd: Keyboard) -> None:
        rthumb_tr = self.mesh.add_point(rkbd.thumb_tr.out1)
        rthumb_tl = self.mesh.add_point(rkbd.thumb_tl.out1)
        rthumb_tl_b = self.mesh.add_xyz(rthumb_tl.x, rthumb_tl.y, 0.0)

        lthumb_tl = self.mesh.add_point(lkbd.thumb_tr.out1)
        lthumb_tr = self.mesh.add_point(lkbd.thumb_tl.out1)
        lthumb_tr_b = self.mesh.add_xyz(lthumb_tr.x, lthumb_tr.y, 0.0)

        self.mesh.add_tri(rthumb_tr, rthumb_tl, self.br[0])
        self.mesh.add_tri(lthumb_tr, lthumb_tl, self.bl[0])
        self.mesh.add_quad(lthumb_tr, self.bl[0], self.br[0], rthumb_tl)
        self.mesh.add_quad(lthumb_tr, rthumb_tl, rthumb_tl_b, lthumb_tr_b)

        rthumb_conn_tr = self.mesh.add_point(rkbd.thumb_bu4)
        self.mesh.add_tri(rthumb_tr, self.br[0], rthumb_conn_tr)
        lthumb_conn_tl = self.mesh.add_point(lkbd.thumb_bu4)
        self.mesh.add_tri(lthumb_tl, self.bl[0], lthumb_conn_tl)

        right_wall = [
            self.mesh.add_point(wp.out2) for wp in reversed(rkbd.left_wall)
        ]
        right_wall.append(self.mesh.add_point(rkbd.bl.out2))

        self.mesh.add_tri(rthumb_conn_tr, self.br[0], right_wall[0])
        self.mesh.add_tri(self.br[0], right_wall[1], right_wall[0])
        self.mesh.add_tri(self.br[0], right_wall[2], right_wall[1])
        self.mesh.add_tri(self.br[0], right_wall[3], right_wall[2])
        self.mesh.add_tri(self.br[0], self.tr[0], right_wall[3])
        self.mesh.add_tri(self.tr[0], right_wall[4], right_wall[3])
        self.mesh.add_tri(self.tr[0], right_wall[5], right_wall[4])
        self.mesh.add_tri(self.tr[0], right_wall[6], right_wall[5])
        self.mesh.add_tri(self.tr[0], right_wall[7], right_wall[6])
        self.mesh.add_tri(self.tr[0], right_wall[8], right_wall[7])
        self.mesh.add_tri(self.tr[0], right_wall[9], right_wall[8])
        self.mesh.add_tri(self.tr2[0], self.tr[0], right_wall[9])

        left_wall = [
            self.mesh.add_point(wp.out2) for wp in reversed(lkbd.left_wall)
        ]
        left_wall.append(self.mesh.add_point(lkbd.bl.out2))
        self.mesh.add_tri(lthumb_conn_tl, self.bl[0], left_wall[0])
        self.mesh.add_tri(self.bl[0], left_wall[1], left_wall[0])
        self.mesh.add_tri(self.bl[0], left_wall[2], left_wall[1])
        self.mesh.add_tri(self.bl[0], left_wall[3], left_wall[2])
        self.mesh.add_tri(self.bl[0], self.tl[0], left_wall[3])
        self.mesh.add_tri(self.tl[0], left_wall[4], left_wall[3])
        self.mesh.add_tri(self.tl[0], left_wall[5], left_wall[4])
        self.mesh.add_tri(self.tl[0], left_wall[6], left_wall[5])
        self.mesh.add_tri(self.tl[0], left_wall[7], left_wall[6])
        self.mesh.add_tri(self.tl[0], left_wall[8], left_wall[7])
        self.mesh.add_tri(self.tl[0], left_wall[9], left_wall[8])
        self.mesh.add_tri(self.tl2[0], self.tl[0], left_wall[9])

        self.mesh.add_quad(self.tr[0], self.tl[0], self.tl2[0], self.tr2[0])


def gen_numpad() -> Mesh:
    from .keyboard import Keyboard

    rkbd = Keyboard()
    rkbd.gen_mesh()

    lkbd = Keyboard()
    lkbd.gen_mesh()

    half_offset = 140
    right_tf = Transform().translate(half_offset, 0.0, 0.0)
    left_tf = Transform().mirror_x().translate(-half_offset, 0.0, 0.0)
    rkbd.mesh.transform(right_tf)
    lkbd.mesh.transform(left_tf)

    np = NumpadPlate()
    np.mesh.rotate(12.0, 0.0, 0.0)
    np.mesh.translate(-9.5, 15.0, 70.0)

    np.add_walls(rkbd, lkbd)
    return np.mesh


def test() -> bpy.types.Object:
    mesh = gen_numpad()
    blend_mesh = blender_util.blender_mesh("numpad_mesh", mesh)
    obj = blender_util.new_mesh_obj("numpad", blend_mesh)
    return obj
