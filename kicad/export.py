#!/usr/bin/python3 -tt
#
# Copyright (c) 2023, Adam Simpkins
#

"""
Command-line script to generate JLCPCB production files from a Kicad project.
"""

from __future__ import annotations

import argparse
import csv
import logging
import math
import os
import re
import shutil
import subprocess
import sys
import xml.dom.minidom
import yaml
import zipfile
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional, Set, Union, Tuple

logger: logging.Logger = logging.getLogger("export")


@dataclass
class Component:
    ref: str
    value: str
    footprint: str
    properties: Dict[str, str]


class BOM:
    def __init__(self, components: List[Component]) -> None:
        self.components = components
        self.by_part: Dict[str, List[Component]] = {}
        self.by_ref: Dict[str, Component] = {}

        # Build the dictionary by ref
        for comp in self.components:
            if not comp.ref:
                raise Exception("component present with no ref")
            if comp.ref in self.by_ref:
                raise Exception(
                    f"multiple components present with ref {comp.ref}"
                )
            self.by_ref[comp.ref] = comp

    def process_part_numbers(self, mapper: JlcPcbMapper) -> None:
        # Build the dictionary grouping components together by part number
        for component in self.components:
            jlc_info = mapper.get_jlc_part(component)
            part = jlc_info.part
            if not part:
                raise Exception(
                    f"no LCSC part number specified for {component.ref}: "
                    "specify one in the mapping file or in an 'LCSC Part #' "
                    "field on the symbol"
                )
            comp_list = self.by_part.setdefault(part, [])
            comp_list.append(component)

        # Warn about components that share the same part number but different
        # values.  This likely indicates an incorrect part number if there are
        # capacitors/resistors/etc with mismatched values but the same part
        # number.
        #
        # We ignore this check for switches and headers that may use the value
        # simply as a label.
        for part, components in self.by_part.items():
            values = set([comp.value for comp in components])
            if len(values) == 1:
                continue

            # Ignore this warning for switches and headers, where the value
            # might be used simply as a label
            for comp in components:
                if not re.match("^(SW|J)[0-9]+$", comp.ref):
                    break
            else:
                # All components were switches or headers
                continue

            refs = ",".join(sorted(comp.ref for comp in components))
            logger.warning(
                f"mismatched component values: {refs} all "
                f"have the same part number ({part}), but different values:"
            )
            for comp in components:
                logger.warning(f"  {comp.ref}: {comp.value}")

    @classmethod
    def load(cls, kicad_cli: str, sch: Path) -> BOM:
        components = cls._read_bom(kicad_cli, sch)
        return cls(components)

    @classmethod
    def _read_bom(cls, kicad_cli: str, sch: Path) -> List[Component]:
        # Kicad 7.0 only has a "python-bom" export command.
        # Newer development versions also have a "bom" export that allows
        # exporting the BOM in a CSV format, with a custom list of fields.
        #
        # For now we use python-bom since it is available in stable released
        # versions of Kicad.
        with TemporaryDirectory(prefix="kicad_bom") as tmpdir:
            out_path = Path(tmpdir) / "kicad_bom.xml"
            cmd = [
                kicad_cli,
                "sch",
                "export",
                "python-bom",
                "-o",
                str(out_path),
                str(sch),
            ]
            subprocess.run(cmd, check=True)
            return cls._parse_bom(out_path)

    @classmethod
    def _parse_bom(cls, path: Path) -> List[Component]:
        with path.open("rb") as f:
            doc = xml.dom.minidom.parse(f)

        for child in doc.childNodes:
            if child.nodeName == "export":
                export_node = child
                break
        else:
            raise Exception("unable to find export node in BOM")

        for child in export_node.childNodes:
            if child.nodeName == "components":
                components_node = child
                break
        else:
            raise Exception("unable to find components node in BOM")

        bom: List[Component] = []
        for child in components_node.childNodes:
            if child.nodeName != "comp":
                continue

            bom.append(cls._parse_component(child))

        return bom

    @classmethod
    def _parse_component(cls, node: xml.dom.minidom.Element) -> Component:
        props: Dict[str, str] = {}
        ref_attr = node.attributes.get("ref")
        assert ref_attr is not None, "BOM component present without a ref"

        value: str = ""
        footprint: str = ""

        for child in node.childNodes:
            if child.nodeName == "value":
                assert (
                    len(child.childNodes) == 1
                ), "component value has unexpected number of children"
                value = child.childNodes[0].data
            elif child.nodeName == "footprint":
                assert (
                    len(child.childNodes) == 1
                ), "component footprint has unexpected number of children"
                footprint = child.childNodes[0].data
            elif child.nodeName == "property":
                name_attr = child.attributes.get("name")
                value_attr = child.attributes.get("value")
                assert (
                    name_attr is not None
                ), "BOM component property present without a name"
                assert (
                    value_attr is not None
                ), "BOM component property present without a value"
                props[name_attr.value] = value_attr.value

        return Component(
            ref=ref_attr.value,
            value=value,
            footprint=footprint,
            properties=props,
        )


