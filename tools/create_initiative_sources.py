#!/usr/bin/env python3
"""Create clean, high-contrast numeral sources for initiative tokens."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("/Users/lukas/dev/projects/dnd-tokens")
OUTPUT = ROOT / "initiative-markers" / "source"
FONT = Path("/System/Library/Fonts/Supplemental/Herculanum.ttf")
CANVAS = 1024
MAX_WIDTH = 700
MAX_HEIGHT = 600


def fitted_font(text: str) -> ImageFont.FreeTypeFont:
    low, high = 16, 900
    probe = Image.new("L", (CANVAS, CANVAS), 255)
    draw = ImageDraw.Draw(probe)
    while low < high:
        size = (low + high + 1) // 2
        font = ImageFont.truetype(str(FONT), size)
        box = draw.textbbox((0, 0), text, font=font, stroke_width=0)
        if box[2] - box[0] <= MAX_WIDTH and box[3] - box[1] <= MAX_HEIGHT:
            low = size
        else:
            high = size - 1
    return ImageFont.truetype(str(FONT), low)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for number in range(1, 21):
        text = str(number)
        image = Image.new("L", (CANVAS, CANVAS), 255)
        draw = ImageDraw.Draw(image)
        font = fitted_font(text)
        box = draw.textbbox((0, 0), text, font=font)
        width, height = box[2] - box[0], box[3] - box[1]
        x = (CANVAS - width) / 2 - box[0]
        y = (CANVAS - height) / 2 - box[1]
        draw.text((x, y), text, font=font, fill=0)
        image.convert("RGB").save(OUTPUT / f"initiative-{number:02d}.png")


if __name__ == "__main__":
    main()
