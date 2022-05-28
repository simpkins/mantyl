#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

from cad import Mesh, Point, Transform, intersect_line_and_plane

import math
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

        self._bevel_edges: Dict[Tuple[int, int], float] = {}

    def gen_mesh(self, gen_walls: bool = True) -> None:
        self.gen_main_grid()
        self.gen_thumb_grid()

        if gen_walls:
            self.gen_walls()
        else:
            self.gen_main_grid_edges()
            self.gen_thumb_grid_edges()

    def add_quad_matrix(self, matrix: List[List[MeshPoint]]) -> None:
        for col in range(len(matrix) - 1):
            for row in range(len(matrix[col]) - 1):
                self.mesh.add_quad(
                    matrix[col][row],
                    matrix[col + 1][row],
                    matrix[col + 1][row + 1],
                    matrix[col][row + 1],
                )

    def _bevel_edge(
        self, p0: MeshPoint, p1: MeshPoint, weight: float = 1.0
    ) -> None:
        """Mark that a vertex is along an edge to be beveled."""
        if p0.index < p1.index:
            key = p0.index, p1.index
        else:
            key = p1.index, p0.index
        self._bevel_edges[key] = weight

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

    def gen_walls(self) -> None:
        # Main grid walls
        front_wall = self.gen_front_wall()
        right_wall = self.gen_right_wall()
        back_wall = self.gen_back_wall()
        left_wall = self.gen_left_wall()

        self.add_wall_faces(front_wall)
        self.add_wall_faces(right_wall)
        self.add_wall_faces(back_wall)
        self.add_wall_faces(left_wall)

        # The main wall corners
        self._front_right_wall_corner(front_wall[-1], right_wall[0])
        self._back_right_wall_corner(right_wall[-1], back_wall[0])
        self._back_left_wall_corner(back_wall[-1], left_wall)

        # Thumb walls
        thumb_wall = self.gen_thumb_wall()
        self.add_wall_faces(list(reversed(thumb_wall)))

        # Connections between the thumb area and main grid area
        self.gen_thumb_connect(thumb_wall, front_wall, left_wall)

    def add_wall_faces(
        self, columns: Union[List[WallColumn], List[ThumbColumn]]
    ) -> None:
        for idx in range(len(columns) - 1):
            col0 = columns[idx].get_rows()
            col1 = columns[idx + 1].get_rows()
            for row in range(len(col0) - 1):
                self.mesh.add_quad(
                    col0[row], col1[row], col1[row + 1], col0[row + 1]
                )

    def add_wall_corner(
        self,
        c0: WallColumn,
        c1: WallColumn,
        c2: WallColumn,
        start_row: int = 1,
    ) -> None:
        # Very similar to add_wall_faces(), but exclude the first and last rows
        # (out0 and in0)
        columns = (c0, c1, c2)
        for idx in range(len(columns) - 1):
            col0 = columns[idx].get_rows()
            col1 = columns[idx + 1].get_rows()
            for row in range(start_row, len(col0) - 2):
                self.mesh.add_quad(
                    col0[row], col1[row], col1[row + 1], col0[row + 1]
                )

        # Now handle the quads at out0 and in0
        self.mesh.add_quad(c0.in0, c0.in1, c1.in1, c2.in1)
        self.mesh.add_quad(c0.out0, c2.out1, c1.out1, c0.out1)

    def gen_back_wall(self) -> List[WallColumn]:
        u_near_off = 4.0
        l_near_off = 2.0
        far_off = Point(0.0, 6.0, -4.0)

        columns: List[WallColumn] = []
        for col in range(6, 0, -1):
            k = self._keys[col][0]

            # Left and right columns for this key hole
            l = WallColumn()
            r = WallColumn()
            columns += [r, l]

            l.out0 = k.u_tl
            l.in0 = k.l_tl
            r.out0 = k.u_tr
            r.in0 = k.l_tr

            l.out1 = k.add_point(-k.outer_w, k.outer_h + u_near_off, k.height)
            l.in1 = k.add_point(
                -k.outer_w, k.outer_h + l_near_off, k.mid_height
            )
            r.out1 = k.add_point(k.outer_w, k.outer_h + u_near_off, k.height)
            r.in1 = k.add_point(
                k.outer_w, k.outer_h + l_near_off, k.mid_height
            )

        for col in columns:
            col.out2 = self.mesh.add_point(col.out1.point.ptranslate(far_off))

        max_y = max(col.out2.y for col in columns)
        for idx, col in enumerate(columns):
            col.out2.point.y = max_y
            col.out3 = self.mesh.add_point(Point(col.out2.x, col.out2.y, 0.0))
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

            self._bevel_edge(col.out1, col.out2, 0.5)
            if idx + 1 < len(columns):
                self._bevel_edge(col.out1, columns[idx + 1].out1)
                self._bevel_edge(col.out2, columns[idx + 1].out2)

        return columns

    def gen_right_wall(self) -> List[WallColumn]:
        near_off = 4.5
        far_off = Point(0.6, 0, 0.0)

        columns: List[WallColumn] = []
        for row in range(5, -1, -1):
            k = self._keys[6][row]
            # top and bottom columns
            b = WallColumn()
            t = WallColumn()
            columns += [b, t]

            b.out0 = k.u_br
            t.out0 = k.u_tr
            b.in0 = k.l_br
            t.in0 = k.l_tr

            b.out1 = k.add_point(k.outer_w + near_off, -k.outer_h, k.height)
            t.out1 = k.add_point(k.outer_w + near_off, k.outer_h, k.height)

            b.in1 = k.add_point(k.outer_w + near_off, -k.outer_h, k.mid_height)
            t.in1 = k.add_point(k.outer_w + near_off, k.outer_h, k.mid_height)

        far_offset = 10.0
        max_x = max(col.out1.point.x for col in columns)
        for idx, col in enumerate(columns):
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

                prev_p = columns[idx - 1].out1
                p_normal = Point(0, prev_p.z - p.z, p.y - prev_p.y).unit()
                normal = p_normal
                if idx + 1 < len(columns):
                    next_p = columns[idx + 1].out1
                    n_normal = Point(0, p.z - next_p.z, next_p.y - p.y).unit()
                    normal += n_normal
                    # We have added 2 unit normals, so we have to multiply by
                    # 0.5 to get back to a unit normal
                    normal *= 0.5 * far_offset
                    if idx + 2 == len(columns):
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

            if idx + 1 < len(columns):
                self._bevel_edge(col.out1, columns[idx + 1].out1)

            self._bevel_edge(col.out0, col.out1)

        return columns

    def gen_front_wall(self) -> List[WallColumn]:
        u_near_off = Point(0.0, -5.0, -2.0)
        m_near_off = Point(0.0, -0.0, 0.0)

        columns: List[WallColumn] = []
        last_row = 5
        for col in range(2, 7):
            k = self._keys[col][last_row]

            # Left and right columns for this key hole
            l = WallColumn()
            r = WallColumn()
            columns += [l, r]

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

        # We want the front wall to start at the right-hand side of
        # key column 2, so drop the left side.
        del columns[0]

        min_y = min(col.out1.y for col in columns)

        # Also adjust min_y to make sure the inner wall won't hit k25
        k25_edge = Point(KeyHole.outer_w, -KeyHole.outer_h, 0).transform(
            self.k25.transform
        )
        min_y = min(min_y, k25_edge.y - self.wall_thickness - 0.25)

        far_offset = 10.0
        for col in columns:
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

        for idx in range(len(columns) - 1):
            c0 = columns[idx]
            c1 = columns[idx + 1]
            self._bevel_edge(c0.out1, c1.out1)

            self._bevel_edge(c0.out0, c1.out0, 0.5)
            self._bevel_edge(c0.out0, c0.out1)

        return columns

    def _left_wall_helper(
        self, indices: List[Tuple[int, int]], x_aligned: bool
    ) -> List[WallColumn]:
        u_near_off = -2.0
        l_near_off = -1.0
        far_off = Point(-6.0, 0.0, 0.0)

        columns: List[WallColumn] = []
        for col, row in indices:
            k = self._keys[col][row]

            t = WallColumn()
            b = WallColumn()
            columns += [t, b]

            t.out0 = k.u_tl
            b.out0 = k.u_bl
            t.in0 = k.l_tl
            b.in0 = k.l_bl

            t.out1 = k.add_point(-k.outer_w + u_near_off, k.outer_h, k.height)
            t.in1 = k.add_point(
                -k.outer_w + l_near_off, k.outer_h, k.mid_height
            )
            b.out1 = k.add_point(-k.outer_w + u_near_off, -k.outer_h, k.height)
            b.in1 = k.add_point(
                -k.outer_w + l_near_off, -k.outer_h, k.mid_height
            )

        for col in columns:
            col.out2 = self.mesh.add_point(col.out1.point.ptranslate(far_off))
        min_x = min(col.out2.x for col in columns)

        for col in columns:
            if x_aligned:
                # Make the line straight on the x axis
                col.out2.point.x = min_x
            elif False:
                # Straighten the wall between the two endpoints,
                # rather than along the x_axis
                start = columns[0].out2
                end = columns[-1].out2
                fraction = (col.out2.y - start.y) / (start.y - end.y)
                col.out2.point.x = start.x + fraction * (start.x - end.x)

            col.out3 = self.mesh.add_point(Point(col.out2.x, col.out2.y, 0.0))
            col.in3 = self.mesh.add_point(
                Point(col.out3.x + self.wall_thickness, col.out3.y, 0.0)
            )
            col.in2 = self.mesh.add_point(
                Point(col.in3.x, col.in3.y, col.out2.z - 3.0)
            )

        return columns

    def _left_wall_inner_corner(self) -> WallColumn:
        ic = WallColumn()
        k = self.k11

        ic.out0 = k.u_bl
        ic.in0 = k.l_bl

        ic.out1 = k.add_point(-k.outer_w - 2.0, -k.outer_h + 2.0, k.height)
        ic.in1 = k.add_point(-k.outer_w - 2.0, -k.outer_h + 2.0, k.mid_height)

        ic.in2 = self.mesh.add_point(
            Point(ic.in1.x - 0.2, ic.in1.y + 0.2, ic.in1.z)
        )
        ic.in3 = self.mesh.add_point(Point(ic.in2.x, ic.in2.y, 0.0))

        ic.out3 = self.mesh.add_point(
            Point(
                ic.in3.x - self.wall_thickness,
                ic.in3.y + self.wall_thickness,
                0.0,
            )
        )
        ic.out2 = self.mesh.add_point(Point(ic.out3.x, ic.out3.y, ic.out1.z))

        return ic

    def _left_wall_outer_corner(self, bottom_out_x: float) -> WallColumn:
        oc = WallColumn()
        k = self.k02

        oc.out0 = k.u_tl
        oc.in0 = k.l_tl

        oc.out1 = k.add_point(-k.outer_w - 2.0, k.outer_h + 2.0, k.height)
        oc.in1 = k.add_point(-k.outer_w - 2.0, k.outer_h + 2.0, k.mid_height)

        oc.out2 = self.mesh.add_point(
            Point(bottom_out_x, oc.out1.y + 6.0, oc.out1.z)
        )
        oc.out3 = self.mesh.add_point(Point(oc.out2.x, oc.out2.y, 0.0))
        oc.in3 = self.mesh.add_point(
            Point(
                oc.out3.x + self.wall_thickness,
                oc.out3.y - self.wall_thickness,
                0.0,
            )
        )
        oc.in2 = self.mesh.add_point(
            Point(oc.in3.x, oc.in3.y, oc.out2.z - 4.0)
        )

        return oc

    def _left_wall_straighten(self, segment: List[WallColumn]) -> None:
        dx = segment[0].out2.x - segment[-1].out2.x
        dy = segment[0].out2.y - segment[-1].out2.y

        for idx in range(1, len(segment) - 1):
            col = segment[idx]
            fx = (col.out2.x - segment[-1].out2.x) / dx
            fy = (col.out2.y - segment[-1].out2.y) / dy
            col.out2.point.x = segment[-1].out2.x + (fy * dx)

            col.out3.point.x = col.out2.x
            col.in3.point.x = col.out3.x + self.wall_thickness
            col.in2.point.x = col.in3.x

    def gen_left_wall(self) -> List[WallColumn]:
        ic = self._left_wall_inner_corner()

        # The top-most vertical segment
        segment0 = self._left_wall_helper([(1, 0), (1, 1)], x_aligned=False)
        # The bottom vertical segment
        segment2 = self._left_wall_helper(
            [(0, 2), (0, 3), (0, 4)], x_aligned=True
        )

        oc = self._left_wall_outer_corner(segment2[0].out3.x)

        # The last column of segment0 will be replaced by the inner corner
        segment0 = segment0[:-1] + [ic]

        # Straighten out segment0 between its first point and the inner corner
        self._left_wall_straighten(segment0)

        # Fill in one gap left where we connected the concave corner
        KeyHole.top_bottom_tri(self.k02.tl, self.k11.bl, self.k02.tr)

        columns = segment0[:-1] + [ic, oc] + segment2[1:-1]

        for idx in range(len(columns) - 1):
            c0 = columns[idx]
            c1 = columns[idx + 1]
            self._bevel_edge(c0.out2, c1.out2)
            self._bevel_edge(c0.out1, c1.out1, 0.5)

        for col in columns:
            self._bevel_edge(col.out1, col.out2, 0.5)

        self._bevel_edge(oc.out3, oc.out2)
        self._bevel_edge(oc.in3, oc.in2)
        self._bevel_edge(ic.out3, ic.out2)
        self._bevel_edge(ic.in3, ic.in2)

        return columns

    def _front_right_wall_corner(
        self, front: WallColumn, right: WallColumn
    ) -> None:
        fr = WallColumn()
        fr.out0 = self.k65.u_bl
        fr.in0 = self.k65.l_bl
        fr.out1 = self.mesh.add_point(
            Point(right.out1.x, front.out1.y, front.out1.z)
        )
        fr.in1 = self.mesh.add_point(
            Point(right.in1.x, front.in1.y, front.in1.z)
        )
        fr.out2 = self.mesh.add_point(
            Point(right.out2.x, front.out2.y, front.out2.z)
        )
        fr.in2 = self.mesh.add_point(
            Point(right.in2.x, front.in2.y, front.in2.z)
        )
        fr.out3 = self.mesh.add_point(
            Point(right.out3.x, front.out3.y, front.out3.z)
        )
        fr.in3 = self.mesh.add_point(
            Point(right.in3.x, front.in3.y, front.in3.z)
        )

        self.add_wall_corner(front, fr, right)

        self._bevel_edge(fr.out3, fr.out2)
        self._bevel_edge(fr.out2, fr.out1)
        self._bevel_edge(fr.in3, fr.in2, 0.5)
        self._bevel_edge(fr.in2, fr.in1, 0.5)

        self._bevel_edge(fr.out1, front.out1)
        self._bevel_edge(fr.out1, right.out1)

    def _back_right_wall_corner(
        self, right: WallColumn, back: WallColumn
    ) -> None:
        br = WallColumn()
        br.out0 = self.k65.u_bl
        br.in0 = self.k65.l_bl
        br.out1 = self.mesh.add_point(
            Point(right.out1.x, back.out1.y, back.out1.z)
        )
        br.in1 = self.mesh.add_point(
            Point(right.in1.x, back.in1.y, back.in1.z)
        )
        br.out2 = self.mesh.add_point(
            Point(right.out2.x, back.out2.y, back.out2.z)
        )
        br.in2 = self.mesh.add_point(
            Point(right.in2.x, back.in2.y, back.in2.z)
        )
        br.out3 = self.mesh.add_point(
            Point(right.out3.x, back.out3.y, back.out3.z)
        )
        br.in3 = self.mesh.add_point(
            Point(right.in3.x, back.in3.y, back.in3.z)
        )

        self.add_wall_corner(right, br, back)

        self._bevel_edge(br.out3, br.out2)
        self._bevel_edge(br.out2, br.out1)
        self._bevel_edge(br.out1, right.out1)
        self._bevel_edge(br.out1, back.out1)
        self._bevel_edge(br.out2, back.out2)

    def _back_left_wall_corner(
        self, back: WallColumn, left_wall: List[WallColumn]
    ) -> None:
        left = left_wall[0]
        last_left = left_wall[-1]

        # Make the X position line up with the left wall
        dx = left.out2.x - last_left.out2.x
        dy = left.out2.y - last_left.out2.y
        f = (back.out2.y - last_left.out2.y) / dy
        out_x = last_left.out2.x + f * dx

        in_x = out_x + 3.0
        assert in_x < back.in3.x

        # out_x = left.out2.x
        # in_x = left.in2.x

        bl = WallColumn()
        bl.out0 = self.k65.u_bl
        bl.in0 = self.k65.l_bl

        # bl.out1 = self.mesh.add_point(Point(left.out1.x, back.out1.y, back.out1.z))
        # bl.in1 = self.mesh.add_point(Point(left.in1.x, back.in1.y, back.in1.z))
        KH = KeyHole
        bl.out1 = self.k10.add_point(
            -KH.outer_w - 2.0, KH.outer_h + 3.0, KH.height
        )
        bl.in1 = self.k10.add_point(
            -KH.outer_w - 0.5, KH.outer_h + 1.0, KH.mid_height
        )

        bl.out2 = self.mesh.add_point(Point(out_x, back.out2.y, back.out2.z))
        bl.in2 = self.mesh.add_point(Point(in_x, back.in2.y, back.in2.z))
        bl.out3 = self.mesh.add_point(Point(out_x, back.out3.y, back.out3.z))
        bl.in3 = self.mesh.add_point(Point(in_x, back.in3.y, back.in3.z))

        # Some of the top corner faces aren't really flat here.
        # Prevent add_wall_corner() from adding row 1 as quads, and we will
        # add them ourselves as triangles, to ensure that they are subdivided
        # into the triangles we want.
        self.add_wall_corner(back, bl, left, start_row=2)
        self.mesh.add_tri(bl.out1, left.out1, left.out2)
        self.mesh.add_tri(bl.out1, left.out2, bl.out2)
        self.mesh.add_quad(bl.out1, bl.out2, back.out2, back.out1)

        self._bevel_edge(bl.out3, bl.out2)
        self._bevel_edge(bl.out2, bl.out1)

        self._bevel_edge(bl.out2, back.out2)
        self._bevel_edge(bl.out1, back.out1)

        self._bevel_edge(bl.out2, left.out2)
        self._bevel_edge(bl.out1, left.out2)

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

    def gen_thumb_wall(self) -> List[ThumbColumn]:
        offset = 7.0
        KH = KeyHole

        # Compute the outer corners
        br = ThumbColumn()
        br.out0 = self.t12.u_br
        br.in0 = self.t12.l_br
        br.out1 = self.t12.add_point(
            KH.outer_w, -KH.outer_h - offset, KH.height
        )
        br.out2 = self.mesh.add_point(Point(br.out1.x, br.out1.y, 0.0))

        bl = ThumbColumn()
        bl.out0 = self.t02.u_bl
        bl.in0 = self.t02.l_bl
        bl.out1 = self.t02.add_point(
            -KH.outer_w - offset, -KH.outer_h - offset, KH.height
        )
        bl.out2 = self.mesh.add_point(Point(bl.out1.x, bl.out1.y, 0.0))

        tl = ThumbColumn()
        tl.out0 = self.t00.u_tl
        tl.in0 = self.t00.l_tl
        tl.out1 = self.t00.add_point(
            -KH.outer_w - offset, KH.outer_h + offset, KH.height
        )
        tl.out2 = self.mesh.add_point(Point(tl.out1.x, tl.out1.y, 0.0))

        tr = ThumbColumn()
        tr.out0 = self.t10.u_tr
        tr.in0 = self.t10.l_tr
        tr.out1 = self.t10.add_point(
            KH.outer_w, KH.outer_h + offset, KH.height
        )
        tr.out2 = self.mesh.add_point(Point(tr.out1.x, tr.out1.y, 0.0))

        # Now compute the inner ground corner locations, to maintain a wall
        # thickness of self.wall_thickness.
        front_dx = br.out2.x - bl.out2.x
        front_dy = br.out2.y - bl.out2.y
        front_delta = (
            Point(-front_dy, front_dx, 0.0).unit() * self.wall_thickness
        )

        left_dx = bl.out2.x - tl.out2.x
        left_dy = bl.out2.y - tl.out2.y
        left_delta = Point(-left_dy, left_dx, 0.0).unit() * self.wall_thickness

        back_dx = tl.out2.x - tr.out2.x
        back_dy = tl.out2.y - tr.out2.y
        back_delta = Point(-back_dy, back_dx, 0.0).unit() * self.wall_thickness

        # Compute the inner ground corners now that we have
        # the inner wall offsets
        br.in2 = self.mesh.add_point(br.out2.point + front_delta)
        bl.in2 = self.mesh.add_point(bl.out2.point + front_delta + left_delta)
        tl.in2 = self.mesh.add_point(tl.out2.point + back_delta + left_delta)
        tr.in2 = self.mesh.add_point(tr.out2.point + back_delta)

        def in1_from_in2(in2: Point) -> Point:
            line = (Point(in2.x, in2.y, 0.0), Point(in2.x, in2.y, 1.0))
            plane = (
                self.t00.l_tl.point,
                self.t00.l_tr.point,
                self.t00.l_br.point,
            )
            intersect = intersect_line_and_plane(line, plane)
            if intersect is None:
                raise Exception("thumb grid is completely vertical")
            return Point(in2.x, in2.y, intersect.z)

        # Now compute the inner wall top points
        l_plane = (self.t00.l_tl, self.t00.l_tr, self.t00.l_br)
        br.in1 = self.mesh.add_point(in1_from_in2(br.in2))
        bl.in1 = self.mesh.add_point(in1_from_in2(bl.in2))
        tl.in1 = self.mesh.add_point(in1_from_in2(tl.in2))
        tr.in1 = self.mesh.add_point(in1_from_in2(tr.in2))

        def make_column(mp: MeshPoint, p0: Tuple[MeshPoint, MeshPoint], x_off: float, y_off: float, in_delta: Point) -> ThumbColumn:
            c = ThumbColumn()
            c.out0 = p0[0]
            c.in0 = p0[1]
            c.out1 = mp.add_point(x_off, y_off, KH.height)
            c.out2 = self.mesh.add_point(Point(c.out1.x, c.out1.y, 0.0))
            c.in2 = self.mesh.add_point(c.out2.point + in_delta)
            c.in1 = self.mesh.add_point(in1_from_in2(c.in2))
            return c

        def front_column(mp: MeshPoint, p0: Tuple[MeshPoint, MeshPoint], x_off: float) -> ThumbColumn:
            return make_column(mp, p0, x_off, -KH.outer_h - offset, front_delta)

        def left_column(mp: MeshPoint, p0: Tuple[MeshPoint, MeshPoint], y_off: float) -> ThumbColumn:
            return make_column(mp, p0, -KH.outer_w - offset, y_off, left_delta)

        def top_column(mp: MeshPoint, p0: Tuple[MeshPoint, MeshPoint], x_off: float) -> ThumbColumn:
            return make_column(mp, p0, x_off, KH.outer_h + offset, back_delta)

        columns = [
            br,
            front_column(self.t12, self.t12.bl, -KH.outer_w),
            front_column(self.t02, self.t02.br, KH.outer_w),
            bl,
            left_column(self.t02, self.t02.tl, KH.outer_h),
            left_column(self.t01, self.t01.bl, -KH.outer_h),
            left_column(self.t01, self.t01.tl, KH.outer_h),
            left_column(self.t00, self.t00.bl, -KH.outer_h),
            tl,
            top_column(self.t00, self.t00.tr, KH.outer_w),
            top_column(self.t10, self.t10.tl, -KH.outer_w),
            tr,
        ]

        for idx in range(len(columns) - 1):
            self._bevel_edge(columns[idx].out1, columns[idx + 1].out1)

        self._bevel_edge(bl.out2, bl.out1)
        self._bevel_edge(bl.in2, bl.in1, .75)
        self._bevel_edge(tl.out2, tl.out1)
        self._bevel_edge(tl.in2, tl.in1, .75)
        return columns

    def gen_thumb_connect(
        self,
        thumb_wall: List[ThumbColumn],
        front_wall: List[WallColumn],
        left_wall: List[WallColumn],
    ) -> None:
        bu0, bl0 = self.connect_thumb_front(thumb_wall, front_wall)
        (c0_in2, c1_in2, c2_in2, c3_in2), (
            c0_out2,
            c1_out2,
            c2_out2,
            c3_out2,
        ) = self.thumb_connect_top(front_wall, left_wall)

        KH = KeyHole

        # Top thumb area face from the thumb grid to the wall
        bu1 = self.t21.add_point(
            KH.outer_w + 8.0, -KH.outer_h + 2.0, KH.height
        )
        bu2 = self.t20.add_point(KH.outer_w + 4.0, KH.outer_h + 4.0, KH.height)
        bu3_x_offset = 3.0
        bu3 = self.t10.add_point(
            KH.outer_w + bu3_x_offset, KH.outer_h + 3.0, KH.height
        )

        self.mesh.add_quad(
            self.t12.u_br, self.t21.u_br, bu0, thumb_wall[0].out1
        )
        self.mesh.add_tri(self.t21.u_br, bu1, bu0)
        self.mesh.add_tri(self.t21.u_tr, bu1, self.t21.u_br)
        self.mesh.add_quad(self.t20.u_br, bu2, bu1, self.t21.u_tr)
        self.mesh.add_tri(self.t20.u_tr, bu2, self.t20.u_br)
        self.mesh.add_quad(bu3, bu2, self.t20.u_tr, self.t10.u_tr)

        thumb_wall_offset = 7.0
        bu4 = self.t10.add_point(
            KH.outer_w + bu3_x_offset,
            KH.outer_h + thumb_wall_offset,
            KH.height,
        )

        self.mesh.add_quad(bu3, self.t10.u_tr, thumb_wall[-1].out1, bu4)

        # Lower thumb area face from the thumb grid to the wall
        bl1 = self.t21.add_point(
            KH.outer_w + 10.0, -KH.outer_h + 4.0, KH.mid_height
        )
        bl2 = self.t20.add_point(
            KH.outer_w + 6.5, KH.outer_h + 5.5, KH.mid_height
        )
        bl3 = self.t10.add_point(
            KH.outer_w + 6.0, KH.outer_h + 3.0, KH.mid_height
        )

        self.mesh.add_quad(
            self.t12.l_br, thumb_wall[0].in1, bl0, self.t21.l_br
        )
        self.mesh.add_tri(self.t21.l_br, bl0, bl1)
        self.mesh.add_tri(self.t21.l_tr, self.t21.l_br, bl1)
        self.mesh.add_quad(self.t20.l_br, self.t21.l_tr, bl1, bl2)
        self.mesh.add_tri(self.t20.l_br, bl2, self.t20.l_tr)

        self.mesh.add_quad(self.t20.l_tr, bl2, bl3, self.t10.l_tr)
        self.mesh.add_tri(self.t10.l_tr, bl3, thumb_wall[-1].in1)
        self.mesh.add_tri(bl2, c3_in2, bl3)

        # Remaining vertical connection walls
        self.mesh.add_tri(bl0, front_wall[0].in2, c0_in2)
        self.mesh.add_tri(bl0, c0_in2, bl1)
        self.mesh.add_tri(bu0, c0_out2, front_wall[0].out2)
        self.mesh.add_tri(front_wall[0].out2, c0_out2, front_wall[0].out1)
        self.mesh.add_tri(bu0, bu1, c0_out2)

        self.mesh.add_quad(bl2, bl1, c0_in2, c1_in2)
        self.mesh.add_tri(bl2, c1_in2, c2_in2)
        self.mesh.add_tri(bl2, c2_in2, c3_in2)

        self.mesh.add_quad(bu1, bu2, c1_out2, c0_out2)
        self.mesh.add_tri(bu2, c2_out2, c1_out2)
        self.mesh.add_tri(bu2, c3_out2, c2_out2)
        self.mesh.add_tri(bu2, bu3, c3_out2)

        self.mesh.add_quad(bu3, bu4, left_wall[-1].out2, c3_out2)

        self.connect_thumb_left(thumb_wall, left_wall, bu4, bl3, c3_in2)

        self._bevel_edge(bu3, c3_out2)

    def connect_thumb_front(
        self, thumb_wall: List[ThumbColumn], front_wall: List[WallColumn]
    ) -> None:
        def find_y_intersect(
            p1: MeshPoint, p2: MeshPoint, y: float
        ) -> MeshPoint:
            d = p2.point - p1.point
            f = (y - p2.y) / d.y
            x = p2.x + f * d.x
            z = p2.z + f * d.z
            return self.mesh.add_point(Point(x, y, z))

        # Connect front thumb wall to front wall
        # Find the intersection point between the two outer walls
        o = find_y_intersect(
            thumb_wall[0].out1, thumb_wall[1].out1, front_wall[0].out1.y
        )
        og = self.mesh.add_point(Point(o.x, o.y, 0.0))

        # Find the intersection point between the two inner walls
        i = find_y_intersect(
            thumb_wall[0].in1, thumb_wall[1].in1, front_wall[0].in1.y
        )
        ig = self.mesh.add_point(Point(i.x, i.y, 0.0))

        self.mesh.add_quad(thumb_wall[0].out1, o, og, thumb_wall[0].out2)
        self.mesh.add_quad(thumb_wall[0].in1, thumb_wall[0].in2, ig, i)
        self.mesh.add_quad(thumb_wall[0].out2, og, ig, thumb_wall[0].in2)
        self.mesh.add_quad(og, front_wall[0].out3, front_wall[0].in3, ig)
        self.mesh.add_quad(o, front_wall[0].out2, front_wall[0].out3, og)
        self.mesh.add_quad(i, ig, front_wall[0].in3, front_wall[0].in2)

        self._bevel_edge(thumb_wall[0].out1, o)

        return o, i

    def connect_thumb_left(
        self,
        thumb_wall: List[ThumbColumn],
        left_wall: List[WallColumn],
        bu4: MeshPoint,
        bl3: MeshPoint,
        c3_in2: MeshPoint,
    ) -> None:
        def find_x_intersect(
            p1: MeshPoint, p2: MeshPoint, x: float
        ) -> MeshPoint:
            d = p2.point - p1.point
            f = (x - p2.x) / d.x
            y = p2.y + f * d.y
            z = p2.z + f * d.z
            return self.mesh.add_point(Point(x, y, z))

        o = find_x_intersect(
            thumb_wall[-1].out1, thumb_wall[-2].out1, left_wall[-1].out2.x
        )
        og = self.mesh.add_point(Point(o.x, o.y, 0.0))
        i = find_x_intersect(
            thumb_wall[-1].in1, thumb_wall[-2].in1, left_wall[-1].in2.x
        )
        ig = self.mesh.add_point(Point(i.x, i.y, 0.0))

        bu4g = self.mesh.add_point(Point(bu4.x, bu4.y, 0.0))
        bl3g = self.mesh.add_point(Point(bl3.x, bl3.y, 0.0))

        self.mesh.add_quad(left_wall[-1].out3, left_wall[-1].out2, o, og)
        self.mesh.add_tri(o, left_wall[-1].out2, bu4)

        self.mesh.add_quad(og, o, bu4, bu4g)
        self.mesh.add_quad(bu4g, bu4, thumb_wall[-1].out1, thumb_wall[-1].out2)

        self.mesh.add_quad(thumb_wall[-1].in2, bl3g, bu4g, thumb_wall[-1].out2)
        self.mesh.add_quad(thumb_wall[-1].in2, thumb_wall[-1].in1, bl3, bl3g)
        self.mesh.add_quad(bl3g, bl3, i, ig)
        self.mesh.add_quad(bu4g, bl3g, ig, og)
        self.mesh.add_quad(og, ig, left_wall[-1].in3, left_wall[-1].out3)

        self.mesh.add_quad(ig, i, left_wall[-1].in2, left_wall[-1].in3)

        self.mesh.add_tri(left_wall[-1].in2, bl3, c3_in2)
        self.mesh.add_tri(left_wall[-1].in2, i, bl3)

        self._bevel_edge(thumb_wall[-1].out1, bu4)
        self._bevel_edge(left_wall[-1].out2, bu4)

    def thumb_connect_top(
        self, front_wall: List[WallColumn], left_wall: List[WallColumn]
    ) -> None:
        KH = KeyHole
        c0_out1 = self.k25.add_point(
            -KH.outer_w - 1.5, -KH.outer_h - 1.5, KH.height
        )
        c0_out2 = self.k25.add_point(
            -KH.outer_w - 1.5, -KH.outer_h - 1.5, KH.height - 7.0
        )
        self.mesh.add_quad(
            self.k25.u_bl, self.k25.u_br, front_wall[0].out1, c0_out1
        )
        self.mesh.add_tri(c0_out1, front_wall[0].out1, c0_out2)

        c0_in1 = self.k25.add_point(
            -KH.outer_w - 0.25, -KH.outer_h - 0.25, KH.mid_height
        )
        c0_in2 = self.k25.add_point(
            -KH.outer_w - 0.25, -KH.outer_h - 0.25, KH.mid_height - 3.0
        )

        # The top portion of wall in front of k25
        self.mesh.add_quad(
            front_wall[0].in0, self.k25.l_bl, c0_in1, front_wall[0].in1
        )
        self.mesh.add_tri(front_wall[0].in1, c0_in1, c0_in2)
        self.mesh.add_tri(front_wall[0].in1, c0_in2, front_wall[0].in2)

        # The wall down the triangular section between k25 and k14
        c1_out1 = self.k14.add_point(
            -KH.outer_w - 1.5, -KH.outer_h - 1.5, KH.height
        )
        c1_out2 = self.k14.add_point(
            -KH.outer_w - 1.5, -KH.outer_h - 1.5, KH.height - 7.0
        )
        c1_in1 = self.k14.add_point(
            -KH.outer_w - 0.25, -KH.outer_h - 0.25, KH.mid_height
        )
        c1_in2 = self.k14.add_point(
            -KH.outer_w - 0.25, -KH.outer_h - 0.25, KH.mid_height - 3.0
        )
        self.mesh.add_quad(self.k14.l_bl, c1_in1, c0_in1, self.k25.l_bl)
        self.mesh.add_quad(c1_in1, c1_in2, c0_in2, c0_in1)
        self.mesh.add_quad(self.k14.u_bl, self.k25.u_bl, c0_out1, c1_out1)
        self.mesh.add_quad(c1_out1, c0_out1, c0_out2, c1_out2)

        # The wall down between k14 and k04
        c2_out1 = self.k04.add_point(
            KH.outer_w - 1.5, -KH.outer_h - 2.0, KH.height
        )
        c2_out2 = self.k04.add_point(
            KH.outer_w - 1.5, -KH.outer_h - 2.0, KH.height - 7.0
        )
        c2_in1 = self.k04.add_point(
            KH.outer_w - 0.25, -KH.outer_h - 0.50, KH.mid_height
        )
        c2_in2 = self.k04.add_point(
            KH.outer_w - 0.25, -KH.outer_h - 0.50, KH.mid_height - 3.0
        )
        self.mesh.add_quad(self.k04.l_br, c2_in1, c1_in1, self.k14.l_bl)
        self.mesh.add_quad(c2_in1, c2_in2, c1_in2, c1_in1)
        self.mesh.add_quad(self.k04.u_br, self.k14.u_bl, c1_out1, c2_out1)
        self.mesh.add_quad(c2_out1, c1_out1, c1_out2, c2_out2)

        # The wall down the front of k04
        c3_out1 = self.k04.add_point(
            -KH.outer_w - 3.5, -KH.outer_h - 2.0, KH.height
        )
        c3_out2 = self.k04.add_point(
            -KH.outer_w - 3.5, -KH.outer_h - 2.0, KH.height - 7.0
        )
        c3_in1 = self.k04.add_point(
            -KH.outer_w - 1.5, -KH.outer_h - 0.50, KH.mid_height
        )
        c3_in2 = self.k04.add_point(
            -KH.outer_w - 1.5, -KH.outer_h - 0.50, KH.mid_height - 3.0
        )
        self.mesh.add_quad(self.k04.l_bl, c3_in1, c2_in1, self.k04.l_br)
        self.mesh.add_quad(c3_in1, c3_in2, c2_in2, c2_in1)
        self.mesh.add_quad(self.k04.u_bl, self.k04.u_br, c2_out1, c3_out1)
        self.mesh.add_quad(c3_out1, c2_out1, c2_out2, c3_out2)

        # The wall to the left of k04
        # This section is a little irregular
        self.mesh.add_quad(
            self.k04.l_tl, left_wall[-1].in1, c3_in1, self.k04.l_bl
        )
        self.mesh.add_tri(left_wall[-1].in1, left_wall[-1].in2, c3_in1)
        self.mesh.add_tri(left_wall[-1].in2, c3_in2, c3_in1)

        self.mesh.add_quad(
            self.k04.u_tl, self.k04.u_bl, c3_out1, left_wall[-1].out1
        )
        self.mesh.add_tri(left_wall[-1].out1, c3_out1, left_wall[-1].out2)
        self.mesh.add_tri(left_wall[-1].out2, c3_out1, c3_out2)

        self._bevel_edge(front_wall[0].out1, c0_out1, 0.5)
        self._bevel_edge(c0_out1, c1_out1, 0.5)
        self._bevel_edge(c1_out1, c2_out1, 0.5)
        self._bevel_edge(c2_out1, c3_out1, 0.5)

        self._bevel_edge(front_wall[0].out1, c0_out2, 0.5)
        self._bevel_edge(c0_out2, c1_out2)
        self._bevel_edge(c1_out2, c2_out2)
        self._bevel_edge(c2_out2, c3_out2)

        self._bevel_edge(c3_out2, c3_out1)

        return (
            (c0_in2, c1_in2, c2_in2, c3_in2),
            (c0_out2, c1_out2, c2_out2, c3_out2),
        )

    def get_bevel_weights(self, edges) -> Dict[int, float]:
        results: Dict[int, float] = {}
        for idx, e in enumerate(edges):
            v0 = e.vertices[0]
            v1 = e.vertices[1]
            if v0 < v1:
                key = v0, v1
            else:
                key = v1, v0

            weight = self._bevel_edges.get(key, 0.0)
            if weight > 0.0:
                results[idx] = weight

        return results


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

        outer_w = self.outer_w
        outer_h = self.outer_h

        # Upper outer points.
        # These are the main connection points used externally for the walls
        self.u_bl = self.add_point(-outer_w, -outer_h, self.height)
        self.u_br = self.add_point(outer_w, -outer_h, self.height)
        self.u_tr = self.add_point(outer_w, outer_h, self.height)
        self.u_tl = self.add_point(-outer_w, outer_h, self.height)

        # Lower outer points.
        # These are also connection points used externally,
        # for the underside of the walls
        self.l_bl = self.add_point(-outer_w, -outer_h, self.mid_height)
        self.l_br = self.add_point(outer_w, -outer_h, self.mid_height)
        self.l_tr = self.add_point(outer_w, outer_h, self.mid_height)
        self.l_tl = self.add_point(-outer_w, outer_h, self.mid_height)

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
        quad = self.mesh.add_quad
        tri = self.mesh.add_tri

        outer_w = self.outer_w
        outer_h = self.outer_h
        inner_w = self.inner_w
        inner_h = self.inner_h

        nub_h = 2.75 * 0.5
        nub_r = 1

        # Upper inner points
        u_in_bl = self.add_point(-inner_w, -inner_h, self.height)
        u_in_br = self.add_point(inner_w, -inner_h, self.height)
        u_in_tr = self.add_point(inner_w, inner_h, self.height)
        u_in_tl = self.add_point(-inner_w, inner_h, self.height)

        # Bottom-most inner points.
        # The bottom-most points extend slightly below the "lower" points
        # used for connections to the walls.
        b_in_bl = self.add_point(-inner_w, -inner_h, 0.0)
        b_in_br = self.add_point(inner_w, -inner_h, 0.0)
        b_in_tr = self.add_point(inner_w, inner_h, 0.0)
        b_in_tl = self.add_point(-inner_w, inner_h, 0.0)

        # Bottom-most outer points
        b_out_bl = self.add_point(-outer_w, -outer_h, 0.0)
        b_out_br = self.add_point(outer_w, -outer_h, 0.0)
        b_out_tr = self.add_point(outer_w, outer_h, 0.0)
        b_out_tl = self.add_point(-outer_w, outer_h, 0.0)

        # Bottom section
        quad(u_in_bl, b_in_bl, b_in_br, u_in_br)
        quad(u_in_bl, u_in_br, self.u_br, self.u_bl)
        quad(b_in_bl, b_out_bl, b_out_br, b_in_br)
        quad(b_out_bl, self.l_bl, self.l_br, b_out_br)

        # Top section
        quad(u_in_tr, b_in_tr, b_in_tl, u_in_tl)
        quad(u_in_tr, u_in_tl, self.u_tl, self.u_tr)
        quad(b_in_tr, b_out_tr, b_out_tl, b_in_tl)
        quad(b_out_tr, self.l_tr, self.l_tl, b_out_tl)

        # Left section, except for the nub
        u_mid_bl = self.add_point(-inner_w, -nub_h, self.height)
        u_mid_tl = self.add_point(-inner_w, nub_h, self.height)
        b_mid_bl = self.add_point(-inner_w, -nub_h, 0)
        b_mid_tl = self.add_point(-inner_w, nub_h, 0)
        lnub_center_b = self.add_point(-inner_w, -nub_h, nub_r)
        lnub_center_t = self.add_point(-inner_w, nub_h, nub_r)

        quad(self.u_bl, self.u_tl, u_mid_tl, u_mid_bl)
        tri(self.u_bl, u_mid_bl, u_in_bl)
        tri(u_mid_tl, self.u_tl, u_in_tl)
        quad(b_out_tl, b_out_bl, b_mid_bl, b_mid_tl)
        tri(b_out_bl, b_in_bl, b_mid_bl)
        tri(b_out_tl, b_mid_tl, b_in_tl)
        quad(b_out_tl, self.l_tl, self.l_bl, b_out_bl)
        quad(u_in_bl, lnub_center_b, b_mid_bl, b_in_bl)
        tri(u_in_bl, u_mid_bl, lnub_center_b)
        quad(lnub_center_t, u_in_tl, b_in_tl, b_mid_tl)
        tri(u_mid_tl, u_in_tl, lnub_center_t)

        # Right section, except for the nub
        u_mid_br = self.add_point(inner_w, -nub_h, self.height)
        u_mid_tr = self.add_point(inner_w, nub_h, self.height)
        b_mid_br = self.add_point(inner_w, -nub_h, 0)
        b_mid_tr = self.add_point(inner_w, nub_h, 0)
        rnub_center_b = self.add_point(inner_w, -nub_h, nub_r)
        rnub_center_t = self.add_point(inner_w, nub_h, nub_r)

        quad(self.u_br, u_mid_br, u_mid_tr, self.u_tr)
        tri(self.u_br, u_in_br, u_mid_br)
        tri(u_mid_tr, u_in_tr, self.u_tr)
        quad(b_out_br, b_out_tr, b_mid_tr, b_mid_br)
        tri(b_out_br, b_mid_br, b_in_br)
        tri(b_mid_tr, b_out_tr, b_in_tr)
        quad(b_out_br, self.l_br, self.l_tr, b_out_tr)
        quad(u_in_tr, rnub_center_t, b_mid_tr, b_in_tr)
        tri(u_in_tr, u_mid_tr, rnub_center_t)
        quad(rnub_center_b, u_in_br, b_in_br, b_mid_br)
        tri(u_mid_br, u_in_br, rnub_center_b)

        # The left nub
        prev_b = b_mid_bl
        prev_t = b_mid_tl
        for angle in range(0, 110, 12):
            rad = math.radians(angle)
            x = math.sin(rad) * nub_r
            z = nub_r - (nub_r * math.cos(rad))
            b = self.add_point(-inner_w + x, -nub_h, z)
            t = self.add_point(-inner_w + x, nub_h, z)

            tri(lnub_center_b, b, prev_b)
            tri(lnub_center_t, prev_t, t)
            quad(prev_b, b, t, prev_t)

            prev_b = b
            prev_t = t

        tri(u_mid_bl, prev_b, lnub_center_b)
        tri(u_mid_tl, lnub_center_t, prev_t)
        quad(u_mid_bl, u_mid_tl, prev_t, prev_b)

        # The right nub
        prev_b = b_mid_br
        prev_t = b_mid_tr
        for angle in range(0, 110, 12):
            rad = math.radians(angle)
            x = math.sin(rad) * nub_r
            z = nub_r - (nub_r * math.cos(rad))
            b = self.add_point(inner_w - x, -nub_h, z)
            t = self.add_point(inner_w - x, nub_h, z)

            tri(rnub_center_b, prev_b, b)
            tri(rnub_center_t, t, prev_t)
            quad(t, b, prev_b, prev_t)

            prev_b = b
            prev_t = t

        tri(u_mid_br, rnub_center_b, prev_b)
        tri(u_mid_tr, prev_t, rnub_center_t)
        quad(u_mid_tr, u_mid_br, prev_b, prev_t)

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
    """A class representing a vertical column of points in the main grid walls.
    """

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


class ThumbColumn:
    """A class representing a vertical column of points in the thumb walls.
    """

    __slots__ = ["out0", "out1", "out2", "out3", "in0", "in1", "in2", "in3"]

    def __init__(self) -> None:
        # Outer wall points, from the top of the wall to the bottom
        self.out0: Optional[MeshPoint] = None
        self.out1: Optional[MeshPoint] = None
        self.out2: Optional[MeshPoint] = None
        # Inner wall points, from the top of the wall to the bottom
        self.in0: Optional[MeshPoint] = None
        self.in1: Optional[MeshPoint] = None
        self.in2: Optional[MeshPoint] = None

    def get_rows(self) -> List[MeshPoint]:
        rows = [self.out0, self.out1, self.out2, self.in2, self.in1, self.in0]
        for p in rows:
            assert p is not None
        return rows


def gen_keyboard() -> Mesh:
    kbd = Keyboard()
    kbd.gen_mesh()
    return kbd.mesh
