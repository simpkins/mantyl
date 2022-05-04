#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List, Tuple, TypeVar

from cad import Point, Shape, Transform, tri_strip
from keyboard import (
    corner_tl,
    corner_tr,
    corner_bl,
    corner_br,
    dsa_cap,
    mount_width,
    mount_height,
    plate_thickness,
    single_plate,
)

ShapeOrTransform = TypeVar("ShapeOrTransform", Shape, Transform)

dsa_profile_key_height = 7.4
cap_top_height = plate_thickness + dsa_profile_key_height
extra_width = 2.5  # extra space between keyhole mounts
extra_height = 0  # extra space between keyhole mounts


class WallPost:
    """
    WallPost contains point information about a single vertical portion of the
    outer walls, from one corner of a key hole down to the ground.
    """

    def __init__(
        self, post: Shape, near_corner: Point, far_corner: Point
    ) -> None:
        self.post = post
        self.near = near_corner
        self.far = far_corner


class MyKeyboard:
    def __init__(self) -> None:
        self.num_columns = 6
        self.num_rows = 6
        self.key_hole = single_plate()

        self.center_col = 3
        self.center_row = self.num_rows - 3
        self.col_curvature = 18.0
        self.row_curvature = 5.0

        self.row_radius = cap_top_height + (
            (mount_height + extra_height)
            / (2 * math.sin(math.radians(self.col_curvature / 2)))
        )
        self.col_radius = cap_top_height + (
            (mount_width + extra_width)
            / (2 * math.sin(math.radians(self.row_curvature / 2)))
        )
        self.col_x_delta = (
            -1 - math.sin(math.radians(self.row_curvature)) * self.col_radius
        )

        self.tenting_angle = 15
        self.keyboard_z_offset: float = 9.0

        # Wall thickness = 2 * wall_radius
        self.wall_radius = 2

    def key_indices(self) -> Generator[Tuple[int, int], None, None]:
        for column in range(self.num_columns):
            for row in range(self.num_rows):
                if row == (self.num_rows - 1) and column == 0:
                    # Skip the lower inner corner, to make room
                    # for thumb keys instead.
                    continue
                yield (column, row)

        # Add an extra inner column of 3 keys
        yield (-1, 2)
        yield (-1, 3)
        yield (-1, 4)

    def key_positions(self, comment_name: str, shape: Shape) -> List[Shape]:
        shapes: List[Shape] = []
        for (column, row) in self.key_indices():
            hole = self.place_key(shape, column, row).comment(
                f"{comment_name} (c={column}, r={row})"
            )
            shapes.append(hole)

        return shapes

    def key_holes(self) -> List[Shape]:
        return self.key_positions("Key", self.key_hole)

    def key_caps(self) -> Shape:
        cap = dsa_cap()
        return Shape.union(self.key_positions("Keycap", cap))

    def key_collisions(self) -> Shape:
        cap = dsa_cap(include_base=True)
        shapes: List[Shape] = []

        positions = set(self.key_indices())
        for column in range(self.num_columns):
            for row in range(self.num_rows):
                if (column, row) not in positions:
                    continue

                for pos in (
                    (column, row - 1),
                    (column, row + 1),
                    (column - 1, row),
                    (column + 1, row),
                ):
                    if pos not in positions:
                        continue
                    shapes.append(
                        Shape.intersection(
                            [
                                self.place_key(cap, column, row),
                                self.place_key(cap, pos[0], pos[1]),
                            ]
                        )
                    )

        return Shape.union(shapes)

    def column_offset(self, column: int) -> Tuple[float, float, float]:
        if column == 2:
            return (0.0, 2.82, -4.5)
        if column >= 4:
            return (0.0, -12.0, 5.64)
        return (0.0, 0.0, 0.0)

    def place_key(
        self, shape: ShapeOrTransform, column: int, row: int
    ) -> ShapeOrTransform:
        if column == 0:
            return self.place_key_col0(shape, row)
        elif column == 1:
            return self.place_key_col1(shape, row)
        elif column == 2:
            return self.place_key_col2(shape, row)
        elif column == 3:
            return self.place_key_col3(shape, row)
        elif column == 4:
            return self.place_key_col4(shape, row)
        elif column == 5:
            return self.place_key_col5(shape, row)
        elif column == -1:
            return self.place_key_col_extra(shape, row)
        raise Exception("invalid key col, row: ({column}, {row})")

    def place_key_col0(
        self, shape: ShapeOrTransform, row: int
    ) -> ShapeOrTransform:
        if row == 0:
            shape = shape.rotate(0, 0, 8)
            shape = shape.rotate(48, 0, 0)
            shape = shape.translate(-2, 56, 32)
        elif row == 1:
            shape = shape.rotate(0, 0, 4)
            shape = shape.rotate(0, 3, 0)
            shape = shape.rotate(38, 0, 0)
            shape = shape.translate(0, 40.5, 18)
        elif row == 2:
            shape = shape.rotate(12, 0, 0)
            shape = shape.translate(0, 18, 9)
        elif row == 3:
            shape = shape.rotate(10, 0, 0)
            shape = shape.translate(0, -1.25, 5)
        elif row == 4:
            shape = shape.rotate(0, 0, 0)
            shape = shape.translate(0, -22, 4)
        else:
            raise Exception("invalid col, row: (0, {row})")

        shape = shape.rotate(0, 0, 5)
        shape = shape.rotate(0, 29, 0)
        shape = shape.translate(-60.5, -5, 45)
        return shape

    def place_key_col1(
        self, shape: ShapeOrTransform, row: int
    ) -> ShapeOrTransform:
        if row == 0:
            shape = shape.rotate(0, 0, 8)
            shape = shape.rotate(0, 4, 0)
            shape = shape.rotate(52, 0, 0)
            shape = shape.translate(-2, 57, 34)
        elif row == 1:
            shape = shape.rotate(0, 0, 5)
            shape = shape.rotate(0, 3, 0)
            shape = shape.rotate(38, 0, 0)
            shape = shape.translate(0, 42, 17.5)
        elif row == 2:
            shape = shape.rotate(18, 0, 0)
            shape = shape.translate(0, 20.5, 8)
        elif row == 3:
            shape = shape.rotate(6, 0, 0)
            shape = shape.translate(0, -1.25, 5)
        elif row == 4:
            shape = shape.rotate(3, 0, 0)
            shape = shape.translate(0, -21, 4)
        elif row == 5:
            shape = shape.rotate(-22, 0, 0)
            shape = shape.translate(0, -44, 8)
        else:
            raise Exception(f"invalid col, row: (1, {row})")

        shape = shape.rotate(0, 0, 5)
        shape = shape.rotate(0, 28, 0)
        shape = shape.translate(-43, -5, 35)
        return shape

    def place_key_col2(
        self, shape: ShapeOrTransform, row: int
    ) -> ShapeOrTransform:
        if row == 0:
            shape = shape.rotate(0, 0, 6)
            shape = shape.rotate(0, 5, 0)
            shape = shape.rotate(60, 0, 0)
            shape = shape.translate(-2, 59, 36)
        elif row == 1:
            shape = shape.rotate(0, 0, 3)
            shape = shape.rotate(0, 3, 0)
            shape = shape.rotate(46, 0, 0)
            shape = shape.translate(0, 45, 18)
        elif row == 2:
            shape = shape.rotate(15, 0, 0)
            shape = shape.translate(0, 24, 3.25)
        elif row == 3:
            shape = shape.rotate(-3, 0, 0)
            shape = shape.translate(0, 1, 2)
        elif row == 4:
            shape = shape.rotate(-10, 0, 0)
            shape = shape.translate(0, -19, 4.5)
        elif row == 5:
            shape = shape.rotate(-30, 0, 0)
            shape = shape.translate(0, -40.5, 11.5)
        else:
            raise Exception(f"invalid col, row: (1, {row})")

        shape = shape.rotate(0, 0, 3)
        shape = shape.rotate(0, 20, 0)
        shape = shape.translate(-21, -5, 24)
        return shape

    def place_key_col3(
        self, shape: ShapeOrTransform, row: int
    ) -> ShapeOrTransform:
        if row == 0:
            shape = shape.rotate(0, 0, 1)
            shape = shape.rotate(0, 5, 0)
            shape = shape.rotate(60, 0, 0)
            shape = shape.translate(1, 62, 32)
        elif row == 1:
            shape = shape.rotate(0, 0, 0)
            shape = shape.rotate(0, 3, 0)
            shape = shape.rotate(44, 0, 0)
            shape = shape.translate(0, 48.5, 14)
        elif row == 2:
            shape = shape.rotate(19, 0, 0)
            shape = shape.translate(0, 25.5, 2.5)
        elif row == 3:
            shape = shape.rotate(0, 0, 0)
            shape = shape.translate(0, 3, 0)
        elif row == 4:
            shape = shape.rotate(-10, 0, 0)
            shape = shape.translate(0, -19, 2)
        elif row == 5:
            shape = shape.rotate(-25, 0, 0)
            shape = shape.translate(0, -40, 9)
        else:
            raise Exception(f"invalid col, row: (1, {row})")

        shape = shape.rotate(0, 0, 2)
        shape = shape.rotate(0, 8, 0)
        shape = shape.translate(4, -5, 24)
        return shape

    def place_key_col4(
        self, shape: ShapeOrTransform, row: int
    ) -> ShapeOrTransform:
        if row == 0:
            shape = shape.rotate(0, 0, 10)
            shape = shape.rotate(0, 0, 0)
            shape = shape.rotate(60, 0, 0)
            shape = shape.translate(-3, 61, 34)
        elif row == 1:
            shape = shape.rotate(0, 0, 6)
            shape = shape.rotate(0, 0, 0)
            shape = shape.rotate(45, 0, 0)
            shape = shape.translate(-2, 48, 15)
        elif row == 2:
            shape = shape.rotate(15, 0, 0)
            shape = shape.translate(0, 25.25, 3.5)
        elif row == 3:
            shape = shape.rotate(2, 0, 0)
            shape = shape.translate(0, 3, 1)
        elif row == 4:
            shape = shape.rotate(-10, 0, 0)
            shape = shape.translate(0, -19, 2)
        elif row == 5:
            shape = shape.rotate(0, 0, -2)
            shape = shape.rotate(-28, 0, 0)
            shape = shape.translate(0, -41, 9)
        else:
            raise Exception(f"invalid col, row: (1, {row})")

        shape = shape.rotate(0, 0, 1)
        shape = shape.rotate(0, 15, 0)
        shape = shape.translate(23.5, -5, 22)
        return shape

    def place_key_col5(
        self, shape: ShapeOrTransform, row: int
    ) -> ShapeOrTransform:
        if row == 0:
            shape = shape.rotate(0, 0, 2)
            shape = shape.rotate(0, -5, 0)
            shape = shape.rotate(60, 0, 0)
            shape = shape.translate(0, 60, 35)
        elif row == 1:
            shape = shape.rotate(0, 0, 2)
            shape = shape.rotate(0, 3, 0)
            shape = shape.rotate(45, 0, 0)
            shape = shape.translate(-1, 48, 17)
        elif row == 2:
            shape = shape.rotate(20, 0, 0)
            shape = shape.translate(0, 28, 4.5)
        elif row == 3:
            shape = shape.rotate(3, 0, 0)
            shape = shape.translate(0, 6, 0.5)
        elif row == 4:
            shape = shape.rotate(-10, 0, 0)
            shape = shape.translate(0, -17, 2)
        elif row == 5:
            # shape = shape.rotate(0, 0, 0)
            shape = shape.rotate(-28, 0, 0)
            shape = shape.translate(1, -39, 10)
        else:
            raise Exception(f"invalid col, row: (1, {row})")

        # shape = shape.rotate(0, 0, 0)
        shape = shape.rotate(0, 5, 0)
        shape = shape.translate(47, -5, 19)
        return shape

    def place_key_col_extra(
        self, shape: ShapeOrTransform, row: int
    ) -> ShapeOrTransform:
        if row == 0:
            raise Exception("invalid col, row: (-1, {row})")
        elif row == 1:
            raise Exception("invalid col, row: (-1, {row})")
        elif row == 2:
            shape = shape.rotate(12, 0, 0)
            shape = shape.translate(0, 18, 9)
        elif row == 3:
            shape = shape.rotate(10, 0, 0)
            shape = shape.translate(0, -1.25, 5)
        elif row == 4:
            shape = shape.rotate(0, 0, 0)
            shape = shape.translate(0, -22.15, 4)
        else:
            raise Exception("invalid col, row: (-1, {row})")

        shape = shape.rotate(0, 0, 6)
        shape = shape.rotate(0, 38, 0)
        shape = shape.translate(-78.5, -3, 58)
        return shape

    def connectors(self) -> List[Shape]:
        return (
            self.horiz_connectors()
            + self.vert_connectors()
            + self.corner_connectors()
        )

    def horiz_connectors(self) -> List[Shape]:
        result: List[Shape] = []
        for column in range(self.num_columns - 1):
            for row in range(self.num_rows):
                if column == 0 and row == self.num_rows - 1:
                    # Nothing to connect here: this is open for the thumb
                    continue
                result += self.connect_horiz((column, row), (column + 1, row))

        # Extra key column
        result += tri_strip(
            self.place_key(corner_bl(), 0, 1),
            self.place_key(corner_tr(), -1, 2),
            self.place_key(corner_tl(), 0, 2),
            self.place_key(corner_br(), -1, 2),
            self.place_key(corner_bl(), 0, 2),
            self.place_key(corner_tr(), -1, 3),
            self.place_key(corner_tl(), 0, 3),
            self.place_key(corner_br(), -1, 3),
            self.place_key(corner_bl(), 0, 3),
            self.place_key(corner_tr(), -1, 4),
            self.place_key(corner_tl(), 0, 4),
            self.place_key(corner_br(), -1, 4),
            self.place_key(corner_bl(), 0, 4),
        )

        return result

    def vert_connectors(self) -> List[Shape]:
        result: List[Shape] = []
        for column in range(self.num_columns):
            for row in range(self.num_rows - 1):
                if column == 0 and row == self.num_rows - 2:
                    # Nothing to connect here: this is open for the thumb
                    continue
                result += self.connect_vert((column, row), (column, row + 1))

        # Extra key column
        result += self.connect_vert((-1, 2), (-1, 3))
        result += self.connect_vert((-1, 3), (-1, 4))

        return result

    def corner_connectors(self) -> List[Shape]:
        result: List[Shape] = []
        for column in range(self.num_columns - 1):
            for row in range(self.num_rows - 1):
                if column == 0 and row == self.num_rows - 2:
                    # Nothing to connect here: this is open for the thumb
                    continue
                result += self.connect_corner(
                    (column, row),
                    (column, row + 1),
                    (column + 1, row),
                    (column + 1, row + 1),
                )

        # Connect the thumb area
        result += tri_strip(
            self.place_key(corner_bl(), 0, self.num_rows - 2),
            self.place_key(corner_bl(), 1, self.num_rows - 1),
            self.place_key(corner_br(), 0, self.num_rows - 2),
            self.place_key(corner_tl(), 1, self.num_rows - 1),
            self.place_key(corner_bl(), 1, self.num_rows - 2),
        )

        return result

    def connect_horiz(
        self, left: Tuple[int, int], right: Tuple[int, int]
    ) -> List[Shape]:
        return tri_strip(
            self.place_key(corner_tl(), right[0], right[1]),
            self.place_key(corner_tr(), left[0], left[1]),
            self.place_key(corner_bl(), right[0], right[1]),
            self.place_key(corner_br(), left[0], left[1]),
        )

    def connect_vert(
        self, top: Tuple[int, int], bottom: Tuple[int, int]
    ) -> List[Shape]:
        return tri_strip(
            self.place_key(corner_bl(), top[0], top[1]),
            self.place_key(corner_br(), top[0], top[1]),
            self.place_key(corner_tl(), bottom[0], bottom[1]),
            self.place_key(corner_tr(), bottom[0], bottom[1]),
        )

    def connect_corner(
        self,
        tl: Tuple[int, int],
        bl: Tuple[int, int],
        tr: Tuple[int, int],
        br: Tuple[int, int],
    ) -> List[Shape]:
        return tri_strip(
            self.place_key(corner_br(), tl[0], tl[1]),
            self.place_key(corner_bl(), tr[0], tr[1]),
            self.place_key(corner_tr(), bl[0], bl[1]),
            self.place_key(corner_tl(), br[0], br[1]),
        )

    def thumb_pos(
        self, shape: Shape, col: int, row: int, true_pos: bool = False
    ) -> Shape:
        if true_pos:
            return self.thumb_orientation(self.thumb_pos(shape, col, row))

        offset = 19
        key = (col, row)

        # Left column
        if key == (0, 0):
            return shape.translate(-offset, offset, 0)
        if key == (0, 1):
            return shape.translate(-offset, 0, 0)
        if key == (0, 2):
            return shape.translate(-offset, -offset, 0)

        # Middle column
        if key == (1, 0):
            return shape.translate(0, offset, 0)
        if key == (1, 1):
            return shape
        if key == (1, 2):
            return shape.translate(0, -offset, 0)

        # Right column
        if key == (2, 0):
            return shape.translate(offset, offset / 2.0, 0)
        if key == (2, 1):
            return shape.translate(offset, -offset / 2.0, 0)
        if key == (2, 2):
            return shape.translate(offset, offset * -1.5, 0)

        # extra
        if key == (3, 0):
            return shape.translate(offset * 2, offset * -2.0, 0)

        raise Exception("unknown thumb position")

    def thumb_positions(self, shape: Shape) -> List[Shape]:
        shapes: List[Shape] = []

        for col in range(3):
            for row in range(3):
                shapes.append(self.thumb_pos(shape, col, row))

        shapes.append(self.thumb_pos(shape, 3, 0))
        return shapes

    def thumb_orientation(self, shape: Shape) -> Shape:
        return shape.rotate(0, 0, 40).rotate(0, 25, 0).translate(-86, -66, 41)

    def thumb_connectors(self) -> List[Shape]:
        result: List[Shape] = []

        # vertical line between columns 0 and 1
        result += tri_strip(
            self.thumb_pos(corner_tr(), 0, 0),
            self.thumb_pos(corner_tl(), 1, 0),
            self.thumb_pos(corner_br(), 0, 0),
            self.thumb_pos(corner_bl(), 1, 0),
            self.thumb_pos(corner_tr(), 0, 1),
            self.thumb_pos(corner_tl(), 1, 1),
            self.thumb_pos(corner_br(), 0, 1),
            self.thumb_pos(corner_bl(), 1, 1),
            self.thumb_pos(corner_tr(), 0, 2),
            self.thumb_pos(corner_tl(), 1, 2),
            self.thumb_pos(corner_br(), 0, 2),
            self.thumb_pos(corner_bl(), 1, 2),
        )

        # vertical line between columns 1 and 2
        result += tri_strip(
            self.thumb_pos(corner_tr(), 1, 0),
            self.thumb_pos(corner_tl(), 2, 0),
            self.thumb_pos(corner_br(), 1, 0),
            self.thumb_pos(corner_bl(), 2, 0),
            self.thumb_pos(corner_tr(), 1, 1),
            self.thumb_pos(corner_tl(), 2, 1),
            self.thumb_pos(corner_br(), 1, 1),
            self.thumb_pos(corner_bl(), 2, 1),
            self.thumb_pos(corner_tr(), 1, 2),
            self.thumb_pos(corner_tl(), 2, 2),
            self.thumb_pos(corner_br(), 1, 2),
            self.thumb_pos(corner_bl(), 2, 2),
        )

        # vertical line between columns 2 and extra
        result += tri_strip(
            self.thumb_pos(corner_tr(), 2, 2),
            self.thumb_pos(corner_tl(), 3, 0),
            self.thumb_pos(corner_br(), 2, 2),
            self.thumb_pos(corner_bl(), 3, 0),
        )

        # horizontal connectors between rows 0 and 1
        result += tri_strip(
            self.thumb_pos(corner_bl(), 0, 0),
            self.thumb_pos(corner_tl(), 0, 1),
            self.thumb_pos(corner_br(), 0, 0),
            self.thumb_pos(corner_tr(), 0, 1),
        )
        result += tri_strip(
            self.thumb_pos(corner_bl(), 1, 0),
            self.thumb_pos(corner_tl(), 1, 1),
            self.thumb_pos(corner_br(), 1, 0),
            self.thumb_pos(corner_tr(), 1, 1),
        )
        result += tri_strip(
            self.thumb_pos(corner_bl(), 2, 0),
            self.thumb_pos(corner_tl(), 2, 1),
            self.thumb_pos(corner_br(), 2, 0),
            self.thumb_pos(corner_tr(), 2, 1),
        )

        # horizontal connectors between rows 1 and 2
        result += tri_strip(
            self.thumb_pos(corner_bl(), 0, 1),
            self.thumb_pos(corner_tl(), 0, 2),
            self.thumb_pos(corner_br(), 0, 1),
            self.thumb_pos(corner_tr(), 0, 2),
        )
        result += tri_strip(
            self.thumb_pos(corner_bl(), 1, 1),
            self.thumb_pos(corner_tl(), 1, 2),
            self.thumb_pos(corner_br(), 1, 1),
            self.thumb_pos(corner_tr(), 1, 2),
        )
        result += tri_strip(
            self.thumb_pos(corner_bl(), 2, 1),
            self.thumb_pos(corner_tl(), 2, 2),
            self.thumb_pos(corner_br(), 2, 1),
            self.thumb_pos(corner_tr(), 2, 2),
        )

        # extra perimeter around thumb area
        result += tri_strip(
            self.thumb_pos(corner_tl(), 3, 0),
            self.thumb_pos(corner_tr(), 2, 2),
            self.thumb_pos(corner_tr(), 3, 0),
            self.thumb_pos(corner_br(), 2, 1),
        )
        result += tri_strip(
            self.thumb_pos(corner_bl(), 3, 0),
            self.thumb_pos(corner_br(), 2, 2),
            self.thumb_pos(corner_bl(), 2, 2),
        )
        result += tri_strip(
            self.thumb_pos(corner_br(), 1, 2),
            self.thumb_pos(corner_bl(), 2, 2),
            self.thumb_pos(corner_bl(), 1, 2),
            self.thumb_pos(corner_br(), 0, 2),
        )
        result += tri_strip(
            self.thumb_pos(corner_br(), 0, 2),
            self.thumb_pos(corner_bl(), 2, 2),
            self.thumb_pos(corner_bl(), 0, 2),
        )
        result += tri_strip(
            self.thumb_pos(corner_tr(), 2, 0),
            self.thumb_pos(corner_tl(), 2, 0),
            self.thumb_pos(corner_tr(), 1, 0),
        )

        return result

    def thumb_area(self) -> List[Shape]:
        shapes: List[Shape] = []
        shapes += self.thumb_positions(self.key_hole)
        shapes += self.thumb_connectors()
        return [self.thumb_orientation(Shape.union(shapes))]

    def thumb_connect_wall(self) -> List[Shape]:
        result: List[Shape] = []

        # Some extra horizontal perimeter on the upper and right
        # boundary of the thumb area
        result += tri_strip(
            self.thumb_pos(corner_tr(), 1, 0, true_pos=True),
            self.thumb_pos(corner_tr(x=0, y=3), 1, 0, true_pos=True),
            self.thumb_pos(corner_tr(), 2, 0, true_pos=True),
            self.thumb_pos(corner_tr(x=3, y=3), 2, 0, true_pos=True),
            self.thumb_pos(corner_br(), 2, 0, true_pos=True),
            self.thumb_pos(corner_br(x=3), 2, 0, true_pos=True),
            self.thumb_pos(corner_tr(), 2, 1, true_pos=True),
            self.thumb_pos(corner_tr(x=3), 2, 1, true_pos=True),
            self.thumb_pos(corner_br(), 2, 1, true_pos=True),
            self.thumb_pos(corner_br(x=3, y=2), 2, 1, true_pos=True),
            self.thumb_pos(corner_tr(), 3, 0, true_pos=True),
            self.thumb_pos(corner_tr(x=3, y=2), 3, 0, true_pos=True),
            self.thumb_pos(corner_br(), 3, 0, true_pos=True),
        )

        # Connecting wall between the thumb and main keys
        result += [
            Shape.hull(
                [
                    self.place_key(corner_bl().translate(0, 0, -2), 1, 5),
                    self.place_key(
                        corner_bl(x=-1, y=-1).translate(0, 0, -2), 1, 5
                    ),
                    self.place_key(corner_bl().translate(0, 0, -6), 1, 5),
                    self.place_key(
                        corner_bl(x=-1, y=-1).translate(0, 0, -6), 1, 5
                    ),
                    self.place_key(corner_br().translate(0, 0, -2), 1, 5),
                    self.place_key(corner_br(y=-1).translate(0, 0, -2), 1, 5),
                    self.place_key(corner_br().translate(0, 0, -6), 1, 5),
                    self.place_key(corner_br(y=-1).translate(0, 0, -6), 1, 5),
                ]
            ),
            Shape.hull(
                [
                    self.thumb_pos(corner_tr(x=3, y=2), 3, 0, true_pos=True),
                    self.thumb_pos(corner_tr(x=5, y=4), 3, 0, true_pos=True),
                    self.thumb_pos(corner_br(x=3, y=2), 2, 1, true_pos=True),
                    self.thumb_pos(corner_br(x=5, y=4), 2, 1, true_pos=True),
                    self.thumb_pos(
                        corner_tr(x=3, y=2).translate(0, 0, 8),
                        3,
                        0,
                        true_pos=True,
                    ),
                    self.thumb_pos(
                        corner_tr(x=5, y=4).translate(0, 0, 8),
                        3,
                        0,
                        true_pos=True,
                    ),
                    self.thumb_pos(
                        corner_br(x=3, y=2).translate(0, 0, 8),
                        2,
                        1,
                        true_pos=True,
                    ),
                    self.thumb_pos(
                        corner_br(x=5, y=4).translate(0, 0, 8),
                        2,
                        1,
                        true_pos=True,
                    ),
                ]
            ),
            Shape.hull(
                [
                    self.thumb_pos(
                        corner_tr(x=3, y=2).translate(0, 0, 8),
                        3,
                        0,
                        true_pos=True,
                    ),
                    self.thumb_pos(
                        corner_tr(x=5, y=4).translate(0, 0, 8),
                        3,
                        0,
                        true_pos=True,
                    ),
                    self.thumb_pos(
                        corner_br(x=3, y=2).translate(0, 0, 8),
                        2,
                        1,
                        true_pos=True,
                    ),
                    self.thumb_pos(
                        corner_br(x=5, y=4).translate(0, 0, 8),
                        2,
                        1,
                        true_pos=True,
                    ),
                    self.place_key(corner_br().translate(0, 0, -6), 1, 5),
                    self.place_key(corner_br(y=-1).translate(0, 0, -6), 1, 5),
                ]
            ),
            Shape.hull(
                [
                    self.thumb_pos(
                        corner_br(x=3, y=2).translate(0, 0, 8),
                        2,
                        1,
                        true_pos=True,
                    ),
                    self.thumb_pos(
                        corner_br(x=5, y=4).translate(0, 0, 8),
                        2,
                        1,
                        true_pos=True,
                    ),
                    self.place_key(corner_br().translate(0, 0, -6), 1, 5),
                    self.place_key(corner_br(y=-1).translate(0, 0, -6), 1, 5),
                    self.place_key(corner_bl().translate(0, 0, -6), 1, 5),
                    self.place_key(
                        corner_bl(x=-1, y=-1).translate(0, 0, -6), 1, 5
                    ),
                ]
            ),
            Shape.hull(
                [
                    self.place_key(corner_bl().translate(0, 0, -2), 1, 5),
                    self.place_key(
                        corner_bl(x=-1, y=-1).translate(0, 0, -2), 1, 5
                    ),
                    self.place_key(corner_bl().translate(0, 0, -6), 1, 5),
                    self.place_key(
                        corner_bl(x=-1, y=-1).translate(0, 0, -6), 1, 5
                    ),
                    self.place_key(corner_bl().translate(0, 0, -2), 0, 4),
                    self.place_key(
                        corner_bl(x=-1, y=-1).translate(0, 0, -2), 0, 4
                    ),
                ]
            ),
            Shape.hull(
                [
                    self.place_key(corner_bl().translate(0, 0, -6), 1, 5),
                    self.place_key(
                        corner_bl(x=-1, y=-1).translate(0, 0, -6), 1, 5
                    ),
                    self.place_key(corner_bl().translate(0, 0, -2), 0, 4),
                    self.place_key(
                        corner_bl(x=-1, y=-1).translate(0, 0, -2), 0, 4
                    ),
                    self.thumb_pos(
                        corner_br(x=3, y=2).translate(0, 0, 8),
                        2,
                        1,
                        true_pos=True,
                    ),
                    self.thumb_pos(
                        corner_br(x=5, y=4).translate(0, 0, 8),
                        2,
                        1,
                        true_pos=True,
                    ),
                ]
            ),
            Shape.hull(
                [
                    self.place_key(corner_bl().translate(0, 0, -2), 0, 4),
                    self.place_key(
                        corner_bl(x=-1, y=-1).translate(0, 0, -2), 0, 4
                    ),
                    self.thumb_pos(
                        corner_br(x=3, y=2).translate(0, 0, 8),
                        2,
                        1,
                        true_pos=True,
                    ),
                    self.thumb_pos(
                        corner_br(x=5, y=4).translate(0, 0, 8),
                        2,
                        1,
                        true_pos=True,
                    ),
                    self.thumb_pos(corner_tr(x=3, y=3), 2, 0, true_pos=True),
                    self.thumb_pos(corner_tr(x=5, y=5), 2, 0, true_pos=True),
                ]
            ),
            Shape.hull(
                [
                    self.thumb_pos(
                        corner_br(x=3, y=2).translate(0, 0, 8),
                        2,
                        1,
                        true_pos=True,
                    ),
                    self.thumb_pos(
                        corner_br(x=5, y=4).translate(0, 0, 8),
                        2,
                        1,
                        true_pos=True,
                    ),
                    self.thumb_pos(corner_br(x=3, y=2), 2, 1, true_pos=True),
                    self.thumb_pos(corner_br(x=5, y=4), 2, 1, true_pos=True),
                    self.thumb_pos(corner_tr(x=3, y=3), 2, 0, true_pos=True),
                    self.thumb_pos(corner_tr(x=5, y=5), 2, 0, true_pos=True),
                ]
            ),
            Shape.hull(
                [
                    self.thumb_pos(corner_tr(x=3, y=3), 2, 0, true_pos=True),
                    self.thumb_pos(corner_tr(x=5, y=5), 2, 0, true_pos=True),
                    self.place_key(corner_bl().translate(0, 0, -2), 0, 4),
                    self.place_key(
                        corner_bl(x=-1, y=-1).translate(0, 0, -2), 0, 4
                    ),
                    self.place_key(corner_br().translate(0, 0, -2), -1, 4),
                    self.place_key(
                        corner_br(x=-1, y=-1).translate(0, 0, -2), -1, 4
                    ),
                ]
            ),
            Shape.hull(
                [
                    self.thumb_pos(corner_tr(x=3, y=3), 2, 0, true_pos=True),
                    self.thumb_pos(corner_tr(x=5, y=5), 2, 0, true_pos=True),
                    self.place_key(corner_br().translate(0, 0, -2), -1, 4),
                    self.place_key(
                        corner_br(x=-1, y=-1).translate(0, 0, -2), -1, 4
                    ),
                    self.place_key(corner_bl().translate(0, 0, -2), -1, 4),
                    self.place_key(
                        corner_bl(x=0, y=-1).translate(0, 0, -2), -1, 4
                    ),
                ]
            ),
        ]

        # Bevel from the wall to the main keys
        result += [
            Shape.hull(
                [
                    self.place_key(corner_br(), 1, 5),
                    self.place_key(corner_br(y=-1).translate(0, 0, -2), 1, 5),
                    self.place_key(corner_bl(), 1, 5),
                    self.place_key(
                        corner_bl(x=-1, y=-1).translate(0, 0, -2), 1, 5
                    ),
                ]
            ),
            Shape.hull(
                [
                    self.place_key(corner_bl(), 1, 5),
                    self.place_key(
                        corner_bl(x=-1, y=-1).translate(0, 0, -2), 1, 5
                    ),
                    self.place_key(corner_bl(), 0, 4),
                    self.place_key(
                        corner_bl(x=-1, y=-1).translate(0, 0, -2), 0, 4
                    ),
                ]
            ),
            Shape.hull(
                [
                    self.place_key(corner_bl(), 0, 4),
                    self.place_key(
                        corner_bl(x=-1, y=-1).translate(0, 0, -2), 0, 4
                    ),
                    self.place_key(corner_br(), -1, 4),
                    self.place_key(
                        corner_br(x=-1, y=-1).translate(0, 0, -2), -1, 4
                    ),
                ]
            ),
            Shape.hull(
                [
                    self.place_key(corner_br(), -1, 4),
                    self.place_key(
                        corner_br(x=-1, y=-1).translate(0, 0, -2), -1, 4
                    ),
                    self.place_key(corner_bl(), -1, 4),
                    self.place_key(
                        corner_bl(x=0, y=-1).translate(0, 0, -2), -1, 4
                    ),
                ]
            ),
        ]

        return result

    def thumb_caps(self) -> Shape:
        return self.thumb_orientation(
            Shape.union(self.thumb_positions(dsa_cap()))
        )

    def wrist_rest(self) -> List[Shape]:
        rest = (
            Shape.cube(140, 90, 3)
            .translate(50, -97, 34)
            .rotate(10, 12, 0)
            .translate(0, 0, 20)
        )
        return [rest]

    def wall_tl(self, column: int, row: int) -> Transform:
        tf = Transform().translate(-mount_width / 2, mount_height / 2, 0)
        tf2 = self.place_key(tf, column, row)
        return tf2.translate(0, 3, 0)

    def wall_tr(self, column: int, row: int) -> Transform:
        tf = Transform().translate(mount_width / 2, mount_height / 2, 0)
        tf2 = self.place_key(tf, column, row)
        return tf2.translate(0, 5, 0)

    def wall_segment(
        self,
        side1_post: Shape,
        side1_near_corner: Point,
        side1_far_corner: Point,
        side2_post: Shape,
        side2_near_corner: Point,
        side2_far_corner: Point,
    ) -> List[Shape]:
        corner = Shape.sphere(self.wall_radius, fn=30)
        ground_corner = Shape.sphere(self.wall_radius, fn=30).difference(
            [
                Shape.cube(
                    self.wall_radius * 2,
                    self.wall_radius * 2,
                    self.wall_radius * 2,
                ).translate(0, 0, -self.wall_radius)
            ]
        )

        ground1 = Point(side1_far_corner.x, side1_far_corner.y, 0)
        ground2 = Point(side2_far_corner.x, side2_far_corner.y, 0)
        return [
            Shape.hull(
                [
                    side1_post,
                    side2_post,
                    corner.ptranslate(side1_near_corner),
                    corner.ptranslate(side2_near_corner),
                ]
            ),
            Shape.hull(
                [
                    corner.ptranslate(side1_near_corner),
                    corner.ptranslate(side2_near_corner),
                    corner.ptranslate(side1_far_corner),
                    corner.ptranslate(side2_far_corner),
                ]
            ),
            Shape.hull(
                [
                    corner.ptranslate(side1_far_corner),
                    corner.ptranslate(side2_far_corner),
                    ground_corner.ptranslate(ground1),
                    ground_corner.ptranslate(ground2),
                ]
            ),
        ]

    def wall_post(
        self,
        column: int,
        row: int,
        key_post: Shape,
        corner_transform: Transform,
        far_offset: Point,
    ) -> WallPost:
        near = self.place_key(corner_transform, column, row).point()
        far = near.ptranslate(far_offset)
        post = self.place_key(key_post, column, row)
        return WallPost(post, near, far)

    def wall_left(self) -> Tuple[List[WallPost], float]:
        # Top left key hole corner
        left_tl = Transform().translate(
            -mount_width / 2 - self.wall_radius,
            mount_height / 2,
            plate_thickness - self.wall_radius,
        )
        # Bottom right key hole corner
        left_bl = Transform().translate(
            -mount_width / 2 - self.wall_radius,
            -mount_height / 2,
            plate_thickness - self.wall_radius,
        )

        left_wall_offset = Point(-3.0, 0.0, 0.0)
        lower_posts: List[WallPost] = [
            self.wall_post(-1, 4, corner_tl(), left_tl, left_wall_offset),
            self.wall_post(-1, 3, corner_bl(), left_bl, left_wall_offset),
            self.wall_post(-1, 3, corner_tl(), left_tl, left_wall_offset),
            self.wall_post(-1, 2, corner_bl(), left_bl, left_wall_offset),
            self.wall_post(-1, 2, corner_tl(), left_tl, Point(-3.0, 3.0, 0.0)),
        ]

        lower_x = min(post.far.x for post in lower_posts)
        for post in lower_posts:
            post.far.x = lower_x

        top_tl = Transform().translate(
            -mount_width / 2,
            mount_height / 2 + self.wall_radius,
            plate_thickness - self.wall_radius,
        )
        top_tr = Transform().translate(
            mount_width / 2,
            mount_height / 2 + self.wall_radius,
            plate_thickness - self.wall_radius,
        )
        horiz_posts = [
            self.wall_post(-1, 2, corner_tl(), top_tl, Point(0.0, 3.0, 0.0)),
            self.wall_post(-1, 2, corner_tr(), top_tr, Point(0.0, 3.0, 0.0)),
        ]

        upper_posts: List[WallPost] = [
            self.wall_post(0, 1, corner_bl(), left_bl, Point(-3.0, 0.0, 0.0)),
            self.wall_post(0, 1, corner_tl(), left_tl, Point(-3.0, 0.0, 0.0)),
            self.wall_post(0, 0, corner_bl(), left_bl, Point(-3.0, 0.0, 0.0)),
            self.wall_post(0, 0, corner_tl(), left_tl, Point(-3.0, 0.0, 0.0)),
        ]
        # upper_x = min(post.far.x for post in upper_posts)
        # for post in upper_posts:
        #    post.far.x = upper_x

        return (lower_posts + horiz_posts + upper_posts), lower_x

    def wall_back(self) -> List[WallPost]:
        # Top left key hole corner
        top_tl = Transform().translate(
            -mount_width / 2,
            mount_height / 2 + self.wall_radius,
            plate_thickness - self.wall_radius,
        )
        # Top right key hole corner
        top_tr = Transform().translate(
            mount_width / 2,
            mount_height / 2 + self.wall_radius,
            plate_thickness - self.wall_radius,
        )

        back_wall_offset = Point(0.0, 3.0, -3.0)
        posts: List[WallPost] = []
        num_cols = 6
        first_row = 0
        for column in range(num_cols):
            posts.append(
                self.wall_post(
                    column, first_row, corner_tl(), top_tl, back_wall_offset
                )
            )
            posts.append(
                self.wall_post(
                    column, first_row, corner_tr(), top_tr, back_wall_offset
                )
            )

        max_y = max(post.far.y for post in posts)
        for post in posts:
            post.far.y = max_y

        return posts

    def wall_right(self) -> List[WallPost]:
        # Top right key hole corner
        right_tr = Transform().translate(
            mount_width / 2 + self.wall_radius,
            mount_height / 2,
            plate_thickness - self.wall_radius,
        )
        # Bottom right key hole corner
        right_br = Transform().translate(
            mount_width / 2 + self.wall_radius,
            -mount_height / 2,
            plate_thickness - self.wall_radius,
        )

        posts: List[WallPost] = []
        num_rows = 6
        last_column = 5
        right_wall_offset = Point(0.0, 0.0, 0.0)
        for row in range(num_rows):
            posts.append(
                self.wall_post(
                    last_column, row, corner_tr(), right_tr, right_wall_offset
                )
            )
            posts.append(
                self.wall_post(
                    last_column, row, corner_br(), right_br, right_wall_offset
                )
            )

        max_x = max(post.far.x for post in posts)
        for post in posts:
            post.far.x = max_x

        return posts

    def wall_front(self) -> Tuple[List[WallPost], float]:
        # Bottom left key hole corner
        front_bl = Transform().translate(
            -mount_width / 2,
            -mount_height / 2 - self.wall_radius,
            plate_thickness - self.wall_radius,
        )
        # Bottom right key hole corner
        front_br = Transform().translate(
            mount_width / 2,
            -mount_height / 2 - self.wall_radius,
            plate_thickness - self.wall_radius,
        )

        last_row = 5
        front_wall_offset = Point(0.0, -1.0, 0.0)
        posts: List[WallPost] = []
        for column in (5, 4, 3):
            posts.append(
                self.wall_post(
                    column, last_row, corner_br(), front_br, front_wall_offset
                )
            )
            posts.append(
                self.wall_post(
                    column, last_row, corner_bl(), front_bl, front_wall_offset
                )
            )

        # On column 2, we move the bottom left end inwards a little bit, so
        # it does not stick out past the key hole
        posts.append(
            self.wall_post(
                2, last_row, corner_br(), front_br, front_wall_offset
            )
        )
        front_bl2 = Transform().translate(
            -mount_width / 2 + self.wall_radius,
            -mount_height / 2 - self.wall_radius,
            plate_thickness - self.wall_radius,
        )
        posts.append(
            self.wall_post(
                2, last_row, corner_bl(), front_bl2, front_wall_offset
            )
        )

        min_y = min(post.far.y for post in posts)
        for post in posts:
            post.far.y = min_y

        return posts, min_y

    def wall_thumb(self) -> List[Shape]:
        result: List[Shape] = []

        # Left side wall
        posts: List[Shape] = []
        top_points: List[Point] = []
        ground_points: List[Point] = []

        # top-right corner of thumb (1, 0) position
        top_right = Transform().translate(
            mount_width / 2 + self.wall_radius,
            mount_height / 2 + self.wall_radius + 2.0,
            plate_thickness - self.wall_radius,
        )
        posts.append(self.thumb_pos(corner_tr(), 1, 0, true_pos=True))
        tr_corner = self.thumb_pos(top_right, 1, 0, true_pos=True).point()
        top_points.append(tr_corner)
        ground_points.append(Point(tr_corner.x, tr_corner.y, 0))

        # top-left corner of thumb (0, 0) position
        top_left = Transform().translate(
            -mount_width / 2 - self.wall_radius,
            mount_height / 2 + self.wall_radius,
            plate_thickness - self.wall_radius,
        )
        posts.append(self.thumb_pos(corner_tl(), 0, 0, true_pos=True))
        tl_corner = self.thumb_pos(top_left, 0, 0, true_pos=True).point()
        top_points.append(tl_corner)
        ground_points.append(Point(tl_corner.x, tl_corner.y, 0))

        # bottom-left corner of thumb (0, 2) position
        bottom_left = Transform().translate(
            -mount_width / 2 - self.wall_radius,
            -mount_height / 2 - self.wall_radius,
            plate_thickness - self.wall_radius,
        )
        posts.append(self.thumb_pos(corner_bl(), 0, 2, true_pos=True))
        bl_corner = self.thumb_pos(bottom_left, 0, 2, true_pos=True).point()
        top_points.append(bl_corner)
        ground_points.append(Point(bl_corner.x, bl_corner.y, 0))

        # bottom-left corner of thumb (2, 2) position
        posts.append(self.thumb_pos(corner_bl(), 2, 2, true_pos=True))
        bl_corner = self.thumb_pos(bottom_left, 2, 2, true_pos=True).point()
        top_points.append(bl_corner)
        ground_points.append(Point(bl_corner.x, bl_corner.y, 0))

        # bottom-left corner of thumb (3, 0) position
        posts.append(self.thumb_pos(corner_bl(), 3, 0, true_pos=True))
        bl_corner = self.thumb_pos(bottom_left, 3, 0, true_pos=True).point()
        top_points.append(bl_corner)
        ground_points.append(Point(bl_corner.x, bl_corner.y, 0))

        # bottom-right corner of thumb (3, 0) position
        bottom_right = Transform().translate(
            mount_width / 2 + self.wall_radius,
            -mount_height / 2 - self.wall_radius,
            plate_thickness - self.wall_radius,
        )
        posts.append(self.thumb_pos(corner_br(), 3, 0, true_pos=True))
        br_corner = self.thumb_pos(bottom_right, 3, 0, true_pos=True).point()
        top_points.append(br_corner)
        ground_points.append(Point(br_corner.x, br_corner.y, 0))

        corner = Shape.sphere(self.wall_radius, fn=30)
        ground_corner = Shape.sphere(self.wall_radius, fn=30).difference(
            [
                Shape.cube(
                    self.wall_radius * 2,
                    self.wall_radius * 2,
                    self.wall_radius * 2,
                ).translate(0, 0, -self.wall_radius)
            ]
        )
        for idx in range(1, len(posts)):
            result.append(
                Shape.hull(
                    [
                        corner.ptranslate(top_points[idx - 1]),
                        ground_corner.ptranslate(ground_points[idx - 1]),
                        corner.ptranslate(top_points[idx]),
                        ground_corner.ptranslate(ground_points[idx]),
                    ]
                )
            )
            result.append(
                Shape.hull(
                    [
                        posts[idx - 1],
                        posts[idx],
                        corner.ptranslate(top_points[idx - 1]),
                        corner.ptranslate(top_points[idx]),
                    ]
                )
            )

        # Bottom wall

        return result

    def wall_thumb_gap0(self, left_wall_x: float) -> List[Shape]:
        corner = Shape.sphere(self.wall_radius, fn=30)
        ground_corner = Shape.sphere(self.wall_radius, fn=30).difference(
            [
                Shape.cube(
                    self.wall_radius * 2,
                    self.wall_radius * 2,
                    self.wall_radius * 2,
                ).translate(0, 0, -self.wall_radius)
            ]
        )

        left_tl = Transform().translate(
            -mount_width / 2 - self.wall_radius,
            mount_height / 2,
            plate_thickness - self.wall_radius,
        )
        left_bl = Transform().translate(
            -mount_width / 2 - self.wall_radius,
            -mount_height / 2 + self.wall_radius,
            plate_thickness - self.wall_radius,
        )

        tl_post = self.place_key(corner_tl(), -1, 4)
        tl_near = self.place_key(left_tl, -1, 4).point()
        tl_far = tl_near.translate(-3.0, 0.0, 0.0)
        tl_far.x = left_wall_x
        tl_ground = Point(tl_far.x, tl_far.y, 0.0)
        ctl_near = corner.ptranslate(tl_near)
        ctl_far = corner.ptranslate(tl_far)
        ctl_ground = ground_corner.ptranslate(tl_ground)

        bl_post = self.place_key(corner_bl(), -1, 4)
        bl_near = self.place_key(left_bl, -1, 4).point()
        bl_far = bl_near.translate(-3.0, 0.0, 0.0)
        bl_ground = Point(bl_far.x, bl_far.y, 0.0)
        cbl_near = corner.ptranslate(bl_near)
        cbl_far = corner.ptranslate(bl_far)

        result: List[Shape] = []
        result.append(Shape.hull([tl_post, ctl_near, bl_post, cbl_near]))
        result.append(Shape.hull([ctl_near, ctl_far, cbl_near, cbl_far]))

        top_right = Transform().translate(
            mount_width / 2 + self.wall_radius,
            mount_height / 2 + self.wall_radius + 2.0,
            plate_thickness - self.wall_radius,
        )
        thumb_tr_corner = self.thumb_pos(
            top_right, 1, 0, true_pos=True
        ).point()
        thumb_tr_ground = Point(thumb_tr_corner.x, thumb_tr_corner.y, 0.0)

        cthumb_tr_corner = corner.ptranslate(thumb_tr_corner)
        cthumb_tr_ground = ground_corner.ptranslate(thumb_tr_ground)

        result += [
            Shape.hull([cthumb_tr_ground, ctl_ground, ctl_far]),
            Shape.hull([cthumb_tr_ground, ctl_far, cthumb_tr_corner]),
            Shape.hull([ctl_far, cthumb_tr_corner, cbl_far]),
            Shape.hull(
                [
                    self.thumb_pos(corner_tr(x=3, y=3), 2, 0, true_pos=True),
                    cthumb_tr_corner,
                    self.place_key(
                        corner_bl(x=0, y=-1).translate(0, 0, -2), -1, 4
                    ),
                ]
            ),
            Shape.hull(
                [
                    cthumb_tr_corner,
                    self.place_key(
                        corner_bl(x=0, y=-1).translate(0, 0, -2), -1, 4
                    ),
                    cbl_far,
                ]
            ),
            Shape.hull(
                [
                    self.place_key(
                        corner_bl(x=0, y=-1).translate(0, 0, -2), -1, 4
                    ),
                    cbl_far,
                    cbl_near,
                ]
            ),
            Shape.hull(
                [
                    self.place_key(
                        corner_bl(x=0, y=-1).translate(0, 0, -2), -1, 4
                    ),
                    self.place_key(corner_bl(), -1, 4),
                    cbl_near,
                ]
            ),
        ]

        return result

    def wall_thumb_gap1(self, front_wall_post: WallPost) -> List[Shape]:
        corner = Shape.sphere(self.wall_radius, fn=30)
        ground_corner = Shape.sphere(self.wall_radius, fn=30).difference(
            [
                Shape.cube(
                    self.wall_radius * 2,
                    self.wall_radius * 2,
                    self.wall_radius * 2,
                ).translate(0, 0, -self.wall_radius)
            ]
        )

        # bottom-right corner of thumb (3, 0) position
        bottom_right = Transform().translate(
            mount_width / 2 + self.wall_radius,
            -mount_height / 2 - self.wall_radius,
            plate_thickness - self.wall_radius,
        )
        # posts.append(self.thumb_pos(corner_br(), 3, 0, true_pos=True))
        br_corner = self.thumb_pos(bottom_right, 3, 0, true_pos=True).point()
        cbr_corner = corner.ptranslate(br_corner)
        br_ground = Point(br_corner.x, br_corner.y, 0)
        cbr_ground = ground_corner.ptranslate(br_ground)

        n_bl = front_wall_post.near.copy()
        f_bl = front_wall_post.far.copy()
        f_ground = f_bl.copy()
        f_ground.z = 0
        f_mid = f_ground.copy()
        f_mid.z = br_corner.z
        cf_ground = ground_corner.ptranslate(f_ground)
        cf_mid = corner.ptranslate(f_mid)
        cf_bl = corner.ptranslate(f_bl)
        cn_bl = corner.ptranslate(n_bl)

        bl_ground = br_ground.copy()
        bl_ground.y = f_ground.y
        cbl_ground = ground_corner.ptranslate(bl_ground)

        bl_mid = bl_ground.copy()
        bl_mid.z = br_corner.z
        cbl_mid = ground_corner.ptranslate(bl_mid)

        br_post = self.thumb_pos(corner_br(), 3, 0, true_pos=True)
        tr_post = self.thumb_pos(corner_tr(), 3, 0, true_pos=True)
        tr_far_post = self.thumb_pos(corner_tr(x=3, y=2), 3, 0, true_pos=True)

        result: List[Shape] = [
            Shape.hull([cbr_corner, cbr_ground, cbl_ground, cbl_mid]),
            Shape.hull([cf_ground, cf_mid, cbl_ground, cbl_mid]),
            Shape.hull([cbr_corner, cbl_mid, br_post]),
            Shape.hull([cbl_mid, br_post, tr_far_post]),
            Shape.hull(
                [
                    self.place_key(corner_br(), 1, 5),
                    self.place_key(corner_bl(), 2, 5),
                    cn_bl,
                ]
            ),
            Shape.hull(
                [
                    self.place_key(corner_br(), 1, 5),
                    self.place_key(corner_br(y=-1).translate(0, 0, -2), 1, 5),
                    cn_bl,
                    cf_bl,
                ]
            ),
            Shape.hull(
                [
                    self.place_key(corner_br(y=-1).translate(0, 0, -2), 1, 5),
                    self.place_key(corner_br().translate(0, 0, -2), 1, 5),
                    cf_bl,
                ]
            ),
            Shape.hull(
                [
                    self.place_key(corner_br(y=-1).translate(0, 0, -6), 1, 5),
                    self.place_key(corner_br().translate(0, 0, -6), 1, 5),
                    self.place_key(corner_br(y=-1).translate(0, 0, -2), 1, 5),
                    self.place_key(corner_br().translate(0, 0, -2), 1, 5),
                    cf_bl,
                ]
            ),
            Shape.hull(
                [
                    self.place_key(corner_br(y=-1).translate(0, 0, -6), 1, 5),
                    self.place_key(corner_br().translate(0, 0, -6), 1, 5),
                    self.place_key(corner_br(y=-1).translate(0, 0, -2), 1, 5),
                    self.place_key(corner_br().translate(0, 0, -2), 1, 5),
                    cf_mid,
                    cf_bl,
                ]
            ),
            Shape.hull(
                [
                    self.place_key(corner_br(y=-1).translate(0, 0, -6), 1, 5),
                    self.place_key(corner_br().translate(0, 0, -6), 1, 5),
                    self.place_key(corner_br(y=-1).translate(0, 0, -2), 1, 5),
                    self.place_key(corner_br().translate(0, 0, -2), 1, 5),
                    cf_mid,
                    cbl_mid,
                ]
            ),
            Shape.hull(
                [
                    self.thumb_pos(corner_tr(x=3, y=2), 3, 0, true_pos=True),
                    self.thumb_pos(corner_tr(x=5, y=4), 3, 0, true_pos=True),
                    self.thumb_pos(
                        corner_tr(x=3, y=2).translate(0, 0, 8),
                        3,
                        0,
                        true_pos=True,
                    ),
                    self.thumb_pos(
                        corner_tr(x=5, y=4).translate(0, 0, 8),
                        3,
                        0,
                        true_pos=True,
                    ),
                    cbl_mid,
                ]
            ),
            Shape.hull(
                [
                    self.thumb_pos(
                        corner_tr(x=3, y=2).translate(0, 0, 8),
                        3,
                        0,
                        true_pos=True,
                    ),
                    self.thumb_pos(
                        corner_tr(x=5, y=4).translate(0, 0, 8),
                        3,
                        0,
                        true_pos=True,
                    ),
                    self.place_key(corner_br().translate(0, 0, -6), 1, 5),
                    self.place_key(corner_br(y=-1).translate(0, 0, -6), 1, 5),
                    cbl_mid,
                ]
            ),
        ]
        return result

    def walls(self) -> List[Shape]:
        left_wall_posts, left_wall_x = self.wall_left()
        front_wall_posts, front_wall_y = self.wall_front()
        posts = (
            left_wall_posts
            + self.wall_back()
            + self.wall_right()
            + front_wall_posts
        )

        result: List[Shape] = []
        for idx in range(1, len(posts)):
            result += self.wall_segment(
                posts[idx - 1].post,
                posts[idx - 1].near,
                posts[idx - 1].far,
                posts[idx].post,
                posts[idx].near,
                posts[idx].far,
            )

        return (
            result
            + self.wall_thumb()
            + self.wall_thumb_gap0(left_wall_x)
            + self.wall_thumb_gap1(front_wall_posts[-1])
        )


