#!/usr/bin/env python3
"""Render one compact showcase image containing every token in the collection."""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from render_category_preview import BACKGROUND, FONT, INK, token_image


ROOT = Path("/Users/lukas/dev/projects/dnd-tokens")
OUTPUT = ROOT / "previews/all-tokens-preview.png"

CANVAS_WIDTH = 3300
COLUMNS = 20
CELL = 160
TOKEN = 138
TOP = 228
BOTTOM = 92


def centered_text(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    y: float,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
) -> None:
    bounds = draw.textbbox((0, 0), text, font=font)
    draw.text((center_x - (bounds[2] - bounds[0]) / 2, y), text, font=font, fill=fill)


def entries() -> list[tuple[Path, dict]]:
    result: list[tuple[Path, dict]] = []
    for manifest in sorted(ROOT.glob("*/manifest.json")):
        category = manifest.parent
        data = json.loads(manifest.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("items", data.get("tokens", []))
        result.extend((category, item) for item in items)
    return result


def main() -> None:
    tokens = entries()
    rows = math.ceil(len(tokens) / COLUMNS)
    canvas_height = TOP + rows * CELL + BOTTOM
    canvas = Image.new("RGB", (CANVAS_WIDTH, canvas_height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)

    title_font = ImageFont.truetype(FONT, 76)
    subtitle_font = ImageFont.truetype(FONT, 31)
    footer_font = ImageFont.truetype(FONT, 24)

    centered_text(draw, CANVAS_WIDTH / 2, 42, "FANTASY TOKEN COLLECTION", title_font, INK)
    centered_text(
        draw,
        CANVAS_WIDTH / 2,
        139,
        f"{len(tokens)} TOKENS  •  77 SETS  •  PRUSA CORE ONE INDX",
        subtitle_font,
        (63, 64, 66),
    )
    draw.rounded_rectangle((46, 199, CANVAS_WIDTH - 46, 207), radius=4, fill=(196, 191, 182))

    grid_width = COLUMNS * CELL
    x_origin = (CANVAS_WIDTH - grid_width) // 2
    for index, (category, entry) in enumerate(tokens):
        row, column = divmod(index, COLUMNS)
        items_in_row = min(COLUMNS, len(tokens) - row * COLUMNS)
        row_width = items_in_row * CELL
        row_origin = (CANVAS_WIDTH - row_width) // 2
        x = row_origin + column * CELL + (CELL - TOKEN) // 2
        y = TOP + row * CELL + (CELL - TOKEN) // 2

        rendered = token_image(category / "source" / f"{entry['slug']}.png")
        rendered = rendered.resize((TOKEN, TOKEN), Image.Resampling.LANCZOS)

        shadow = Image.new("RGBA", (TOKEN + 20, TOKEN + 20), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.ellipse((7, 7, TOKEN + 6, TOKEN + 6), fill=(0, 0, 0, 92))
        shadow = shadow.filter(ImageFilter.GaussianBlur(7))
        canvas.paste(shadow, (x - 3, y + 1), shadow)
        canvas.paste(rendered, (x, y), rendered)

    footer_y = TOP + rows * CELL + 29
    centered_text(
        draw,
        CANVAS_WIDTH / 2,
        footer_y,
        "DOUBLE-SIDED  •  TWO-COLOUR  •  25 MM  •  FDM READY",
        footer_font,
        (83, 83, 84),
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT, optimize=True)
    print(f"{OUTPUT} ({canvas.width} × {canvas.height}, {len(tokens)} tokens)")


if __name__ == "__main__":
    main()
