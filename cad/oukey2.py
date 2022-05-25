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
            return self._get_key_variable(name, self._keys, "thumb key")

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
        self.mesh.add_tri(
            self.k02.u_out_tr, self.k11.u_out_bl, self.k12.u_out_tl
        )
        self.mesh.add_tri(
            self.k02.m_out_tr, self.k12.m_out_tl, self.k11.m_out_bl
        )

        # Extra connector for the thumb area
        # top
        self.mesh.add_tri(
            self.k14.u_out_bl, self.k14.u_out_br, self.k24.u_out_bl
        )
        self.mesh.add_tri(
            self.k14.u_out_bl, self.k24.u_out_bl, self.k25.u_out_tl
        )
        self.mesh.add_tri(
            self.k14.u_out_bl, self.k25.u_out_tl, self.k25.u_out_bl
        )
        # bottom
        self.mesh.add_tri(
            self.k14.m_out_bl, self.k24.m_out_bl, self.k14.m_out_br
        )
        self.mesh.add_tri(
            self.k14.m_out_bl, self.k25.m_out_tl, self.k24.m_out_bl
        )
        self.mesh.add_tri(
            self.k14.m_out_bl, self.k25.m_out_bl, self.k25.m_out_tl
        )

    def gen_main_grid_edges(self) -> None:
        """Close off the edges around the main key grid section.

        Useful if we want to render the main grid section by itself, without
        normal walls dropping down to the ground.
        """
        # Wall on the corner section at the upper right of k02
        self.mesh.add_quad(
            self.k11.u_out_bl,
            self.k02.u_out_tr,
            self.k02.m_out_tr,
            self.k11.m_out_bl,
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
            self.k14.u_out_bl,
            self.k25.u_out_bl,
            self.k25.m_out_bl,
            self.k14.m_out_bl,
        )

    def gen_main_wall(self) -> None:
        back_wall = self.gen_back_wall()
        right_wall = self.gen_right_wall()
        front_wall = self.gen_front_wall()

        self.add_quad_matrix(back_wall.matrix())
        self.add_quad_matrix(right_wall.matrix())
        self.add_quad_matrix(front_wall.matrix())

    def gen_back_wall(self) -> WallPoints:
        u_near_off = 4.0
        m_near_off = 2.0
        far_off = Point(0.0, 6.0, -4.0)

        wp = WallPoints()
        for col in range(1, 7):
            k = self._keys[col][0]

            u_near_tl = k.add_point(
                -k.outer_w, k.outer_h + u_near_off, k.height
            )
            m_near_tl = k.add_point(
                -k.outer_w, k.outer_h + m_near_off, k.mid_height
            )

            u_near_tr = k.add_point(
                k.outer_w, k.outer_h + u_near_off, k.height
            )
            m_near_tr = k.add_point(
                k.outer_w, k.outer_h + m_near_off, k.mid_height
            )

            u_far_tl = self.mesh.add_point(u_near_tl.point.ptranslate(far_off))
            u_far_tr = self.mesh.add_point(u_near_tr.point.ptranslate(far_off))
            u_ground_tl = self.mesh.add_point(
                Point(u_far_tl.x, u_far_tl.y, 0.0)
            )
            u_ground_tr = self.mesh.add_point(
                Point(u_far_tr.x, u_far_tr.y, 0.0)
            )

            wp.u_wall_points += [k.u_out_tl, k.u_out_tr]
            wp.m_wall_points += [k.m_out_tl, k.m_out_tr]
            wp.u_near_points += [u_near_tl, u_near_tr]
            wp.u_far_points += [u_far_tl, u_far_tr]
            wp.u_ground_points += [u_ground_tl, u_ground_tr]
            wp.m_near_points += [m_near_tl, m_near_tr]

        max_y = max(p.point.y for p in wp.u_far_points)
        for p in wp.u_far_points:
            p.point.y = max_y
            wp.m_far_points.append(
                self.mesh.add_point(
                    Point(
                        p.point.x, p.point.y - self.wall_thickness, p.z - 3.0
                    )
                )
            )
        for p in wp.u_ground_points:
            p.point.y = max_y
            wp.m_ground_points.append(
                self.mesh.add_point(
                    Point(p.point.x, p.point.y - self.wall_thickness, 0.0)
                )
            )

        return wp

    def gen_right_wall(self) -> WallPoints:
        near_off = 4.5
        far_off = Point(0.6, 0, 0.0)

        wp = WallPoints()

        for row in range(6):
            k = self._keys[6][row]
            wp.u_wall_points += [k.u_out_tr, k.u_out_br]
            wp.m_wall_points += [k.m_out_tr, k.m_out_br]

            u_near_tr = k.add_point(k.outer_w + near_off, k.outer_h, k.height)
            u_near_br = k.add_point(k.outer_w + near_off, -k.outer_h, k.height)
            wp.u_near_points += [u_near_tr, u_near_br]

            m_near_tr = k.add_point(
                k.outer_w + near_off, k.outer_h, k.mid_height
            )
            m_near_br = k.add_point(
                k.outer_w + near_off, -k.outer_h, k.mid_height
            )
            wp.m_near_points += [m_near_tr, m_near_br]

        max_x = max(p.point.x for p in wp.u_near_points)
        for p in wp.u_near_points:
            p.point.x = max_x
        for p in wp.m_near_points:
            p.point.x = max_x - self.wall_thickness

        far_offset = 10.0
        for idx, p in enumerate(wp.m_near_points):
            if idx + 1 == len(wp.m_near_points):
                # At the front edge, just drop straight down
                u_far = k.mesh.add_point(Point(max_x, p.y, p.z - far_offset))
            else:
                # Compute the normal at this point along the wall,
                # Then add the far point along the normal

                normal = Point()
                if idx > 0:
                    prev_p = wp.m_near_points[idx - 1]
                    p_normal = Point(0, prev_p.z - p.z, p.y - prev_p.y).unit()
                    normal += p_normal
                if idx + 1 < len(wp.m_near_points):
                    next_p = wp.m_near_points[idx + 1]
                    n_normal = Point(0, p.z - next_p.z, next_p.y - p.y).unit()
                    normal += n_normal

                if idx == 0:
                    # At index 0 we only have 1 unit normal.
                    # We still want to shrink a bit here, to avoid extending
                    # past the back wall
                    normal *= 0.5 * far_offset
                else:
                    # We have added 2 unit normals, so we have to multiply by
                    # 0.5 to get back to a unit normal
                    normal *= 0.5 * far_offset
                    if idx == 1:
                        # Add a little more here to even some things out
                        normal *= 1.15

                u_far = k.mesh.add_point(
                    Point(max_x + normal.x, p.y + normal.y, p.z + normal.z)
                )

            m_far = Point(u_far.x - self.wall_thickness, u_far.y, u_far.z)
            u_ground = Point(u_far.x, u_far.y, 0.0)
            m_ground = Point(
                u_ground.x - self.wall_thickness, u_ground.y, u_ground.z
            )

            wp.u_far_points.append(u_far)
            wp.m_far_points.append(k.mesh.add_point(m_far))
            wp.u_ground_points.append(k.mesh.add_point(u_ground))
            wp.m_ground_points.append(k.mesh.add_point(m_ground))

        return wp

    def gen_front_wall(self) -> WallPoints:
        u_near_off = Point(0.0, -7.0, -2.0)
        m_near_off = Point(0.0, -0.5, 0.0)

        wp = WallPoints()
        last_row = 5
        for col in range(6, 2, -1):
            k = self._keys[col][last_row]
            wp.u_wall_points += [k.u_out_br, k.u_out_bl]
            wp.m_wall_points += [k.m_out_br, k.m_out_bl]

            u_near_bl = k.add_point(
                -k.outer_w + u_near_off.x,
                -k.outer_h + u_near_off.y,
                k.height + u_near_off.z,
            )
            u_near_br = k.add_point(
                k.outer_w + u_near_off.x,
                -k.outer_h + u_near_off.y,
                k.height + u_near_off.z,
            )
            wp.u_near_points += [u_near_br, u_near_bl]

            m_near_bl = k.add_point(
                -k.outer_w + m_near_off.x,
                -k.outer_h + m_near_off.y,
                k.mid_height + m_near_off.z,
            )
            m_near_br = k.add_point(
                k.outer_w + m_near_off.x,
                -k.outer_h + m_near_off.y,
                k.mid_height + m_near_off.z,
            )
            wp.m_near_points += [m_near_br, m_near_bl]

        min_y = min(p.point.y for p in wp.u_near_points)
        for p in wp.u_near_points:
            p.point.y = min_y
        for p in wp.m_near_points:
            new_y = min_y + self.wall_thickness
            if new_y > p.point.y:
                breakpoint()

            assert new_y <= p.point.y
            p.point.y = new_y

        far_offset = 10.0
        for idx, p in enumerate(wp.u_near_points):
            u_far = k.mesh.add_point(Point(p.x, p.y, p.z - far_offset))
            m_far = k.mesh.add_point(
                Point(u_far.x, u_far.y + self.wall_thickness, u_far.z)
            )

            u_ground = k.mesh.add_point(Point(u_far.x, u_far.y, 0.0))
            m_near = wp.m_near_points[idx]
            m_ground = k.mesh.add_point(Point(m_near.x, m_near.y, 0.0))

            wp.u_far_points.append(u_far)
            wp.m_far_points.append(m_far)
            wp.u_ground_points.append(u_ground)
            wp.m_ground_points.append(m_ground)

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

        tri = self.mesh.add_tri
        tri(self.t10.u_out_tr, self.t20.u_out_tr, self.t20.u_out_tl)
        tri(self.t10.m_out_tr, self.t20.m_out_tl, self.t20.m_out_tr)

        tri(self.t10.u_out_tr, self.t20.u_out_tl, self.t10.u_out_br)



