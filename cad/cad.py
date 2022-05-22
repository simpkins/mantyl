#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import math
import numpy
from typing import List, Optional, Sequence, Tuple


class Transform:
    def __init__(self, data: Optional[numpy.array] = None) -> None:
        if data is None:
            self._data = numpy.array(
                ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))
            )
        else:
            self._data = data

    def __str__(self) -> str:
        row_strs = []
        for row in self._data:
            row_contents = ", ".join(str(elem) for elem in row)
            row_strs.append(f"[{row_contents}]")
        contents = ", ".join(row_strs)
        return f"[{contents}]"

    def point(self) -> Point:
        return Point(self._data[0][3], self._data[1][3], self._data[2][3])

    def apply(self, point: Point) -> Point:
        x = numpy.matmul(
            self._data, numpy.array((point.x, point.y, point.z, 1))
        )
        return Point(x[0], x[1], x[2])

    def transform(self, tf: Transform) -> Transform:
        return Transform(numpy.matmul(tf._data, self._data))

    def translate(self, x: float, y: float, z: float) -> Transform:
        x = numpy.array(
            ((1, 0, 0, x), (0, 1, 0, y), (0, 0, 1, z), (0, 0, 0, 1))
        )
        return Transform(numpy.matmul(x, self._data))

    def rotate(self, x: float, y: float, z: float) -> Transform:
        x_r = math.radians(x)
        y_r = math.radians(y)
        z_r = math.radians(z)
        x = numpy.array(
            (
                (
                    math.cos(y_r) * math.cos(z_r),
                    (math.sin(x_r) * math.sin(y_r) * math.cos(z_r))
                    - (math.cos(x_r) * math.sin(z_r)),
                    (math.cos(x_r) * math.sin(y_r) * math.cos(z_r))
                    + (math.sin(x_r) * math.sin(z_r)),
                    0,
                ),
                (
                    math.cos(y_r) * math.sin(z_r),
                    (math.sin(x_r) * math.sin(y_r) * math.sin(z_r))
                    + (math.cos(x_r) * math.cos(z_r)),
                    (math.cos(x_r) * math.sin(y_r) * math.sin(z_r))
                    - (math.sin(x_r) * math.cos(z_r)),
                    0,
                ),
                (
                    -math.sin(y_r),
                    math.sin(x_r) * math.cos(y_r),
                    math.cos(x_r) * math.cos(y_r),
                    0,
                ),
                (0, 0, 0, 1),
            )
        )
        return Transform(numpy.matmul(x, self._data))


class Point:
    def __init__(self, x: float, y: float, z: float) -> None:
        self._x = x
        self._y = y
        self._z = z

    def __str__(self) -> str:
        return f"[{self.x}, {self.y}, {self.z}]"

    def as_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def get_x(self) -> float:
        return self._x

    def get_y(self) -> float:
        return self._y

    def get_z(self) -> float:
        return self._z

    def set_x(self, x: float) -> None:
        self._x = x

    def set_y(self, y: float) -> None:
        self._y = y

    def set_z(self, z: float) -> None:
        self._z = z

    x = property(get_x, set_x)
    y = property(get_y, set_y)
    z = property(get_z, set_z)

    def copy(self) -> Point:
        return Point(self._x, self._y, self._z)

    def translate(self, x: float, y: float, z: float) -> Point:
        return Point(self._x + x, self._y + y, self._z + z)

    def ptranslate(self, point: Point) -> Point:
        return Point(
            self._x + point._x, self._y + point._y, self._z + point._z
        )

    def transform(self, tf: Transform) -> Point:
        return (
            Transform().translate(self._x, self._y, self._z)
            .transform(tf)
            .point()
        )

    def __add__(self, other: Point) -> Point:
        assert isinstance(other, Point)
        return Point(
            self._x + other._x, self._y + other._y, self._z + other._z
        )
