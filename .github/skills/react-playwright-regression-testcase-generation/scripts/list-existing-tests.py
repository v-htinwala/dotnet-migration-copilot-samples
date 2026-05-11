#!/usr/bin/env python3
"""
list-existing-tests.py — Map React/TypeScript source files to existing Playwright test files.

Usage:
    python list-existing-tests.py <module-path> [--output <file>]

Discovers existing Playwright test files and maps them to their corresponding
source files. Outputs test-map.json with source -> test file mappings.
Supports *.spec.ts, *.spec.tsx, *.e2e.ts, *.e2e.tsx, *.ct.ts, *.ct.tsx patterns
and e2e/ or tests/ directory conventions.
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
    "playwright-report", "test-results",
}

# Source file extensions
SOURCE_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx"}

# Playwright test file patterns
PLAYWRIGHT_TEST_PATTERNS = [
    r".*\.(spec|e2e)\.(ts|tsx|js|jsx)$",
    r".*\.ct\.(ts|tsx|js|jsx)$",
]

# Also check for test files in standard test directories
TEST_DIR_NAMES = {"e2e", "tests", "__tests__"}

# Source file patterns to skip
SKIP_FILE_PATTERNS = [
    r"\.d\.ts$",
    r"\.config\.\w+$",
    r"\.stories\.\w+$",
    r"\.styled\.\w+$",
]


def is_playwright_test_file(name: str, rel_path: str = "") -> bool:
    """Check if a filename is a Playwright test file."""
    if any(re.match(p, name) for p in PLAYWRIGHT_TEST_PATTERNS):
        return True
    # Check if it's in an e2e/ or tests/ directory and has .spec or .e2e
    parts = rel_path.replace("\\", "/").split("/")
    if any(part in TEST_DIR_NAMES for part in parts):
        if re.match(r".*\.(spec|e2e|ct)\.(ts|tsx|js|jsx)$", name):
            return True
    return False


def is_any_test_file(filepath: str) -> bool:
    """Check if a file is any kind of test file (Playwright, Jest, etc.)."""
    return bool(re.match(
        r".*\.(test|spec|e2e|ct)\.(ts|tsx|js|jsx)$|.*__tests__/.*\.(ts|tsx|js|jsx)$",
        filepath,
    ))


def classify_test_type(filepath: str) -> str:
    """Classify a Playwright test file as 'e2e' or 'component'."""
    name = Path(filepath).name
    if re.match(r".*\.ct\.(ts|tsx|js|jsx)$", name):
        return "component"
    if re.match(r".*\.e2e\.(ts|tsx|js|jsx)$", name):
        return "e2e"
    if re.match(r".*\.spec\.(ts|tsx|js|jsx)$", name):
        # Check directory context
        parts = filepath.replace("\\", "/").split("/")
        if "e2e" in parts or "tests" in parts:
            return "e2e"
        return "e2e"  # Default to e2e for spec files in Playwright context
    return "e2e"


def is_skip_file(filepath: str) -> bool:
    """Check if a file should be skipped."""
    return any(re.search(p, filepath) for p in SKIP_FILE_PATTERNS)


def find_test_files(module_path: Path) -> list[dict[str, str]]:
    """Find all Playwright test files in the project."""
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

        if is_playwright_test_file(src_file.name, rel_path):
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

        # Skip any test files
        if is_any_test_file(rel_path):
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


def strip_test_suffix(name: str) -> str:
    """Remove test-related suffixes from a test file stem.

    E.g. 'UserProfile.spec' -> 'UserProfile'
         'orders.e2e' -> 'orders'
         'Header.ct' -> 'Header'
    """
    name = re.sub(r"\.(spec|e2e|ct)$", "", name)
    return name


def find_corresponding_test(
    source: dict[str, str],
    test_files: list[dict[str, str]],
    module_path: Path,
) -> list[dict[str, str]]:
    """Find all corresponding Playwright test files for a source file."""
    stem = source["name"]
    source_file = source["file"]
    source_dir = str(Path(source_file).parent)

    matches: list[dict[str, str]] = []
    matched_files: set[str] = set()

    for test in test_files:
        test_stem = strip_test_suffix(test["name"])
        test_dir = str(Path(test["file"]).parent)

        # Direct name match: Component.spec.ts matches Component.tsx
        if test_stem.lower() == stem.lower() and test["file"] not in matched_files:
            matches.append(test)
            matched_files.add(test["file"])
            continue

        # Kebab-case match: user-profile.spec.ts -> UserProfile.tsx
        kebab_stem = re.sub(r"(?<!^)(?=[A-Z])", "-", stem).lower()
        if test_stem.lower() == kebab_stem and test["file"] not in matched_files:
            matches.append(test)
            matched_files.add(test["file"])
            continue

        # Check e2e/ or tests/ directory matches
        if test_dir.startswith("e2e/") or test_dir.startswith("tests/"):
            if test_stem.lower() == stem.lower() and test["file"] not in matched_files:
                matches.append(test)
                matched_files.add(test["file"])

        # Check __tests__ directory
        if "__tests__" in test_dir:
            parent_of_tests = test_dir.replace("__tests__", "").rstrip("/")
            if parent_of_tests == source_dir and test_stem.lower() == stem.lower():
                if test["file"] not in matched_files:
                    matches.append(test)
                    matched_files.add(test["file"])

    return matches


def main():
    parser = argparse.ArgumentParser(
        description="Map React/TypeScript source files to existing Playwright test files."
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
            e2e_tests = [t for t in test_matches if t.get("testType") == "e2e"]
            component_tests = [t for t in test_matches if t.get("testType") == "component"]
            primary = e2e_tests[0] if e2e_tests else test_matches[0]

            mapping: dict[str, Any] = {
                "sourceFile": source["file"],
                "testFile": primary["file"],
                "testType": primary.get("testType", "e2e"),
                "hasExistingTest": True,
            }

            if component_tests:
                mapping["componentTestFile"] = component_tests[0]["file"]

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
