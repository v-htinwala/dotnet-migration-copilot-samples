#!/usr/bin/env python3
"""
parse-snapshot.py — Parse playwright-cli snapshot YAML into structured JSON.

Extracts element refs, types, labels, and hierarchy from the accessibility
tree YAML produced by `playwright-cli snapshot`.

Usage:
    python parse-snapshot.py <snapshot-file> [--output <output-file>]

Input:  YAML file from `playwright-cli snapshot` (piped to file)
Output: JSON with structured element data
"""

import argparse
import json
import sys
import re
from typing import Any


# ARIA roles that indicate interactive elements
INTERACTIVE_ROLES = {
    "link", "button", "textbox", "searchbox", "combobox", "listbox",
    "checkbox", "radio", "tab", "menuitem", "menuitemcheckbox",
    "menuitemradio", "option", "slider", "spinbutton", "switch",
    "treeitem",
}

# Classification mapping from ARIA role to interaction type
ROLE_CLASSIFICATION = {
    "link": "navigation",
    "button": "action-trigger",
    "textbox": "form-input",
    "searchbox": "form-input",
    "combobox": "form-select",
    "listbox": "form-select",
    "checkbox": "form-choice",
    "radio": "form-choice",
    "tab": "tab-navigation",
    "menuitem": "menu-navigation",
    "menuitemcheckbox": "menu-navigation",
    "menuitemradio": "menu-navigation",
    "option": "form-select",
    "slider": "form-input",
    "spinbutton": "form-input",
    "switch": "form-choice",
    "treeitem": "navigation",
}


def parse_yaml_snapshot(content: str) -> list[dict]:
    """
    Parse the YAML-like snapshot output from playwright-cli.

    This is a simplified parser that handles the indented YAML structure
    produced by playwright-cli's snapshot command. It does NOT require
    the pyyaml library.
    """
    lines = content.strip().split("\n")
    root_elements = []
    stack: list[tuple[int, dict]] = []  # (indent_level, node)

    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue

        # Determine indent level
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # Parse the line into a node
        if stripped.startswith("- role:"):
            node: dict[str, Any] = {
                "role": stripped.split(":", 1)[1].strip(),
                "children": [],
            }
        elif ":" in stripped:
            # This is an attribute of the current node
            key, value = stripped.split(":", 1)
            key = key.strip().lstrip("- ")
            value = value.strip().strip('"').strip("'")

            if stack:
                current_node = stack[-1][1]
                if key == "ref":
                    current_node["ref"] = int(value) if value.isdigit() else value
                elif key == "level":
                    current_node["level"] = int(value) if value.isdigit() else value
                elif key in ("checked", "disabled", "required"):
                    current_node[key] = value.lower() == "true"
                else:
                    current_node[key] = value
            continue
        else:
            continue

        # Place node in hierarchy based on indent
        while stack and stack[-1][0] >= indent:
            stack.pop()

        if stack:
            stack[-1][1]["children"].append(node)
        else:
            root_elements.append(node)

        stack.append((indent, node))

    return root_elements


def extract_interactive_elements(nodes: list[dict], page_url: str = "") -> list[dict]:
    """Recursively extract all interactive elements from the parsed tree."""
    elements = []

    def walk(node_list: list[dict]):
        for node in node_list:
            role = node.get("role", "")
            if role in INTERACTIVE_ROLES and "ref" in node:
                element = {
                    "ref": node["ref"],
                    "role": role,
                    "name": node.get("name", ""),
                    "type": ROLE_CLASSIFICATION.get(role, "other"),
                    "attributes": {},
                }
                # Collect relevant attributes
                for attr in ("placeholder", "required", "disabled", "checked", "value", "url"):
                    if attr in node:
                        element["attributes"][attr] = node[attr]
                if page_url:
                    element["page_url"] = page_url
                elements.append(element)

            # Recurse into children
            if "children" in node:
                walk(node["children"])

    walk(nodes)
    return elements


def extract_links(nodes: list[dict]) -> list[dict]:
    """Extract all link elements with their URLs."""
    links = []

    def walk(node_list: list[dict]):
        for node in node_list:
            if node.get("role") == "link" and "ref" in node:
                links.append({
                    "ref": node["ref"],
                    "name": node.get("name", ""),
                    "url": node.get("url", ""),
                })
            if "children" in node:
                walk(node["children"])

    walk(nodes)
    return links


def extract_landmarks(nodes: list[dict]) -> list[str]:
    """Extract ARIA landmark roles found on the page."""
    landmark_roles = {"banner", "navigation", "main", "complementary",
                      "contentinfo", "form", "region", "search"}
    landmarks = []

    def walk(node_list: list[dict]):
        for node in node_list:
            role = node.get("role", "")
            if role in landmark_roles:
                landmarks.append(role)
            if "children" in node:
                walk(node["children"])

    walk(nodes)
    return landmarks


def count_elements(nodes: list[dict]) -> int:
    """Count total elements in the tree."""
    count = 0

    def walk(node_list: list[dict]):
        nonlocal count
        for node in node_list:
            count += 1
            if "children" in node:
                walk(node["children"])

    walk(nodes)
    return count


def main():
    parser = argparse.ArgumentParser(
        description="Parse playwright-cli snapshot YAML into structured JSON"
    )
    parser.add_argument("snapshot_file", help="Path to snapshot YAML file")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--page-url", default="", help="URL of the page this snapshot is from")

    args = parser.parse_args()

    # Read snapshot content
    try:
        with open(args.snapshot_file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {args.snapshot_file}", file=sys.stderr)
        sys.exit(1)

    # Parse the snapshot
    tree = parse_yaml_snapshot(content)

    # Extract data
    result = {
        "page_url": args.page_url,
        "title": tree[0].get("name", "") if tree else "",
        "total_elements": count_elements(tree),
        "landmarks": extract_landmarks(tree),
        "interactive_elements": extract_interactive_elements(tree, args.page_url),
        "links": extract_links(tree),
        "interactive_element_count": len(extract_interactive_elements(tree, args.page_url)),
    }

    # Output
    output_json = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Parsed snapshot written to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
