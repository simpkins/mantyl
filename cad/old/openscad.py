#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import math
import numpy
from typing import List, Optional, Sequence, Tuple

from cad import Mesh, Point, Transform


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
    def polyhedron(
        cls,
        points: List[Tuple[float, float, float]],
        faces: List[Sequence[int]],
        convexivity: int = 10,
    ) -> Shape:
        points_str = ",\n    ".join(f"[{x}, {y}, {z}]" for x, y, z in points)

        faces_strs = []
        for f in faces:
            faces_strs.append("[" + ", ".join(str(idx) for idx in f) + "]")
        faces_str = ",\n    ".join(faces_strs)
        return cls(
            "polyhedron(\n"
            "  [\n"
            f"    {points_str}\n"
            "  ],\n"
            "  [\n"
            f"    {faces_str}\n"
            "  ],\n"
            f"  {convexivity}\n"
            ")"
        )

    @classmethod
    def polyhedron_from_mesh(cls, mesh: Mesh, convexivity: int = 10) -> Shape:
        points = [(p.x, p.y, p.z) for p in mesh.points]
        faces = [tuple(f) for f in mesh.faces]
        return cls.polyhedron(
            points=points, faces=faces, convexivity=convexivity
        )

    @classmethod
    def project(cls, children: List[Shape]) -> Shape:
        return cls(f"projection(cut = false)", children)

    @classmethod
    def stl(cls, path: str, convexity: int = 10) -> Shape:
        # TODO: properly escape the path
        return cls(f'import("{path}", convexity={convexity})', [])

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


class PosAndNeg:
    """
    A helper class for tracking both a positive shape (to be unioned with
    something else) and a negative shape (to be removed from something else).

    This is mainly a convenience class to allow the same set of transformations
    to be applied to both, but then still access them individually afterwards.
    """

    def __init__(self, pos: Shape, neg: Shape) -> None:
        self.pos = pos
        self.neg = neg

    def mirror(self, x: float, y: float, z: float) -> Shape:
        return PosAndNeg(self.pos.mirror(x, y, z), self.neg.mirror(x, y, z))

    def translate(self, x: float, y: float, z: float) -> Shape:
        return PosAndNeg(
            self.pos.translate(x, y, z), self.neg.translate(x, y, z)
        )

    def ptranslate(self, point: Point) -> Shape:
        return PosAndNeg(
            self.pos.ptranslate(point), self.neg.ptranslate(point)
        )

    def rotate(self, x: float, y: float, z: float) -> Shape:
        return PosAndNeg(self.pos.rotate(x, y, z), self.neg.rotate(x, y, z))