@dataclass
class JlcPcbFootprint:
    footprint: Optional[str] = None
    rotation: Optional[float] = None  # In degrees
    center_x: Optional[float] = None
    center_y: Optional[float] = None

    @classmethod
    def load(
        self, path: Path, identifier: str, data: Dict[str, Any]
    ) -> JlcPcbFootprint:
        fp: Optional[str] = None
        rot: Optional[float] = None
        cx: Optional[float] = None
        cy: Optional[float] = None
        for name, value in data.items():
            if name == "jlc_footprint":
                fp = value
            elif name == "rotation":
                assert isinstance(
                    value, (int, float)
                ), f"{path}:{identifier}: rotation must be a float"
                rot = float(value)
            elif name == "center_x":
                assert isinstance(
                    value, (int, float)
                ), f"{path}:{identifier}: center_x must be a float"
                cx = float(value)
            elif name == "center_y":
                assert isinstance(
                    value, (int, float)
                ), f"{path}:{identifier}: center_y must be a float"
                cy = float(value)
            else:
                logger.warning(
                    f"{path}: unexpected field in footprint mapping info for "
                    f"{identifier}: {name}"
                )

        return JlcPcbFootprint(
            footprint=fp, rotation=rot, center_x=cx, center_y=cy
        )


@dataclass
class JlcPcbPart:
    part: str
    footprint: str
    rotation: float = 0.0  # In degrees
    center_x: float = 0.0
    center_y: float = 0.0


@dataclass
class JlcPcbSymbolInfo:
    part: Optional[str]
    footprint: JlcPcbFootprint

    @classmethod
    def load(
        self, path: Path, ref: str, data: Union[str, Dict[str, Any]]
    ) -> JlcPcbSymbolInfo:
        if isinstance(data, str):
            return JlcPcbSymbolInfo(part=data, footprint=JlcPcbFootprint())

        part: Optional[str] = None
        footprint_info: Dict[str, Any] = {}
        for name, value in data.items():
            if name == "part":
                part = data.get("part", None)
            elif name in ("footprint", "rotation", "center_x", "center_y"):
                footprint_info[name] = value
            else:
                logger.warning(
                    f"{path}: unexpected field in mapping info for component "
                    f"{ref}: {name}"
                )

        if footprint_info:
            footprint = JlcPcbFootprint.load(path, ref, footprint_info)
        else:
            footprint = JlcPcbFootprint()
        return JlcPcbSymbolInfo(part=part, footprint=footprint)


