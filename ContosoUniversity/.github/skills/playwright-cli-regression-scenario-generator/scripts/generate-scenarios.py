#!/usr/bin/env python3
"""
generate-scenarios.py — Transform regression-analysis.json into regression-scenarios.yml

Reads the risk-scored regression analysis output and generates:
  1. regression-scenarios.yml  (structured YAML for orchestrator)
  2. regression-scenarios.md   (natural language Markdown for orchestrator)
  3. orchestrator-inputs.json  (convenience file with pre-computed params)

Usage:
    python generate-scenarios.py \
        --analysis regression-analysis.json \
        --output-dir ./discovery-output \
        [--interactions interaction-inventory.json] \
        [--api-surface api-surface.json] \
        [--requirement-ids "REQ-001,REQ-002"] \
        [--base-url "https://example.com"]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def to_pascal_case(name: str) -> str:
    """Convert a flow name to PascalCase scenario name."""
    # Remove special characters, keep alphanumeric and spaces
    clean = re.sub(r"[^a-zA-Z0-9\s]", " ", name)
    words = clean.split()
    return "".join(w.capitalize() for w in words)


def risk_to_priority(risk_level: str) -> str:
    """Map risk level to priority."""
    mapping = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
    }
    return mapping.get(risk_level.lower(), "medium")


def generate_target_files(routes: List[str]) -> List[str]:
    """Generate glob patterns for target files from routes."""
    patterns = set()
    for route in routes:
        # Extract resource segment: /api/orders/:id -> orders
        segments = [s for s in route.strip("/").split("/") if s and not s.startswith(":")]
        if segments:
            # Use the last non-parameter segment as the feature name
            resource = segments[-1] if len(segments) <= 2 else segments[0]
            patterns.add(f'"src/features/{resource}/**"')
            patterns.add(f'"src/components/{resource.capitalize()}*.tsx"')
    return sorted(patterns) if patterns else ['"src/**"']


# ---------------------------------------------------------------------------
# Behavior generation
# ---------------------------------------------------------------------------

CATEGORY_BEHAVIORS = {
    "navigation": [
        'Clicking navigation link at {route} navigates to correct target',
        'Browser back button returns to previous route from {route}',
    ],
    "user_interaction": [
        'Interactive elements at {route} respond to click events',
        'Button actions at {route} trigger expected operations',
    ],
    "form_handling": [
        'Form at {route} renders with all required fields',
        'Form at {route} shows validation error for empty required fields',
        'Form submission at {route} calls expected API endpoint',
        'Validation errors display inline next to invalid fields at {route}',
    ],
    "api_integration": [
        'Page at {route} loads data from API endpoint',
        'Error response from API shows user-friendly error message at {route}',
    ],
    "routing": [
        'Route {route} resolves with valid parameters',
        'Invalid route parameters show 404 or error page',
    ],
    "authentication": [
        'Login form accepts credentials and authenticates user',
        'Protected route {route} redirects to login without auth',
        'Logout clears session and redirects to login page',
    ],
    "modal_dialog": [
        'Modal at {route} can be opened by trigger element',
        'Modal can be dismissed via Escape key',
        'Modal confirm action performs expected operation',
    ],
    "table_data": [
        'Table at {route} renders data from API',
        'Clicking column header sorts table data',
        'Pagination controls navigate between pages',
    ],
    "error_boundary": [
        'Error state at {route} shows user-friendly message',
        'Error boundary provides recovery action',
    ],
    "responsive_layout": [
        'Layout at {route} adapts to mobile viewport',
        'Navigation remains accessible at all viewport sizes',
    ],
}


def generate_behaviors(
    flow: Dict[str, Any],
    interactions: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Generate expected behaviors for a flow based on its categories."""
    behaviors: List[str] = []
    routes = flow.get("routes", [])
    categories = flow.get("regression_categories", [])
    primary_route = routes[0] if routes else "/"

    # Page rendering for all routes
    for route in routes[:5]:  # Limit to first 5 routes
        behaviors.append(f"Page at {route} should render successfully")

    # Category-based behaviors
    for category in categories:
        templates = CATEGORY_BEHAVIORS.get(category, [])
        for template in templates:
            behavior = template.format(route=primary_route)
            if behavior not in behaviors:
                behaviors.append(behavior)

    # API-based behaviors
    api_endpoints = flow.get("api_endpoints", [])
    for ep in api_endpoints[:3]:  # Limit to first 3 endpoints
        behaviors.append(f"API {ep} should return expected response for {primary_route}")

    # Cap at 15 behaviors per scenario
    return behaviors[:15]


