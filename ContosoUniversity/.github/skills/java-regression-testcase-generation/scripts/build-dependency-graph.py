#!/usr/bin/env python3
"""
build-dependency-graph.py — Build Java import dependency graph.

Usage:
    python build-dependency-graph.py <codebase-path> --depth <N>
                                     [--changed-files <json>] [--output <file>]

Parses Java import statements, builds a dependency graph, and computes the
impact set by traversing dependents up to the specified depth.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", ".svn", "target", "build", "out",
    ".gradle", ".idea", ".vscode", "generated", "generated-sources",
    "generated-test-sources", "bin", "obj",
}

# Test file patterns to identify (but still include in graph)
TEST_PATTERNS = [
    r".*Test\.java$", r".*Tests\.java$", r".*IT\.java$", r".*Spec\.java$",
]


def is_test_file(name: str) -> bool:
    """Check if a filename is a test file."""
    return any(re.match(p, name) for p in TEST_PATTERNS)


def extract_package(content: str) -> str:
    """Extract package declaration from Java source."""
    match = re.search(r"package\s+([\w.]+)\s*;", content)
    return match.group(1) if match else ""


def extract_imports(content: str) -> list[str]:
    """Extract import statements from Java source."""
    imports = re.findall(r"import\s+(?:static\s+)?([\w.]+)\s*;", content)
    return imports


def extract_class_name(content: str) -> str | None:
    """Extract the primary class/interface name."""
    match = re.search(
        r"(?:public\s+)?(?:abstract\s+)?(?:final\s+)?"
        r"(?:class|interface|enum|record)\s+(\w+)",
        content,
    )
    return match.group(1) if match else None


def build_file_index(codebase_path: Path) -> dict[str, str]:
    """
    Build a mapping from fully qualified class name to file path.

    Returns: {"com.example.UserService": "src/main/java/com/example/UserService.java"}
    """
    index: dict[str, str] = {}

    for java_file in codebase_path.rglob("*.java"):
        rel_parts = java_file.relative_to(codebase_path).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue

        try:
            content = java_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        package = extract_package(content)
        class_name = extract_class_name(content)
        if class_name:
            fqcn = f"{package}.{class_name}" if package else class_name
            rel_path = str(java_file.relative_to(codebase_path)).replace("\\", "/")
            index[fqcn] = rel_path

    return index


def build_dependency_graph(
    codebase_path: Path, file_index: dict[str, str]
) -> dict[str, list[str]]:
    """
    Build a reverse dependency graph: for each file, list files that depend on it.

    Returns: {"src/main/java/.../A.java": ["src/main/java/.../B.java", ...]}
    """
    # Forward deps: file -> list of files it imports
    forward: dict[str, list[str]] = {}
    # Reverse deps: file -> list of files that import it
    reverse: dict[str, list[str]] = {}

    # Initialize reverse for all files
    for fqcn, filepath in file_index.items():
        reverse.setdefault(filepath, [])

    # Build forward dependencies
    for fqcn, filepath in file_index.items():
        full_path = codebase_path / filepath
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        imports = extract_imports(content)
        deps = []
        for imp in imports:
            # Handle wildcard imports: com.example.* -> match all in that package
            if imp.endswith(".*"):
                prefix = imp[:-2]
                for other_fqcn, other_path in file_index.items():
                    if other_fqcn.startswith(prefix) and other_path != filepath:
                        deps.append(other_path)
            else:
                # Direct import or static import (strip method name for static)
                # Try exact match first
                if imp in file_index:
                    dep_path = file_index[imp]
                    if dep_path != filepath:
                        deps.append(dep_path)
                else:
                    # For static imports, try stripping the last segment
                    parent = imp.rsplit(".", 1)[0]
                    if parent in file_index:
                        dep_path = file_index[parent]
                        if dep_path != filepath:
                            deps.append(dep_path)

        forward[filepath] = list(set(deps))

        # Populate reverse
        for dep in forward[filepath]:
            reverse.setdefault(dep, [])
            if filepath not in reverse[dep]:
                reverse[dep].append(filepath)

    return reverse


def compute_impact_set(
    changed_files: list[str],
    reverse_deps: dict[str, list[str]],
    depth: int,
) -> dict[str, dict[str, Any]]:
    """
    Compute the impact set by traversing reverse dependencies.

    Returns: {filepath: {"depth": N, "impactedBy": [list of changed files]}}
    """
    impact: dict[str, dict[str, Any]] = {}

    # Seed with changed files at depth 0
    frontier = set()
    for f in changed_files:
        if f in reverse_deps or f in {v for vals in reverse_deps.values() for v in vals}:
            impact[f] = {"depth": 0, "impactedBy": [f], "isDirectChange": True}
            frontier.add(f)
        else:
            # File exists but has no dependents recorded
            impact[f] = {"depth": 0, "impactedBy": [f], "isDirectChange": True}

    # BFS traversal up to specified depth
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
                    # Same depth, additional impact source
                    if f not in impact[dep]["impactedBy"]:
                        impact[dep]["impactedBy"].append(f)
        frontier = next_frontier
        if not frontier:
            break

    return impact


def main():
    parser = argparse.ArgumentParser(
        description="Build Java import dependency graph and compute impact set."
    )
    parser.add_argument("codebase_path", help="Path to the Java project root")
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

    # Load changed files
    changed_files: list[str] = []
    if args.changed_files:
        changes_path = Path(args.changed_files)
        if changes_path.exists():
            with open(changes_path, encoding="utf-8") as f:
                changes_data = json.load(f)
            changed_files = [c["file"] for c in changes_data.get("changes", [])]
        else:
            print(f"Warning: Changes file '{args.changed_files}' not found.", file=sys.stderr)

    print("Building file index...", file=sys.stderr)
    file_index = build_file_index(codebase_path)
    print(f"  Indexed {len(file_index)} Java classes.", file=sys.stderr)

    print("Building dependency graph...", file=sys.stderr)
    reverse_deps = build_dependency_graph(codebase_path, file_index)

    if changed_files:
        print(f"Computing impact set (depth={args.depth})...", file=sys.stderr)
        impact = compute_impact_set(changed_files, reverse_deps, args.depth)
    else:
        # If no changed files provided, just output the graph structure
        impact = {}

    # Build result
    impacted_files = []
    for filepath, info in sorted(impact.items()):
        impacted_files.append({
            "file": filepath,
            "depth": info["depth"],
            "impactedBy": info["impactedBy"],
            "isDirectChange": info["isDirectChange"],
            "isTestFile": is_test_file(Path(filepath).name),
        })

    result = {
        "codebasePath": str(codebase_path),
        "totalIndexedClasses": len(file_index),
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
