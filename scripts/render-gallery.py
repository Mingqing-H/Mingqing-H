"""Compose the two-column gallery WebP from the individual artwork (Pillow)."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ASSETS = Path(__file__).resolve().parents[1] / "assets"
GALLERY = ASSETS / "gallery"
COLUMN_WIDTH = 610
GUTTER = 18
RADIUS = 14
COLUMNS = (
    (
        (ASSETS / "alpine-twilight.webp", 254, (.52, .56)),
        (GALLERY / "fern.webp", 590, (.56, .43)),
        (GALLERY / "paper.webp", 460, (.52, .13)),
    ),
    (
        (GALLERY / "architecture.webp", 452, (.52, .00)),
        (GALLERY / "jellyfish.webp", 570, (.50, .40)),
        (GALLERY / "city.webp", 282, (.55, .53)),
    ),
)


def render():
    heights = [sum(tile[1] for tile in col) + GUTTER * (len(col) - 1) for col in COLUMNS]
    assert len(set(heights)) == 1, "The two columns should finish flush"
    canvas = Image.new("RGBA", (COLUMN_WIDTH * 2 + GUTTER, heights[0]))
    for index, column in enumerate(COLUMNS):
        x, y = index * (COLUMN_WIDTH + GUTTER), 0
        for path, height, focus in column:
            with Image.open(path) as source:
                tile = ImageOps.fit(source.convert("RGB"), (COLUMN_WIDTH, height), Image.Resampling.LANCZOS, centering=focus)
            mask = Image.new("L", tile.size)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, COLUMN_WIDTH - 1, height - 1), RADIUS, fill=255)
            canvas.paste(tile, (x, y), mask)
            y += height + GUTTER
    target = GALLERY / "field-notes.webp"
    canvas.save(target, format="WEBP", quality=82, method=6)
    print(f"{target.name}: {canvas.width}x{canvas.height}, {target.stat().st_size:,} bytes")


if __name__ == "__main__":
    render()
