#!/usr/bin/env python3
"""
run-regression-tests.py — Execute selected Angular regression tests via Karma or Jest.

Usage:
    python run-regression-tests.py <module-path> --test-runner <karma|jest>
                                   [--tests <test-list-json>] [--output <file>]
                                   [--check-integrity] [--ci-mode]
                                   [--report-dir <path>] [--report-formats <list>]
                                   [--shard-index <N> --total-shards <M>]
                                   [--flaky-threshold <N>]

Runs the appropriate test command, parses results from JUnit XML reports,
generates Istanbul coverage, and outputs normalized JSON.
Supports test sharding and flaky test detection.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def run_command(
    cmd: list[str],
    cwd: str,
    timeout: int = 600,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Run a shell command and capture output."""
    merged_env = {**os.environ, **(env or {})}
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True,
            timeout=timeout, env=merged_env,
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s: {' '.join(cmd)}",
        }
    except FileNotFoundError:
        return {
            "returncode": -2,
            "stdout": "",
            "stderr": f"Command not found: {cmd[0]}. Ensure it is installed and on PATH.",
        }


def run_karma(
    module_path: str,
    test_files: list[str] | None = None,
) -> dict[str, Any]:
    """Run Angular tests via ng test (Karma)."""
    cmd = [
        "npx", "ng", "test",
        "--watch=false",
        "--browsers=ChromeHeadless",
        "--code-coverage",
    ]

    # If specific test files provided, use --include
    if test_files:
        for tf in test_files:
            cmd.extend(["--include", tf])

    result = run_command(cmd, cwd=module_path)
    test_results = parse_junit_reports(module_path)
    coverage_report = find_coverage_report(module_path)

    return {
        "testRunner": "karma",
        "command": " ".join(cmd),
        "exitCode": result["returncode"],
        "testExecution": test_results,
        "coverageReportPath": coverage_report,
        "coverageFormat": "istanbul" if coverage_report else None,
        "stdout": result["stdout"][-2000:] if result["stdout"] else "",
        "stderr": result["stderr"][-2000:] if result["stderr"] else "",
    }


def run_jest(
    module_path: str,
    test_files: list[str] | None = None,
) -> dict[str, Any]:
    """Run Angular tests via Jest."""
    cmd = [
        "npx", "jest",
        "--ci",
        "--coverage",
        "--reporters=default",
        "--reporters=jest-junit",
    ]

    if test_files:
        cmd.extend(test_files)

    result = run_command(cmd, cwd=module_path)
    test_results = parse_junit_reports(module_path)
    coverage_report = find_coverage_report(module_path)

    return {
        "testRunner": "jest",
        "command": " ".join(cmd),
        "exitCode": result["returncode"],
        "testExecution": test_results,
        "coverageReportPath": coverage_report,
        "coverageFormat": "istanbul" if coverage_report else None,
        "stdout": result["stdout"][-2000:] if result["stdout"] else "",
        "stderr": result["stderr"][-2000:] if result["stderr"] else "",
    }


def parse_junit_reports(module_path: str) -> dict[str, Any]:
    """Parse JUnit XML test results."""
    base = Path(module_path)
    total = passed = failed = skipped = 0
    errors: list[dict[str, str]] = []

    # Search for JUnit XML reports in common locations
    report_candidates = [
        base / "regression-reports",
        base / "test-results",
        base / "junit",
        base,
    ]

    for reports_dir in report_candidates:
        if not reports_dir.exists():
            continue
        for xml_file in reports_dir.glob("**/*.xml"):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Handle both <testsuites> and <testsuite> root elements
                if root.tag == "testsuites":
                    suites = root.findall("testsuite")
                elif root.tag == "testsuite":
                    suites = [root]
                else:
                    continue

                for suite in suites:
                    total += int(suite.get("tests", 0))
                    failed += int(suite.get("failures", 0))
                    failed += int(suite.get("errors", 0))
                    skipped += int(suite.get("skipped", 0))

                    for testcase in suite.findall(".//testcase"):
                        failure = testcase.find("failure") or testcase.find("error")
                        if failure is not None:
                            errors.append({
                                "file": testcase.get("classname", ""),
                                "test": testcase.get("name", ""),
                                "message": (failure.get("message", "") or "")[:500],
                            })
            except Exception:
                continue

    if total > 0:
        passed = total - failed - skipped

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
    }


