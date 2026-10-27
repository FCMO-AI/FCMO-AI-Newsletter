#!/usr/bin/env python3
"""Production Airlock transport with truthful partial native-locale coverage.

The original ``newswire_bridge.py`` remains the strict all-locales-parity verifier.
Production freshness uses the same privacy/content-addressing/path checks, but a new
English Story may cross before its ES/ZH prose is authored. Locale deltas must remain
well-formed, source-authored, symmetric between ES/ZH, and subsets of the public
corpus. Missing translations are handled downstream as explicit pending pages.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from tools import newswire_bridge as strict
except ImportError:  # executed as tools/newswire_bridge_partial_locales.py
    import newswire_bridge as strict  # type: ignore


def _public_ids(release: Path) -> set[str]:
    errors: list[str] = []
    ids = strict._canonical_ids(release / "data" / "developments.jsonl", errors)
    if errors:
        raise ValueError("public corpus identity validation failed: " + "; ".join(errors))
    return ids


def _locale_delta_ids(release: Path, locale: str) -> set[str]:
    path = release / "data" / "locales" / locale / "records.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    rows = doc.get("records") if isinstance(doc, dict) else None
    if not isinstance(rows, dict):
        raise ValueError(f"{locale}: locale records missing")
    return set(rows)


def _synthetic_coverage_baseline(release: Path) -> Path:
    """Create a verifier-only baseline proving coverage without inventing prose.

    ``newswire_bridge.verify_release`` validates public paths, digests, privacy,
    schemas and locale record shapes; its only production-incompatible rule is that
    baseline+delta cover every English ID. Give that one check a temporary ID-only
    baseline. No synthetic overlay is staged or persisted, and we independently prove
    the real incoming locale sets are symmetric subsets of the corpus below.
    """
    ids = sorted(_public_ids(release))
    root = Path(tempfile.mkdtemp(prefix="fcmo-locale-coverage-proof-"))
    for locale in strict.LOCALES:
        folder = root / locale
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "part-coverage-proof.json").write_text(
            json.dumps(
                {
                    "schema": strict.CURATED_PART_SCHEMA,
                    "locale": locale,
                    "canonical_locale": "en",
                    "records": {rid: {} for rid in ids},
                },
                indent=2,
                sort_keys=True,
            ) + "\n",
            encoding="utf-8",
        )
    return root


def _bad_record_reasons(release: Path) -> dict[str, list[str]]:
    """Closed reason codes for record defects; never retain the offending prose."""
    bad = {rid: {"CLAIM_LABEL"} for rid in
           strict._unclassified_claims(release / "data" / "developments.jsonl")}
    # A record whose own bytes carry a private/implementation marker (e.g. prose naming the
    # internal pipeline "ARB-run") is withheld alone; it is never published, and the rest of
    # the release must not stay blocked behind it (incident inc-4e68b9a0, 2026-10-22).
    for line in (release / "data" / "developments.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip() and strict.private_marker(line):
            try:
                rid = json.loads(line).get("id")
            except (json.JSONDecodeError, AttributeError):
                continue
            if isinstance(rid, str):
                bad.setdefault(rid, set()).add("PRIVATE_MARKER")
    path = release / "data" / "locales" / "es-419" / "records.json"
    if path.is_file():
        rows = json.loads(path.read_text(encoding="utf-8")).get("records")
        for rid, overlay in (rows.items() if isinstance(rows, dict) else []):
            if isinstance(overlay, dict) and strict.private_marker(json.dumps(overlay, ensure_ascii=False)):
                bad.setdefault(rid, set()).add("PRIVATE_MARKER")
            elif isinstance(overlay, dict) and any(
                isinstance(overlay.get(k), str) and strict._han_dominated(overlay[k]) for k in ("title", "summary")
            ):
                bad.setdefault(rid, set()).add("WRONG_LOCALE")
    return {rid: sorted(reasons) for rid, reasons in sorted(bad.items())}


def quarantine_release(release: Path) -> list[str]:
    """Drop per-record defects from the release instead of refusing the whole transfer.

    A quarantined story is removed from the corpus and from every locale delta, and the
    airlock receipt is re-sealed over the remaining bytes. The corpus guard then carries
    the last published version of it forward (or never admits it if it was never published).
    A historical editions/YYYY-MM-DD.html is also an independent optional document:
    withhold the entire document if its own bytes carry a private marker. Never edit
    out a phrase to make a document pass. Required surfaces and other paths, schema
    defects and secrets still fail verification.
    """
    release = release.resolve()
    # Integrity first, before any mutation: the ORIGINAL bytes must match the ORIGINAL receipt,
    # otherwise re-sealing would launder tampered bytes. Nothing is changed if this fails.
    receipt_path = release / "airlock.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not isinstance(receipt, dict) or receipt.get("schema") != strict.AIRLOCK_SCHEMA \
            or receipt.get("state") != strict.AIRLOCK_STATE:
        raise ValueError("airlock.json: not a ready airlock receipt; refusing to quarantine")
    original_digest = strict.release_digest(release)
    if receipt.get("corpus_digest") != original_digest \
            or receipt.get("release_id") != f"newswire-{original_digest[:24]}":
        raise ValueError("airlock.json: original bytes do not match the original receipt; refusing to quarantine")
    record_reasons = _bad_record_reasons(release)
    bad = set(record_reasons)
    bad_editions = [
        path for path in sorted((release / "editions").glob("*.html"))
        if not (release / "editions").is_symlink() and not path.is_symlink() and path.is_file()
        and strict._allowed(path.relative_to(release).as_posix())
        and strict.private_marker(path.read_text(encoding="utf-8"))
    ]
    if not bad and not bad_editions:
        return []
    original_release_id = receipt["release_id"]
    dev = release / "data" / "developments.jsonl"
    kept = []
    for line in dev.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                if json.loads(line).get("id") in bad:
                    continue
            except (json.JSONDecodeError, AttributeError):
                pass
        kept.append(line)
    if bad:
        dev.write_text("\n".join(kept) + "\n", encoding="utf-8")
    for locale in strict.LOCALES:
        lp = release / "data" / "locales" / locale / "records.json"
        if bad and lp.is_file():
            doc = json.loads(lp.read_text(encoding="utf-8"))
            if isinstance(doc.get("records"), dict):
                for rid in bad:
                    doc["records"].pop(rid, None)
                lp.write_text(json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    # Pages keyed by a quarantined id (developments/<rid>.html, per-locale pages) must not be
    # published: the build asserts pages == ids. Aggregates (topics, search) are regenerated
    # by the newsroom build from the remaining corpus.
    for path in sorted(release.rglob("*")):
        if path.is_file() and path != receipt_path and any(rid in path.name for rid in bad):
            path.unlink()
    for path in bad_editions:
        path.unlink()
    digest = strict.release_digest(release)
    receipt.update(
        corpus_digest=digest,
        release_id=f"newswire-{digest[:24]}",
        record_count=len(_public_ids(release)),
        quarantined_from={
            "release_id": original_release_id,
            "corpus_digest": original_digest,
            "ids": sorted(bad),
        },
    )
    if bad_editions:
        receipt["quarantined_from"]["paths"] = [path.relative_to(release).as_posix() for path in bad_editions]
    receipt["quarantine_reasons"] = {
        "records": record_reasons,
        "documents": {path.relative_to(release).as_posix(): ["PRIVATE_MARKER"] for path in bad_editions},
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sorted(bad)


def verify_release(release: Path) -> dict[str, Any]:
    release = release.resolve()
    proof = _synthetic_coverage_baseline(release)
    try:
        receipt = strict.verify_release(release, proof)
    finally:
        shutil.rmtree(proof, ignore_errors=True)

    ids = _public_ids(release)
    locale_sets = {locale: _locale_delta_ids(release, locale) for locale in strict.LOCALES}
    for locale, localized in locale_sets.items():
        extra = localized - ids
        if extra:
            raise ValueError(f"{locale}: locale delta contains IDs outside public corpus")
    if locale_sets[strict.LOCALES[0]] != locale_sets[strict.LOCALES[1]]:
        raise ValueError("native locale delta ID sets differ between es-419 and zh-Hans")

    translated = len(locale_sets[strict.LOCALES[0]])
    pending = len(ids - locale_sets[strict.LOCALES[0]])
    print(
        f"partial-locale Airlock OK: stories={len(ids)} translated_delta={translated} "
        f"pending={pending}"
    )
    return receipt


def stage_release(release: Path, corpus: Path, now: str | None = None) -> dict[str, Any]:
    release = release.resolve()
    corpus = corpus.resolve()
    receipt = verify_release(release)
    # The corpus guard decides per record before anything moves (exit 3 on refusal).
    result = strict.guard_candidate(release, corpus)
    corpus.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{corpus.name}.stage-", dir=corpus.parent))
    backup = corpus.parent / f".{corpus.name}.previous"
    try:
        shutil.rmtree(stage)
        shutil.copytree(release, stage, symlinks=False)
        strict.carry_newsroom_files(corpus, stage, result, now)
        verify_release(stage)
        if backup.exists():
            shutil.rmtree(backup)
        if corpus.exists():
            corpus.rename(backup)
        stage.rename(corpus)
        verify_release(corpus)
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        if not corpus.exists() and backup.exists():
            backup.rename(corpus)
        raise
    return receipt


def _failure_code(command: str, exc: Exception) -> str:
    """Map diagnostics to a closed vocabulary; never publish exception text/paths.

    The strict verifier intentionally keeps detailed local errors. Only these fixed
    categories may cross the public Actions/wire-status boundary. Unknown messages
    remain UNCLASSIFIED rather than being copied or truncated into public output.
    """
    reason = "UNCLASSIFIED"
    if isinstance(exc, OSError):
        reason = "IO"
    elif isinstance(exc, UnicodeError):
        reason = "ENCODING"
    else:
        text = str(exc)
        for marker, category in (
            ("private/implementation/strategic marker", "PRIVATE_MARKER"),
            ("secret-like material", "SECRET"),
            ("personal email", "PERSONAL_EMAIL"),
            ("private runner path", "RUNNER_PATH"),
            ("original bytes do not match the original receipt", "INTEGRITY"),
            ("corpus digest does not match", "INTEGRITY"),
            ("release_id does not match", "INTEGRITY"),
            ("public corpus identity validation failed", "CORPUS_IDENTITY"),
            ("claims without a valid label", "CLAIM_LABEL"),
            ("symlink forbidden", "PATH"),
            ("path not allowlisted", "PATH"),
            ("publication receipt", "PUBLICATION_RECEIPT"),
            ("locale", "LOCALE"),
            ("airlock.json:", "RECEIPT"),
            ("invalid JSON", "JSON"),
            ("required transfer file missing", "MISSING_FILE"),
        ):
            if marker in text:
                reason = category
                break
    return f"{command.upper()}:{reason}"


def _report_failure(args: argparse.Namespace, exc: Exception) -> None:
    code = _failure_code(args.command, exc)
    # These are explicit caller-owned destinations, never paths read from a release.
    if args.error_code_out:
        args.error_code_out.write_text(code + "\n", encoding="utf-8")
    print(code if args.error_code_out else str(exc), file=sys.stderr)


def _public_failure_summary(code_file: Path, summary: Path) -> int:
    """Report a closed code only; this command never opens the release or a log."""
    reasons = {
        "UNCLASSIFIED", "IO", "ENCODING", "PRIVATE_MARKER", "SECRET", "PERSONAL_EMAIL",
        "RUNNER_PATH", "INTEGRITY", "CORPUS_IDENTITY", "CLAIM_LABEL", "PATH",
        "PUBLICATION_RECEIPT", "LOCALE", "RECEIPT", "JSON", "MISSING_FILE",
    }
    allowed = {f"{command}:{reason}" for command in ("VERIFY", "QUARANTINE") for reason in reasons}
    try:
        # Reject oversized/untrusted diagnostics instead of reading an arbitrary log.
        with code_file.open("rb") as stream:
            code = stream.read(65).decode("ascii").strip()
    except (OSError, UnicodeError):
        code = "VERIFY:UNCLASSIFIED"
    if code not in allowed:
        code = "VERIFY:UNCLASSIFIED"
    try:
        with summary.open("a", encoding="utf-8") as stream:
            stream.write(f"Verificación del airlock rechazada: `{code}`.\n")
    except OSError:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    v = sub.add_parser("verify")
    v.add_argument("release", type=Path)
    q = sub.add_parser("quarantine")
    q.add_argument("release", type=Path)
    q.add_argument("--out", type=Path, help="file receiving one quarantined id per line")
    s = sub.add_parser("stage")
    s.add_argument("release", type=Path)
    s.add_argument("corpus", type=Path)
    report = sub.add_parser("report", help="publica un código de fallo sin abrir el release")
    report.add_argument("--code-file", type=Path, required=True)
    report.add_argument("--summary", type=Path, required=True)
    for command in (v, q, s):
        command.add_argument("--error-code-out", type=Path, help="escribe solo un código público de fallo")
    args = parser.parse_args(argv)
    if args.command == "report":
        return _public_failure_summary(args.code_file, args.summary)
    if args.command == "quarantine":
        try:
            ids = quarantine_release(args.release)
        except Exception as exc:
            _report_failure(args, exc)
            return 1
        if args.out:
            args.out.write_text("".join(f"{i}\n" for i in ids), encoding="utf-8")
        print(f"quarantined {len(ids)} record(s)")
        return 0
    try:
        receipt = verify_release(args.release) if args.command == "verify" else stage_release(args.release, args.corpus)
    except strict.GuardRefused as exc:
        print(f"corpus guard refused the release; corpus/ untouched: {exc}", file=sys.stderr)
        return strict.corpus_guard.EXIT_REFUSED
    except Exception as exc:
        _report_failure(args, exc)
        return 1
    print(f"airlock transfer OK: {receipt.get('release_id')} records={receipt.get('record_count')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
