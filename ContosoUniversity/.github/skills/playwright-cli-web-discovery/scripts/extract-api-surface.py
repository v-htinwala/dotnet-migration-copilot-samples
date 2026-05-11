#!/usr/bin/env python3
"""
extract-api-surface.py — Parse playwright-cli network output to api-surface.json.

Processes network capture data from `playwright-cli network` command output
and produces a structured api-surface.json with deduplicated, classified
API endpoints.

Usage:
    python extract-api-surface.py <network-logs-dir> --base-url <url> [--output <output-file>]

Input:  Directory containing network log text files (one per page/action)
Output: api-surface.json with classified API endpoints
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse


# Patterns to skip (static assets, not API calls)
STATIC_PATTERNS = [
    r"\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot|map)(\?|$)",
    r"webpack",
    r"hot-update",
    r"__vite",
    r"sockjs-node",
    r"_next/static",
]

# Auth-related URL patterns
AUTH_PATTERNS = [
    r"/auth",
    r"/login",
    r"/logout",
    r"/signin",
    r"/signout",
    r"/session",
    r"/token",
    r"/oauth",
    r"/sso",
    r"/callback",
]


def is_static_asset(url: str) -> bool:
    """Check if a URL is a static asset request."""
    path = urlparse(url).path.lower()
    return any(re.search(pattern, path) for pattern in STATIC_PATTERNS)


def is_auth_endpoint(url: str) -> bool:
    """Check if a URL is related to authentication."""
    path = urlparse(url).path.lower()
    return any(re.search(pattern, path) for pattern in AUTH_PATTERNS)


def abstract_path_params(url: str) -> str:
    """
    Abstract path parameters from a URL.
    
    Examples:
        /api/users/123       -> /api/users/:id
        /api/orders/abc-def  -> /api/orders/:id
        /api/items/42/reviews -> /api/items/:id/reviews
    """
    parsed = urlparse(url)
    path = parsed.path

    # Replace numeric path segments
    path = re.sub(r"/\d+", "/:id", path)

    # Replace UUID-like segments
    path = re.sub(
        r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "/:id",
        path,
        flags=re.IGNORECASE,
    )

    # Replace MongoDB ObjectId-like segments (24 hex chars)
    path = re.sub(r"/[0-9a-f]{24}", "/:id", path, flags=re.IGNORECASE)

    # Replace slug-like segments that look like IDs (short alphanumeric)
    # Only if they're not common path words
    common_words = {"api", "v1", "v2", "v3", "admin", "public", "auth", "users",
                    "items", "orders", "products", "categories", "search", "list",
                    "create", "update", "delete", "new", "edit"}

    segments = path.split("/")
    abstracted_segments = []
    for seg in segments:
        if seg and seg not in common_words and re.match(r"^[a-f0-9]{6,}$", seg, re.IGNORECASE):
            abstracted_segments.append(":id")
        else:
            abstracted_segments.append(seg)
    path = "/".join(abstracted_segments)

    return path


def classify_endpoint(method: str, url: str) -> str:
    """Classify an endpoint by its method and URL."""
    if is_auth_endpoint(url):
        return "auth"
    if is_static_asset(url):
        return "static"
    if method.upper() == "GET":
        return "data-fetch"
    if method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
        return "mutation"
    return "other"


def parse_network_log(content: str, page_url: str = "") -> list[dict]:
    """
    Parse network log output from playwright-cli.
    
    Expected format per line:
        METHOD  URL  STATUS  CONTENT_TYPE
    
    Example:
        GET  https://example.com/api/products  200  application/json
        POST https://example.com/api/cart       201  application/json
    """
    entries = []
    lines = content.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Parse space-separated fields
        parts = line.split()
        if len(parts) < 3:
            continue

        method = parts[0].upper()
        url = parts[1]
        status = int(parts[2]) if parts[2].isdigit() else 0
        content_type = parts[3] if len(parts) > 3 else ""

        # Skip static assets
        if is_static_asset(url):
            continue

        entries.append({
            "method": method,
            "url": url,
            "status": status,
            "content_type": content_type,
            "page_url": page_url,
        })

    return entries


def deduplicate_endpoints(entries: list[dict], base_url: str) -> list[dict]:
    """
    Deduplicate and aggregate network entries into endpoint definitions.
    
    Groups by method + abstracted URL pattern, merges observations.
    """
    endpoint_map: dict[str, dict] = {}

    for entry in entries:
        url_pattern = abstract_path_params(entry["url"])
        key = f"{entry['method']}:{url_pattern}"

        if key not in endpoint_map:
            endpoint_map[key] = {
                "method": entry["method"],
                "url_pattern": url_pattern,
                "url_examples": [],
                "status_codes": [],
                "content_type": entry.get("content_type", ""),
                "classification": classify_endpoint(entry["method"], entry["url"]),
                "triggered_by": [],
                "request_body_shape": None,
                "response_body_shape": None,
                "observation_count": 0,
            }

        ep = endpoint_map[key]

        # Add unique URL examples (max 3)
        if entry["url"] not in ep["url_examples"] and len(ep["url_examples"]) < 3:
            ep["url_examples"].append(entry["url"])

        # Add unique status codes
        if entry["status"] and entry["status"] not in ep["status_codes"]:
            ep["status_codes"].append(entry["status"])

        # Add trigger info
        if entry.get("page_url"):
            trigger = {"page_url": entry["page_url"], "action": "page-load"}
            if trigger not in ep["triggered_by"]:
                ep["triggered_by"].append(trigger)

        ep["observation_count"] += 1

    # Convert to list and sort by method + pattern
    endpoints = sorted(endpoint_map.values(), key=lambda e: f"{e['method']}:{e['url_pattern']}")
    return endpoints


def build_api_surface(network_logs_dir: str, base_url: str) -> dict:
    """Build the complete API surface from network log files."""
    all_entries = []

    for filename in sorted(os.listdir(network_logs_dir)):
        if filename.endswith(".txt") or filename.endswith(".log"):
            filepath = os.path.join(network_logs_dir, filename)
            # Derive page URL from filename (convention: page_path.txt)
            page_path = filename.rsplit(".", 1)[0].replace("_", "/")

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                entries = parse_network_log(content, page_url=f"{base_url}/{page_path}")
                all_entries.extend(entries)
            except OSError as e:
                print(f"Warning: Skipping {filename}: {e}", file=sys.stderr)

    # Deduplicate
    endpoints = deduplicate_endpoints(all_entries, base_url)

    # Calculate stats
    stats = {
        "total_endpoints": len(endpoints),
        "data_fetch_count": sum(1 for e in endpoints if e["classification"] == "data-fetch"),
        "mutation_count": sum(1 for e in endpoints if e["classification"] == "mutation"),
        "auth_count": sum(1 for e in endpoints if e["classification"] == "auth"),
    }

    api_surface = {
        "base_url": base_url,
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "endpoints": endpoints,
        "stats": stats,
    }

    return api_surface


def main():
    parser = argparse.ArgumentParser(
        description="Build api-surface.json from network log files"
    )
    parser.add_argument("network_logs_dir", help="Directory containing network log files")
    parser.add_argument("--base-url", required=True, help="Base URL of the web application")
    parser.add_argument("--output", "-o", default="api-surface.json", help="Output file path")

    args = parser.parse_args()

    if not os.path.isdir(args.network_logs_dir):
        print(f"Error: Directory not found: {args.network_logs_dir}", file=sys.stderr)
        sys.exit(1)

    api_surface = build_api_surface(args.network_logs_dir, args.base_url)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(api_surface, f, indent=2)

    print(f"API surface written to {args.output}")
    print(f"  Total endpoints:  {api_surface['stats']['total_endpoints']}")
    print(f"  Data fetch:       {api_surface['stats']['data_fetch_count']}")
    print(f"  Mutations:        {api_surface['stats']['mutation_count']}")
    print(f"  Auth endpoints:   {api_surface['stats']['auth_count']}")


if __name__ == "__main__":
    main()
