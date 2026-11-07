"""Generate the static MQ FM asset for readers who prefer reduced motion."""

from pathlib import Path
import re


assets = Path(__file__).resolve().parents[1] / "assets"
animated = (assets / "mq-fm.svg").read_text(encoding="utf-8")
still, removed = re.subn(r"^  <style>\n.*?^  </style>\n", "", animated, flags=re.M | re.S)
if removed != 1:
    raise ValueError("Expected exactly one stylesheet in the animated banner")
(assets / "mq-fm-still.svg").write_text(still, encoding="utf-8", newline="\n")
