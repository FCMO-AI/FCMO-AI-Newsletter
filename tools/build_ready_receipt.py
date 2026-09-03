#!/usr/bin/env python3
"""Generate or verify the measured public-release receipt.

The receipt is derived from the same public tree that the release assembler
mounts: the frozen overlay is checked, applied over ``site/``, and then
localized.  ``--check`` compares the receipt's individual measured values, so
platform-specific CRLF/LF line endings do not make a valid receipt fail.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SITE = REPO / "site"
OVERLAY = REPO / "release-overlay" / "final"
MANIFEST_PATH = OVERLAY / "manifest.json"
RECEIPT_PATH = REPO / "READY_TO_PUBLISH.md"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_string(mapping: dict, key: str, source: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{source}.{key} must be a non-empty string")
    return value


def require_integer(mapping: dict, key: str, source: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{source}.{key} must be a non-negative integer")
    return value


def read_manifest() -> dict:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"cannot read release manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValueError("release manifest must be a JSON object")
    return manifest


def run(*arguments: str) -> None:
    subprocess.run([sys.executable, *arguments], cwd=REPO, check=True)


def release_display(slug: str) -> str:
    """Derive the receipt heading from the release slug without a second label."""
    words = slug.split("-")
    if not words or any(not word for word in words):
        raise ValueError("release manifest has an invalid release slug")
    return " ".join(
        word if word.startswith("v") and word[1:2].isdigit() else word.capitalize()
        for word in words[:-1]
    ) + f" {words[-1]}"


def viewport_label(widths: list[int]) -> str:
    labels = [f"{width}px" for width in widths]
    if not labels:
        raise ValueError("manifest.qa.viewport_widths must not be empty")
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return " and ".join(labels)
    return ", ".join(labels[:-1]) + ", and " + labels[-1]


def payload_measurements(manifest: dict) -> tuple[int, str, str]:
    part_paths = sorted((OVERLAY / "parts").glob("part-*.b64"))
    part_count = len(part_paths)
    expected_parts = require_integer(manifest, "parts", "manifest")
    if part_count != expected_parts:
        raise ValueError(
            f"release payload part count mismatch: manifest={expected_parts}, disk={part_count}"
        )
    try:
        encoded = "".join(path.read_text(encoding="ascii").strip() for path in part_paths)
        archive = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError(f"cannot decode release payload parts: {exc}") from exc
    return part_count, sha256(archive), sha256(encoded.encode("ascii"))


def mount_public_tree(manifest: dict) -> dict[str, str]:
    """Mount and measure the exact candidate that Pages would serve."""
    run("tools/build_final_release.py", "--check")
    canonical_index_sha256 = require_string(manifest, "index_sha256", "manifest")
    with tempfile.TemporaryDirectory(prefix="fcmo-ready-receipt-") as temporary:
        target = Path(temporary) / "publish"
        shutil.copytree(SITE, target)
        run("tools/apply_final_release.py", str(target))
        run("tools/apply_curated_i18n.py", str(target), canonical_index_sha256)

        index = target / "index.html"
        frontend_sha256 = sha256(index.read_bytes())
        public_files = sum(1 for path in target.rglob("*") if path.is_file())
        canonical_dossiers = len(list((target / "data" / "briefs").glob("FCMO-*.json")))
        stable_dossier_routes = len(list((target / "developments").glob("FCMO-*.html")))
        edition_html_routes = len(list((target / "editions").glob("*.html")))
        edition_json_routes = len(list((target / "data" / "editions").glob("*.json")))
        if edition_html_routes != edition_json_routes:
            raise ValueError(
                "assembled edition route mismatch: "
                f"HTML={edition_html_routes}, JSON={edition_json_routes}"
            )
        try:
            media = json.loads((target / "data" / "media.json").read_text(encoding="utf-8"))
            agent = json.loads((target / "agent.json").read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError(f"cannot read assembled public data: {exc}") from exc
        if not isinstance(media, list):
            raise ValueError("assembled data/media.json must be an array")
        if not isinstance(agent, dict):
            raise ValueError("assembled agent.json must be an object")
        real_visuals = sum(1 for item in media if isinstance(item, dict) and item.get("sourced") is True)
        fallback_visuals = sum(1 for item in media if isinstance(item, dict) and item.get("sourced") is False)
        return {
            "frontend_sha256": frontend_sha256,
            "public_files": str(public_files),
            "canonical_dossiers": str(canonical_dossiers),
            "stable_dossier_routes": str(stable_dossier_routes),
            "edition_routes": str(edition_html_routes),
            "real_visuals": str(real_visuals),
            "fallback_visuals": str(fallback_visuals),
            "agent_schema": require_string(agent, "schema", "assembled agent.json"),
            "agent_query_contract": require_string(agent, "query_contract", "assembled agent.json"),
        }


def measured_values() -> dict[str, str]:
    manifest = read_manifest()
    qa = manifest.get("qa")
    if not isinstance(qa, dict):
        raise ValueError("manifest.qa must be an object")
    viewport_widths = qa.get("viewport_widths")
    if (
        not isinstance(viewport_widths, list)
        or not viewport_widths
        or any(not isinstance(width, int) or isinstance(width, bool) or width < 0 for width in viewport_widths)
    ):
        raise ValueError("manifest.qa.viewport_widths must be a non-empty array of non-negative integers")
    part_count, archive_sha256, payload_sha256 = payload_measurements(manifest)
    mounted = mount_public_tree(manifest)
    return {
        "release_display": release_display(require_string(manifest, "release", "manifest")),
        "receipt_measurement": require_string(qa, "measured_at", "manifest.qa"),
        "qa_tool": require_string(qa, "tool", "manifest.qa"),
        "qa_browser": require_string(qa, "browser", "manifest.qa"),
        "manifest_schema": require_string(manifest, "schema", "manifest"),
        "release": require_string(manifest, "release", "manifest"),
        "frontend_sha256": mounted["frontend_sha256"],
        "archive_sha256": archive_sha256,
        "payload_sha256": payload_sha256,
        "part_count": str(part_count),
        "public_files": mounted["public_files"],
        "canonical_dossiers": mounted["canonical_dossiers"],
        "stable_dossier_routes": mounted["stable_dossier_routes"],
        "edition_routes": mounted["edition_routes"],
        "real_visuals": mounted["real_visuals"],
        "fallback_visuals": mounted["fallback_visuals"],
        "viewport_widths": viewport_label(viewport_widths),
        "route_viewport_checks": str(require_integer(qa, "route_viewport_checks", "manifest.qa")),
        "javascript_failures": str(require_integer(qa, "javascript_failures", "manifest.qa")),
        "overflow_failures": str(require_integer(qa, "overflow_failures", "manifest.qa")),
        "blank_route_failures": str(require_integer(qa, "blank_route_failures", "manifest.qa")),
        "legal_dom_checks": str(require_integer(qa, "legal_dom_checks", "manifest.qa")),
        "i18n_dom_checks": str(require_integer(qa, "i18n_dom_checks", "manifest.qa")),
        "agent_schema": mounted["agent_schema"],
        "agent_query_contract": mounted["agent_query_contract"],
        "visual_receipt_measurement": require_string(qa, "measured_at", "manifest.qa"),
        "visual_qa_tool": require_string(qa, "tool", "manifest.qa"),
        "visual_qa_browser": require_string(qa, "browser", "manifest.qa"),
        "data_qa_canonical_dossiers": mounted["canonical_dossiers"],
        "data_qa_edition_routes": mounted["edition_routes"],
        "data_qa_real_visuals": mounted["real_visuals"],
        "data_qa_fallback_visuals": mounted["fallback_visuals"],
        "assembled_release": require_string(manifest, "release", "manifest"),
        "assembled_public_files": mounted["public_files"],
        "assembled_frontend_sha256_prefix": mounted["frontend_sha256"][:12],
    }


def render_receipt(values: dict[str, str]) -> str:
    return f"""# FCMO AI Newsletter — ready to publish

