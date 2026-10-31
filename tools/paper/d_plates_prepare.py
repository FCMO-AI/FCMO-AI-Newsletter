#!/usr/bin/env python3
"""Optimise the D material plates (GPT-Image, conditioned on the approved R4) into site-src/assets/img/d-plates.

Usage: d_plates_prepare.py SRC_DIR [DEST_DIR]. Trims letterbox bands (near-white or near-black full rows),
writes <name>.webp (wide, <=200 KB) and <name>-thumb.webp (16:10 crop, <=40 KB).
"""
import sys
from pathlib import Path
from PIL import Image

WIDE_W, THUMB = 1800, (360, 225)


def trim(im):
    g = im.convert('L')
    keep = [y for y in range(g.height) if sum(g.crop((0, y, g.width, y + 1)).getdata()) / g.width < 235]  # letterbox rows are almost white
    return im.crop((0, keep[0], im.width, keep[-1] + 1))


def save_under(im, path, limit):
    for q in range(82, 30, -4):
        im.save(path, 'WEBP', quality=q, method=6)
        if path.stat().st_size <= limit:
            return q
    raise SystemExit(f'{path} over {limit}')


def main():
    src = Path(sys.argv[1]); dest = Path(sys.argv[2] if len(sys.argv) > 2 else 'site-src/assets/img/d-plates')
    dest.mkdir(parents=True, exist_ok=True)
    for f in sorted(src.glob('d-*.png')):
        im = trim(Image.open(f).convert('RGB'))
        wide = im.resize((WIDE_W, round(im.height * WIDE_W / im.width)), Image.LANCZOS)
        q = save_under(wide, dest / (f.stem + '.webp'), 200_000)
        # thumbnail: centre 16:10 crop
        h = round(im.height); w = min(im.width, round(h * 1.6))
        if w == im.width: h = round(w / 1.6)
        l, t = (im.width - w) // 2, (im.height - h) // 2
        th = im.crop((l, t, l + w, t + h)).resize(THUMB, Image.LANCZOS)
        save_under(th, dest / (f.stem + '-thumb.webp'), 40_000)
        print(f.stem, wide.size, q)


if __name__ == '__main__':
    main()
