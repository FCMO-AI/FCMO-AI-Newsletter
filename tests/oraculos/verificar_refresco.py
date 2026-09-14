#!/usr/bin/env python3
"""Exercise the autonomous refresh with one synthetic new Story.

This test follows the production boundary: start from the *current sanitized
corpus*, append one plausible Story plus ARB-authored ES/ZH deltas, then run the
same deterministic ingestion/localization/publication stages. A frozen historical
fixture is still useful for the generator's independent growth test, but it must
not be mixed with today's locale packs or publication state.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "corpus"
NEW_ID = "FCMO-0C0DE0000001"
EXCLUDE = {".git", "publish", "regression", "__pycache__", ".pytest_cache"}
IGNORE = ("publish/", "regression/", "__pycache__/", ".pytest_cache/")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verificar_generador import con_historia_sintetica

PROSE_STRINGS = ("title", "summary", "why_it_matters", "why", "importance_rationale")
PROSE_LISTS = ("limitations", "contradictory_evidence", "engineering_implications", "policy_implications", "research_implications")
PROSE_OBJECT_LISTS = {"claims": ("text",), "evidence_gaps": ("description",), "relationships": ("summary",)}
PROSE_DICTS = ("technical",)


def row_for(corpus: Path, ident: str) -> dict:
    for line in (corpus / "data/developments.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("id") == ident:
                return row
    raise ValueError(f"{ident} missing from synthetic corpus")


def native(value: Any, locale: str) -> Any:
    if not isinstance(value, str) or not value.strip():
        return value
    if locale == "es-419":
        return value + " — redacción editorial en español, preservando exactamente la evidencia y sus límites."
    return value + " — 简体中文编辑说明：保持原始证据、数字、标识、链接与适用范围完全不变。"


def overlay(row: dict, locale: str) -> dict:
    result: dict[str, Any] = {}
    for key in PROSE_STRINGS:
        if isinstance(row.get(key), str) and row[key].strip():
            result[key] = native(row[key], locale)
    if "why" not in result:
        rationale = row.get("why_it_matters") or row.get("summary")
        if isinstance(rationale, str) and rationale.strip():
            result["why"] = native(rationale, locale)
    for key in PROSE_LISTS:
        source = row.get(key)
        if isinstance(source, list) and source:
            result[key] = [native(value, locale) for value in source]
    for key, fields in PROSE_OBJECT_LISTS.items():
        source = row.get(key)
        if isinstance(source, list) and source:
            translated = []
            for item in source:
                if not isinstance(item, dict):
                    translated.append(item); continue
                target = {field: native(item[field], locale) for field in fields if isinstance(item.get(field), str) and item[field].strip()}
                translated.append(target)
            result[key] = translated
    for key in PROSE_DICTS:
        source = row.get(key)
        if isinstance(source, dict):
            target = {field: native(value, locale) for field, value in source.items() if isinstance(value, str) and value.strip()}
            if target:
                result[key] = target
    return result


def inject_locales(corpus: Path) -> None:
    row = row_for(corpus, NEW_ID)
    for locale in ("es-419", "zh-Hans"):
        path = corpus / "data/locales" / locale / "records.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = {}
        if path.is_file():
            existing = json.loads(path.read_text(encoding="utf-8")).get("records") or {}
        existing[NEW_ID] = overlay(row, locale)
        path.write_text(json.dumps({"schema":"fcmo-airlocked-locale-delta-v1","locale":locale,"canonical_locale":"en","records":existing}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def run(cwd: Path, label: str, args: list[str]) -> bool:
    proc = subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode:
        print(f"refresh broke at {label} ({proc.returncode})", file=sys.stderr)
        print((proc.stderr or proc.stdout or "")[-3000:], file=sys.stderr)
        return False
    print("ok ", label)
    return True


def mtimes(root: Path) -> dict[str, float]:
    return {p.relative_to(root).as_posix(): p.stat().st_mtime_ns for p in root.rglob("*") if p.is_file()}


def changed(before: dict[str,float], after: dict[str,float]) -> list[str]:
    moved=[r for r in set(before)|set(after) if before.get(r)!=after.get(r)]
    return [r for r in moved if not any(r.startswith(x) or f"/{x}" in r for x in IGNORE)]


def commit_paths() -> list[str]:
    text=(ROOT/".github/workflows/daily-refresh.yml").read_text(encoding="utf-8")
    match=re.search(r"git add -A -- (.+)", text)
    if not match: raise SystemExit("daily-refresh.yml has no closed git-add boundary")
    return match.group(1).split()


def covered(path: str, roots: list[str]) -> bool:
    return any(path==r or path.startswith(r.rstrip("/")+"/") for r in roots)


def ignored_by_git(paths: list[str]) -> set[str]:
    if not paths:return set()
    proc=subprocess.run(["git","check-ignore","--stdin"], cwd=ROOT, input="\n".join(paths).encode(), capture_output=True)
    return {line.strip() for line in proc.stdout.decode("utf-8","replace").splitlines() if line.strip()}


def main() -> int:
    if not CORPUS.is_dir():
        print("current sanitized corpus missing", file=sys.stderr); return 1
    with tempfile.TemporaryDirectory(prefix="fcmo-refresh-") as tmp:
        repo=Path(tmp)/"repo"
        shutil.copytree(ROOT, repo, ignore=lambda _d,names:[n for n in names if n in EXCLUDE])
        corpus=Path(tmp)/"corpus-plus-one"
        con_historia_sintetica(CORPUS, corpus, NEW_ID)
        inject_locales(corpus)
        before=mtimes(repo)
        steps=(
            ("ingest", ["tools/ingest_corpus.py","--corpus",str(corpus),"--out","release-src"]),
            ("relationships", ["tools/synchronize_relationship_surfaces.py","--site","release-src"]),
            ("airlocked locales", ["tools/sync_airlocked_locales.py","--corpus",str(corpus)]),
            ("locale reconciliation", ["tools/reconcile_locale_overlays.py","--site","release-src"]),
            ("locale identity", ["tools/refresh_locale_identity.py","--site","release-src"]),
            ("native integrity/backlog", ["tools/validate_localizations_partial.py","--site","release-src"]),
            ("visual desk offline", ["tools/visual_desk.py","--release-src","release-src","--site","site","--offline"]),
            ("story layer", ["tools/build_newsroom_surfaces.py","--release-src","release-src","--site","site"]),
            ("pending locale pages", ["tools/mark_pending_localizations.py","--site","site"]),
            ("fresh lead", ["tools/editorial_freshness.py","select","--stories","site/data/stories.json"]),
            ("promote lead", ["tools/promote_story_front_page.py","--site","site"]),
            ("frontends", ["tools/build_editorial_frontends.py","--site","site"]),
            ("frontends final", ["tools/finalize_editorial_frontends.py","--site","site"]),
            ("overlay", ["tools/build_final_release.py"]),
            ("ready receipt", ["tools/build_ready_receipt.py"]),
            ("publication gates", ["tools/verify_release.py"]),
        )
        for label,args in steps:
            if not run(repo,label,args): return 1

        moved=changed(before,mtimes(repo)); ignored=ignored_by_git(moved); allowed=commit_paths()
        outside=sorted(r for r in moved if r not in ignored and not covered(r,allowed))
        if outside:
            print("refresh writes outside commit boundary:\n  - "+"\n  - ".join(outside[:20]),file=sys.stderr); return 1

        publish=repo/"publish"
        if not publish.is_dir():
            print("publication gates did not create publish/",file=sys.stderr); return 1
        required=(f"data/briefs/{NEW_ID}.json",f"developments/{NEW_ID}.html",f"news/en/{NEW_ID}.html",f"news/es/{NEW_ID}.html",f"news/zh-hans/{NEW_ID}.html")
        missing=[rel for rel in required if not (publish/rel).is_file()]
        if missing:
            print("new Story missing published surfaces: "+", ".join(missing),file=sys.stderr); return 1
        html=(publish/"index.html").read_text(encoding="utf-8")
        match=re.search(r'<script id="fcmo-data" type="application/json">(.*?)</script>',html,re.S)
        records=json.loads(match.group(1))["records"] if match else []
        if NEW_ID not in {row["id"] for row in records}:
            print("new Story missing from published canonical corpus",file=sys.stderr); return 1

    print(f"refresh OK: {len(records)} Stories; synthetic Story reached EN/ES/ZH + discovery through current pipeline")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
