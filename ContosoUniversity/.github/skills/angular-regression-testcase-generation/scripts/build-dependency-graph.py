#!/usr/bin/env python3
"""
build-dependency-graph.py — Build TypeScript/Angular import dependency graph.

Usage:
    python build-dependency-graph.py <codebase-path> --depth <N>
                                     [--changed-files <json>] [--output <file>]

Parses TypeScript import statements and Angular @NgModule metadata, builds a
dependency graph, and computes the impact set by traversing dependents up to
the specified depth.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", ".svn", "dist", "coverage",
    ".angular", ".nyc_output", "tmp", "e2e",
}

# Test file patterns to identify (but still include in graph)
TEST_PATTERNS = [
    r".*\.spec\.ts$", r".*\.test\.ts$", r".*\.integration\.spec\.ts$",
]

# TypeScript source extensions to index
TS_EXTENSIONS = {".ts"}


def is_test_file(name: str) -> bool:
    """Check if a filename is a test file."""
    return any(re.match(p, name) for p in TEST_PATTERNS)


def extract_imports(content: str) -> list[str]:
    """Extract TypeScript import paths from source content."""
    imports = []

    # ES module imports: import { X } from 'path'; import X from 'path';
    es_imports = re.findall(
        r"""import\s+(?:(?:\{[^}]*\}|[\w*]+|\w+\s*,\s*\{[^}]*\})\s+from\s+)?['"]([^'"]+)['"]""",
        content,
    )
    imports.extend(es_imports)

    # Dynamic imports: import('path')
    dynamic_imports = re.findall(r"""import\s*\(\s*['"]([^'"]+)['"]\s*\)""", content)
    imports.extend(dynamic_imports)

    # require() calls: require('path')
    requires = re.findall(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""", content)
    imports.extend(requires)

    return imports


def extract_ng_module_deps(content: str) -> list[str]:
    """Extract Angular @NgModule imports, declarations, and providers."""
    deps = []

    # Match @NgModule({ imports: [...], declarations: [...], providers: [...] })
    ng_module_match = re.search(
        r"@NgModule\s*\(\s*\{(.*?)\}\s*\)", content, re.DOTALL
    )
    if ng_module_match:
        module_body = ng_module_match.group(1)
        # Extract array elements from imports, declarations, providers
        for key in ["imports", "declarations", "providers", "exports"]:
            array_match = re.search(
                rf"{key}\s*:\s*\[(.*?)\]", module_body, re.DOTALL
            )
            if array_match:
                items = array_match.group(1)
                # Extract identifiers (class names)
                identifiers = re.findall(r"\b([A-Z]\w+)\b", items)
                deps.extend(identifiers)

    return deps


def load_tsconfig_paths(codebase_path: Path) -> dict[str, str]:
    """Load path aliases from tsconfig.json."""
    paths: dict[str, str] = {}
    tsconfig_candidates = [
        codebase_path / "tsconfig.json",
        codebase_path / "tsconfig.app.json",
        codebase_path / "tsconfig.base.json",
    ]

    for tsconfig_path in tsconfig_candidates:
        if tsconfig_path.exists():
            try:
                content = tsconfig_path.read_text(encoding="utf-8")
                # Strip comments (// and /* */)
                content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
                content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
                config = json.loads(content)
                compiler_options = config.get("compilerOptions", {})
                ts_paths = compiler_options.get("paths", {})
                base_url = compiler_options.get("baseUrl", ".")
                for alias, targets in ts_paths.items():
                    if targets:
                        # Remove trailing /* from alias and target
                        clean_alias = alias.rstrip("/*")
                        clean_target = targets[0].rstrip("/*")
                        resolved = str((codebase_path / base_url / clean_target).resolve())
                        paths[clean_alias] = resolved
            except (json.JSONDecodeError, Exception):
                continue

    return paths


