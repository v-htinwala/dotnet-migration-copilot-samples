#!/usr/bin/env python3
"""
select-tests.py — Apply qualification criteria, rank, and select regression tests.

Usage:
    python select-tests.py --changes <json> --risks <json> --test-map <json>
                           [--config <json>] [--max-tests <N>] [--output <file>]
                           [--scenarios <yaml>]
                           [--shard-index <N> --total-shards <M>]

Combines change-based, risk-based, and coverage-based criteria to produce a
prioritized list of existing tests to run, and identifies coverage gaps needing
new test generation.
"""

import argparse
import fnmatch
import json
import sys
from pathlib import Path
from typing import Any


# Default qualification configuration
DEFAULT_CONFIG = {
    "change_based": {
        "enabled": True,
        "weight": 0.4,
    },
    "risk_based": {
        "enabled": True,
        "weight": 0.35,
        "min_risk_level": "medium",
    },
    "coverage_based": {
        "enabled": True,
        "weight": 0.25,
        "generate_for_uncovered": True,
    },
}

# Risk level numeric values
RISK_VALUES = {
    "critical": 100,
    "high": 75,
    "medium": 50,
    "low": 25,
}


def load_scenarios(filepath: str | None) -> list[dict[str, Any]]:
    """Load regression scenarios from a YAML file."""
    if not filepath:
        return []
    try:
        # Try YAML first, fall back to JSON
        path = Path(filepath)
        if not path.exists():
            return []
        content = path.read_text(encoding="utf-8")
        try:
            import yaml
            data = yaml.safe_load(content)
        except ImportError:
            # Fallback: try JSON format
            data = json.loads(content)
        return data.get("scenarios", []) if isinstance(data, dict) else []
    except Exception:
        return []


def calculate_scenario_boost(
    filepath: str,
    scenarios: list[dict[str, Any]],
    boost_points: float = 20.0,
) -> float:
    """Calculate priority boost if file is targeted by a user-defined scenario."""
    if not scenarios:
        return 0.0
    normalized = filepath.replace("\\", "/").lower()
    for scenario in scenarios:
        for pattern in scenario.get("target_files", []):
            norm_pattern = pattern.replace("\\", "/").lower()
            if fnmatch.fnmatch(normalized, norm_pattern):
                return boost_points
    return 0.0


def load_json(filepath: str) -> dict[str, Any]:
    """Load a JSON file."""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def calculate_change_relevance(
    filepath: str, changes_data: dict[str, Any]
) -> float:
    """Calculate change relevance score (0-100) for a file."""
    for change in changes_data.get("changes", []):
        if change["file"] == filepath:
            lines_changed = change.get("linesAdded", 0) + change.get("linesRemoved", 0)
            # Direct change gets high relevance, scaled by magnitude
            return min(100.0, 50 + lines_changed * 2)
    return 0.0


def calculate_impact_relevance(
    filepath: str, impact_data: dict[str, Any]
) -> float:
    """Calculate impact relevance score (0-100) based on dependency depth."""
    for impacted in impact_data.get("impactedFiles", []):
        if impacted["file"] == filepath:
            depth = impacted.get("depth", 0)
            if depth == 0:
                return 100.0  # Direct change
            elif depth == 1:
                return 70.0  # First-level dependent
            elif depth == 2:
                return 40.0  # Second-level dependent
            else:
                return max(10.0, 100 - depth * 30)
    return 0.0


def combined_score(
    filepath: str,
    changes_data: dict[str, Any],
    impact_data: dict[str, Any],
    risk_data: dict[str, Any],
    config: dict[str, Any],
    scenarios: list[dict[str, Any]] | None = None,
    scenario_boost_points: float = 20.0,
) -> dict[str, Any]:
    """Calculate the combined qualification score for a file."""
    change_relevance = 0.0
    risk_score = 0.0

    if config["change_based"]["enabled"]:
        change_relevance = max(
            calculate_change_relevance(filepath, changes_data),
            calculate_impact_relevance(filepath, impact_data),
        )

    if config["risk_based"]["enabled"]:
        for f in risk_data.get("files", []):
            if f["file"] == filepath:
                risk_score = f["riskScore"]
                break

    # Coverage component: use inverse of current coverage (estimated)
    # Actual coverage is checked in a separate phase
    coverage_gap = 50.0  # Default assumption: 50% uncovered

    weights = {
        "change": config["change_based"].get("weight", 0.4),
        "risk": config["risk_based"].get("weight", 0.35),
        "coverage": config["coverage_based"].get("weight", 0.25),
    }

    final = (
        weights["change"] * change_relevance +
        weights["risk"] * risk_score +
        weights["coverage"] * coverage_gap
    )

    # Apply scenario boost
    scenario_boost = calculate_scenario_boost(
        filepath, scenarios or [], scenario_boost_points
    )
    final += scenario_boost

    return {
        "file": filepath,
        "finalScore": round(final, 1),
        "changeRelevance": round(change_relevance, 1),
        "riskScore": round(risk_score, 1),
        "coverageGap": round(coverage_gap, 1),
        "scenarioBoost": round(scenario_boost, 1),
    }


