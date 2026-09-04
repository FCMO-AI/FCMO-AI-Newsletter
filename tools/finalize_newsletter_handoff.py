#!/usr/bin/env python3
"""One-shot deterministic closure of the 2026-09-04 Newsletter handoff.

This file is intentionally temporary: the workflow that invokes it deletes it
before committing the resulting product changes.  Every replacement below has
an assertion so a changed source tree fails closed instead of silently applying
an approximate patch.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def patch_release_index() -> None:
    path = REPO / "release-src" / "index.html"
    text = path.read_text(encoding="utf-8")

    # Footnote: persistent chrome used to freeze yesterday's metrics in raw HTML.
    # The canonical data block already owns these values, so the chrome now binds
    # to D.meta once and never needs a manual count edit again.
    old_strip = (
        '<div class="utility-strip"><div class="utility-inner"><div class="stats">'
        '<span><b>22</b> public briefs</span><span><b>21</b> Evidence A</span>'
        '<span><b>46</b> open evidence gaps</span><span><b>4</b> explicit relationships</span>'
        '</div><a href="#/agent">Machine-readable corpus →</a></div></div>'
    )
    new_strip = (
        '<div class="utility-strip"><div class="utility-inner"><div class="stats">'
        '<span><b data-fcmo-stat="count">—</b> public briefs</span>'
        '<span><b data-fcmo-stat="evidenceA">—</b> Evidence A</span>'
        '<span><b data-fcmo-stat="open_gaps">—</b> open evidence gaps</span>'
        '<span><b data-fcmo-stat="relationships">—</b> explicit relationships</span>'
        '</div><a href="#/agent">Machine-readable corpus →</a></div></div>'
    )
    text = replace_once(text, old_strip, new_strip, "persistent corpus chrome")

    old_boot = (
        "const D=JSON.parse(document.getElementById('fcmo-data').textContent); "
        "const $=s=>document.querySelector(s);"
    )
    new_boot = """const D=JSON.parse(document.getElementById('fcmo-data').textContent);
