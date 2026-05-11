#!/usr/bin/env python3
"""
run-regression-tests.py — Execute selected JS/TS regression tests via Jest or Vitest.

Usage:
    python run-regression-tests.py <module-path> --test-runner <jest|vitest>
                                   [--tests <test-list-json>] [--package-name <name>]
                                   [--check-integrity] [--output <file>]
                                   [--test-type <unit|integration|both>]
                                   [--ci-mode] [--shard-index N --total-shards M]
                                   [--flaky-retries N]

Runs the appropriate test command, parses results from Jest JSON or Vitest output,
triggers coverage report generation, detects flaky tests, and outputs normalized JSON.
"""

import argparse
import json
import os
import re
import subprocess
import sys
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
            timeout=timeout, env=merged_env, shell=True,
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


def detect_test_runner(module_path: str) -> str:
    """Auto-detect test runner from package.json."""
    pkg_json = Path(module_path) / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json, encoding="utf-8") as f:
                pkg = json.load(f)
            dev_deps = pkg.get("devDependencies", {})
            deps = pkg.get("dependencies", {})
            all_deps = {**deps, **dev_deps}

            if "vitest" in all_deps:
                return "vitest"
            if "jest" in all_deps:
                return "jest"
        except (json.JSONDecodeError, KeyError):
            pass
    return "jest"  # default


def run_jest(
    module_path: str,
    test_files: list[str] | None = None,
    test_type: str = "unit",
    shard_args: list[str] | None = None,
) -> dict[str, Any]:
    """Run Jest tests with optional selective test execution."""
    cmd = ["npx", "jest", "--json", "--coverage", "--forceExit"]
    if test_files:
        # Use testPathPattern to filter
        pattern = "|".join(re.escape(f) for f in test_files)
        cmd.extend(["--testPathPattern", pattern])

    # Filter by test type
    if test_type == "integration":
        cmd.extend(["--testPathPattern", ".*\\.integration\\.test\\."])
    elif test_type == "unit":
        cmd.extend(["--testPathIgnorePatterns", ".*\\.integration\\.test\\."])
    # "both" -> no additional filtering

    if shard_args:
        cmd.extend(shard_args)

    result = run_command(cmd, cwd=module_path)

    # Parse Jest JSON output
    test_results = parse_jest_json(result["stdout"])

    # Find coverage report
    coverage_report = find_coverage_report(module_path, "jest")

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
    module_path: str,
    test_files: list[str] | None = None,
    test_type: str = "unit",
    shard_args: list[str] | None = None,
) -> dict[str, Any]:
    """Run Vitest tests with optional selective test execution."""
    cmd = ["npx", "vitest", "run", "--reporter=json", "--coverage"]
    if test_files:
        cmd.extend(test_files)

    # Filter by test type
    if test_type == "integration":
        cmd.extend(["--include", "**/*.integration.test.*"])
    elif test_type == "unit":
        cmd.extend(["--exclude", "**/*.integration.test.*"])
    # "both" -> no additional filtering

    if shard_args:
        cmd.extend(shard_args)

    result = run_command(cmd, cwd=module_path)

    # Parse Vitest JSON output (similar to Jest format)
    test_results = parse_jest_json(result["stdout"])

    coverage_report = find_coverage_report(module_path, "vitest")

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


def parse_jest_json(stdout: str) -> dict[str, Any]:
    """Parse Jest/Vitest JSON output for test results."""
    total = passed = failed = skipped = 0
    errors: list[dict[str, str]] = []

    try:
        # Jest JSON output may have other output before/after the JSON
        json_match = re.search(r'\{.*"numTotalTests".*\}', stdout, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            total = data.get("numTotalTests", 0)
            passed = data.get("numPassedTests", 0)
            failed = data.get("numFailedTests", 0)
            skipped = data.get("numPendingTests", 0)

            for suite in data.get("testResults", []):
                for test_result in suite.get("testResults", []):
                    if test_result.get("status") == "failed":
                        errors.append({
                            "file": suite.get("testFilePath", ""),
                            "test": test_result.get("fullName", test_result.get("title", "")),
                            "message": (
                                "\n".join(test_result.get("failureMessages", []))[:500]
                            ),
                        })
    except (json.JSONDecodeError, AttributeError):
        pass

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
    }


