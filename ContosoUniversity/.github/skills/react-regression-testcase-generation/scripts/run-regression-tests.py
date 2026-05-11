#!/usr/bin/env python3
"""
run-regression-tests.py — Execute selected React regression tests via Jest or Vitest.

Usage:
    python run-regression-tests.py <project-path> --test-runner <jest|vitest>
                                   [--tests <test-list-json>] [--check-integrity]
                                   [--output <file>] [--ci-mode]
                                   [--report-dir <path>] [--report-formats <list>]
                                   [--shard-index <N> --total-shards <M>]
                                   [--flaky-threshold <N>]

Runs the appropriate test command, parses results from JUnit XML or JSON reporters,
collects coverage output, and outputs normalized JSON.
Supports Jest and Vitest, CI artifact generation, test sharding, and flaky detection.
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


def detect_test_runner(project_path: str) -> str:
    """Auto-detect Jest vs Vitest from project configuration."""
    pkg_json_path = Path(project_path) / "package.json"
    if pkg_json_path.exists():
        try:
            with open(pkg_json_path, encoding="utf-8") as f:
                pkg = json.load(f)
            all_deps = {
                **pkg.get("dependencies", {}),
                **pkg.get("devDependencies", {}),
            }
            if "vitest" in all_deps:
                return "vitest"
        except Exception:
            pass

    # Check for vitest config files
    vitest_configs = ["vitest.config.ts", "vitest.config.js", "vitest.config.mts"]
    for config in vitest_configs:
        if (Path(project_path) / config).exists():
            return "vitest"

    return "jest"


def run_jest(
    project_path: str,
    test_files: list[str] | None = None,
    shard_info: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Run Jest tests with optional selective test execution."""
    cmd = ["npx", "jest", "--coverage", "--ci", "--forceExit"]

    if test_files:
        cmd.extend(test_files)

    if shard_info:
        cmd.append(f"--shard={shard_info['index'] + 1}/{shard_info['total']}")

    # Use JSON reporter + JUnit XML
    cmd.extend(["--reporters", "default"])

    result = run_command(cmd, cwd=project_path)

    # Parse Jest JSON output if available
    test_results = parse_jest_results(project_path, result)

    # Look for coverage
    coverage_report = find_coverage_report(project_path, "jest")

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


