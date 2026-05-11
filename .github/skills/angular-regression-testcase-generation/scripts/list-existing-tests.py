#!/usr/bin/env python3
"""
list-existing-tests.py — Map Angular source files to existing spec files.

Usage:
    python list-existing-tests.py <module-path> [--output <file>]

Discovers existing test files and maps them to their corresponding source files.
Outputs test-map.json with source -> test file mappings.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", ".svn", "dist", "coverage",
    ".angular", ".nyc_output", "tmp", "e2e",
}

# Test file patterns
TEST_FILE_PATTERNS = [
    r".*\.spec\.ts$",
    r".*\.test\.ts$",
    r".*\.integration\.spec\.ts$",
]

# Source file patterns to skip
SKIP_FILE_PATTERNS = [
    r"polyfills\.ts$",
    r"main\.ts$",
    r"test\.ts$",
    r"environment.*\.ts$",
    r".*\.module\.ts$",
    r".*\.routing\.module\.ts$",
    r"index\.ts$",
]

# Test directories
TEST_DIR_MARKERS = ["__tests__", "__test__"]


def is_test_file(name: str) -> bool:
    """Check if a filename is a test file."""
    return any(re.match(p, name) for p in TEST_FILE_PATTERNS)


def classify_test_type(name: str) -> str:
    """Classify a test file as 'unit' or 'integration' based on naming convention."""
    if re.match(r".*\.integration\.spec\.ts$", name):
        return "integration"
    return "unit"


def is_skip_file(filepath: str) -> bool:
    """Check if a file should be skipped."""
    return any(re.search(p, filepath) for p in SKIP_FILE_PATTERNS)


def find_test_files(module_path: Path) -> list[dict[str, str]]:
    """Find all test files in the module."""
    test_files = []

    for ts_file in module_path.rglob("*.ts"):
        rel_parts = ts_file.relative_to(module_path).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue

        if is_test_file(ts_file.name):
            rel_path = str(ts_file.relative_to(module_path)).replace("\\", "/")
            test_files.append({
                "file": rel_path,
                "name": ts_file.stem,
                "absolutePath": str(ts_file),
                "testType": classify_test_type(ts_file.name),
            })

    return test_files


def find_source_files(module_path: Path) -> list[dict[str, str]]:
    """Find all non-test TypeScript source files in the module."""
    source_files = []

    for ts_file in module_path.rglob("*.ts"):
        rel_parts = ts_file.relative_to(module_path).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue

        rel_path = str(ts_file.relative_to(module_path)).replace("\\", "/")

        # Skip test files
        if is_test_file(ts_file.name):
            continue
        # Skip config/bootstrap files
        if is_skip_file(rel_path):
            continue

        source_files.append({
            "file": rel_path,
            "name": ts_file.stem,
            "absolutePath": str(ts_file),
        })

    return source_files


def find_corresponding_test(
    source: dict[str, str],
    test_files: list[dict[str, str]],
    module_path: Path,
) -> list[dict[str, str]]:
    """Find all corresponding test files for a source file (unit + integration)."""
    stem = source["name"]
    source_dir = str(Path(source["file"]).parent)

    # Generate candidate test file names
    # e.g., user.service.ts -> user.service.spec.ts, user.service.test.ts, user.service.integration.spec.ts
    candidates = [
        f"{stem}.spec",       # user.service.spec.ts
        f"{stem}.test",       # user.service.test.ts
        f"{stem}.integration.spec",  # user.service.integration.spec.ts
    ]

    matches: list[dict[str, str]] = []
    matched_names: set[str] = set()

    for test in test_files:
        test_stem = test["name"]
        test_dir = str(Path(test["file"]).parent)

        # Check if test stem matches any candidate
        if test_stem in candidates and test_stem not in matched_names:
            # Prefer tests in the same directory
            matches.append(test)
            matched_names.add(test_stem)

    # If no matches found by name, try co-located file check
    if not matches:
        source_file = Path(source["file"])
        # Angular convention: source.ts -> source.spec.ts (same directory)
        spec_name = f"{stem}.spec.ts"
        spec_path = source_file.parent / spec_name
        full_spec = module_path / spec_path
        if full_spec.exists():
            rel_spec = str(spec_path).replace("\\", "/")
            matches.append({
                "file": rel_spec,
                "name": f"{stem}.spec",
                "absolutePath": str(full_spec),
                "testType": "unit",
            })

    return matches


def main():
    parser = argparse.ArgumentParser(
        description="Map Angular source files to existing spec files."
    )
    parser.add_argument("module_path", help="Path to the module directory")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument(
        "--impacted-files",
        help="Path to impact.json to filter only impacted source files",
    )
    args = parser.parse_args()

    module_path = Path(args.module_path).resolve()
    if not module_path.exists():
        print(f"Error: Path '{module_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Find all test and source files
    test_files = find_test_files(module_path)
    source_files = find_source_files(module_path)

    # Load impacted files filter if provided
    impacted_filter = None
    if args.impacted_files:
        impact_path = Path(args.impacted_files)
        if impact_path.exists():
            with open(impact_path, encoding="utf-8") as f:
                impact_data = json.load(f)
            impacted_filter = {
                f["file"] for f in impact_data.get("impactedFiles", [])
            }

    # Build mapping
    mappings: list[dict[str, Any]] = []
    for source in source_files:
        # Skip if not in impacted set
        if impacted_filter and source["file"] not in impacted_filter:
            continue

        test_matches = find_corresponding_test(source, test_files, module_path)
        if test_matches:
            unit_tests = [t for t in test_matches if t.get("testType") == "unit"]
            integration_tests = [t for t in test_matches if t.get("testType") == "integration"]
            primary = unit_tests[0] if unit_tests else test_matches[0]

            mapping: dict[str, Any] = {
                "sourceFile": source["file"],
                "testFile": primary["file"],
                "testType": primary.get("testType", "unit"),
                "hasExistingTest": True,
            }

            if integration_tests:
                mapping["integrationTestFile"] = integration_tests[0]["file"]

            mappings.append(mapping)
        else:
            mappings.append({
                "sourceFile": source["file"],
                "testFile": None,
                "testType": None,
                "hasExistingTest": False,
            })

    # Sort: untested files first for prioritization
    mappings.sort(key=lambda x: (x["hasExistingTest"], x["sourceFile"]))

    result = {
        "module": module_path.name,
        "totalSourceFiles": len(source_files),
        "totalTestFiles": len(test_files),
        "mappedCount": sum(1 for m in mappings if m["hasExistingTest"]),
        "unmappedCount": sum(1 for m in mappings if not m["hasExistingTest"]),
        "mappings": mappings,
    }

    output = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