Release: **{values['release_display']}**

Status: **release-ready after the assembler, curated-localization gate, and DOM verification pass.**

Receipt measurement: **{values['receipt_measurement']}** (UTC), using `{values['qa_tool']}` and {values['qa_browser']}.

The private repository is staged so the publication release is assembled from a frozen, hash-verified overlay at deploy time. `main` contains only the public base tree, release package, validation tooling, legal/publication scaffold, and deployment workflow needed for the public site. No private research state is required at build time.

## Final manual action

Change the repository visibility from **Private** to **Public**.

The Pages workflow listens for GitHub's `public` repository event and will reconstruct, validate, upload, and deploy the frozen release to:

**https://fcmo-ai.github.io/FCMO-AI-Newsletter/**

Do not manually copy a different `index.html` into Pages or bypass the release validator; the frozen release identity below is the canonical candidate.

## Release identity

- Release manifest schema: `{values['manifest_schema']}`
- Release: `{values['release']}`
- Front-end SHA-256: `{values['frontend_sha256']}`
- Release archive SHA-256: `{values['archive_sha256']}`
- Encoded release payload SHA-256: `{values['payload_sha256']}`
- {values['part_count']}/{values['part_count']} release payload parts present; payload and archive checked by SHA-256
- {values['public_files']} public files after assembly
- {values['canonical_dossiers']} canonical dossiers
- {values['stable_dossier_routes']} stable dossier routes
- {values['edition_routes']} frozen edition routes
- {values['real_visuals']} vetted sourced story visuals + {values['fallback_visuals']} embedded editorial fallbacks