def find_coverage_report(module_path: str, runner: str) -> str | None:
    """Find the coverage report file."""
    base = Path(module_path)

    candidates = [
        base / "coverage" / "coverage-final.json",
        base / "coverage" / "lcov.info",
        base / "coverage" / "coverage-summary.json",
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


def check_source_integrity(module_path: str) -> dict[str, Any]:
    """Check if any source files were modified using git."""
    result = run_command(["git", "diff", "--name-only"], cwd=module_path)
    modified_files = [
        f for f in result["stdout"].strip().split("\n")
        if f and not any(
            pattern in f
            for pattern in [".test.", ".spec.", "__tests__/", "test/", "tests/"]
        )
    ]

    return {
        "pass": len(modified_files) == 0,
        "modifiedSourceFiles": modified_files,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Execute selected JS/TS regression tests via Jest or Vitest."
    )
    parser.add_argument("module_path", help="Path to the module directory")
    parser.add_argument(
        "--test-runner", "-r",
        choices=["jest", "vitest", "auto"],
        default="auto",
        help="Test runner type (default: auto-detect)",
    )
    parser.add_argument(
        "--package-name", "-p",
        help="Package name (for workspace projects)",
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
        "--test-type",
        choices=["unit", "integration", "both"],
        default="unit",
        help="Type of tests to run (default: unit)",
    )
    parser.add_argument(
        "--ci-mode", action="store_true",
        help="Enable CI mode: junit-xml reports, sharding, and flaky detection",
    )
    parser.add_argument(
        "--shard-index", type=int,
        help="Current shard index for test splitting (1-based for Jest, 0-based for Vitest)",
    )
    parser.add_argument(
        "--total-shards", type=int,
        help="Total number of shards for test splitting",
    )
    parser.add_argument(
        "--flaky-retries", type=int, default=0,
        help="Number of retries for failed tests to detect flaky tests (default: 0)",
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

    # Auto-detect test runner if needed
    runner = args.test_runner
    if runner == "auto":
        runner = detect_test_runner(str(module_path))
        print(f"Auto-detected test runner: {runner}", file=sys.stderr)

    # Load selective test list if provided
    test_files = None
    if args.tests:
        tests_path = Path(args.tests)
        if tests_path.exists():
            with open(tests_path, encoding="utf-8") as f:
                tests_data = json.load(f)
            test_files = [t.get("testFile", "") for t in tests_data.get("tests", []) if t.get("testFile")]

    # Build shard arguments if provided
    shard_args: list[str] | None = None
    if args.shard_index is not None and args.total_shards is not None:
        if runner == "jest":
            # Jest uses --shard=i/n (1-based)
            shard_idx = args.shard_index if args.shard_index >= 1 else args.shard_index + 1
            shard_args = [f"--shard={shard_idx}/{args.total_shards}"]
        else:
            # Vitest uses --shard=i/n (1-based)
            shard_idx = args.shard_index if args.shard_index >= 1 else args.shard_index + 1
            shard_args = [f"--shard={shard_idx}/{args.total_shards}"]

    # Determine test type
    test_type = getattr(args, "test_type", "unit") or "unit"

    if runner == "jest":
        result = run_jest(str(module_path), test_files, test_type, shard_args)
    else:
        result = run_vitest(str(module_path), test_files, test_type, shard_args)

    # Flaky test detection via retries
    flaky_tests: list[dict[str, str]] = []
    failed_tests = result.get("testExecution", {}).get("errors", [])
    if args.flaky_retries and args.flaky_retries > 0 and failed_tests:
        print(f"Retrying {len(failed_tests)} failed tests up to {args.flaky_retries} times...", file=sys.stderr)
        for failed_test in list(failed_tests):
            test_file = failed_test.get("file", "")
            if not test_file:
                continue

            passed_on_retry = False
            for attempt in range(1, args.flaky_retries + 1):
                if runner == "jest":
                    retry_result = run_jest(str(module_path), [test_file], test_type)
                else:
                    retry_result = run_vitest(str(module_path), [test_file], test_type)

                retry_exec = retry_result.get("testExecution", {})
                if retry_exec.get("failed", 0) == 0:
                    passed_on_retry = True
                    print(f"  Flaky: {test_file} passed on retry attempt {attempt}", file=sys.stderr)
                    break

            if passed_on_retry:
                flaky_tests.append({
                    "file": test_file,
                    "test": failed_test.get("test", ""),
                    "status": "flaky",
                })
                # Remove from errors since it's flaky, not a real failure
                failed_tests.remove(failed_test)

    if flaky_tests:
        result["flakyTests"] = flaky_tests
        # Adjust counts
        exec_info = result.get("testExecution", {})
        exec_info["failed"] = len(failed_tests)
        exec_info["flaky"] = len(flaky_tests)

    if args.ci_mode:
        result["ciMode"] = True
        if shard_args:
            result["shardInfo"] = {
                "index": args.shard_index,
                "total": args.total_shards,
            }

    if args.check_integrity:
        result["sourceIntegrity"] = check_source_integrity(str(module_path))

    output = json.dumps(result, indent=2, default=str)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output)

    sys.exit(0 if result.get("testExecution", {}).get("failed", 0) == 0 else 1)


if __name__ == "__main__":
    main()