def run_vitest(
    project_path: str,
    test_files: list[str] | None = None,
    shard_info: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Run Vitest tests with optional selective test execution."""
    cmd = ["npx", "vitest", "run", "--coverage", "--reporter=verbose"]

    if test_files:
        cmd.extend(test_files)

    if shard_info:
        cmd.append(f"--shard={shard_info['index'] + 1}/{shard_info['total']}")

    result = run_command(cmd, cwd=project_path)

    test_results = parse_vitest_results(project_path, result)

    coverage_report = find_coverage_report(project_path, "vitest")

    return {
        "testRunner": "vitest",
        "command": " ".join(cmd),
        "exitCode": result["returncode"],
        "testExecution": test_results,
        "coverageReportPath": coverage_report,
        "coverageFormat": "istanbul" if coverage_report else None,
        "stdout": result["stdout"][-2000:] if result["stdout"] else "",
        "stderr": result["stderr"][-2000:] if result["stderr"] else "",
    }


def parse_jest_results(
    project_path: str, cmd_result: dict[str, Any]
) -> dict[str, Any]:
    """Parse Jest test results from stdout or JSON report."""
    total = passed = failed = skipped = 0
    errors: list[dict[str, str]] = []

    stdout = cmd_result.get("stdout", "")

    # Try to parse from JSON output first
    json_report = Path(project_path) / "jest-results.json"
    if json_report.exists():
        try:
            with open(json_report, encoding="utf-8") as f:
                data = json.load(f)
            total = data.get("numTotalTests", 0)
            passed = data.get("numPassedTests", 0)
            failed = data.get("numFailedTests", 0)
            skipped = data.get("numPendingTests", 0)

            for suite in data.get("testResults", []):
                for test in suite.get("testResults", []):
                    if test.get("status") == "failed":
                        errors.append({
                            "file": suite.get("testFilePath", ""),
                            "test": test.get("fullName", ""),
                            "message": "\n".join(test.get("failureMessages", []))[:500],
                        })

            return {"total": total, "passed": passed, "failed": failed, "skipped": skipped, "errors": errors}
        except Exception:
            pass

    # Try JUnit XML reports
    junit_report = Path(project_path) / "junit.xml"
    if junit_report.exists():
        return parse_junit_xml(junit_report)

    # Fallback: parse stdout
    tests_match = re.search(r"Tests:\s+(\d+)\s+failed.*?(\d+)\s+passed.*?(\d+)\s+total", stdout)
    if not tests_match:
        tests_match = re.search(r"Tests:\s+(\d+)\s+passed.*?(\d+)\s+total", stdout)
        if tests_match:
            passed = int(tests_match.group(1))
            total = int(tests_match.group(2))
    else:
        failed = int(tests_match.group(1))
        passed = int(tests_match.group(2))
        total = int(tests_match.group(3))

    return {"total": total, "passed": passed, "failed": failed, "skipped": skipped, "errors": errors}


def parse_vitest_results(
    project_path: str, cmd_result: dict[str, Any]
) -> dict[str, Any]:
    """Parse Vitest test results from stdout or JSON report."""
    total = passed = failed = skipped = 0
    errors: list[dict[str, str]] = []

    stdout = cmd_result.get("stdout", "")

    # Check for JUnit XML report
    junit_report = Path(project_path) / "junit.xml"
    if junit_report.exists():
        return parse_junit_xml(junit_report)

    # Parse from verbose output
    # Pattern: "Tests  42 passed | 2 failed | 44 total"
    tests_match = re.search(
        r"Tests\s+(?:(\d+)\s+passed)?\s*\|?\s*(?:(\d+)\s+failed)?\s*\|?\s*(\d+)\s+total",
        stdout,
    )
    if tests_match:
        passed = int(tests_match.group(1) or 0)
        failed = int(tests_match.group(2) or 0)
        total = int(tests_match.group(3) or 0)

    # Extract failure details from stdout
    fail_blocks = re.findall(
        r"FAIL\s+(.*?)\s*>\s*(.*?)(?:\n.*?Error:\s*(.*?)(?:\n|$))?",
        stdout,
    )
    for block in fail_blocks:
        errors.append({
            "file": block[0].strip(),
            "test": block[1].strip(),
            "message": (block[2].strip() if len(block) > 2 else "")[:500],
        })

    return {"total": total, "passed": passed, "failed": failed, "skipped": skipped, "errors": errors}


def parse_junit_xml(report_path: Path) -> dict[str, Any]:
    """Parse JUnit XML test results."""
    total = passed = failed = skipped = 0
    errors: list[dict[str, str]] = []

    try:
        tree = ET.parse(report_path)
        root = tree.getroot()

        # Handle both <testsuites> and <testsuite> root elements
        suites = root.findall(".//testsuite") if root.tag == "testsuites" else [root]

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

        passed = total - failed - skipped
    except Exception:
        pass

    return {"total": total, "passed": passed, "failed": failed, "skipped": skipped, "errors": errors}


def find_coverage_report(project_path: str, runner: str) -> str | None:
    """Find Istanbul/c8 coverage report file."""
    base = Path(project_path)

    candidates = [
        base / "coverage" / "coverage-summary.json",
        base / "coverage" / "lcov.info",
        base / "coverage" / "coverage-final.json",
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
    project_path: str,
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
            if test_runner == "vitest":
                cmd = ["npx", "vitest", "run", test_file]
            else:
                cmd = ["npx", "jest", test_file, "--forceExit"]

            result = run_command(cmd, cwd=project_path, timeout=120)
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
    project_path: str,
    shard_info: dict[str, int] | None = None,
) -> dict[str, str]:
    """Generate CI-ready reports in the report directory."""
    report_path = Path(report_dir)
    report_path.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, str] = {}

    # Copy JUnit XML if exists
    if "junit-xml" in report_formats:
        junit_source = Path(project_path) / "junit.xml"
        xml_dest = report_path / "regression-results.xml"
        if junit_source.exists():
            shutil.copy2(junit_source, xml_dest)
            artifacts["junitXml"] = str(xml_dest)

    # Generate JSON manifest
    if "json" in report_formats:
        json_dest = report_path / "regression-results.json"
        manifest = {
            "project": Path(project_path).name,
            "testRunner": result.get("testRunner", "unknown"),
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

    # Generate Markdown summary
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


def check_source_integrity(project_path: str) -> dict[str, Any]:
    """Check if any source files were modified using git."""
    result = run_command(["git", "diff", "--name-only"], cwd=project_path)
    modified_files = [
        f for f in result["stdout"].strip().split("\n")
        if f and not any(
            pattern in f
            for pattern in [
                ".test.", ".spec.", "__tests__/",
                ".test.tsx", ".test.ts", ".spec.tsx", ".spec.ts",
            ]
        )
    ]

    return {
        "pass": len(modified_files) == 0,
        "modifiedSourceFiles": modified_files,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Execute selected React regression tests via Jest or Vitest."
    )
    parser.add_argument("project_path", help="Path to the React project directory")
    parser.add_argument(
        "--test-runner", "-r",
        choices=["jest", "vitest", "auto"],
        default="auto",
        help="Test runner to use (default: auto-detect)",
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
        help="Comma-separated list of report formats: junit-xml,json,markdown",
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

    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Path '{project_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Detect or use specified test runner
    test_runner = args.test_runner
    if test_runner == "auto":
        test_runner = detect_test_runner(str(project_path))
        print(f"Auto-detected test runner: {test_runner}", file=sys.stderr)

    # Load selective test list if provided
    test_files = None
    if args.tests:
        tests_path = Path(args.tests)
        if tests_path.exists():
            with open(tests_path, encoding="utf-8") as f:
                tests_data = json.load(f)
            test_files = [
                test.get("testFile", "") for test in tests_data.get("tests", [])
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
    if test_runner == "vitest":
        result = run_vitest(str(project_path), test_files, shard_info)
    else:
        result = run_jest(str(project_path), test_files, shard_info)

    # Detect flaky tests
    test_exec = result.get("testExecution", {})
    failed_errors = test_exec.get("errors", [])
    if args.flaky_threshold > 0 and failed_errors:
        flaky_tests, truly_failed = detect_flaky_tests(
            str(project_path), test_runner, failed_errors, args.flaky_threshold,
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
        result["sourceIntegrity"] = check_source_integrity(str(project_path))

    if shard_info:
        result["shardInfo"] = shard_info

    # Generate CI reports if requested
    if args.ci_mode:
        report_formats = [f.strip() for f in args.report_formats.split(",")]
        artifacts = generate_ci_reports(
            result, args.report_dir, report_formats,
            str(project_path), shard_info,
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
