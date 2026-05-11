#!/usr/bin/env python3
"""
check-coverage.py — Parse Istanbul coverage reports and check against a threshold.

Usage:
    python check-coverage.py <report-path> --format <istanbul>
                             --threshold <N> [--changed-files <json>] [--output <file>]

Supports Istanbul coverage formats:
  - lcov.info (LCOV format)
  - coverage-summary.json (Istanbul JSON summary)
Optionally filters coverage to only changed files.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def parse_lcov(report_path: Path) -> dict[str, Any]:
    """Parse LCOV coverage report."""
    content = report_path.read_text(encoding="utf-8", errors="replace")

    overall_line = {"covered": 0, "total": 0}
    overall_branch = {"covered": 0, "total": 0}
    by_file: list[dict[str, Any]] = []
    uncovered: list[dict[str, Any]] = []

    current_file = None
    file_line = {"covered": 0, "total": 0}
    file_branch = {"covered": 0, "total": 0}
    file_uncov_lines: list[int] = []

    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("SF:"):
            current_file = line[3:]
            file_line = {"covered": 0, "total": 0}
            file_branch = {"covered": 0, "total": 0}
            file_uncov_lines = []
        elif line.startswith("LF:"):
            file_line["total"] = int(line[3:])
        elif line.startswith("LH:"):
            file_line["covered"] = int(line[3:])
        elif line.startswith("BRF:"):
            file_branch["total"] = int(line[4:])
        elif line.startswith("BRH:"):
            file_branch["covered"] = int(line[4:])
        elif line.startswith("DA:"):
            parts = line[3:].split(",")
            if len(parts) >= 2 and parts[1] == "0":
                file_uncov_lines.append(int(parts[0]))
        elif line == "end_of_record" and current_file:
            total_lines = file_line["total"]
            line_pct = (
                (file_line["covered"] / total_lines * 100)
                if total_lines > 0
                else 100.0
            )
            total_branches = file_branch["total"]
            branch_pct = (
                (file_branch["covered"] / total_branches * 100)
                if total_branches > 0
                else 100.0
            )

            by_file.append({
                "file": current_file,
                "lineCoverage": round(line_pct, 1),
                "branchCoverage": round(branch_pct, 1),
                "linesCovered": file_line["covered"],
                "linesMissed": file_line["total"] - file_line["covered"],
            })

            if file_uncov_lines:
                uncovered.append({
                    "file": current_file,
                    "uncoveredLines": file_uncov_lines,
                })

            overall_line["covered"] += file_line["covered"]
            overall_line["total"] += file_line["total"]
            overall_branch["covered"] += file_branch["covered"]
            overall_branch["total"] += file_branch["total"]
            current_file = None

    overall_pct = (
        (overall_line["covered"] / overall_line["total"] * 100)
        if overall_line["total"] > 0
        else 0.0
    )

    return {
        "overall": round(overall_pct, 1),
        "byFile": by_file,
        "uncovered": uncovered,
    }


def parse_istanbul_json(report_path: Path) -> dict[str, Any]:
    """Parse Istanbul JSON summary coverage report (coverage-summary.json)."""
    with open(report_path, encoding="utf-8") as f:
        data = json.load(f)

    by_file: list[dict[str, Any]] = []
    uncovered: list[dict[str, Any]] = []
    overall_covered = 0
    overall_total = 0

    for filepath, metrics in data.items():
        if filepath == "total":
            continue

        lines = metrics.get("lines", {})
        branches = metrics.get("branches", {})

        line_pct = lines.get("pct", 0)
        branch_pct = branches.get("pct", 0)
        lines_covered = lines.get("covered", 0)
        lines_total = lines.get("total", 0)

        by_file.append({
            "file": filepath,
            "lineCoverage": round(line_pct, 1),
            "branchCoverage": round(branch_pct, 1),
            "linesCovered": lines_covered,
            "linesMissed": lines_total - lines_covered,
        })

        overall_covered += lines_covered
        overall_total += lines_total

        if lines_covered < lines_total:
            uncovered.append({
                "file": filepath,
                "uncoveredLines": [],  # JSON summary doesn't include line details
            })

    # Use "total" key if present
    if "total" in data:
        total_lines = data["total"].get("lines", {})
        overall_pct = total_lines.get("pct", 0)
    else:
        overall_pct = (
            (overall_covered / overall_total * 100)
            if overall_total > 0
            else 0.0
        )

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
        # Also add without src/ prefix for matching
        if normalized.startswith("src/"):
            changed_set.add(normalized[4:])

    filtered_by_file = []
    total_covered = 0
    total_missed = 0

    for entry in coverage_data["byFile"]:
        file_path = entry["file"].replace("\\", "/")
        # Check various matching strategies
        matched = False
        for changed in changed_set:
            if file_path.endswith(changed) or changed.endswith(file_path):
                matched = True
                break
        if file_path in changed_set:
            matched = True

        if matched:
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


def detect_format(report_path: Path) -> str:
    """Auto-detect coverage report format."""
    name = report_path.name.lower()
    if name.endswith(".json"):
        return "istanbul-json"
    elif name == "lcov.info" or name.endswith(".lcov"):
        return "lcov"
    # Try to detect by content
    try:
        content = report_path.read_text(encoding="utf-8", errors="replace")[:200]
        if content.strip().startswith("{"):
            return "istanbul-json"
        if content.startswith("TN:") or content.startswith("SF:"):
            return "lcov"
    except Exception:
        pass
    return "lcov"  # default


def main():
    parser = argparse.ArgumentParser(
        description="Parse Istanbul coverage reports and check against a threshold."
    )
    parser.add_argument("report_path", help="Path to the coverage report file")
    parser.add_argument(
        "--format", "-f", default="auto",
        choices=["auto", "lcov", "istanbul-json"],
        help="Coverage report format (default: auto-detect)",
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

    # Detect or use specified format
    fmt = args.format
    if fmt == "auto":
        fmt = detect_format(report_path)

    try:
        if fmt == "lcov":
            coverage_data = parse_lcov(report_path)
        elif fmt == "istanbul-json":
            coverage_data = parse_istanbul_json(report_path)
        else:
            print(f"Error: Unsupported format '{fmt}'.", file=sys.stderr)
            sys.exit(1)
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
        "format": fmt,
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
