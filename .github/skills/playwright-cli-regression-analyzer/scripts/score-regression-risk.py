#!/usr/bin/env python3
"""
score-regression-risk.py — Compute per-route and per-flow risk scores.

Uses the risk scoring criteria to calculate regression risk scores for
each discovered route and identified flow.

Usage:
    python score-regression-risk.py \
        --site-map <site-map.json> \
        --interactions <interaction-inventory.json> \
        --api-surface <api-surface.json> \
        --auth-flows <auth-flows.json> \
        --flow-graph <flow-graph.json> \
        [--output <regression-analysis.json>]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse


# Scoring thresholds
RISK_LEVELS = {
    "critical": 75,
    "high": 50,
    "medium": 25,
    "low": 0,
}

# Factor weights (must sum to 1.0)
WEIGHTS = {
    "interactive_elements": 0.25,
    "api_calls": 0.20,
    "form_fields": 0.20,
    "state_indicators": 0.15,
    "auth_required": 0.10,
    "nav_depth": 0.10,
}

# Regression categories
REGRESSION_CATEGORIES = [
    "navigation",
    "interaction",
    "form-handling",
    "api-integration",
    "routing",
    "authentication",
    "modal-dialog",
    "table-data",
    "error-boundary",
    "responsive-layout",
]


def load_json(path: str) -> dict:
    """Load and parse a JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error loading {path}: {e}", file=sys.stderr)
        sys.exit(1)


def extract_path(url: str) -> str:
    """Extract path from URL."""
    try:
        return urlparse(url).path or "/"
    except Exception:
        return "/"


def score_interactive_elements(count: int) -> int:
    """Score based on interactive element count."""
    if count <= 2:
        return 0
    if count <= 5:
        return 3
    if count <= 10:
        return 5
    if count <= 20:
        return 8
    return 10


def score_api_calls(count: int) -> int:
    """Score based on API call count."""
    if count == 0:
        return 0
    if count == 1:
        return 3
    if count <= 3:
        return 5
    if count <= 5:
        return 8
    return 10


def score_form_fields(count: int) -> int:
    """Score based on form field count."""
    if count == 0:
        return 0
    if count <= 2:
        return 3
    if count <= 5:
        return 5
    if count <= 10:
        return 8
    return 10


def score_state_indicators(elements: list[dict]) -> int:
    """Score based on state management indicators."""
    score = 0
    type_counts: dict[str, int] = {}
    for el in elements:
        el_type = el.get("type", "")
        type_counts[el_type] = type_counts.get(el_type, 0) + 1

    if type_counts.get("modal-trigger", 0) > 0:
        score += 3
    if type_counts.get("tab-navigation", 0) > 0:
        score += 2
    if type_counts.get("action-toggle", 0) > 0:
        score += min(3, type_counts["action-toggle"])
    if type_counts.get("menu-navigation", 0) > 0:
        score += 2

    return min(10, score)


def score_auth(route_url: str, auth_flows: dict) -> int:
    """Score based on authentication requirements."""
    protected_urls = [
        r.get("url", "") for r in auth_flows.get("protected_routes", [])
    ]
    route_path = extract_path(route_url)

    for protected_url in protected_urls:
        if extract_path(protected_url) == route_path:
            return 10

    if auth_flows.get("auth_detected") and route_path not in ("/", "/login", "/register"):
        return 5

    return 0


def score_nav_depth(depth: int) -> int:
    """Score based on navigation depth."""
    if depth <= 0:
        return 0
    if depth == 1:
        return 3
    if depth == 2:
        return 5
    return 10


def get_risk_level(score: float) -> str:
    """Map numerical score to risk level."""
    if score >= RISK_LEVELS["critical"]:
        return "critical"
    if score >= RISK_LEVELS["high"]:
        return "high"
    if score >= RISK_LEVELS["medium"]:
        return "medium"
    return "low"


