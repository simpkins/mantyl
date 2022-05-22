#!/usr/bin/python3 -tt
#
# Copyright (c) 2022, Adam Simpkins
#

from __future__ import annotations

from typing import Optional

from cad import Shape

keyswitch_width: float = 14.4
keyswitch_height: float = 14.4
plate_thickness: float = 4.0

keywell_wall_width = 1.5
web_thickness = 3.5
post_size = 0.1

mount_width = keyswitch_width + (2 * keywell_wall_width)
mount_height = keyswitch_height + (2 * keywell_wall_width)


def dsa_cap(include_base: bool = False) -> Shape:
    # Signature Plastics DSA keycap specs:
    # https://www.solutionsinplastic.com/wp-content/uploads/2017/05/DSAFamily.pdf
    #
    # Keycap dimensions:
    # 1x1: .725" square at base (18.415mm), .5" square at top
    #      In practice mine are closer to 18mm square at the base
    #
    # 1x1: 18mm x 18mm
    # 1x1.25: 18mm x 23mm
    # 1x1.5: 18mm x 28mm
    # 1x1.75: 18mm x 32.5mm
    # 1x2: 18mm x 37.5mm

    lower_dim = 18.415  # .725"
    upper_dim = 12.7  # 0.5"
    # The datasheet claims the height is 0.291" (7.4mm)
    # However, for the keycaps I have the height appears to be closer
    # to about 7.85mm.  The taper inwards only starts about 1mm up.
    height = 7.85
    lower_height = 1
    upper_height = height - lower_height

    # The offset from the key plate to the bottom of the key cap,
    # when the key switch is not pressed.
    switch_height = 6.5

    scale = upper_dim / lower_dim

    lower = Shape.cube(lower_dim, lower_dim, lower_height).translate(
        0, 0, lower_height / 2.0
    )
    upper = (
        Shape.square(lower_dim, lower_dim)
        .extrude_linear(upper_height, scale=scale)
        .translate(0, 0, (upper_height / 2.0) + lower_height)
    )
    parts = [lower, upper]

    # The base is a solid cube beneath the keycap, just to indicate the amount
    # of space that will be taken up by the edge of the cap when the key is depressed.
    # This helps detect if there will be collisions with another key along the
    # key's path of travel.
    if include_base:
        base = Shape.cube(
            lower_dim, lower_dim, switch_height - 0.01
        ).translate(0, 0, 0.01 - switch_height / 2)
        parts.append(base)

    # This is the DSA keycap, with the lower edge at Z-offset 0
    cap = Shape.union(parts)

    # Translate the cap upwards to take into account the plate thickness, and
    # the key switch offset.
    z_offset = plate_thickness + switch_height
    return cap.translate(0, 0, z_offset)


def dsa_cap(ratio=1.0, include_base: bool = False) -> Shape:
    """
    Create an approximation of a 1xN DSA keycap.

    The ratio argument controls the length dimension (N).
    DSA keycaps are commonly available in 1x1, 1.25, 1.5, 1.75, and 1x2

    Signature Plastics DSA keycap specs:
    https://www.solutionsinplastic.com/wp-content/uploads/2017/05/DSAFamily.pdf

    In practice the keycaps I have have roughly the following measurements at
    the base:
    - 1x1: 18mm x 18mm
    - 1x1.25: 18mm x 23mm
    - 1x1.5: 18mm x 28mm
    - 1x1.75: 18mm x 32.5mm
    - 1x2: 18mm x 37.5mm
    """
    # The datasheet claims the height is 0.291" (7.4mm)
    # However, for the keycaps I have the height appears to be closer
    # to about 7.85mm.  The taper inwards only starts about 1mm up.
    height = 7.85

    lower_w = 18.415
    lower_d = lower_w * ratio
    # The height of the lower portion before it starts to taper in
    lower_h = 1

    upper_w = 12.7
    upper_d = lower_d - (lower_w - upper_w)
    # upper_h doesn't really matter, just needs to be a number less than height
    upper_h = 1

    lower = Shape.cube(lower_w, lower_d, lower_h).translate(
        0, 0, lower_h * 0.5
    )
    top = Shape.cube(upper_w, upper_d, upper_h).translate(
        0, 0, height - (upper_h * 0.5)
    )
    main = Shape.hull([lower, top])
    parts = [lower, top, main]

    # The offset from the key plate to the bottom of the key cap,
    # when the key switch is not pressed.
    switch_height = 6.5

    # The base is a solid cube beneath the keycap, just to indicate the amount
    # of space that will be taken up by the edge of the cap when the key is depressed.
    # This helps detect if there will be collisions with another key along the
    # key's path of travel.
    if include_base:
        base = Shape.cube(lower_w, lower_d, switch_height - 0.01).translate(
            0, 0, 0.01 - switch_height / 2
        )
        parts.append(base)

    # Translate the cap upwards to take into account the plate thickness, and
    # the key switch offset.
    z_offset = plate_thickness + switch_height
    return Shape.union(parts).translate(0, 0, z_offset)


