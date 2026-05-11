#!/usr/bin/env python3
"""
check-coverage.py — Parse JaCoCo coverage reports and check against a threshold.

Usage:
    python check-coverage.py <report-path> --format <jacoco>
                             --threshold <N> [--changed-files <json>] [--output <file>]

Supports JaCoCo XML coverage reports (Maven/Gradle).
Optionally filters coverage to only changed files.
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def parse_jacoco(report_path: Path) -> dict[str, Any]:
    """Parse JaCoCo XML coverage report."""
    tree = ET.parse(report_path)
    root = tree.getroot()

    # Overall counters
    overall_line = {"covered": 0, "missed": 0}
    overall_branch = {"covered": 0, "missed": 0}

    by_file: list[dict[str, Any]] = []
    uncovered: list[dict[str, Any]] = []

    # Process each package and class
    for package in root.findall(".//package"):
        pkg_name = package.get("name", "").replace("/", ".")

        for source_file in package.findall("sourcefile"):
            file_name = source_file.get("name", "")
            file_path = f"{pkg_name.replace('.', '/')}/{file_name}"

            file_line = {"covered": 0, "missed": 0}
            file_branch = {"covered": 0, "missed": 0}

            for counter in source_file.findall("counter"):
                counter_type = counter.get("type")
                covered = int(counter.get("covered", 0))
                missed = int(counter.get("missed", 0))

                if counter_type == "LINE":
                    file_line["covered"] += covered
                    file_line["missed"] += missed
                elif counter_type == "BRANCH":
                    file_branch["covered"] += covered
                    file_branch["missed"] += missed

            total_lines = file_line["covered"] + file_line["missed"]
            total_branches = file_branch["covered"] + file_branch["missed"]

            line_pct = (
                (file_line["covered"] / total_lines * 100)
                if total_lines > 0
                else 100.0
            )
            branch_pct = (
                (file_branch["covered"] / total_branches * 100)
                if total_branches > 0
                else 100.0
            )

            by_file.append({
                "file": file_path,
                "lineCoverage": round(line_pct, 1),
                "branchCoverage": round(branch_pct, 1),
                "linesCovered": file_line["covered"],
                "linesMissed": file_line["missed"],
            })

            overall_line["covered"] += file_line["covered"]
            overall_line["missed"] += file_line["missed"]
            overall_branch["covered"] += file_branch["covered"]
            overall_branch["missed"] += file_branch["missed"]

    # Also check top-level counters as fallback
    for counter in root.findall("counter"):
        counter_type = counter.get("type")
        covered = int(counter.get("covered", 0))
        missed = int(counter.get("missed", 0))
        if counter_type == "LINE":
            if overall_line["covered"] == 0 and overall_line["missed"] == 0:
                overall_line = {"covered": covered, "missed": missed}
        elif counter_type == "BRANCH":
            if overall_branch["covered"] == 0 and overall_branch["missed"] == 0:
                overall_branch = {"covered": covered, "missed": missed}

    total_lines = overall_line["covered"] + overall_line["missed"]
    overall_pct = (
        (overall_line["covered"] / total_lines * 100)
        if total_lines > 0
        else 0.0
    )

    # Find uncovered methods from class-level data
    for package in root.findall(".//package"):
        pkg_name = package.get("name", "").replace("/", ".")
        for cls in package.findall("class"):
            cls_name = cls.get("name", "").replace("/", ".")
            file_uncov_methods = []
            for method in cls.findall("method"):
                method_name = method.get("name", "")
                if method_name in ("<init>", "<clinit>"):
                    continue
                for counter in method.findall("counter"):
                    if counter.get("type") == "LINE":
                        m_covered = int(counter.get("covered", 0))
                        m_missed = int(counter.get("missed", 0))
                        if m_missed > 0 and m_covered == 0:
                            file_uncov_methods.append(method_name)
                        break
            if file_uncov_methods:
                uncovered.append({
                    "file": cls_name,
                    "methods": file_uncov_methods,
                })

    return {
        "overall": round(overall_pct, 1),
        "byFile": by_file,
        "uncovered": uncovered,
    }


def filter_to_changed_files(
    coverage_data: dict[str, Any],
    changed_files: list[str],
) -> dict[str, Any]:
    """Filter coverage data to only include changed files."""
    # Normalize changed file paths for matching
    changed_set = set()
    for f in changed_files:
        # Strip src/main/java/ prefix for matching against JaCoCo paths
        normalized = f.replace("\\", "/")
        if "src/main/java/" in normalized:
            normalized = normalized.split("src/main/java/", 1)[1]
        # Remove .java extension for package-based matching
        normalized_no_ext = normalized.rsplit(".java", 1)[0]
        changed_set.add(normalized)
        changed_set.add(normalized_no_ext)

    # Filter by_file entries
    filtered_by_file = []
    total_covered = 0
    total_missed = 0

    for entry in coverage_data["byFile"]:
        file_path = entry["file"]
        # Check if this file matches any changed file
        if file_path in changed_set or file_path.replace(".", "/") in changed_set:
            filtered_by_file.append(entry)
            total_covered += entry.get("linesCovered", 0)
            total_missed += entry.get("linesMissed", 0)

    total_lines = total_covered + total_missed
    filtered_overall = (
        (total_covered / total_lines * 100) if total_lines > 0 else 0.0
    )

    return {
        "overall": round(filtered_overall, 1),
        "byFile": filtered_by_file,
        "uncovered": coverage_data["uncovered"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Parse JaCoCo coverage reports and check against a threshold."
    )
    parser.add_argument("report_path", help="Path to the JaCoCo XML coverage report")
    parser.add_argument(
        "--format", "-f", default="jacoco",
        choices=["jacoco"],
        help="Coverage report format (default: jacoco)",
    )
    parser.add_argument(
        "--threshold", "-t", type=float, default=80.0,
        help="Minimum coverage percentage (default: 80.0)",
    )
    parser.add_argument(
        "--changed-files", "-c",
        help="Path to changes.json to filter coverage to changed files only",
    )
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    args = parser.parse_args()

    report_path = Path(args.report_path)
    if not report_path.exists():
        print(f"Error: Report file '{report_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    try:
        coverage_data = parse_jacoco(report_path)
    except Exception as e:
        print(f"Error parsing coverage report: {e}", file=sys.stderr)
        sys.exit(1)

    # Optionally filter to changed files
    if args.changed_files:
        changes_path = Path(args.changed_files)
        if changes_path.exists():
            with open(changes_path, encoding="utf-8") as f:
                changes_data = json.load(f)
            changed_files = [c["file"] for c in changes_data.get("changes", [])]
            coverage_data = filter_to_changed_files(coverage_data, changed_files)

    result = {
        "reportPath": str(report_path),
        "format": args.format,
        "threshold": args.threshold,
        "overall": coverage_data["overall"],
        "pass": coverage_data["overall"] >= args.threshold,
        "gap": round(max(0, args.threshold - coverage_data["overall"]), 1),
        "byFile": coverage_data["byFile"],
        "uncovered": coverage_data["uncovered"],
        "filesAboveThreshold": sum(
            1 for f in coverage_data["byFile"]
            if f["lineCoverage"] >= args.threshold
        ),
        "filesBelowThreshold": sum(
            1 for f in coverage_data["byFile"]
            if f["lineCoverage"] < args.threshold
        ),
    }

    output = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output)

    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
