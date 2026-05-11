#!/usr/bin/env python3
"""
check-coverage.py — Parse Istanbul/V8/lcov coverage reports and check against a threshold.

Usage:
    python check-coverage.py <report-path> --format <istanbul|lcov|v8>
                             --threshold <N> [--changed-files <json>] [--output <file>]

Supports Istanbul coverage-summary.json, lcov.info, and V8 coverage-report.json formats.
Optionally filters coverage to only changed files.

Note: Playwright does not generate coverage by default. Use Playwright's V8 coverage
API or configure Istanbul instrumentation separately. This script parses the resulting
coverage reports regardless of how they were generated.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def parse_istanbul_summary(report_path: Path) -> dict[str, Any]:
    """Parse Istanbul coverage-summary.json report."""
    with open(report_path, encoding="utf-8") as f:
        data = json.load(f)

    overall_lines_covered = 0
    overall_lines_total = 0
    by_file: list[dict[str, Any]] = []
    uncovered: list[dict[str, Any]] = []

    for filepath, metrics in data.items():
        if filepath == "total":
            continue

        lines = metrics.get("lines", {})
        branches = metrics.get("branches", {})
        functions = metrics.get("functions", {})

        line_pct = lines.get("pct", 0)
        branch_pct = branches.get("pct", 0)
        lines_covered = lines.get("covered", 0)
        lines_total = lines.get("total", 0)
        lines_missed = lines_total - lines_covered

        overall_lines_covered += lines_covered
        overall_lines_total += lines_total

        by_file.append({
            "file": filepath,
            "lineCoverage": round(line_pct, 1),
            "branchCoverage": round(branch_pct, 1),
            "linesCovered": lines_covered,
            "linesMissed": lines_missed,
        })

        func_covered = functions.get("covered", 0)
        func_total = functions.get("total", 0)
        if func_total > func_covered:
            uncovered.append({
                "file": filepath,
                "uncoveredFunctions": func_total - func_covered,
                "totalFunctions": func_total,
            })

    overall_pct = (
        (overall_lines_covered / overall_lines_total * 100)
        if overall_lines_total > 0
        else 0.0
    )

    return {
        "overall": round(overall_pct, 1),
        "byFile": by_file,
        "uncovered": uncovered,
    }


def parse_lcov(report_path: Path) -> dict[str, Any]:
    """Parse lcov.info coverage report."""
    content = report_path.read_text(encoding="utf-8", errors="replace")

    overall_lines_covered = 0
    overall_lines_total = 0
    by_file: list[dict[str, Any]] = []
    uncovered: list[dict[str, Any]] = []

    current_file = None
    file_lines_hit = 0
    file_lines_total = 0
    file_branches_hit = 0
    file_branches_total = 0
    file_functions_hit = 0
    file_functions_total = 0

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue

        if line.startswith("SF:"):
            current_file = line[3:]
            file_lines_hit = 0
            file_lines_total = 0
            file_branches_hit = 0
            file_branches_total = 0
            file_functions_hit = 0
            file_functions_total = 0
        elif line.startswith("LH:"):
            file_lines_hit = int(line[3:])
        elif line.startswith("LF:"):
            file_lines_total = int(line[3:])
        elif line.startswith("BRH:"):
            file_branches_hit = int(line[4:])
        elif line.startswith("BRF:"):
            file_branches_total = int(line[4:])
        elif line.startswith("FNH:"):
            file_functions_hit = int(line[4:])
        elif line.startswith("FNF:"):
            file_functions_total = int(line[4:])
        elif line == "end_of_record":
            if current_file:
                line_pct = (
                    (file_lines_hit / file_lines_total * 100)
                    if file_lines_total > 0
                    else 100.0
                )
                branch_pct = (
                    (file_branches_hit / file_branches_total * 100)
                    if file_branches_total > 0
                    else 100.0
                )

                by_file.append({
                    "file": current_file,
                    "lineCoverage": round(line_pct, 1),
                    "branchCoverage": round(branch_pct, 1),
                    "linesCovered": file_lines_hit,
                    "linesMissed": file_lines_total - file_lines_hit,
                })

                overall_lines_covered += file_lines_hit
                overall_lines_total += file_lines_total

                if file_functions_total > file_functions_hit:
                    uncovered.append({
                        "file": current_file,
                        "uncoveredFunctions": file_functions_total - file_functions_hit,
                        "totalFunctions": file_functions_total,
                    })

            current_file = None

    overall_pct = (
        (overall_lines_covered / overall_lines_total * 100)
        if overall_lines_total > 0
        else 0.0
    )

    return {
        "overall": round(overall_pct, 1),
        "byFile": by_file,
        "uncovered": uncovered,
    }


def parse_v8_coverage(report_path: Path) -> dict[str, Any]:
    """Parse V8 coverage JSON report (as generated by Playwright V8 coverage API).

    V8 coverage JSON is an array of entries with shape:
    [{ "url": "...", "functions": [{ "functionName": "...", "ranges": [{ "startOffset": N, "endOffset": N, "count": N }] }] }]
    """
    with open(report_path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = data.get("result", [])

    overall_covered = 0
    overall_total = 0
    by_file: list[dict[str, Any]] = []
    uncovered: list[dict[str, Any]] = []

    for entry in data:
        url = entry.get("url", "")
        # Skip non-file URLs and node_modules
        if "node_modules" in url or not url:
            continue

        functions = entry.get("functions", [])
        file_covered = 0
        file_total = 0
        uncovered_funcs = 0
        total_funcs = len(functions)

        for func in functions:
            ranges = func.get("ranges", [])
            func_has_coverage = False
            for r in ranges:
                count = r.get("count", 0)
                size = r.get("endOffset", 0) - r.get("startOffset", 0)
                file_total += size
                if count > 0:
                    file_covered += size
                    func_has_coverage = True

            if not func_has_coverage and func.get("functionName"):
                uncovered_funcs += 1

        line_pct = (file_covered / file_total * 100) if file_total > 0 else 100.0

        by_file.append({
            "file": url,
            "lineCoverage": round(line_pct, 1),
            "branchCoverage": 0.0,  # V8 raw coverage doesn't include branches
            "linesCovered": file_covered,
            "linesMissed": file_total - file_covered,
        })

        overall_covered += file_covered
        overall_total += file_total

        if uncovered_funcs > 0:
            uncovered.append({
                "file": url,
                "uncoveredFunctions": uncovered_funcs,
                "totalFunctions": total_funcs,
            })

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
        if normalized.startswith("src/"):
            changed_set.add(normalized[4:])
        else:
            changed_set.add("src/" + normalized)

    filtered_by_file = []
    total_covered = 0
    total_missed = 0

    for entry in coverage_data["byFile"]:
        file_path = entry["file"].replace("\\", "/")
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


def main():
    parser = argparse.ArgumentParser(
        description="Parse Istanbul/V8/lcov coverage reports and check against a threshold."
    )
    parser.add_argument("report_path", help="Path to the coverage report file")
    parser.add_argument(
        "--format", "-f", default="istanbul",
        choices=["istanbul", "lcov", "v8"],
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
        if args.format == "lcov":
            coverage_data = parse_lcov(report_path)
        elif args.format == "v8":
            coverage_data = parse_v8_coverage(report_path)
        else:
            coverage_data = parse_istanbul_summary(report_path)
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
