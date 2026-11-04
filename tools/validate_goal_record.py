#!/usr/bin/env python3
"""Subset JSON Schema validator for LLCO goal records (draft 0.1).

Validates instances against schema/goal-record.schema.json using ONLY the
Python standard library (the sandbox has no `jsonschema` package and pip
installation is blocked). Supports exactly the keywords used by the schema:

    $ref (local "#/$defs/..." only), type (incl. type lists), enum, const,
    pattern, properties, required, additionalProperties: false, items,
    minItems, contains, allOf, if/then/else, $defs (resolution target).

LIMITATION (deliberate, honest): this is a subset validator, not a JSON
Schema implementation. Keywords outside the list above are ignored silently.
Error paths use "$" for the document root. When a real validator (e.g. the
`jsonschema` package) becomes available in this environment, replace this
script; until then it is the executable part of the schema's test evidence.

Usage:
    python3 tools/validate_goal_record.py schema/goal-record.schema.json FILE...
    python3 tools/validate_goal_record.py --selftest [ROOT]

--selftest validates the shipped fixtures: every file in
fixtures/goal-record/ must PASS, and every file in
fixtures/goal-record/invalid/ must FAIL with the expected marker substring
in its violation output (marker map below). Exit 0 on success, 1 on any
failure, 2 on usage error.
"""

import json
import os
import re
import sys

EXPECTED_INVALID_MARKERS = {
    "01-missing-coverage.json": "coverage",
    "02-purpose-confirmed-without-human-ruling.json": "human_ruling",
    "03-native-coverage-without-kind.json": "coverage_kind",
    "04-recovered-without-source.json": "source",
    "05-hypothetical-without-notice.json": "hypothetical_notice",
    "06-means-without-reason.json": "means_reason",
    "07-bad-goal-id.json": "goal_id",
}


def _type_ok(t, data):
    if t == "object":
        return isinstance(data, dict)
    if t == "array":
        return isinstance(data, list)
    if t == "string":
        return isinstance(data, str)
    if t == "number":
        return isinstance(data, (int, float)) and not isinstance(data, bool)
    if t == "boolean":
        return isinstance(data, bool)
    if t == "null":
        return data is None
    return False


def _resolve_ref(root, ref):
    if not ref.startswith("#/"):
        raise ValueError(f"only local '#/$defs/...' $ref supported, got {ref!r}")
    node = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def _validate(schema, data, path, errors, root):
    """Collect violations of `schema` against `data` into errors (list of str)."""

    if "$ref" in schema:
        _validate(_resolve_ref(root, schema["$ref"]), data, path, errors, root)

    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_type_ok(t, data) for t in types):
            errors.append(
                f"type: {path} is {type(data).__name__}, expected {schema['type']!r}"
            )
            return  # further keywords meaningless on wrong type

    if "enum" in schema and data not in schema["enum"]:
        errors.append(f"enum: {path} value {data!r} not in {schema['enum']!r}")
    if "const" in schema and data != schema["const"]:
        errors.append(
            f"const: {path} value {data!r} does not match const {schema['const']!r}"
        )
    if "pattern" in schema and isinstance(data, str):
        if not re.search(schema["pattern"], data):
            errors.append(
                f"pattern: {path} value {data!r} does not match {schema['pattern']!r}"
            )

    if isinstance(data, dict):
        for prop in schema.get("required", []):
            if prop not in data:
                errors.append(f"required: missing '{prop}' at {path}")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in data:
                if key not in props:
                    errors.append(
                        f"additionalProperties: '{key}' at {path} is not allowed"
                    )
        for key, sub in props.items():
            if key in data:
                _validate(sub, data[key], f"{path}.{key}", errors, root)

    if isinstance(data, list):
        if len(data) < schema.get("minItems", 0):
            errors.append(f"minItems: {path} has {len(data)} items, need {schema['minItems']}")
        if "items" in schema:
            for i, item in enumerate(data):
                _validate(schema["items"], item, f"{path}[{i}]", errors, root)
        if "contains" in schema:
            for item in data:
                sub_errors = []
                _validate(schema["contains"], item, f"{path}[contains]", sub_errors, root)
                if not sub_errors:
                    break
            else:
                first = sub_errors[0] if sub_errors else "contains: no item matched"
                errors.append(f"contains: no item at {path} matches; e.g. {first}")

    for sub in schema.get("allOf", []):
        _validate(sub, data, path, errors, root)

    if "if" in schema:
        cond_errors = []
        _validate(schema["if"], data, path, cond_errors, root)
        if not cond_errors:
            if "then" in schema:
                _validate(schema["then"], data, path, errors, root)
        elif "else" in schema:
            _validate(schema["else"], data, path, errors, root)


def validate_file(schema, filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    errors = []
    _validate(schema, data, "$", errors, schema)
    return errors


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2

    if argv[1] == "--selftest":
        root = argv[2] if len(argv) > 2 else "."
        schema_path = os.path.join(root, "schema", "goal-record.schema.json")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        failures = 0
        valid_dir = os.path.join(root, "fixtures", "goal-record")
        valid_files = sorted(
            f for f in os.listdir(valid_dir) if f.endswith(".json")
        )
        for name in valid_files:
            errs = validate_file(schema, os.path.join(valid_dir, name))
            if errs:
                failures += 1
                print(f"FAIL (expected PASS): {name}")
                for e in errs:
                    print(f"    {e}")
            else:
                print(f"PASS: {name}")

        invalid_dir = os.path.join(valid_dir, "invalid")
        for name in sorted(os.listdir(invalid_dir)):
            if not name.endswith(".json"):
                continue
            marker = EXPECTED_INVALID_MARKERS.get(name)
            errs = validate_file(schema, os.path.join(invalid_dir, name))
            text = " | ".join(errs)
            if not errs:
                failures += 1
                print(f"FAIL (expected FAIL): {name} unexpectedly passed")
            elif marker and marker not in text:
                failures += 1
                print(f"FAIL (marker missing): {name} expected marker {marker!r}")
                for e in errs:
                    print(f"    {e}")
            else:
                print(f"FAIL-AS-EXPECTED: {name} [{marker}] -> {errs[0]}")

        print(
            f"selftest: {len(valid_files)} valid fixtures, "
            f"{len(EXPECTED_INVALID_MARKERS)} invalid fixtures, {failures} test failures"
        )
        return 0 if failures == 0 else 1

    schema_path = argv[1]
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    failures = 0
    for filepath in argv[2:]:
        errs = validate_file(schema, filepath)
        if errs:
            failures += 1
            print(f"FAIL: {filepath}")
            for e in errs:
                print(f"    {e}")
        else:
            print(f"PASS: {filepath}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
