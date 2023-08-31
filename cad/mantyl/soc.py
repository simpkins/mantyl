#!/usr/bin/python3 -tt
#
# Copyright (c) 2023, Adam Simpkins
#

from __future__ import annotations

from .numpad import NumpadSection

from typing import List, Tuple

from bpycad import blender_util
from bpycad import cad

import bpy


def esp32s3_wroom_devkit_c() -> bpy.types.Object:
    # Dimensions datasheet:
    # https://dl.espressif.com/dl/DXF_ESP32-S3-DevKitC-1_V1_20210312CB.pdf
    #
    # Length = 70mm (including antenna)
    # Width = 25.5mm
    l = 63
    w = 25.5
    board_d = 1.57
    obj = blender_util.cube(w, l, board_d, "esp32s3_wroom_devkit_c")

    antenna_l = 7
    antenna_w = 18
    overlap_l = 2
    antenna = blender_util.cube(antenna_w, antenna_l + overlap_l, board_d)
    with blender_util.TransformContext(antenna) as ctx:
        ctx.translate(0, (l + antenna_l - overlap_l) * 0.5, 0)

    blender_util.union(obj, antenna)

    return obj


def esp32s3_wroom_1() -> bpy.types.Object:
    l = 25.5
    w = 18
    pcb_d = 0.8
    antenna_len = 6
    obj = blender_util.cube(w, l, pcb_d, "ESP32-S3-WROOM-1")
    with blender_util.TransformContext(obj) as ctx:
        ctx.translate(0, antenna_len * 0.5, pcb_d * 0.5)

    mod_w = 15.8
    mod_l = 17.6
    mod_d = 3.1 - pcb_d
    d_overlap = pcb_d * 0.5
    module = blender_util.cube(mod_w, mod_l, mod_d + d_overlap)
    with blender_util.TransformContext(module) as ctx:
        ctx.translate(0, 0, pcb_d + (mod_d - d_overlap) * 0.5)

    blender_util.union(obj, module)
    return obj


def esp32s3_wroom_1u() -> bpy.types.Object:
    l = 19.2
    w = 18
    pcb_d = 0.8
    obj = blender_util.cube(w, l, pcb_d, "ESP32-S3-WROOM-1")

    mod_w = 15.65
    mod_l = 17.5
    mod_d = 3.2 - pcb_d
    d_overlap = pcb_d * 0.5
    module = blender_util.cube(mod_w, mod_l, mod_d + d_overlap)
    with blender_util.TransformContext(module) as ctx:
        ctx.translate(0, 0, pcb_d + (mod_d - d_overlap) * 0.5)

    blender_util.union(obj, module)
    return obj


