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

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "corpus"
NEW_ID = "FCMO-0C0DE0000001"
EXCLUDE = {".git", "publish", "regression", "__pycache__", ".pytest_cache", "_audit"}
IGNORE = ("publish/", "regression/", "__pycache__/", ".pytest_cache/")

def inject_locales(corpus: Path) -> None:
    # Reuse a complete source-controlled EN/ES/ZH artifact. Appending a language
    # suffix to English prose is counterfeit translation and fails ENGLISH_LEAK.
    existing_id = "FCMO-FAD9D0AFD3E4"
    source_path = corpus / "data/developments.jsonl"
    records = [json.loads(line) for line in source_path.read_text().splitlines() if line.strip()]
    source = next(row for row in records if row["id"] == existing_id)
    new = json.loads(json.dumps(source).replace(existing_id, NEW_ID))
    # Distinct fixture evidence prevents the Story duplicate rule merging it.
    new["source_urls"] = ["https://example.invalid/refresh-fixture"]
    new.pop("sources", None)
    records = [row for row in records if row["id"] != NEW_ID] + [new]
    source_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records))
    for locale in ("es-419", "zh-Hans"):
        native = {}
        for pack in sorted((ROOT / "site/data/i18n" / locale).glob("part-*.json")):
            for key, value in json.loads(pack.read_text())["records"].get(existing_id, {}).items():
                native.setdefault(key, value)
        path = corpus / "data/locales" / locale / "records.json"
        doc = json.loads(path.read_text())
        doc["records"][NEW_ID] = json.loads(json.dumps(native).replace(existing_id, NEW_ID))
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")


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
        corpus=repo/"corpus"
        inject_locales(corpus)
        before=mtimes(repo)
        steps=(
            ("ingest", ["tools/ingest_corpus.py","--corpus",str(corpus),"--out","release-src","--i18n-dir","site/data/i18n"]),
            ("relationships", ["tools/synchronize_relationship_surfaces.py","--site","release-src"]),
            ("airlocked locales", ["tools/sync_airlocked_locales.py","--corpus",str(corpus),"--publication-src","release-src"]),
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
            ("native admission oracle", ["tests/oraculos/verificar_traduccion.py"]),
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
