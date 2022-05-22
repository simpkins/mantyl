#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

from cad import Mesh, Point, Transform

from typing import Any, Generator, List, Optional, Tuple


class KeyGrid:
    def __init__(self):
        self.mesh = Mesh()
        self._define_keys()

    def __getattr__(self, name) -> Any:
        # Allow the keys to be accessed as kXY.  e.e., k12 is self._keys[1][2]
        if name.startswith("k") and len(name) == 3:
            try:
                col = int(name[1])
                row = int(name[2])
            except ValueError:
                raise AttributeError(name)
            if col < 0 or col > len(self._keys):
                raise AttributeError(name)
            if row < 0 or row > len(self._keys[col]):
                raise AttributeError(name)
            value = self._keys[col][row]
            if value is None:
                raise IndexError(f"invalid key position {name}")
            return value

        raise AttributeError(name)

    def key_indices(self) -> Generator[[Tuple[int, int]], None, None]:
        for row in (2, 3, 4):
            yield (0, row)
        for row in range(5):
            yield (1, row)
        for col in (2, 3, 4, 5, 6):
            for row in range(6):
                yield (col, row)

    def _define_keys(self) -> None:
        self._keys: List[List[Optional[KeyHole]]] = []
        for col in range(7):
            self._keys.append([None] * 6)

        for col, row in self.key_indices():
            self._keys[col][row] = KeyHole(self.mesh, self._key_tf(col, row))

    def _key_tf(self, column: int, row: int) -> Transform:
        if column == 0:
            return self._key_tf_col0(row)
        elif column == 1:
            return self._key_tf_col1(row)
        elif column == 2:
            return self._key_tf_col2(row)
        elif column == 3:
            return self._key_tf_col3(row)
        elif column == 4:
            return self._key_tf_col4(row)
        elif column == 5:
            return self._key_tf_col5(row)
        elif column == 6:
            return self._key_tf_col6(row)
        raise Exception("invalid key col, row: ({column}, {row})")

    def _key_tf_col0(self, row: int) -> Transform:
        tf = Transform()
        if row == 0:
            raise Exception("invalid col, row: (-1, {row})")
        elif row == 1:
            raise Exception("invalid col, row: (-1, {row})")
        elif row == 2:
            tf = tf.rotate(12, 0, 0)
            tf = tf.translate(0, 18, 9)
        elif row == 3:
            tf = tf.rotate(10, 0, 0)
            tf = tf.translate(0, -1.25, 5)
        elif row == 4:
            tf = tf.rotate(0, 0, 0)
            tf = tf.translate(0, -22.15, 4)
        else:
            raise Exception("invalid col, row: (-1, {row})")

        tf = tf.rotate(0, 0, 6)
        tf = tf.rotate(0, 38, 0)
        tf = tf.translate(-78.5, -3, 58)
        return tf

    def _key_tf_col1(self, row: int) -> Transform:
        tf = Transform()
        if row == 0:
            tf = tf.rotate(0, 0, 8)
            tf = tf.rotate(48, 0, 0)
            tf = tf.translate(-2, 56, 32)
        elif row == 1:
            tf = tf.rotate(0, 0, 4)
            tf = tf.rotate(0, 3, 0)
            tf = tf.rotate(38, 0, 0)
            tf = tf.translate(0, 40.5, 18)
        elif row == 2:
            tf = tf.rotate(12, 0, 0)
            tf = tf.translate(0, 18, 9)
        elif row == 3:
            tf = tf.rotate(10, 0, 0)
            tf = tf.translate(0, -1.25, 5)
        elif row == 4:
            tf = tf.rotate(0, 0, 0)
            tf = tf.translate(0, -22, 4)
        else:
            raise Exception("invalid col, row: (0, {row})")

        tf = tf.rotate(0, 0, 5)
        tf = tf.rotate(0, 29, 0)
        tf = tf.translate(-60.5, -5, 45)
        return tf

    def _key_tf_col2(self, row: int) -> Transform:
        tf = Transform()
        if row == 0:
            tf = tf.rotate(0, 0, 8)
            tf = tf.rotate(0, 4, 0)
            tf = tf.rotate(52, 0, 0)
            tf = tf.translate(-2, 57, 34)
        elif row == 1:
            tf = tf.rotate(0, 0, 5)
            tf = tf.rotate(0, 3, 0)
            tf = tf.rotate(38, 0, 0)
            tf = tf.translate(0, 42, 17.5)
        elif row == 2:
            tf = tf.rotate(18, 0, 0)
            tf = tf.translate(0, 20.5, 8)
        elif row == 3:
            tf = tf.rotate(6, 0, 0)
            tf = tf.translate(0, -1.25, 5)
        elif row == 4:
            tf = tf.rotate(3, 0, 0)
            tf = tf.translate(0, -21, 4)
        elif row == 5:
            tf = tf.rotate(-22, 0, 0)
            tf = tf.translate(0, -44, 8)
        else:
            raise Exception(f"invalid col, row: (1, {row})")

        tf = tf.rotate(0, 0, 5)
        tf = tf.rotate(0, 28, 0)
        tf = tf.translate(-43, -5, 35)
        return tf

    def _key_tf_col3(self, row: int) -> Transform:
        tf = Transform()
        if row == 0:
            tf = tf.rotate(0, 0, 6)
            tf = tf.rotate(0, 5, 0)
            tf = tf.rotate(60, 0, 0)
            tf = tf.translate(-2, 59, 36)
        elif row == 1:
            tf = tf.rotate(0, 0, 3)
            tf = tf.rotate(0, 3, 0)
            tf = tf.rotate(46, 0, 0)
            tf = tf.translate(0, 45, 18)
        elif row == 2:
            tf = tf.rotate(15, 0, 0)
            tf = tf.translate(0, 24, 3.25)
        elif row == 3:
            tf = tf.rotate(-3, 0, 0)
            tf = tf.translate(0, 1, 2)
        elif row == 4:
            tf = tf.rotate(-10, 0, 0)
            tf = tf.translate(0, -19, 4.5)
        elif row == 5:
            tf = tf.rotate(-30, 0, 0)
            tf = tf.translate(0, -40.5, 11.5)
        else:
            raise Exception(f"invalid col, row: (1, {row})")

        tf = tf.rotate(0, 0, 3)
        tf = tf.rotate(0, 20, 0)
        tf = tf.translate(-21, -5, 24)
        return tf

    def _key_tf_col4(self, row: int) -> Transform:
        tf = Transform()
        if row == 0:
            tf = tf.rotate(0, 0, 1)
            tf = tf.rotate(0, 5, 0)
            tf = tf.rotate(60, 0, 0)
            tf = tf.translate(1, 62, 32)
        elif row == 1:
            tf = tf.rotate(0, 0, 0)
            tf = tf.rotate(0, 3, 0)
            tf = tf.rotate(44, 0, 0)
            tf = tf.translate(0, 48.5, 14)
        elif row == 2:
            tf = tf.rotate(19, 0, 0)
            tf = tf.translate(0, 25.5, 2.5)
        elif row == 3:
            tf = tf.rotate(0, 0, 0)
            tf = tf.translate(0, 3, 0)
        elif row == 4:
            tf = tf.rotate(-10, 0, 0)
            tf = tf.translate(0, -19, 2)
        elif row == 5:
            tf = tf.rotate(-25, 0, 0)
            tf = tf.translate(0, -40, 9)
        else:
            raise Exception(f"invalid col, row: (1, {row})")

        tf = tf.rotate(0, 0, 2)
        tf = tf.rotate(0, 8, 0)
        tf = tf.translate(4, -5, 24)
        return tf

    def _key_tf_col5(self, row: int) -> Transform:
        tf = Transform()
        if row == 0:
            tf = tf.rotate(0, 0, 10)
            tf = tf.rotate(0, 0, 0)
            tf = tf.rotate(60, 0, 0)
            tf = tf.translate(-3, 61, 34)
        elif row == 1:
            tf = tf.rotate(0, 0, 6)
            tf = tf.rotate(0, 0, 0)
            tf = tf.rotate(45, 0, 0)
            tf = tf.translate(-2, 48, 15)
        elif row == 2:
            tf = tf.rotate(15, 0, 0)
            tf = tf.translate(0, 25.25, 3.5)
        elif row == 3:
            tf = tf.rotate(2, 0, 0)
            tf = tf.translate(0, 3, 1)
        elif row == 4:
            tf = tf.rotate(-10, 0, 0)
            tf = tf.translate(0, -19, 2)
        elif row == 5:
            tf = tf.rotate(0, 0, -2)
            tf = tf.rotate(-28, 0, 0)
            tf = tf.translate(0, -41, 9)
        else:
            raise Exception(f"invalid col, row: (1, {row})")

        tf = tf.rotate(0, 0, 1)
        tf = tf.rotate(0, 15, 0)
        tf = tf.translate(23.5, -5, 22)
        return tf

    def _key_tf_col6(self, row: int) -> Transform:
        tf = Transform()
        if row == 0:
            tf = tf.rotate(0, 0, 2)
            tf = tf.rotate(0, -5, 0)
            tf = tf.rotate(60, 0, 0)
            tf = tf.translate(0, 60, 35)
        elif row == 1:
            tf = tf.rotate(0, 0, 2)
            tf = tf.rotate(0, 3, 0)
            tf = tf.rotate(45, 0, 0)
            tf = tf.translate(-1, 48, 17)
        elif row == 2:
            tf = tf.rotate(20, 0, 0)
            tf = tf.translate(0, 28, 4.5)
        elif row == 3:
            tf = tf.rotate(3, 0, 0)
            tf = tf.translate(0, 6, 0.5)
        elif row == 4:
            tf = tf.rotate(-10, 0, 0)
            tf = tf.translate(0, -17, 2)
        elif row == 5:
            tf = tf.rotate(-28, 0, 0)
            tf = tf.translate(1, -39, 10)
        else:
            raise Exception(f"invalid col, row: (1, {row})")

        tf = tf.rotate(0, 5, 0)
        tf = tf.translate(47, -5, 19)
        return tf

    def gen_main_grid(self) -> None:
        """Generate mesh faces for the main key hole section.
        """
        # All key holes need the inner walls
        for col, row in self.key_indices():
            self._keys[col][row].inner_walls()

        # Connections between vertical keys on each column
        self.k02.join_bottom(self.k03)
        self.k03.join_bottom(self.k04)
        for row in range(4):
            self._keys[1][row].join_bottom(self._keys[1][row + 1])
        for col in range(2, 7):
            for row in range(5):
                self._keys[col][row].join_bottom(self._keys[col][row + 1])

        # Connections between horizontal keys on each row
        self.k02.join_right(self.k12)
        self.k03.join_right(self.k13)
        self.k04.join_right(self.k14)
        for col in range(1, 6):
            for row in range(5):
                self._keys[col][row].join_right(self._keys[col + 1][row])
        for col in range(2, 6):
            self._keys[col][5].join_right(self._keys[col + 1][5])

        # Corner connections
        KeyHole.join_corner(self.k02, self.k12, self.k13, self.k03)
        KeyHole.join_corner(self.k03, self.k13, self.k14, self.k04)
        for col in range(1, 6):
            for row in range(4):
                KeyHole.join_corner(
                    self._keys[col][row],
                    self._keys[col + 1][row],
                    self._keys[col + 1][row + 1],
                    self._keys[col][row + 1],
                )
        for col in range(2, 6):
            KeyHole.join_corner(
                self._keys[col][4],
                self._keys[col + 1][4],
                self._keys[col + 1][5],
                self._keys[col][5],
            )

        # One slightly unusual corner at the upper-right of k02
        self.mesh.add_face(
            self.k02.u_out_tr, self.k11.u_out_bl, self.k12.u_out_tl
        )
        self.mesh.add_face(
            self.k02.m_out_tr, self.k12.m_out_tl, self.k11.m_out_bl
        )

        # Extra connector for the thumb area
        # top
        self.mesh.add_face(
            self.k14.u_out_bl, self.k14.u_out_br, self.k24.u_out_bl
        )
        self.mesh.add_face(
            self.k14.u_out_bl, self.k24.u_out_bl, self.k25.u_out_tl
        )
        self.mesh.add_face(
            self.k14.u_out_bl, self.k25.u_out_tl, self.k25.u_out_bl
        )
        # bottom
        self.mesh.add_face(
            self.k14.m_out_bl, self.k24.m_out_bl, self.k14.m_out_br
        )
        self.mesh.add_face(
            self.k14.m_out_bl, self.k25.m_out_tl, self.k24.m_out_bl
        )
        self.mesh.add_face(
            self.k14.m_out_bl, self.k25.m_out_bl, self.k25.m_out_tl
        )

    def gen_main_grid_edges(self) -> None:
        """Close off the edges around the main key grid section.

        Useful if we want to render the main grid section by itself, without
        normal walls dropping down to the ground.
        """
        # Wall on the corner section at the upper right of k02
        self.mesh.add_face(
            self.k11.u_out_bl, self.k02.u_out_tr, self.k02.m_out_tr
        )
        self.mesh.add_face(
            self.k02.m_out_tr, self.k11.m_out_bl, self.k11.u_out_bl
        )

        # Left side walls
        self.k02.left_wall()
        self.k02.left_wall_bottom(self.k03)
        self.k03.left_wall()
        self.k03.left_wall_bottom(self.k04)
        self.k04.left_wall()

        self.k10.left_wall()
        self.k10.left_wall_bottom(self.k11)
        self.k11.left_wall()

        # Top walls
        self.k02.top_wall()
        for col in range(1, 6):
            self._keys[col][0].top_wall()
            self._keys[col][0].top_wall_right(self._keys[col + 1][0])
        self.k60.top_wall()

        # Right walls
        for row in range(5):
            self._keys[6][row].right_wall()
            self._keys[6][row].right_wall_bottom(self._keys[6][row + 1])
        self.k65.right_wall()

        # Bottom walls
        for col in range(2, 6):
            self._keys[col][5].bottom_wall()
            self._keys[col][5].bottom_wall_right(self._keys[col + 1][5])
        self.k04.bottom_wall()
        self.k04.bottom_wall_right(self.k14)
        self.k65.bottom_wall()

        # Side wall for the thumb connector area
        self.mesh.add_face(
            self.k14.u_out_bl, self.k25.u_out_bl, self.k25.m_out_bl
        )
        self.mesh.add_face(
            self.k25.m_out_bl, self.k14.m_out_bl, self.k14.u_out_bl
        )


