#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List, Tuple, TypeVar

from cad import Mesh, Point, Transform
from openscad import PosAndNeg, Shape, tri_strip
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
import oukey2

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
        self,
        post: Shape,
        near_corner: Point,
        far_corner: Point,
        highlight: bool = False,
    ) -> None:
        self.post = post
        self.near = near_corner
        self.far = far_corner
        self.highlight = highlight

    def ground(self) -> Point:
        return Point(self.far.x, self.far.y, 0)


class ThumbWallPost:
    """
    WallPost contains point information about a single vertical portion of the
    outer thumb section walls.

    This is similar to WallPost, but the thumb walls do not have separate near
    & far corners.  They drop straight to the ground instead of having a taper
    from the near to far corner.
    """

    def __init__(
        self, post: Shape, corner: Point, highlight: bool = False
    ) -> None:
        self.post = post
        self.corner = corner
        self.highlight = highlight

    def ground(self) -> Point:
        return Point(self.corner.x, self.corner.y, 0)


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

        # Set to true to render the walls transparent grey.  This makes it a
        # little easier to see and debug positioning of the feet.
        self.grey_walls = False

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
        self,
        shape: ShapeOrTransform,
        col: int,
        row: int,
        true_pos: bool = False,
    ) -> ShapeOrTransform:
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
            # I plan to use a 1x1.5 key for this position
            # The bottom end of the other rows is at -offset - (18.415 / 2)
            # The 1.5 key is 27.6225mm in length.
            len_1x1 = 18.415
            len_1x1_5 = len_1x1 * 1.5
            bottom_edge = -offset - (len_1x1 * 0.5)
            y = bottom_edge + (len_1x1_5 * 0.5)
            return shape.translate(offset, y, 0)
        if key == (2, 2):
            raise Exception("todo")
            # TODO: remove this
            larger_offset = 24
            return shape.translate(
                offset, (offset / 2.0) - (2 * larger_offset), 0
            )

        raise Exception("unknown thumb position")

    def thumb_pos_br(
        self, shape: ShapeOrTransform, true_pos: bool = False
    ) -> ShapeOrTransform:
        """Return the position of the bottom right thumb if the thumb section
        were actually 3x3 grid.  This is used for computing the connecting mesh
        around the thumb holes, and for the thumb wall, so that the wall is a
        straight line at the bottom.
        """
        if true_pos:
            return self.thumb_orientation(self.thumb_pos_br(shape))

        offset = 19
        return shape.translate(offset, -offset, 0)

    def thumb_positions_1x1(self, shape: Shape) -> List[Shape]:
        shapes: List[Shape] = []

        for col in (0, 1):
            for row in range(3):
                shapes.append(self.thumb_pos(shape, col, row))

        shapes.append(self.thumb_pos(shape, 2, 0))

        return shapes

    def thumb_positions(self, shape: Shape) -> List[Shape]:
        return self.thumb_positions_1x1(shape) + [self.thumb_pos(shape, 2, 1)]

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

        # vertical line between columns 1 and 2,
        # plus wrapping around the top and bottoms of column 2
        result += tri_strip(
            self.thumb_pos(corner_tr(), 2, 0),
            self.thumb_pos(corner_tr(), 1, 0),
            self.thumb_pos(corner_tl(), 2, 0),
            self.thumb_pos(corner_br(), 1, 2),
            self.thumb_pos(corner_bl(), 2, 1),
            self.thumb_pos_br(corner_bl()),
            self.thumb_pos(corner_br(), 2, 1),
            self.thumb_pos_br(corner_br()),
        )

        # horizontal connectors between rows 0 and 1
        result += tri_strip(
            self.thumb_pos(corner_bl(), 0, 0),
            self.thumb_pos(corner_tl(), 0, 1),
            self.thumb_pos(corner_br(), 1, 0),
            self.thumb_pos(corner_tr(), 1, 1),
        )
        # horizontal connectors between rows 1 and 2
        result += tri_strip(
            self.thumb_pos(corner_bl(), 0, 1),
            self.thumb_pos(corner_tl(), 0, 2),
            self.thumb_pos(corner_br(), 1, 1),
            self.thumb_pos(corner_tr(), 1, 2),
        )
        # horizontal connectors between rows 0 and 1
        # for column 2
        result += tri_strip(
            self.thumb_pos(corner_bl(), 2, 0),
            self.thumb_pos(corner_tl(), 2, 1),
            self.thumb_pos(corner_br(), 2, 0),
            self.thumb_pos(corner_tr(), 2, 1),
        )

        return result

    def thumb_area(self) -> List[Shape]:
        shapes: List[Shape] = []
        shapes += self.thumb_positions(self.key_hole)
        shapes += self.thumb_connectors()
        return [self.thumb_orientation(Shape.union(shapes))]

    def thumb_connect_wall(self) -> List[Shape]:
        result: List[Shape] = []

        upper_wall_height = 5

        corner, ground_corner = self.wall_corners()
        small_r = self.wall_radius * 0.5
        small_corner = Shape.sphere(small_r, fn=24)

        left_bl = small_corner.translate(
            -mount_width / 2 - (small_r * 0.5),
            -mount_height / 2 - (small_r * 0.5),
            plate_thickness - small_r,
        )
        left_br = small_corner.translate(
            mount_width / 2 - small_r,
            -mount_height / 2 - small_r,
            plate_thickness - small_r,
        )
        left_bl_low = left_bl.translate(0, 0, -upper_wall_height)
        left_br_low = left_br.translate(0, 0, -upper_wall_height)
        corners: List[Shape] = [
            self.place_key(left_bl.translate(-2, 0, 0), -1, 4),
            self.place_key(left_br, -1, 4),
            self.place_key(left_bl, 0, 4),
            self.place_key(left_bl, 1, 5),
        ]
        low_corners: List[Shape] = [
            self.place_key(left_bl_low.translate(-2, 0, 0), -1, 4),
            self.place_key(left_br_low, -1, 4),
            self.place_key(left_bl_low, 0, 4),
            self.place_key(left_bl_low, 1, 5),
        ]

        right_tr = small_corner.translate(
            mount_width / 2 + (small_r * 0.5) + 4,
            mount_height / 2 + (small_r * 0.5) + 4,
            plate_thickness - small_r,
        )
        right_br = small_corner.translate(
            mount_width / 2 + (small_r * 0.5) + 8,
            -mount_height / 2 - (small_r * 0.5) + 8,
            plate_thickness - small_r,
        )
        thumb_corners: List[Shape] = [
            corner.ptranslate(self.thumb_posts[-1].corner),
            self.thumb_pos(right_tr, 2, 0, true_pos=True),
            self.thumb_pos_br(right_br, true_pos=True),
            corner.ptranslate(self.thumb_posts[0].corner),
        ]

        # Gap between upper key holes and the connecting wall
        result += tri_strip(
            self.place_key(corner_tl(), -1, 4),
            corner.ptranslate(self.left_wall_posts[0].near),
            self.place_key(corner_bl(), -1, 4),
            corners[0],
            self.place_key(corner_br(), -1, 4),
            corners[1],
            self.place_key(corner_bl(), 0, 4),
            corners[2],
            self.place_key(corner_bl(), 1, 5),
            corners[3],
            self.place_key(corner_br(), 1, 5),
            corner.ptranslate(self.front_wall_posts[-1].far),
        )
        # Strip from top corners to top-lower corners
        result += tri_strip(
            corner.ptranslate(self.left_wall_posts[0].near),
            corner.ptranslate(self.left_wall_posts[0].far),
            corners[0],
            low_corners[0],
            corners[1],
            low_corners[1],
            corners[2],
            low_corners[2],
            corners[3],
            low_corners[3],
            corner.ptranslate(self.front_wall_posts[-1].far),
        )
        # Strip from top-lower corners to thumb corners
        result += tri_strip(
            corner.ptranslate(self.left_wall_posts[0].far),
            thumb_corners[0],
            low_corners[0],
            thumb_corners[1],
            low_corners[1],
        )
        result += tri_strip(
            low_corners[1],
            thumb_corners[1],
            low_corners[2],
            thumb_corners[2],
            low_corners[3],
            thumb_corners[3],
            corner.ptranslate(self.front_wall_posts[-1].far),
        )

        # Connecting wall at top of thumb section
        result += tri_strip(
            ground_corner.ptranslate(self.thumb_posts[-1].ground()),
            ground_corner.ptranslate(self.left_wall_posts[0].ground()),
            thumb_corners[0],
            corner.ptranslate(self.left_wall_posts[0].far),
        )
        # Connecting wall at bottom-right of thumb section
        result += tri_strip(
            ground_corner.ptranslate(self.thumb_posts[0].ground()),
            ground_corner.ptranslate(self.front_wall_posts[-1].ground()),
            thumb_corners[-1],
            corner.ptranslate(self.front_wall_posts[-1].far),
        )

        # Horizontal perimeter between the thumb keys and the connecting wall
        result += tri_strip(
            self.thumb_pos(corner_tr(), 1, 0, true_pos=True),
            thumb_corners[0],
            self.thumb_pos(corner_tr(), 2, 0, true_pos=True),
            thumb_corners[1],
            self.thumb_pos_br(corner_br(), true_pos=True),
            thumb_corners[2],
            thumb_corners[3],
        )
        return result

    def thumb_caps(self) -> Shape:
        parts = self.thumb_positions_1x1(dsa_cap())
        parts.append(self.thumb_pos(dsa_cap(ratio=1.5), 2, 1))
        return self.thumb_orientation(Shape.union(parts))

    def wall_tl(self, column: int, row: int) -> Transform:
        tf = Transform().translate(-mount_width / 2, mount_height / 2, 0)
        tf2 = self.place_key(tf, column, row)
        return tf2.translate(0, 3, 0)

    def wall_tr(self, column: int, row: int) -> Transform:
        tf = Transform().translate(mount_width / 2, mount_height / 2, 0)
        tf2 = self.place_key(tf, column, row)
        return tf2.translate(0, 5, 0)

    def wall_segments(self, posts: List[WallPost]) -> List[Shape]:
        result: List[Shape] = []
        for idx in range(1, len(posts)):
            result += self.wall_segment(posts[idx - 1], posts[idx])

        return result

    def wall_corners(self) -> Tuple[Shape, Shape]:
        corner = Shape.sphere(self.wall_radius, fn=24)
        ground_corner = Shape.sphere(self.wall_radius, fn=24).difference(
            [
                Shape.cube(
                    self.wall_radius * 2,
                    self.wall_radius * 2,
                    self.wall_radius * 2,
                ).translate(0, 0, -self.wall_radius)
            ]
        )
        return corner, ground_corner

    def wall_segment(self, post1: WallPost, post2: WallPost) -> List[Shape]:
        corner, ground_corner = self.wall_corners()

        ground1 = Point(post1.far.x, post1.far.y, 0)
        ground2 = Point(post2.far.x, post2.far.y, 0)
        return [
            Shape.hull(
                [
                    post1.post,
                    post2.post,
                    corner.ptranslate(post1.near),
                    corner.ptranslate(post2.near),
                ]
            ).highlight(post1.highlight or post2.highlight),
            Shape.hull(
                [
                    corner.ptranslate(post1.near),
                    corner.ptranslate(post2.near),
                    corner.ptranslate(post1.far),
                    corner.ptranslate(post2.far),
                ]
            ).highlight(post1.highlight or post2.highlight),
            Shape.hull(
                [
                    corner.ptranslate(post1.far),
                    corner.ptranslate(post2.far),
                    ground_corner.ptranslate(ground1),
                    ground_corner.ptranslate(ground2),
                ]
            ).highlight(post1.highlight or post2.highlight),
        ]

    def wall_post(
        self,
        column: int,
        row: int,
        key_post: Shape,
        corner_transform: Transform,
        far_offset: Point,
        highlight: bool = False,
    ) -> WallPost:
        near = self.place_key(corner_transform, column, row).point()
        far = near.ptranslate(far_offset)
        post = self.place_key(key_post, column, row)
        return WallPost(post, near, far, highlight=highlight)

    def wall_left(self) -> List[WallPost]:
        straight_lower_wall = True
        straight_upper_wall = False

        # Top left key hole corner
        left_tl = Transform().translate(
            -mount_width / 2 - self.wall_radius,
            mount_height / 2,
            plate_thickness - self.wall_radius,
        )
        # Bottom left key hole corner
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

        if straight_lower_wall:
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

        if straight_upper_wall:
            upper_x = min(post.far.x for post in upper_posts)
            for post in upper_posts:
                post.far.x = upper_x

        # The concave corner between the horizontal wall and upper wall needs
        # a little tweaking.  Make sure these two posts do not intersect into
        # the other wall.
        if horiz_posts[-1].far.x > upper_posts[0].far.x:
            horiz_posts[-1].far.x = upper_posts[0].far.x
        if upper_posts[0].far.y < horiz_posts[-1].far.y:
            upper_posts[0].far.y = horiz_posts[-1].far.y

        return lower_posts + horiz_posts + upper_posts

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

    def wall_front(self) -> List[WallPost]:
        # Bottom left key hole corner
        front_bl = Transform().translate(
            -mount_width / 2 + (self.wall_radius * 0.5),
            -mount_height / 2 - self.wall_radius,
            plate_thickness - self.wall_radius,
        )
        # Bottom right key hole corner
        front_br = Transform().translate(
            mount_width / 2 + self.wall_radius,
            -mount_height / 2 - self.wall_radius,
            plate_thickness - self.wall_radius,
        )
        front_br_normal = Transform().translate(
            mount_width / 2,
            -mount_height / 2 - self.wall_radius,
            plate_thickness - self.wall_radius,
        )

        last_row = 5
        front_wall_offset = Point(0.0, -1.0, 0.0)
        posts: List[WallPost] = []
        posts.append(
            self.wall_post(
                5, last_row, corner_br(), front_br_normal, front_wall_offset
            )
        )
        posts.append(
            self.wall_post(
                5, last_row, corner_bl(), front_bl, front_wall_offset
            )
        )
        for column in (4, 3, 2, 1):
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

        # We don't want the very last post; we want to end on the right hand
        # side of column 1 rather than the left.
        del posts[-1]

        min_y = min(post.far.y for post in posts)
        for post in posts:
            post.far.y = min_y

        return posts

    def thumb_wall_segments(self, posts: List[ThumbWallPost]) -> List[Shape]:
        corner, ground_corner = self.wall_corners()

        result: List[Shape] = []
        for idx in range(1, len(posts)):
            post1 = posts[idx - 1]
            post2 = posts[idx]
            ground1 = Point(post1.corner.x, post1.corner.y, 0)
            ground2 = Point(post2.corner.x, post2.corner.y, 0)
            result.append(
                Shape.hull(
                    [
                        corner.ptranslate(post1.corner),
                        ground_corner.ptranslate(ground1),
                        corner.ptranslate(post2.corner),
                        ground_corner.ptranslate(ground2),
                    ]
                )
            )
            result.append(
                Shape.hull(
                    [
                        post1.post,
                        post2.post,
                        corner.ptranslate(post1.corner),
                        corner.ptranslate(post2.corner),
                    ]
                )
            )

        return result

    def wall_thumb_posts(self) -> List[ThumbWallPost]:
        posts: List[ThumbWallPost] = []

        def add_post(
            col: int, row: int, post: Shape, transform: Transform
        ) -> None:
            posts.append(
                ThumbWallPost(
                    self.thumb_pos(post, col, row, true_pos=True),
                    self.thumb_pos(transform, col, row, true_pos=True).point(),
                )
            )

        # Add some extra offset between the key holes and the wall.  This is
        # mainly to give some extra room to make soldering the keys easier.
        wall_offset = 3.0
        top_left = Transform().translate(
            -mount_width / 2 - self.wall_radius - wall_offset,
            mount_height / 2 + self.wall_radius + wall_offset,
            plate_thickness - self.wall_radius,
        )
        top_right = Transform().translate(
            mount_width / 2 + self.wall_radius + wall_offset,
            mount_height / 2 + self.wall_radius + wall_offset,
            plate_thickness - self.wall_radius,
        )
        bottom_left = Transform().translate(
            -mount_width / 2 - self.wall_radius - wall_offset,
            -mount_height / 2 - self.wall_radius - wall_offset,
            plate_thickness - self.wall_radius,
        )

        # Note: wall_extra_len is the extra length needed so that this wall
        # extends so that it is even with the front wall.  Ideally it would be
        # nice to calculate this from self.front_wall_posts[-1].far.y
        wall_extra_len = 18.6

        bottom_right = Transform().translate(
            mount_width / 2 + self.wall_radius + wall_offset + wall_extra_len,
            -mount_height / 2 - self.wall_radius - wall_offset,
            plate_thickness - self.wall_radius,
        )

        posts.append(
            ThumbWallPost(
                self.thumb_pos_br(corner_br(), true_pos=True),
                self.thumb_pos_br(bottom_right, true_pos=True).point(),
            )
        )
        add_post(0, 2, corner_bl(), bottom_left)
        add_post(0, 0, corner_tl(), top_left)
        add_post(1, 0, corner_tr(), top_right)

        return posts

    def thumb_walls(self, oled_display: bool) -> List[Shape]:
        self.thumb_posts = self.wall_thumb_posts()

        # Thumb area walls
        wall_segments = self.thumb_wall_segments(self.thumb_posts)
        neg_parts: List[Shape] = []

        if self.grey_walls:
            pos_parts: List[Shape] = [Shape.union(wall_segments).grey()]
        else:
            pos_parts: List[Shape] = wall_segments

        # OLED holder
        if oled_display:
            holder_tf = self.apply_to_wall(
                self.thumb_posts[2].corner,
                self.thumb_posts[1].corner,
                Transform().translate(1.75 * 0.5, 0, 22.5),
            )
            holder_neg, holder_pos = joint_holder_parts(
                self.wall_radius * 2, holder_top=False
            )
            neg_parts.append(holder_neg.transform(holder_tf))
            holder_pos = holder_pos.transform(holder_tf)

        # Add the cable connector cutout
        cable_holder_neg = mag_conn_holder_parts(
            self.wall_radius * 2
        ).translate(0, 0, 4)
        cable_holder_tf = self.apply_to_wall(
            self.thumb_posts[3].corner,
            self.thumb_posts[2].corner,
            Transform().translate(0, 0, 7.5),
        )
        neg_parts.append(cable_holder_neg.transform(cable_holder_tf))

        # Add feet
        back_left = self.thumb_posts[2].corner
        back_left_foot = foot(off_x=9, off_y=-0.5)
        back_left_foot = back_left_foot.translate(back_left.x, back_left.y, 0)
        pos_parts.append(back_left_foot.pos)
        neg_parts.append(back_left_foot.neg)

        front_right = self.thumb_posts[1].corner
        front_right_foot = foot(off_x=1, off_y=10)
        front_right_foot = front_right_foot.translate(
            front_right.x, front_right.y, 0
        )
        pos_parts.append(front_right_foot.pos)
        neg_parts.append(front_right_foot.neg)

        result = [Shape.difference(Shape.union(pos_parts), neg_parts)]
        if oled_display:
            result.append(holder_pos)

        return result

    def main_walls(self) -> List[Shape]:
        back_wall_posts = self.wall_back()
        self.front_wall_posts = self.wall_front()
        self.left_wall_posts = self.wall_left()

        posts = (
            self.left_wall_posts
            + back_wall_posts
            + self.wall_right()
            + self.front_wall_posts
        )
        main_walls = self.wall_segments(posts)

        if self.grey_walls:
            pos_parts: List[Shape] = [Shape.union(main_walls).grey()]
        else:
            pos_parts: List[Shape] = main_walls
        neg_parts: List[Shape] = []

        # Feet
        back_left = back_wall_posts[0].far
        back_left_foot = foot(off_x=4.2, off_y=-6.8)
        back_left_foot = back_left_foot.translate(back_left.x, back_left.y, 0)
        pos_parts.append(back_left_foot.pos)
        neg_parts.append(back_left_foot.neg)

        back_right = back_wall_posts[-1].far
        back_right_foot = foot(off_x=-5.2, off_y=-6.8)
        back_right_foot = back_right_foot.translate(
            back_right.x, back_right.y, 0
        )
        pos_parts.append(back_right_foot.pos)
        neg_parts.append(back_right_foot.neg)

        front_right = self.front_wall_posts[0].far
        front_right_foot = foot(off_x=-5.2, off_y=6.8)
        front_right_foot = front_right_foot.translate(
            front_right.x, front_right.y, 0
        )
        pos_parts.append(front_right_foot.pos)
        neg_parts.append(front_right_foot.neg)

        left_corner = self.left_wall_posts[4].far
        left_corner_foot = foot(off_x=7, off_y=-5)
        left_corner_foot = left_corner_foot.translate(
            left_corner.x, left_corner.y, 0
        )
        pos_parts.append(left_corner_foot.pos)
        neg_parts.append(left_corner_foot.neg)

        # Screw holes for wrist rest
        for x, z in [(-20, 5), (20, 5), (-20, 25), (20, 25)]:
            screw_hole_tf = self.apply_to_wall(
                self.front_wall_posts[0].far,
                self.front_wall_posts[-1].far,
                Transform().translate(x, 0, z),
            )
            neg_parts.append(
                screw_hole_parts(self.wall_radius * 2).transform(screw_hole_tf)
            )

        return [Shape.difference(Shape.union(pos_parts), neg_parts)]

    def apply_to_wall(
        self,
        post1: Point,
        post2: Point,
        initial_tf: Optional[Transform] = None,
    ) -> Transform:
        """
        Return a transform to apply an object to the surface of a wall.

        post1 and post2 should be the left and right points of the wall.
        This only looks at the x and y coordinates, and does not adjust up or
        down on the z axis.
        """
        # Move the object forwards by half the wall thickness so its front
        # aligns with the front of the wall (assuming its front is along the
        # y=0 axis).
        #
        # Also adjust it along the x axis so that it is centered on the wall
        # (assuming it starts centered around x = 0)
        wall_len = math.sqrt(
            ((post2.y - post1.y) ** 2) + ((post2.x - post1.x) ** 2)
        )
        if initial_tf is None:
            initial_tf = Transform()
        translate_tf = initial_tf.translate(
            wall_len * 0.5, -self.wall_radius, 0.0
        )

        # Next rotate the object so it is at the same angle to the x axis
        # as the wall.
        angle = math.atan2(post2.y - post1.y, post2.x - post1.x)
        angle_tf = Transform(
            (
                (math.cos(angle), -math.sin(angle), 0.0, 0.0),
                (math.sin(angle), math.cos(angle), 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (0.0, 0.0, 0.0, 1.0),
            )
        )

        # Finally move the object from the origin so it is at the wall location
        tf = translate_tf.transform(angle_tf).translate(post1.x, post1.y, 0)
        return tf


def model_right(
    *,
    oled_display: bool = False,
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
        + kbd.thumb_walls(oled_display=oled_display)
        + kbd.main_walls()
        + kbd.thumb_connect_wall()
    )

    if show_caps:
        parts.append(kbd.key_caps().grey())
        parts.append(kbd.thumb_caps().grey())
    if show_collisions:
        parts.append(kbd.key_collisions().highlight())

    return Shape.union(parts)


def model_left(
    *,
    show_caps: bool = False,
    show_collisions: bool = False,
    loose_holes: bool = False,
) -> Shape:
    right = model_right(
        oled_display=True,
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


def sx1509_breakout() -> Shape:
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
        ],
    )


