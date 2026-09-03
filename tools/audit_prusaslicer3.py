#!/usr/bin/env python3
"""Audit every PrusaSlicer 3.0 token project in the collection."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re
import subprocess
import sys
from zipfile import ZipFile
import xml.etree.ElementTree as ET


ROOT = Path("/Users/lukas/dev/projects/dnd-tokens")
SLICER = Path("/Applications/PrusaSlicer-3.0.0-alpha11.app/Contents/MacOS/PrusaSlicer")
CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
NS = {"m": CORE}


def expected_count(category: Path) -> int:
    data = json.loads((category / "manifest.json").read_text(encoding="utf-8"))
    if isinstance(data, list):
        return len(data)
    return len(data.get("items", data.get("tokens", [])))


def audit(category: Path) -> list[str]:
    errors: list[str] = []
    count = expected_count(category)
    originals = list((category / "3mf").glob("*-tokens.3mf"))
    outputs = list((category / "3mf").glob("*-tokens-prusaslicer-3.0.3mf"))
    if len(originals) != 1 or len(outputs) != 1:
        return [f"{category.name}: expected one production original and one production 3.0 file"]
    output = outputs[0]

    with ZipFile(output) as archive:
        names = set(archive.namelist())
        required = {
            "[Content_Types].xml",
            "_rels/.rels",
            "3D/3dmodel.model",
            "Metadata/PrusaSlicer3_project.json",
        }
        if not required.issubset(names):
            errors.append(f"{category.name}: incomplete package")
            return errors
        project = json.loads(archive.read("Metadata/PrusaSlicer3_project.json"))
        model = ET.fromstring(archive.read("3D/3dmodel.model"))

    objects = project.get("objects", [])
    containers = project.get("config_containers", [])
    if len(containers) != 1:
        errors.append(f"{category.name}: expected one printer configuration")
    else:
        hardware = containers[0].get("preset", {}).get("hw_config", {})
        if hardware.get("legacy_printer_model") != "COREONE_INDX8T" or hardware.get("tool_count") != 8:
            errors.append(f"{category.name}: project is not configured for CORE One INDX 8T")
    if len(objects) != count:
        errors.append(f"{category.name}: JSON objects {len(objects)} != {count}")
    for obj in objects:
        volumes = obj.get("volumes", [])
        extruders = [volume.get("volume_settings", {}).get("extruder") for volume in volumes]
        if len(volumes) != 2 or extruders != [2, 1]:
            errors.append(f"{category.name}: invalid volumes/extruders for {obj.get('name', obj.get('id'))}")
    items = model.findall("m:build/m:item", NS)
    if len(items) != count:
        errors.append(f"{category.name}: build items {len(items)} != {count}")

    result = subprocess.run(
        [str(SLICER), "--info", str(output)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    info = result.stdout
    if result.returncode:
        errors.append(f"{category.name}: PrusaSlicer returned {result.returncode}")
    if "manifold = no" in info or info.count("manifold = yes") != count:
        errors.append(f"{category.name}: manifold validation failed")
    for key, value in (("size_x", "25.000000"), ("size_y", "25.000000"), ("size_z", "1.000000")):
        values = re.findall(rf"{key} = ([0-9.]+)", info)
        if values != [value] * count:
            errors.append(f"{category.name}: unexpected {key} values")
    return errors


def main() -> None:
    categories = sorted(
        path.parent
        for path in ROOT.glob("*/manifest.json")
    )
    all_errors: list[str] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {pool.submit(audit, category): category for category in categories}
        for job in as_completed(jobs):
            all_errors.extend(job.result())
    print(f"PRUSASLICER3_AUDIT={'PASS' if not all_errors else 'FAIL'}")
    print(f"categories={len(categories)}")
    for error in sorted(all_errors):
        print(error)
    raise SystemExit(1 if all_errors else 0)


if __name__ == "__main__":
    main()
