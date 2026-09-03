#!/usr/bin/env python3
"""Add a proven INDX 8T project configuration to a token 3MF."""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


CONFIG = "Metadata/Slic3r_PE.config"
WIPE_TOWER = "Metadata/Prusa_Slicer_wipe_tower_information.xml"


def package(source: Path, output: Path, profile_project: Path) -> None:
    with ZipFile(source) as original, ZipFile(profile_project) as profile:
        additions = {CONFIG: profile.read(CONFIG)}
        if WIPE_TOWER in profile.namelist():
            additions[WIPE_TOWER] = profile.read(WIPE_TOWER)
        output.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(output, "w", ZIP_DEFLATED) as result:
            for info in original.infolist():
                if info.filename not in additions:
                    result.writestr(info, original.read(info.filename))
            for name, payload in additions.items():
                result.writestr(name, payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--profile-project", type=Path, required=True)
    args = parser.parse_args()
    package(args.source.resolve(), args.output.resolve(), args.profile_project.resolve())
    print(args.output.resolve())


if __name__ == "__main__":
    main()