def standoff_stud(d: float, offset: float = 0.0) -> Shape:
    tolerance = d * 0.075
    r = (d / 2) - tolerance

    pcb_thickness = 1.57
    lip_r = 0.3
    lip_h = 0.3

    h = 4
    cutout_ratio = 0.25

    points: List[Tuple[float, float]] = [(0.0, 0.0)]
    if offset > 0.0:
        collar_r = 0.5
        points += [(r + collar_r, 0.0), (r + collar_r, offset)]

    points += [
        (r, offset),
        (r, offset + (pcb_thickness * 0.85)),
        (r + lip_r, offset + (pcb_thickness + lip_h)),
        (r * cutout_ratio, offset + h),
        (0.0, offset + h),
    ]

    flat = Shape.polygon(points)
    stud = flat.extrude_rotate(fn=30)
    cutout = Shape.cube(r * cutout_ratio * 2, r * 4, h).translate(
        0, 0, (h / 2) + (pcb_thickness * 0.50) + offset
    )
    return Shape.difference(stud, [cutout])


def oled_holder_parts(wall_thickness: float) -> Tuple[Shape, Shape]:
    display_w = 32.5
    display_h = 12.2
    extra_thickness = 0.1
    display_thickness = 1.53 + extra_thickness

    pcb_w = 33.5
    pcb_h = 21.8
    pcb_thickness = 1.57
    pcb_tolerance = 0.5

    qt_cable_h = 9
    qt_cable_cutout_w = 3

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

    cutin_w = 2.5
    cutin_h = 2.0
    cutin_thickness = display_thickness - 0.1
    cable_cutin = Shape.cube(cutin_w, cutin_thickness, cutin_h).translate(
        (display_w - cutin_w) / 2,
        cutin_thickness / 2,
        (display_h - cutin_h) / 2.0,
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


def sx1509_holder_part(
    wall_thickness: float, stud_offset: float = 3.0, holder_top: bool = True
) -> Shape:
    stud = (
        standoff_stud(d=3.302, offset=stud_offset)
        .rotate(-90, 0, 0)
        .translate(0, wall_thickness - 0.01, 0)
    )

    bracket_d = stud_offset + 2.5
    bracket_l = 26.0
    bracket_h = 1.5
    bracket = (
        Shape.polygon(
            [
                (0.0, 0.0),
                (stud_offset + 1.8, 0.0),
                (stud_offset + 1.8, 0.5),
                (stud_offset + 2.5, 0.0),
                (stud_offset + 2.5, -bracket_h),
                (0.0, -bracket_h),
            ]
        )
        .extrude_linear(bracket_l)
        .rotate(90.0, 0.0, 90.0)
        .translate(0.0, wall_thickness - 0.01, -18.4)
    )

    x = 10.287
    y = 15.367
    parts = [
        stud.translate(x, 0.0, y),
        stud.translate(-x, 0.0, y),
        stud.translate(-x, 0.0, -y),
        stud.translate(x, 0.0, -y),
        bracket,
    ]
    if holder_top:
        parts.append(bracket.mirror(0.0, 0.0, 1.0))

    if False:
        pcb_thickness = 1.57
        sx1509 = (
            sx1509_breakout()
            .rotate(90, 90, 0)
            .highlight()
            .translate(
                0, (pcb_thickness / 2.0) + wall_thickness + stud_offset, 0
            )
        )
        parts.append(sx1509)

    return Shape.union(parts)


def sx1509_holder() -> Shape:
    wall_thickness = 4
    part = sx1509_holder_part(wall_thickness)

    wall = Shape.difference(
        Shape.cube(28, wall_thickness, 38),
        [Shape.cube(18, wall_thickness * 1.1, 26)],
    ).translate(0, wall_thickness / 2, 0)
    return Shape.union([wall, part])


def joint_holder_parts(
    wall_thickness: float, holder_top: bool = True
) -> Tuple[Shape, Shape]:
    """Return (neg_part, pos_part)"""
    wall = (
        Shape.cube(50, wall_thickness, 48)
        .translate(0, wall_thickness / 2, 0)
        .translate(-4, 0, 0)
    )

    sx1509_part = sx1509_holder_part(
        wall_thickness, stud_offset=5.0, holder_top=holder_top
    )
    oled_neg_part, oled_pos_part = oled_holder_parts(wall_thickness)
    return oled_neg_part, Shape.union([sx1509_part, oled_pos_part])


def joint_holder() -> Shape:
    wall_thickness = 4
    wall = (
        Shape.cube(50, wall_thickness, 48)
        .translate(0, wall_thickness / 2, 0)
        .translate(-4, 0, 0)
    )

    neg_part, pos_part = joint_holder_parts(wall_thickness)
    return Shape.union([Shape.difference(wall, [neg_part]), pos_part])


def idc_header() -> Shape:
    body_h = 8.6
    main = Shape.cube(28.0, 8.5, body_h)
    inner = Shape.cube(25.9, 6.4, body_h).translate(0.0, 0.0, 2.25)
    edge_cutout1 = Shape.cube(4.0, 3.3, body_h).translate(
        12.945 + 2.0, 0.0, -2.10
    )
    edge_cutout2 = Shape.cube(4.0, 3.3, body_h).translate(
        -12.945 - 2.0, 0.0, -2.10
    )

    body = Shape.difference(
        main, [inner, edge_cutout1, edge_cutout2]
    ).translate(0.0, 0.0, body_h / 2.0)

    pin_h = 11.25
    pin_pitch = 2.54
    pin_z = (pin_h / 2) - 4.0
    pin = Shape.cube(0.64, 0.64, pin_h)
    parts = [body]
    for y in (0.5, -0.5):
        for n in range(8):
            p = pin.translate(pin_pitch * (n - 3.5), pin_pitch * y, pin_z)
            parts.append(p)

    return Shape.union(parts)


def idc_header_holder_parts(wall_thickness: float) -> Shape:
    offset = 6.0

    header_w = 28.0
    header_d = 8.5
    header_h = 8.6

    base_w = 4.0
    base_d = 12.0
    nub_d = (base_d - header_d) / 2.0
    nub_h = 6.0
    nub_tolerance = 0.1

    nub = Shape.cube(base_w, nub_d - nub_tolerance, nub_h)
    nub_l = nub.translate(
        0.0, nub_tolerance + (base_d - nub_d) / 2.0, offset + (nub_h / 2.0)
    )
    nub_r = nub.translate(
        0.0,
        -1.0 * (nub_tolerance + (base_d - nub_d) / 2.0),
        offset + (nub_h / 2.0),
    )

    clip_outline = Shape.polygon(
        [
            (1.0, offset),
            (2.0, offset),
            (2.0, offset + 5.0),
            (0.0, offset + 2.3),
            (1.0, offset + 2.3),
        ]
    )
    clip = clip_outline.extrude_linear(3.0).rotate(90.0, 0.0, 0.0)

    base = Shape.union(
        [
            Shape.cube(base_w, base_d, offset).translate(
                0.0, 0.0, offset / 2.0
            ),
            nub_l,
            nub_r,
            clip,
        ]
    )

    left = base.translate((header_w - base_w) / 2.0, 0.0, 0.0)
    right = left.mirror(1.0, 0.0, 0.0)

    parts = [left, right]

    if False:
        parts.append(idc_header().translate(0.0, 0.0, offset).highlight())

    return (
        Shape.union(parts)
        .rotate(-90, 0, 0)
        .translate(0.0, wall_thickness - 0.1, 0.0)
    )


def idc_header_holder() -> Shape:
    wall_thickness = 4
    holder = idc_header_holder_parts(wall_thickness)

    wall = Shape.cube(30, wall_thickness, 15).translate(
        0, wall_thickness / 2, 0
    )
    return Shape.union([wall, holder])


def foot(off_x: float = 0.0, off_y: float = 0.0, h: float = 15.0) -> PosAndNeg:
    wall_thickness = 4.0
    top_r = wall_thickness * 0.5

    # Actual foot dimensions are about
    # 12.5mm in diameter (6.25mm radius)
    # and about 3.6mm tall

    inner_r = 6.5
    outer_r = inner_r + 2.0
    base_h = 1.25
    recess = 2.75
    fn = 30.0

    t = 0.01
    bottom = Shape.cylinder(h=base_h + recess, r=outer_r, fn=fn).translate(
        off_x, off_y, (base_h + recess) * 0.5
    )
    recess = Shape.cylinder(h=(recess + t), r=inner_r, fn=fn).translate(
        off_x, off_y, (recess * 0.5) - t
    )
    if h > base_h:
        top = Shape.sphere(top_r, fn=fn).translate(0, 0, h - top_r)
        return PosAndNeg(Shape.hull([bottom, top]), recess)
    else:
        return PosAndNeg(bottom, recess)


def mag_conn() -> Shape:
    """Holder for a 5-pin magnetic connector:
    https://www.adafruit.com/product/5413
    """
    w = 20.1
    h = 4.25
    d = 4.05

    flange_d = 0.75
    flange_offset = 2.25

    fn = 30

    core_r = h * 0.5
    core_cyl = Shape.cylinder(h=d, r=core_r, fn=fn).rotate(90.0, 0.0, 0.0)
    core = Shape.hull(
        [
            core_cyl.translate(core_r - (w * 0.5), d * 0.5, 0.0),
            core_cyl.translate((w * 0.5) - core_r, d * 0.5, 0.0),
        ]
    )
    flange = Shape.cube(w, flange_d, h).translate(
        0.0, (flange_d * 0.5) + flange_offset, 0.0
    )
    return Shape.union([core, flange])


def mag_conn_holder_parts(wall_thickness: float) -> Shape:
    d = wall_thickness * 1.1

    w = 20.6
    # If printing the holder face down, h = 4.5 is a good value.
    # However, if printing vertically with support needed to hold up the top
    # of the opening, then this value needs to be a little bit bigger.
    h = 4.8

    flange_d = 0.90
    flange_cutout_d = wall_thickness
    flange_offset = 2.25

    fn = 30
    t = 0.01

    core_r = h * 0.5
    core_cyl = (
        Shape.cylinder(h=d, r=core_r, fn=fn)
        .rotate(90.0, 0.0, 0.0)
        .translate(0.0, -t, 0.0)
    )
    core = Shape.hull(
        [
            core_cyl.translate(core_r - (w * 0.5), d * 0.5, 0.0),
            core_cyl.translate((w * 0.5) - core_r, d * 0.5, 0.0),
        ]
    )
    flange = Shape.cube(w, flange_cutout_d, h).translate(
        0.0, (flange_cutout_d * 0.5) + flange_offset, 0.0
    )

    nub_h = 0.5  # how much the nub sticks out to hold the connector
    nub_w = 0.75
    nub_d = 0.75
    nub = Shape.polygon(
        [(0.0, 0.0), (nub_h, 0.0), (nub_h * 0.5, nub_d), (0.0, nub_d)]
    ).extrude_linear(nub_w)
    nub_bottom = nub.mirror(1.0, 0.0, 0.0)
    nub_offset_d = flange_d + flange_offset - t
    nubbed_flange = Shape.difference(
        flange,
        [
            nub_bottom.translate(
                w * 0.5 + t, nub_offset_d, ((h - nub_w) * 0.5) + t
            ),
            nub_bottom.translate(
                w * 0.5 + t, nub_offset_d, -((h - nub_w) * 0.5) - t
            ),
            nub.translate(-w * 0.5 - t, nub_offset_d, ((h - nub_w) * 0.5) + t),
            nub.translate(
                -w * 0.5 - t, nub_offset_d, -((h - nub_w) * 0.5) - t
            ),
        ],
    )
    return Shape.union([core, nubbed_flange])


def mag_conn_holder() -> Shape:
    wall_thickness = 4.0
    negative_part = mag_conn_holder_parts(wall_thickness)
    wall = Shape.cube(28, wall_thickness, 10).translate(
        0, wall_thickness / 2, 0
    )
    return Shape.difference(wall, [negative_part])


def micro_usb_holder_parts() -> Shape:
    sy = 1.0
    w = 3.85
    h = 2.6
    bx = 2.85

    vertical_mount = True
    if vertical_mount:
        # When printing vertically, we need to add a little extra tolerance
        # in the height
        sy += 0.1
        h += 0.3

    points: List[Tuple[float, float]] = [
        (0, 0),
        (bx, 0),
        (w, sy),
        (w, h - 0.4),
        (w - 0.3, h),
        (w - 1, h),
        (w - 1, h + 0.2),
        (w - 2, h + 0.2),
        (w - 2, h),
        (0, h),
    ]
    all_points = points[:] + list((-x, y) for x, y in reversed(points))

    flare_l = 0.4
    flare = (
        Shape.polygon(all_points)
        .translate(0.0, h * -0.5, 0.0)
        .extrude_linear(flare_l, scale=1.2)
        .translate(0, 0, 2.3 + (flare_l * 0.5))
    )
    main = (
        Shape.polygon(all_points)
        .extrude_linear(4.601)
        .translate(0, -h * 0.5, 0)
    )
    return (
        Shape.union([main, flare])
        .rotate(90.0, 0.0, 0.0)
        .translate(0, 2.3 + flare_l - 0.01, 0)
    )


def micro_usb_holder() -> Shape:
    wall_thickness = 4.0
    negative_part = micro_usb_holder_parts()
    wall = Shape.cube(12, wall_thickness, 8).translate(
        0, wall_thickness / 2, 0
    )

    return Shape.difference(wall, [negative_part])


def screw_hole_parts(wall_thickness: float) -> Shape:
    r = 1.8
    return (
        Shape.cylinder(h=wall_thickness * 1.1, r=r, fn=15)
        .rotate(90, 0, 0)
        .translate(0, wall_thickness * 0.5, 0)
    )


def screw_hole_test() -> Shape:
    wall_thickness = 4.0
    negative_part = screw_hole_parts(wall_thickness)
    wall = Shape.cube(8, wall_thickness, 8).translate(0, wall_thickness / 2, 0)

    return Shape.difference(wall, [negative_part])


def keycaps() -> Shape:
    import keyboard

    return Shape.union(
        [
            keyboard.dsa_cap().translate(-50, 0, 0),
            keyboard.dsa_cap(1.25).translate(-25, 0, 0),
            keyboard.dsa_cap(1.5).translate(0, 0, 0),
            keyboard.dsa_cap(1.75).translate(25, 0, 0),
            keyboard.dsa_cap(2.0).translate(50, 0, 0),
        ]
    )


def write_shape(shape: Shape, path: Path) -> None:
    path.write_text(shape.to_str())


def kbd2_test() -> Shape:
    mesh = oukey2.gen_keyboard()
    return Shape.polyhedron_from_mesh(mesh, convexivity=20)


def key_hole_test() -> Shape:
    mesh = Mesh()
    kh = oukey2.KeyHole(mesh, Transform())
    kh.inner_walls()

    mesh.add_quad(kh.u_bl, kh.u_br, kh.l_br, kh.l_bl)
    mesh.add_quad(kh.u_tl, kh.u_bl, kh.l_bl, kh.l_tl)
    mesh.add_quad(kh.u_tr, kh.u_tl, kh.l_tl, kh.l_tr)
    mesh.add_quad(kh.u_br, kh.u_tr, kh.l_tr, kh.l_br)
    return Shape.polyhedron_from_mesh(mesh)


def orig_key_hole_test() -> Shape:
    return single_plate()


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

    # Component debugging
    write_shape(kbd2_test(), out_dir / "kbd2.scad")
    write_shape(key_hole_test(), out_dir / "key_hole.scad")
    write_shape(orig_key_hole_test(), out_dir / "orig_key_hole.scad")
    write_shape(sx1509_holder(), out_dir / "sx1509_holder.scad")
    write_shape(oled_holder(), out_dir / "oled_holder.scad")
    write_shape(joint_holder(), out_dir / "joint_holder.scad")
    write_shape(idc_header_holder(), out_dir / "header_holder.scad")
    write_shape(mag_conn_holder(), out_dir / "mag_conn_holder.scad")
    write_shape(micro_usb_holder(), out_dir / "micro_usb_holder.scad")
    write_shape(screw_hole_test(), out_dir / "screw_hole.scad")
    write_shape(keycaps(), out_dir / "keycaps.scad")


if __name__ == "__main__":
    main()