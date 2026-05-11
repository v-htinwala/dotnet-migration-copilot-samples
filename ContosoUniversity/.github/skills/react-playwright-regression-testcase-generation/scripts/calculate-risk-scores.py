#!/usr/bin/env python3
"""
calculate-risk-scores.py — Compute risk scores for React/TypeScript/JavaScript files.

Usage:
    python calculate-risk-scores.py <files-json> [--window 90] [--weights <json>]
                                    [--codebase <path>] [--criticality-map <json>]
                                    [--output <file>]

Calculates a composite risk score per file based on:
  - Cyclomatic complexity (regex-based)
  - Change frequency (git log)
  - Defect history (git log grep)
  - Business criticality (path heuristics for React)

This script is identical to the Jest/Vitest variant — risk scoring is
framework-agnostic.
"""

import argparse
import fnmatch
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


# Default weights for risk factors
DEFAULT_WEIGHTS = {
    "complexity": 0.3,
    "change_frequency": 0.3,
    "defect_history": 0.2,
    "business_criticality": 0.2,
}

# Risk level thresholds
RISK_LEVELS = [
    (76, "critical"),
    (51, "high"),
    (26, "medium"),
    (0, "low"),
]

# Cyclomatic complexity keywords for TypeScript/JavaScript/React
COMPLEXITY_KEYWORDS = [
    r"\bif\b",
    r"\belse\s+if\b",
    r"\bfor\b",
    r"\bwhile\b",
    r"\bdo\b",
    r"\bswitch\b",
    r"\bcase\b",
    r"\bcatch\b",
    r"\?\.",          # Optional chaining
    r"\?\?",          # Nullish coalescing
    r"\?[^?.?:]",     # Ternary operator
    r"&&",
    r"\|\|",
    r"\.then\b",      # Promise chains
    r"\bawait\b",     # Async control flow
    r"\.catch\b",     # Promise error handling
]

# Business criticality path heuristics for React
CRITICALITY_HIGH = [
    r"hooks?/",
    r"context/",
    r"api/",
    r"pages?/",
    r"app/",
    r"auth/",
    r"payment/",
    r"features?/",
    r"providers?/",
    r"middleware/",
    r"store/",
    r"slices?/",
]

CRITICALITY_LOW = [
    r"types?/",
    r"interfaces?/",
    r"models?/",
    r"constants?/",
    r"utils?/",
    r"helpers?/",
    r"styles?/",
    r"assets?/",
    r"__mocks__/",
    r"__fixtures__/",
]


# User-defined criticality level mapping
CRITICALITY_LEVEL_VALUES = {
    "critical": 1.0,
    "high": 0.8,
    "medium": 0.5,
    "low": 0.2,
}