## Verification receipts

### Visual/browser QA

Measured on **{values['receipt_measurement']}** with **{values['qa_browser']}** by `{values['qa_tool']}`:

- {values['route_viewport_checks']} route/viewport checks at {values['viewport_widths']}
- {values['javascript_failures']} JavaScript failures
- {values['overflow_failures']} overflow failures
- {values['blank_route_failures']} blank-route failures
- {values['legal_dom_checks']} legal DOM checks
- {values['i18n_dom_checks']} curated-i18n DOM checks

### Release/data QA

The final assembler validates, before deployment:

- exact release archive and front-end hashes;
- archive path/symlink safety;
- required human and machine-readable public files;
- {values['canonical_dossiers']} dossier identifiers and stable human routes;
- {values['edition_routes']} edition JSON/HTML routes;
- JSON, JSONL, RSS, and sitemap parsing;
- agent discovery/query contracts (`{values['agent_schema']}`, `{values['agent_query_contract']}`);
- final {values['real_visuals']}/{values['fallback_visuals']} story-media policy;
- credential-like strings and personal-mailbox leakage;
- remote JavaScript and remote stylesheet dependencies while allowing legitimate canonical/feed/discovery links and vetted story imagery;
- deterministic build-manifest generation.

The release assembler and curated-localization gate were rerun; the assembled public candidate measures:

`FCMO AI Newsletter {values['release']} READY: {values['public_files']} public files; index {values['frontend_sha256'][:12]}…`

## GitHub Actions note

GitHub Actions jobs in the private repository have repeatedly failed **before a runner or workflow step was assigned** (empty runner and step metadata). The same release logic has therefore been executed directly against the frozen artifacts as an independent pre-publication gate. This is not a recorded application/test failure.

Once the repository is public, public GitHub-hosted Actions should be able to run the prepared deployment workflow normally.

## GitHub Pages note

GitHub currently reports Pages as not yet enabled while the repository is private. The deployment workflow is already present and listens for the visibility-change event. If GitHub requires first-time Pages activation for this organization, the only platform-side follow-up is:

**Settings → Pages → Source: GitHub Actions**, then **Actions → Deploy FCMO AI Newsletter → Run workflow**.

