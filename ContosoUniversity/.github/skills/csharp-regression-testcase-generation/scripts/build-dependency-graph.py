#!/usr/bin/env python3
"""
build-dependency-graph.py — Build C# using-directive dependency graph.

Usage:
    python build-dependency-graph.py <codebase-path> --depth <N>
                                     [--changed-files <json>] [--output <file>]

Parses C# using directives, resolves via .csproj ProjectReference elements,
builds a dependency graph, and computes the impact set by traversing dependents
up to the specified depth.
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", ".svn", "bin", "obj", "out",
    ".vs", ".idea", ".vscode", "Migrations", "Generated",
    "TestResults", "packages",
}

# Test project name patterns
TEST_PROJECT_PATTERNS = [
    r"\.Tests$", r"\.Test$", r"\.UnitTests$", r"\.IntegrationTests$",
]


def is_test_project(project_name: str) -> bool:
    """Check if a project name indicates a test project."""
    return any(re.search(p, project_name) for p in TEST_PROJECT_PATTERNS)


def is_test_file(filepath: str) -> bool:
    """Check if a filepath is a test file."""
    name = Path(filepath).stem
    normalized = filepath.replace("\\", "/")
    if re.match(r".*Tests?$", name):
        return True
    for pattern in TEST_PROJECT_PATTERNS:
        if re.search(pattern.replace("$", "/"), normalized):
            return True
    return False


def extract_namespace(content: str) -> str:
    """Extract namespace declaration from C# source."""
    # File-scoped namespace: namespace Foo.Bar;
    match = re.search(r"namespace\s+([\w.]+)\s*;", content)
    if match:
        return match.group(1)
    # Block-scoped namespace: namespace Foo.Bar { ... }
    match = re.search(r"namespace\s+([\w.]+)\s*\{", content)
    if match:
        return match.group(1)
    return ""


def extract_usings(content: str) -> list[str]:
    """Extract using directives from C# source."""
    # using Foo.Bar; (not using static, not using alias = )
    usings = re.findall(r"using\s+(?!static\s)(?!\w+\s*=\s*)([\w.]+)\s*;", content)
    return usings


def extract_type_name(content: str) -> str | None:
    """Extract the primary class/interface/struct/record name."""
    match = re.search(
        r"(?:public|internal|protected|private)?\s*(?:abstract\s+|sealed\s+|static\s+|partial\s+)*"
        r"(?:class|interface|struct|record|enum)\s+(\w+)",
        content,
    )
    return match.group(1) if match else None


def parse_project_references(csproj_path: Path) -> list[str]:
    """Parse ProjectReference elements from a .csproj file."""
    refs = []
    try:
        tree = ET.parse(csproj_path)
        root = tree.getroot()
        # Handle with or without XML namespace
        for ref in root.findall(".//{*}ProjectReference"):
            include = ref.get("Include", "")
            if include:
                refs.append(include.replace("\\", "/"))
    except Exception:
        pass
    return refs


def build_file_index(codebase_path: Path) -> dict[str, str]:
    """
    Build a mapping from fully qualified type name to file path.
    Returns: {"Namespace.ClassName": "relative/path/ClassName.cs"}
    """
    index: dict[str, str] = {}

    for cs_file in codebase_path.rglob("*.cs"):
        rel_parts = cs_file.relative_to(codebase_path).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue

        try:
            content = cs_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        namespace = extract_namespace(content)
        type_name = extract_type_name(content)
        if type_name:
            fqn = f"{namespace}.{type_name}" if namespace else type_name
            rel_path = str(cs_file.relative_to(codebase_path)).replace("\\", "/")
            index[fqn] = rel_path

    return index


def build_namespace_to_files(codebase_path: Path) -> dict[str, list[str]]:
    """Build a mapping from namespace to files in that namespace."""
    ns_map: dict[str, list[str]] = {}

    for cs_file in codebase_path.rglob("*.cs"):
        rel_parts = cs_file.relative_to(codebase_path).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue

        try:
            content = cs_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        namespace = extract_namespace(content)
        if namespace:
            rel_path = str(cs_file.relative_to(codebase_path)).replace("\\", "/")
            ns_map.setdefault(namespace, [])
            ns_map[namespace].append(rel_path)

    return ns_map