def detect_categories(route_data: dict) -> list[str]:
    """Detect regression categories for a route based on its characteristics."""
    categories = []
    elements = route_data.get("elements", [])
    element_types = {el.get("type", "") for el in elements}
    api_count = route_data.get("api_count", 0)
    form_count = route_data.get("form_count", 0)
    has_auth = route_data.get("auth_score", 0) > 0

    if "navigation" in element_types or "menu-navigation" in element_types:
        categories.append("navigation")
    if "action-trigger" in element_types or "action-toggle" in element_types:
        categories.append("interaction")
    if form_count > 0:
        categories.append("form-handling")
    if api_count > 0:
        categories.append("api-integration")
    if route_data.get("depth", 0) > 0:
        categories.append("routing")
    if has_auth:
        categories.append("authentication")
    if "modal-trigger" in element_types:
        categories.append("modal-dialog")
    if route_data.get("interactive_count", 0) > 10:
        categories.append("table-data")
    # Error boundary — detected if any API endpoints returned error status codes
    if route_data.get("has_error_apis", False):
        categories.append("error-boundary")
    # Responsive layout — always a consideration for routes with layout landmarks
    if route_data.get("has_layout_landmarks", False):
        categories.append("responsive-layout")

    return categories if categories else ["navigation"]


def score_routes(site_map: dict, interactions: dict, api_surface: dict, auth_flows: dict) -> list[dict]:
    """Score all routes for regression risk."""
    route_scores = []

    for route in site_map.get("routes", []):
        url = route.get("url", "")
        path = route.get("path", extract_path(url))

        # Get interactions for this route
        page_data = None
        for page in interactions.get("pages", []):
            if page.get("url") == url or extract_path(page.get("url", "")) == path:
                page_data = page
                break

        elements = page_data.get("elements", []) if page_data else []
        forms = page_data.get("forms", []) if page_data else []
        stats = page_data.get("stats", {}) if page_data else {}

        # Count API calls for this route
        api_count = 0
        has_error_apis = False
        for endpoint in api_surface.get("endpoints", []):
            for trigger in endpoint.get("triggered_by", []):
                if trigger.get("page_url") == url or extract_path(trigger.get("page_url", "")) == path:
                    api_count += 1
                    if any(s >= 400 for s in endpoint.get("status_codes", [])):
                        has_error_apis = True
                    break

        # Calculate scores
        interactive_count = stats.get("total_interactive", len(elements))
        form_field_count = sum(f.get("total_field_count", 0) for f in forms)
        depth = route.get("depth", 0)

        factors = {
            "interactive_elements": score_interactive_elements(interactive_count),
            "api_calls": score_api_calls(api_count),
            "form_fields": score_form_fields(form_field_count),
            "state_indicators": score_state_indicators(elements),
            "auth_required": score_auth(url, auth_flows),
            "nav_depth": score_nav_depth(depth),
        }

        # Weighted sum * 10 for 0-100 scale
        raw_score = sum(factors[k] * WEIGHTS[k] for k in WEIGHTS)
        final_score = round(raw_score * 10, 1)

        # Detect categories
        route_info = {
            "elements": elements,
            "api_count": api_count,
            "form_count": len(forms),
            "depth": depth,
            "auth_score": factors["auth_required"],
            "interactive_count": interactive_count,
            "has_error_apis": has_error_apis,
            "has_layout_landmarks": bool(route.get("landmarks")),
        }
        categories = detect_categories(route_info)

        route_scores.append({
            "url": path,
            "risk_score": final_score,
            "risk_level": get_risk_level(final_score),
            "factors": factors,
            "categories": categories,
            "interactions": {
                "total_interactive_elements": interactive_count,
                "form_count": len(forms),
                "api_call_count": api_count,
                "requires_auth": factors["auth_required"] > 0,
            },
        })

    # Sort by risk score descending
    route_scores.sort(key=lambda r: r["risk_score"], reverse=True)
    return route_scores


