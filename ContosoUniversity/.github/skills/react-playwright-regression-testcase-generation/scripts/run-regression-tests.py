#!/usr/bin/env python3
"""
run-regression-tests.py — Execute selected Playwright regression tests.

Usage:
    python run-regression-tests.py <project-path> [--test-runner playwright]
                                   [--tests <test-list-json>] [--check-integrity]
                                   [--output <file>] [--ci-mode]
                                   [--report-dir <path>] [--report-formats <list>]
                                   [--shard <N/M>] [--retries <N>]
                                   [--browsers <list>] [--headed]

Runs Playwright tests, parses results from JUnit XML or JSON reporters,
collects coverage output, and outputs normalized JSON.
Supports CI artifact generation, built-in Playwright sharding, and flaky detection.
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


def detect_playwright_config(project_path: str) -> str | None:
    """Find the Playwright config file."""
    configs = [
        "playwright.config.ts",
        "playwright.config.js",
        "playwright.config.mjs",
    ]
    for config in configs:
        if (Path(project_path) / config).exists():
            return config
    return None


def detect_playwright_ct_config(project_path: str) -> str | None:
    """Find the Playwright component testing config file."""
    configs = [
        "playwright-ct.config.ts",
        "playwright-ct.config.js",
    ]
    for config in configs:
        if (Path(project_path) / config).exists():
            return config
    return None


def run_playwright(
    project_path: str,
    test_files: list[str] | None = None,
    shard: str | None = None,
    retries: int = 0,
    browsers: list[str] | None = None,
    headed: bool = False,
    report_dir: str = "./regression-reports",
    config_file: str | None = None,
    test_level: str = "e2e",
) -> dict[str, Any]:
    """Run Playwright tests with optional selective test execution."""
    cmd = ["npx", "playwright", "test"]

    # Use specific config if provided
    if config_file:
        cmd.extend(["--config", config_file])
    elif test_level == "component":
        ct_config = detect_playwright_ct_config(project_path)
        if ct_config:
            cmd.extend(["--config", ct_config])

    # Add test files if selective execution
    if test_files:
        cmd.extend(test_files)

    # Sharding (Playwright native format: --shard=N/M)
    if shard:
        cmd.append(f"--shard={shard}")

    # Retries for flaky detection
    if retries > 0:
        cmd.append(f"--retries={retries}")

    # Browser selection
    if browsers:
        for browser in browsers:
            cmd.extend(["--project", browser])

    # Headed mode
    if headed:
        cmd.append("--headed")

    # Reporters
    junit_output = str(Path(report_dir) / "regression-results.xml")
    cmd.extend([
        "--reporter", f"list,junit,html",
    ])

    env = {
        "PLAYWRIGHT_JUNIT_OUTPUT_NAME": junit_output,
    }

    result = run_command(cmd, cwd=project_path, env=env)

    # Parse results
    test_results = parse_playwright_results(project_path, result, report_dir)

    # Look for coverage if available
    coverage_report = find_coverage_report(project_path)

    return {
        "testRunner": "playwright",
        "testLevel": test_level,
        "command": " ".join(cmd),
        "exitCode": result["returncode"],
        "testExecution": test_results,
        "coverageReportPath": coverage_report,
        "coverageFormat": "istanbul" if coverage_report else None,
        "stdout": result["stdout"][-2000:] if result["stdout"] else "",
        "stderr": result["stderr"][-2000:] if result["stderr"] else "",
    }


def parse_playwright_results(
    project_path: str, cmd_result: dict[str, Any], report_dir: str
) -> dict[str, Any]:
    """Parse Playwright test results from JUnit XML or stdout."""
    total = passed = failed = skipped = flaky = 0
    errors: list[dict[str, str]] = []

    # Try JUnit XML first
    junit_paths = [
        Path(report_dir) / "regression-results.xml",
        Path(project_path) / "test-results" / "results.xml",
        Path(project_path) / "junit.xml",
    ]

    for junit_path in junit_paths:
        if junit_path.exists():
            result = parse_junit_xml(junit_path)
            return result

    # Fallback: parse stdout
    stdout = cmd_result.get("stdout", "")

    # Playwright output format: "X passed", "X failed", "X skipped", "X flaky"
    passed_match = re.search(r"(\d+)\s+passed", stdout)
    failed_match = re.search(r"(\d+)\s+failed", stdout)
    skipped_match = re.search(r"(\d+)\s+skipped", stdout)
    flaky_match = re.search(r"(\d+)\s+flaky", stdout)

    if passed_match:
        passed = int(passed_match.group(1))
    if failed_match:
        failed = int(failed_match.group(1))
    if skipped_match:
        skipped = int(skipped_match.group(1))
    if flaky_match:
        flaky = int(flaky_match.group(1))

    total = passed + failed + skipped + flaky

    # Extract failure details
    fail_blocks = re.findall(
        r"(\d+)\)\s+\[(\w+)\]\s+›\s+(.+?)\s+›\s+(.+?)(?:\n.*?Error:\s*(.*?)(?:\n|$))?",
        stdout,
    )
    for block in fail_blocks:
        errors.append({
            "file": block[2].strip(),
            "test": block[3].strip(),
            "browser": block[1].strip(),
            "message": (block[4].strip() if len(block) > 4 else "")[:500],
        })

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "flaky": flaky,
        "errors": errors,
    }


def parse_junit_xml(report_path: Path) -> dict[str, Any]:
    """Parse JUnit XML test results."""
    total = passed = failed = skipped = 0
    errors: list[dict[str, str]] = []

    try:
        tree = ET.parse(report_path)
        root = tree.getroot()

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

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "flaky": 0,
        "errors": errors,
    }


def find_coverage_report(project_path: str) -> str | None:
    """Find coverage report file (Istanbul/V8)."""
    base = Path(project_path)

    candidates = [
        base / "coverage" / "coverage-summary.json",
        base / "coverage" / "lcov.info",
        base / "coverage" / "coverage-final.json",
        base / ".nyc_output" / "coverage-summary.json",
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


def detect_flaky_tests(
    project_path: str,
    failed_tests: list[dict[str, str]],
    retries: int = 2,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Retry failed tests to detect flaky ones.

    Returns (flaky_tests, truly_failed_tests).
    """
    if not failed_tests or retries < 1:
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

        for attempt in range(1, retries + 1):
            cmd = ["npx", "playwright", "test", test_file, "--retries=0"]
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
    shard: str | None = None,
) -> dict[str, str]:
    """Generate CI-ready reports in the report directory."""
    report_path = Path(report_dir)
    report_path.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, str] = {}

    # JUnit XML is generated by Playwright reporter automatically
    junit_file = report_path / "regression-results.xml"
    if junit_file.exists() and "junit-xml" in report_formats:
        artifacts["junitXml"] = str(junit_file)

    # Copy Playwright HTML report
    if "html" in report_formats:
        html_source = Path(project_path) / "playwright-report"
        html_dest = report_path / "report"
        if html_source.exists():
            if html_dest.exists():
                shutil.rmtree(html_dest)
            shutil.copytree(html_source, html_dest)
            artifacts["htmlReport"] = str(html_dest / "index.html")

    # Copy traces
    traces_source = Path(project_path) / "test-results"
    if traces_source.exists():
        trace_files = list(traces_source.rglob("*.zip"))
        if trace_files:
            traces_dest = report_path / "traces"
            traces_dest.mkdir(parents=True, exist_ok=True)
            for trace in trace_files:
                shutil.copy2(trace, traces_dest / trace.name)
            artifacts["traces"] = str(traces_dest)

    # Copy screenshots
    if traces_source.exists():
        screenshot_files = list(traces_source.rglob("*.png"))
        if screenshot_files:
            screenshots_dest = report_path / "screenshots"
            screenshots_dest.mkdir(parents=True, exist_ok=True)
            for ss in screenshot_files:
                shutil.copy2(ss, screenshots_dest / ss.name)
            artifacts["screenshots"] = str(screenshots_dest)

    # Generate JSON manifest
    if "json" in report_formats:
        json_dest = report_path / "regression-results.json"
        manifest = {
            "project": Path(project_path).name,
            "testRunner": "playwright",
            "testExecution": result.get("testExecution", {}),
            "coverage": result.get("coverage"),
            "sourceIntegrity": result.get("sourceIntegrity"),
        }
        if shard:
            manifest["shard"] = shard
        if "flakyTests" in result:
            manifest["flakyTests"] = result["flakyTests"]

        json_dest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        artifacts["jsonReport"] = str(json_dest)

    # Generate Markdown summary
    if "markdown" in report_formats:
        md_dest = report_path / "regression-summary.md"
        te = result.get("testExecution", {})
        lines = [
            "# Playwright Regression Test Summary\n",
            f"- **Total**: {te.get('total', 0)}",
            f"- **Passed**: {te.get('passed', 0)}",
            f"- **Failed**: {te.get('failed', 0)}",
            f"- **Skipped**: {te.get('skipped', 0)}",
        ]
        if te.get("flaky", 0) > 0:
            lines.append(f"- **Flaky**: {te.get('flaky', 0)}")
        if shard:
            lines.append(f"- **Shard**: {shard}")
        if artifacts.get("htmlReport"):
            lines.append(f"\n## HTML Report\nSee [{artifacts['htmlReport']}]({artifacts['htmlReport']})")
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
                ".test.", ".spec.", ".e2e.", ".ct.",
                "__tests__/", "e2e/", "tests/",
                "playwright-report/", "test-results/",
            ]
        )
    ]

    return {
        "pass": len(modified_files) == 0,
        "modifiedSourceFiles": modified_files,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Execute selected Playwright regression tests."
    )
    parser.add_argument("project_path", help="Path to the React project directory")
    parser.add_argument(
        "--test-runner", "-r",
        choices=["playwright"],
        default="playwright",
        help="Test runner (default: playwright)",
    )
    parser.add_argument(
        "--tests",
        help="Path to JSON file with test files to run (selected-tests.json)",
    )
    parser.add_argument(
        "--test-level",
        choices=["e2e", "component", "both"],
        default="e2e",
        help="Test level to run (default: e2e)",
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
        "--report-formats", default="junit-xml,html,json",
        help="Comma-separated list of report formats: junit-xml,html,json,markdown",
    )
    parser.add_argument(
        "--shard",
        help="Playwright shard format: N/M (e.g., 1/4 for first of four shards)",
    )
    parser.add_argument(
        "--retries", type=int, default=0,
        help="Number of retries for failed tests (for flaky detection, default: 0)",
    )
    parser.add_argument(
        "--browsers",
        help="Comma-separated list of browser projects to run (e.g., chromium,firefox)",
    )
    parser.add_argument(
        "--headed", action="store_true",
        help="Run tests in headed mode (visible browser)",
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

    # Detect Playwright config
    config_file = detect_playwright_config(str(project_path))
    if not config_file:
        print("Warning: No playwright.config.* found. Using Playwright defaults.", file=sys.stderr)

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

    # Parse browsers
    browsers = None
    if args.browsers:
        browsers = [b.strip() for b in args.browsers.split(",")]

    # Ensure report dir exists
    Path(args.report_dir).mkdir(parents=True, exist_ok=True)

    # Run tests
    result = run_playwright(
        str(project_path),
        test_files=test_files,
        shard=args.shard,
        retries=args.retries,
        browsers=browsers,
        headed=args.headed,
        report_dir=args.report_dir,
        config_file=config_file,
        test_level=args.test_level,
    )

    # Detect flaky tests (if not using Playwright's built-in retries)
    test_exec = result.get("testExecution", {})
    failed_errors = test_exec.get("errors", [])
    if args.retries == 0 and failed_errors:
        # Manual flaky detection when retries aren't configured
        flaky_tests, truly_failed = detect_flaky_tests(
            str(project_path), failed_errors, retries=2,
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

    if args.shard:
        result["shard"] = args.shard

    # Generate CI reports if requested
    if args.ci_mode:
        report_formats = [f.strip() for f in args.report_formats.split(",")]
        artifacts = generate_ci_reports(
            result, args.report_dir, report_formats,
            str(project_path), args.shard,
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
