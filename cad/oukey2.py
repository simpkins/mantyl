#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

from cad import Mesh, Point, Transform

from typing import Any, Generator, List, Optional, Tuple


class Keyboard:
    def __init__(self):
        self.wall_thickness = 4.0

        self._main_thumb_transform = (
            Transform()
            .rotate(0, 0, 40)
            .rotate(0, 25, 0)
            .translate(-86, -66, 41)
        )

        self.mesh = Mesh()
        self._define_keys()

    def add_quad_matrix(self, matrix: List[List[MeshPoint]]) -> None:
        for col in range(len(matrix) - 1):
            for row in range(len(matrix[col]) - 1):
                self.mesh.add_quad(
                    matrix[col][row],
                    matrix[col + 1][row],
                    matrix[col + 1][row + 1],
                    matrix[col][row + 1],
                )

    @staticmethod
    def _get_key_variable(
        name: str, keys: List[List[KeyHole]], msg: str
    ) -> KeyHole:
        try:
            col = int(name[1])
            row = int(name[2])
        except ValueError:
            raise AttributeError(name)
        if col < 0 or col > len(keys):
            raise AttributeError(name)
        if row < 0 or row > len(keys[col]):
            raise AttributeError(name)
        value = keys[col][row]
        if value is None:
            raise IndexError(f"invalid {msg} position {name}")
        return value

    def __getattr__(self, name) -> Any:
        # Allow the keys to be accessed as kXY.  e.g., k12 is self._keys[1][2]
        if name.startswith("k") and len(name) == 3:
            return self._get_key_variable(name, self._keys, "key")

        # Allow the thumb keys to be accessed as tXY.
        # e.g., t12 is self._thumb_keys[1][2]
        if name.startswith("t") and len(name) == 3:
            return self._get_key_variable(name, self._thumb_keys, "thumb key")

        raise AttributeError(name)

    def key_indices(self) -> Generator[[Tuple[int, int]], None, None]:
        for row in (2, 3, 4):
            yield (0, row)
        for row in range(5):
            yield (1, row)
        for col in (2, 3, 4, 5, 6):
            for row in range(6):
                yield (col, row)

    def thumb_indices(self) -> Generator[[Tuple[int, int]], None, None]:
        for col in range(2):
            for row in range(3):
                yield (col, row)
        yield (2, 0)
        yield (2, 1)

    def _define_keys(self) -> None:
        self._keys: List[List[Optional[KeyHole]]] = []
        for col in range(7):
            self._keys.append([None] * 6)
        for col, row in self.key_indices():
            self._keys[col][row] = KeyHole(self.mesh, self._key_tf(col, row))

        self._thumb_keys: List[List[Optional[KeyHole]]] = []
        for col in range(3):
            self._thumb_keys.append([None] * 3)
        for col, row in self.thumb_indices():
            self._thumb_keys[col][row] = KeyHole(
                self.mesh, self._thumb_tf(col, row)
            )

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

    def _thumb_tf(self, col: int, row: int) -> Transform:
        return self._rel_thumb_tf(col, row).transform(
            self._main_thumb_transform
        )

    def _rel_thumb_tf(self, col: int, row: int) -> Transform:
        offset = 19
        key = (col, row)
        tf = Transform()

        # Left column
        if key == (0, 0):
            return tf.translate(-offset, offset, 0)
        if key == (0, 1):
            return tf.translate(-offset, 0, 0)
        if key == (0, 2):
            return tf.translate(-offset, -offset, 0)

        # Middle column
        if key == (1, 0):
            return tf.translate(0, offset, 0)
        if key == (1, 1):
            return tf
        if key == (1, 2):
            return tf.translate(0, -offset, 0)

        # Right column
        if key == (2, 0):
            return tf.translate(offset, offset / 2.0, 0)
        if key == (2, 1):
            # I plan to use a 1x1.5 key for this position
            # The bottom end of the other rows is at -offset - (18.415 / 2)
            # The 1.5 key is 27.6225mm in length.
            len_1x1 = 18.415
            len_1x1_5 = len_1x1 * 1.5
            bottom_edge = -offset - (len_1x1 * 0.5)
            y = bottom_edge + (len_1x1_5 * 0.5)
            return tf.translate(offset, y, 0)

        raise Exception("unknown thumb position")

    def _thumb_br(self) -> Transform:
        """The position of the thumb bottom-right key hole,
        if it were a 3x3 grid.
        """
        offset = 19
        return (
            Transform()
            .translate(offset, -offset, 0)
            .transform(self._main_thumb_transform)
        )

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
        KeyHole.top_bottom_tri(self.k02.tr, self.k11.bl, self.k12.tl)

        # Extra connector for the thumb area
        # top
        KeyHole.top_bottom_tri(self.k14.bl, self.k14.br, self.k24.bl)
        KeyHole.top_bottom_tri(self.k14.bl, self.k24.bl, self.k25.tl)
        KeyHole.top_bottom_tri(self.k14.bl, self.k25.tl, self.k25.bl)

    def gen_main_grid_edges(self) -> None:
        """Close off the edges around the main key grid section.

        Useful if we want to render the main grid section by itself, without
        normal walls dropping down to the ground.
        """
        # Wall on the corner section at the upper right of k02
        self.mesh.add_quad(
            self.k11.u_bl, self.k02.u_tr, self.k02.l_tr, self.k11.l_bl
        )

        # Left side walls
        self.k02.left_edge()
        self.k02.left_edge_bottom(self.k03)
        self.k03.left_edge()
        self.k03.left_edge_bottom(self.k04)
        self.k04.left_edge()

        self.k10.left_edge()
        self.k10.left_edge_bottom(self.k11)
        self.k11.left_edge()

        # Top walls
        self.k02.top_edge()
        for col in range(1, 6):
            self._keys[col][0].top_edge()
            self._keys[col][0].top_edge_right(self._keys[col + 1][0])
        self.k60.top_edge()

        # Right walls
        for row in range(5):
            self._keys[6][row].right_edge()
            self._keys[6][row].right_edge_bottom(self._keys[6][row + 1])
        self.k65.right_edge()

        # Bottom walls
        for col in range(2, 6):
            self._keys[col][5].bottom_edge()
            self._keys[col][5].bottom_edge_right(self._keys[col + 1][5])
        self.k04.bottom_edge()
        self.k04.bottom_edge_right(self.k14)
        self.k65.bottom_edge()

        # Side wall for the thumb connector area
        self.mesh.add_quad(
            self.k14.u_bl, self.k25.u_bl, self.k25.l_bl, self.k14.l_bl
        )

    def gen_main_wall(self) -> None:
        back_wall = self.gen_back_wall()
        right_wall = self.gen_right_wall()
        front_wall = self.gen_front_wall()

        back_wall.add_faces(self.mesh)
        right_wall.add_faces(self.mesh)
        front_wall.add_faces(self.mesh)

    def gen_back_wall(self) -> WallPoints:
        u_near_off = 4.0
        l_near_off = 2.0
        far_off = Point(0.0, 6.0, -4.0)

        wp = WallPoints()
        for col in range(6, 0, -1):
            k = self._keys[col][0]

            # Left and right columns for this key hole
            l = WallColumn()
            r = WallColumn()
            wp.columns += [r, l]

            l.out0 = k.u_tl
            r.out0 = k.u_tr

            l.in0 = k.l_tl
            r.in0 = k.l_tr

            l.out1 = k.add_point(-k.outer_w, k.outer_h + u_near_off, k.height)
            l.in1 = k.add_point(
                -k.outer_w, k.outer_h + l_near_off, k.mid_height
            )

            r.out1 = k.add_point(k.outer_w, k.outer_h + u_near_off, k.height)
            r.in1 = k.add_point(
                k.outer_w, k.outer_h + l_near_off, k.mid_height
            )

            l.out2 = self.mesh.add_point(l.out1.point.ptranslate(far_off))
            r.out2 = self.mesh.add_point(r.out1.point.ptranslate(far_off))
            l.out3 = self.mesh.add_point(Point(l.out2.x, l.out2.y, 0.0))
            r.out3 = self.mesh.add_point(Point(r.out2.x, r.out2.y, 0.0))

        max_y = max(col.out2.y for col in wp.columns)
        for col in wp.columns:
            col.out2.point.y = max_y
            col.out3.point.y = max_y
            col.in2 = self.mesh.add_point(
                Point(
                    col.out2.point.x,
                    col.out2.point.y - self.wall_thickness,
                    col.out2.z - 3.0,
                )
            )
            col.in3 = self.mesh.add_point(
                Point(
                    col.out3.point.x,
                    col.out3.point.y - self.wall_thickness,
                    0.0,
                )
            )

        return wp

    def gen_right_wall(self) -> WallPoints:
        near_off = 4.5
        far_off = Point(0.6, 0, 0.0)

        wp = WallPoints()

        for row in range(5, -1, -1):
            k = self._keys[6][row]
            # top and bottom columns
            b = WallColumn()
            t = WallColumn()
            wp.columns += [b, t]

            b.out0 = k.u_br
            t.out0 = k.u_tr
            b.in0 = k.l_br
            t.in0 = k.l_tr

            b.out1 = k.add_point(k.outer_w + near_off, -k.outer_h, k.height)
            t.out1 = k.add_point(k.outer_w + near_off, k.outer_h, k.height)

            b.in1 = k.add_point(k.outer_w + near_off, -k.outer_h, k.mid_height)
            t.in1 = k.add_point(k.outer_w + near_off, k.outer_h, k.mid_height)

        far_offset = 10.0
        max_x = max(col.out1.point.x for col in wp.columns)
        for idx, col in enumerate(wp.columns):
            # Set the x values
            col.out1.point.x = max_x
            col.in1.point.x = max_x - self.wall_thickness

            # Define out2 values
            if idx == 0:
                # At the front edge, just drop straight down
                col.out2 = k.mesh.add_point(
                    Point(max_x, col.in1.y, col.in1.z - far_offset)
                )
            else:
                # Compute the normal at this point along the wall,
                # Then add the far point along the normal
                p = col.out1

                prev_p = wp.columns[idx - 1].out1
                p_normal = Point(0, prev_p.z - p.z, p.y - prev_p.y).unit()
                normal = p_normal
                if idx + 1 < len(wp.columns):
                    next_p = wp.columns[idx + 1].out1
                    n_normal = Point(0, p.z - next_p.z, next_p.y - p.y).unit()
                    normal += n_normal
                    # We have added 2 unit normals, so we have to multiply by
                    # 0.5 to get back to a unit normal
                    normal *= 0.5 * far_offset
                    if idx + 2 == len(wp.columns):
                        # Add a little more here to even some things out
                        normal *= 1.2
                else:
                    # At the back wall we only have 1 unit normal.
                    # We still want to shrink a bit here, to avoid extending
                    # past the back wall
                    normal *= 0.6 * far_offset

                col.out2 = k.mesh.add_point(
                    Point(max_x - normal.x, p.y - normal.y, p.z - normal.z)
                )

            # in2, and ground points (out3, in3)
            col.in2 = k.mesh.add_point(
                Point(col.out2.x - self.wall_thickness, col.out2.y, col.out2.z)
            )
            col.out3 = k.mesh.add_point(Point(col.out2.x, col.out2.y, 0.0))
            col.in3 = k.mesh.add_point(
                Point(col.out3.x - self.wall_thickness, col.out3.y, col.out3.z)
            )

        return wp

    def gen_front_wall(self) -> WallPoints:
        u_near_off = Point(0.0, -7.0, -2.0)
        m_near_off = Point(0.0, -0.5, 0.0)

        wp = WallPoints()
        last_row = 5
        for col in range(3, 7):
            k = self._keys[col][last_row]

            # Left and right columns for this key hole
            l = WallColumn()
            r = WallColumn()
            wp.columns += [l, r]

            l.out0 = k.u_bl
            r.out0 = k.u_br
            l.in0 = k.l_bl
            r.in0 = k.l_br

            l.out1 = k.add_point(
                -k.outer_w + u_near_off.x,
                -k.outer_h + u_near_off.y,
                k.height + u_near_off.z,
            )
            r.out1 = k.add_point(
                k.outer_w + u_near_off.x,
                -k.outer_h + u_near_off.y,
                k.height + u_near_off.z,
            )

            l.in1 = k.add_point(
                -k.outer_w + m_near_off.x,
                -k.outer_h + m_near_off.y,
                k.mid_height + m_near_off.z,
            )
            r.in1 = k.add_point(
                k.outer_w + m_near_off.x,
                -k.outer_h + m_near_off.y,
                k.mid_height + m_near_off.z,
            )

        min_y = min(col.out1.y for col in wp.columns)
        far_offset = 10.0
        for col in wp.columns:
            col.out1.point.y = min_y
            assert min_y + self.wall_thickness <= col.in1.y
            col.in1.point.y = min_y + self.wall_thickness

            col.out2 = k.mesh.add_point(
                Point(col.out1.x, col.out1.y, col.out1.z - far_offset)
            )
            col.in2 = k.mesh.add_point(
                Point(col.in1.x, col.in1.y, col.in1.z - far_offset)
            )

            col.out3 = k.mesh.add_point(Point(col.out2.x, col.out2.y, 0.0))
            col.in3 = k.mesh.add_point(Point(col.in1.x, col.in1.y, 0.0))

        return wp

    def gen_thumb_grid(self) -> None:
        """Generate mesh faces for the thumb key hole section.
        """
        for col, row in self.thumb_indices():
            self._thumb_keys[col][row].inner_walls()

        # Connections between key holes
        self.t00.join_bottom(self.t01)
        self.t01.join_bottom(self.t02)
        self.t10.join_bottom(self.t11)
        self.t11.join_bottom(self.t12)
        self.t20.join_bottom(self.t21)

        self.t00.join_right(self.t10)
        self.t01.join_right(self.t11)
        self.t02.join_right(self.t12)

        KeyHole.join_corner(self.t00, self.t10, self.t11, self.t01)
        KeyHole.join_corner(self.t01, self.t11, self.t12, self.t02)

        self.t10.join_right(self.t20)
        KeyHole.join_corner(self.t10, self.t20, self.t21, self.t11)

        KeyHole.top_bottom_tri(self.t11.tr, self.t21.tl, self.t11.br)
        KeyHole.top_bottom_tri(self.t11.br, self.t21.tl, self.t12.tr)
        self.t12.join_right(self.t21)

        KeyHole.top_bottom_tri(self.t10.tr, self.t20.tr, self.t20.tl)
        KeyHole.top_bottom_tri(self.t21.bl, self.t21.br, self.t12.br)

    def gen_thumb_grid_edges(self) -> None:
        """Close off the edges around the main key grid section.

        Useful if we want to render the main grid section by itself, without
        normal walls dropping down to the ground.
        """
        self.t00.left_edge()
        self.t00.left_edge_bottom(self.t01)
        self.t01.left_edge()
        self.t01.left_edge_bottom(self.t02)
        self.t02.left_edge()

        self.t00.top_edge()
        self.t00.top_edge_right(self.t10)
        self.t10.top_edge()

        self.t02.bottom_edge()
        self.t02.bottom_edge_right(self.t12)
        self.t12.bottom_edge()

        self.t20.right_edge()
        self.t20.right_edge_bottom(self.t21)
        self.t21.right_edge()

        self.mesh.add_quad(
            self.t12.u_br, self.t21.u_br, self.t21.l_br, self.t12.l_br
        )
        self.mesh.add_quad(
            self.t20.u_tr, self.t10.u_tr, self.t10.l_tr, self.t20.l_tr
        )

    def gen_thumb_wall(self) -> None:
        offset = 7.0

        matrix: List[List[MeshPoint]] = []
        kh_w = KeyHole.outer_w
        kh_h = KeyHole.outer_h

        off_b = Point(0.0, -1.0, 0.0)
        off_l = Point(-1.0, 0.0, 0.0)
        off_bl = Point(-1.0, -1.0, 0.0)
        off_tl = Point(-1.0, 1.0, 0.0)
        off_t = Point(0.0, 1.0, 0.0)

        def add(
            key_points: Tuple[MeshPoint, MeshPoint],
            key_tf: Transform,
            x_off: float,
            y_off: float,
            wall_direction: Point,
        ) -> None:
            upper_rel = Point(x_off, y_off, KeyHole.height) + (
                wall_direction * offset
            )
            lower_rel = Point(x_off, y_off, KeyHole.mid_height) + (
                wall_direction * (offset - self.wall_thickness)
            )
            upper = self.mesh.add_point(upper_rel.transform(key_tf))
            lower = self.mesh.add_point(lower_rel.transform(key_tf))
            out_ground = self.mesh.add_point(Point(upper.x, upper.y, 0.0))
            in_ground = self.mesh.add_point(Point(lower.x, lower.y, 0.0))
            matrix.append(
                [
                    key_points[0],
                    upper,
                    out_ground,
                    in_ground,
                    lower,
                    key_points[1],
                ]
            )

        add(self.t12.br, self.t12.transform, kh_w, -kh_h, off_b)
        add(self.t12.bl, self.t12.transform, -kh_w, -kh_h, off_b)
        add(self.t02.br, self.t02.transform, kh_w, -kh_h, off_b)
        add(self.t02.bl, self.t02.transform, -kh_w, -kh_h, off_bl)
        add(self.t02.tl, self.t02.transform, -kh_w, kh_h, off_l)
        add(self.t01.bl, self.t01.transform, -kh_w, -kh_h, off_l)
        add(self.t01.tl, self.t01.transform, -kh_w, kh_h, off_l)
        add(self.t00.bl, self.t00.transform, -kh_w, -kh_h, off_l)
        add(self.t00.tl, self.t00.transform, -kh_w, kh_h, off_tl)
        add(self.t00.tr, self.t00.transform, kh_w, kh_h, off_t)
        add(self.t10.tl, self.t10.transform, -kh_w, kh_h, off_t)
        add(self.t10.tr, self.t10.transform, kh_w, kh_h, off_t)

        self.add_quad_matrix(matrix)


