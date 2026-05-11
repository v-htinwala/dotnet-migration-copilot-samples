#!/usr/bin/env python3
"""
identify-flows.py — Group discovery data into logical user flows.

Analyzes site-map.json, interaction-inventory.json, and api-surface.json
to identify user flows using link/API dependency graph analysis.

Usage:
    python identify-flows.py \
        --site-map <site-map.json> \
        --interactions <interaction-inventory.json> \
        --api-surface <api-surface.json> \
        --auth-flows <auth-flows.json> \
        [--output <flow-graph.json>]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse


# Flow type heuristics
CREATION_SIGNALS = {"form-input", "form-select", "form-choice", "action-submit"}
BROWSING_SIGNALS = {"tab-navigation", "navigation"}
MODAL_SIGNALS = {"modal-trigger"}


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


def get_route_interactions(interactions: dict, route_url: str) -> dict:
    """Get interaction data for a specific route."""
    for page in interactions.get("pages", []):
        if page.get("url") == route_url or extract_path(page.get("url", "")) == extract_path(route_url):
            return page
    return {"elements": [], "forms": [], "stats": {}}


def get_route_apis(api_surface: dict, route_url: str) -> list[dict]:
    """Get API endpoints triggered by a specific route."""
    route_apis = []
    for endpoint in api_surface.get("endpoints", []):
        for trigger in endpoint.get("triggered_by", []):
            if trigger.get("page_url") == route_url or extract_path(trigger.get("page_url", "")) == extract_path(route_url):
                route_apis.append(endpoint)
                break
    return route_apis


def extract_resource_from_api(url_pattern: str) -> str:
    """Extract the primary resource name from an API URL pattern."""
    parts = url_pattern.strip("/").split("/")
    # Skip 'api', 'v1', etc. and find the first "real" resource name
    skip_words = {"api", "v1", "v2", "v3", "auth"}
    for part in parts:
        if part not in skip_words and not part.startswith(":"):
            return part
    return ""


def identify_flow_type(routes_data: list[dict]) -> str:
    """Determine the flow type based on aggregate route data."""
    has_forms = any(r.get("form_count", 0) > 0 for r in routes_data)
    has_mutation_api = any(
        ep.get("classification") == "mutation"
        for r in routes_data
        for ep in r.get("apis", [])
    )
    has_auth_api = any(
        ep.get("classification") == "auth"
        for r in routes_data
        for ep in r.get("apis", [])
    )
    has_table = any(
        r.get("interaction_stats", {}).get("total_interactive", 0) > 10
        for r in routes_data
    )

    if has_auth_api:
        return "authentication"
    if has_forms and has_mutation_api:
        return "creation"
    if has_table:
        return "data-browsing"
    if has_mutation_api:
        return "management"
    return "navigation"


def group_routes_by_resource(routes: list[dict], api_surface: dict, site_map: dict) -> list[dict]:
    """Group routes into flows based on shared API resources and URL patterns."""
    flows = []
    used_routes = set()

    # Get all routes with their interaction and API data
    routes_with_data = []
    for route in site_map.get("routes", []):
        url = route.get("url", "")
        path = route.get("path", extract_path(url))
        apis = get_route_apis(api_surface, url)
        resources = set()
        for api in apis:
            res = extract_resource_from_api(api.get("url_pattern", ""))
            if res:
                resources.add(res)

        routes_with_data.append({
            "url": url,
            "path": path,
            "title": route.get("title", ""),
            "apis": apis,
            "resources": resources,
            "form_count": 0,
            "interaction_stats": {},
        })

    # Group by shared API resource
    resource_groups: dict[str, list] = {}
    for rd in routes_with_data:
        for res in rd["resources"]:
            resource_groups.setdefault(res, []).append(rd)

    flow_id = 0
    for resource, grouped_routes in resource_groups.items():
        if len(grouped_routes) < 1:
            continue

        route_urls = [r["url"] for r in grouped_routes]
        # Skip if all routes already assigned
        new_urls = [u for u in route_urls if u not in used_routes]
        if not new_urls:
            continue

        flow_id += 1
        flow_type = identify_flow_type(grouped_routes)

        # Build chain
        chain = []
        for rd in grouped_routes:
            api_patterns = [ep.get("url_pattern", "") for ep in rd["apis"]]
            chain_entry = {
                "url": rd["path"],
                "action": f"{'view' if not rd['apis'] or all(e.get('method') == 'GET' for e in rd['apis']) else 'modify'} {resource}",
                "next": [],
            }
            if api_patterns:
                chain_entry["api"] = ", ".join(f"{ep.get('method', 'GET')} {ep.get('url_pattern', '')}" for ep in rd["apis"])
            chain.append(chain_entry)

        # Connect chain entries via navigation graph
        nav_graph = site_map.get("navigation_graph", {})
        for i, entry in enumerate(chain):
            full_url = grouped_routes[i]["url"]
            if full_url in nav_graph:
                for link in nav_graph[full_url]:
                    target = link.get("target_url", "")
                    if target in route_urls:
                        entry["next"].append(extract_path(target))

        # Collect all API endpoints for this flow
        all_api_patterns = []
        for rd in grouped_routes:
            for ep in rd["apis"]:
                pattern = f"{ep.get('method', 'GET')} {ep.get('url_pattern', '')}"
                if pattern not in all_api_patterns:
                    all_api_patterns.append(pattern)

        flow = {
            "id": f"flow-{flow_id}",
            "name": f"{resource.capitalize()} {flow_type.replace('-', ' ').title()} Flow",
            "chain": chain,
            "entry_point": chain[0]["url"] if chain else "",
            "exit_points": [chain[0]["url"]] if chain else [],
            "routes": [extract_path(r["url"]) for r in grouped_routes],
            "api_endpoints": all_api_patterns,
        }
        flows.append(flow)

        for u in route_urls:
            used_routes.add(u)

    # Collect orphan routes
    all_urls = {r.get("url", "") for r in site_map.get("routes", [])}
    orphan_routes = [extract_path(u) for u in all_urls - used_routes]

    return flows, orphan_routes


def main():
    parser = argparse.ArgumentParser(description="Identify user flows from discovery data")
    parser.add_argument("--site-map", required=True, help="Path to site-map.json")
    parser.add_argument("--interactions", required=True, help="Path to interaction-inventory.json")
    parser.add_argument("--api-surface", required=True, help="Path to api-surface.json")
    parser.add_argument("--auth-flows", required=True, help="Path to auth-flows.json")
    parser.add_argument("--output", "-o", default="flow-graph.json", help="Output file path")

    args = parser.parse_args()

    # Load inputs
    site_map = load_json(args.site_map)
    interactions = load_json(args.interactions)
    api_surface = load_json(args.api_surface)
    auth_flows_data = load_json(args.auth_flows)

    # Identify flows
    flows, orphan_routes = group_routes_by_resource(
        site_map.get("routes", []),
        api_surface,
        site_map,
    )

    # Add auth flow if detected
    if auth_flows_data.get("auth_detected"):
        login_url = auth_flows_data.get("login_page", {}).get("url", "")
        protected = [r.get("url", "") for r in auth_flows_data.get("protected_routes", [])]
        auth_endpoints = auth_flows_data.get("auth_api_endpoints", [])

        if login_url or protected:
            auth_flow = {
                "id": f"flow-{len(flows) + 1}",
                "name": "Authentication Flow",
                "chain": [],
                "entry_point": extract_path(login_url) if login_url else "/login",
                "exit_points": [extract_path(p) for p in protected[:1]] or ["/"],
                "routes": [extract_path(login_url)] + [extract_path(p) for p in protected],
                "api_endpoints": auth_endpoints,
            }
            if login_url:
                auth_flow["chain"].append({
                    "url": extract_path(login_url),
                    "action": "login",
                    "next": [extract_path(p) for p in protected[:1]] or ["/"],
                })
            flows.append(auth_flow)

    # Build output
    flow_graph = {
        "base_url": site_map.get("base_url", ""),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "flows": flows,
        "orphan_routes": orphan_routes,
        "stats": {
            "total_flows": len(flows),
            "max_chain_length": max((len(f["chain"]) for f in flows), default=0),
            "orphan_count": len(orphan_routes),
        },
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(flow_graph, f, indent=2)

    print(f"Flow graph written to {args.output}")
    print(f"  Flows identified: {flow_graph['stats']['total_flows']}")
    print(f"  Orphan routes:    {flow_graph['stats']['orphan_count']}")


if __name__ == "__main__":
    main()
