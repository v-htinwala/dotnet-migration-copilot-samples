#!/usr/bin/env python3
"""
analyze-changes.py — Parse git diff for changed C# files.

Usage:
    python analyze-changes.py <codebase-path> [--ref HEAD~1] [--files file1,file2]
                              [--output <file>]

Detects changed C# source files from git diff or a user-provided file list.
Outputs changes.json with changed files and diff stats.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


# C# source file extensions
SOURCE_EXTENSIONS = {".cs"}

# Directories to exclude from change detection
EXCLUDE_DIRS = {
    "node_modules", ".git", ".svn", ".hg", "bin", "obj", "out",
    ".vs", ".idea", ".vscode", "Migrations", "Generated",
    "TestResults", "packages",
}

# File patterns to exclude
EXCLUDE_PATTERNS = [
    r"\.Designer\.cs$",
    r"\.g\.cs$",
    r"\.generated\.cs$",
    r"AssemblyInfo\.cs$",
    r"GlobalUsings\.cs$",
]


def run_git_command(cmd: list[str], cwd: str) -> str:
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"Warning: git command failed: {' '.join(cmd)}", file=sys.stderr)
            print(f"  stderr: {result.stderr.strip()}", file=sys.stderr)
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"Warning: git command timed out: {' '.join(cmd)}", file=sys.stderr)
        return ""
    except FileNotFoundError:
        print("Error: git not found. Ensure git is installed and on PATH.", file=sys.stderr)
        sys.exit(1)


def is_excluded(filepath: str) -> bool:
    """Check if a file path should be excluded."""
    parts = filepath.replace("\\", "/").split("/")
    if any(part in EXCLUDE_DIRS for part in parts):
        return True
    if any(re.search(p, filepath) for p in EXCLUDE_PATTERNS):
        return True
    return False


def is_cs_source(filepath: str) -> bool:
    """Check if a file is a C# source file."""
    return Path(filepath).suffix in SOURCE_EXTENSIONS


def is_test_file(filepath: str) -> bool:
    """Check if a file is a C# test file."""
    name = Path(filepath).name
    normalized = filepath.replace("\\", "/")
    if re.match(r".*Tests?\.cs$", name):
        return True
    if ".Tests/" in normalized or ".Test/" in normalized or ".UnitTests/" in normalized:
        return True
    return False


def parse_git_diff(codebase_path: str, ref: str) -> list[dict[str, Any]]:
    """Parse git diff output for changed files with stats."""
    diff_stat = run_git_command(
        ["git", "diff", "--numstat", ref], cwd=codebase_path
    )
    diff_names = run_git_command(
        ["git", "diff", "--name-status", ref], cwd=codebase_path
    )

    status_map: dict[str, str] = {}
    for line in diff_names.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            status = parts[0][0]
            filepath = parts[-1]
            status_map[filepath] = status

    changes: list[dict[str, Any]] = []
    for line in diff_stat.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added = parts[0]
        removed = parts[1]
        filepath = parts[2]

        if not is_cs_source(filepath):
            continue
        if is_excluded(filepath):
            continue

        change_type = status_map.get(filepath, "M")
        changes.append({
            "file": filepath,
            "changeType": {
                "A": "added",
                "M": "modified",
                "D": "deleted",
                "R": "renamed",
                "C": "copied",
            }.get(change_type, "modified"),
            "linesAdded": int(added) if added != "-" else 0,
            "linesRemoved": int(removed) if removed != "-" else 0,
            "isTestFile": is_test_file(filepath),
        })

    return changes


def parse_manual_file_list(
    codebase_path: str, files: list[str]
) -> list[dict[str, Any]]:
    """Create change entries from a manual file list."""
    changes = []
    for filepath in files:
        filepath = filepath.strip()
        if not filepath:
            continue
        if not is_cs_source(filepath):
            continue
        if is_excluded(filepath):
            continue

        full_path = Path(codebase_path) / filepath
        change_type = "modified" if full_path.exists() else "deleted"

        changes.append({
            "file": filepath,
            "changeType": change_type,
            "linesAdded": 0,
            "linesRemoved": 0,
            "isTestFile": is_test_file(filepath),
        })

    return changes


def detect_build_file_changes(codebase_path: str, ref: str) -> list[str]:
    """Detect changes to build/project files."""
    diff_names = run_git_command(
        ["git", "diff", "--name-only", ref], cwd=codebase_path
    )
    build_files = []
    build_patterns = [
        r"\.csproj$",
        r"\.sln$",
        r"Directory\.Build\.props$",
        r"Directory\.Build\.targets$",
        r"Directory\.Packages\.props$",
        r"nuget\.config$",
        r"global\.json$",
    ]
    for line in diff_names.strip().split("\n"):
        line = line.strip()
        if any(re.search(p, line) for p in build_patterns):
            build_files.append(line)
    return build_files


def main():
    parser = argparse.ArgumentParser(
        description="Parse git diff for changed C# files."
    )
    parser.add_argument("codebase_path", help="Path to the .NET solution root")
    parser.add_argument(
        "--ref", "-r", default="HEAD~1",
        help="Git ref to diff against (default: HEAD~1)",
    )
    parser.add_argument(
        "--files", "-f",
        help="Comma-separated list of files (skip git diff)",
    )
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    args = parser.parse_args()

    codebase_path = Path(args.codebase_path).resolve()
    if not codebase_path.exists():
        print(f"Error: Path '{codebase_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if args.files:
        file_list = [f.strip() for f in args.files.split(",")]
        changes = parse_manual_file_list(str(codebase_path), file_list)
        build_changes = []
    else:
        changes = parse_git_diff(str(codebase_path), args.ref)
        build_changes = detect_build_file_changes(str(codebase_path), args.ref)

    source_changes = [c for c in changes if not c["isTestFile"]]
    test_changes = [c for c in changes if c["isTestFile"]]

    result = {
        "codebasePath": str(codebase_path),
        "changeSource": args.files or f"git diff {args.ref}",
        "totalChanges": len(changes),
        "sourceChanges": len(source_changes),
        "testChanges": len(test_changes),
        "buildFileChanges": build_changes,
        "changes": source_changes,
        "testFileChanges": test_changes,
    }

    output = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
