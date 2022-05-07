#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import math
import numpy
from typing import List, Optional, Tuple


class Shape:
    """
    Utility class for emitting OpenSCAD elements.
    """

    def __init__(
        self,
        value: str,
        children: Optional[List[Shape]] = None,
        comment: Optional[str] = None,
    ) -> None:
        self.value = value
        self.children = children or []
        self._comment: Optional[str] = comment

    def to_str(self) -> str:
        lines = self.gen()
        lines.append("")
        return "\n".join(lines)

    def gen(self) -> List[str]:
        result: List[str] = []
        if self._comment:
            result.append(f"// {self._comment}")

        if not self.children:
            result.append(f"{self.value};")
        else:
            indent_prefix = "  "
            if len(self.children) == 1:
                result.append(self.value)
            else:
                result.append(f"{self.value} {{")

            for child in self.children:
                for line in child.gen():
                    result.append(indent_prefix + line)
            if len(self.children) > 1:
                result.append("}")

        return result

    def comment(self, comment: str) -> Shape:
        return Shape(value=self.value, children=self.children, comment=comment)

    def highlight(self, highlight: bool = True) -> Shape:
        if highlight:
            return Shape("#", children=[self])
        else:
            return self

    def grey(self) -> Shape:
        return Shape("%", children=[self])

    def color(self, name: str, alpha: float = 1.0) -> Shape:
        return Shape(f'color("{name}", alpha={alpha})', [self])

    def mirror(self, x: float, y: float, z: float) -> Shape:
        return Shape(f"mirror([{x}, {y}, {z}])", [self])

    def translate(self, x: float, y: float, z: float) -> Shape:
        return Shape(f"translate([{x}, {y}, {z}])", [self])

    def ptranslate(self, point: Point) -> Shape:
        return Shape(f"translate([{point.x}, {point.y}, {point.z}])", [self])

    def rotate(self, x: float, y: float, z: float) -> Shape:
        return Shape(f"rotate([{x}, {y}, {z}])", [self])

    def rotate_axis(
        self, deg: float, axis: Tuple[float, float, float]
    ) -> Shape:
        return Shape(
            f"rotate({deg}, [{axis[0]}, {axis[1]}, {axis[2]}])", [self]
        )

    def extrude_linear(
        self,
        height: float,
        twist: float = 0.0,
        scale: float = 1.0,
        convexity: int = 0,
        center: bool = True,
    ) -> Shape:
        return Shape(
            f"linear_extrude(height={height}, twist={twist}, scale={scale}, "
            f"convexity={convexity}, center={self.bool_str(center)})",
            [self],
        )

    def extrude_rotate(
        self,
        angle: float = 360.0,
        *,
        convexivity: Optional[int] = None,
        fa: Optional[float] = None,
        fs: Optional[float] = None,
        fn: Optional[float] = None,
    ) -> Shape:
        args: List[str] = [f"angle={angle}"]
        if convexivity is not None:
            args.append(f"convexivity={convexivity}")
        if fa is not None:
            args.append(f"$fa={fa}")
        if fs is not None:
            args.append(f"$fs={fs}")
        if fn is not None:
            args.append(f"$fn={fn}")

        args_str = ", ".join(args)
        return Shape(f"rotate_extrude({args_str})", [self])

    @classmethod
    def union(cls, children: List[Shape]) -> Shape:
        return cls(f"union()", children)

    def transform(self, tf: Transform) -> Shape:
        return Shape(f"multmatrix({tf})", [self])

    def transform_translate_only(self, tf: Transform) -> Shape:
        return self.translate(tf._data[0][3], tf._data[1][3], tf._data[2][3])

    @classmethod
    def intersection(cls, children: List[Shape]) -> Shape:
        return cls(f"intersection()", children)

    def difference(self, children: List[Shape]) -> Shape:
        return Shape(f"difference()", [self] + children)

    @classmethod
    def hull(cls, children: List[Shape]) -> Shape:
        return cls(f"hull()", children)

    @classmethod
    def cube(cls, x: float, y: float, z: float, center: bool = True) -> Shape:
        return cls(f"cube([{x}, {y}, {z}], center={cls.bool_str(center)})")

    @classmethod
    def square(cls, x: float, y: float, center: bool = True) -> Shape:
        return cls(f"square([{x}, {y}], center={cls.bool_str(center)})")

    @classmethod
    def cylinder(
        cls,
        h: float,
        r: float,
        r2: Optional[float] = None,
        *,
        center: bool = True,
        fa: Optional[float] = None,
        fs: Optional[float] = None,
        fn: Optional[float] = None,
    ) -> Shape:
        args: List[str] = []

        if r2 is None:
            args.append(f"r={r}")
        else:
            args.append(f"r1={r}")
            args.append(f"r2={r2}")

        args.append(f"center={cls.bool_str(center)}")
        if fa is not None:
            args.append(f"$fa={fa}")
        if fs is not None:
            args.append(f"$fs={fs}")
        if fn is not None:
            args.append(f"$fn={fn}")

        args_str = ", ".join(args)
        return cls(f"cylinder(h={h}, {args_str})")

    @classmethod
    def sphere(
        cls,
        r: float,
        *,
        fa: Optional[float] = None,
        fs: Optional[float] = None,
        fn: Optional[float] = None,
    ) -> Shape:
        args: List[str] = [str(r)]
        if fa is not None:
            args.append(f"$fa={fa}")
        if fs is not None:
            args.append(f"$fs={fs}")
        if fn is not None:
            args.append(f"$fn={fn}")

        args_str = ", ".join(args)
        return cls(f"sphere({args_str})")

    @classmethod
    def polygon(cls, points: List[Tuple[float, float]]) -> Shape:
        points_str = ", ".join(f"[{x}, {y}]" for x, y in points)
        return cls(f"polygon([{points_str}])")

    @classmethod
    def project(cls, children: List[Shape]) -> Shape:
        return cls(f"projection(cut = false)", children)

    @staticmethod
    def bool_str(value: bool) -> str:
        return "true" if value else "false"