def model_right(
    *,
    show_caps: bool = False,
    show_collisions: bool = False,
    loose_holes: bool = False,
) -> Shape:
    kbd = MyKeyboard()
    if loose_holes:
        kbd.key_hole = single_plate(loose=True)
    parts = (
        kbd.key_holes()
        + kbd.connectors()
        + kbd.thumb_area()
        + kbd.thumb_connect_wall()
        # + kbd.wrist_rest()
        + kbd.walls()
    )
    if show_caps:
        parts.append(kbd.key_caps().grey())
        parts.append(kbd.thumb_caps().grey())
    if show_collisions:
        parts.append(kbd.key_collisions().highlight())

    # OLED display mock-up
    if False:
        parts.append(
            Shape.cube(46.3, 11.5, 1.45)
            .highlight()
            .rotate(90, 0, -53)
            .translate(-110, -85, 20)
        )
    return Shape.union(parts)


def model_left(
    *,
    show_caps: bool = False,
    show_collisions: bool = False,
    loose_holes: bool = False,
) -> Shape:
    right = model_right(
        show_caps=show_caps,
        show_collisions=show_collisions,
        loose_holes=loose_holes,
    )
    left = right.mirror(1, 0, 0)
    return left


def oled_display() -> Shape:
    pcb_w = 33
    pcb_h = 21.65
    pcb_thickness = 1.57

    display_w = 30
    display_h = 11.5
    display_thickness = 1.63

    display_z = pcb_thickness + (display_thickness / 2)

    base = Shape.cube(pcb_w, pcb_h, pcb_thickness).translate(
        pcb_w / 2, pcb_h / 2, pcb_thickness / 2
    )
    display = Shape.cube(display_w, display_h, display_thickness).translate(
        (pcb_w / 2) - 1, pcb_h / 2, display_z
    )
    cable_w = 4.35
    cable_thickness = pcb_thickness + display_thickness
    cable = Shape.cube(cable_w, 8.5, cable_thickness).translate(
        pcb_w - (cable_w / 2) + 1.75, pcb_h / 2, cable_thickness / 2
    )

    stemma_w = 4.3
    stemma_h = 6.1
    stemma_z = 3.0
    stemma_conn = Shape.cube(stemma_w, stemma_h, stemma_z).translate(
        stemma_w / 2, pcb_h / 2, -stemma_z / 2.0
    )

    standoff = Shape.cylinder(h=2, r=2.5 / 2, fn=30).translate(0, 0, 0.98)
    main = Shape.union([base, display, cable, stemma_conn])
    return Shape.difference(
        main,
        [
            standoff.translate(2.5, 2.5, 0),
            standoff.translate(30.5, 2.5, 0),
            standoff.translate(30.5, 19, 0),
            standoff.translate(2.5, 19, 0),
        ],
    )