# ---------------------------------------------------------------------------
# YAML output
# ---------------------------------------------------------------------------

def to_yaml_string(scenarios: List[Dict[str, Any]]) -> str:
    """Serialize scenarios to YAML string without external dependencies."""
    lines = [
        "# =============================================================================",
        "# Regression Scenarios — Generated by playwright-cli-regression-scenario-generator",
        "# =============================================================================",
        "# Auto-generated from live web application discovery data.",
        "# Compatible with regression-orchestrator agent input #11.",
        "# =============================================================================",
        "",
        "scenarios:",
    ]

    for scenario in scenarios:
        lines.append("")
        lines.append(f"  - name: {scenario['name']}")

        # Description (block scalar)
        lines.append("    description: >")
        desc = scenario.get("description", "")
        # Wrap description at ~72 chars
        words = desc.split()
        line_buf = "      "
        for word in words:
            if len(line_buf) + len(word) + 1 > 78:
                lines.append(line_buf.rstrip())
                line_buf = "      " + word + " "
            else:
                line_buf += word + " "
        if line_buf.strip():
            lines.append(line_buf.rstrip())

        # List fields
        for field in ["target_files", "target_routes", "api_endpoints",
                       "expected_behaviors", "requirement_ids"]:
            values = scenario.get(field, [])
            if values:
                lines.append(f"    {field}:")
                for v in values:
                    # Quote strings that contain special YAML chars
                    if any(c in str(v) for c in ":#{}[]|>&*!%@"):
                        lines.append(f'      - "{v}"')
                    else:
                        lines.append(f"      - \"{v}\"")

        lines.append(f"    priority: {scenario.get('priority', 'medium')}")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Markdown output
# ---------------------------------------------------------------------------

def to_markdown_string(scenarios: List[Dict[str, Any]]) -> str:
    """Serialize scenarios to natural language Markdown."""
    lines = [
        "# Regression Scenarios",
        "",
        "> Auto-generated from live web application discovery data by",
        "> `playwright-cli-regression-scenario-generator`.",
        "",
    ]

    for scenario in scenarios:
        name = scenario["name"]
        lines.append(f"## Scenario: {name}")
        lines.append("")
        lines.append(f"**Priority**: {scenario.get('priority', 'medium').capitalize()}")

        routes = scenario.get("target_routes", [])
        if routes:
            lines.append(f"**Routes**: {', '.join(routes)}")

        endpoints = scenario.get("api_endpoints", [])
        if endpoints:
            lines.append(f"**API Endpoints**: {', '.join(endpoints)}")

        lines.append("")
        desc = scenario.get("description", "")
        if desc:
            lines.append(desc)
            lines.append("")

        behaviors = scenario.get("expected_behaviors", [])
        if behaviors:
            lines.append("### Expected Behaviors")
            lines.append("")
            for b in behaviors:
                lines.append(f"- {b}")
            lines.append("")

        req_ids = scenario.get("requirement_ids", [])
        if req_ids:
            lines.append(f"**Requirement IDs**: {', '.join(req_ids)}")

        target_files = scenario.get("target_files", [])
        if target_files:
            lines.append(f"**Target Files**: {', '.join(target_files)}")

        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_scenarios(
    analysis: Dict[str, Any],
    interactions: Optional[Dict[str, Any]],
    api_surface: Optional[Dict[str, Any]],
    requirement_ids: Optional[List[str]],
) -> List[Dict[str, Any]]:
    """Build scenario list from regression analysis data."""
    scenarios = []
    flows = analysis.get("flows", [])

    # Sort flows by risk score descending
    flows_sorted = sorted(flows, key=lambda f: f.get("risk_score", 0), reverse=True)

    for flow in flows_sorted:
        name = to_pascal_case(flow.get("name", "UnknownFlow"))
        risk_level = flow.get("risk_level", "medium")
        routes = flow.get("routes", [])
        api_eps = flow.get("api_endpoints", [])

        # Use provided target_files or generate from routes
        target_files = flow.get("target_files", [])
        if not target_files:
            target_files = generate_target_files(routes)

        # Build description
        route_list = ", ".join(routes[:5]) if routes else "unknown routes"
        category_list = ", ".join(flow.get("regression_categories", []))
        description = (
            f"Regression coverage for {flow.get('name', name)} "
            f"spanning routes {route_list}. "
            f"Risk score: {flow.get('risk_score', 0)}. "
            f"Categories: {category_list}."
        )

        # Generate behaviors
        behaviors = generate_behaviors(flow, interactions)

        # Requirement IDs
        req_ids = flow.get("requirement_ids", [])
        if not req_ids and requirement_ids:
            # Assign from user-provided pool
            prefix = name[:3].upper()
            req_ids = [f"REQ-{prefix}-{str(i+1).zfill(3)}" for i in range(min(3, len(routes)))]

        scenario = {
            "name": name,
            "description": description,
            "target_files": target_files,
            "target_routes": routes,
            "api_endpoints": api_eps,
            "expected_behaviors": behaviors,
            "requirement_ids": req_ids,
            "priority": risk_to_priority(risk_level),
        }
        scenarios.append(scenario)

    return scenarios


