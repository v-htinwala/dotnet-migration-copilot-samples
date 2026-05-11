#!/usr/bin/env python3
"""
run-regression-tests.py — Execute selected C# regression tests via dotnet test.

Usage:
    python run-regression-tests.py <project-path> --test-framework <xunit|nunit>
                                   [--tests <test-list-json>] [--project-name <name>]
                                   [--check-integrity] [--output <file>]
                                   [--include-integration] [--ci-mode]
                                   [--report-dir <path>] [--report-formats <list>]
                                   [--shard-index <N> --total-shards <M>]
                                   [--flaky-threshold <N>]

Runs dotnet test, parses TRX results, triggers coverlet coverage report generation,
and outputs normalized JSON. Supports integration tests (*.IntegrationTests projects),
CI artifact generation, test sharding, and flaky test detection.
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
            "stderr": f"Command not found: {cmd[0]}. Ensure dotnet SDK is installed.",
        }


def run_dotnet_test(
    project_path: str,
    project_name: str | None = None,
    test_filter: str | None = None,
    include_integration: bool = False,
) -> dict[str, Any]:
    """Run dotnet test with optional selective test execution."""
    cmd = ["dotnet", "test"]

    if project_name:
        cmd.append(project_name)

    cmd.extend([
        "--results-directory", "TestResults",
        "--logger", "trx",
        '--collect:"XPlat Code Coverage"',
    ])

    if test_filter:
        cmd.extend(["--filter", test_filter])

    result = run_command(cmd, cwd=project_path)
    test_results = parse_trx_reports(project_path)
    coverage_report = find_coverage_report(project_path)

    # Run integration tests if requested
    integration_results = None
    if include_integration:
        int_projects = find_integration_test_projects(project_path)
        if int_projects:
            for int_proj in int_projects:
                int_cmd = ["dotnet", "test", int_proj,
                           "--results-directory", "TestResults",
                           "--logger", "trx",
                           '--collect:"XPlat Code Coverage"']
                run_command(int_cmd, cwd=project_path)
            integration_results = parse_trx_reports(project_path, prefix="integration")

    output = {
        "testFramework": "dotnet",
        "command": " ".join(cmd),
        "exitCode": result["returncode"],
        "testExecution": test_results,
        "coverageReportPath": coverage_report,
        "coverageFormat": "cobertura" if coverage_report else None,
        "stdout": result["stdout"][-2000:] if result["stdout"] else "",
        "stderr": result["stderr"][-2000:] if result["stderr"] else "",
    }

    if integration_results:
        output["integrationTestExecution"] = integration_results

    return output


def find_integration_test_projects(project_path: str) -> list[str]:
    """Find integration test project files."""
    base = Path(project_path)
    projects = []
    for csproj in base.rglob("*.IntegrationTests.csproj"):
        projects.append(str(csproj.relative_to(base)))
    return projects


def parse_trx_reports(project_path: str) -> dict[str, Any]:
    """Parse TRX test result files."""
    total = passed = failed = skipped = 0
    errors: list[dict[str, str]] = []

    results_dir = Path(project_path) / "TestResults"
    if not results_dir.exists():
        return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": []}

    # TRX uses a namespace
    ns = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}

    for trx_file in results_dir.glob("*.trx"):
        try:
            tree = ET.parse(trx_file)
            root = tree.getroot()

            counters = root.find(".//t:ResultSummary/t:Counters", ns)
            if counters is not None:
                total += int(counters.get("total", 0))
                passed += int(counters.get("passed", 0))
                failed += int(counters.get("failed", 0))
                skipped += int(counters.get("notExecuted", 0))

            for result in root.findall(".//t:UnitTestResult", ns):
                outcome = result.get("outcome", "")
                if outcome == "Failed":
                    test_name = result.get("testName", "")
                    output_elem = result.find("t:Output/t:ErrorInfo/t:Message", ns)
                    message = output_elem.text[:500] if output_elem is not None and output_elem.text else ""
                    errors.append({
                        "file": "",
                        "test": test_name,
                        "message": message,
                    })
        except Exception:
            continue

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
    }


def find_coverage_report(project_path: str) -> str | None:
    """Find the Cobertura coverage report file."""
    results_dir = Path(project_path) / "TestResults"
    if not results_dir.exists():
        return None

    # coverlet generates coverage in TestResults/<guid>/coverage.cobertura.xml
    for cobertura in results_dir.rglob("coverage.cobertura.xml"):
        return str(cobertura)

    return None


def check_source_integrity(project_path: str) -> dict[str, Any]:
    """Check if any source files were modified using git."""
    result = run_command(["git", "diff", "--name-only"], cwd=project_path)
    modified_files = [
        f for f in result["stdout"].strip().split("\n")
        if f and not any(
            pattern in f
            for pattern in [".Tests/", ".Test/", "Tests.cs", "Test.cs", "TestResults/"]
        )
    ]

    return {
        "pass": len(modified_files) == 0,
        "modifiedSourceFiles": modified_files,
    }


def split_tests_for_shard(
    test_classes: list[str],
    shard_index: int,
    total_shards: int,
) -> list[str]:
    """Partition test list using round-robin for test splitting."""
    if total_shards <= 1:
        return test_classes
    return [tc for i, tc in enumerate(test_classes) if i % total_shards == shard_index]


def detect_flaky_tests(
    project_path: str,
    project_name: str | None,
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
        test_name = test_error.get("test", "")
        if not test_name:
            truly_failed.append(test_error)
            continue

        passed_on_retry = False
        retries_needed = 0

        for attempt in range(1, flaky_threshold + 1):
            cmd = ["dotnet", "test", "--filter", f"FullyQualifiedName~{test_name}"]
            if project_name:
                cmd.insert(2, project_name)

            result = run_command(cmd, cwd=project_path, timeout=120)
            if result["returncode"] == 0:
                passed_on_retry = True
                retries_needed = attempt
                break

        if passed_on_retry:
            flaky.append({
                "file": test_error.get("file", ""),
                "test": test_name,
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

    # Copy TRX reports
    if "trx" in report_formats:
        results_dir = Path(project_path) / "TestResults"
        if results_dir.exists():
            trx_dest = report_path / "regression-results.trx"
            for trx_file in results_dir.glob("*.trx"):
                shutil.copy2(str(trx_file), str(trx_dest))
                artifacts["trx"] = str(trx_dest)
                break  # Take the most recent

    # Generate JSON manifest
    if "json" in report_formats:
        json_dest = report_path / "regression-results.json"
        manifest = {
            "project": Path(project_path).name,
            "testExecution": result.get("testExecution", {}),
            "coverage": result.get("coverageReportPath"),
            "sourceIntegrity": result.get("sourceIntegrity"),
        }
        if shard_info:
            manifest["shardInfo"] = shard_info
        if "flakyTests" in result:
            manifest["flakyTests"] = result["flakyTests"]
        if "integrationTestExecution" in result:
            manifest["integrationTestExecution"] = result["integrationTestExecution"]

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


def main():
    parser = argparse.ArgumentParser(
        description="Execute selected C# regression tests via dotnet test."
    )
    parser.add_argument("project_path", help="Path to the project/solution directory")
    parser.add_argument(
        "--test-framework", "-f",
        choices=["xunit", "nunit", "mstest"],
        default="xunit",
        help="Test framework type (default: xunit)",
    )
    parser.add_argument(
        "--project-name", "-p",
        help="Test project name or path",
    )
    parser.add_argument(
        "--tests",
        help="Path to JSON file with test classes to run (selected-tests.json)",
    )
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument(
        "--check-integrity", action="store_true",
        help="Check source file integrity after tests",
    )
    parser.add_argument(
        "--include-integration", action="store_true",
        help="Also run integration test projects (*.IntegrationTests)",
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
        "--report-formats", default="trx,json",
        help="Comma-separated list of report formats: trx,json,markdown,html",
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

    # Build test filter from selected tests
    test_filter = None
    if args.tests:
        tests_path = Path(args.tests)
        if tests_path.exists():
            with open(tests_path, encoding="utf-8") as f:
                tests_data = json.load(f)
            test_classes = []
            for test in tests_data.get("tests", []):
                test_file = test.get("testFile", "")
                class_name = Path(test_file).stem
                test_classes.append(class_name)
            if test_classes:
                # dotnet test --filter "FullyQualifiedName~Class1|FullyQualifiedName~Class2"
                test_filter = "|".join(f"FullyQualifiedName~{tc}" for tc in test_classes)

    # Apply test splitting (sharding)
    shard_info = None
    if args.shard_index is not None and args.total_shards is not None:
        total_shards = max(1, args.total_shards)
        shard_index = args.shard_index % total_shards
        shard_info = {"index": shard_index, "total": total_shards}
        if test_classes:
            test_classes = split_tests_for_shard(test_classes, shard_index, total_shards)
            test_filter = "|".join(f"FullyQualifiedName~{tc}" for tc in test_classes) if test_classes else None
            print(
                f"Shard {shard_index}/{total_shards}: running {len(test_classes)} tests",
                file=sys.stderr,
            )

    result = run_dotnet_test(str(project_path), args.project_name, test_filter, args.include_integration)

    # Detect flaky tests
    test_exec = result.get("testExecution", {})
    failed_errors = test_exec.get("errors", [])
    if args.flaky_threshold > 0 and failed_errors:
        flaky_tests, truly_failed = detect_flaky_tests(
            str(project_path), args.project_name,
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
