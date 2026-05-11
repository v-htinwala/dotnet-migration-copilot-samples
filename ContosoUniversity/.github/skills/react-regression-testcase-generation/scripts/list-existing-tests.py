#!/usr/bin/env python3
"""
list-existing-tests.py — Map React/TypeScript source files to existing test files.

Usage:
    python list-existing-tests.py <module-path> [--output <file>]

Discovers existing test files and maps them to their corresponding source files.
Outputs test-map.json with source -> test file mappings.
Supports *.test.tsx, *.test.ts, *.spec.tsx, *.spec.ts and __tests__/ patterns.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", ".svn", "dist", "build", ".next", "out",
    "coverage", ".cache", ".turbo", ".vercel", "__snapshots__",
}

# Source file extensions
SOURCE_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx"}

# Test file patterns
TEST_FILE_PATTERNS = [
    r".*\.(test|spec)\.(ts|tsx|js|jsx)$",
]

# __tests__ directory pattern
TESTS_DIR_PATTERN = r"__tests__"

# Source file patterns to skip
SKIP_FILE_PATTERNS = [
    r"\.d\.ts$",
    r"\.config\.\w+$",
    r"\.stories\.\w+$",
    r"\.styled\.\w+$",
]


def is_test_file(name: str) -> bool:
    """Check if a filename is a test file."""
    return any(re.match(p, name) for p in TEST_FILE_PATTERNS)


def is_in_tests_dir(rel_path: str) -> bool:
    """Check if a path is within a __tests__ directory."""
    return "__tests__" in rel_path.replace("\\", "/")


def classify_test_type(filepath: str) -> str:
    """Classify a test file as 'unit' or 'integration' based on naming convention."""
    name = Path(filepath).name
    if re.match(r".*\.integration\.(test|spec)\.(ts|tsx|js|jsx)$", name):
        return "integration"
    if re.match(r".*\.e2e\.(test|spec)\.(ts|tsx|js|jsx)$", name):
        return "integration"
    return "unit"


def is_skip_file(filepath: str) -> bool:
    """Check if a file should be skipped."""
    return any(re.search(p, filepath) for p in SKIP_FILE_PATTERNS)


def find_test_files(module_path: Path) -> list[dict[str, str]]:
    """Find all test files in the project."""
    test_files = []

    for src_file in module_path.rglob("*"):
        if not src_file.is_file():
            continue
        if src_file.suffix not in SOURCE_EXTENSIONS:
            continue

        rel_parts = src_file.relative_to(module_path).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue

        rel_path = str(src_file.relative_to(module_path)).replace("\\", "/")

        if is_test_file(src_file.name) or is_in_tests_dir(rel_path):
            test_files.append({
                "file": rel_path,
                "name": src_file.stem,
                "absolutePath": str(src_file),
                "testType": classify_test_type(rel_path),
            })

    return test_files


def find_source_files(module_path: Path) -> list[dict[str, str]]:
    """Find all non-test source files in the project."""
    source_files = []

    for src_file in module_path.rglob("*"):
        if not src_file.is_file():
            continue
        if src_file.suffix not in SOURCE_EXTENSIONS:
            continue

        rel_parts = src_file.relative_to(module_path).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue

        rel_path = str(src_file.relative_to(module_path)).replace("\\", "/")

        # Skip test files
        if is_test_file(src_file.name):
            continue
        # Skip files in __tests__ directories
        if is_in_tests_dir(rel_path):
            continue
        # Skip config/info files
        if is_skip_file(rel_path):
            continue

        source_files.append({
            "file": rel_path,
            "name": src_file.stem,
            "absolutePath": str(src_file),
        })

    return source_files


def source_stem_without_ext(name: str) -> str:
    """Get the stem without common suffixes like .test, .spec."""
    # Remove double extension patterns
    name = re.sub(r"\.(test|spec)$", "", name)
    return name


def find_corresponding_test(
    source: dict[str, str],
    test_files: list[dict[str, str]],
    module_path: Path,
) -> list[dict[str, str]]:
    """Find all corresponding test files for a source file."""
    stem = source["name"]
    source_file = source["file"]
    source_dir = str(Path(source_file).parent)

    # Generate candidate test patterns
    # e.g., UserList -> UserList.test.tsx, UserList.spec.tsx, UserList.test.ts, etc.
    candidate_names = set()
    for test_suffix in [".test", ".spec"]:
        candidate_names.add(f"{stem}{test_suffix}")

    matches: list[dict[str, str]] = []
    matched_files: set[str] = set()

    for test in test_files:
        test_stem = source_stem_without_ext(test["name"])
        test_dir = str(Path(test["file"]).parent)

        # Direct name match: Component.test.tsx matches Component.tsx
        if test_stem == stem and test["file"] not in matched_files:
            # Prefer co-located tests (same directory or __tests__ sibling)
            matches.append(test)
            matched_files.add(test["file"])
            continue

        # Check __tests__ directory: src/components/__tests__/Button.test.tsx -> src/components/Button.tsx
        if "__tests__" in test_dir:
            parent_of_tests = test_dir.replace("__tests__", "").rstrip("/")
            if parent_of_tests == source_dir and test_stem == stem:
                if test["file"] not in matched_files:
                    matches.append(test)
                    matched_files.add(test["file"])

    return matches


def main():
    parser = argparse.ArgumentParser(
        description="Map React/TypeScript source files to existing test files."
    )
    parser.add_argument("module_path", help="Path to the project directory")
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