def cherry_mx() -> Shape:
    # TODO
    pass


def single_plate(
    show_cap: Optional[bool] = False, loose: bool = False
) -> Shape:
    """
    If loose is True, print the hole a bit wider so the key switch is a little
    loose.  This helps printing prototypes that are not intended to be the
    final design, so it is easier to get key switches in and out for testing.
    """
    nub_width = 2.75

    if not loose:
        hole_width = keyswitch_width
        hole_height = keyswitch_height
        wall_width = keywell_wall_width
    else:
        gap = 0.40
        hole_width = keyswitch_width + gap
        hole_height = keyswitch_height + gap
        wall_width = keywell_wall_width - (gap / 2.0)

    top_wall = Shape.cube(
        hole_width + (wall_width * 2), wall_width, plate_thickness
    ).translate(0, (hole_height + wall_width) / 2, plate_thickness / 2)

    left_wall = Shape.cube(
        wall_width, hole_height + (wall_width * 2), plate_thickness
    ).translate((hole_width + wall_width) / 2, 0, plate_thickness / 2)

    parts = [top_wall, left_wall]

    if not loose:
        nub_cube = Shape.cube(
            wall_width, nub_width, plate_thickness
        ).translate((wall_width + hole_width) / 2, 0, plate_thickness / 2)
        nub_cylinder = (
            Shape.cylinder(h=nub_width, r=1, fn=30)
            .rotate(90, 0, 0)
            .translate(hole_width / 2, 0, 1)
        )
        nub = Shape.hull([nub_cylinder, nub_cube])
        parts.append(nub)

    half = Shape.union(parts)
    other_half = half.mirror(1, 0, 0).mirror(0, 1, 0)
    parts = [half, other_half]

    if show_cap:
        parts.append(
            dsa_cap()
            .color("#c0c0c0", alpha=0.8)
            .translate(0, 0, plate_thickness / 2 + 5)
        )

    return Shape.union(parts)


def corner_post(size: float = post_size) -> Shape:
    return Shape.cube(size, size, web_thickness).translate(
        0, 0, plate_thickness - (web_thickness / 2)
    )


def corner_tl(
    x: float = 0.0, y: float = 0.0, size: float = post_size
) -> Shape:
    return corner_post(size=size).translate(
        ((size - mount_width) / 2) + x,
        ((mount_height - size) / 2) + y,
        0,
    )


def corner_tr(
    x: float = 0.0, y: float = 0.0, size: float = post_size
) -> Shape:
    return corner_post(size=size).translate(
        ((mount_width - size) / 2) + x,
        ((mount_height - size) / 2) + y,
        0,
    )


def corner_bl(x: float = 0.0, y: float = 0.0, size: float = post_size) -> Shape:
    return corner_post(size=size).translate(
        ((size - mount_width) / 2) + x,
        ((size - mount_height) / 2) + y,
        0,
    )


def corner_br(x: float = 0.0, y: float = 0.0, size: float = post_size) -> Shape:
    return corner_post(size=size).translate(
        ((mount_width - size) / 2) + x,
        ((size - mount_height) / 2) + y,
        0,
    )