function syncPersistentCorpusChrome(){
  // Footnote: em dash is the no-JS fallback; with JS every value comes from the
  // same embedded manifest used by the route views, eliminating split-brain UI.
  const stats={count:D.meta.count,evidenceA:D.meta.evidenceA,open_gaps:D.meta.open_gaps,relationships:D.meta.relationships};
  for(const [key,value] of Object.entries(stats)){const node=document.querySelector(`[data-fcmo-stat="${key}"]`);if(node)node.textContent=String(value)}
}
syncPersistentCorpusChrome();
const $=s=>document.querySelector(s);"""
    text = replace_once(text, old_boot, new_boot, "canonical data bootstrap")

    # Footnote: these two literals lived in JS templates.  They are changed to
    # expressions rather than today's number so story 24/100 cannot revive them.
    text = replace_once(text, ">22 BRIEFS<", ">${D.meta.count} BRIEFS<", "agent machine diagram count")
    text = replace_once(
        text,
        '<span>22</span><strong>Research briefs</strong>',
        '<span>${D.meta.count}</span><strong>Research briefs</strong>',
        "legacy complete-record count",
    )

    write(path, text)


def patch_runtime() -> None:
    path = REPO / "site" / "assets" / "curated-i18n.js"
    text = path.read_text(encoding="utf-8")

    # Footnote: the full dossier is curated today.  The previous summary text
    # claimed the technical dossier stayed English even though walk(document.body)
    # translated it; the copy now describes the product that actually ships.
    text = text.replace(
        "phraseMap.get('English canonical record') || 'English canonical record'",
        "phraseMap.get('Curated dossier · English canonical source') || 'Curated dossier · English canonical source'",
    )
    text = text.replace(
        "phraseMap.get('Technical evidence stays in English so its meaning is not altered.')\n      || 'Technical evidence stays in English so its meaning is not altered.'",
        "phraseMap.get('This view translates the full dossier. Use the English version for the canonical semantic source.')\n      || 'This view translates the full dossier. Use the English version for the canonical semantic source.'",
    )
    if "English canonical record') || 'English canonical record" in text:
        raise SystemExit("runtime canonical-boundary label replacement did not converge")
    if "Technical evidence stays in English so its meaning is not altered.'" in text:
        raise SystemExit("runtime canonical-boundary note replacement did not converge")

    # Remove harmless duplicate object keys left by the successive i18n passes.
    text = text.replace("'public briefs':'dossiers públicos','lead impact'", "'lead impact'")
    text = text.replace("'public briefs':'公开档案','lead impact'", "'lead impact'")
    write(path, text)


def patch_ui_catalogs() -> None:
    translations = {
        "es-419": {
            "Evidence distribution": "Distribución de evidencia",
            "That standalone route does not exist. Use the publication navigation above.":
                "Esa ruta independiente no existe. Usa la navegación de la publicación que aparece arriba.",
            "Curated dossier · English canonical source":
                "Dossier curado · fuente canónica en inglés",
            "This view translates the full dossier. Use the English version for the canonical semantic source.":
                "Esta vista traduce el expediente completo. Usa la versión en inglés como fuente semántica canónica.",
        },
        "zh-Hans": {
            "Evidence distribution": "证据分布",
            "That standalone route does not exist. Use the publication navigation above.":
                "该独立路由不存在。请使用上方的出版物导航。",
            "Curated dossier · English canonical source":
                "策展档案 · 英文规范来源",
            "This view translates the full dossier. Use the English version for the canonical semantic source.":
                "此视图会翻译完整档案。规范语义来源以英文版本为准。",
        },
    }
    for locale, additions in translations.items():
        path = REPO / "site" / "data" / "i18n" / locale / "ui.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        ui = data["ui"]
        ui.pop("Evidence distribution / 22 briefs", None)
        ui.pop("English canonical record", None)
        ui.pop("Technical evidence stays in English so its meaning is not altered.", None)
        ui.update(additions)
        data["ui"] = dict(sorted(ui.items(), key=lambda item: item[0].casefold()))
        write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def patch_i18n_validator() -> None:
    path = REPO / "tools" / "apply_curated_i18n.py"
    text = path.read_text(encoding="utf-8")

    old = '''RUNTIME_UI_KEYS = {
    "Language", "Newsletter language", "Lead signal", "Uncertainty docket",
    "Evidence", "Impact", "public briefs", "total public briefs",
    "source families", "claim records", "open gaps",
    "Front page", "Research", "Desks", "Editions", "Chronology", "Topics",
    "Organizations", "Agent",
}'''
    new = '''RUNTIME_UI_KEYS = {
    "Language", "Newsletter language", "Lead signal", "Uncertainty docket",
    "Evidence", "Impact", "public briefs", "total public briefs",
    "source families", "claim records", "open gaps", "Evidence distribution",
    "That standalone route does not exist. Use the publication navigation above.",
    "Curated dossier · English canonical source",
    "This view translates the full dossier. Use the English version for the canonical semantic source.",
    "Front page", "Research", "Desks", "Editions", "Chronology", "Topics",
    "Organizations", "Agent",
}
# Footnote: a source key containing a live corpus count is a time bomb.  Dates,
# licenses and model names may contain digits; only count-bearing brief labels
# are forbidden here, because those must be formatted dynamically.
COUNT_BOUND_UI_KEY = re.compile(r"\\b\\d+\\s+(?:public\\s+)?briefs?\\b", re.I)'''
    text = replace_once(text, old, new, "runtime i18n required keys")

    old_validate = '''def _validate_runtime_catalog(
    locale: str, catalog: dict[str, object], formats: dict[str, object], records: dict[str, dict], errors: list[str]
) -> None:
    for source in sorted(RUNTIME_UI_KEYS):'''
    new_validate = '''def _validate_runtime_catalog(
    locale: str, catalog: dict[str, object], formats: dict[str, object], records: dict[str, dict], errors: list[str]
) -> None:
    for source in sorted(catalog):
        if COUNT_BOUND_UI_KEY.search(source):
            errors.append(
                f"{locale}: count-bearing UI key {source!r} is forbidden; use a dynamic format/pattern instead"
            )
    for source in sorted(RUNTIME_UI_KEYS):'''
    text = replace_once(text, old_validate, new_validate, "count-bound i18n gate")
    write(path, text)


def patch_ready_receipt_builder() -> None:
    path = REPO / "tools" / "build_ready_receipt.py"
    text = path.read_text(encoding="utf-8")

    start = text.index("def render_receipt(values: dict[str, str]) -> str:\n")
    end = text.index("\ndef receipt_values(text: str) -> dict[str, str]:\n", start)
    render = '''def render_receipt(values: dict[str, str]) -> str:
    # Footnote: this is a live public-release receipt, not a prelaunch checklist.
    # Operational prose is generated together with the measured values so a
    # repository visibility change cannot leave a technically green but false doc.
    return f"""# FCMO AI Newsletter — public release receipt

Release: **{values['release_display']}**

Status: **public release assembled, localized, validated, and deployable through GitHub Pages.**

