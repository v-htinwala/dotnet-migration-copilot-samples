#!/usr/bin/env python3
"""
run-regression-tests.py — Execute selected Java regression tests via Maven or Gradle.

Usage:
    python run-regression-tests.py <module-path> --build-system <maven|gradle>
                                   [--tests <test-list-json>] [--module-name <name>]
                                   [--check-integrity] [--output <file>]
                                   [--include-integration] [--ci-mode]
                                   [--report-dir <path>] [--report-formats <list>]
                                   [--shard-index <N> --total-shards <M>]
                                   [--flaky-threshold <N>]

Runs the appropriate test command, parses results from Surefire/Gradle XML reports,
triggers JaCoCo coverage report generation, and outputs normalized JSON.
Supports integration tests (Failsafe/*IT.java), CI artifact generation,
test sharding, and flaky test detection.
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


def run_maven(
    module_path: str,
    module_name: str | None = None,
    test_classes: list[str] | None = None,
    include_integration: bool = False,
) -> dict[str, Any]:
    """Run Maven tests with optional selective test execution."""
    cmd = ["mvn", "test"]
    if module_name:
        cmd.extend(["-pl", module_name])
    if test_classes:
        # Run specific test classes
        test_param = ",".join(test_classes)
        cmd.extend([f"-Dtest={test_param}"])
    cmd.extend(["-B", "-q"])  # Batch mode, quiet

    result = run_command(cmd, cwd=module_path)
    test_results = parse_surefire_reports(module_path, module_name)

    # Run integration tests if requested
    integration_results = None
    if include_integration:
        int_cmd = ["mvn", "verify"]
        if module_name:
            int_cmd.extend(["-pl", module_name])
        int_cmd.extend(["-B", "-q"])
        run_command(int_cmd, cwd=module_path)
        integration_results = parse_failsafe_reports(module_path, module_name)

    # Generate JaCoCo report
    jacoco_cmd = ["mvn", "jacoco:report"]
    if module_name:
        jacoco_cmd.extend(["-pl", module_name])
    jacoco_cmd.extend(["-B", "-q"])
    run_command(jacoco_cmd, cwd=module_path)

    coverage_report = find_coverage_report(module_path, module_name)

    output = {
        "buildSystem": "maven",
        "command": " ".join(cmd),
        "exitCode": result["returncode"],
        "testExecution": test_results,
        "coverageReportPath": coverage_report,
        "coverageFormat": "jacoco" if coverage_report else None,
        "stdout": result["stdout"][-2000:] if result["stdout"] else "",
        "stderr": result["stderr"][-2000:] if result["stderr"] else "",
    }

    if integration_results:
        output["integrationTestExecution"] = integration_results

    return output


def run_gradle(
    module_path: str,
    module_name: str | None = None,
    test_classes: list[str] | None = None,
    include_integration: bool = False,
) -> dict[str, Any]:
    """Run Gradle tests with optional selective test execution."""
    if module_name:
        cmd = ["gradle", f":{module_name}:test", f":{module_name}:jacocoTestReport", "--quiet"]
    else:
        cmd = ["gradle", "test", "jacocoTestReport", "--quiet"]

    if test_classes:
        test_filter = " || ".join(f"it.name == '{tc}'" for tc in test_classes)
        cmd.extend(["--tests", ",".join(test_classes)])

    result = run_command(cmd, cwd=module_path)
    test_results = parse_gradle_reports(module_path, module_name)

    # Run integration tests if requested
    integration_results = None
    if include_integration:
        if module_name:
            int_cmd = ["gradle", f":{module_name}:integrationTest", "--quiet"]
        else:
            int_cmd = ["gradle", "integrationTest", "--quiet"]
        int_result = run_command(int_cmd, cwd=module_path)
        if int_result["returncode"] != -2:  # Task exists
            integration_results = parse_gradle_reports(
                module_path, module_name, report_subdir="integrationTest"
            )

    coverage_report = find_coverage_report(module_path, module_name, "gradle")

    output = {
        "buildSystem": "gradle",
        "command": " ".join(cmd),
        "exitCode": result["returncode"],
        "testExecution": test_results,
        "coverageReportPath": coverage_report,
        "coverageFormat": "jacoco" if coverage_report else None,
        "stdout": result["stdout"][-2000:] if result["stdout"] else "",
        "stderr": result["stderr"][-2000:] if result["stderr"] else "",
    }

    if integration_results:
        output["integrationTestExecution"] = integration_results

    return output


def parse_surefire_reports(
    module_path: str, module_name: str | None
) -> dict[str, Any]:
    """Parse Maven Surefire XML test results."""
    base = Path(module_path)
    if module_name:
        base = base / module_name

    reports_dir = base / "target" / "surefire-reports"
    total = passed = failed = skipped = 0
    errors: list[dict[str, str]] = []

    if reports_dir.exists():
        for xml_file in reports_dir.glob("TEST-*.xml"):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                total += int(root.get("tests", 0))
                failed += int(root.get("failures", 0))
                failed += int(root.get("errors", 0))
                skipped += int(root.get("skipped", 0))

                for testcase in root.findall(".//testcase"):
                    failure = testcase.find("failure") or testcase.find("error")
                    if failure is not None:
                        errors.append({
                            "file": testcase.get("classname", ""),
                            "test": testcase.get("name", ""),
                            "message": (failure.get("message", "") or "")[:500],
                        })
            except Exception:
                continue
        passed = total - failed - skipped

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
    }


def parse_gradle_reports(
    module_path: str, module_name: str | None,
    report_subdir: str = "test",
) -> dict[str, Any]:
    """Parse Gradle XML test results."""
    base = Path(module_path)
    if module_name:
        base = base / module_name

    reports_dir = base / "build" / "test-results" / report_subdir
    total = passed = failed = skipped = 0
    errors: list[dict[str, str]] = []

    if reports_dir.exists():
        for xml_file in reports_dir.glob("TEST-*.xml"):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                total += int(root.get("tests", 0))
                failed += int(root.get("failures", 0))
                failed += int(root.get("errors", 0))
                skipped += int(root.get("skipped", 0))

                for testcase in root.findall(".//testcase"):
                    failure = testcase.find("failure") or testcase.find("error")
                    if failure is not None:
                        errors.append({
                            "file": testcase.get("classname", ""),
                            "test": testcase.get("name", ""),
                            "message": (failure.get("message", "") or "")[:500],
                        })
            except Exception:
                continue
        passed = total - failed - skipped

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
    }


def find_coverage_report(
    module_path: str,
    module_name: str | None,
    build_system: str = "maven",
) -> str | None:
    """Find the JaCoCo coverage report file."""
    base = Path(module_path)
    if module_name:
        base = base / module_name

    if build_system == "maven":
        candidates = [
            base / "target" / "site" / "jacoco" / "jacoco.xml",
        ]
    else:  # gradle
        candidates = [
            base / "build" / "reports" / "jacoco" / "test" / "jacocoTestReport.xml",
        ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


def parse_failsafe_reports(
    module_path: str, module_name: str | None
) -> dict[str, Any]:
    """Parse Maven Failsafe XML test results for integration tests."""
    base = Path(module_path)
    if module_name:
        base = base / module_name

    reports_dir = base / "target" / "failsafe-reports"
    total = passed = failed = skipped = 0
    errors: list[dict[str, str]] = []

    if reports_dir.exists():
        for xml_file in reports_dir.glob("TEST-*.xml"):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                total += int(root.get("tests", 0))
                failed += int(root.get("failures", 0))
                failed += int(root.get("errors", 0))
                skipped += int(root.get("skipped", 0))

                for testcase in root.findall(".//testcase"):
                    failure = testcase.find("failure") or testcase.find("error")
                    if failure is not None:
                        errors.append({
                            "file": testcase.get("classname", ""),
                            "test": testcase.get("name", ""),
                            "message": (failure.get("message", "") or "")[:500],
                        })
            except Exception:
                continue
        passed = total - failed - skipped

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
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
    module_path: str,
    build_system: str,
    module_name: str | None,
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
        test_class = test_error.get("file", "")
        if not test_class:
            truly_failed.append(test_error)
            continue

        passed_on_retry = False
        retries_needed = 0

        for attempt in range(1, flaky_threshold + 1):
            if build_system == "maven":
                cmd = ["mvn", "test", f"-Dtest={test_class}", "-B", "-q"]
                if module_name:
                    cmd.extend(["-pl", module_name])
            else:
                cmd = ["gradle", "test", "--tests", test_class, "--quiet"]
                if module_name:
                    cmd[1] = f":{module_name}:test"

            result = run_command(cmd, cwd=module_path, timeout=120)
            if result["returncode"] == 0:
                passed_on_retry = True
                retries_needed = attempt
                break

        if passed_on_retry:
            flaky.append({
                "file": test_class,
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
    module_name: str | None,
    build_system: str,
    shard_info: dict[str, int] | None = None,
) -> dict[str, str]:
    """Generate CI-ready reports in the report directory."""
    report_path = Path(report_dir)
    report_path.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, str] = {}

    # Copy/aggregate XML reports
    if "junit-xml" in report_formats:
        xml_dest = report_path / "regression-results.xml"
        base = Path(module_path)
        if module_name:
            base = base / module_name

        # Aggregate all Surefire/Failsafe/Gradle XML into one file
        if build_system == "maven":
            source_dirs = [
                base / "target" / "surefire-reports",
                base / "target" / "failsafe-reports",
            ]
        else:
            source_dirs = [
                base / "build" / "test-results" / "test",
                base / "build" / "test-results" / "integrationTest",
            ]

        # Create aggregated XML
        root = ET.Element("testsuites")
        for src_dir in source_dirs:
            if src_dir.exists():
                for xml_file in src_dir.glob("TEST-*.xml"):
                    try:
                        tree = ET.parse(xml_file)
                        root.append(tree.getroot())
                    except Exception:
                        continue

        tree = ET.ElementTree(root)
        tree.write(str(xml_dest), encoding="unicode", xml_declaration=True)
        artifacts["junitXml"] = str(xml_dest)

    # Generate JSON manifest
    if "json" in report_formats:
        json_dest = report_path / "regression-results.json"
        manifest = {
            "module": module_name or Path(module_path).name,
            "buildSystem": build_system,
            "testExecution": result.get("testExecution", {}),
            "coverage": result.get("coverage"),
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


def check_source_integrity(module_path: str) -> dict[str, Any]:
    """Check if any source files were modified using git."""
    result = run_command(["git", "diff", "--name-only"], cwd=module_path)
    modified_files = [
        f for f in result["stdout"].strip().split("\n")
        if f and not any(
            pattern in f
            for pattern in ["src/test/", "Test.java", "Tests.java", "IT.java"]
        )
    ]

    return {
        "pass": len(modified_files) == 0,
        "modifiedSourceFiles": modified_files,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Execute selected Java regression tests via Maven or Gradle."
    )
    parser.add_argument("module_path", help="Path to the module directory")
    parser.add_argument(
        "--build-system", "-b", required=True,
        choices=["maven", "gradle"],
        help="Build system type",
    )
    parser.add_argument(
        "--module-name", "-m",
        help="Module name (for multi-module projects)",
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
        help="Also run integration tests (*IT.java via Failsafe/integrationTest)",
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
    test_classes = None
    if args.tests:
        tests_path = Path(args.tests)
        if tests_path.exists():
            with open(tests_path, encoding="utf-8") as f:
                tests_data = json.load(f)
            # Extract test class names from selected-tests.json
            test_classes = []
            for test in tests_data.get("tests", []):
                test_file = test.get("testFile", "")
                # Convert path to class name: src/test/java/com/Foo.java -> com.Foo
                class_name = test_file
                if "src/test/java/" in class_name:
                    class_name = class_name.split("src/test/java/", 1)[1]
                class_name = class_name.replace("/", ".").replace(".java", "")
                test_classes.append(class_name)

    # Apply test splitting (sharding)
    shard_info = None
    if args.shard_index is not None and args.total_shards is not None:
        total_shards = max(1, args.total_shards)
        shard_index = args.shard_index % total_shards
        shard_info = {"index": shard_index, "total": total_shards}
        if test_classes:
            test_classes = split_tests_for_shard(test_classes, shard_index, total_shards)
            print(
                f"Shard {shard_index}/{total_shards}: running {len(test_classes)} tests",
                file=sys.stderr,
            )

    # Run tests
    if args.build_system == "maven":
        result = run_maven(
            str(module_path), args.module_name, test_classes, args.include_integration
        )
    else:
        result = run_gradle(
            str(module_path), args.module_name, test_classes, args.include_integration
        )

    # Detect flaky tests
    test_exec = result.get("testExecution", {})
    failed_errors = test_exec.get("errors", [])
    if args.flaky_threshold > 0 and failed_errors:
        flaky_tests, truly_failed = detect_flaky_tests(
            str(module_path), args.build_system, args.module_name,
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
            str(module_path), args.module_name, args.build_system, shard_info,
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
