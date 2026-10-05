from __future__ import annotations

import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from .common import GateResult, fail, rel

CODE = "AGENT_LAYER"
ID = re.compile(r"FCMO-[A-F0-9]{12}\Z")


def _validate(value, schema, at="$", problems=None):
    problems = problems if problems is not None else []
    kind = schema.get("type")
    valid = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool}
    if kind in valid and not isinstance(value, valid[kind]):
        problems.append(f"{at}: expected {kind}"); return problems
    if kind == "object":
        for required in schema.get("required", []):
            if required not in value: problems.append(f"{at}: missing {required}")
        for key, sub in schema.get("properties", {}).items():
            if key in value: _validate(value[key], sub, f"{at}.{key}", problems)
    if kind == "array":
        for index, item in enumerate(value): _validate(item, schema.get("items", {}), f"{at}[{index}]", problems)
    if kind == "string" and schema.get("format") == "uri":
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc: problems.append(f"{at}: invalid URI {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        problems.append(f"{at}: value {value!r} is outside enum")
    return problems


def _root_path(root: Path, value: str, origin: str, base: str) -> Path | None:
    parsed = urlsplit(value)
    if parsed.scheme and parsed.netloc and f"{parsed.scheme}://{parsed.netloc}" != origin:
        return None
    path = unquote(parsed.path)
    if base != "/":
        if not path.startswith(base): return None
        path = path[len(base):]
    else: path = path.lstrip("/")
    parts = Path(path).parts
    if ".." in parts: return None
    target = root.joinpath(*parts)
    if path.endswith("/") or not target.suffix: target = target / "index.html"
    return target


def _walk_urls(obj):
    if isinstance(obj, dict):
        for value in obj.values(): yield from _walk_urls(value)
    elif isinstance(obj, list):
        for value in obj: yield from _walk_urls(value)
    elif isinstance(obj, str) and (obj.startswith(("https://", "http://", "./"))):
        yield obj


def check(root: Path) -> GateResult:
    problems: list[str] = []
    agent_file = root / "agent.json"
    api = root / "api/v1"
    # run_all is also exercised against intentionally partial, hand-built gate
    # fixtures. A completed publication always has the route manifest written
    # by PaperBuilder; apply this layer's required-file checks at that boundary.
    if (not agent_file.is_file() and not api.exists()
            and not ((root / "data/routes.json").is_file() and (root / "data/stories.v2.json").is_file())):
        return GateResult(CODE, 0)
    try:
        agent = json.loads(agent_file.read_text(encoding="utf-8"))
        index = json.loads((api / "index.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(CODE, [f"required discovery/index file missing or invalid: {exc}"])
    origin, base = "", "/"
    parsed_base = urlsplit(agent.get("base_url", ""))
    if parsed_base.scheme and parsed_base.netloc:
        origin = f"{parsed_base.scheme}://{parsed_base.netloc}"
        base = parsed_base.path if parsed_base.path.endswith("/") else parsed_base.path.rsplit("/", 1)[0] + "/"
    story_ids = set()
    for path in root.rglob("*.html"):
        text = path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r'data-story-id="(FCMO-[A-F0-9]{12})"', text)
        if match: story_ids.add(match.group(1))
    index_ids = set()
    try:
        for raw in index["stories"]:
            match = re.search(r"/stories/(FCMO-[A-F0-9]{12})\.json\Z", raw)
            if match:
                index_ids.add(match.group(1))
                if not (api / "stories" / f"{match.group(1)}.json").is_file(): problems.append(f"API index story target is missing: {match.group(1)}")
        full_paths = [root / locale for locale in ("llms-full.txt", "es/llms-full.txt", "zh/llms-full.txt") if (root / locale).is_file()]
        for sid in sorted(story_ids):
            if sid not in index_ids: problems.append(f"published story {sid} is missing from API index")
            for full_path in full_paths:
                if f"`{sid}`" not in full_path.read_text(encoding="utf-8"):
                    problems.append(f"published story {sid} is missing from {rel(root, full_path)}")
            story_file = api / "stories" / f"{sid}.json"
            try: story_doc = json.loads(story_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError): story_doc = {}
            story_path = _root_path(root, story_doc.get("canonical_url", ""), origin, base)
            if story_path is None or not story_path.is_file():
                problems.append(f"published story {sid} has no HTML twin")
            markdown_path = story_path.parent.parent / (story_path.parent.name + ".md") if story_path else None
            # Story HTML routes are nested index.html files; their Markdown twins use the slug route.
            if markdown_path is None or not markdown_path.is_file():
                problems.append(f"published story {sid} has no Markdown twin")
    except (KeyError, TypeError) as exc: problems.append(f"invalid API index shape: {exc}")
    schemas = {}
    for path in (api / "schema").glob("*.schema.json"):
        try: schemas[path.name.replace(".schema.json", "")] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc: problems.append(f"invalid schema {rel(root, path)}: {exc}")
    paths = [(api / "index.json", "index"), (api / "corrections.json", "corrections"), (api / "search-index.json", "search-index"), (api / "openapi.json", "openapi")]
    for subdir, kind in (("stories", "story"), ("editions", "edition"), ("topics", "topic"), ("organizations", "organization")):
        paths.extend((p, kind) for p in (api / subdir).glob("*.json"))
    checked = 0
    for path, kind in paths:
        try: payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"invalid API file {rel(root, path)}: {exc}"); continue
        schema = schemas.get(kind)
        if not schema: problems.append(f"schema missing for {kind}"); continue
        for issue in _validate(payload, schema): problems.append(f"{rel(root, path)} {issue}")
        canonical_url = payload.get("canonical_url") if isinstance(payload, dict) else None
        if canonical_url:
            target = _root_path(root, canonical_url, origin, base)
            if target is None or not target.is_file(): problems.append(f"{rel(root, path)} canonical URL does not resolve inside build: {canonical_url}")
        checked += 1
    for filename in ("agent.json", "api/v1/openapi.json"):
        try: document = json.loads((root / filename).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"{filename} invalid: {exc}"); continue
        for url in _walk_urls(document):
            if filename.endswith("openapi.json") and url.startswith("./"):
                if not (api / url[2:]).is_file():
                    problems.append(f"{filename} URL does not resolve inside build: {url}")
                continue
            if urlsplit(url).scheme not in {"http", "https"}: continue
            target = _root_path(root, url, origin, base)
            # External rights references are descriptive metadata, not publication routes.
            if target is None and urlsplit(url).netloc != parsed_base.netloc: continue
            if target is None or target.is_file(): continue
            path = urlsplit(url).path
            if "{" in path or "<" in path:
                prefix = re.split(r"[<{]", path, maxsplit=1)[0]
                local_prefix = _root_path(root, prefix, origin, base)
                if local_prefix and (local_prefix.parent.exists() or local_prefix.exists()): continue
            problems.append(f"{filename} URL does not resolve inside build: {url}")
    fail(CODE, problems)
    return GateResult(CODE, checked)


def main(argv=None) -> int:
    import argparse
    import sys
    from .common import GateFailure
    parser = argparse.ArgumentParser(); parser.add_argument("root", type=Path); args = parser.parse_args(argv)
    try: result = check(args.root)
    except GateFailure as exc:
        print(f"{exc.code} FAIL", file=sys.stderr)
        for problem in exc.problems: print(f"- {problem}", file=sys.stderr)
        return 1
    print(f"{result.code} PASS ({result.checked} API files)")
    return 0


if __name__ == "__main__": raise SystemExit(main())
