#!/usr/bin/env python3
"""
check-coverage.py — Parse Cobertura XML coverage reports and check against a threshold.

Usage:
    python check-coverage.py <report-path> --format <cobertura>
                             --threshold <N> [--changed-files <json>] [--output <file>]

Supports Cobertura XML coverage reports (coverlet for .NET).
Optionally filters coverage to only changed files.
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def parse_cobertura(report_path: Path) -> dict[str, Any]:
    """Parse Cobertura XML coverage report."""
    tree = ET.parse(report_path)
    root = tree.getroot()

    overall_covered = 0
    overall_total = 0
    by_file: list[dict[str, Any]] = []
    uncovered: list[dict[str, Any]] = []

    for package in root.findall(".//package"):
        for cls in package.findall("classes/class"):
            file_name = cls.get("filename", "")
            cls_name = cls.get("name", "")

            line_covered = 0
            line_total = 0
            branch_covered = 0
            branch_total = 0
            uncov_methods: list[str] = []

            for method in cls.findall("methods/method"):
                method_name = method.get("name", "")
                method_lines_hit = 0
                method_lines_total = 0

                for line in method.findall("lines/line"):
                    hits = int(line.get("hits", 0))
                    method_lines_total += 1
                    if hits > 0:
                        method_lines_hit += 1

                    # Branch coverage
                    if line.get("branch") == "True":
                        condition = line.get("condition-coverage", "")
                        # Parse "50% (1/2)" format
                        if "(" in condition:
                            parts = condition.split("(")[1].rstrip(")").split("/")
                            if len(parts) == 2:
                                branch_covered += int(parts[0])
                                branch_total += int(parts[1])

                if method_lines_total > 0 and method_lines_hit == 0:
                    if method_name not in (".ctor", ".cctor"):
                        uncov_methods.append(method_name)

            # Also parse class-level lines
            for line in cls.findall("lines/line"):
                hits = int(line.get("hits", 0))
                line_total += 1
                if hits > 0:
                    line_covered += 1

            line_pct = (line_covered / line_total * 100) if line_total > 0 else 100.0
            branch_pct = (branch_covered / branch_total * 100) if branch_total > 0 else 100.0

            by_file.append({
                "file": file_name,
                "lineCoverage": round(line_pct, 1),
                "branchCoverage": round(branch_pct, 1),
                "linesCovered": line_covered,
                "linesMissed": line_total - line_covered,
            })

            overall_covered += line_covered
            overall_total += line_total

            if uncov_methods:
                uncovered.append({
                    "file": cls_name,
                    "methods": uncov_methods,
                })

    # Fallback: check top-level attributes
    if overall_total == 0:
        line_rate = float(root.get("line-rate", 0))
        lines_valid = int(root.get("lines-valid", 0))
        overall_total = lines_valid
        overall_covered = int(line_rate * lines_valid)

    overall_pct = (overall_covered / overall_total * 100) if overall_total > 0 else 0.0

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
    changed_set = set()
    for f in changed_files:
        normalized = f.replace("\\", "/")
        changed_set.add(normalized)
        # Strip common prefixes
        parts = normalized.split("/")
        if len(parts) > 1:
            changed_set.add("/".join(parts[1:]))  # without project folder

    filtered_by_file = []
    total_covered = 0
    total_missed = 0

    for entry in coverage_data["byFile"]:
        file_path = entry["file"].replace("\\", "/")
        matches = False
        for cf in changed_set:
            if file_path.endswith(cf) or cf.endswith(file_path):
                matches = True
                break

        if matches:
            filtered_by_file.append(entry)
            total_covered += entry.get("linesCovered", 0)
            total_missed += entry.get("linesMissed", 0)

    total_lines = total_covered + total_missed
    filtered_overall = (total_covered / total_lines * 100) if total_lines > 0 else 0.0

    return {
        "overall": round(filtered_overall, 1),
        "byFile": filtered_by_file,
        "uncovered": coverage_data["uncovered"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Parse Cobertura coverage reports and check against a threshold."
    )
    parser.add_argument("report_path", help="Path to the Cobertura XML coverage report")
    parser.add_argument(
        "--format", "-f", default="cobertura",
        choices=["cobertura"],
        help="Coverage report format (default: cobertura)",
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
        coverage_data = parse_cobertura(report_path)
    except Exception as e:
        print(f"Error parsing coverage report: {e}", file=sys.stderr)
        sys.exit(1)

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
        "filesAboveThreshold": sum(1 for f in coverage_data["byFile"] if f["lineCoverage"] >= args.threshold),
        "filesBelowThreshold": sum(1 for f in coverage_data["byFile"] if f["lineCoverage"] < args.threshold),
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