def resolve_import_path(
    import_path: str,
    source_file: Path,
    codebase_path: Path,
    ts_paths: dict[str, str],
) -> str | None:
    """Resolve a TypeScript import path to a relative file path."""
    # Skip external packages
    if not import_path.startswith(".") and not import_path.startswith("@app"):
        # Check tsconfig paths
        for alias, resolved_base in ts_paths.items():
            if import_path.startswith(alias):
                remainder = import_path[len(alias):].lstrip("/")
                resolved = Path(resolved_base) / remainder
                # Try with .ts extension
                for ext in [".ts", "/index.ts"]:
                    candidate = Path(str(resolved) + ext)
                    if candidate.exists():
                        return str(candidate.relative_to(codebase_path)).replace("\\", "/")
                return None
        return None  # External package

    # Relative import
    if import_path.startswith("."):
        base_dir = source_file.parent
        resolved = (base_dir / import_path).resolve()
    else:
        resolved = (codebase_path / "src" / import_path).resolve()

    # Try with various extensions
    for ext in [".ts", ".component.ts", ".service.ts", "/index.ts"]:
        candidate = Path(str(resolved) + ext)
        if candidate.exists():
            try:
                return str(candidate.relative_to(codebase_path)).replace("\\", "/")
            except ValueError:
                continue

    # Try exact path
    if resolved.exists() and resolved.is_file():
        try:
            return str(resolved.relative_to(codebase_path)).replace("\\", "/")
        except ValueError:
            pass

    return None


def build_file_index(codebase_path: Path) -> dict[str, str]:
    """
    Build a mapping from file path to class/component name.

    Returns: {"src/app/services/user.service.ts": "UserService", ...}
    """
    index: dict[str, str] = {}

    for ts_file in codebase_path.rglob("*.ts"):
        rel_parts = ts_file.relative_to(codebase_path).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue

        try:
            content = ts_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        # Extract primary class/interface/component name
        match = re.search(
            r"(?:export\s+)?(?:abstract\s+)?(?:class|interface|enum|type)\s+(\w+)",
            content,
        )
        name = match.group(1) if match else ts_file.stem
        rel_path = str(ts_file.relative_to(codebase_path)).replace("\\", "/")
        index[rel_path] = name

    return index


def build_dependency_graph(
    codebase_path: Path,
    file_index: dict[str, str],
    ts_paths: dict[str, str],
) -> dict[str, list[str]]:
    """
    Build a reverse dependency graph: for each file, list files that depend on it.

    Returns: {"src/app/.../A.ts": ["src/app/.../B.ts", ...]}
    """
    reverse: dict[str, list[str]] = {}

    # Initialize reverse for all files
    for filepath in file_index:
        reverse.setdefault(filepath, [])

    # Build forward dependencies and populate reverse
    for filepath in file_index:
        full_path = codebase_path / filepath
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        imports = extract_imports(content)
        for imp in imports:
            resolved = resolve_import_path(imp, full_path, codebase_path, ts_paths)
            if resolved and resolved in file_index and resolved != filepath:
                reverse.setdefault(resolved, [])
                if filepath not in reverse[resolved]:
                    reverse[resolved].append(filepath)

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
        impact[f] = {"depth": 0, "impactedBy": [f], "isDirectChange": True}
        frontier.add(f)

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
                    if f not in impact[dep]["impactedBy"]:
                        impact[dep]["impactedBy"].append(f)
        frontier = next_frontier
        if not frontier:
            break

    return impact


def main():
    parser = argparse.ArgumentParser(
        description="Build TypeScript/Angular import dependency graph and compute impact set."
    )
    parser.add_argument("codebase_path", help="Path to the Angular project root")
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

    # Load tsconfig paths for alias resolution
    print("Loading tsconfig paths...", file=sys.stderr)
    ts_paths = load_tsconfig_paths(codebase_path)
    if ts_paths:
        print(f"  Found {len(ts_paths)} path aliases.", file=sys.stderr)

    print("Building file index...", file=sys.stderr)
    file_index = build_file_index(codebase_path)
    print(f"  Indexed {len(file_index)} TypeScript files.", file=sys.stderr)

    print("Building dependency graph...", file=sys.stderr)
    reverse_deps = build_dependency_graph(codebase_path, file_index, ts_paths)

    if changed_files:
        print(f"Computing impact set (depth={args.depth})...", file=sys.stderr)
        impact = compute_impact_set(changed_files, reverse_deps, args.depth)
    else:
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
