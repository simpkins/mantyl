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
    __slots__ = ["x", "y", "z"]
    x: float
    y: float
    z: float

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> str:
        self.x = x
        self.y = y
        self.z = z

    def __str__(self) -> str:
        return f"[{self.x}, {self.y}, {self.z}]"

    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y}, {self.z})"

    def as_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def copy(self) -> Point:
        return Point(self.x, self.y, self.z)

    def translate(self, x: float, y: float, z: float) -> Point:
        return Point(self.x + x, self.y + y, self.z + z)

    def ptranslate(self, point: Point) -> Point:
        return Point(self.x + point.x, self.y + point.y, self.z + point.z)

    def to_transform(self) -> Transform:
        return Transform().translate(self.x, self.y, self.z)

    def transform(self, tf: Transform) -> Point:
        return self.to_transform().transform(tf).point()

    def unit(self) -> Point:
        """Treating this point as a vector, return a new vector of length 1.0
        """
        length = math.sqrt(
            (self.x * self.x) + (self.y * self.y) + (self.z * self.z)
        )
        factor = 1.0 / length
        return Point(self.x * factor, self.y * factor, self.z * factor)

    def __hash__(self) -> int:
        return hash(self.as_tuple())

    def __eq__(self, other: Point) -> Point:
        assert isinstance(other, Point)
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __ne__(self, other: Point) -> Point:
        assert isinstance(other, Point)
        return not self.__eq__(other)

    def __add__(self, other: Point) -> Point:
        assert isinstance(other, Point)
        return Point(self.x + other.x, self.y + other.y, self.z + other.z)

    def __mul__(self, n: Union[float, int]) -> Point:
        assert isinstance(n, (float, int))
        return Point(self.x * n, self.y * n, self.z * n)


class MeshPoint:
    __slots__ = ["mesh", "_index", "point"]
    mesh: Mesh
    _index: Optional[int]
    point: Point

    def __init__(self, mesh: Mesh, point: Point) -> None:
        self.mesh = mesh
        self._index = None
        self.point = point

    def __repr__(self) -> str:
        return (
            f"MeshPoint(mesh={self.mesh!r}, point={self.point!r}, "
            f"index={self.index!r})"
        )

    @property
    def index(self) -> int:
        if self._index is None:
            self._index = len(self.mesh.points)
            self.mesh.points.append(self)
        return self._index

    @property
    def x(self) -> int:
        return self.point.x

    @property
    def y(self) -> int:
        return self.point.y

    @property
    def z(self) -> int:
        return self.point.z


class MeshFace:
    __slots__ = ["mesh", "_index", "point"]
    mesh: Mesh
    _index: int
    point: Point


class Mesh:
    def __init__(self) -> None:
        self.points: List[MeshPoint] = []
        # We only allow triangular faces for now
        self.faces: List[Tuple[int, int, int]] = []

    def add_point(self, point: Point) -> MeshPoint:
        return MeshPoint(self, point=point)

    def add_tri(self, p0: MeshPoint, p1: MeshPoint, p2: MeshPoint) -> int:
        index = len(self.faces)
        self.faces.append((p0.index, p1.index, p2.index))
        return index

    def add_quad(
        self, p0: MeshPoint, p1: MeshPoint, p2: MeshPoint, p3: MeshPoint
    ) -> int:
        index = len(self.faces)
        self.faces.append((p0.index, p1.index, p2.index, p3.index))
        return index
