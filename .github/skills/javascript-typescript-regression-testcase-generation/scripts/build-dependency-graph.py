#!/usr/bin/env python3
"""
build-dependency-graph.py — Build JS/TS import dependency graph.

Usage:
    python build-dependency-graph.py <codebase-path> --depth <N>
                                     [--changed-files <json>] [--output <file>]

Parses ESM import and CJS require() statements, resolves tsconfig.json path
aliases, builds a dependency graph, and computes the impact set by traversing
dependents up to the specified depth.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", ".svn", "dist", "build", "out",
    ".next", ".nuxt", ".output", "coverage", ".cache", ".turbo",
    ".parcel-cache", "generated", "__generated__",
}

# Source file extensions
SOURCE_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}

# Test file indicator patterns
TEST_PATTERNS = [
    r".*\.(test|spec)\.(js|jsx|ts|tsx|mjs|cjs)$",
    r"__tests__/",
]


def is_test_file(filepath: str) -> bool:
    """Check if a filepath is a test file."""
    return any(re.search(p, filepath) for p in TEST_PATTERNS)


def load_tsconfig_paths(codebase_path: Path) -> dict[str, str]:
    """Load path aliases from tsconfig.json."""
    aliases: dict[str, str] = {}
    tsconfig_path = codebase_path / "tsconfig.json"
    if not tsconfig_path.exists():
        return aliases

    try:
        content = tsconfig_path.read_text(encoding="utf-8")
        # Strip comments (// and /* */)
        content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        config = json.loads(content)

        base_url = config.get("compilerOptions", {}).get("baseUrl", ".")
        paths = config.get("compilerOptions", {}).get("paths", {})

        for alias, targets in paths.items():
            if targets:
                # Strip trailing /* from alias and target
                alias_prefix = alias.rstrip("*").rstrip("/")
                target_prefix = targets[0].rstrip("*").rstrip("/")
                resolved = str((codebase_path / base_url / target_prefix).resolve())
                aliases[alias_prefix] = resolved
    except (json.JSONDecodeError, KeyError, IndexError):
        pass

    return aliases


def extract_imports(content: str) -> list[str]:
    """Extract import specifiers from JS/TS source."""
    imports = []

    # ESM: import ... from 'module'  /  import 'module'
    esm_pattern = r"""(?:import\s+(?:(?:[\w{}\s,*]+)\s+from\s+)?['"]([^'"]+)['"])"""
    imports.extend(re.findall(esm_pattern, content))

    # CJS: require('module')
    cjs_pattern = r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)"""
    imports.extend(re.findall(cjs_pattern, content))

    # Dynamic import: import('module')
    dynamic_pattern = r"""import\s*\(\s*['"]([^'"]+)['"]\s*\)"""
    imports.extend(re.findall(dynamic_pattern, content))

    # Filter out external packages (no relative path, no alias)
    return imports


def resolve_import(
    specifier: str,
    source_file: Path,
    codebase_path: Path,
    file_index: dict[str, str],
    tsconfig_aliases: dict[str, str],
) -> str | None:
    """Resolve an import specifier to a file path relative to codebase."""
    # Relative imports
    if specifier.startswith("."):
        base_dir = source_file.parent
        resolved = (base_dir / specifier).resolve()
        return _try_resolve_file(resolved, codebase_path, file_index)

    # tsconfig path aliases
    for alias, target_dir in tsconfig_aliases.items():
        if specifier == alias or specifier.startswith(alias + "/"):
            remainder = specifier[len(alias):].lstrip("/")
            resolved = Path(target_dir) / remainder
            return _try_resolve_file(resolved.resolve(), codebase_path, file_index)

    # Bare specifiers starting with @ could be scoped packages or aliases
    # Skip external node_modules packages
    return None


def _try_resolve_file(
    resolved: Path, codebase_path: Path, file_index: dict[str, str]
) -> str | None:
    """Try to resolve a path to an existing file with extension."""
    # Try exact path first
    if resolved.suffix in SOURCE_EXTENSIONS:
        rel = _rel_path(resolved, codebase_path)
        if rel and rel in file_index:
            return rel
        return None

    # Try adding extensions
    for ext in [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"]:
        candidate = resolved.with_suffix(ext)
        rel = _rel_path(candidate, codebase_path)
        if rel and rel in file_index:
            return rel

    # Try index files (barrel imports)
    for index_name in ["index.ts", "index.tsx", "index.js", "index.jsx"]:
        candidate = resolved / index_name
        rel = _rel_path(candidate, codebase_path)
        if rel and rel in file_index:
            return rel

    return None


def _rel_path(filepath: Path, codebase_path: Path) -> str | None:
    """Get relative path string, or None if not under codebase."""
    try:
        return str(filepath.relative_to(codebase_path)).replace("\\", "/")
    except ValueError:
        return None


def build_file_index(codebase_path: Path) -> dict[str, str]:
    """Build an index of all source files: relative_path -> relative_path."""
    index: dict[str, str] = {}

    for ext in SOURCE_EXTENSIONS:
        for source_file in codebase_path.rglob(f"*{ext}"):
            rel_parts = source_file.relative_to(codebase_path).parts
            if any(part in SKIP_DIRS for part in rel_parts):
                continue
            rel_path = str(source_file.relative_to(codebase_path)).replace("\\", "/")
            index[rel_path] = rel_path

    return index


def build_dependency_graph(
    codebase_path: Path,
    file_index: dict[str, str],
    tsconfig_aliases: dict[str, str],
) -> dict[str, list[str]]:
    """Build a reverse dependency graph: file -> list of files that import it."""
    reverse: dict[str, list[str]] = {}

    for filepath in file_index:
        reverse.setdefault(filepath, [])

    for filepath in file_index:
        full_path = codebase_path / filepath
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        # Remove comments and strings to reduce false positives
        content_clean = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
        content_clean = re.sub(r"/\*.*?\*/", "", content_clean, flags=re.DOTALL)

        imports = extract_imports(content_clean)
        deps = set()

        for specifier in imports:
            resolved = resolve_import(
                specifier, full_path, codebase_path, file_index, tsconfig_aliases
            )
            if resolved and resolved != filepath:
                deps.add(resolved)

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
        description="Build JS/TS import dependency graph and compute impact set."
    )
    parser.add_argument("codebase_path", help="Path to the JS/TS project root")
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

    print("Loading tsconfig path aliases...", file=sys.stderr)
    tsconfig_aliases = load_tsconfig_paths(codebase_path)

    print("Building file index...", file=sys.stderr)
    file_index = build_file_index(codebase_path)
    print(f"  Indexed {len(file_index)} JS/TS files.", file=sys.stderr)

    print("Building dependency graph...", file=sys.stderr)
    reverse_deps = build_dependency_graph(codebase_path, file_index, tsconfig_aliases)

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
        "totalIndexedFiles": len(file_index),
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