def main():
    parser = argparse.ArgumentParser(
        description="Generate regression-scenarios.yml from regression analysis"
    )
    parser.add_argument(
        "--analysis", required=True,
        help="Path to regression-analysis.json",
    )
    parser.add_argument(
        "--output-dir", default="./discovery-output",
        help="Output directory (default: ./discovery-output)",
    )
    parser.add_argument(
        "--interactions",
        help="Path to interaction-inventory.json (optional)",
    )
    parser.add_argument(
        "--api-surface",
        help="Path to api-surface.json (optional)",
    )
    parser.add_argument(
        "--requirement-ids",
        help="Comma-separated requirement IDs for traceability",
    )
    parser.add_argument(
        "--base-url", default="https://example.com",
        help="Base URL of the web application",
    )
    args = parser.parse_args()

    # Load analysis
    analysis_path = Path(args.analysis)
    if not analysis_path.exists():
        print(f"Error: {analysis_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(analysis_path) as f:
        analysis = json.load(f)

    # Load optional inputs
    interactions = None
    if args.interactions:
        with open(args.interactions) as f:
            interactions = json.load(f)

    api_surface = None
    if args.api_surface:
        with open(args.api_surface) as f:
            api_surface = json.load(f)

    req_ids = args.requirement_ids.split(",") if args.requirement_ids else None

    # Build scenarios
    scenarios = build_scenarios(analysis, interactions, api_surface, req_ids)

    # Write outputs
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. YAML
    yaml_path = output_dir / "regression-scenarios.yml"
    yaml_path.write_text(to_yaml_string(scenarios), encoding="utf-8")
    print(f"Wrote {yaml_path} ({len(scenarios)} scenarios)")

    # 2. Markdown
    md_path = output_dir / "regression-scenarios.md"
    md_path.write_text(to_markdown_string(scenarios), encoding="utf-8")
    print(f"Wrote {md_path}")

    # 3. Orchestrator inputs JSON
    priority_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for s in scenarios:
        p = s.get("priority", "medium")
        priority_counts[p] = priority_counts.get(p, 0) + 1

    orchestrator_inputs = {
        "regression_scenarios": str(yaml_path),
        "test_framework": "playwright",
        "test_level": "e2e",
        "base_url": args.base_url,
        "browser_targets": "chromium",
        "scenario_count": len(scenarios),
        "critical_count": priority_counts["critical"],
        "high_count": priority_counts["high"],
        "medium_count": priority_counts["medium"],
        "low_count": priority_counts["low"],
    }

    inputs_path = output_dir / "orchestrator-inputs.json"
    inputs_path.write_text(
        json.dumps(orchestrator_inputs, indent=2), encoding="utf-8"
    )
    print(f"Wrote {inputs_path}")


if __name__ == "__main__":
    main()