def find_coverage_report(module_path: str) -> str | None:
    """Find the Istanbul coverage report file."""
    base = Path(module_path)
    candidates = [
        base / "coverage" / "lcov.info",
        base / "coverage" / "coverage-summary.json",
        base / "coverage" / "lcov-report" / "lcov.info",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def split_tests_for_shard(
    test_files: list[str],
    shard_index: int,
    total_shards: int,
) -> list[str]:
    """Partition test list using round-robin for test splitting."""
    if total_shards <= 1:
        return test_files
    return [tf for i, tf in enumerate(test_files) if i % total_shards == shard_index]


def detect_flaky_tests(
    module_path: str,
    test_runner: str,
    failed_tests: list[dict[str, str]],
    flaky_threshold: int = 2,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Retry failed tests to detect flaky ones.

    Returns (flaky_tests, truly_failed_tests).
    """
    if not failed_tests or flaky_threshold < 1:
        return [], failed_tests

    flaky: list[dict[str, Any]] = []
    truly_failed: list[dict[str, str]] = []

    for test_error in failed_tests:
        test_file = test_error.get("file", "")
        if not test_file:
            truly_failed.append(test_error)
            continue

        passed_on_retry = False
        retries_needed = 0

        for attempt in range(1, flaky_threshold + 1):
            if test_runner == "karma":
                cmd = [
                    "npx", "ng", "test",
                    "--watch=false",
                    "--browsers=ChromeHeadless",
                    "--include", test_file,
                ]
            else:  # jest
                cmd = ["npx", "jest", "--ci", test_file]

            result = run_command(cmd, cwd=module_path, timeout=120)
            if result["returncode"] == 0:
                passed_on_retry = True
                retries_needed = attempt
                break

        if passed_on_retry:
            flaky.append({
                "file": test_file,
                "test": test_error.get("test", ""),
                "retriesBeforePass": retries_needed,
            })
        else:
            truly_failed.append(test_error)

    return flaky, truly_failed


def generate_ci_reports(
    result: dict[str, Any],
    report_dir: str,
    report_formats: list[str],
    module_path: str,
    test_runner: str,
    shard_info: dict[str, int] | None = None,
) -> dict[str, str]:
    """Generate CI-ready reports in the report directory."""
    report_path = Path(report_dir)
    report_path.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, str] = {}

    # JUnit XML aggregation
    if "junit-xml" in report_formats:
        xml_dest = report_path / "regression-results.xml"
        root = ET.Element("testsuites")

        base = Path(module_path)
        for src_dir in [base / "regression-reports", base / "test-results", base / "junit"]:
            if src_dir.exists():
                for xml_file in src_dir.glob("**/*.xml"):
                    try:
                        tree = ET.parse(xml_file)
                        root.append(tree.getroot())
                    except Exception:
                        continue

        tree = ET.ElementTree(root)
        tree.write(str(xml_dest), encoding="unicode", xml_declaration=True)
        artifacts["junitXml"] = str(xml_dest)

    # JSON manifest
    if "json" in report_formats:
        json_dest = report_path / "regression-results.json"
        manifest = {
            "testRunner": test_runner,
            "testExecution": result.get("testExecution", {}),
            "coverage": result.get("coverage"),
            "sourceIntegrity": result.get("sourceIntegrity"),
        }
        if shard_info:
            manifest["shardInfo"] = shard_info
        if "flakyTests" in result:
            manifest["flakyTests"] = result["flakyTests"]

        json_dest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        artifacts["jsonReport"] = str(json_dest)

    # Markdown summary
    if "markdown" in report_formats:
        md_dest = report_path / "regression-summary.md"
        te = result.get("testExecution", {})
        lines = [
            "# Regression Test Summary\n",
            f"- **Total**: {te.get('total', 0)}",
            f"- **Passed**: {te.get('passed', 0)}",
            f"- **Failed**: {te.get('failed', 0)}",
            f"- **Skipped**: {te.get('skipped', 0)}",
        ]
        if "flaky" in te:
            lines.append(f"- **Flaky**: {te.get('flaky', 0)}")
        if shard_info:
            lines.append(f"- **Shard**: {shard_info['index']} of {shard_info['total']}")
        md_dest.write_text("\n".join(lines), encoding="utf-8")
        artifacts["markdownSummary"] = str(md_dest)

    return artifacts


def check_source_integrity(module_path: str) -> dict[str, Any]:
    """Check if any source files were modified using git."""
    result = run_command(["git", "diff", "--name-only"], cwd=module_path)
    modified_files = [
        f for f in result["stdout"].strip().split("\n")
        if f and not any(
            pattern in f
            for pattern in [".spec.ts", ".test.ts", "__tests__/"]
        )
    ]

    return {
        "pass": len(modified_files) == 0,
        "modifiedSourceFiles": modified_files,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Execute selected Angular regression tests via Karma or Jest."
    )
    parser.add_argument("module_path", help="Path to the Angular project directory")
    parser.add_argument(
        "--test-runner", "-b", required=True,
        choices=["karma", "jest"],
        help="Test runner type",
    )
    parser.add_argument(
        "--tests",
        help="Path to JSON file with test files to run (selected-tests.json)",
    )
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument(
        "--check-integrity", action="store_true",
        help="Check source file integrity after tests",
    )
    parser.add_argument(
        "--ci-mode", action="store_true",
        help="Generate CI-ready report artifacts in report-dir",
    )
    parser.add_argument(
        "--report-dir", default="./regression-reports",
        help="Output directory for CI reports (default: ./regression-reports)",
    )
    parser.add_argument(
        "--report-formats", default="junit-xml,json",
        help="Comma-separated list of report formats: junit-xml,json,markdown,html",
    )
    parser.add_argument(
        "--shard-index", type=int,
        help="Current shard index for test splitting (0-based)",
    )
    parser.add_argument(
        "--total-shards", type=int,
        help="Total number of shards for test splitting",
    )
    parser.add_argument(
        "--flaky-threshold", type=int, default=2,
        help="Retry count for flaky test detection (default: 2). Set to 0 to disable.",
    )
    parser.add_argument(
        "--timeout", type=int, default=600,
        help="Test execution timeout in seconds (default: 600)",
    )
    args = parser.parse_args()

    module_path = Path(args.module_path)
    if not module_path.exists():
        print(f"Error: Path '{module_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Load selective test list if provided
    test_files = None
    if args.tests:
        tests_path = Path(args.tests)
        if tests_path.exists():
            with open(tests_path, encoding="utf-8") as f:
                tests_data = json.load(f)
            test_files = [
                test.get("testFile", "")
                for test in tests_data.get("tests", [])
                if test.get("testFile")
            ]

    # Apply test splitting (sharding)
    shard_info = None
    if args.shard_index is not None and args.total_shards is not None:
        total_shards = max(1, args.total_shards)
        shard_index = args.shard_index % total_shards
        shard_info = {"index": shard_index, "total": total_shards}
        if test_files:
            test_files = split_tests_for_shard(test_files, shard_index, total_shards)
            print(
                f"Shard {shard_index}/{total_shards}: running {len(test_files)} tests",
                file=sys.stderr,
            )

    # Run tests
    if args.test_runner == "karma":
        result = run_karma(str(module_path), test_files)
    else:
        result = run_jest(str(module_path), test_files)

    # Detect flaky tests
    test_exec = result.get("testExecution", {})
    failed_errors = test_exec.get("errors", [])
    if args.flaky_threshold > 0 and failed_errors:
        flaky_tests, truly_failed = detect_flaky_tests(
            str(module_path), args.test_runner,
            failed_errors, args.flaky_threshold,
        )
        if flaky_tests:
            result["testExecution"]["flaky"] = len(flaky_tests)
            result["testExecution"]["failed"] = len(truly_failed)
            result["testExecution"]["passed"] = (
                test_exec["total"] - len(truly_failed) - test_exec.get("skipped", 0)
            )
            result["testExecution"]["errors"] = truly_failed
            result["flakyTests"] = flaky_tests

    if args.check_integrity:
        result["sourceIntegrity"] = check_source_integrity(str(module_path))

    if shard_info:
        result["shardInfo"] = shard_info

    # Generate CI reports if requested
    if args.ci_mode:
        report_formats = [f.strip() for f in args.report_formats.split(",")]
        artifacts = generate_ci_reports(
            result, args.report_dir, report_formats,
            str(module_path), args.test_runner, shard_info,
        )
        result["artifacts"] = artifacts

    output = json.dumps(result, indent=2, default=str)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output)

    sys.exit(0 if result.get("testExecution", {}).get("failed", 0) == 0 else 1)


if __name__ == "__main__":
    main()
