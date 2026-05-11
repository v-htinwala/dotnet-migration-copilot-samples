# Exploration Strategies — url-functional-explorer

Detailed algorithms for page crawling, SPA handling, and DOM-state discovery
using playwright-cli commands.

---

## Crawl Algorithm

### Breadth-First Page Discovery

```
QUEUE = [app_url]
VISITED = {}
PAGES = []

# Open the browser session
playwright-cli -s=<session-name> open --headed <app_url>

while QUEUE is not empty AND len(PAGES) < max_pages:
    url = QUEUE.dequeue()
    if url in VISITED: continue
    VISITED[url] = true

    # Navigate to the page
    playwright-cli -s=<session-name> goto <url>

    # Capture accessibility snapshot and screenshot
    playwright-cli -s=<session-name> snapshot --filename=<output_dir>/snapshots/<page-slug>.yaml
    playwright-cli -s=<session-name> screenshot --filename=<output_dir>/screenshots/<page-slug>.png

    page = parse_snapshot_for_metadata(<page-slug>.yaml)
    PAGES.append(page)

    # Extract same-domain links from snapshot (link role nodes with url attribute)
    links = extract_links_from_snapshot(<page-slug>.yaml)
    for link in links:
        if link not in VISITED:
            QUEUE.enqueue(link)

# Clean up session
playwright-cli -s=<session-name> close
```

### Link Prioritization

When the queue has more URLs than remaining budget (`max_pages`), prioritize:

1. **Navigation menu links** (sidebar, header) — highest priority
2. **CRUD action links** (/new, /create, /edit) — high priority
3. **Detail page links** (/:id patterns) — sample 2-3 max
4. **Settings/config pages** — medium priority
5. **Static/info pages** (about, help, terms) — lowest priority

### Same-Domain Filter

```
base_domain = extract_domain(app_url)

function is_same_domain(url):
    return extract_domain(url) == base_domain
        AND not is_logout_url(url)         # Skip /logout, /signout
        AND not is_external_auth(url)      # Skip OAuth redirects
        AND not is_static_asset(url)       # Skip .css, .js, .png
        AND not is_api_endpoint(url)       # Skip /api/* (unless collecting)
```

---

## SPA Handling Strategy

### DOM-State-Based Discovery

For Single Page Applications where navigation happens without URL changes:

#### Step 1: Baseline Capture

After initial page load, capture the accessibility snapshot:
```bash
playwright-cli -s=<session-name> snapshot --filename=<output_dir>/snapshots/baseline.yaml
playwright-cli -s=<session-name> eval "window.location.href"
```

Parse the snapshot using `parse-snapshot.py` to get structured data:
```bash
python scripts/parse-snapshot.py <output_dir>/snapshots/baseline.yaml --page-url <current-url> --output <output_dir>/parsed/baseline.json
```

```
baseline = {
    url: current_url,
    dom_hash: hash(parsed_snapshot),
    node_count: parsed_snapshot.total_elements,
    key_elements: parsed_snapshot.interactive_elements  # headings, forms, tables
}
```

#### Step 2: Interaction-Triggered State Detection

After each interactive action, use playwright-cli to interact and re-snapshot:
```bash
# Perform interaction (e.g., click a tab)
playwright-cli -s=<session-name> click <ref>
# Capture new state
playwright-cli -s=<session-name> snapshot --filename=<output_dir>/snapshots/state-<n>.yaml
# Check if URL changed
playwright-cli -s=<session-name> eval "window.location.href"
```

Parse and compare:
```
new_state = parse_snapshot(state-<n>.yaml)
difference = compare_states(baseline, new_state)

if difference.structural_change > 0.50:
    # MAJOR CHANGE — treat as new page
    playwright-cli -s=<session-name> screenshot --filename=<output_dir>/screenshots/state-<n>.png
    record_as_new_page(new_state)
    baseline = new_state  # Reset baseline

elif difference.structural_change > 0.30:
    # MEDIUM CHANGE — treat as new state (tab content, modal)
    playwright-cli -s=<session-name> screenshot --filename=<output_dir>/screenshots/state-<n>.png
    record_as_sub_state(new_state, parent=baseline)

else:
    # MINOR CHANGE — not significant (filter, sort, toggle)
    # Log but don't record as new state
```

