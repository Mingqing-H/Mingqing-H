"""Build the static and animated chart from the signed-out GitHub calendar.

Run `python scripts/render-contributions.py` to refresh the snapshot. Use
`--html FILE` to render from a previously downloaded public calendar instead.
"""

import argparse
from datetime import date, timedelta
from html.parser import HTMLParser
from math import log2
from pathlib import Path
import re
from urllib.request import Request, urlopen


CALENDAR_URL = "https://github.com/users/Mingqing-H/contributions"
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "contribution-terrain.svg"
MOTION_OUTPUT = OUTPUT.with_name("contribution-terrain-motion.svg")
PALETTES = (
    ("#7C81CE", "#40477A", "#545B9B"),
    ("#999DE9", "#50578F", "#696FB0"),
    ("#BDC0F8", "#6763A2", "#857EBF"),
    ("#E6CDAB", "#84618F", "#A484AB"),
)


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.counts = {}
        self.tooltip = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and {"data-date", "data-level", "id"} <= attrs.keys():
            self.cells[attrs["id"]] = (
                date.fromisoformat(attrs["data-date"]), int(attrs["data-level"])
            )
        elif tag == "tool-tip":
            self.tooltip = attrs.get("for")

    def handle_data(self, data):
        if self.tooltip:
            match = re.match(r"\s*(No|[0-9,]+) contributions? on\b", data)
            if match:
                number = match[1]
                self.counts[self.tooltip] = 0 if number == "No" else int(number.replace(",", ""))

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self.tooltip = None


def extract_days(html):
    calendar = Calendar()
    calendar.feed(html)
    if not calendar.cells or not calendar.cells.keys() <= calendar.counts.keys():
        raise ValueError("GitHub did not return a complete public contribution calendar")
    days = sorted((day, calendar.counts[key], level) for key, (day, level) in calendar.cells.items())[-365:]
    if len(days) != 365 or any((b[0] - a[0]).days != 1 for a, b in zip(days, days[1:])):
        raise ValueError("The public calendar does not contain 365 consecutive days")
    if any(not 0 <= level <= 4 or (count == 0) != (level == 0) for _, count, level in days):
        raise ValueError("Contribution counts do not match the GitHub calendar levels")
    return days


def polygon(points):
    return "M" + "L".join(f"{x:g} {y:g}" for x, y in points) + "z"


def motion_layers(tops):
    outlines = "".join(tops)
    return f'''  <style>
    .tower {{ transform-box: fill-box; transform-origin: center bottom; animation: rise .66s cubic-bezier(.22, 1, .36, 1) var(--rise-delay) both; }}
    .glint {{ animation: sweep 15s linear 1.8s infinite both; }}
    @keyframes rise {{ from {{ transform: scaleY(0); opacity: 0; }} to {{ transform: scaleY(1); opacity: 1; }} }}
    @keyframes sweep {{ from {{ transform: translateX(-96px); }} 34%, to {{ transform: translateX(880px); }} }}
    @media (prefers-reduced-motion: reduce) {{ .tower {{ animation: none; }} .glint {{ display: none; }} }}
  </style>
  <defs>
    <linearGradient id="light">
      <stop stop-color="#FFF3D8" stop-opacity="0"/>
      <stop offset=".5" stop-color="#FFF3D8" stop-opacity=".7"/>
      <stop offset="1" stop-color="#FFF3D8" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="summits"><path d="{outlines}"/></clipPath>
  </defs>
''', '\n  <g clip-path="url(#summits)"><rect class="glint" width="96" height="372" fill="url(#light)"/></g>'


def render(days, *, animated=False):
    first, last = days[0][0], days[-1][0]
    sunday = first - timedelta(days=(first.weekday() + 1) % 7)
    total = sum(count for _, count, _ in days)
    active = sum(count > 0 for _, count, _ in days)
    peak = max(count for _, count, _ in days)
    start_week = next(((day - sunday).days // 7 for day, count, _ in days if count), 0)
    flat, towers, tops = [], [], []
    for day, count, level in days:
        week, weekday = divmod((day - sunday).days, 7)
        x, y = 112 + 13 * week - 8 * weekday, 158 + 2 * week + 5 * weekday
        a, b, c, d = (x, y), (x + 11, y + 1.7), (x + 4, y + 5.7), (x - 7, y + 4)
        flat.append(polygon((a, b, c, d)))
        if not count:
            continue
        # Log height keeps the busiest day from hiding the rest of the year.
        height = round(10 + 88 * log2(1 + count) / log2(1 + peak))
        at, bt, ct, dt = ((px, round(py - height, 1)) for px, py in (a, b, c, d))
        top, left, right = PALETTES[level - 1]
        summit = polygon((at, bt, ct, dt))
        shape = (f'<path fill="{left}" d="{polygon((d, c, ct, dt))}"/>'
                 f'<path fill="{right}" d="{polygon((c, b, bt, ct))}"/>'
                 f'<path fill="{top}" d="{summit}"/>')
        if animated:
            delay = (week - start_week) * 29 + weekday * 11
            shape = f'<g class="tower" style="--rise-delay:{delay}ms">{shape}</g>'
            tops.append(summit)
        towers.append((y, x, shape))
    chart = "\n  ".join(shape for _, _, shape in sorted(towers))
    grid = "".join(flat)
    motion_defs, motion_overlay = motion_layers(tops) if animated and tops else ("", "")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="880" height="372" viewBox="0 0 880 372" fill="none">
  <title>GitHub contribution terrain</title>
  <desc>{total} visible contributions across {active} active days from {first} to {last}. Each tile is one day, with logarithmic column height.</desc>
{motion_defs}  <rect x=".5" y=".5" width="879" height="371" rx="20" fill="#141827" stroke="#555C81"/>
  <path d="M54 101h772M54 312h772" stroke="#3A4262" stroke-dasharray="3 5"/>
  <g font-family="ui-monospace, Consolas, monospace">
    <text x="54" y="73" fill="#E9D4B3" font-size="26" font-weight="600">{total:,} contributions</text>
    <text x="826" y="73" fill="#BDC7EC" text-anchor="end" font-size="21">{active} active days</text>
    <text x="54" y="347" fill="#BDC7EC" font-size="20">{first}</text>
    <text x="826" y="347" fill="#BDC7EC" text-anchor="end" font-size="20">{last}</text>
  </g>
  <path d="{grid}" fill="#313953"/>
  {chart}{motion_overlay}
</svg>\n'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()
    if args.html:
        html = args.html.read_text(encoding="utf-8")
    else:
        request = Request(CALENDAR_URL, headers={"User-Agent": "MQ-FM-profile", "Accept-Language": "en"})
        with urlopen(request, timeout=20) as response:
            html = response.read().decode("utf-8")
    days = extract_days(html)
    OUTPUT.write_text(render(days), encoding="utf-8", newline="\n")
    MOTION_OUTPUT.write_text(render(days, animated=True), encoding="utf-8", newline="\n")
    print(f"{days[0][0]} to {days[-1][0]} · {sum(count for _, count, _ in days):,} contributions · "
          f"{OUTPUT.stat().st_size:,} bytes static / {MOTION_OUTPUT.stat().st_size:,} bytes animated")


if __name__ == "__main__":
    main()