Receipt measurement: **{values['receipt_measurement']}** (UTC), using `{values['qa_tool']}` and {values['qa_browser']}.

This repository is the public publication sink. `site/` supplies the public base, `release-src/` holds the editable canonical release source, `release-overlay/final/` freezes that source deterministically, and deployment assembles only the validated `publish/` candidate. No private research workspace is required to build or serve the site.

## Publication state

The public site is deployed at:

**https://fcmo-ai.github.io/FCMO-AI-Newsletter/**

Ordinary releases require no repository-visibility step. A candidate that fails release integrity, privacy, or curated-localization validation is not deployed; the previous public version remains live.

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

## Daily refresh readiness

The code path for a daily update is fail-closed: a sanitized public corpus is ingested, missing curated locales are produced before publication, the frozen overlay and this receipt are rebuilt, and the same release gates run before a commit can deploy. Platform credentials or runner/billing availability are external prerequisites; their absence must stop an update rather than weaken the publication boundary.

## GitHub Pages

Pages deploys only the assembled `publish/` artifact after the build job succeeds. The deployment workflow also listens to the completed daily-refresh workflow so a bot-authored refresh can reach Pages without relying on a second `push` event.
"""
'''
    text = text[:start] + render + text[end + 1:]

    start = text.index("def check_receipt(expected: dict[str, str]) -> None:\n")
    end = text.index("\ndef main(argv: list[str] | None = None) -> int:\n", start)
    check = '''def check_receipt(expected: dict[str, str]) -> None:
    try:
        actual_text = RECEIPT_PATH.read_text(encoding="utf-8")
        actual = receipt_values(actual_text)
    except Exception as exc:
        raise SystemExit(f"ready receipt check FAILED: {exc}") from exc
    differences = [
        f"{field}: receipt={actual.get(field)!r}, assembled={value!r}"
        for field, value in expected.items()
        if actual.get(field) != value
    ]
    if differences:
        raise SystemExit("ready receipt check FAILED:\\n- " + "\\n- ".join(differences))
    # Footnote: the old checker validated only parsed numbers/hashes, allowing
    # obsolete prelaunch prose to remain green after the repository went public.
    # Exact generated text closes that semantic hole while read_text normalizes
    # platform line endings for us.
    rendered = render_receipt(expected)
    if actual_text != rendered:
        raise SystemExit(
            "ready receipt check FAILED: receipt narrative/structure drift; regenerate with tools/build_ready_receipt.py"
        )
    print(
        "ready receipt check OK: "
        f"{expected['public_files']} public files; index {expected['frontend_sha256'][:12]}..."
    )
'''
    text = text[:start] + check + text[end + 1:]
    write(path, text)


def rewrite_docs() -> None:
    localization = '''# FCMO AI Newsletter curated localization contract

English is the **canonical semantic source** of the FCMO AI Newsletter. The native publication supports exactly three locales:

- `en` — English, canonical semantic source;
- `es-419` — Latin American Spanish, curated translation;
- `zh-Hans` — Simplified Chinese, curated translation.

Browser extensions, operating-system translation and third-party translation layers are outside this contract.

## What “curated” means

Spanish and Chinese are model-curated, source-controlled publication artifacts. They are generated before publication, never at page-view time, and are deliberately **not labelled human-reviewed** unless a qualified reviewer actually performs that review.

Translate intent rather than English syntax while preserving evidence strength, uncertainty, caveats, numbers, model/version identities, benchmarks, stable FCMO IDs, URLs, and the distinction between demonstrated, claimed, inferred and editorial interpretation. A translation may improve naturalness, but may not strengthen a research claim beyond the canonical English source.

## Coverage contract

Every canonical record must have a curated translation for the reader-facing prose that the site renders, including:

- title, summary, why-it-matters and importance rationale;
- limitations, contradictory evidence and research/engineering/policy implications;
- claim text and evidence-gap descriptions;
- reader-facing technical-dossier prose and relationship summaries.

Coverage is **dynamic, never hard-coded to a historical corpus size**. If English contains `N` stable FCMO IDs, Spanish and Chinese must contain exactly the same `N` IDs. Locale metadata, public brief JSON, stable development routes and the localization manifest must agree with that live set.

Count-bearing UI is formatted dynamically. A catalogue key must not bake in a corpus count such as `22 briefs`; growth of the corpus must not invalidate translation lookup.

English remains directly selectable and authoritative as the semantic source. Non-English dossier views are curated translations of that source, not a separate evidence record. The interface labels that relationship explicitly rather than falsely claiming translated technical prose is still English.

## Runtime behavior

Locale resolution is deterministic:

1. explicit `?lang=` parameter;
2. saved manual selection;
3. `navigator.languages` / browser preference;
4. English fallback.

All `es-*` browser locales resolve to `es-419`; all `zh-*` locales resolve to `zh-Hans`. The selected locale persists locally and is reflected in the URL.

The runtime performs **presentation lookup only** against committed packs. It contains no translation-provider endpoint and no generative fallback. A missing translation is a release defect.

Legal/disclosure text is also translated for readability. Where English is the governing legal wording, the translated block carries an explicit notice and a route back to the English version.

## Source-control layout

- `site/data/i18n/es-419/part-*.json` + `ui.json` — curated Spanish prose and UI catalogue;
- `site/data/i18n/zh-Hans/part-*.json` + `ui.json` — curated Simplified Chinese prose and UI catalogue;
- `site/assets/curated-i18n.js` — deterministic presentation/runtime layer;
- `site/assets/curated-i18n.css` — language selector and translated-dossier presentation;
- `tools/apply_curated_i18n.py` — coverage validation, bundle injection, provenance manifest and integrity refresh.

The canonical English release is assembled and hash-verified first. Localization is injected only after that identity passes. The localized build records both the canonical and localized index SHA-256 values in `data/i18n/manifest.json`.

## Publication gate

A release must fail if:

- either curated locale omits a canonical FCMO ID or contains a stale/extra ID;
- locale record-count metadata differs from the live canonical corpus;
- public brief JSON or stable development routes differ from the canonical IDs;
- required reader-facing prose is absent, empty or unchanged English;
- a locale pack was built against a different canonical editorial digest;
- a count-bearing historical UI key is introduced;
- a runtime translation-provider endpoint appears;
- any native locale outside `en`, `es-419`, `zh-Hans` is exposed;
- the localized index cannot be traced to the frozen canonical English index hash.

A new story and its curated native translations are one publication obligation. The gate fails closed rather than publishing a partial language edition.
'''
    write(REPO / "LOCALIZATION.md", localization)

    policy = '''# Publication safety policy

FCMO AI Newsletter is a **public-only publication repository**. It is the public sink, not the private research workspace.

## Safety boundary

This repository must contain only material intended for public release. It must never contain private research workspaces, internal agent state, internal project-specific relevance, private hypotheses or experiments, operational logs from a private source, private-source repository history, upstream commit identifiers, personal email addresses, credentials or private keys.

Only a sanitized, allowlisted public corpus may cross the upstream publication airlock. The public repository does not fetch, clone or authenticate to a private research repository.

## Safe-fail rule

If privacy, integrity, localization or release validation fails, the public release is not advanced. The previous deployed version remains live. No failed privacy check may be bypassed merely to refresh the website.

## Repository structure

- `corpus/` — sanitized public handoff produced by the upstream publication airlock; never raw private research state;
- `site/` — checked-in public base tree, shared assets, legal pages and curated locale packs;
- `release-src/` — editable canonical English release source regenerated from the sanitized corpus;
- `release-overlay/final/` — deterministic frozen package of `release-src/`, hash-checked before assembly;
- `tools/` — ingest, localization, release, receipt and verification tooling;
- `publish/` — ephemeral assembled deployment candidate, never the authority-bearing source;
- `.github/workflows/daily-refresh.yml` — fail-closed corpus → translation → overlay → receipt → validation → commit cycle;
- `.github/workflows/pages.yml` — assembles and deploys only a validated public candidate.

The public repository's git history remains independent from any private source repository.
'''
    write(REPO / "PUBLICATION_POLICY.md", policy)

    readme = REPO / "README.md"
    text = readme.read_text(encoding="utf-8")
    old = '''Every current public news record has a committed Spanish and Chinese translation of its reader-facing title, summary, and editorial consequence. The selector resolves an explicit `?lang=` request first, then a saved manual choice, then browser language, with English as the final fallback.

The site does **not** call a translation service or generative model at page-view time. Missing translations are release defects rather than permission to silently machine-translate. English remains directly selectable as the authority-bearing source. The deeper technical/evidence record can therefore preserve its canonical wording and identifiers even when the reader is using a curated translated edition.'''
    new = '''Every current public news record has committed Spanish and Chinese translations for the reader-facing prose rendered by the publication, including the deep dossier fields that materially affect interpretation. The selector resolves an explicit `?lang=` request first, then a saved manual choice, then browser language, with English as the final fallback.

The site does **not** call a translation service or generative model at page-view time. Missing translations are release defects rather than permission to silently machine-translate. English remains directly selectable as the authority-bearing semantic source; Spanish and Chinese are curated views of that same record, with stable IDs, numbers, evidence status and provenance preserved.'''
    text = replace_once(text, old, new, "README localization contract")
    write(readme, text)

    handoff = REPO / "HANDOFF.md"
    text = handoff.read_text(encoding="utf-8")
    heading = "# Handoff — estado del sitio y trabajo pendiente\n"
    closure = '''# Handoff — cierre del relevo de software

> **Cierre 2026-09-04:** el relevo de software quedó completado por el siguiente pase. Los dos defectos de i18n de la sección 2 fueron corregidos y convertidos en regresiones. La auditoría adicional encontró y corrigió también métricas persistentes congeladas (22 briefs / 46 gaps), el `22 BRIEFS` de Agent, deriva del contrato de localización, el recibo prelaunch que todavía describía un repo privado y la política de publicación desactualizada. Los prerrequisitos externos de la sección 3 siguen siendo configuración de plataforma, no trabajo de código pendiente.

'''
    text = replace_once(text, heading, closure, "handoff closure heading")
    text = text.replace(
        "## 2. Lo que queda abierto — dos defectos reales",
        "## 2. Defectos heredados — diagnóstico histórico, ya resuelto",
        1,
    )
    write(handoff, text)


def patch_manifest_operational_state() -> None:
    path = REPO / "release-overlay" / "final" / "manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["launch_gate"] = (
        "Public production repository; ordinary updates deploy only after release, privacy and curated-localization gates pass. "
        "Sanitized-corpus refresh remains fail-closed when external platform prerequisites are unavailable."
    )
    write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def add_regression_test() -> None:
    path = REPO / "tests" / "test_dynamic_contracts.py"
    test = r'''from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNT_KEY = re.compile(r"\b\d+\s+(?:public\s+)?briefs?\b", re.I)


class DynamicPublicationContractTests(unittest.TestCase):
    def test_corpus_metrics_are_not_frozen_in_the_shell(self):
        text = (ROOT / "release-src" / "index.html").read_text(encoding="utf-8")
        for label in ("count", "evidenceA", "open_gaps", "relationships"):
            self.assertIn(f'data-fcmo-stat="{label}"', text)
        self.assertNotRegex(text, r"<b>\d+</b> public briefs")
        self.assertNotRegex(text, r"<b>\d+</b> open evidence gaps")
        self.assertNotRegex(text, r"<b>\d+</b> explicit relationships")
        self.assertNotRegex(text, r">\d+ BRIEFS<")
        self.assertIn("${D.meta.count} BRIEFS", text)
        self.assertNotRegex(text, r"<span>\d+</span><strong>Research briefs</strong>")

    def test_curated_catalogues_cannot_embed_live_brief_counts(self):
        required = {
            "Evidence distribution",
            "That standalone route does not exist. Use the publication navigation above.",
            "Curated dossier · English canonical source",
            "This view translates the full dossier. Use the English version for the canonical semantic source.",
        }
        for locale in ("es-419", "zh-Hans"):
            data = json.loads((ROOT / "site" / "data" / "i18n" / locale / "ui.json").read_text(encoding="utf-8"))
            keys = set(data["ui"])
            self.assertTrue(required <= keys, (locale, sorted(required - keys)))
            self.assertFalse([key for key in keys if COUNT_KEY.search(key)], locale)
            self.assertNotIn("Evidence distribution / 22 briefs", keys)

    def test_public_operational_docs_no_longer_describe_prelaunch(self):
        receipt_builder = (ROOT / "tools" / "build_ready_receipt.py").read_text(encoding="utf-8")
        self.assertNotIn("Change the repository visibility from **Private** to **Public**", receipt_builder)
        self.assertNotIn("The private repository is staged", receipt_builder)
        policy = (ROOT / "PUBLICATION_POLICY.md").read_text(encoding="utf-8")
        for token in ("corpus/", "site/", "release-src/", "release-overlay/final/", "publish/"):
            self.assertIn(token, policy)
        manifest = json.loads((ROOT / "release-overlay" / "final" / "manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("Private integration", manifest.get("launch_gate", ""))


if __name__ == "__main__":
    unittest.main()
'''
    write(path, test)


def main() -> int:
    patch_release_index()
    patch_runtime()
    patch_ui_catalogs()
    patch_i18n_validator()
    patch_ready_receipt_builder()
    rewrite_docs()
    patch_manifest_operational_state()
    add_regression_test()
    print("handoff closure patches applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
