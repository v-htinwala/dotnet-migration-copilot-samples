#!/usr/bin/env python3
"""
build-site-map.py — Aggregate parsed snapshots into a site-map.json.

Takes a directory of parsed snapshot JSON files (from parse-snapshot.py)
and builds a route graph representing the site's navigation structure.

Usage:
    python build-site-map.py <snapshots-dir> --base-url <url> [--output <output-file>]

Input:  Directory containing parsed snapshot JSON files (one per page)
Output: site-map.json with route graph, navigation links, and stats
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin


def normalize_url(url: str, base_url: str) -> str:
    """Normalize a URL relative to the base URL."""
    if not url:
        return ""
    if url.startswith("//"):
        url = "https:" + url
    if url.startswith("/"):
        parsed_base = urlparse(base_url)
        url = f"{parsed_base.scheme}://{parsed_base.netloc}{url}"
    elif not url.startswith("http"):
        url = urljoin(base_url, url)
    # Remove trailing slash for consistency
    return url.rstrip("/")


def is_same_domain(url: str, base_url: str) -> bool:
    """Check if a URL belongs to the same domain as the base URL."""
    try:
        return urlparse(url).netloc == urlparse(base_url).netloc
    except Exception:
        return False


def extract_path(url: str) -> str:
    """Extract the path component from a URL."""
    try:
        parsed = urlparse(url)
        return parsed.path or "/"
    except Exception:
        return "/"


def build_navigation_graph(snapshots: list[dict], base_url: str) -> dict:
    """Build adjacency list from parsed snapshot link data."""
    graph: dict[str, list[dict]] = {}

    for snapshot in snapshots:
        page_url = normalize_url(snapshot.get("page_url", ""), base_url)
        if not page_url:
            continue

        links = snapshot.get("links", [])
        graph[page_url] = []

        for link in links:
            target_url = normalize_url(link.get("url", ""), base_url)
            if target_url and is_same_domain(target_url, base_url):
                graph[page_url].append({
                    "target_url": target_url,
                    "link_text": link.get("name", ""),
                    "ref": link.get("ref", 0),
                })

    return graph


def calculate_depth(graph: dict[str, list], start_url: str) -> dict[str, int]:
    """Calculate BFS depth from the start URL for each route."""
    depths: dict[str, int] = {start_url: 0}
    queue = [start_url]
    visited = {start_url}

    while queue:
        current = queue.pop(0)
        current_depth = depths[current]

        for edge in graph.get(current, []):
            target = edge.get("target_url", "")
            if target and target not in visited:
                visited.add(target)
                depths[target] = current_depth + 1
                queue.append(target)

    return depths


def find_parent(graph: dict[str, list], target_url: str) -> str | None:
    """Find the first route that links to the target URL."""
    for source_url, links in graph.items():
        for link in links:
            if link.get("target_url") == target_url:
                return source_url
    return None


def build_site_map(snapshots_dir: str, base_url: str, exploration_depth: int = 2) -> dict:
    """Build the complete site map from parsed snapshot files."""
    # Load all parsed snapshots
    snapshots = []
    for filename in sorted(os.listdir(snapshots_dir)):
        if filename.endswith(".json"):
            filepath = os.path.join(snapshots_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    snapshot = json.load(f)
                    snapshots.append(snapshot)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: Skipping {filename}: {e}", file=sys.stderr)

    if not snapshots:
        print("Error: No valid snapshot files found", file=sys.stderr)
        return {"error": "No snapshots found"}

    # Build navigation graph
    graph = build_navigation_graph(snapshots, base_url)

    # Calculate depths
    normalized_base = normalize_url(base_url, base_url)
    depths = calculate_depth(graph, normalized_base)

    # Build route entries
    routes = []
    seen_urls = set()

    for snapshot in snapshots:
        page_url = normalize_url(snapshot.get("page_url", ""), base_url)
        if not page_url or page_url in seen_urls:
            continue
        seen_urls.add(page_url)

        route = {
            "url": page_url,
            "path": extract_path(page_url),
            "title": snapshot.get("title", ""),
            "element_count": snapshot.get("total_elements", 0),
            "interactive_element_count": snapshot.get("interactive_element_count", 0),
            "depth": depths.get(page_url, -1),
            "parent_url": find_parent(graph, page_url),
            "screenshot_path": f"screenshots/{extract_path(page_url).strip('/').replace('/', '_') or 'index'}.png",
            "landmarks": snapshot.get("landmarks", []),
            "is_protected": False,
            "redirect_target": None,
        }
        routes.append(route)

    # Sort routes by depth then path
    routes.sort(key=lambda r: (r["depth"], r["path"]))

    # Calculate stats
    total_links = sum(len(links) for links in graph.values())
    protected_count = sum(1 for r in routes if r["is_protected"])

    site_map = {
        "base_url": base_url,
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "exploration_depth": exploration_depth,
        "routes": routes,
        "navigation_graph": graph,
        "stats": {
            "total_routes": len(routes),
            "total_links": total_links,
            "protected_routes": protected_count,
            "failed_routes": 0,
        },
    }

    return site_map


def main():
    parser = argparse.ArgumentParser(
        description="Build site-map.json from parsed snapshot files"
    )
    parser.add_argument("snapshots_dir", help="Directory containing parsed snapshot JSON files")
    parser.add_argument("--base-url", required=True, help="Base URL of the web application")
    parser.add_argument("--depth", type=int, default=2, help="Exploration depth used")
    parser.add_argument("--output", "-o", default="site-map.json", help="Output file path")

    args = parser.parse_args()

    if not os.path.isdir(args.snapshots_dir):
        print(f"Error: Directory not found: {args.snapshots_dir}", file=sys.stderr)
        sys.exit(1)

    site_map = build_site_map(args.snapshots_dir, args.base_url, args.depth)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(site_map, f, indent=2)

    print(f"Site map written to {args.output}")
    print(f"  Routes discovered: {site_map['stats']['total_routes']}")
    print(f"  Navigation links:  {site_map['stats']['total_links']}")


if __name__ == "__main__":
    main()
