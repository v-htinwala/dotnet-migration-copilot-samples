#!/usr/bin/env python3
"""
list-existing-tests.py — Map JS/TS source files to existing test files.

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
    "node_modules", ".git", ".svn", "dist", "build", "out",
    ".next", ".nuxt", ".output", "coverage", ".cache", ".turbo",
    ".parcel-cache", "generated", "__generated__",
}

# Source extensions
SOURCE_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}

# Test file patterns
TEST_FILE_PATTERNS = [
    r".*\.(test|spec)\.(js|jsx|ts|tsx|mjs|cjs)$",
]

# Source file patterns to skip
SKIP_FILE_PATTERNS = [
    r"\.d\.ts$",
    r"\.min\.js$",
    r"\.config\.(js|ts|mjs|cjs)$",
]

# Test directory markers
TEST_DIR_MARKERS = ["__tests__", "__test__"]

# Integration test indicators
INTEGRATION_TEST_PATTERNS = [
    r"\.integration\.(test|spec)\.",
    r"\.e2e\.(test|spec)\.",
    r"\.it\.(test|spec)\.",
]


def is_test_file(name: str) -> bool:
    """Check if a filename is a test file."""
    return any(re.match(p, name) for p in TEST_FILE_PATTERNS)


def classify_test_type(filepath: str) -> str:
    """Classify whether a test file is unit or integration."""
    normalized = filepath.replace("\\", "/").lower()
    for pattern in INTEGRATION_TEST_PATTERNS:
        if re.search(pattern, normalized):
            return "integration"
    # Check directory-based classification
    if "/integration/" in normalized or "/e2e/" in normalized:
        return "integration"
    return "unit"


def is_in_test_dir(rel_path: str) -> bool:
    """Check if a path is within a test directory."""
    normalized = rel_path.replace("\\", "/").lower()
    return any(marker in normalized for marker in TEST_DIR_MARKERS)


def is_skip_file(filepath: str) -> bool:
    """Check if a file should be skipped."""
    return any(re.search(p, filepath) for p in SKIP_FILE_PATTERNS)


def find_test_files(module_path: Path) -> list[dict[str, str]]:
    """Find all test files in the module."""
    test_files = []

    for ext in SOURCE_EXTENSIONS:
        for f in module_path.rglob(f"*{ext}"):
            rel_parts = f.relative_to(module_path).parts
            if any(part in SKIP_DIRS for part in rel_parts):
                continue

            rel_path = str(f.relative_to(module_path)).replace("\\", "/")

            if is_test_file(f.name) or is_in_test_dir(rel_path):
                test_files.append({
                    "file": rel_path,
                    "name": f.stem,
                    "absolutePath": str(f),
                })

    return test_files


def find_source_files(module_path: Path) -> list[dict[str, str]]:
    """Find all non-test source files in the module."""
    source_files = []

    for ext in SOURCE_EXTENSIONS:
        for f in module_path.rglob(f"*{ext}"):
            rel_parts = f.relative_to(module_path).parts
            if any(part in SKIP_DIRS for part in rel_parts):
                continue

            rel_path = str(f.relative_to(module_path)).replace("\\", "/")

            if is_test_file(f.name):
                continue
            if is_in_test_dir(rel_path):
                continue
            if is_skip_file(rel_path):
                continue

            source_files.append({
                "file": rel_path,
                "name": f.stem,
                "absolutePath": str(f),
            })

    return source_files


def find_corresponding_test(
    source: dict[str, str],
    test_files: list[dict[str, str]],
    module_path: Path,
) -> dict[str, str] | None:
    """Find the corresponding test file for a source file."""
    stem = source["name"]
    source_dir = str(Path(source["file"]).parent)

    # Generate candidate test names
    candidates_names = [
        f"{stem}.test",
        f"{stem}.spec",
    ]

    # Check test files for a match by name
    for test in test_files:
        if test["name"] in candidates_names:
            return test

    # Check colocated test files (same directory)
    source_path = Path(source["file"])
    for ext in [".ts", ".tsx", ".js", ".jsx"]:
        for suffix in [".test", ".spec"]:
            candidate_name = f"{stem}{suffix}{ext}"
            candidate_path = source_path.parent / candidate_name
            candidate_rel = str(candidate_path).replace("\\", "/")
            for test in test_files:
                if test["file"] == candidate_rel:
                    return test

    # Check __tests__ directory
    for ext in [".ts", ".tsx", ".js", ".jsx"]:
        candidate_path = source_path.parent / "__tests__" / f"{stem}{ext}"
        candidate_rel = str(candidate_path).replace("\\", "/")
        for test in test_files:
            if test["file"] == candidate_rel:
                return test

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Map JS/TS source files to existing test files."
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
        if impacted_filter and source["file"] not in impacted_filter:
            continue

        test = find_corresponding_test(source, test_files, module_path)
        mapping_entry: dict[str, Any] = {
            "sourceFile": source["file"],
            "testFile": test["file"] if test else None,
            "hasExistingTest": test is not None,
        }
        if test:
            mapping_entry["testType"] = classify_test_type(test["file"])
        mappings.append(mapping_entry)

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