class KeyHole:
    def __init__(self, grid: Mesh, transform: Transform) -> None:
        from keyboard import (
            keyswitch_width,
            keyswitch_height,
            keywell_wall_width,
            plate_thickness,
            web_thickness,
        )

        self.grid = grid

        inner_w = keyswitch_width * 0.5
        outer_w = inner_w + keywell_wall_width
        inner_h = keyswitch_height * 0.5
        outer_h = inner_h + keywell_wall_width
        mid_thickness = plate_thickness - web_thickness

        def add_point(x: float, y: float, z: float) -> MeshPoint:
            p = Point(x, y, z).transform(transform)
            return grid.add_point(p)

        # Lower inner points
        self.l_in_bl = add_point(-inner_w, -inner_h, 0.0)
        self.l_in_br = add_point(inner_w, -inner_h, 0.0)
        self.l_in_tr = add_point(inner_w, inner_h, 0.0)
        self.l_in_tl = add_point(-inner_w, inner_h, 0.0)

        # Lower outer points
        self.l_out_bl = add_point(-outer_w, -outer_h, 0.0)
        self.l_out_br = add_point(outer_w, -outer_h, 0.0)
        self.l_out_tr = add_point(outer_w, outer_h, 0.0)
        self.l_out_tl = add_point(-outer_w, outer_h, 0.0)

        # Upper inner points
        self.u_in_bl = add_point(-inner_w, -inner_h, plate_thickness)
        self.u_in_br = add_point(inner_w, -inner_h, plate_thickness)
        self.u_in_tr = add_point(inner_w, inner_h, plate_thickness)
        self.u_in_tl = add_point(-inner_w, inner_h, plate_thickness)

        # Upper outer points
        self.u_out_bl = add_point(-outer_w, -outer_h, plate_thickness)
        self.u_out_br = add_point(outer_w, -outer_h, plate_thickness)
        self.u_out_tr = add_point(outer_w, outer_h, plate_thickness)
        self.u_out_tl = add_point(-outer_w, outer_h, plate_thickness)

        # Mid outer points
        self.m_out_bl = add_point(-outer_w, -outer_h, mid_thickness)
        self.m_out_br = add_point(outer_w, -outer_h, mid_thickness)
        self.m_out_tr = add_point(outer_w, outer_h, mid_thickness)
        self.m_out_tl = add_point(-outer_w, outer_h, mid_thickness)

    def add_quad(
        self, p0: MeshPoint, p1: MeshPoint, p2: MeshPoint, p3: MeshPoint
    ) -> None:
        self.grid.add_face(p0, p1, p2)
        self.grid.add_face(p2, p3, p0)

    def inner_walls(self) -> None:
        q = self.add_quad

        # inner walls
        q(self.u_in_bl, self.l_in_bl, self.l_in_br, self.u_in_br)
        q(self.u_in_br, self.l_in_br, self.l_in_tr, self.u_in_tr)
        q(self.u_in_tr, self.l_in_tr, self.l_in_tl, self.u_in_tl)
        q(self.u_in_tl, self.l_in_tl, self.l_in_bl, self.u_in_bl)

        # top walls
        q(self.u_in_bl, self.u_in_br, self.u_out_br, self.u_out_bl)
        q(self.u_in_br, self.u_in_tr, self.u_out_tr, self.u_out_br)
        q(self.u_in_tr, self.u_in_tl, self.u_out_tl, self.u_out_tr)
        q(self.u_in_tl, self.u_in_bl, self.u_out_bl, self.u_out_tl)

        # bottom walls
        q(self.l_in_bl, self.l_out_bl, self.l_out_br, self.l_in_br)
        q(self.l_in_br, self.l_out_br, self.l_out_tr, self.l_in_tr)
        q(self.l_in_tr, self.l_out_tr, self.l_out_tl, self.l_in_tl)
        q(self.l_in_tl, self.l_out_tl, self.l_out_bl, self.l_in_bl)

        # outer walls from bottom layer to mid point
        q(self.l_out_bl, self.m_out_bl, self.m_out_br, self.l_out_br)
        q(self.l_out_br, self.m_out_br, self.m_out_tr, self.l_out_tr)
        q(self.l_out_tr, self.m_out_tr, self.m_out_tl, self.l_out_tl)
        q(self.l_out_tl, self.m_out_tl, self.m_out_bl, self.l_out_bl)

    def top_wall(self) -> None:
        self.add_quad(
            self.u_out_tr, self.u_out_tl, self.m_out_tl, self.m_out_tr
        )

    def top_wall_right(self, kh: KeyHole) -> None:
        self.grid.add_face(kh.u_out_tl, self.u_out_tr, self.m_out_tr)
        self.grid.add_face(self.m_out_tr, kh.m_out_tl, kh.u_out_tl)

    def bottom_wall(self) -> None:
        self.add_quad(
            self.u_out_bl, self.u_out_br, self.m_out_br, self.m_out_bl
        )

    def bottom_wall_right(self, kh: KeyHole) -> None:
        self.grid.add_face(self.u_out_br, kh.u_out_bl, kh.m_out_bl)
        self.grid.add_face(kh.m_out_bl, self.m_out_br, self.u_out_br)

    def left_wall(self) -> None:
        self.add_quad(
            self.u_out_tl, self.u_out_bl, self.m_out_bl, self.m_out_tl
        )

    def right_wall(self) -> None:
        self.add_quad(
            self.u_out_br, self.u_out_tr, self.m_out_tr, self.m_out_br
        )

    def join_bottom(self, kh: KeyHole) -> None:
        f = self.grid.add_face

        # Join this key hole to one below it
        f(self.u_out_bl, self.u_out_br, kh.u_out_tr)
        f(kh.u_out_tr, kh.u_out_tl, self.u_out_bl)
        f(self.m_out_bl, kh.m_out_tr, self.m_out_br)
        f(kh.m_out_tr, self.m_out_bl, kh.m_out_tl)

    def left_wall_bottom(self, kh: KeyHole) -> None:
        self.grid.add_face(self.u_out_bl, kh.u_out_tl, self.m_out_bl)
        self.grid.add_face(self.m_out_bl, kh.u_out_tl, kh.m_out_tl)

    def right_wall_bottom(self, kh: KeyHole) -> None:
        self.grid.add_face(kh.u_out_tr, self.u_out_br, self.m_out_br)
        self.grid.add_face(self.m_out_br, kh.m_out_tr, kh.u_out_tr)

    def join_right(self, kh: KeyHole) -> None:
        f = self.grid.add_face

        f(self.u_out_tr, kh.u_out_tl, kh.u_out_bl)
        f(kh.u_out_bl, self.u_out_br, self.u_out_tr)
        f(self.m_out_tr, kh.m_out_bl, kh.m_out_tl)
        f(kh.m_out_bl, self.m_out_tr, self.m_out_br)

    @staticmethod
    def join_corner(
        tl: KeyHole, tr: KeyHole, br: KeyHole, bl: KeyHole
    ) -> None:
        f = tl.grid.add_face

        f(tl.u_out_br, tr.u_out_bl, br.u_out_tl)
        f(br.u_out_tl, bl.u_out_tr, tl.u_out_br)
        f(tl.m_out_br, br.m_out_tl, tr.m_out_bl)
        f(br.m_out_tl, tl.m_out_br, bl.m_out_tr)