def tri_strip(*shapes: Shape, highlight: bool = False) -> List[Shape]:
    hulls: List[Shape] = []
    for idx in range(len(shapes) - 2):
        hulls.append(
            Shape.hull([shapes[idx], shapes[idx + 1], shapes[idx + 2]])
        )

    if highlight:
        return [Shape.union(hulls).highlight()]

    return hulls


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

    def __add__(self, other: Point) -> Point:
        assert isinstance(other, Point)
        return Point(
            self._x + other._x, self._y + other._y, self._z + other._z
        )


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

    def apply(self, point: Point) -> Point:
        x = numpy.matmul(
            self._data, numpy.array((point.x, point.y, point.z, 1))
        )
        return Point(x[0], x[1], x[2])

    def translate(self, x: float, y: float, z: float) -> Transform:
        x = numpy.array(
            ((1, 0, 0, x), (0, 1, 0, y), (0, 0, 1, z), (0, 0, 0, 1))
        )
        return Transform(numpy.matmul(x, self._data))

    def point(self) -> Point:
        return Point(self._data[0][3], self._data[1][3], self._data[2][3])

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

    def rotate_around_x(self, angle: Radians) -> Transform:
        r = math.radians(angle)

        return Transform(
            [
                (1, 0, 0),
                (0, math.cos(r), -math.sin(r)),
                (0, math.sin(r), math.cos(r)),
            ]
        )

    def rotate_around_y(self, angle: Radians) -> Transform:
        r = math.radians(angle)

        return Transform(
            [
                (math.cos(r), 0, math.sin(r)),
                (0, 1, 0),
                (-math.sin(r), 0, math.cos(r)),
            ]
        )