def score_flows(flow_graph: dict, route_scores: list[dict]) -> list[dict]:
    """Score flows based on their constituent route scores."""
    route_score_map = {r["url"]: r for r in route_scores}
    flow_scores = []

    for flow in flow_graph.get("flows", []):
        flow_routes = flow.get("routes", [])
        route_data = [route_score_map.get(r, {}) for r in flow_routes]
        route_data = [r for r in route_data if r]  # Filter out unmatched

        if not route_data:
            continue

        # Weighted average by interactive element count
        total_weight = 0
        weighted_sum = 0
        for rd in route_data:
            weight = max(1, rd.get("interactions", {}).get("total_interactive_elements", 1))
            weighted_sum += rd.get("risk_score", 0) * weight
            total_weight += weight

        avg_score = weighted_sum / total_weight if total_weight > 0 else 0

        # Multi-route bonus
        multi_route_bonus = min(30, (len(flow_routes) - 1) * 10)
        flow_score = min(100, round(avg_score + multi_route_bonus, 1))

        # Aggregate categories
        all_categories = set()
        for rd in route_data:
            all_categories.update(rd.get("categories", []))

        # Aggregate interactions
        total_elements = sum(rd.get("interactions", {}).get("total_interactive_elements", 0) for rd in route_data)
        total_forms = sum(rd.get("interactions", {}).get("form_count", 0) for rd in route_data)
        total_apis = sum(rd.get("interactions", {}).get("api_call_count", 0) for rd in route_data)
        any_auth = any(rd.get("interactions", {}).get("requires_auth", False) for rd in route_data)

        flow_scores.append({
            "id": flow.get("id", ""),
            "name": flow.get("name", ""),
            "description": f"User flow across {len(flow_routes)} routes: {', '.join(flow_routes)}",
            "routes": flow_routes,
            "api_endpoints": flow.get("api_endpoints", []),
            "categories": sorted(all_categories),
            "risk_score": flow_score,
            "risk_level": get_risk_level(flow_score),
            "target_files": [],  # Populated by Phase 4 (source correlation)
            "interactions": {
                "total_interactive_elements": total_elements,
                "form_count": total_forms,
                "api_call_count": total_apis,
                "requires_auth": any_auth,
            },
        })

    flow_scores.sort(key=lambda f: f["risk_score"], reverse=True)
    return flow_scores


def main():
    parser = argparse.ArgumentParser(description="Score regression risk for routes and flows")
    parser.add_argument("--site-map", required=True, help="Path to site-map.json")
    parser.add_argument("--interactions", required=True, help="Path to interaction-inventory.json")
    parser.add_argument("--api-surface", required=True, help="Path to api-surface.json")
    parser.add_argument("--auth-flows", required=True, help="Path to auth-flows.json")
    parser.add_argument("--flow-graph", required=True, help="Path to flow-graph.json")
    parser.add_argument("--output", "-o", default="regression-analysis.json", help="Output file path")

    args = parser.parse_args()

    # Load inputs
    site_map = load_json(args.site_map)
    interactions = load_json(args.interactions)
    api_surface = load_json(args.api_surface)
    auth_flows_data = load_json(args.auth_flows)
    flow_graph = load_json(args.flow_graph)

    # Score routes
    route_scores = score_routes(site_map, interactions, api_surface, auth_flows_data)

    # Score flows
    flow_scores = score_flows(flow_graph, route_scores)

    # Calculate stats
    level_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in flow_scores:
        level_counts[f["risk_level"]] += 1

    all_categories = set()
    for f in flow_scores:
        all_categories.update(f["categories"])

    # Build output
    analysis = {
        "base_url": site_map.get("base_url", ""),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "flows": flow_scores,
        "route_scores": route_scores,
        "stats": {
            "total_flows": len(flow_scores),
            "critical_flows": level_counts["critical"],
            "high_flows": level_counts["high"],
            "medium_flows": level_counts["medium"],
            "low_flows": level_counts["low"],
            "total_categories_covered": len(all_categories),
        },
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)

    print(f"Regression analysis written to {args.output}")
    print(f"  Total flows:  {analysis['stats']['total_flows']}")
    print(f"  Critical:     {analysis['stats']['critical_flows']}")
    print(f"  High:         {analysis['stats']['high_flows']}")
    print(f"  Medium:       {analysis['stats']['medium_flows']}")
    print(f"  Low:          {analysis['stats']['low_flows']}")
    print(f"  Categories:   {analysis['stats']['total_categories_covered']}")


if __name__ == "__main__":
    main()
