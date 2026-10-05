#!/usr/bin/env python3
"""Standard-library JSON Schema validator for the newsroom contracts.

Implements the subset of JSON Schema draft 2020-12 that ``contracts/*.schema.json``
use, with two deliberate differences from the specification:

* ``format`` is an assertion, not an annotation (``date-time``, ``date``, ``uri``).
* Schemas are checked strictly: an unknown keyword is a schema error, so a typo
  such as ``"requried"`` can never silently disable a rule. Keys starting with
  ``x-`` are extension annotations, except ``x-unique-by`` which asserts that the
  named property is unique across the objects of an array.

Only local references (``#`` and ``#/...`` JSON pointers) are supported, so every
contract is self-contained.

Usage::

    validate.py SCHEMA INSTANCE [INSTANCE ...]   # .json, or .jsonl (one document per line)
    validate.py --all-fixtures                  # every entry of contracts/fixtures/MANIFEST.json
    validate.py --check-schemas                 # strict meta-check of contracts/*.schema.json

Exit codes: 0 valid, 1 invalid instance/fixture, 2 usage or schema error.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parents[2]
CONTRACTS = REPO / "contracts"
FIXTURES = CONTRACTS / "fixtures"
MANIFEST = FIXTURES / "MANIFEST.json"

ANNOTATIONS = {
    "$schema", "$id", "$comment", "$anchor", "title", "description", "examples",
    "default", "deprecated", "readOnly", "writeOnly",
}
ASSERTIONS = {
    "$ref", "$defs", "type", "enum", "const", "properties", "required",
    "additionalProperties", "patternProperties", "propertyNames", "minProperties",
    "maxProperties", "dependentRequired", "items", "prefixItems", "contains",
    "minItems", "maxItems", "uniqueItems", "minLength", "maxLength", "pattern",
    "format", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    "multipleOf", "allOf", "anyOf", "oneOf", "not", "if", "then", "else",
    "x-unique-by",
}
TYPES = {"null", "boolean", "object", "array", "number", "integer", "string"}
FORMATS = {"date-time", "date", "uri"}
DATE_TIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
)
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_REPORTED_ERRORS = 25


class SchemaError(ValueError):
    """The schema document itself is malformed or uses an unsupported keyword."""


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_documents(path: Path) -> list[tuple[str, Any]]:
    """Return ``(label, document)`` pairs; a ``.jsonl`` file yields one per line."""
    if path.suffix == ".jsonl":
        docs: list[tuple[str, Any]] = []
        with path.open(encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                if line.strip():
                    docs.append((f"{path}:{number}", json.loads(line)))
        return docs
    return [(str(path), load_json(path))]


def _pointer_escape(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _type_of(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _is_type(value: Any, expected: str) -> bool:
    actual = _type_of(value)
    if expected == "number":
        return actual in {"integer", "number"}
    if expected == "integer":
        return actual == "integer" or (actual == "number" and float(value).is_integer())
    return actual == expected


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    return _canonical(left) == _canonical(right)


def _check_format(value: str, fmt: str) -> str | None:
    if fmt == "date-time":
        if not DATE_TIME.match(value):
            return "is not an RFC 3339 date-time"
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return "is not a real calendar date-time"
    elif fmt == "date":
        if not DATE.match(value):
            return "is not a YYYY-MM-DD date"
        try:
            date.fromisoformat(value)
        except ValueError:
            return "is not a real calendar date"
    elif fmt == "uri":
        parts = urlsplit(value)
        if parts.scheme not in {"http", "https"} or not parts.netloc or " " in value:
            return "is not an absolute http(s) URI"
    return None


class Validator:
    """Validate instances against one self-contained schema document."""

    def __init__(self, schema: Any, name: str = "<schema>") -> None:
        self.root = schema
        self.name = name
        check_schema(schema, root=schema)

    def errors(self, instance: Any) -> list[str]:
        found: list[str] = []
        self._validate(self.root, instance, "", found)
        return found

    def is_valid(self, instance: Any) -> bool:
        return not self.errors(instance)

    # -- internals -----------------------------------------------------------------
    def _resolve(self, ref: str) -> Any:
        return resolve_ref(self.root, ref)

    def _validate(self, schema: Any, inst: Any, ptr: str, out: list[str]) -> None:
        where = ptr or "/"
        if schema is True:
            return
        if schema is False:
            out.append(f"{where}: no value is allowed here")
            return
        if "$ref" in schema:
            self._validate(self._resolve(schema["$ref"]), inst, ptr, out)
        if "type" in schema:
            expected = schema["type"]
            names = expected if isinstance(expected, list) else [expected]
            if not any(_is_type(inst, name) for name in names):
                out.append(f"{where}: expected type {'|'.join(names)}, got {_type_of(inst)}")
                return
        if "enum" in schema and not any(_equal(inst, option) for option in schema["enum"]):
            options = ", ".join(json.dumps(option, ensure_ascii=False) for option in schema["enum"])
            out.append(f"{where}: {json.dumps(inst, ensure_ascii=False)[:80]} is not one of [{options}]")
        if "const" in schema and not _equal(inst, schema["const"]):
            out.append(
                f"{where}: expected constant {json.dumps(schema['const'], ensure_ascii=False)}, "
                f"got {json.dumps(inst, ensure_ascii=False)[:80]}"
            )
        if isinstance(inst, str):
            self._string(schema, inst, where, out)
        elif _type_of(inst) in {"integer", "number"}:
            self._number(schema, inst, where, out)
        elif isinstance(inst, list):
            self._array(schema, inst, ptr, out)
        elif isinstance(inst, dict):
            self._object(schema, inst, ptr, out)
        for sub in schema.get("allOf", []):
            self._validate(sub, inst, ptr, out)
        if "anyOf" in schema:
            branches = [self._branch(sub, inst, ptr) for sub in schema["anyOf"]]
            if all(branches):
                out.append(f"{where}: matches none of anyOf ({self._first(branches)})")
        if "oneOf" in schema:
            branches = [self._branch(sub, inst, ptr) for sub in schema["oneOf"]]
            passing = sum(1 for branch in branches if not branch)
            if passing != 1:
                detail = self._first(branches) if passing == 0 else f"{passing} branches match"
                out.append(f"{where}: must match exactly one of oneOf ({detail})")
        if "not" in schema and not self._branch(schema["not"], inst, ptr):
            out.append(f"{where}: must not match the 'not' schema")
        if "if" in schema:
            if not self._branch(schema["if"], inst, ptr):
                if "then" in schema:
                    self._validate(schema["then"], inst, ptr, out)
            elif "else" in schema:
                self._validate(schema["else"], inst, ptr, out)

    def _branch(self, schema: Any, inst: Any, ptr: str) -> list[str]:
        sub: list[str] = []
        self._validate(schema, inst, ptr, sub)
        return sub

    @staticmethod
    def _first(branches: list[list[str]]) -> str:
        for branch in branches:
            if branch:
                return branch[0]
        return "no detail"

    @staticmethod
    def _string(schema: dict, inst: str, where: str, out: list[str]) -> None:
        length = len(inst)
        if "minLength" in schema and length < schema["minLength"]:
            out.append(f"{where}: string shorter than {schema['minLength']} characters")
        if "maxLength" in schema and length > schema["maxLength"]:
            out.append(f"{where}: string longer than {schema['maxLength']} characters ({length})")
        if "pattern" in schema and not re.search(schema["pattern"], inst):
            out.append(f"{where}: {inst[:80]!r} does not match pattern {schema['pattern']}")
        if "format" in schema:
            problem = _check_format(inst, schema["format"])
            if problem:
                out.append(f"{where}: {inst[:80]!r} {problem}")

    @staticmethod
    def _number(schema: dict, inst: float, where: str, out: list[str]) -> None:
        if "minimum" in schema and inst < schema["minimum"]:
            out.append(f"{where}: {inst} is below minimum {schema['minimum']}")
        if "maximum" in schema and inst > schema["maximum"]:
            out.append(f"{where}: {inst} is above maximum {schema['maximum']}")
        if "exclusiveMinimum" in schema and inst <= schema["exclusiveMinimum"]:
            out.append(f"{where}: {inst} must be greater than {schema['exclusiveMinimum']}")
        if "exclusiveMaximum" in schema and inst >= schema["exclusiveMaximum"]:
            out.append(f"{where}: {inst} must be less than {schema['exclusiveMaximum']}")
        if "multipleOf" in schema:
            quotient = inst / schema["multipleOf"]
            if not math.isclose(quotient, round(quotient), abs_tol=1e-9):
                out.append(f"{where}: {inst} is not a multiple of {schema['multipleOf']}")

    def _array(self, schema: dict, inst: list, ptr: str, out: list[str]) -> None:
        where = ptr or "/"
        if "minItems" in schema and len(inst) < schema["minItems"]:
            out.append(f"{where}: expected at least {schema['minItems']} items, got {len(inst)}")
        if "maxItems" in schema and len(inst) > schema["maxItems"]:
            out.append(f"{where}: expected at most {schema['maxItems']} items, got {len(inst)}")
        if schema.get("uniqueItems"):
            seen: set[str] = set()
            for item in inst:
                key = _canonical(item)
                if key in seen:
                    out.append(f"{where}: items are not unique ({key[:60]})")
                    break
                seen.add(key)
        if "x-unique-by" in schema:
            prop = schema["x-unique-by"]
            seen_values: set[str] = set()
            for index, item in enumerate(inst):
                if isinstance(item, dict) and prop in item:
                    key = _canonical(item[prop])
                    if key in seen_values:
                        out.append(f"{where}/{index}/{prop}: duplicate {prop} {key}")
                    seen_values.add(key)
        prefix = schema.get("prefixItems", [])
        for index, sub in enumerate(prefix):
            if index < len(inst):
                self._validate(sub, inst[index], f"{ptr}/{index}", out)
        if "items" in schema:
            for index in range(len(prefix), len(inst)):
                self._validate(schema["items"], inst[index], f"{ptr}/{index}", out)
        if "contains" in schema:
            if not any(not self._branch(schema["contains"], item, ptr) for item in inst):
                out.append(f"{where}: no item matches 'contains'")

    def _object(self, schema: dict, inst: dict, ptr: str, out: list[str]) -> None:
        where = ptr or "/"
        for key in schema.get("required", []):
            if key not in inst:
                out.append(f"{where}: missing required property '{key}'")
        if "minProperties" in schema and len(inst) < schema["minProperties"]:
            out.append(f"{where}: expected at least {schema['minProperties']} properties")
        if "maxProperties" in schema and len(inst) > schema["maxProperties"]:
            out.append(f"{where}: expected at most {schema['maxProperties']} properties")
        for key, needed in schema.get("dependentRequired", {}).items():
            if key in inst:
                for other in needed:
                    if other not in inst:
                        out.append(f"{where}: property '{key}' requires property '{other}'")
        properties = schema.get("properties", {})
        patterns = schema.get("patternProperties", {})
        for key, value in inst.items():
            child = f"{ptr}/{_pointer_escape(key)}"
            matched = False
            if key in properties:
                matched = True
                self._validate(properties[key], value, child, out)
            for pattern, sub in patterns.items():
                if re.search(pattern, key):
                    matched = True
                    self._validate(sub, value, child, out)
            if not matched and "additionalProperties" in schema:
                extra = schema["additionalProperties"]
                if extra is False:
                    out.append(f"{where}: property '{key}' is not allowed")
                else:
                    self._validate(extra, value, child, out)
            if "propertyNames" in schema:
                for problem in self._branch(schema["propertyNames"], key, child):
                    out.append(f"{where}: property name {key!r}: {problem.split(': ', 1)[-1]}")


def resolve_ref(root: Any, ref: str) -> Any:
    if ref == "#":
        return root
    if not ref.startswith("#/"):
        raise SchemaError(f"only local $ref values are supported, got {ref!r}")
    node = root
    for raw in ref[2:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and token in node:
            node = node[token]
        elif isinstance(node, list) and token.isdigit() and int(token) < len(node):
            node = node[int(token)]
        else:
            raise SchemaError(f"$ref {ref!r} does not resolve")
    return node


def check_schema(schema: Any, root: Any = None, path: str = "#") -> None:
    """Strictly check a schema document; raise SchemaError on the first problem."""
    root = schema if root is None else root
    if isinstance(schema, bool):
        return
    if not isinstance(schema, dict):
        raise SchemaError(f"{path}: a schema must be an object or boolean")
    for key in schema:
        if key in ANNOTATIONS or key in ASSERTIONS:
            continue
        if key.startswith("x-"):
            continue
        raise SchemaError(f"{path}: unknown or unsupported keyword {key!r}")
    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        for name in names:
            if name not in TYPES:
                raise SchemaError(f"{path}/type: unknown type {name!r}")
    if "format" in schema and schema["format"] not in FORMATS:
        raise SchemaError(f"{path}/format: unsupported format {schema['format']!r}")
    if "pattern" in schema:
        try:
            re.compile(schema["pattern"])
        except re.error as exc:
            raise SchemaError(f"{path}/pattern: {exc}") from exc
    if "required" in schema:
        if not isinstance(schema["required"], list) or not all(isinstance(k, str) for k in schema["required"]):
            raise SchemaError(f"{path}/required: must be a list of strings")
    if "enum" in schema and (not isinstance(schema["enum"], list) or not schema["enum"]):
        raise SchemaError(f"{path}/enum: must be a non-empty list")
    if "$ref" in schema:
        resolve_ref(root, schema["$ref"])
    if "x-unique-by" in schema and not isinstance(schema["x-unique-by"], str):
        raise SchemaError(f"{path}/x-unique-by: must name a property")
    for key in ("properties", "patternProperties", "$defs"):
        for name, sub in schema.get(key, {}).items():
            if key == "patternProperties":
                try:
                    re.compile(name)
                except re.error as exc:
                    raise SchemaError(f"{path}/{key}/{name}: {exc}") from exc
            check_schema(sub, root, f"{path}/{key}/{_pointer_escape(name)}")
    for key in ("additionalProperties", "items", "contains", "not", "if", "then", "else", "propertyNames"):
        if key in schema:
            check_schema(schema[key], root, f"{path}/{key}")
    for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
        if key in schema:
            if not isinstance(schema[key], list) or not schema[key]:
                raise SchemaError(f"{path}/{key}: must be a non-empty list")
            for index, sub in enumerate(schema[key]):
                check_schema(sub, root, f"{path}/{key}/{index}")


_CACHE: dict[Path, Validator] = {}


def validator_for(schema_path: Path) -> Validator:
    schema_path = schema_path.resolve()
    if schema_path not in _CACHE:
        _CACHE[schema_path] = Validator(load_json(schema_path), name=schema_path.name)
    return _CACHE[schema_path]


def validate_file(schema_path: Path, instance_path: Path) -> list[str]:
    """Validate a .json or .jsonl file; return error strings (empty when valid)."""
    validator = validator_for(schema_path)
    problems: list[str] = []
    for label, document in load_documents(instance_path):
        for error in validator.errors(document):
            problems.append(f"{label}#{error}" if label != str(instance_path) else error)
    return problems


def validate_corpus(directory: Path) -> list[str]:
    """Validate an airlocked corpus snapshot directory (airlock.json + data/developments.jsonl)."""
    problems: list[str] = []
    airlock_path = directory / "airlock.json"
    records_path = directory / "data" / "developments.jsonl"
    for required in (airlock_path, records_path):
        if not required.is_file():
            return [f"{required}: missing"]
    problems += [f"airlock.json{e}" for e in validate_file(CONTRACTS / "airlock.v2.schema.json", airlock_path)]
    problems += validate_file(CONTRACTS / "record.v2.schema.json", records_path)
    airlock = load_json(airlock_path)
    ids = [doc.get("id") for _, doc in load_documents(records_path) if isinstance(doc, dict)]
    if len(ids) != len(set(ids)):
        problems.append("data/developments.jsonl: duplicate record ids")
    if airlock.get("record_count") != len(ids):
        problems.append(f"airlock.json: record_count {airlock.get('record_count')} != {len(ids)} records")
    digest = str(airlock.get("corpus_digest", ""))
    if airlock.get("release_id") != f"newswire-{digest[:24]}":
        problems.append("airlock.json: release_id is not newswire-<corpus_digest[:24]>")
    return problems


def _fixture_files() -> set[Path]:
    return {
        path.resolve()
        for path in FIXTURES.rglob("*")
        if path.is_file() and path.name != "MANIFEST.json"
    }


def run_manifest(manifest_path: Path = MANIFEST, stream=sys.stdout) -> int:
    manifest = load_json(manifest_path)
    entries = manifest.get("fixtures", [])
    failures = 0
    covered: set[Path] = set()
    for entry in entries:
        name = entry["name"]
        path = (REPO / entry["path"]).resolve()
        expect = entry.get("expect", "valid")
        try:
            if entry.get("kind") == "corpus":
                covered.update(p.resolve() for p in path.rglob("*") if p.is_file())
                problems = validate_corpus(path)
            else:
                covered.add(path)
                problems = validate_file(REPO / entry["schema"], path)
        except (OSError, ValueError, SchemaError) as exc:
            problems = [f"cannot validate: {exc}"]
            expect = "valid"  # an unreadable fixture is always a failure
        if expect == "valid":
            ok = not problems
            detail = problems[0] if problems else ""
        else:
            wanted = entry.get("expect_error", "")
            ok = bool(problems) and any(wanted in problem for problem in problems)
            detail = "accepted but must be rejected" if not problems else (
                "" if ok else f"rejected for another reason: {problems[0]}"
            )
        failures += 0 if ok else 1
        label = "ok  " if ok else "FAIL"
        suffix = f" ({expect})" if expect != "valid" else ""
        print(f"{label} {name}{suffix}" + (f": {detail}" if not ok else ""), file=stream)
    unmanaged = sorted(str(p.relative_to(REPO)) for p in _fixture_files() - covered)
    for path in unmanaged:
        failures += 1
        print(f"FAIL unmanaged fixture {path} (add it to MANIFEST.json)", file=stream)
    total = len(entries)
    if failures:
        print(f"fixtures FAILED ({failures}/{total})", file=stream)
        return 1
    print(f"fixtures OK ({total})", file=stream)
    return 0


def check_all_schemas(stream=sys.stdout) -> int:
    failures = 0
    for path in sorted(CONTRACTS.glob("*.schema.json")):
        try:
            validator_for(path)
        except (ValueError, SchemaError) as exc:
            failures += 1
            print(f"SCHEMA ERROR {path.name}: {exc}", file=stream)
    return failures


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("schema", nargs="?", help="schema file")
    parser.add_argument("instances", nargs="*", help=".json or .jsonl instance files")
    parser.add_argument("--all-fixtures", action="store_true", help="validate every MANIFEST entry")
    parser.add_argument("--manifest", default=str(MANIFEST), help="fixture manifest path")
    parser.add_argument("--check-schemas", action="store_true", help="meta-check contracts/*.schema.json")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.all_fixtures or args.check_schemas:
        schema_failures = check_all_schemas()
        if schema_failures:
            return 2
        if args.check_schemas and not args.all_fixtures:
            count = len(list(CONTRACTS.glob("*.schema.json")))
            print(f"schemas OK ({count})")
            return 0
        return run_manifest(Path(args.manifest))

    if not args.schema or not args.instances:
        parser.print_usage(sys.stderr)
        return 2
    try:
        validator_for(Path(args.schema))
    except (OSError, ValueError, SchemaError) as exc:
        print(f"SCHEMA ERROR {args.schema}: {exc}", file=sys.stderr)
        return 2
    status = 0
    for raw in args.instances:
        path = Path(raw)
        try:
            problems = validate_file(Path(args.schema), path)
        except (OSError, ValueError) as exc:
            problems = [f"cannot read: {exc}"]
        if problems:
            status = 1
            print(f"INVALID {path}")
            for problem in problems[:MAX_REPORTED_ERRORS]:
                print(f"  {problem}")
            if len(problems) > MAX_REPORTED_ERRORS:
                print(f"  ... {len(problems) - MAX_REPORTED_ERRORS} more")
        else:
            print(f"valid {path}")
    return status


if __name__ == "__main__":
    sys.exit(main())