class JlcPcbMapper:
    """
    This class stores info about how to map KiCad symbols and footprints to
    JLCPCB parts and footprints.

    It's data can be stored to a YAML file so that users can manually edit the
    mapping configuration.
    """

    def __init__(self) -> None:
        self.by_ref: Dict[str, JlcPcbSymbolInfo] = {}
        self.by_part: Dict[str, JlcPcbFootprint] = {}
        self.footprint_rules: List[Tuple[re.Pattern, JlcPcbFootprint]] = []

    def get_jlc_part(self, component: Component) -> JlcPcbPart:
        part: Optional[str] = None
        footprint: Optional[str] = None
        rotation: Optional[float] = None
        center_x: Optional[float] = None
        center_y: Optional[float] = None

        def update_values(fp_info: JlcPcbFootprint) -> None:
            nonlocal footprint, rotation, center_x, center_y
            if footprint is None:
                footprint = fp_info.footprint
            if rotation is None:
                rotation = fp_info.rotation
            if center_x is None:
                center_x = fp_info.center_x
            if center_y is None:
                center_y = fp_info.center_y

        # Look for data first in the self.by_ref dictionary.
        # If data was explicitly specified for this component, it takes
        # precedence over everything else.
        sym_info = self.by_ref.get(component.ref, None)
        if sym_info is not None:
            part = sym_info.part
            update_values(sym_info.footprint)
        if part is None:
            part = component.properties.get("LCSC Part #", None)

        # Look for data first in the self.by_part dictionary.
        # If we have information for this specific LCSC part, it takes
        # precedence over the more generic footprint info.
        if part is not None:
            part_info = self.by_part.get(part, None)
            if part_info is not None:
                update_values(part_info)
        else:
            # If we couldn't find a part name, return it as the empty string
            # rather than None
            part = ""

        # Check data based on the KiCad footprint name.
        for pattern, fp_info in self.footprint_rules:
            match = pattern.search(component.footprint)
            if match is not None:
                if footprint is None and fp_info.footprint is not None:
                    # The footprint field is a template that needs expansion
                    footprint = self._expand_footprint_template(
                        fp_info.footprint, match
                    )

                update_values(fp_info)
                break

        # Some final defaults
        if footprint is None:
            # KiCad's footprint name is in the form LIBRARY:FOOTPRINT
            # Remove the library part.
            footprint_name_parts = component.footprint.split(":", 1)
            footprint = footprint_name_parts[-1]
        if rotation is None:
            rotation = 0.0
        if center_x is None:
            center_x = 0.0
        if center_y is None:
            center_y = 0.0

        return JlcPcbPart(
            part=part,
            footprint=footprint,
            rotation=rotation,
            center_x=center_x,
            center_y=center_y,
        )

    def _expand_footprint_template(
        self, template: str, match: re.Match
    ) -> str:
        idx = 0
        out_parts: List[str] = []
        while True:
            next_idx = template.find("{", idx)
            if next_idx == -1:
                out_parts.append(template[idx:])
                break

            out_parts.append(template[idx:next_idx])
            idx = next_idx + 1
            if idx == len(template):
                raise Exception(
                    "invalid footprint name template: unterminated '{': "
                    f"{template!r}"
                )
            if template[idx] == "{":
                out_parts.append("{")
                idx += 1
                continue

            next_idx = template.find("}", idx)
            if idx == -1:
                raise Exception(
                    "invalid footprint name template: unterminated '{': "
                    f"{template!r}"
                )
            key = template[idx:next_idx]
            idx = next_idx + 1

            try:
                key = int(key)
            except ValueError:
                # may be a string named group
                pass

            try:
                value = match.group(key)
            except IndexError:
                raise Exception(
                    "invalid footprint name template: "
                    f"match group {key!r} does not exist"
                )
            out_parts.append(value)

        return "".join(out_parts)

    @classmethod
    def load(cls, path: Path, data: Dict[str, Any]) -> JlcPcbMapper:
        mapper = cls()

        for name, value in data.items():
            if name == "footprint_rules":
                if value is not None:
                    for entry in value:
                        pattern, fp_info = cls._load_footprint_rule(
                            path, entry
                        )
                        mapper.footprint_rules.append((pattern, fp_info))
            elif name == "components":
                if value is not None:
                    for ref, data in value.items():
                        sym_info = JlcPcbSymbolInfo.load(path, ref, data)
                        mapper.by_ref[ref] = sym_info
            elif name == "parts":
                if value is not None:
                    for part_id, data in value.items():
                        fp_info = JlcPcbFootprint.load(path, part_id, data)
                        mapper.by_part[part_id] = fp_info
            else:
                logger.warning(
                    f"{path}: unexpected field in JLCPCB mapping file: {name}"
                )

        return mapper

    @classmethod
    def _load_footprint_rule(
        cls, path: Path, data: Dict[str, Any]
    ) -> Tuple[re.Pattern, JlcPcbFootprint]:
        pattern_str: Optional[str] = None
        pattern: Optional[re.Pattern] = None
        fp_data: Dict[str, Any] = {}
        for name, value in data.items():
            if name == "pattern":
                pattern_str = value
                pattern = re.compile(value)
            else:
                fp_data[name] = value

        if pattern is None:
            raise Exception(
                f"{path}: invalid footprint rule present with no pattern.  "
                f"Other rule fields are {data}"
            )
        assert pattern_str is not None

        fp_info = JlcPcbFootprint.load(path, pattern_str, fp_data)
        return (pattern, fp_info)


