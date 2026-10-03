#!/usr/bin/env python3
"""Check every declared foreground/background text pairing."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def luminance(value: str) -> float:
    channels = []
    for channel in rgb(value):
        normalized = channel / 255
        channels.append(normalized / 12.92 if normalized <= 0.04045 else ((normalized + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def ratio(foreground: str, background: str) -> float:
    a, b = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def main() -> int:
    colors = json.loads((ROOT / "design" / "tokens.json").read_text(encoding="utf-8"))["color"]
    pairs = {
        "ink/bone": ("ink", "bone", 4.5),
        "ink-soft/bone": ("ink_soft", "bone", 4.5),
        "muted/bone": ("muted", "bone", 4.5),
        "metis-text/bone": ("metis_text", "bone", 4.5),
        "warning": ("warning_text", "warning_bg", 4.5),
        "danger": ("danger_text", "danger_bg", 4.5),
        "bone/ink": ("bone", "ink", 4.5),
        "success/bone": ("success_text", "bone", 4.5),
    }
    failed = []
    for name, (fg, bg, minimum) in pairs.items():
        value = ratio(colors[fg], colors[bg])
        print(f"{name} {value:.2f}:1 (min {minimum:.1f})")
        if value + 1e-9 < minimum:
            failed.append(name)
    if failed:
        print("CONTRAST FAIL " + ", ".join(failed))
        return 1
    print(f"CONTRAST OK pairs={len(pairs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