def sx509_breakout() -> Shape:
    standoff = Shape.cylinder(h=2, r=3.302 / 2, fn=30)
    # Note, the 2 long sides are cut in inside the stand-off holes.
    # Only 22.87mm wide
    base = Shape.cube(36.2, 26, 1.57)
    return Shape.difference(
        base,
        [
            standoff.translate(15.367, 10.287, 0.0),
            standoff.translate(-15.367, 10.287, 0.0),
            standoff.translate(-15.367, -10.287, 0.0),
            standoff.translate(15.367, -10.287, 0.0),
        ],
    )


def esp32_feather() -> Shape:
    pcb_w = 51.2
    pcb_d = 22.8
    pcb_h = 1.57
    base = Shape.cube(pcb_w, pcb_d, pcb_h).translate(
        pcb_w * 0.5, pcb_d * 0.5, pcb_h * 0.5
    )
    standoff_big = Shape.cylinder(h=2, r=2.5 / 2, fn=30).translate(0, 0, 0.98)

    return Shape.difference(
        base,
        [
            standoff_big.translate(48.40, 2.5, 0.0),
            standoff_big.translate(48.40, 19.0 + 1.25, 0.0),
            # standoff.translate(-15.367, 10.287, 0.0),
            # standoff.translate(-15.367, -10.287, 0.0),
            # standoff.translate(15.367, -10.287, 0.0),
        ],
    )


