#!/usr/bin/env python3
"""Create the standard metadata files for one token category."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("category_dir", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--items", required=True, help="JSON list with slug, name, role, request")
    parser.add_argument("--shared", required=True)
    args = parser.parse_args()

    items = json.loads(args.items)
    args.category_dir.mkdir(parents=True, exist_ok=True)
    (args.category_dir / "source").mkdir(exist_ok=True)

    manifest = [{k: item[k] for k in ("slug", "name", "role")} for item in items]
    (args.category_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    names = ", ".join(item["name"] for item in items[:-1])
    if len(items) > 1:
        names += f", and {items[-1]['name']}"
    else:
        names = items[0]["name"]
    readme = f"""# {args.title}

{len(items)} double-sided, flush, two-colour FDM tokens: {names}.

- Diameter: 25 mm; total thickness: 1.0 mm
- Colour inlay: 0.4 mm on each face; centre core: 0.2 mm
- Base and centre core: extruder 2; artwork and perimeter ring: extruder 1
- Bottom artwork: mirrored; surfaces: flush
- Direct trace with no dilation, erosion, hole filling, island removal, or line thickening
"""
    (args.category_dir / "README.md").write_text(readme, encoding="utf-8")

    lines = [
        f"# {args.title} — Image generation prompts",
        "",
        "Generated with the built-in ImageGen tool.",
        "",
        "## Shared direction",
        "",
        args.shared.strip(),
        "",
        "## Creature requests",
        "",
    ]
    lines.extend(f"- **{item['name']}:** {item['request']}" for item in items)
    lines.append("")
    (args.category_dir / "PROMPTS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
