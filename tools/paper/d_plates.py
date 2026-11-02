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
# The bank shares one lighting and framing, so plates with the same LOOK read as repeats (11-02, M4; 11-02 debt: a cracked
# clay thumbnail next to a cracked stone lead, a folded-paper slab next to a concrete block). The families group by look,
# not by material name: a page takes one plate per look before it reuses one.
FAMILY = {'acero-junta': 'metal', 'metal-arista': 'metal', 'hierro-fundido': 'metal',
          'papel-pila': 'capas', 'pizarra-capas': 'capas',
          'papel-pliegue': 'bloque', 'concreto-bloque': 'bloque', 'piedra-escalon': 'bloque', 'marmol-corte': 'bloque',
          'piedra-grieta': 'grieta', 'arcilla-seca': 'grieta',
          'madera-veta': 'madera'}


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
    families = {FAMILY[n] for n in taken}
    for fresh_family in (True, False):
        for step in range(len(PLATES)):
            name = PLATES[(start + step) % len(PLATES)]
            if name in taken or (wide and name in THUMB_ONLY) or (fresh_family and FAMILY[name] in families):
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