GitHub's standard workflow token cannot pre-enable first-time Pages for a private repository because that operation requires separate administration/Pages permission.
"""


def receipt_values(text: str) -> dict[str, str]:
    patterns = {
        "release_display": r"^Release: \*\*(?P<value>.+)\*\*$",
        "receipt_measurement": r"^Receipt measurement: \*\*(?P<value>[^*]+)\*\* \(UTC\), using `[^`]+` and .+\.$",
        "qa_tool": r"^Receipt measurement: \*\*[^*]+\*\* \(UTC\), using `(?P<value>[^`]+)` and .+\.$",
        "qa_browser": r"^Receipt measurement: \*\*[^*]+\*\* \(UTC\), using `[^`]+` and (?P<value>.+)\.$",
        "manifest_schema": r"^- Release manifest schema: `(?P<value>[^`]+)`$",
        "release": r"^- Release: `(?P<value>[^`]+)`$",
        "frontend_sha256": r"^- Front-end SHA-256: `(?P<value>[0-9a-f]+)`$",
        "archive_sha256": r"^- Release archive SHA-256: `(?P<value>[0-9a-f]+)`$",
        "payload_sha256": r"^- Encoded release payload SHA-256: `(?P<value>[0-9a-f]+)`$",
        "part_count": r"^- (?P<value>\d+)/\d+ release payload parts present; payload and archive checked by SHA-256$",
        "public_files": r"^- (?P<value>\d+) public files after assembly$",
        "canonical_dossiers": r"^- (?P<value>\d+) canonical dossiers$",
        "stable_dossier_routes": r"^- (?P<value>\d+) stable dossier routes$",
        "edition_routes": r"^- (?P<value>\d+) frozen edition routes$",
        "real_visuals": r"^- (?P<value>\d+) vetted sourced story visuals \+ \d+ embedded editorial fallbacks$",
        "fallback_visuals": r"^- \d+ vetted sourced story visuals \+ (?P<value>\d+) embedded editorial fallbacks$",
        "viewport_widths": r"^- \d+ route/viewport checks at (?P<value>.+)$",
        "route_viewport_checks": r"^- (?P<value>\d+) route/viewport checks at .+$",
        "javascript_failures": r"^- (?P<value>\d+) JavaScript failures$",
        "overflow_failures": r"^- (?P<value>\d+) overflow failures$",
        "blank_route_failures": r"^- (?P<value>\d+) blank-route failures$",
        "legal_dom_checks": r"^- (?P<value>\d+) legal DOM checks$",
        "i18n_dom_checks": r"^- (?P<value>\d+) curated-i18n DOM checks$",
        "agent_schema": r"^- agent discovery/query contracts \(`(?P<value>[^`]+)`, `[^`]+`\);$",
        "agent_query_contract": r"^- agent discovery/query contracts \(`[^`]+`, `(?P<value>[^`]+)`\);$",
        "visual_receipt_measurement": r"^Measured on \*\*(?P<value>[^*]+)\*\* with \*\*[^*]+\*\* by `[^`]+`:$",
        "visual_qa_tool": r"^Measured on \*\*[^*]+\*\* with \*\*[^*]+\*\* by `(?P<value>[^`]+)`:$",
        "visual_qa_browser": r"^Measured on \*\*[^*]+\*\* with \*\*(?P<value>[^*]+)\*\* by `[^`]+`:$",
        "data_qa_canonical_dossiers": r"^- (?P<value>\d+) dossier identifiers and stable human routes;$",
        "data_qa_edition_routes": r"^- (?P<value>\d+) edition JSON/HTML routes;$",
        "data_qa_real_visuals": r"^- final (?P<value>\d+)/\d+ story-media policy;$",
        "data_qa_fallback_visuals": r"^- final \d+/(?P<value>\d+) story-media policy;$",
        "assembled_release": r"^`FCMO AI Newsletter (?P<value>[^ ]+) READY: \d+ public files; index [0-9a-f]+…`$",
        "assembled_public_files": r"^`FCMO AI Newsletter [^ ]+ READY: (?P<value>\d+) public files; index [0-9a-f]+…`$",
        "assembled_frontend_sha256_prefix": r"^`FCMO AI Newsletter [^ ]+ READY: \d+ public files; index (?P<value>[0-9a-f]+)…`$",
    }
    values: dict[str, str] = {}
    for field, pattern in patterns.items():
        matches = re.findall(pattern, text, flags=re.MULTILINE)
        if len(matches) != 1:
            raise ValueError(f"receipt has {len(matches)} readable value(s) for {field}, expected one")
        values[field] = matches[0]
    full_part_match = re.search(
        r"^- (?P<left>\d+)/(?P<right>\d+) release payload parts present; payload and archive checked by SHA-256$",
        text,
        flags=re.MULTILINE,
    )
    if not full_part_match or full_part_match["left"] != full_part_match["right"]:
        raise ValueError("receipt payload-part numerator and denominator must match")
    return values


def check_receipt(expected: dict[str, str]) -> None:
    try:
        actual = receipt_values(RECEIPT_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"ready receipt check FAILED: {exc}") from exc
    differences = [
        f"{field}: receipt={actual.get(field)!r}, assembled={value!r}"
        for field, value in expected.items()
        if actual.get(field) != value
    ]
    if differences:
        raise SystemExit("ready receipt check FAILED:\n- " + "\n- ".join(differences))
    print(
        "ready receipt check OK: "
        f"{expected['public_files']} public files; index {expected['frontend_sha256'][:12]}..."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare measured receipt values without rewriting it")
    args = parser.parse_args(argv)
    try:
        values = measured_values()
        if args.check:
            check_receipt(values)
        else:
            RECEIPT_PATH.write_text(render_receipt(values), encoding="utf-8", newline="\n")
            print(
                "ready receipt generated: "
                f"{values['public_files']} public files; index {values['frontend_sha256'][:12]}..."
            )
    except (OSError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ready receipt build FAILED: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
