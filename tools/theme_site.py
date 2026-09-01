#!/usr/bin/env python3
"""Apply the public-only FCMO AI Newsletter presentation layer.

This script operates exclusively on an already-public static site tree. It has no
knowledge of, dependency on, or credential for any upstream research workspace.
It is deliberately safe to run on both older plain publication snapshots and newer
snapshots that already carry the visual system.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CSS = r'''
:root{--ink:#f5f7fb;--muted:#9aa5b7;--line:rgba(255,255,255,.105);--paper:#06070a;--accent:#78e7ff;--card:rgba(14,17,25,.78);--warn:#ffd66b;--soft:rgba(255,255,255,.045);--void:#06070a;--panel:rgba(13,17,26,.76);--text:#f6f8fc;--text2:#c4ccda;--text3:#8995a8;--cyan:#78e7ff;--violet:#9f80ff;--magenta:#ff71c8;--gold:#ffd66b;--green:#67e5aa;--radius:18px;--ui:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;--display:Futura,"Avenir Next",Avenir,Inter,ui-sans-serif,sans-serif}
*{box-sizing:border-box}html{scroll-behavior:smooth;background:var(--void)}body{margin:0;color:var(--text);font-family:var(--ui);font-size:16px;line-height:1.62;background:radial-gradient(circle at 8% 2%,rgba(120,231,255,.095),transparent 26rem),radial-gradient(circle at 92% 9%,rgba(159,128,255,.12),transparent 28rem),radial-gradient(circle at 60% 70%,rgba(255,113,200,.035),transparent 32rem),linear-gradient(180deg,#07090d,#06070a 38%,#080a10);min-height:100vh;overflow-x:hidden}body:before{content:"";position:fixed;inset:0;pointer-events:none;z-index:-1;opacity:.32;background-image:linear-gradient(rgba(255,255,255,.018) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.018) 1px,transparent 1px);background-size:72px 72px;mask-image:linear-gradient(to bottom,black,transparent 78%)}::selection{background:rgba(120,231,255,.28);color:#fff}a{color:inherit;text-decoration-color:rgba(120,231,255,.42);text-underline-offset:3px;transition:color .18s,text-decoration-color .18s}a:hover{color:#fff;text-decoration-color:var(--cyan)}.wrap{max-width:1320px;margin:auto;padding:0 clamp(18px,3.2vw,48px)}
.mast{position:relative;display:flex;align-items:flex-end;justify-content:space-between;gap:28px;text-align:left;border:0;padding:34px 0 21px}.mast:after{content:"";position:absolute;left:0;right:0;bottom:0;height:1px;background:linear-gradient(90deg,var(--cyan),rgba(159,128,255,.55) 32%,rgba(255,255,255,.08) 72%,transparent)}.brandlock{display:flex;align-items:center;gap:16px;text-decoration:none!important;min-width:0}.brand-sigil{display:grid;place-items:center;width:54px;height:54px;border-radius:15px;font:900 12px/1 var(--display);letter-spacing:.12em;color:#061018;background:linear-gradient(135deg,#dfffff,var(--cyan) 33%,#9f9cff 72%,#ffc0e8);box-shadow:0 0 0 1px rgba(255,255,255,.28),0 12px 40px rgba(111,166,255,.18)}.brand-copy{display:block}.brand-eyebrow{display:block;margin:0 0 2px;font:800 9px/1.2 var(--ui);letter-spacing:.25em;text-transform:uppercase;color:var(--cyan)}.mast h1{margin:0;font:800 clamp(28px,3.1vw,43px)/.96 var(--display);letter-spacing:-.055em;background:linear-gradient(100deg,#fff,#dce8ff 48%,#adbbd2);-webkit-background-clip:text;background-clip:text;color:transparent}.mast p{max-width:440px;margin:0 0 3px;font:600 11px/1.45 var(--ui);letter-spacing:.12em;text-transform:uppercase;text-align:right;color:var(--text3)}
.nav{position:sticky;top:0;z-index:40;display:flex;align-items:center;gap:5px;flex-wrap:wrap;margin:0 calc(clamp(18px,3.2vw,48px)*-.28);padding:9px 8px;border:0;border-bottom:1px solid var(--line);font:750 10px/1 var(--ui);letter-spacing:.085em;text-transform:uppercase;background:rgba(7,9,13,.74);backdrop-filter:blur(18px) saturate(150%)}.nav a{display:inline-flex;align-items:center;min-height:34px;padding:0 11px;border-radius:9px;text-decoration:none;color:#9faabc;transition:.18s}.nav a:hover{background:rgba(255,255,255,.065);color:#fff;transform:translateY(-1px)}.nav a:first-child{color:#071017;background:linear-gradient(120deg,#d9fbff,var(--cyan));box-shadow:0 0 22px rgba(120,231,255,.12)}
.signal-rail{display:grid;grid-template-columns:auto 1fr auto auto;align-items:center;gap:18px;margin:18px 0 4px;padding:10px 13px;border:1px solid var(--line);border-radius:12px;background:rgba(12,15,22,.62);box-shadow:0 0 0 1px rgba(255,255,255,.05);font:700 10px/1.25 var(--ui);letter-spacing:.08em;text-transform:uppercase;color:var(--text3);overflow:hidden}.signal-live{display:inline-flex;align-items:center;gap:8px;color:#d8fff0}.signal-live:before{content:"";width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 0 5px rgba(103,229,170,.08),0 0 18px rgba(103,229,170,.65);animation:pulse 2.4s ease-in-out infinite}.signal-rail strong{color:#fff}.spectrum{height:1px;background:linear-gradient(90deg,var(--cyan),var(--violet),var(--magenta),transparent)}@keyframes pulse{50%{opacity:.55;transform:scale(.78)}}
.hero{position:relative;display:grid;grid-template-columns:minmax(0,2.35fr) minmax(245px,.65fr);gap:0;margin:18px 0 10px;padding:0;border:1px solid var(--line);border-radius:24px;overflow:hidden;background:linear-gradient(135deg,rgba(17,22,34,.94),rgba(8,11,17,.82));box-shadow:0 28px 80px rgba(0,0,0,.36),inset 0 1px rgba(255,255,255,.03)}.hero:before{content:"FLAGSHIP / VERIFIED";position:absolute;right:17px;top:14px;z-index:2;font:850 9px/1 var(--ui);letter-spacing:.18em;color:rgba(120,231,255,.78)}.hero>div{position:relative;padding:clamp(28px,5vw,70px) clamp(24px,5vw,68px) clamp(30px,5vw,58px);background:radial-gradient(circle at 12% 8%,rgba(120,231,255,.09),transparent 36%),linear-gradient(125deg,rgba(255,255,255,.018),transparent 55%)}.hero>div:after{content:"";position:absolute;width:230px;height:230px;right:-90px;bottom:-120px;border-radius:50%;border:1px solid rgba(120,231,255,.16);box-shadow:0 0 0 38px rgba(159,128,255,.018),0 0 0 78px rgba(255,113,200,.012)}.hero aside{padding:72px clamp(24px,3.2vw,42px) clamp(24px,3.2vw,42px);border-left:1px solid var(--line);background:linear-gradient(180deg,rgba(255,255,255,.035),rgba(255,255,255,.008));display:flex;flex-direction:column;justify-content:flex-start}.hero h2{max-width:980px;margin:9px 0 20px;font:760 clamp(40px,4.35vw,64px)/.98 var(--display);letter-spacing:-.058em;text-wrap:balance}.hero h2 a{text-decoration:none;background:linear-gradient(100deg,#fff,#eef4ff 54%,#b8c7e3);-webkit-background-clip:text;background-clip:text;color:transparent}.hero p{max-width:82ch;color:var(--text2);font-size:15px}.hero aside h3{margin:7px 0 12px;max-width:12ch;font:800 clamp(28px,3vw,42px)/1 var(--display);letter-spacing:-.04em}.hero aside a{font-weight:750;color:var(--cyan)}.hero-summary,.hero-why{display:-webkit-box;-webkit-box-orient:vertical;overflow:hidden}.hero-summary{-webkit-line-clamp:5}.hero-why{-webkit-line-clamp:4;margin-top:17px!important}.hero-cta{margin-top:24px!important;display:block!important;overflow:visible!important}.hero-cta a{display:inline-flex;align-items:center;gap:10px;padding:10px 14px;border:1px solid rgba(120,231,255,.22);border-radius:999px;text-decoration:none!important;background:rgba(120,231,255,.055);font:800 10px/1 var(--ui);letter-spacing:.09em;text-transform:uppercase;color:#d9fbff!important}.hero-cta a span{font-size:15px;transition:transform .18s}.hero-cta a:hover span{transform:translateX(3px)}
.kicker{display:flex;align-items:center;gap:8px;margin-bottom:7px;font:850 10px/1.2 var(--ui);letter-spacing:.16em;text-transform:uppercase;color:var(--cyan)}.kicker:before{content:"";width:18px;height:1px;background:currentColor;opacity:.72}.meta,.tiny{font:600 11px/1.5 var(--ui);color:var(--text3)}.sectionhead{display:flex;justify-content:space-between;align-items:end;gap:18px;margin:42px 0 0;padding:0 0 13px;border:0;border-bottom:1px solid var(--line)}.sectionhead h2{margin:0;font:760 clamp(25px,3.2vw,39px)/1 var(--display);letter-spacing:-.04em}.sectionhead .meta{text-transform:uppercase;letter-spacing:.1em}
.grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:14px;padding:18px 0 30px}.card{position:relative;grid-column:span 4;min-height:265px;padding:22px 21px 20px;border:1px solid var(--line);border-top:1px solid rgba(255,255,255,.13);border-radius:var(--radius);overflow:hidden;background:linear-gradient(145deg,rgba(18,23,35,.82),rgba(10,13,20,.76));box-shadow:0 12px 38px rgba(0,0,0,.15);transition:transform .22s,border-color .22s,background .22s}.card:before{content:"";position:absolute;left:0;top:0;width:100%;height:2px;background:linear-gradient(90deg,var(--cyan),var(--violet),transparent 72%);opacity:.68}.card:hover{transform:translateY(-4px);border-color:rgba(120,231,255,.26);background:linear-gradient(145deg,rgba(21,28,42,.92),rgba(11,14,22,.86))}.card:nth-child(6n+2):before,.card:nth-child(6n+5):before{background:linear-gradient(90deg,var(--violet),var(--magenta),transparent 72%)}.card:nth-child(6n+3):before{background:linear-gradient(90deg,var(--gold),var(--magenta),transparent 72%)}.card.signal:before{background:linear-gradient(90deg,var(--gold),#ff9d64,transparent 75%)}.card h3{margin:8px 0 13px;font:720 clamp(20px,2vw,26px)/1.08 var(--display);letter-spacing:-.032em}.card h3 a{text-decoration:none}.card p{margin:14px 0 0;color:#adb7c8;font-size:13.5px}.badge{display:inline-flex;align-items:center;min-height:24px;margin:3px 4px 3px 0;padding:4px 8px;border:1px solid rgba(255,255,255,.11);border-radius:999px;background:rgba(255,255,255,.035);font:750 9px/1 var(--ui);letter-spacing:.055em;text-transform:uppercase;color:#aeb8c8}.badge.impact{border-color:rgba(255,214,107,.22);background:rgba(255,214,107,.07);color:#ffe49d}.badge.signal{border-color:rgba(255,214,107,.27);color:var(--gold);background:rgba(255,214,107,.055)}
.story{max-width:1040px;margin:0 auto;padding:clamp(42px,6vw,82px) 0}.story>h1{max-width:980px;margin:0 0 22px;font:780 clamp(40px,6vw,72px)/.99 var(--display);letter-spacing:-.055em;background:linear-gradient(105deg,#fff,#e9f0ff 62%,#aebed8);-webkit-background-clip:text;background-clip:text;color:transparent}.story>p{max-width:82ch;color:#c1cad8}.story>p:first-of-type{font-size:17px;line-height:1.72;color:#d7deea}.story h2{margin:54px 0 14px;padding-top:7px;font:760 clamp(23px,3vw,34px)/1.08 var(--display);letter-spacing:-.035em}.story h2:after{content:"";display:block;width:44px;height:2px;margin-top:12px;background:linear-gradient(90deg,var(--cyan),var(--violet))}.story strong{color:#f7f9ff}.story li{margin:9px 0;color:#bac4d3}.notice{position:relative;margin:26px 0;padding:18px 20px 18px 22px;border:1px solid rgba(120,231,255,.15);border-left:2px solid var(--cyan);border-radius:0 13px 13px 0;background:linear-gradient(90deg,rgba(120,231,255,.07),rgba(120,231,255,.015) 68%,transparent);color:#cbd4e1}.signalnotice{border-color:rgba(255,214,107,.18);border-left-color:var(--gold);background:linear-gradient(90deg,rgba(255,214,107,.075),transparent 72%)}.facts{display:grid;grid-template-columns:minmax(145px,.55fr) minmax(0,2.45fr);margin:18px 0 40px;border:1px solid var(--line);border-radius:16px;overflow:hidden;background:rgba(12,15,23,.5)}.facts dt,.facts dd{margin:0;padding:15px 18px;border:0;border-bottom:1px solid var(--line)}.facts dt{font:800 9.5px/1.4 var(--ui);letter-spacing:.12em;text-transform:uppercase;color:#8090a7;background:rgba(255,255,255,.025)}.facts dd{color:#c1cad7}.sources a{color:#d9f9ff}
.controls{display:grid;grid-template-columns:2fr repeat(4,1fr);gap:9px;margin:18px 0 28px;padding:12px;border:1px solid var(--line);border-radius:15px;background:rgba(12,15,23,.62)}.controls input,.controls select{width:100%;min-height:43px;padding:10px 12px;border:1px solid rgba(255,255,255,.1);border-radius:9px;outline:none;background:#0b0e15;color:#e7ecf5;font:600 12px var(--ui)}.result{padding:23px 0;border-top:1px solid var(--line)}.result h3{margin:0 0 8px;font:720 23px/1.1 var(--display);letter-spacing:-.028em}.scale{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:20px 0}.scale div{padding:14px;border:1px solid var(--line);border-radius:11px;background:rgba(255,255,255,.028)}.archive{list-style:none;padding:0!important;margin:25px 0}.archive li{display:grid;grid-template-columns:1fr auto;align-items:center;gap:15px;margin:0!important;padding:18px 0!important;border-top:1px solid var(--line)}.archive li>a{font:760 clamp(22px,3vw,32px)/1 var(--display);letter-spacing:-.035em;text-decoration:none}.footer{position:relative;margin-top:52px;padding:28px 0 44px;border:0;border-top:1px solid var(--line);font:600 10px/1.8 var(--ui);color:#69778c}.footer:before{content:"FCMO / AI FRONTIER";display:block;margin-bottom:10px;font:850 9px/1 var(--ui);letter-spacing:.2em;color:var(--cyan)}.footer a{color:#9ba8bb;text-decoration:none}code{padding:2px 5px;border:1px solid rgba(255,255,255,.07);border-radius:5px;background:#10141d;color:#d6deeb}
@media(prefers-reduced-motion:no-preference){.hero,.card{animation:rise .5s cubic-bezier(.2,.7,.2,1) both}@keyframes rise{from{opacity:0;transform:translateY(9px)}to{opacity:1;transform:none}}}
@media(max-width:1050px){.card{grid-column:span 6}.hero{grid-template-columns:1fr}.hero aside{border-left:0;border-top:1px solid var(--line)}.signal-rail{grid-template-columns:auto 1fr auto}.rail-last{display:none}}
@media(max-width:780px){body{font-size:15px}.wrap{padding:0 17px}.mast{align-items:flex-start;padding-top:24px}.mast p{display:none}.brand-sigil{width:46px;height:46px;border-radius:13px}.nav{margin:0 -5px;overflow-x:auto;flex-wrap:nowrap;scrollbar-width:none}.nav::-webkit-scrollbar{display:none}.nav a{white-space:nowrap}.signal-rail{grid-template-columns:auto 1fr}.rail-mid,.rail-last{display:none}.hero{border-radius:18px}.hero>div{padding:32px 22px}.hero aside{padding-top:30px}.hero h2{font-size:clamp(35px,10vw,56px)}.hero-summary{-webkit-line-clamp:6}.hero-why{-webkit-line-clamp:5}.grid{gap:11px}.card{grid-column:span 12;min-height:0}.story{padding:44px 2px}.story>h1{font-size:clamp(36px,10vw,54px)}.facts{grid-template-columns:1fr}.controls{grid-template-columns:1fr 1fr}.scale{grid-template-columns:1fr 1fr}.sectionhead{align-items:flex-start;flex-direction:column}.archive li{grid-template-columns:1fr}}
@media(max-width:500px){.controls,.scale{grid-template-columns:1fr}.brand-eyebrow{font-size:8px}.mast h1{font-size:27px}.hero:before{display:none}}
'''


def counts(root: Path) -> tuple[int,int]:
    briefs=0
    data=root/'data'/'developments.jsonl'
    if data.exists(): briefs=sum(1 for x in data.read_text(encoding='utf-8').splitlines() if x.strip())
    editions=len(list((root/'editions').glob('????-??-??.html'))) if (root/'editions').exists() else 0
    return briefs,editions


def mast() -> str:
    return '<header class="mast"><a class="brandlock" href="/FCMO-AI-Newsletter/" aria-label="FCMO AI Newsletter front page"><span class="brand-sigil">FCMO</span><span class="brand-copy"><span class="brand-eyebrow">Frontier intelligence</span><h1>AI Newsletter</h1></span></a><p>Evidence-first intelligence for people who want the signal before the noise.</p></header>'


def role(rel:str)->str:
    if rel=='index.html': return 'fcmo-page fcmo-home'
    if rel.startswith('developments/'): return 'fcmo-page fcmo-development'
    if rel.startswith('editions/'): return 'fcmo-page fcmo-edition'
    return 'fcmo-page fcmo-index'


def theme(text:str,rel:str,briefs:int,editions:int)->str:
    text=re.sub(r'<header class="mast">.*?</header>',mast(),text,count=1,flags=re.I|re.S)
    text=re.sub(r'<body(?:\s+class="[^"]*")?>',f'<body class="{role(rel)}">',text,count=1,flags=re.I)
    if 'id="fcmo-visual-system"' not in text:
        text=text.replace('</head>',f'<style id="fcmo-visual-system">{CSS}</style></head>',1)
    if rel!='index.html': return text
    text=re.sub(r'Latest\s+archive\s+date','LATEST EDITION',text,count=1,flags=re.I)
    text=text.replace('Front-page placement follows explicit importance/evidence fields. Historical daily newsletters are frozen by publication receipts.','Front-page placement weighs evidence strength and potential importance separately. Daily editions are preserved as published, with corrections tracked transparently.')
    if 'class="signal-rail"' not in text:
        rail=f'<div class="signal-rail" aria-label="Publication status"><span class="signal-live">Live frontier feed</span><span class="spectrum" aria-hidden="true"></span><span class="rail-mid"><strong>{briefs}</strong> research briefs</span><span class="rail-last"><strong>{editions}</strong> daily editions</span></div>'
        text=re.sub(r'(<div class="nav">.*?</div>)',lambda m:m.group(1)+rail,text,count=1,flags=re.I|re.S)
    else:
        text=re.sub(r'<span class="rail-mid">.*?</span>\s*<span class="rail-last">.*?</span>',f'<span class="rail-mid"><strong>{briefs}</strong> research briefs</span><span class="rail-last"><strong>{editions}</strong> daily editions</span>',text,count=1,flags=re.I|re.S)
    hero=re.search(r'<section class="hero">(?P<body>.*?)</section>',text,re.I|re.S)
    if hero:
        body=hero.group('body')
        if '<aside>' in body and 'class="hero-summary"' not in body:
            left,aside=body.split('<aside>',1); i=0
            def tag(m):
                nonlocal i;i+=1
                cls='hero-summary' if i==1 else 'hero-why';attrs=m.group(1) or ''
                return f'<p class="{cls}"{attrs}>'
            left=re.sub(r'<p([^>]*)>',tag,left,count=2,flags=re.I);body=left+'<aside>'+aside
        if 'class="hero-cta"' not in body:
            href=re.search(r'<h2>\s*<a href="([^"]+)"',body,re.I|re.S)
            if href: body=body.replace('</div><aside>',f'<p class="hero-cta"><a href="{href.group(1)}">Read full research brief <span aria-hidden="true">→</span></a></p></div><aside>',1)
        text=text[:hero.start('body')]+body+text[hero.end('body'):]
    return text


def main()->int:
    root=Path(sys.argv[1] if len(sys.argv)>1 else 'site').resolve()
    if not (root/'index.html').is_file(): raise SystemExit('theme: site/index.html missing')
    briefs,editions=counts(root); changed=0
    for path in sorted(root.rglob('*.html')):
        rel=path.relative_to(root).as_posix();before=path.read_text(encoding='utf-8');after=theme(before,rel,briefs,editions)
        if after!=before: path.write_text(after,encoding='utf-8');changed+=1
    home=(root/'index.html').read_text(encoding='utf-8')
    required=('fcmo-visual-system','class="brandlock"','class="signal-rail"','class="hero-summary"','class="hero-why"','class="hero-cta"','LATEST EDITION')
    missing=[x for x in required if x not in home]
    if missing: raise SystemExit('theme missing required surface tokens: '+', '.join(missing))
    for bad in ('publication receipts','Latest archive date'):
        if bad.lower() in home.lower(): raise SystemExit('theme retained implementation-facing wording: '+bad)
    print(f'FCMO Frontier Signal theme OK: {changed} HTML pages; {briefs} briefs; {editions} editions')
    return 0

if __name__=='__main__': raise SystemExit(main())