class NumpadPcb:
    pcb_thickness = 1.6

    def __init__(self) -> None:
        self.mesh = self._gen_mesh()
        self.object = self._gen_object()

    def _gen_mesh(self) -> cad.Mesh:
        mesh = cad.Mesh()
        perim_xy: List[Tuple[float, float]] = [
            (16, -57),
            (53, -16),
            (53, 33),
            (44, 59),
            (-44, 59),
            (-47, 50),
            (-47, -22),
            (-16, -57),
        ]
        perim: List[Tuple[cad.MeshPoint, cad.MeshPoint]] = []
        for x, y in perim_xy:
            t = mesh.add_xyz(x, y, self.pcb_thickness)
            b = mesh.add_xyz(x, y, 0)
            perim.append((t, b))

        top_face_indices = [t.index for t, b in reversed(perim)]
        # pyre-fixme[6]: we are letting blender deal with a polygon face here,
        #     but we did not declare typing in cad.Mesh to allow polygon faces
        mesh.faces.append(top_face_indices)
        bottom_face_indices = [b.index for t, b in perim]
        # pyre-fixme[6]: we are letting blender deal with a polygon face here,
        #     but we did not declare typing in cad.Mesh to allow polygon faces
        mesh.faces.append(bottom_face_indices)

        for idx in range(len(perim)):
            mesh.add_quad(
                perim[idx - 1][0], perim[idx][0], perim[idx][1], perim[idx - 1][1]
            )

        return mesh

    def _gen_object(self) -> bpy.types.Object:
        bmesh = blender_util.blender_mesh(f"pcb_mesh", self.mesh)
        obj = blender_util.new_mesh_obj("numpad_pcb", bmesh)

        self._add_esp32(obj)
        self._add_keys(obj)
        self._add_screw_holes(obj)
        self._add_headers(obj)
        self._add_usb(obj)
        self._add_display(obj)
        self._add_status_leds(obj)

        return obj

    def _add_esp32(self, obj: bpy.types.Object) -> None:
        esp32 = esp32s3_wroom_1()
        esp32_x = -37.25
        esp32_y = 2.5
        with blender_util.TransformContext(esp32) as ctx:
            ctx.rotate(90, "Z")
            ctx.translate(esp32_x, esp32_y, self.pcb_thickness)
        blender_util.union(obj, esp32)

    def _add_keys(self, obj: bpy.types.Object) -> None:
        key_positions = [
            (28.5, -7),  # KP1
            (9.5, -7),  # KP2
            (-9.5, -7),  # KP3
            (28.5, 12),  # KP4
            (9.5, 12),  # KP5
            (-9.5, 12),  # KP6
            (28.5, 31),  # KP7
            (9.5, 31),  # KP8
            (-9.5, 31),  # KP9

            (28.5, 50),  # KP_Extra
            (9.5, 50),  # KP_Slash
            (-9.5, 50),  # KP_Star
            (-28.5, 50),  # KP_Minus

            (19.0, -26),  # KP0
            (-9.5, -26),  # KP_Dot

            (-28.5, 21.5),  # KP_Plus
            (-28.5, -16.5),  # KP_Enter
        ]
        d = 6.75
        for x, y in key_positions:
            c = blender_util.range_cube((-d, d), (-d, d), (-10, 10))
            with blender_util.TransformContext(c) as ctx:
                ctx.translate(x, y, 0.0)
            blender_util.difference(obj, c)

    def _add_screw_holes(self, obj: bpy.types.Object) -> None:
        screw_positions = [
            (-26, -40),
            (26, -40),
            (41.5, 53.5),
            (-41.5, 53.5),
        ]
        d = 6.75
        for x, y in screw_positions:
            hole = blender_util.cylinder(r=1.35, h=10)
            with blender_util.TransformContext(hole) as ctx:
                ctx.translate(x, y, 0.0)
            blender_util.difference(obj, hole)

    def _add_headers(self, obj: bpy.types.Object) -> None:
        main_header_positions = [(-41.3, 31.85), (43.05, 29.355)]

        h = 8.9
        for x, y in main_header_positions:
            header = blender_util.cube(8.9, 33.02, h)
            with blender_util.TransformContext(header) as ctx:
                ctx.translate(x, y, self.pcb_thickness + (h * 0.5))
            blender_util.union(obj, header)

        hat_h = 8.5
        hat_header = blender_util.cube(5, 8.02, hat_h)
        with blender_util.TransformContext(hat_header) as ctx:
            ctx.translate(19.1, -41.3, self.pcb_thickness + (hat_h * 0.5))
        blender_util.union(obj, hat_header)

    def _add_usb(self, obj: bpy.types.Object) -> None:
        main_pos = (-21.6, 4.24)
        uart_pos = (42.67, -16.7)
        l = 8.4
        w = 3.16
        h = 10.0

        h_offset = (h * 0.5) + self.pcb_thickness

        # Main USB header
        main_hdr = blender_util.cube(l, w, h)
        with blender_util.TransformContext(main_hdr) as ctx:
            ctx.translate(main_pos[0], main_pos[1], h_offset)
        blender_util.union(obj, main_hdr)

        # UART USB header
        uart_hdr = blender_util.cube(w, l, h)
        with blender_util.TransformContext(uart_hdr) as ctx:
            ctx.translate(uart_pos[0], uart_pos[1], h_offset)
        blender_util.union(obj, uart_hdr)

    def _add_status_leds(self, obj: bpy.types.Object) -> None:
        y = -52.0
        x_list = (-12, -4, 4, 12)

        for x in x_list:
            hole = blender_util.cube(3.4, 3.0, 10)
            with blender_util.TransformContext(hole) as ctx:
                ctx.translate(x, y, 0.0)
            blender_util.difference(obj, hole)

    def _add_display(self, obj: bpy.types.Object) -> None:
        # https://datasheet.lcsc.com/lcsc/2109031030_Newvisio-N091-2832TSWFG02-H14_C2890599.pdf
        # The length of the display glass is 30mm
        # This is split into a main area on the left of 26.6mm, and 3.4mm on
        # the right for the connector.
        #
        # I have centered the entire glass area, rather than centering the
        # active area.

        y = -41.75
        h = 4
        disp = blender_util.cube(30, 11.6, h)
        with blender_util.TransformContext(disp) as ctx:
            ctx.translate(0, y, (-h / 2) + .3)

        blender_util.difference(obj, disp)


def numpad_pcb() -> bpy.types.Object:
    return NumpadPcb().object