class Exporter:
    kicad_cli: str = "kicad-cli"

    def __init__(
        self,
        project: Path,
        mapping_file: Path,
        kicad_cli: Optional[str] = None,
    ) -> None:
        self.project_name: str = project.name
        self.pcb: Path = project / f"{project.name}.kicad_pcb"
        self.sch: Path = project / f"{project.name}.kicad_sch"
        self._bom: Optional[BOM] = None

        self.mapping_file = mapping_file
        self.mapper: JlcPcbMapper = self._load_mapper(mapping_file)

        if kicad_cli is not None:
            self.kicad_cli = kicad_cli

    def get_bom(self) -> BOM:
        bom = self._bom
        if bom is None:
            bom = BOM.load(self.kicad_cli, self.sch)
            self._bom = bom
        return bom

    def _load_mapper(self, path: Path) -> JlcPcbMapper:
        try:
            in_file = path.open("r")
        except FileNotFoundError:
            return JlcPcbMapper()

        with in_file:
            data = yaml.load(in_file, Loader=yaml.SafeLoader)
        return JlcPcbMapper.load(path, data)

    def export_all(self, output_dir: Path, force_update: bool = False) -> None:
        self.prepare_export(output_dir, remove_existing=force_update)
        self.export_pcb(output_dir, force_update=force_update)
        self.export_bom(output_dir)
        self.export_cpl(output_dir)
        logger.info(
            f"Successfully exported {self.project_name} to {output_dir}"
        )

    def prepare_export(self, output_dir: Path, remove_existing: bool) -> None:
        self.get_bom().process_part_numbers(self.mapper)
        try:
            output_dir.mkdir()
        except FileExistsError:
            if remove_existing:
                shutil.rmtree(output_dir)
                output_dir.mkdir()

    def export_pcb(self, output_dir: Path, force_update: bool = False) -> None:
        gerber_dir = output_dir / "gerber"
        drill_dir = output_dir / "drill"
        zip_path = output_dir / f"{self.project_name}.zip"

        if not force_update and self._is_zip_file_newer(zip_path, self.pcb):
            # Generating the PCB files is slightly slow compared to other
            # steps.  Avoid regenerating it if the zip file already exists and
            # is newer than the PCB file.
            logger.info(
                "Gerber and Drill file are up-to-date; skipping re-generation"
            )
            return

        if gerber_dir.is_dir():
            shutil.rmtree(gerber_dir)
        if drill_dir.is_dir():
            shutil.rmtree(drill_dir)
        zip_path.unlink(missing_ok=True)

        # Export the gerber and drill files
        self._export_gerbers(gerber_dir)
        self._export_drill_files(drill_dir)
        self._create_zipfile(zip_path, gerber_dir, drill_dir)
        logger.info(f"Generated PCB files at {zip_path}")

    def _is_zip_file_newer(self, zip_path: Path, pcb_path: Path) -> bool:
        try:
            zip_st = zip_path.stat()
        except FileNotFoundError:
            return False

        try:
            pcb_st = pcb_path.stat()
        except FileNotFoundError:
            # This is unexpected.  Gerber and drill generation will probably
            # fail, but just return False here for now and let it fail later.
            return False

        return zip_st.st_mtime > pcb_st.st_mtime

    def _export_gerbers(self, gerber_dir: Path) -> None:
        logger.info(f"Exporting gerbers...")
        gerber_dir.mkdir()

        # Run the gerber export command
        # We don't know how many layers there are, so we just let it export all
        # layers to a temporary directory, and then afterwards we keep only the
        # layers we want.
        with TemporaryDirectory(dir=gerber_dir) as tmpdir_str:
            tmpdir = Path(tmpdir_str)
            cmd = [
                self.kicad_cli,
                "pcb",
                "export",
                "gerbers",
                "--subtract-soldermask",
                "-o",
                tmpdir_str,
                str(self.pcb),
            ]
            subprocess.run(cmd, check=True)

            prefix = f"{self.pcb.stem}-"
            with os.scandir(tmpdir) as scan:
                for entry in scan:
                    name_parts = entry.name.rsplit(".", 1)
                    if len(name_parts) != 2:
                        raise Exception(
                            f"unexpected gerber output file: {entry.name}"
                        )
                    stem, ext = name_parts
                    if not entry.name.startswith(prefix):
                        raise Exception(
                            f"unexpected gerber output file: {entry.name}"
                        )
                    name = stem[len(prefix) :]
                    keep = self._should_keep_gerber(name, ext)
                    if keep:
                        (tmpdir / entry.name).rename(gerber_dir / entry.name)

    def _should_keep_gerber(self, name: str, ext: str) -> bool:
        include_extensions: Set[str] = {
            "gtl",  # Top copper layer
            "gto",  # Top silk layer
            "gtp",  # Top paste layer
            "gts",  # Top mask layer
            "gbl",  # Bottom copper layer
            "gbo",  # Bottom silk layer
            "gbp",  # Bottom paste layer
            "gbs",  # Bottom mask layer
        }
        exclude_extensions: Set[str] = {
            "gta",  # Top Adhesive
            "gba",  # Bottom Adhesive
            "gbrjob",  # Job file
        }

        if ext in include_extensions:
            return True
        if ext in exclude_extensions:
            return False

        def is_int(value: str) -> bool:
            try:
                int(value)
                return True
            except ValueError:
                return False

        # Inner copper layers: # g1, g2, g3, ...
        if ext.startswith("g") and is_int(ext[1:]):
            return True
        # Mechanical layers (e.g., edge cuts): # gm1, gm2, ...
        if ext.startswith("gm") and is_int(ext[2:]):
            return True

        # In general we don't need other layers
        # Most other layers just end in "gbr"
        # The other layers are typically User_N, User_EcoN, F_Fab, B_Fab,
        # F_Courtyard, B_Courtyard
        return False

    def _export_drill_files(self, drill_dir: Path) -> None:
        logger.info(f"Exporting drill files...")
        drill_dir.mkdir()

        # Note: JLCPCB also recommends the older (G85) method of emitting oval
        # holes, rather than Kicad's newer "recommended" way of routing with a
        # G00 command.
        #
        # kicad-cli 7.0 does not currently have a way to control this setting,
        # but fortunately it defaults to the behavior we want.
        #
        # https://gitlab.com/kicad/code/kicad/-/merge_requests/1697
        # is a merge request to add a --excellon-oval-format option
        # to control this behavior.
        cmd = [
            self.kicad_cli,
            "pcb",
            "export",
            "drill",
            "--format",
            "excellon",
            "--drill-origin",
            "absolute",
            "--excellon-separate-th",
            "--excellon-units",
            "mm",
            "--excellon-zeros-format",
            "decimal",
            "--generate-map",
            "--map-format",
            "gerberx2",
            "-o",
            # kicad-cli 7.0 requires that the output path ends in a slash.
            # https://gitlab.com/kicad/code/kicad/-/issues/14438
            f"{drill_dir}/",
            str(self.pcb),
        ]
        subprocess.run(cmd, check=True)

    def _create_zipfile(
        self, zip_path: Path, gerber_dir: Path, drill_dir: Path
    ) -> None:
        logger.info(f"Zipping gerber and drill files...")
        with zipfile.ZipFile(zip_path, "x", zipfile.ZIP_DEFLATED) as zf:
            for path in (gerber_dir, drill_dir):
                with os.scandir(path) as scan:
                    for entry in scan:
                        entry_path = path / entry.name
                        zf.write(entry_path, entry.name)

    def export_bom(self, output_dir: Path) -> None:
        path = output_dir / f"BOM-{self.project_name}.csv"
        bom = self.get_bom()

        dialect = "unix"
        header = ["Comment", "Designator", "Footprint", "LCSC"]
        with path.open("w", newline="") as out_file:
            writer = csv.writer(out_file, dialect=dialect)
            writer.writerow(header)

            for part, components in sorted(bom.by_part.items()):
                # We get the JLCPCB info for just the first component in the
                # list.  We only need the footprint name, and since they all
                # share the same JLCPCB part number, JLCPCB should only know
                # about one footprint for this part.
                jlc_info = self.mapper.get_jlc_part(components[0])
                comment = components[0].value
                refs = ",".join(sorted(comp.ref for comp in components))
                row = [comment, refs, jlc_info.footprint, part]
                writer.writerow(row)

        logger.info(f"Generated BOM file at {path}")

    def export_cpl(self, output_dir: Path) -> None:
        kicad_pos = output_dir / f"kicad_pos.csv"
        cmd = [
            self.kicad_cli,
            "pcb",
            "export",
            "pos",
            "--format",
            "csv",
            "--units",
            "mm",
            "-o",
            str(kicad_pos),
            str(self.pcb),
        ]
        subprocess.run(cmd, check=True)

        try:
            self._process_kicad_pos(kicad_pos, output_dir)
        finally:
            kicad_pos.unlink()

    def _process_kicad_pos(self, kicad_pos: Path, output_dir: Path) -> None:
        # Remove any old CPL files that already exist in the output directory
        for side in "top", "bottom":
            self._cpl_path(output_dir, side).unlink(missing_ok=True)

        rows_by_side: Dict[str, List[List[str]]] = {}
        kicad_header = ["Ref", "Val", "Package", "PosX", "PosY", "Rot", "Side"]
        with kicad_pos.open("r", newline="") as in_file:
            seen_header = False
            for row in csv.reader(in_file):
                if not seen_header:
                    seen_header = True
                    assert (
                        row == kicad_header
                    ), "Unexpected position CSV format"
                    continue

                ref, value, footprint, pos_x, pos_y, rot, side = row
                side_rows = rows_by_side.setdefault(side, [])
                side_rows.append(row)

        jlcpcb_header = [
            "Designator",
            "Val",
            "Package",
            "Mid X",
            "Mid Y",
            "Rotation",
            "Layer",
        ]
        dialect = "unix"
        bom = self.get_bom()
        for side, rows in rows_by_side.items():
            jlcpcb_cpl = self._cpl_path(output_dir, side)
            with jlcpcb_cpl.open("w", newline="") as out_file:
                writer = csv.writer(out_file, dialect=dialect)
                writer.writerow(jlcpcb_header)

                for row in rows:
                    jlc_row = self._adjust_pos_row(row, bom)
                    writer.writerow(jlc_row)

            logger.info(f"Generated {side} CPL file at {jlcpcb_cpl}")

    def _cpl_path(self, output_dir: Path, side: str) -> Path:
        return output_dir / f"CPL-{side}.csv"

    def _adjust_pos_row(self, row: List[str], bom: BOM) -> List[str]:
        ref, value, footprint, pos_x_str, pos_y_str, rot_str, side = row
        pos_x = float(pos_x_str)
        pos_y = float(pos_y_str)
        rot = float(rot_str)

        comp = bom.by_ref[ref]
        jlc = self.mapper.get_jlc_part(comp)

        # If the JLC footprint midpoint is not located at the KiCad footprint
        # origin, we need to adjust the position.
        #
        # Note that the Y axis adjustment is a little confusing:
        # KiCad's default Y axis is inverted, with positive Y increasing
        # towards the bottom of the sheet.  We treat the
        # jlc.footprint.center_y value in this axis system.  However, the CPL
        # file coordinates are normal, with Y values getting more negative
        # towards the bottom off the sheet.  Therefore we negate center_y here
        # to convert from KiCad's coordinate system to the CPL coordinates.
        off_x = jlc.center_x
        off_y = -jlc.center_y
        if (off_x, off_y) != (0.0, 0.0):
            # The JLC center position applies to the KiCad footprint in its
            # original orientation.  If the KiCad footprint is rotated,
            # we need to rotate the JLC center offset as well.
            rot_rad = math.radians(rot)
            sin = math.sin(rot_rad)
            cos = math.cos(rot_rad)
            rotated_x = off_x * cos - off_y * sin
            rotated_y = off_x * sin + off_y * cos

            pos_x += rotated_x
            pos_y += rotated_y

        # If the JLC footprint is rotated compared to the KiCad footprint,
        # we need to apply the rotation.
        if jlc.rotation != 0.0:
            rot = (rot + jlc.rotation) % 360.0

        def fmt_float(value: float) -> str:
            return str(value)

        return [
            ref,
            value,
            jlc.footprint,
            fmt_float(pos_x),
            fmt_float(pos_y),
            fmt_float(rot),
            side,
        ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--kicad-cli",
        metavar="PATH",
        help="The path to the kicad-cli program.",
    )
    ap.add_argument(
        "--mapping-file",
        metavar="PATH",
        help="The path to the file with information on how to map KiCad "
        "components and footprints to JLCPCB parts and footprints.",
    )
    ap.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="Forcibly regenerate output even if it already appears to be "
        "up-to-date.",
    )
    ap.add_argument(
        "project", metavar="PROJECT", help="The path to the project directory."
    )
    args = ap.parse_args()

    log_format = "%(asctime)s: %(message)s"
    logging.basicConfig(
        stream=sys.stderr, level=logging.INFO, format=log_format
    )

    project_dir = Path(args.project)
    if args.mapping_file is not None:
        mapping_file = Path(args.mapping_file)
    else:
        mapping_file = project_dir / f"{project_dir.name}.jlcpcb.yaml"

    exporter = Exporter(project_dir, mapping_file, kicad_cli=args.kicad_cli)
    output_dir = project_dir / "production"
    exporter.export_all(output_dir, force_update=args.force)


if __name__ == "__main__":
    main()
