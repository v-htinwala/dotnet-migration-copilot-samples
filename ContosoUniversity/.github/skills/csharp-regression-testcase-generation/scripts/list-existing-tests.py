#!/usr/bin/env python3
"""
list-existing-tests.py — Map C# source files to existing test files.

Usage:
    python list-existing-tests.py <solution-path> [--output <file>]

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
    "node_modules", ".git", ".svn", "bin", "obj", "out",
    ".vs", ".idea", ".vscode", "Migrations", "Generated",
    "TestResults", "packages",
}

# Test file patterns
TEST_FILE_PATTERNS = [
    r".*Tests?\.cs$",
]

# Test project directory patterns
TEST_PROJECT_PATTERNS = [
    r"\.Tests[/\\]",
    r"\.Test[/\\]",
    r"\.UnitTests[/\\]",
    r"\.IntegrationTests[/\\]",
]

# Integration test project patterns
INTEGRATION_PROJECT_PATTERNS = [
    r"\.IntegrationTests[/\\]",
]

# Source file patterns to skip
SKIP_FILE_PATTERNS = [
    r"\.Designer\.cs$",
    r"\.g\.cs$",
    r"\.generated\.cs$",
    r"AssemblyInfo\.cs$",
    r"GlobalUsings\.cs$",
    r"Program\.cs$",
    r"Startup\.cs$",
]


def is_test_file(name: str) -> bool:
    """Check if a filename is a test file."""
    return any(re.match(p, name) for p in TEST_FILE_PATTERNS)


def is_in_test_project(rel_path: str) -> bool:
    """Check if a path is within a test project."""
    normalized = rel_path.replace("\\", "/")
    return any(re.search(p.replace("\\\\", "/"), normalized) for p in TEST_PROJECT_PATTERNS)


def classify_test_type(rel_path: str, name: str) -> str:
    """Classify a test file as 'unit' or 'integration' based on naming and path."""
    normalized = rel_path.replace("\\", "/")
    if any(re.search(p.replace("\\\\", "/"), normalized) for p in INTEGRATION_PROJECT_PATTERNS):
        return "integration"
    if "IntegrationTest" in name or "IntegrationTests" in name:
        return "integration"
    return "unit"


def is_skip_file(filepath: str) -> bool:
    """Check if a file should be skipped."""
    return any(re.search(p, filepath) for p in SKIP_FILE_PATTERNS)


def find_test_files(solution_path: Path) -> list[dict[str, str]]:
    """Find all test files in the solution."""
    test_files = []

    for cs_file in solution_path.rglob("*.cs"):
        rel_parts = cs_file.relative_to(solution_path).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue

        rel_path = str(cs_file.relative_to(solution_path)).replace("\\", "/")

        if is_test_file(cs_file.name) or is_in_test_project(rel_path):
            test_files.append({
                "file": rel_path,
                "name": cs_file.stem,
                "absolutePath": str(cs_file),
                "testType": classify_test_type(rel_path, cs_file.stem),
            })

    return test_files


def find_source_files(solution_path: Path) -> list[dict[str, str]]:
    """Find all non-test source files in the solution."""
    source_files = []

    for cs_file in solution_path.rglob("*.cs"):
        rel_parts = cs_file.relative_to(solution_path).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue

        rel_path = str(cs_file.relative_to(solution_path)).replace("\\", "/")

        if is_test_file(cs_file.name):
            continue
        if is_in_test_project(rel_path):
            continue
        if is_skip_file(rel_path):
            continue

        source_files.append({
            "file": rel_path,
            "name": cs_file.stem,
            "absolutePath": str(cs_file),
        })

    return source_files


def find_corresponding_test(
    source: dict[str, str],
    test_files: list[dict[str, str]],
    solution_path: Path,
) -> list[dict[str, str]]:
    """Find all corresponding test files for a source file (unit + integration)."""
    stem = source["name"]

    # Generate candidate test names
    candidates = [f"{stem}Tests", f"{stem}Test", f"{stem}IntegrationTests"]

    # Collect all matching test files
    matches: list[dict[str, str]] = []
    matched_names: set[str] = set()

    # Check test files for a match
    for test in test_files:
        if test["name"] in candidates and test["name"] not in matched_names:
            matches.append(test)
            matched_names.add(test["name"])

    # Check mirrored project: MyProject/Services/UserService.cs
    #                       -> MyProject.Tests/Services/UserServiceTests.cs
    source_path = Path(source["file"])
    source_parts = source_path.parts

    if len(source_parts) >= 2:
        project_name = source_parts[0]

        for test_pattern in [".Tests", ".Test", ".UnitTests", ".IntegrationTests"]:
            test_project = project_name + test_pattern
            for candidate_name in candidates:
                if candidate_name in matched_names:
                    continue
                relative_dir = "/".join(source_parts[1:-1])
                if relative_dir:
                    mirrored = f"{test_project}/{relative_dir}/{candidate_name}.cs"
                else:
                    mirrored = f"{test_project}/{candidate_name}.cs"

                mirrored_path = solution_path / mirrored
                if mirrored_path.exists():
                    test_type = classify_test_type(mirrored, candidate_name)
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
        description="Map C# source files to existing test files."
    )
    parser.add_argument("solution_path", help="Path to the .NET solution directory")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument(
        "--impacted-files",
        help="Path to impact.json to filter only impacted source files",
    )
    args = parser.parse_args()

    solution_path = Path(args.solution_path).resolve()
    if not solution_path.exists():
        print(f"Error: Path '{solution_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    test_files = find_test_files(solution_path)
    source_files = find_source_files(solution_path)

    impacted_filter = None
    if args.impacted_files:
        impact_path = Path(args.impacted_files)
        if impact_path.exists():
            with open(impact_path, encoding="utf-8") as f:
                impact_data = json.load(f)
            impacted_filter = {
                f["file"] for f in impact_data.get("impactedFiles", [])
            }

    mappings: list[dict[str, Any]] = []
    for source in source_files:
        if impacted_filter and source["file"] not in impacted_filter:
            continue

        test_matches = find_corresponding_test(source, test_files, solution_path)
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

    mappings.sort(key=lambda x: (x["hasExistingTest"], x["sourceFile"]))

    result = {
        "solution": solution_path.name,
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
