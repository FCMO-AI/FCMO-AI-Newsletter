#!/usr/bin/env python3
"""Deterministic procedural SVG plates for stories (no text nodes, no logos, no people).

Contract (design direction, image system):

    plate(story_id, topic_ids, ratio, locale=None) -> {"svg": str, "alt": {locale: str}, "motif": str}

* ``ratio`` is one of ``"16:10"`` (cards), ``"16:9"`` (wide) or ``"og"`` (1200x630).
  The viewBox matches the slot so layout shift stays at zero.
* The output depends only on ``story_id``, the motif and ``ratio``: the same input
  always yields the same bytes.
* Ink and bone, plus ONE ember element that marks the object of the plate.
* The motif comes from the story's real topics (``MOTIF_TOPICS``). When no topic
  matches, the neutral motif is used and the alt text says "Decorative plate".
  The alt never claims anything about the story's content.
* ``variant=1`` swaps the two circular motifs (monitoring, neutral) for a non-circular drawing, so a page
  can show rings once; the alt and ``data-motif`` stay the same. The caller picks it by slot, so it is deterministic.
* ``alt`` holds one sentence per UI locale, read from ``i18n/ui``. When ``locale`` is
  given the SVG carries ``role="img"`` and that locale's ``aria-label``; otherwise
  it is ``aria-hidden`` and the caller puts the alt on its own ``<img>``/figure.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

INK = "#0D0D0F"
INK2 = "#17171B"
BONE = "#F2EFE8"
EMBER = "#F05A28"

SLOTS = {"16:10": (800, 500), "16:9": (800, 450), "og": (1200, 630)}
LOCALES = ("en", "es-419", "zh-Hans")

MOTIFS = ("agents", "monitoring", "security", "reasoning", "voice", "neutral")

# Motif <-> topic table. A topic id (a hyphenated slug) maps to a motif when one of its
# words starts with one of the stems below. Order is the tie-break priority.
MOTIF_TOPICS: dict[str, tuple[str, ...]] = {
    "security": ("secur", "vulnerab", "cyber", "exploit", "attack", "jailbreak", "adversar", "malware",
                 "privacy", "redteam", "red", "backdoor", "poison", "cve", "threat", "injection", "sandbox"),
    "voice": ("voice", "speech", "audio", "voxtral", "transcri", "asr", "tts", "spoken", "acoustic", "music",
              "podcast", "wake", "dubbing"),
    "monitoring": ("monitor", "evaluat", "benchmark", "audit", "oversight", "observab", "measurement",
                   "calibrat", "interpretab", "probe", "probing", "verification", "testing", "assess", "metric",
                   "reliab", "transparen", "disclos", "alignment"),
    "reasoning": ("reason", "chain", "thought", "cot", "logic", "proof", "theorem", "mathemat", "math",
                  "planning", "deliberat", "inferential", "puzzle", "arc", "deduct", "induct"),
    "agents": ("agent", "agents", "agentic", "orchestrat", "multiagent", "harness", "toolcall", "tool",
               "workflow", "autonom", "delegat", "copilot", "assistant", "swarm", "mcp"),
}
PRIORITY = tuple(MOTIF_TOPICS)  # security, voice, monitoring, reasoning, agents

_ALT_CACHE: dict[str, dict] = {}


def _ui(locale: str) -> dict:
    if locale not in _ALT_CACHE:
        path = ROOT / "i18n" / "ui" / f"{locale}.json"
        _ALT_CACHE[locale] = json.loads(path.read_text(encoding="utf-8"))["strings"]["plate"]
    return _ALT_CACHE[locale]


def choose_motif(topic_ids) -> str:
    """Pick the motif from real topics; earlier topics weigh more. ``neutral`` if nothing matches."""
    scores = {m: 0.0 for m in PRIORITY}
    for position, topic in enumerate(topic_ids or ()):
        words = [w for w in str(topic).lower().replace("_", "-").split("-") if w]
        weight = 1.0 / (1.0 + 0.35 * position)
        for motif in PRIORITY:
            stems = MOTIF_TOPICS[motif]
            if any(w.startswith(s) if len(s) > 4 else w == s for w in words for s in stems):
                scores[motif] += weight
    # "agents" is the generic motif: any specific motif (security, voice, ...) outranks it.
    specific = [m for m in PRIORITY if m != "agents" and scores[m] > 0]
    if specific:
        return max(specific, key=lambda m: (scores[m], -PRIORITY.index(m)))
    return "agents" if scores["agents"] > 0 else "neutral"


def alt_texts(motif: str) -> dict[str, str]:
    out = {}
    for locale in LOCALES:
        ui = _ui(locale)
        if motif == "neutral":
            out[locale] = ui["alt_decorative"]
        else:
            out[locale] = ui["alt_motif"].format(motif=ui[f"motif_{motif}"])
    return out


def _rng(story_id: str, motif: str) -> random.Random:
    digest = hashlib.sha256(f"plate:{motif}:{story_id}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _n(value: float) -> str:
    text = f"{value:.1f}"
    return text[:-2] if text.endswith(".0") else text


def _bar(x: float, y: float, w: float) -> str:
    return f"M{_n(x)} {_n(y)}h{_n(w)}"


def _frame(w: int, h: int) -> str:
    """Hairline inset frame and corner ticks: the 'plate' register marks."""
    i, t = 18, 14
    d = []
    for cx, cy, sx, sy in ((i, i, 1, 1), (w - i, i, -1, 1), (i, h - i, 1, -1), (w - i, h - i, -1, -1)):
        d.append(f"M{cx} {cy + sy * t}V{cy}H{cx + sx * t}")
    return f'<path d="{"".join(d)}" fill="none" stroke="{BONE}" stroke-opacity=".28" stroke-width="1.5"/>'


def _base(w: int, h: int, rnd: random.Random) -> str:
    # one large soft form so the field is not a flat rectangle; no ids, so a page can repeat a plate
    cx, cy = rnd.uniform(.2, .8) * w, rnd.uniform(.2, .8) * h
    r = max(w, h) * rnd.uniform(.55, .8)
    return (f'<rect width="{w}" height="{h}" fill="{INK}"/>'
            f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}" fill="{INK2}"/>'
            f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r * .62)}" fill="{INK2}" stroke="{BONE}" stroke-opacity=".04" stroke-width="2"/>')


def _agents(w: int, h: int, rnd: random.Random) -> str:
    rows = 10 if h > 480 else 9
    pitch = h / (rows + 1)
    th = pitch * .38
    groups = {.07: [], .13: [], .22: []}
    fork_row = rnd.randint(3, rows - 3)
    fx = rnd.uniform(.38, .52) * w
    for i in range(rows):
        y = pitch * (i + 1)
        x = -rnd.uniform(0, 80)
        while x < w:
            seg = rnd.uniform(.04, .2) * w
            gap = rnd.uniform(.012, .035) * w
            if i in (fork_row, fork_row + 2) and x + seg > fx - 6 and x < w * .86:
                x += seg + gap
                continue
            groups[rnd.choice(tuple(groups))].append(_bar(x, y, seg))
            x += seg + gap
    out = "".join(f'<path d="{"".join(v)}" stroke="{BONE}" stroke-opacity="{k}" stroke-width="{_n(th)}"/>'
                  for k, v in groups.items() if v)
    y0 = pitch * (fork_row + 1)
    step = pitch * 2
    x2 = fx + w * rnd.uniform(.1, .16)
    ember_sw = th * 1.15
    path = f"M-10 {_n(y0)}H{_n(fx)}H{_n(x2)}V{_n(y0 + step)}H{_n(w + 10)}"
    ghost = f"M{_n(fx)} {_n(y0)}H{_n(w * .8)}"
    out += (f'<path d="{ghost}" stroke="{BONE}" stroke-opacity=".55" stroke-width="{_n(th * .35)}" stroke-dasharray="2 9" stroke-linecap="round"/>'
            f'<path d="{path}" fill="none" stroke="{EMBER}" stroke-width="{_n(ember_sw)}" stroke-linejoin="round"/>'
            f'<circle cx="{_n(fx)}" cy="{_n(y0)}" r="{_n(ember_sw * 1.35)}" fill="{EMBER}"/>'
            f'<circle cx="{_n(fx)}" cy="{_n(y0)}" r="{_n(ember_sw * .5)}" fill="{INK}"/>'
            f'<circle cx="{_n(x2)}" cy="{_n(y0 + step)}" r="{_n(ember_sw * .8)}" fill="{INK}" stroke="{EMBER}" stroke-width="{_n(ember_sw * .3)}"/>')
    return out


def _monitoring(w: int, h: int, rnd: random.Random) -> str:
    cx = w * rnd.uniform(.56, .7)
    cy = h * rnd.uniform(.42, .58)
    step = h * .075
    out = []
    for i in range(1, 11):
        r = step * i
        out.append(f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}" fill="none" stroke="{BONE}" '
                   f'stroke-opacity="{round(.07 + .02 * i, 2)}" stroke-width="{2 if i % 3 else 3}"/>')
    # radial ticks on the outer ring
    ro = step * 10
    ticks = []
    for k in range(72):
        a = math.radians(k * 5)
        l = 12 if k % 6 == 0 else 6
        ticks.append(f"M{_n(cx + math.cos(a) * (ro + 6))} {_n(cy + math.sin(a) * (ro + 6))}L{_n(cx + math.cos(a) * (ro + 6 + l))} {_n(cy + math.sin(a) * (ro + 6 + l))}")
    out.append(f'<path d="{"".join(ticks)}" stroke="{BONE}" stroke-opacity=".3" stroke-width="1.5"/>')
    rr = step * rnd.choice((4, 5, 6))
    circ = 2 * math.pi * rr
    gap = circ * rnd.uniform(.16, .24)
    rot = rnd.uniform(0, 360)
    sw = step * .36
    out.append(f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(rr)}" fill="none" stroke="{EMBER}" stroke-width="{_n(sw)}" '
               f'stroke-dasharray="{_n(circ - gap)} {_n(gap)}" stroke-linecap="butt" transform="rotate({_n(rot)} {_n(cx)} {_n(cy)})"/>')
    # the missing arc: its ends and a small marker inside the gap
    mid = math.radians(rot + 360 * (1 - gap / circ / 2))
    out.append(f'<circle cx="{_n(cx + math.cos(mid) * rr)}" cy="{_n(cy + math.sin(mid) * rr)}" r="{_n(sw * .55)}" fill="none" stroke="{EMBER}" stroke-width="3" stroke-dasharray="3 5"/>')
    out.append(f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(step * .22)}" fill="{EMBER}"/>')
    return "".join(out)


def _monitoring_scan(w: int, h: int, rnd: random.Random) -> str:
    """Instrument readout: rows of ticks with one stretch missing, marked by an ember bracket (no rings)."""
    rows = 9
    pitch = h / (rows + 1)
    n = 80
    step = w / n
    gap_row = rnd.randint(3, rows - 3)
    a = rnd.randint(int(n * .38), int(n * .55))
    b = a + rnd.randint(int(n * .14), int(n * .24))
    out, base = [], []
    for r in range(rows):
        y = pitch * (r + 1)
        for i in range(n):
            if r == gap_row and a <= i <= b:
                continue
            tall = pitch * (.34 if i % 8 == 0 else .16)
            base.append(f"M{_n(step * i + step / 2)} {_n(y - tall / 2)}v{_n(tall)}")
    out.append(f'<path d="{"".join(base)}" stroke="{BONE}" stroke-opacity=".3" stroke-width="2"/>')
    y = pitch * (gap_row + 1)
    x1, x2 = step * a, step * (b + 1)
    out.append(f'<path d="M{_n(x1)} {_n(y - pitch * .5)}v{_n(pitch)}M{_n(x2)} {_n(y - pitch * .5)}v{_n(pitch)}" stroke="{EMBER}" stroke-width="5"/>'
               f'<path d="M{_n(x1)} {_n(y)}H{_n(x2)}" stroke="{EMBER}" stroke-width="4" stroke-dasharray="3 9" stroke-linecap="round"/>'
               f'<circle cx="{_n((x1 + x2) / 2)}" cy="{_n(y)}" r="{_n(pitch * .2)}" fill="{EMBER}"/>')
    return "".join(out)


def _security(w: int, h: int, rnd: random.Random) -> str:
    s = h / 10
    cols = int(w // s) + 1
    lines = [f"M{_n(i * s)} 0V{h}" for i in range(cols + 1)] + [f"M0 {_n(j * s)}H{w}" for j in range(11)]
    out = [f'<path d="{"".join(lines)}" stroke="{BONE}" stroke-opacity=".1" stroke-width="1.5"/>']
    cells = {.07: [], .13: [], .22: []}
    seen = set()
    for _ in range(int(cols * 10 * .26)):
        c, r = rnd.randrange(cols), rnd.randrange(10)
        if (c, r) in seen:
            continue
        seen.add((c, r))
        cells[rnd.choice(tuple(cells))].append(f"M{_n(c * s + 4)} {_n(r * s + 4)}h{_n(s - 8)}v{_n(s - 8)}h{_n(-(s - 8))}z")
    for k, v in cells.items():
        out.append(f'<path d="{"".join(v)}" fill="{BONE}" fill-opacity="{k}"/>')
    c, r = rnd.randint(int(cols * .45), int(cols * .75)), rnd.randint(2, 6)
    x, y = c * s, r * s
    out.append(f'<rect x="{_n(x + 4)}" y="{_n(y + 4)}" width="{_n(s - 8)}" height="{_n(s - 8)}" fill="{EMBER}"/>')
    out.append(f'<rect x="{_n(x - s * .22)}" y="{_n(y - s * .22)}" width="{_n(s * 1.44)}" height="{_n(s * 1.44)}" fill="none" stroke="{EMBER}" stroke-width="3" transform="rotate({rnd.choice((-9, 7, 11))} {_n(x + s / 2)} {_n(y + s / 2)})"/>')
    # fracture: a short stepped line leaving the cell
    fx, fy = x + s - 4, y + s * .5
    pts = [f"M{_n(fx)} {_n(fy)}"]
    for _ in range(4):
        fx += s * rnd.uniform(.35, .7)
        pts.append(f"H{_n(fx)}")
        fy += s * rnd.choice((-1, 1)) * rnd.uniform(.3, .8)
        pts.append(f"V{_n(fy)}")
    out.append(f'<path d="{"".join(pts)}" fill="none" stroke="{EMBER}" stroke-width="3" stroke-opacity=".75" stroke-dasharray="10 6"/>')
    return "".join(out)


def _reasoning(w: int, h: int, rnd: random.Random) -> str:
    n = 8
    pad = w * .08
    xs = [pad + (w - 2 * pad) * i / (n - 1) for i in range(n)]
    y = h / 2
    pts = []
    for x in xs:
        y = min(h * .78, max(h * .22, y + rnd.uniform(-.2, .2) * h))
        pts.append((x, y))
    out = []
    # echo chain (a parallel, fainter trace)
    echo = [(x, min(h * .9, max(h * .1, yy + h * .13 * (1 if i % 2 else -1)))) for i, (x, yy) in enumerate(pts)]
    out.append(f'<path d="M{" L".join(f"{_n(a)} {_n(b)}" for a, b in echo)}" fill="none" stroke="{BONE}" stroke-opacity=".12" stroke-width="2" stroke-dasharray="4 8"/>')
    out.append(f'<path d="M{" L".join(f"{_n(a)} {_n(b)}" for a, b in pts)}" fill="none" stroke="{BONE}" stroke-opacity=".4" stroke-width="6" stroke-linejoin="round"/>')
    key = rnd.randint(3, 5)
    for i, (x, yy) in enumerate(pts):
        if i == key:
            continue
        r = rnd.choice((18, 22, 27))
        out.append(f'<circle cx="{_n(x)}" cy="{_n(yy)}" r="{r}" fill="{INK}" stroke="{BONE}" stroke-opacity=".7" stroke-width="4"/>'
                   f'<circle cx="{_n(x)}" cy="{_n(yy)}" r="{_n(r * .4)}" fill="{BONE}" fill-opacity=".55"/>')
    kx, ky = pts[key]
    out.append(f'<path d="M{_n(pts[key - 1][0])} {_n(pts[key - 1][1])}L{_n(kx)} {_n(ky)}L{_n(pts[key + 1][0])} {_n(pts[key + 1][1])}" fill="none" stroke="{EMBER}" stroke-width="10" stroke-linejoin="round"/>')
    out.append(f'<circle cx="{_n(kx)}" cy="{_n(ky)}" r="42" fill="{EMBER}"/>'
               f'<circle cx="{_n(kx)}" cy="{_n(ky)}" r="80" fill="none" stroke="{EMBER}" stroke-width="4" stroke-dasharray="6 11"/>'
               f'<circle cx="{_n(kx)}" cy="{_n(ky)}" r="122" fill="none" stroke="{EMBER}" stroke-opacity=".3" stroke-width="2"/>')
    return "".join(out)


def _voice(w: int, h: int, rnd: random.Random) -> str:
    n = 64 if w < 1000 else 96
    pitch = w / n
    bw = pitch * .56
    cy = h / 2
    f1, f2 = rnd.uniform(.12, .22), rnd.uniform(.31, .47)
    p1, p2 = rnd.uniform(0, 6), rnd.uniform(0, 6)
    a = rnd.randint(int(n * .3), int(n * .5))
    b = a + rnd.randint(int(n * .12), int(n * .2))
    base, accent = [], []
    for i in range(n):
        env = .55 + .45 * math.sin(f1 * i + p1) * math.sin(f2 * i + p2)
        amp = h * .08 + h * .34 * abs(env) * (.45 + .55 * rnd.random())
        x = pitch * i + pitch / 2
        d = f"M{_n(x)} {_n(cy - amp)}V{_n(cy + amp)}"
        (accent if a <= i <= b else base).append(d)
    out = [f'<path d="M0 {_n(cy)}H{w}" stroke="{BONE}" stroke-opacity=".18" stroke-width="1.5"/>',
           f'<path d="{"".join(base)}" stroke="{BONE}" stroke-opacity=".34" stroke-width="{_n(bw)}" stroke-linecap="round"/>',
           f'<path d="{"".join(accent)}" stroke="{EMBER}" stroke-width="{_n(bw)}" stroke-linecap="round"/>',
           f'<path d="M{_n(pitch * a)} {_n(h * .12)}V{_n(h * .88)}M{_n(pitch * (b + 1))} {_n(h * .12)}V{_n(h * .88)}" stroke="{EMBER}" stroke-opacity=".55" stroke-width="1.5" stroke-dasharray="3 6"/>']
    return "".join(out)


def _neutral(w: int, h: int, rnd: random.Random) -> str:
    """Stacked offset arcs, like strata; the single ember dot sits on one of them."""
    out, late = [], []
    n = 7
    cx = w * rnd.uniform(.35, .65)
    base = h * rnd.uniform(.92, 1.05)
    pick = rnd.randint(2, 4)
    for i in range(n):
        r = h * (.2 + .105 * i)
        y = base - i * h * .02
        op = round(.05 + .035 * (n - i), 2)
        out.append(f'<circle cx="{_n(cx)}" cy="{_n(y)}" r="{_n(r)}" fill="{BONE}" fill-opacity="{round(.004 * (n - i), 3)}" stroke="{BONE}" stroke-opacity="{round(op * 2.2, 2)}" stroke-width="{3 if i % 2 else 2}"/>')
        if i == pick:
            a = math.radians(rnd.uniform(215, 325))
            late.append(f'<circle cx="{_n(cx + math.cos(a) * r)}" cy="{_n(y + math.sin(a) * r)}" r="{_n(h * .05)}" fill="{EMBER}"/>'
                       f'<circle cx="{_n(cx + math.cos(a) * r)}" cy="{_n(y + math.sin(a) * r)}" r="{_n(h * .09)}" fill="none" stroke="{EMBER}" stroke-opacity=".4" stroke-width="2"/>')
    rule = "".join(f"M{_n(w * i / 12)} 0v{_n(h * .04)}" for i in range(13))
    out.append(f'<path d="{rule}" stroke="{BONE}" stroke-opacity=".25" stroke-width="1.5"/>')
    return "".join(out + late)


def _neutral_bands(w: int, h: int, rnd: random.Random) -> str:
    """Stacked wavy strata; the single ember dot sits on one of them (no circles)."""
    n, out, late = 8, [], []
    pick = rnd.randint(2, 5)
    px = rnd.uniform(.3, .7)
    for i in range(n):
        y0 = h * (.14 + .1 * i)
        amp = h * rnd.uniform(.02, .05)
        f = rnd.uniform(1.2, 2.6)
        ph = rnd.uniform(0, 6.28)
        pts = [(w * k / 40, y0 + amp * math.sin(f * 6.28 * k / 40 + ph)) for k in range(41)]
        op = round(.1 + .035 * (n - i), 2)
        out.append(f'<path d="M{" L".join(f"{_n(a)} {_n(b)}" for a, b in pts)}" fill="none" stroke="{BONE}" stroke-opacity="{op}" stroke-width="{3 if i % 2 else 2}"/>')
        if i == pick:
            k = int(px * 40)
            late.append(f'<circle cx="{_n(pts[k][0])}" cy="{_n(pts[k][1])}" r="{_n(h * .05)}" fill="{EMBER}"/>'
                        f'<circle cx="{_n(pts[k][0])}" cy="{_n(pts[k][1])}" r="{_n(h * .09)}" fill="none" stroke="{EMBER}" stroke-opacity=".4" stroke-width="2"/>')
    rule = "".join(f"M{_n(w * i / 12)} 0v{_n(h * .04)}" for i in range(13))
    out.append(f'<path d="{rule}" stroke="{BONE}" stroke-opacity=".25" stroke-width="1.5"/>')
    return "".join(out + late)


_DRAW = {"agents": _agents, "monitoring": _monitoring, "security": _security,
         "reasoning": _reasoning, "voice": _voice, "neutral": _neutral}
# Second drawing for the two circular motifs: a page that already shows rings asks for variant 1.
_VARIANT = {"monitoring": _monitoring_scan, "neutral": _neutral_bands}


def plate(story_id: str, topic_ids, ratio: str = "16:10", locale: str | None = None, variant: int = 0) -> dict:
    if ratio not in SLOTS:
        raise ValueError(f"unknown plate ratio: {ratio!r}")
    w, h = SLOTS[ratio]
    motif = choose_motif(topic_ids)
    draw = _VARIANT.get(motif) if variant else None
    rnd = _rng(str(story_id), motif + ("+v" if draw else ""))
    body = _base(w, h, rnd) + (draw or _DRAW[motif])(w, h, rnd) + _frame(w, h)
    alt = alt_texts(motif)
    if locale is not None:
        if locale not in alt:
            raise ValueError(f"unknown locale: {locale!r}")
        label = alt[locale].replace("&", "&amp;").replace('"', "&quot;")
        head = f'role="img" aria-label="{label}"'
    else:
        head = 'aria-hidden="true" focusable="false"'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid slice" '
           f'{head} data-motif="{motif}">{body}</svg>')
    return {"svg": svg, "alt": alt, "motif": motif}