def standoff_stud(d: float) -> Shape:
    tolerance = d * 0.075
    r = (d / 2) - tolerance

    pcb_thickness = 1.57
    lip_r = 0.3
    lip_h = 0.3

    h = 4
    cutout_ratio = 0.25

    points = [
        (0.0, 0.0),
        (r, 0.0),
        (r, pcb_thickness * 0.85),
        (r + lip_r, pcb_thickness + lip_h),
        (r * cutout_ratio, h),
        (0.0, h),
    ]

    flat = Shape.polygon(points)
    stud = flat.extrude_rotate(fn=30)
    cutout = Shape.cube(r * cutout_ratio * 2, r * 4, h).translate(
        0, 0, (h / 2) + (pcb_thickness * 0.50)
    )
    return Shape.difference(stud, [cutout])


def oled_holder_parts(wall_thickness: float) -> Tuple[Shape, Shape]:
    display_w = 32.5
    display_h = 12.0
    extra_thickness = 0.1
    display_thickness = 1.53 + extra_thickness

    pcb_w = 33.5
    pcb_h = 21.65
    pcb_thickness = 1.57
    pcb_tolerance = 0.5

    qt_cable_h = 9
    qt_cable_cutout_w = 10

    display_cutout = Shape.cube(
        display_w, display_thickness, display_h
    ).translate(0, (display_thickness - extra_thickness) / 2, 0)
    pcb_cutout = Shape.cube(
        pcb_w + pcb_tolerance, wall_thickness, pcb_h + pcb_tolerance
    ).translate(0, (wall_thickness / 2) + display_thickness - 0.1, 0)
    qt_cable_cutout = Shape.cube(
        qt_cable_cutout_w + extra_thickness, wall_thickness, qt_cable_h
    ).translate(
        -(qt_cable_cutout_w + pcb_w) / 2,
        (wall_thickness / 2) + display_thickness - 0.1,
        0,
    )

    header_cutout = Shape.cube(18, wall_thickness, 4).translate(
        0, (wall_thickness / 2) + 0.8, 2 + (-pcb_h / 2)
    )

    cutin_w = 1.75
    cutin_h = 2.0
    cutin_thickness = display_thickness - 0.1
    cable_cutin = Shape.cube(cutin_w, cutin_thickness, cutin_h).translate(
        (display_w - cutin_w) / 2, cutin_thickness / 2, (display_h - cutin_h) / 2.0
    )

    oled_cable_h = display_h - cutin_h
    oled_cable_cutout_w = 2
    oled_cable_cutout = Shape.difference(
        Shape.cube(
            oled_cable_cutout_w + extra_thickness,
            wall_thickness + extra_thickness,
            oled_cable_h,
        ),
        [
            Shape.cube(10, 2, oled_cable_h + extra_thickness)
            .translate(0, -1, 0)
            .rotate(0, 0, 15)
            .translate(-1, 1 + (-(2 + wall_thickness) / 2), 0)
        ],
    ).translate(
        (oled_cable_cutout_w + display_w) / 2,
        (wall_thickness + extra_thickness) / 2,
        -(cutin_h / 2),
    )

    stud = (
        standoff_stud(d=2.5)
        .rotate(-90, 0, 0)
        .translate(0, display_thickness - 0.01, 0)
    )
    postive_parts = [
        stud.translate(-14.0, 0, -8.325),
        stud.translate(14.0, 0, -8.325),
        stud.translate(14.0, 0, 8.175),
        stud.translate(-14.0, 0, 8.175),
        cable_cutin,
    ]

    cutouts = [
        display_cutout,
        pcb_cutout,
        qt_cable_cutout,
        oled_cable_cutout,
        header_cutout,
    ]

    if False:
        display = (
            oled_display()
            .rotate(90, 0, 0)
            .highlight()
            .translate(
                -pcb_w / 2, pcb_thickness + display_thickness, -pcb_h / 2
            )
        )
        postive_parts.append(display)

    return Shape.union(cutouts), Shape.union(postive_parts)