#### Step 3: State Comparison Algorithm

```
function compare_states(state_a, state_b):
    # Compare by accessibility tree structure (from parse-snapshot.py output)
    nodes_a = set(state_a.accessibility_nodes)
    nodes_b = set(state_b.accessibility_nodes)

    common = nodes_a.intersection(nodes_b)
    total = nodes_a.union(nodes_b)

    structural_change = 1.0 - (len(common) / len(total))

    # Additional signals:
    heading_changed = (state_a.main_heading != state_b.main_heading)
    form_appeared = (state_b.has_form AND NOT state_a.has_form)
    table_changed = (state_a.table_columns != state_b.table_columns)

    return {
        structural_change: structural_change,
        heading_changed: heading_changed,
        form_appeared: form_appeared,
        table_changed: table_changed
    }
```

### Component Correlation (with Codebase Data)

When `component-tree.json` from codebase-functional-analyzer is available:

1. **Match DOM headings to component names**:
   - Page heading "Vehicle Management" → `VehicleList` component
   - Form title "Create Vehicle" → `VehicleForm` component

2. **Cross-reference form fields**:
   - DOM field `input[name="plate_number"]` → `VehicleForm.form_fields` includes `plate_number`
   - This confirms the component mapping and boosts confidence

3. **Identify missing states**:
   - Components in tree but not yet found in DOM → suggest navigation paths to find them
   - DOM states with no matching component → flag as dynamic/generated content

---

## Page Type Classification

Classify each discovered page/state by its primary content:

| Page Type | Detection Heuristics |
|---|---|
| `dashboard` | Charts, metric cards, summary widgets, multiple data sections |
| `list` | `<table>` or repeated card elements, pagination, filter controls |
| `form` | `<form>` element with >2 input fields, submit button |
| `detail` | Single record display, edit/delete buttons, related data sections |
| `modal` | Overlay element with `role="dialog"` or modal-like styling |
| `login` | Password field, sign-in button, auth-related heading |
| `settings` | Toggle switches, configuration forms, preference sections |
| `search` | Prominent search input, filter sidebar, result listing |
| `error` | Error codes (404, 500), error messages, empty states |
| `wizard` | Step indicators, next/prev buttons, progress bar |

### Page Type Signals

```
function classify_page(snapshot):
    if has_element('input[type="password"]') AND has_text('sign in|log in|login'):
        return 'login'
    if count_elements('table') > 0 OR count_elements('.card-grid') > 0:
        if has_element('.pagination') OR has_element('[role="navigation"]'):
            return 'list'
    if count_elements('form input') > 2:
        return 'form'
    if has_element('.chart') OR count_elements('.metric-card') > 2:
        return 'dashboard'
    if has_element('.step-indicator') OR has_element('.wizard'):
        return 'wizard'
    ...
    return 'other'
```

---

## Navigation Menu Extraction

### Common Menu Patterns

| Pattern | Selector Strategy |
|---|---|
| Sidebar nav | `nav.sidebar`, `aside nav`, `[role="navigation"]` in sidebar |
| Header nav | `header nav`, `nav.navbar`, `.top-nav` |
| Breadcrumbs | `nav[aria-label="breadcrumb"]`, `.breadcrumb` |
| Tab bar | `[role="tablist"]`, `.tabs`, `.tab-bar` |
| Footer nav | `footer nav`, `.footer-links` |

### Menu Item Extraction

For each navigation element:
```json
{
  "location": "sidebar",
  "items": [
    {"label": "Dashboard", "href": "/dashboard", "icon": "home", "active": true},
    {"label": "Vehicles", "href": "/vehicles", "icon": "truck", "active": false,
     "children": [
       {"label": "All Vehicles", "href": "/vehicles"},
       {"label": "Add Vehicle", "href": "/vehicles/new"}
     ]
    }
  ]
}
```
