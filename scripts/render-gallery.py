"""Render a static WebP and the matching SVG blinds animation (Pillow)."""

from base64 import b64encode
from math import ceil
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


def render_blinds(still, width, height):
    strips = []
    for col, tiles in enumerate(COLUMNS):
        x, y = col * (COLUMN_WIDTH + GUTTER), 0
        for row, (_, tile_height, _) in enumerate(tiles):
            count = ceil(tile_height / 64)
            for strip in range(count):
                top = y + tile_height * strip // count
                bottom = y + tile_height * (strip + 1) // count
                delay = 370 * col + 160 * row + 48 * strip
                strips.append(f'      <rect class="slat" x="{x}" y="{top}" width="{COLUMN_WIDTH}" '
                              f'height="{bottom - top}" style="animation-delay:{delay}ms"/>')
            y += tile_height + GUTTER

    clip = "\n".join(strips)
    image = b64encode(still.read_bytes()).decode("ascii")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <title>Field notes · Venetian blinds</title>
  <style>
    .slat {{ transform-box: fill-box; transform-origin: center top; animation: blinds 11s cubic-bezier(.22, 1, .36, 1) infinite both; }}
    @keyframes blinds {{
      0%, 6%, 96%, 100% {{ transform: scaleY(.04); }}
      24%, 80% {{ transform: scaleY(1); }}
    }}
    @media (prefers-reduced-motion: reduce) {{ .slat {{ animation: none; }} }}
  </style>
  <defs>
    <image id="gallery" width="{width}" height="{height}" href="data:image/webp;base64,{image}"/>
    <clipPath id="blinds" clipPathUnits="userSpaceOnUse">
{clip}
    </clipPath>
  </defs>
  <use href="#gallery" opacity=".12"/>
  <use href="#gallery" clip-path="url(#blinds)"/>
</svg>\n'''
    target = GALLERY / "field-notes-blinds.svg"
    target.write_text(svg, encoding="utf-8", newline="\n")
    print(f"{target.name}: {len(strips)} slats, {target.stat().st_size:,} bytes")


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
    render_blinds(target, canvas.width, canvas.height)


if __name__ == "__main__":
    render()