def oled_holder() -> Shape:
    wall_thickness = 4
    negative_part, postive_part = oled_holder_parts(wall_thickness)
    wall = (
        Shape.cube(50, wall_thickness, 30)
        .translate(0, wall_thickness / 2, 0)
        .translate(-4, 0, 0)
    )
    main = Shape.difference(wall, [negative_part])
    return Shape.union([main, postive_part])


def sx509_holder() -> Shape:
    # return oled_display()
    # return esp32_feather()
    return sx509_breakout()


def write_shape(shape: Shape, path: Path) -> None:
    path.write_text(shape.to_str())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--show-keycaps", action="store_true")
    ap.add_argument("--show-collisions", action="store_true")
    ap.add_argument("--loose-keyholes", action="store_true")
    args = ap.parse_args()

    out_dir = Path("_out")
    out_dir.mkdir(exist_ok=True)

    write_shape(
        model_right(
            show_caps=args.show_keycaps,
            show_collisions=args.show_collisions,
            loose_holes=args.loose_keyholes,
        ),
        out_dir / "right.scad",
    )
    write_shape(
        model_left(
            show_caps=args.show_keycaps,
            show_collisions=args.show_collisions,
            loose_holes=args.loose_keyholes,
        ),
        out_dir / "left.scad",
    )

    write_shape(sx509_holder(), out_dir / "sx509_holder.scad")
    write_shape(oled_holder(), out_dir / "oled_holder.scad")


if __name__ == "__main__":
    main()