class KeyHole:
    def __init__(self, mesh: Mesh, transform: Transform) -> None:
        from keyboard import (
            keyswitch_width,
            keyswitch_height,
            keywell_wall_width,
            plate_thickness,
            web_thickness,
        )

        self.mesh = mesh
        self.transform = transform

        inner_w = keyswitch_width * 0.5
        outer_w = inner_w + keywell_wall_width
        inner_h = keyswitch_height * 0.5
        outer_h = inner_h + keywell_wall_width

        self.outer_w = outer_w
        self.outer_h = outer_h
        self.height = plate_thickness
        # The height of the connecting mesh between key holes
        self.mid_height = plate_thickness - web_thickness

        add_point = self.add_point

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
        self.u_in_bl = add_point(-inner_w, -inner_h, self.height)
        self.u_in_br = add_point(inner_w, -inner_h, self.height)
        self.u_in_tr = add_point(inner_w, inner_h, self.height)
        self.u_in_tl = add_point(-inner_w, inner_h, self.height)

        # Upper outer points
        self.u_out_bl = add_point(-outer_w, -outer_h, self.height)
        self.u_out_br = add_point(outer_w, -outer_h, self.height)
        self.u_out_tr = add_point(outer_w, outer_h, self.height)
        self.u_out_tl = add_point(-outer_w, outer_h, self.height)

        # Mid outer points
        self.m_out_bl = add_point(-outer_w, -outer_h, self.mid_height)
        self.m_out_br = add_point(outer_w, -outer_h, self.mid_height)
        self.m_out_tr = add_point(outer_w, outer_h, self.mid_height)
        self.m_out_tl = add_point(-outer_w, outer_h, self.mid_height)

    def add_point(self, x: float, y: float, z: float) -> MeshPoint:
        p = Point(x, y, z).transform(self.transform)
        return self.mesh.add_point(p)

    def inner_walls(self) -> None:
        q = self.mesh.add_quad

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

    def top_edge(self) -> None:
        self.mesh.add_quad(
            self.u_out_tr, self.u_out_tl, self.m_out_tl, self.m_out_tr
        )

    def top_edge_right(self, kh: KeyHole) -> None:
        self.mesh.add_quad(
            kh.u_out_tl, self.u_out_tr, self.m_out_tr, kh.m_out_tl
        )

    def bottom_edge(self) -> None:
        self.mesh.add_quad(
            self.u_out_bl, self.u_out_br, self.m_out_br, self.m_out_bl
        )

    def bottom_edge_right(self, kh: KeyHole) -> None:
        self.mesh.add_quad(
            self.u_out_br, kh.u_out_bl, kh.m_out_bl, self.m_out_br
        )

    def left_edge(self) -> None:
        self.mesh.add_quad(
            self.u_out_tl, self.u_out_bl, self.m_out_bl, self.m_out_tl
        )

    def right_edge(self) -> None:
        self.mesh.add_quad(
            self.u_out_br, self.u_out_tr, self.m_out_tr, self.m_out_br
        )

    def join_bottom(self, kh: KeyHole) -> None:
        q = self.mesh.add_quad

        # Join this key hole to one below it
        q(self.u_out_bl, self.u_out_br, kh.u_out_tr, kh.u_out_tl)
        q(self.m_out_bl, kh.m_out_tl, kh.m_out_tr, self.m_out_br)

    def left_edge_bottom(self, kh: KeyHole) -> None:
        self.mesh.add_quad(
            self.u_out_bl, kh.u_out_tl, kh.m_out_tl, self.m_out_bl
        )

    def right_edge_bottom(self, kh: KeyHole) -> None:
        self.mesh.add_quad(
            kh.u_out_tr, self.u_out_br, self.m_out_br, kh.m_out_tr
        )

    def join_right(self, kh: KeyHole) -> None:
        q = self.mesh.add_quad

        q(self.u_out_tr, kh.u_out_tl, kh.u_out_bl, self.u_out_br)
        q(self.m_out_tr, self.m_out_br, kh.m_out_bl, kh.m_out_tl)

    @staticmethod
    def join_corner(
        tl: KeyHole, tr: KeyHole, br: KeyHole, bl: KeyHole
    ) -> None:
        q = tl.mesh.add_quad

        q(tl.u_out_br, tr.u_out_bl, br.u_out_tl, bl.u_out_tr)
        q(tl.m_out_br, bl.m_out_tr, br.m_out_tl, tr.m_out_bl)


