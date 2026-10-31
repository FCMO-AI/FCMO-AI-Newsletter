"""D / Libro de evidencias: material photographs (stone, metal, paper, concrete) as the story image.

Deterministic per story (hash of id + first topic); within one page, different stories take different plates,
so neighbours never repeat while the lead keeps the same plate in the hero and in the rank table.
The plates are text-free GPT-Image photographs conditioned on the approved R4 (see d_plates_prepare.py).
"""
import hashlib
from html import escape

from .routes import href

PLATES = ('piedra-grieta', 'acero-junta', 'papel-pila', 'concreto-bloque', 'marmol-corte', 'madera-veta',
          'pizarra-capas', 'metal-arista', 'piedra-escalon', 'papel-pliegue', 'hierro-fundido', 'arcilla-seca')
# d-arcilla-seca is the warmest: it is only used as a thumbnail, never as a wide plate.
THUMB_ONLY = {'arcilla-seca'}


def _index(story):
    key = f'{story.get("id", "")}|{(story.get("topics") or [""])[0]}'
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:4], 'big')


def choose(story, seen=None, wide=False):
    """seen: dict story_id -> plate shared by every call on one page (mutated)."""
    seen = seen if seen is not None else {}
    sid = story.get('id', '')
    if sid in seen and (not wide or seen[sid] not in THUMB_ONLY):
        return seen[sid]
    start = _index(story)
    taken = set(seen.values())
    for step in range(len(PLATES)):
        name = PLATES[(start + step) % len(PLATES)]
        if name in taken or (wide and name in THUMB_ONLY):
            continue
        seen[sid] = name
        return name
    name = PLATES[start % len(PLATES)]
    seen[sid] = name
    return name


def html(story, ratio, strings, base, seen=None, thumb=False):
    name = choose(story, seen, wide=not thumb)
    src = href(base, f'assets/img/d-plates/d-{name}{"-thumb" if thumb else ""}.webp')
    alt = strings['plate']['alt_decorative']
    dims = 'width="360" height="225"' if thumb else 'width="1800" height="600"'
    loading = 'loading="lazy"' if thumb else 'fetchpriority="high"'
    return (f'<div class="plate" data-ratio="{escape(ratio)}" data-plate="{name}" role="img" aria-label="{escape(alt)}">'
            f'<img src="{escape(src)}" alt="" {dims} {loading} decoding="async"></div>')
