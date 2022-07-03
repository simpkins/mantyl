#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

import bpy

from . import cad
from . import blender_util
from .keyboard import Keyboard


class WristRest:
    def __init__(self, kbd: Keyboard) -> None:
        self.depth = 70.0
        self.back_z_drop = 14
        self.mesh = cad.Mesh()
        self.kbd = kbd

        self.gen_top_face()
        self.gen_thumb_connect()

    def gen(self) -> bpy.types.Object:
        return blender_util.new_mesh_obj("wrist_rest", self.mesh)

    def gen_top_face(self) -> None:
        fl = self.kbd.front_wall[1].out1
        fr = self.kbd.front_wall[-1].out1
        # Define the plane for the top face
        top_plane = (
            fl.point,
            fr.point,
            cad.Point(fr.x, fr.y - self.depth, fr.z - self.back_z_drop),
        )

        def top_z(x: float, y: float) -> float:
            line = (cad.Point(x, y, 0.0), cad.Point(x, y, 1.0))
            intersect = cad.intersect_line_and_plane(line, top_plane)
            return intersect.z

        def top_point(x: float, y: float) -> cad.MeshPoint:
            return self.mesh.add_xyz(x, y, top_z(x, y))

        self.top_tl = top_point(fl.x, fl.y)
        self.top_tr = top_point(fr.x + 40, fr.y)
        self.top_br = top_point(fr.x + 40, fr.y - self.depth)
        self.top_bl = top_point(fl.x, fl.y - self.depth)

        self.mesh.add_quad(self.top_tl, self.top_tr, self.top_br, self.top_bl)

    def gen_thumb_connect(self) -> None:
        corner_tr = self.mesh.add_point(self.kbd.thumb_br_connect.point)
        corner_tl = self.mesh.add_point(self.kbd.thumb_wall[0].out1.point)
        self.mesh.add_tri(self.top_tl, self.top_bl, corner_tr)
        self.mesh.add_tri(corner_tl, corner_tr, self.top_bl)


def right(kbd: Keyboard, mirror: bool) -> bpy.types.Object:
    return WristRest(kbd).gen()


def test() -> bpy.types.Object:
    kbd = Keyboard()
    kbd.gen_mesh()
    return right(kbd, mirror=False)
