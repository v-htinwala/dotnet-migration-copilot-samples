#!/usr/bin/env python3
"""
list-existing-tests.py — Map Java source files to existing test files.

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
    "node_modules", ".git", ".svn", "target", "build", "out",
    ".gradle", ".idea", ".vscode", "generated",
}

# Test file patterns
TEST_FILE_PATTERNS = [
    r".*Test\.java$",
    r".*Tests\.java$",
    r".*IT\.java$",
    r".*Spec\.java$",
]

# Source file patterns to skip
SKIP_FILE_PATTERNS = [
    r"package-info\.java$",
    r"module-info\.java$",
]

# Test directories
TEST_DIR_MARKERS = ["src/test", "test", "tests"]


def is_test_file(name: str) -> bool:
    """Check if a filename is a test file."""
    return any(re.match(p, name) for p in TEST_FILE_PATTERNS)


def classify_test_type(name: str) -> str:
    """Classify a test file as 'unit' or 'integration' based on naming convention."""
    if re.match(r".*IT\.java$", name):
        return "integration"
    return "unit"


def is_skip_file(filepath: str) -> bool:
    """Check if a file should be skipped."""
    return any(re.search(p, filepath) for p in SKIP_FILE_PATTERNS)


def is_in_test_dir(rel_path: str) -> bool:
    """Check if a path is within a test directory."""
    normalized = rel_path.replace("\\", "/").lower()
    return any(marker in normalized for marker in TEST_DIR_MARKERS)


def find_test_files(module_path: Path) -> list[dict[str, str]]:
    """Find all test files in the module."""
    test_files = []

    for java_file in module_path.rglob("*.java"):
        rel_parts = java_file.relative_to(module_path).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue

        if is_test_file(java_file.name):
            rel_path = str(java_file.relative_to(module_path)).replace("\\", "/")
            test_files.append({
                "file": rel_path,
                "name": java_file.stem,
                "absolutePath": str(java_file),
                "testType": classify_test_type(java_file.name),
            })

    return test_files


def find_source_files(module_path: Path) -> list[dict[str, str]]:
    """Find all non-test source files in the module."""
    source_files = []

    for java_file in module_path.rglob("*.java"):
        rel_parts = java_file.relative_to(module_path).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue

        rel_path = str(java_file.relative_to(module_path)).replace("\\", "/")

        # Skip test files
        if is_test_file(java_file.name):
            continue
        # Skip files in test directories
        if is_in_test_dir(rel_path):
            continue
        # Skip config/info files
        if is_skip_file(rel_path):
            continue

        source_files.append({
            "file": rel_path,
            "name": java_file.stem,
            "absolutePath": str(java_file),
        })

    return source_files


def find_corresponding_test(
    source: dict[str, str],
    test_files: list[dict[str, str]],
    module_path: Path,
) -> list[dict[str, str]]:
    """Find all corresponding test files for a source file (unit + integration)."""
    stem = source["name"]

    # Generate candidate test names
    candidates = [f"{stem}Test", f"{stem}Tests", f"{stem}IT", f"{stem}Spec"]

    # Collect all matching test files
    matches: list[dict[str, str]] = []
    matched_names: set[str] = set()

    # Check test files for matches
    for test in test_files:
        if test["name"] in candidates and test["name"] not in matched_names:
            matches.append(test)
            matched_names.add(test["name"])

    # Also check mirrored path: src/main/java/... -> src/test/java/...
    src_path = source["file"]
    if "src/main/java/" in src_path:
        for candidate_name in candidates:
            if candidate_name in matched_names:
                continue
            mirrored = src_path.replace("src/main/java/", "src/test/java/")
            mirrored = mirrored.rsplit("/", 1)[0] + f"/{candidate_name}.java"
            mirrored_path = module_path / mirrored
            if mirrored_path.exists():
                test_type = classify_test_type(f"{candidate_name}.java")
                matches.append({
                    "file": mirrored,
                    "name": candidate_name,
                    "absolutePath": str(mirrored_path),
                    "testType": test_type,
                })
                matched_names.add(candidate_name)

    return matches


def main():
    parser = argparse.ArgumentParser(
        description="Map Java source files to existing test files."
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
            # Primary test file (prefer unit test)
            unit_tests = [t for t in test_matches if t.get("testType") == "unit"]
            integration_tests = [t for t in test_matches if t.get("testType") == "integration"]
            primary = unit_tests[0] if unit_tests else test_matches[0]

            mapping: dict[str, Any] = {
                "sourceFile": source["file"],
                "testFile": primary["file"],
                "testType": primary.get("testType", "unit"),
                "hasExistingTest": True,
            }

            # Add integration test file if it exists separately
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