class KeyHole:
    keyswitch_width: float = 14.4
    keyswitch_height: float = 14.4
    keywell_wall_width = 1.5
    web_thickness = 3.5

    height: float = 4.0
    inner_w: float = keyswitch_width * 0.5
    outer_w: float = inner_w + keywell_wall_width
    inner_h = keyswitch_height * 0.5
    outer_h = inner_h + keywell_wall_width

    # The height of the connecting mesh between key holes
    mid_height = height - web_thickness

    def __init__(self, mesh: Mesh, transform: Transform) -> None:
        self.mesh = mesh
        self.transform = transform

        add_point = self.add_point

        outer_w = self.outer_w
        outer_h = self.outer_h
        inner_w = self.inner_w
        inner_h = self.inner_h

        # Upper outer points.
        # These are the main connection points used externally for the walls
        self.u_bl = add_point(-outer_w, -outer_h, self.height)
        self.u_br = add_point(outer_w, -outer_h, self.height)
        self.u_tr = add_point(outer_w, outer_h, self.height)
        self.u_tl = add_point(-outer_w, outer_h, self.height)

        # Lower outer points.
        # These are also connection points used externally,
        # for the underside of the walls
        self.l_bl = add_point(-outer_w, -outer_h, self.mid_height)
        self.l_br = add_point(outer_w, -outer_h, self.mid_height)
        self.l_tr = add_point(outer_w, outer_h, self.mid_height)
        self.l_tl = add_point(-outer_w, outer_h, self.mid_height)

        # The remaining points are primarily used only internally
        # for the interior walls of the key hole.

        # Upper inner points
        self.u_in_bl = add_point(-inner_w, -inner_h, self.height)
        self.u_in_br = add_point(inner_w, -inner_h, self.height)
        self.u_in_tr = add_point(inner_w, inner_h, self.height)
        self.u_in_tl = add_point(-inner_w, inner_h, self.height)

        # Bottom-most inner points.
        # The bottom-most points extend slightly below the "lower" points
        # used for connections to the walls.
        self.b_in_bl = add_point(-inner_w, -inner_h, 0.0)
        self.b_in_br = add_point(inner_w, -inner_h, 0.0)
        self.b_in_tr = add_point(inner_w, inner_h, 0.0)
        self.b_in_tl = add_point(-inner_w, inner_h, 0.0)

        # Bottom-most outer points
        self.b_out_bl = add_point(-outer_w, -outer_h, 0.0)
        self.b_out_br = add_point(outer_w, -outer_h, 0.0)
        self.b_out_tr = add_point(outer_w, outer_h, 0.0)
        self.b_out_tl = add_point(-outer_w, outer_h, 0.0)

    @property
    def tl(self) -> Tuple[MeshPoint, MeshPoint]:
        return (self.u_tl, self.l_tl)

    @property
    def tr(self) -> Tuple[MeshPoint, MeshPoint]:
        return (self.u_tr, self.l_tr)

    @property
    def bl(self) -> Tuple[MeshPoint, MeshPoint]:
        return (self.u_bl, self.l_bl)

    @property
    def br(self) -> Tuple[MeshPoint, MeshPoint]:
        return (self.u_br, self.l_br)

    def add_point(self, x: float, y: float, z: float) -> MeshPoint:
        p = Point(x, y, z).transform(self.transform)
        return self.mesh.add_point(p)

    def inner_walls(self) -> None:
        q = self.mesh.add_quad

        # inner walls
        q(self.u_in_bl, self.b_in_bl, self.b_in_br, self.u_in_br)
        q(self.u_in_br, self.b_in_br, self.b_in_tr, self.u_in_tr)
        q(self.u_in_tr, self.b_in_tr, self.b_in_tl, self.u_in_tl)
        q(self.u_in_tl, self.b_in_tl, self.b_in_bl, self.u_in_bl)

        # top walls
        q(self.u_in_bl, self.u_in_br, self.u_br, self.u_bl)
        q(self.u_in_br, self.u_in_tr, self.u_tr, self.u_br)
        q(self.u_in_tr, self.u_in_tl, self.u_tl, self.u_tr)
        q(self.u_in_tl, self.u_in_bl, self.u_bl, self.u_tl)

        # bottom walls
        q(self.b_in_bl, self.b_out_bl, self.b_out_br, self.b_in_br)
        q(self.b_in_br, self.b_out_br, self.b_out_tr, self.b_in_tr)
        q(self.b_in_tr, self.b_out_tr, self.b_out_tl, self.b_in_tl)
        q(self.b_in_tl, self.b_out_tl, self.b_out_bl, self.b_in_bl)

        # outer walls from bottom layer to mid point
        q(self.b_out_bl, self.l_bl, self.l_br, self.b_out_br)
        q(self.b_out_br, self.l_br, self.l_tr, self.b_out_tr)
        q(self.b_out_tr, self.l_tr, self.l_tl, self.b_out_tl)
        q(self.b_out_tl, self.l_tl, self.l_bl, self.b_out_bl)

    def top_edge(self) -> None:
        self.mesh.add_quad(self.u_tr, self.u_tl, self.l_tl, self.l_tr)

    def top_edge_right(self, kh: KeyHole) -> None:
        self.mesh.add_quad(kh.u_tl, self.u_tr, self.l_tr, kh.l_tl)

    def bottom_edge(self) -> None:
        self.mesh.add_quad(self.u_bl, self.u_br, self.l_br, self.l_bl)

    def bottom_edge_right(self, kh: KeyHole) -> None:
        self.mesh.add_quad(self.u_br, kh.u_bl, kh.l_bl, self.l_br)

    def left_edge(self) -> None:
        self.mesh.add_quad(self.u_tl, self.u_bl, self.l_bl, self.l_tl)

    def right_edge(self) -> None:
        self.mesh.add_quad(self.u_br, self.u_tr, self.l_tr, self.l_br)

    def join_bottom(self, kh: KeyHole) -> None:
        # Join this key hole to one below it
        KeyHole.top_bottom_quad(self.bl, self.br, kh.tr, kh.tl)

    def left_edge_bottom(self, kh: KeyHole) -> None:
        self.mesh.add_quad(self.u_bl, kh.u_tl, kh.l_tl, self.l_bl)

    def right_edge_bottom(self, kh: KeyHole) -> None:
        self.mesh.add_quad(kh.u_tr, self.u_br, self.l_br, kh.l_tr)

    def join_right(self, kh: KeyHole) -> None:
        KeyHole.top_bottom_quad(self.tr, kh.tl, kh.bl, self.br)

    @staticmethod
    def join_corner(
        tl: KeyHole, tr: KeyHole, br: KeyHole, bl: KeyHole
    ) -> None:
        KeyHole.top_bottom_quad(tl.br, tr.bl, br.tl, bl.tr)

    @staticmethod
    def top_bottom_tri(
        p0: Tuple[MeshPoint, MeshPoint],
        p1: Tuple[MeshPoint, MeshPoint],
        p2: Tuple[MeshPoint, MeshPoint],
    ) -> None:
        mesh = p0[0].mesh
        mesh.add_tri(p0[0], p1[0], p2[0])
        mesh.add_tri(p2[1], p1[1], p0[1])

    @staticmethod
    def top_bottom_quad(
        p0: Tuple[MeshPoint, MeshPoint],
        p1: Tuple[MeshPoint, MeshPoint],
        p2: Tuple[MeshPoint, MeshPoint],
        p3: Tuple[MeshPoint, MeshPoint],
    ) -> None:
        mesh = p0[0].mesh
        mesh.add_quad(p0[0], p1[0], p2[0], p3[0])
        mesh.add_quad(p3[1], p2[1], p1[1], p0[1])