def build_dependency_graph(
    codebase_path: Path,
    file_index: dict[str, str],
    ns_map: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Build a reverse dependency graph: file -> list of files that depend on it."""
    reverse: dict[str, list[str]] = {}

    for fqn, filepath in file_index.items():
        reverse.setdefault(filepath, [])

    for fqn, filepath in file_index.items():
        full_path = codebase_path / filepath
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        usings = extract_usings(content)
        deps = set()

        for using_ns in usings:
            # Check if any files are in this namespace
            if using_ns in ns_map:
                for dep_path in ns_map[using_ns]:
                    if dep_path != filepath:
                        deps.add(dep_path)

            # Check if the using matches a fully qualified type name
            if using_ns in file_index:
                dep_path = file_index[using_ns]
                if dep_path != filepath:
                    deps.add(dep_path)

        for dep in deps:
            reverse.setdefault(dep, [])
            if filepath not in reverse[dep]:
                reverse[dep].append(filepath)

    return reverse


def compute_impact_set(
    changed_files: list[str],
    reverse_deps: dict[str, list[str]],
    depth: int,
) -> dict[str, dict[str, Any]]:
    """Compute the impact set by traversing reverse dependencies."""
    impact: dict[str, dict[str, Any]] = {}

    frontier = set()
    for f in changed_files:
        impact[f] = {"depth": 0, "impactedBy": [f], "isDirectChange": True}
        frontier.add(f)

    for d in range(1, depth + 1):
        next_frontier = set()
        for f in frontier:
            dependents = reverse_deps.get(f, [])
            for dep in dependents:
                if dep not in impact:
                    impact[dep] = {
                        "depth": d,
                        "impactedBy": [f],
                        "isDirectChange": False,
                    }
                    next_frontier.add(dep)
                elif d == impact[dep]["depth"]:
                    if f not in impact[dep]["impactedBy"]:
                        impact[dep]["impactedBy"].append(f)
        frontier = next_frontier
        if not frontier:
            break

    return impact


def main():
    parser = argparse.ArgumentParser(
        description="Build C# using-directive dependency graph and compute impact set."
    )
    parser.add_argument("codebase_path", help="Path to the .NET solution root")
    parser.add_argument(
        "--depth", "-d", type=int, default=2,
        help="Dependency traversal depth (default: 2)",
    )
    parser.add_argument(
        "--changed-files", "-c",
        help="Path to changes.json (from analyze-changes.py)",
    )
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    args = parser.parse_args()

    codebase_path = Path(args.codebase_path).resolve()
    if not codebase_path.exists():
        print(f"Error: Path '{codebase_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    changed_files: list[str] = []
    if args.changed_files:
        changes_path = Path(args.changed_files)
        if changes_path.exists():
            with open(changes_path, encoding="utf-8") as f:
                changes_data = json.load(f)
            changed_files = [c["file"] for c in changes_data.get("changes", [])]

    print("Building file index...", file=sys.stderr)
    file_index = build_file_index(codebase_path)
    print(f"  Indexed {len(file_index)} C# types.", file=sys.stderr)

    print("Building namespace map...", file=sys.stderr)
    ns_map = build_namespace_to_files(codebase_path)

    print("Building dependency graph...", file=sys.stderr)
    reverse_deps = build_dependency_graph(codebase_path, file_index, ns_map)

    if changed_files:
        print(f"Computing impact set (depth={args.depth})...", file=sys.stderr)
        impact = compute_impact_set(changed_files, reverse_deps, args.depth)
    else:
        impact = {}

    impacted_files = []
    for filepath, info in sorted(impact.items()):
        impacted_files.append({
            "file": filepath,
            "depth": info["depth"],
            "impactedBy": info["impactedBy"],
            "isDirectChange": info["isDirectChange"],
            "isTestFile": is_test_file(filepath),
        })

    result = {
        "codebasePath": str(codebase_path),
        "totalIndexedTypes": len(file_index),
        "traversalDepth": args.depth,
        "changedFiles": changed_files,
        "totalImpacted": len(impacted_files),
        "directChanges": sum(1 for f in impacted_files if f["isDirectChange"]),
        "indirectImpacts": sum(1 for f in impacted_files if not f["isDirectChange"]),
        "impactedFiles": impacted_files,
    }

    output = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