def run_git_command(cmd: list[str], cwd: str) -> str:
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=30,
        )
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def calculate_cyclomatic_complexity(filepath: Path) -> int:
    """Calculate cyclomatic complexity using regex-based counting."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return 1

    content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    content = re.sub(r'"(?:[^"\\]|\\.)*"', '""', content)
    content = re.sub(r"'(?:[^'\\]|\\.)*'", "''", content)
    content = re.sub(r"`(?:[^`\\]|\\.)*`", "``", content)

    complexity = 1
    for pattern in COMPLEXITY_KEYWORDS:
        complexity += len(re.findall(pattern, content))

    return complexity


def calculate_change_frequency(
    filepath: str, codebase_path: str, window_days: int
) -> int:
    """Count how often a file has been changed in the past N days."""
    cmd = [
        "git", "log",
        f"--since={window_days} days ago",
        "--follow", "--oneline",
        "--", filepath,
    ]
    output = run_git_command(cmd, cwd=codebase_path)
    return len([line for line in output.strip().split("\n") if line.strip()])


def calculate_defect_history(filepath: str, codebase_path: str) -> int:
    """Count defect-related commits touching this file."""
    cmd = [
        "git", "log",
        r"--grep=fix\|bug\|defect\|hotfix\|patch\|issue",
        "-i", "--oneline",
        "--", filepath,
    ]
    output = run_git_command(cmd, cwd=codebase_path)
    return len([line for line in output.strip().split("\n") if line.strip()])


def calculate_business_criticality(
    filepath: str,
    user_overrides: dict[str, str] | None = None,
    default_level: str = "medium",
) -> float:
    """Estimate business criticality."""
    normalized = filepath.replace("\\", "/").lower()

    if user_overrides:
        for pattern, level in user_overrides.items():
            norm_pattern = pattern.replace("\\", "/").lower()
            if fnmatch.fnmatch(normalized, norm_pattern):
                return CRITICALITY_LEVEL_VALUES.get(level.lower(), 0.5)

    for pattern in CRITICALITY_HIGH:
        if re.search(pattern, normalized):
            return 0.8

    for pattern in CRITICALITY_LOW:
        if re.search(pattern, normalized):
            return 0.2

    return CRITICALITY_LEVEL_VALUES.get(default_level.lower(), 0.5)


def normalize_score(value: float, max_value: float) -> float:
    """Normalize a raw metric to 0-100 scale using log scaling."""
    if max_value <= 0:
        return 0.0
    normalized = min(1.0, math.log1p(value) / math.log1p(max_value))
    return normalized * 100


def get_risk_level(score: float) -> str:
    """Map a numeric risk score to a risk level."""
    for threshold, level in RISK_LEVELS:
        if score >= threshold:
            return level
    return "low"


def main():
    parser = argparse.ArgumentParser(
        description="Compute risk scores for React/TypeScript/JavaScript files."
    )
    parser.add_argument(
        "files_json",
        help="Path to JSON file with list of files to score (impact.json or changes.json)",
    )
    parser.add_argument(
        "--codebase", "-c",
        help="Codebase path (for git commands). Default: detected from files_json.",
    )
    parser.add_argument(
        "--window", "-w", type=int, default=90,
        help="Change frequency window in days (default: 90)",
    )
    parser.add_argument(
        "--weights",
        help='JSON string with factor weights, e.g. \'{"complexity":0.3,"change_frequency":0.3}\'',
    )
    parser.add_argument(
        "--criticality-map",
        help="Path to JSON file mapping file/package glob patterns to criticality levels",
    )
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    args = parser.parse_args()

    files_path = Path(args.files_json)
    if not files_path.exists():
        print(f"Error: File '{files_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    with open(files_path, encoding="utf-8") as f:
        data = json.load(f)

    if "impactedFiles" in data:
        files = [
            f["file"] for f in data["impactedFiles"]
            if not f.get("isTestFile", False)
        ]
        codebase_path = args.codebase or data.get("codebasePath", ".")
    elif "changes" in data:
        files = [c["file"] for c in data["changes"]]
        codebase_path = args.codebase or data.get("codebasePath", ".")
    else:
        print("Error: Unrecognized JSON format. Expected impactedFiles or changes.", file=sys.stderr)
        sys.exit(1)

    weights = DEFAULT_WEIGHTS.copy()
    if args.weights:
        try:
            custom_weights = json.loads(args.weights)
            weights.update(custom_weights)
        except json.JSONDecodeError:
            print(f"Warning: Invalid weights JSON, using defaults.", file=sys.stderr)

    user_criticality_overrides: dict[str, str] | None = None
    criticality_default_level = "medium"
    if args.criticality_map:
        crit_path = Path(args.criticality_map)
        if crit_path.exists():
            try:
                with open(crit_path, encoding="utf-8") as f:
                    crit_data = json.load(f)
                if "overrides" in crit_data:
                    user_criticality_overrides = crit_data["overrides"]
                    criticality_default_level = crit_data.get("default_level", "medium")
                else:
                    user_criticality_overrides = crit_data
                print(f"Loaded {len(user_criticality_overrides)} criticality overrides.", file=sys.stderr)
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Could not load criticality map: {e}", file=sys.stderr)
        else:
            print(f"Warning: Criticality map file '{crit_path}' not found.", file=sys.stderr)

    codebase_resolved = Path(codebase_path).resolve()

    print(f"Calculating risk scores for {len(files)} files...", file=sys.stderr)
    raw_metrics: list[dict[str, Any]] = []

    for filepath in files:
        full_path = codebase_resolved / filepath
        complexity = calculate_cyclomatic_complexity(full_path) if full_path.exists() else 1
        change_freq = calculate_change_frequency(filepath, str(codebase_resolved), args.window)
        defect_hist = calculate_defect_history(filepath, str(codebase_resolved))
        biz_crit = calculate_business_criticality(
            filepath, user_criticality_overrides, criticality_default_level
        )

        raw_metrics.append({
            "file": filepath,
            "rawComplexity": complexity,
            "rawChangeFrequency": change_freq,
            "rawDefectHistory": defect_hist,
            "rawBusinessCriticality": biz_crit,
        })

    max_complexity = max((m["rawComplexity"] for m in raw_metrics), default=1)
    max_change_freq = max((m["rawChangeFrequency"] for m in raw_metrics), default=1)
    max_defect_hist = max((m["rawDefectHistory"] for m in raw_metrics), default=1)

    scored_files: list[dict[str, Any]] = []
    for m in raw_metrics:
        norm_complexity = normalize_score(m["rawComplexity"], max_complexity)
        norm_change_freq = normalize_score(m["rawChangeFrequency"], max_change_freq)
        norm_defect_hist = normalize_score(m["rawDefectHistory"], max_defect_hist)
        norm_biz_crit = m["rawBusinessCriticality"] * 100

        composite = (
            weights["complexity"] * norm_complexity +
            weights["change_frequency"] * norm_change_freq +
            weights["defect_history"] * norm_defect_hist +
            weights["business_criticality"] * norm_biz_crit
        )

        risk_level = get_risk_level(composite)

        scored_files.append({
            "file": m["file"],
            "riskScore": round(composite, 1),
            "riskLevel": risk_level,
            "factors": {
                "complexity": round(norm_complexity, 1),
                "changeFrequency": round(norm_change_freq, 1),
                "defectHistory": round(norm_defect_hist, 1),
                "businessCriticality": round(norm_biz_crit, 1),
            },
            "raw": {
                "complexity": m["rawComplexity"],
                "changeFrequency": m["rawChangeFrequency"],
                "defectHistory": m["rawDefectHistory"],
                "businessCriticality": m["rawBusinessCriticality"],
            },
        })

    scored_files.sort(key=lambda x: x["riskScore"], reverse=True)

    distribution = {
        "critical": sum(1 for f in scored_files if f["riskLevel"] == "critical"),
        "high": sum(1 for f in scored_files if f["riskLevel"] == "high"),
        "medium": sum(1 for f in scored_files if f["riskLevel"] == "medium"),
        "low": sum(1 for f in scored_files if f["riskLevel"] == "low"),
    }

    result = {
        "totalFiles": len(scored_files),
        "weights": weights,
        "windowDays": args.window,
        "distribution": distribution,
        "files": scored_files,
    }

    output = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
