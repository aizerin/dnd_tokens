#!/usr/bin/env python3
"""Center all token sets and assign tool 2/base + tool 1/inlay."""

from __future__ import annotations

import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from make_prusaslicer3_8t import centered_positions, build as build_ps3


ROOT = Path("/Users/lukas/dev/projects/dnd-tokens")
TEMPLATE = ROOT / "goblins/3mf/goblins-4-tokens-prusaslicer-3.0-8t-profile-cli-test.3mf"
CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
ET.register_namespace("", CORE)
NS = {"m": CORE}


def rewrite_archive(source: Path, replacements: dict[str, bytes], output: Path) -> None:
    with ZipFile(source) as original, ZipFile(output, "w", ZIP_DEFLATED) as result:
        for info in original.infolist():
            result.writestr(info.filename, replacements.get(info.filename, original.read(info.filename)))


def update_old_project(source: Path, output: Path) -> int:
    with ZipFile(source) as archive:
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
        config = ET.fromstring(archive.read("Metadata/Slic3r_PE_model.config"))

    items = model.findall(".//m:build/m:item", NS)
    objects = config.findall("object")
    if len(items) != len(objects) or not objects:
        raise ValueError(f"Object mismatch in {source}: {len(items)} placements, {len(objects)} configs")

    for item, (x, y) in zip(items, centered_positions(len(items))):
        item.set("transform", f"1 0 0 0 1 0 0 0 1 {x:g} {y:g} 0")

    for obj in objects:
        volumes = obj.findall("volume")
        if len(volumes) != 2:
            raise ValueError(f"Expected two volumes in {source}, object {obj.get('id')}")
        values = []
        for volume in volumes:
            matches = [m for m in volume.findall("metadata") if m.get("key") == "extruder"]
            if len(matches) != 1:
                raise ValueError(f"Missing volume tool in {source}, object {obj.get('id')}")
            values.append(matches[0].get("value"))
        if values not in (["4", "1"], ["2", "1"]):
            raise ValueError(f"Unexpected tools {values} in {source}, object {obj.get('id')}")
        [m for m in volumes[0].findall("metadata") if m.get("key") == "extruder"][0].set("value", "2")
        [m for m in volumes[1].findall("metadata") if m.get("key") == "extruder"][0].set("value", "1")

    replacements = {
        "3D/3dmodel.model": ET.tostring(model, encoding="utf-8", xml_declaration=True),
        "Metadata/Slic3r_PE_model.config": ET.tostring(config, encoding="utf-8", xml_declaration=True),
    }
    rewrite_archive(source, replacements, output)
    return len(objects)


def validate_old(path: Path, expected: int) -> None:
    with ZipFile(path) as archive:
        config = ET.fromstring(archive.read("Metadata/Slic3r_PE_model.config"))
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
    objects = config.findall("object")
    items = model.findall(".//m:build/m:item", NS)
    if len(objects) != expected or len(items) != expected:
        raise ValueError(f"Validation count failed for {path}")
    for obj in objects:
        tools = [
            next(m.get("value") for m in volume.findall("metadata") if m.get("key") == "extruder")
            for volume in obj.findall("volume")
        ]
        if tools != ["2", "1"]:
            raise ValueError(f"Validation tool assignment failed for {path}: {tools}")


def validate_new(path: Path, expected: int) -> None:
    with ZipFile(path) as archive:
        project = json.loads(archive.read("Metadata/PrusaSlicer3_project.json"))
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
    containers = project.get("config_containers", [])
    if len(containers) != 1:
        raise ValueError(f"Invalid printer configuration count in {path}")
    hardware = containers[0]["preset"]["hw_config"]
    if hardware.get("legacy_printer_model") != "COREONE_INDX8T" or hardware.get("tool_count") != 8:
        raise ValueError(f"Not an INDX 8T project: {path}")
    objects = project.get("objects", [])
    items = model.findall(".//m:build/m:item", NS)
    if len(objects) != expected or len(items) != expected:
        raise ValueError(f"Validation count failed for {path}")
    for obj in objects:
        tools = [v.get("volume_settings", {}).get("extruder") for v in obj.get("volumes", [])]
        if tools != [2, 1]:
            raise ValueError(f"Validation tool assignment failed for {path}: {tools}")


def main() -> None:
    old_paths = sorted(ROOT.glob("*/3mf/*-tokens.3mf"))
    new_paths = sorted(ROOT.glob("*/3mf/*-tokens-prusaslicer-3.0.3mf"))
    if len(old_paths) != len(new_paths):
        raise ValueError(f"Project count mismatch: {len(old_paths)} old, {len(new_paths)} new")

    old_categories = {p.parent.parent.name for p in old_paths}
    new_categories = {p.parent.parent.name for p in new_paths}
    if old_categories != new_categories:
        raise ValueError("Old/new category sets do not match")

    with tempfile.TemporaryDirectory(prefix="dnd-token-3mf-") as temporary:
        staging = Path(temporary)
        staged: list[tuple[Path, Path]] = []
        counts: dict[str, int] = {}

        for source in old_paths:
            output = staging / f"old-{source.parent.parent.name}.3mf"
            count = update_old_project(source, output)
            validate_old(output, count)
            counts[source.parent.parent.name] = count
            staged.append((output, source))

        for source in new_paths:
            output = staging / f"new-{source.parent.parent.name}.3mf"
            build_ps3(source, output, TEMPLATE, base_tool=2)
            validate_new(output, counts[source.parent.parent.name])
            staged.append((output, source))

        for output, destination in staged:
            output.replace(destination)

    print(f"UPDATED_OLD={len(old_paths)}")
    print(f"UPDATED_NEW={len(new_paths)}")
    print(f"OBJECTS={sum(counts.values())}")


if __name__ == "__main__":
    main()