def select_tests(
    test_map: dict[str, Any],
    scores: list[dict[str, Any]],
    risk_data: dict[str, Any],
    config: dict[str, Any],
    max_tests: int | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Select tests to run and identify coverage gaps."""
    # Build score lookup
    score_lookup = {s["file"]: s for s in scores}

    # Get risk level for filtering
    min_risk = config["risk_based"].get("min_risk_level", "medium")
    min_risk_value = RISK_VALUES.get(min_risk, 50)

    risk_lookup = {f["file"]: f for f in risk_data.get("files", [])}

    selected_tests: list[dict[str, Any]] = []
    coverage_gaps: list[dict[str, Any]] = []

    for mapping in test_map.get("mappings", []):
        source_file = mapping["sourceFile"]
        test_file = mapping.get("testFile")
        has_test = mapping.get("hasExistingTest", False)

        file_score = score_lookup.get(source_file, {})
        file_risk = risk_lookup.get(source_file, {})

        final_score = file_score.get("finalScore", 0)
        risk_level = file_risk.get("riskLevel", "low")
        risk_value = RISK_VALUES.get(risk_level, 25)

        # Filter by minimum risk level if risk-based is enabled
        if config["risk_based"]["enabled"] and risk_value < min_risk_value:
            # Still include if it's a direct change
            if file_score.get("changeRelevance", 0) < 50:
                continue

        if has_test and test_file:
            selected_tests.append({
                "sourceFile": source_file,
                "testFile": test_file,
                "priority": final_score,
                "riskLevel": risk_level,
                "reason": _build_reason(file_score, file_risk),
            })
        else:
            # No existing test — this is a coverage gap
            if config["coverage_based"].get("generate_for_uncovered", True):
                coverage_gaps.append({
                    "sourceFile": source_file,
                    "priority": final_score,
                    "riskLevel": risk_level,
                    "reason": f"No existing test for {source_file}",
                })

    # Sort by priority descending
    selected_tests.sort(key=lambda x: x["priority"], reverse=True)
    coverage_gaps.sort(key=lambda x: x["priority"], reverse=True)

    # Apply max tests cap
    if max_tests is not None and max_tests > 0:
        selected_tests = selected_tests[:max_tests]

    return selected_tests, coverage_gaps


def _build_reason(score: dict[str, Any], risk: dict[str, Any]) -> str:
    """Build a human-readable reason for test selection."""
    parts = []
    if score.get("changeRelevance", 0) >= 50:
        parts.append("directly changed")
    elif score.get("changeRelevance", 0) > 0:
        parts.append("impacted by change")
    if risk.get("riskLevel") in ("critical", "high"):
        parts.append(f"risk={risk['riskLevel']}")
    return "; ".join(parts) if parts else "qualification criteria met"


def main():
    parser = argparse.ArgumentParser(
        description="Apply qualification criteria, rank, and select regression tests."
    )
    parser.add_argument("--changes", required=True, help="Path to changes.json")
    parser.add_argument("--impact", help="Path to impact.json")
    parser.add_argument("--risks", required=True, help="Path to risk-scores.json")
    parser.add_argument("--test-map", required=True, help="Path to test-map.json")
    parser.add_argument("--config", help="Path to qualification config JSON")
    parser.add_argument("--max-tests", type=int, help="Maximum tests to select")
    parser.add_argument(
        "--scenarios",
        help="Path to regression scenarios YAML/JSON file for priority boosting",
    )
    parser.add_argument(
        "--shard-index", type=int,
        help="Current shard index for test splitting (0-based)",
    )
    parser.add_argument(
        "--total-shards", type=int,
        help="Total number of shards for test splitting",
    )
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    args = parser.parse_args()

    # Load data
    changes_data = load_json(args.changes)
    impact_data = load_json(args.impact) if args.impact else {"impactedFiles": []}
    risk_data = load_json(args.risks)
    test_map = load_json(args.test_map)

    # Load or use default config
    config = DEFAULT_CONFIG.copy()
    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                user_config = json.load(f)
            qualification = user_config.get("qualification", {})
            for key in config:
                if key in qualification:
                    config[key].update(qualification[key])

    # Load regression scenarios if provided
    scenarios = load_scenarios(args.scenarios)
    scenario_boost_points = 20.0  # Default boost; could be made configurable
    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                full_config = json.load(f)
            traceability = full_config.get("traceability", {})
            scenario_boost_points = traceability.get("scenario_priority_boost", 20.0)

    # Collect all unique source files from mappings
    all_sources = {m["sourceFile"] for m in test_map.get("mappings", [])}

    # Calculate scores for all files
    scores = []
    for filepath in all_sources:
        score = combined_score(
            filepath, changes_data, impact_data, risk_data, config,
            scenarios, scenario_boost_points,
        )
        scores.append(score)

    # Select tests and identify gaps
    selected_tests, coverage_gaps = select_tests(
        test_map, scores, risk_data, config, args.max_tests
    )

    # Apply test splitting (sharding) if requested
    shard_info = None
    if args.shard_index is not None and args.total_shards is not None:
        total_shards = max(1, args.total_shards)
        shard_index = args.shard_index % total_shards
        # Round-robin partition by index in priority-sorted list
        selected_tests = [
            t for i, t in enumerate(selected_tests) if i % total_shards == shard_index
        ]
        shard_info = {
            "index": shard_index,
            "total": total_shards,
        }

    result = {
        "totalSourceFiles": len(all_sources),
        "selectedTests": len(selected_tests),
        "coverageGaps": len(coverage_gaps),
        "config": config,
        "tests": selected_tests,
        "gaps": coverage_gaps,
    }

    if shard_info:
        result["shardInfo"] = shard_info

    if scenarios:
        result["scenariosLoaded"] = len(scenarios)

    output = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
