#!/usr/bin/env python3
"""
check-coverage.py — Parse Istanbul/lcov coverage reports and check against a threshold.

Usage:
    python check-coverage.py <report-path> --format <istanbul|lcov>
                             --threshold <N> [--changed-files <json>] [--output <file>]

Supports Istanbul JSON (coverage-final.json) and lcov coverage reports.
Optionally filters coverage to only changed files.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def parse_istanbul(report_path: Path) -> dict[str, Any]:
    """Parse Istanbul JSON coverage report (coverage-final.json)."""
    with open(report_path, encoding="utf-8") as f:
        data = json.load(f)

    overall_covered = 0
    overall_total = 0
    by_file: list[dict[str, Any]] = []
    uncovered: list[dict[str, Any]] = []

    for filepath, file_data in data.items():
        # Statement coverage
        stmt_map = file_data.get("s", {})
        stmts_covered = sum(1 for v in stmt_map.values() if v > 0)
        stmts_total = len(stmt_map)

        # Branch coverage
        branch_map = file_data.get("b", {})
        branches_covered = sum(
            1 for branches in branch_map.values() for v in branches if v > 0
        )
        branches_total = sum(len(branches) for branches in branch_map.values())

        # Function coverage
        fn_map = file_data.get("f", {})
        fns_covered = sum(1 for v in fn_map.values() if v > 0)
        fns_total = len(fn_map)

        # Line coverage from statementMap
        stmt_line_map = file_data.get("statementMap", {})
        line_set = set()
        covered_lines = set()
        for key, loc in stmt_line_map.items():
            start_line = loc.get("start", {}).get("line", 0)
            if start_line > 0:
                line_set.add(start_line)
                if stmt_map.get(key, 0) > 0:
                    covered_lines.add(start_line)

        lines_total = len(line_set)
        lines_covered = len(covered_lines)

        line_pct = (lines_covered / lines_total * 100) if lines_total > 0 else 100.0
        branch_pct = (branches_covered / branches_total * 100) if branches_total > 0 else 100.0

        by_file.append({
            "file": filepath,
            "lineCoverage": round(line_pct, 1),
            "branchCoverage": round(branch_pct, 1),
            "linesCovered": lines_covered,
            "linesMissed": lines_total - lines_covered,
        })

        overall_covered += lines_covered
        overall_total += lines_total

        # Find uncovered functions
        fn_name_map = file_data.get("fnMap", {})
        uncov_fns = []
        for key, count in fn_map.items():
            if count == 0:
                fn_info = fn_name_map.get(key, {})
                fn_name = fn_info.get("name", f"anonymous_{key}")
                uncov_fns.append(fn_name)
        if uncov_fns:
            uncovered.append({
                "file": filepath,
                "methods": uncov_fns,
            })

    overall_pct = (overall_covered / overall_total * 100) if overall_total > 0 else 0.0

    return {
        "overall": round(overall_pct, 1),
        "byFile": by_file,
        "uncovered": uncovered,
    }


def parse_lcov(report_path: Path) -> dict[str, Any]:
    """Parse lcov.info coverage report."""
    content = report_path.read_text(encoding="utf-8", errors="replace")

    overall_covered = 0
    overall_total = 0
    by_file: list[dict[str, Any]] = []
    uncovered: list[dict[str, Any]] = []

    current_file = None
    file_lines_found = 0
    file_lines_hit = 0
    file_branches_found = 0
    file_branches_hit = 0
    file_uncov_fns: list[str] = []

    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("SF:"):
            current_file = line[3:]
            file_lines_found = 0
            file_lines_hit = 0
            file_branches_found = 0
            file_branches_hit = 0
            file_uncov_fns = []
        elif line.startswith("LF:"):
            file_lines_found = int(line[3:])
        elif line.startswith("LH:"):
            file_lines_hit = int(line[3:])
        elif line.startswith("BRF:"):
            file_branches_found = int(line[4:])
        elif line.startswith("BRH:"):
            file_branches_hit = int(line[4:])
        elif line.startswith("FNDA:"):
            parts = line[5:].split(",", 1)
            if len(parts) == 2 and parts[0] == "0":
                file_uncov_fns.append(parts[1])
        elif line == "end_of_record" and current_file:
            line_pct = (file_lines_hit / file_lines_found * 100) if file_lines_found > 0 else 100.0
            branch_pct = (file_branches_hit / file_branches_found * 100) if file_branches_found > 0 else 100.0

            by_file.append({
                "file": current_file,
                "lineCoverage": round(line_pct, 1),
                "branchCoverage": round(branch_pct, 1),
                "linesCovered": file_lines_hit,
                "linesMissed": file_lines_found - file_lines_hit,
            })

            overall_covered += file_lines_hit
            overall_total += file_lines_found

            if file_uncov_fns:
                uncovered.append({"file": current_file, "methods": file_uncov_fns})

            current_file = None

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
        # Also add without common prefixes
        for prefix in ["src/", "lib/", "app/"]:
            if normalized.startswith(prefix):
                changed_set.add(normalized[len(prefix):])

    filtered_by_file = []
    total_covered = 0
    total_missed = 0

    for entry in coverage_data["byFile"]:
        file_path = entry["file"].replace("\\", "/")
        # Try matching the full path or the basename
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
        description="Parse Istanbul/lcov coverage reports and check against a threshold."
    )
    parser.add_argument("report_path", help="Path to the coverage report file")
    parser.add_argument(
        "--format", "-f", default="istanbul",
        choices=["istanbul", "lcov"],
        help="Coverage report format (default: istanbul)",
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
        if args.format == "istanbul":
            coverage_data = parse_istanbul(report_path)
        else:
            coverage_data = parse_lcov(report_path)
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