class WallPoints:
    """A class representing the points for the main wall sections.

    This is effectively a matrix of points defining quadrilaterals for the
    wall.
    """

    def __init__(self) -> None:
        # The "u" section are the outer walls, connecting to the "upper" points
        # on each keyhole.
        self.u_wall_points: List[MeshPoint] = []
        self.u_near_points: List[MeshPoint] = []
        self.u_far_points: List[MeshPoint] = []
        self.u_ground_points: List[MeshPoint] = []
        # The "m" section are the inner walls, connecting to the "mid" points
        # on each keyhole.
        self.m_ground_points: List[MeshPoint] = []
        self.m_far_points: List[MeshPoint] = []
        self.m_near_points: List[MeshPoint] = []
        self.m_wall_points: List[MeshPoint] = []

    def matrix(self) -> List[List[MeshPoint]]:
        return [
            self.u_wall_points,
            self.u_near_points,
            self.u_far_points,
            self.u_ground_points,
            self.m_ground_points,
            self.m_far_points,
            self.m_near_points,
            self.m_wall_points,
        ]


def gen_keyboard() -> Mesh:
    kbd = Keyboard()
    kbd.gen_main_grid()
    # kbd.gen_main_grid_edges()
    kbd.gen_main_wall()

    kbd.gen_thumb_grid()

    return kbd.mesh
