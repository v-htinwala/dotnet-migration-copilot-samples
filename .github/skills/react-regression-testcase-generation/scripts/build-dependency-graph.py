#!/usr/bin/env python3
"""
build-dependency-graph.py — Build TypeScript/JavaScript import dependency graph for React.

Usage:
    python build-dependency-graph.py <codebase-path> --depth <N>
                                     [--changed-files <json>] [--output <file>]

Parses ESM import and CJS require() statements, resolves tsconfig.json paths,
builds a dependency graph, and computes the impact set by traversing dependents
up to the specified depth.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", ".svn", "dist", "build", ".next", "out",
    "coverage", ".cache", ".turbo", ".vercel", "__snapshots__",
}

# Source extensions
SOURCE_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}

# Test file patterns to identify (but still include in graph)
TEST_PATTERNS = [
    r".*\.(test|spec)\.(ts|tsx|js|jsx)$",
    r".*__tests__/.*\.(ts|tsx|js|jsx)$",
]


def is_test_file(name: str) -> bool:
    """Check if a filename is a test file."""
    return any(re.search(p, name) for p in TEST_PATTERNS)


def is_source_file(filepath: str) -> bool:
    """Check if a file is a source file."""
    return Path(filepath).suffix in SOURCE_EXTENSIONS


def extract_imports(content: str) -> list[str]:
    """Extract ESM import and CJS require() statements from TypeScript/JavaScript."""
    imports = []

    # ESM: import ... from 'module'
    esm_pattern = r"""(?:import\s+(?:[\w{},*\s]+\s+from\s+)?['"]([^'"]+)['"])"""
    imports.extend(re.findall(esm_pattern, content))

    # ESM: export ... from 'module'
    export_pattern = r"""export\s+(?:[\w{},*\s]+\s+from\s+)['"]([^'"]+)['"]"""
    imports.extend(re.findall(export_pattern, content))

    # CJS: require('module')
    cjs_pattern = r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)"""
    imports.extend(re.findall(cjs_pattern, content))

    # Dynamic import: import('module')
    dynamic_pattern = r"""import\s*\(\s*['"]([^'"]+)['"]\s*\)"""
    imports.extend(re.findall(dynamic_pattern, content))

    return imports


def load_tsconfig_paths(codebase_path: Path) -> dict[str, str]:
    """Load path aliases from tsconfig.json."""
    tsconfig_paths: dict[str, str] = {}
    tsconfig_file = codebase_path / "tsconfig.json"

    if not tsconfig_file.exists():
        return tsconfig_paths

    try:
        content = tsconfig_file.read_text(encoding="utf-8")
        # Remove comments (simple approach)
        content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        config = json.loads(content)

        paths = config.get("compilerOptions", {}).get("paths", {})
        base_url = config.get("compilerOptions", {}).get("baseUrl", ".")

        for alias, targets in paths.items():
            if targets:
                # Remove wildcard: "@/*" -> "@/", "src/*" -> "src/"
                clean_alias = alias.replace("/*", "/").rstrip("/")
                clean_target = targets[0].replace("/*", "/").rstrip("/")
                # Resolve relative to baseUrl
                resolved = str((codebase_path / base_url / clean_target).resolve())
                tsconfig_paths[clean_alias] = resolved
    except Exception:
        pass

    return tsconfig_paths


def resolve_import(
    import_path: str,
    importer_file: Path,
    codebase_path: Path,
    tsconfig_paths: dict[str, str],
    file_index: dict[str, str],
) -> str | None:
    """Resolve an import specifier to a file path relative to codebase."""
    # Skip external packages (no leading ./ or ../ and not in tsconfig paths)
    if not import_path.startswith(".") and not any(
        import_path.startswith(alias) for alias in tsconfig_paths
    ):
        return None

    # Resolve tsconfig path aliases
    resolved_path = import_path
    for alias, target in tsconfig_paths.items():
        if import_path.startswith(alias):
            resolved_path = import_path.replace(alias, target, 1)
            break

    # Resolve relative path
    if resolved_path.startswith("."):
        resolved_abs = (importer_file.parent / resolved_path).resolve()
    else:
        resolved_abs = Path(resolved_path)

    # Try various extensions and index files
    candidates = []
    resolved_str = str(resolved_abs)

    # Direct match with extensions
    for ext in [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"]:
        candidates.append(resolved_str + ext)

    # Index file
    for ext in [".ts", ".tsx", ".js", ".jsx"]:
        candidates.append(str(Path(resolved_str) / f"index{ext}"))

    # Direct match (already has extension)
    candidates.append(resolved_str)

    for candidate in candidates:
        candidate_path = Path(candidate)
        if candidate_path.exists():
            try:
                rel = str(candidate_path.relative_to(codebase_path)).replace("\\", "/")
                return rel
            except ValueError:
                continue

    return None


def build_file_index(codebase_path: Path) -> dict[str, str]:
    """Build a mapping from absolute path to relative path for all source files."""
    index: dict[str, str] = {}

    for src_file in codebase_path.rglob("*"):
        if not src_file.is_file():
            continue
        if src_file.suffix not in SOURCE_EXTENSIONS:
            continue

        rel_parts = src_file.relative_to(codebase_path).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue

        rel_path = str(src_file.relative_to(codebase_path)).replace("\\", "/")
        index[str(src_file.resolve())] = rel_path

    return index


def build_dependency_graph(
    codebase_path: Path,
    file_index: dict[str, str],
    tsconfig_paths: dict[str, str],
) -> dict[str, list[str]]:
    """Build a reverse dependency graph: for each file, list files that depend on it."""
    reverse: dict[str, list[str]] = {}

    # Initialize reverse for all files
    for abs_path, rel_path in file_index.items():
        reverse.setdefault(rel_path, [])

    # Build forward dependencies and populate reverse
    for abs_path, rel_path in file_index.items():
        full_path = Path(abs_path)
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        imports = extract_imports(content)

        for imp in imports:
            resolved = resolve_import(
                imp, full_path, codebase_path, tsconfig_paths, file_index
            )
            if resolved and resolved != rel_path:
                reverse.setdefault(resolved, [])
                if rel_path not in reverse[resolved]:
                    reverse[resolved].append(rel_path)

    return reverse


def compute_impact_set(
    changed_files: list[str],
    reverse_deps: dict[str, list[str]],
    depth: int,
) -> dict[str, dict[str, Any]]:
    """Compute the impact set by traversing reverse dependencies."""
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
        description="Build TypeScript/JavaScript import dependency graph and compute impact set."
    )
    parser.add_argument("codebase_path", help="Path to the React project root")
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

    print("Loading tsconfig.json paths...", file=sys.stderr)
    tsconfig_paths = load_tsconfig_paths(codebase_path)
    if tsconfig_paths:
        print(f"  Loaded {len(tsconfig_paths)} path aliases.", file=sys.stderr)

    print("Building file index...", file=sys.stderr)
    file_index = build_file_index(codebase_path)
    print(f"  Indexed {len(file_index)} source files.", file=sys.stderr)

    print("Building dependency graph...", file=sys.stderr)
    reverse_deps = build_dependency_graph(codebase_path, file_index, tsconfig_paths)

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
            "isTestFile": is_test_file(filepath),
        })

    result = {
        "codebasePath": str(codebase_path),
        "totalIndexedFiles": len(file_index),
        "tsconfigPathAliases": len(tsconfig_paths),
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