class WallColumn:
    __slots__ = ["out0", "out1", "out2", "out3", "in0", "in1", "in2", "in3"]

    def __init__(self) -> None:
        # Outer wall points, from the top of the wall to the bottom
        self.out0: Optional[MeshPoint] = None
        self.out1: Optional[MeshPoint] = None
        self.out2: Optional[MeshPoint] = None
        self.out3: Optional[MeshPoint] = None
        # Inner wall points, from the top of the wall to the bottom
        self.in0: Optional[MeshPoint] = None
        self.in1: Optional[MeshPoint] = None
        self.in2: Optional[MeshPoint] = None
        self.in3: Optional[MeshPoint] = None

    def get_rows(self) -> List[MeshPoint]:
        rows = [
            self.out0,
            self.out1,
            self.out2,
            self.out3,
            self.in3,
            self.in2,
            self.in1,
            self.in0,
        ]
        for p in rows:
            assert p is not None
        return rows


class WallPoints:
    """A class representing the points for the main wall sections.

    This is effectively a matrix of points defining quadrilaterals for the
    wall.
    """

    def __init__(self) -> None:
        self.columns: List[WallColumn] = []

    def add_faces(self, mesh: Mesh) -> None:
        for idx in range(len(self.columns) - 1):
            col0 = self.columns[idx].get_rows()
            col1 = self.columns[idx + 1].get_rows()
            for row in range(len(col0) - 1):
                mesh.add_quad(
                    col0[row], col1[row], col1[row + 1], col0[row + 1]
                )


def gen_keyboard() -> Mesh:
    kbd = Keyboard()
    kbd.gen_main_grid()
    kbd.gen_main_wall()

    kbd.gen_thumb_grid()
    kbd.gen_thumb_wall()

    if False:
        kbd.gen_main_grid_edges()
        kbd.gen_thumb_grid_edges()

    return kbd.mesh
