---
name: url-functional-explorer
description: >
  Explores a live web application using playwright-cli to discover features,
  forms, interactions, navigation structure, and dynamic content. SPA-aware with
  DOM-state-based discovery for single-page applications where URL routes may
  not change. Supports three exploration modes: read-only (observe only),
  user-guided (ask before writes), and shadow (aggressive exploration with form
  submissions). Handles authentication checkpoints, smart sampling for paginated
  and dynamic content, and produces structured scenario candidates for functional
  test generation. Use when generating functional test cases from a running web
  application, mapping site navigation, or discovering form fields and validation
  behaviors in a live environment.
license: MIT
compatibility: >
  Requires playwright-cli installed globally or via npx
  (@playwright/cli@latest). Node.js 18+ required. Works with any web
  application accessible via HTTP/HTTPS. Headed mode required for
  authentication checkpoint (user logs in manually).
metadata:
  author: functional-test-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
allowed-tools: Bash(playwright-cli:*) Bash(npx:*) Bash(node:*) Bash(python:*)
---

# URL Functional Explorer

## Purpose

Explore a live web application using Microsoft's playwright-cli for live browser
exploration to discover all features, forms, navigation paths, interactive
elements, and dynamic content — then produce structured scenario candidates for
functional test case generation. This skill bridges a running application with
comprehensive test coverage by observing what the application actually does,
rather than what the code says it should do.

## Prerequisites

Before starting, verify `playwright-cli` is available:

```bash
playwright-cli --help
```

If not installed, install via:

```bash
npm install -g @playwright/cli@latest
```

## When to Use This Skill

- Discover all pages and routes in a running web application
- Map form fields, validation behaviors, and interactive elements
- Generate screenshots and DOM snapshots as test evidence
- Detect SPA navigation (DOM-state changes without URL changes)
- Feed URL-sourced scenario candidates to the merger
- Complement codebase analysis with live behavior verification

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `app_url` | Yes | — | Live application URL (base URL) |
| `exploration_mode` | Yes | — | `read-only` / `user-guided` / `shadow` |
| `output_dir` | Yes | — | Output directory for all artifacts |
| `session_name` | No | `func-explorer` | Named session for playwright-cli (`-s=<name>`) |
| `existing_discovery` | No | — | Path to existing discovery artifacts (skip re-crawling known pages) |
| `max_pages` | No | `50` | Maximum number of pages/states to explore |
| `timeout_per_page` | No | `30000` | Timeout in ms per page exploration |

## Outputs

| File | Format | Description |
|---|---|---|
| `site-map.json` | JSON | Discovered routes and navigation structure |
| `interaction-inventory.json` | JSON | Forms, buttons, links, inputs per page |
| `screenshots/` | PNG | Visual evidence per page/state |
| `snapshots/` | YAML | Accessibility tree snapshots per page/state |
| `scenario-candidates.jsonl` | JSONL | Functional test scenario candidates tagged `source: "url"` |

---

## 6-Phase Workflow

### Phase 1: Authentication Detection & Checkpoint

**Goal**: Detect if the application requires login and handle authentication.

1. **Open the target URL** in a named playwright-cli session (headed mode):
   ```bash
   playwright-cli -s=<session-name> open --headed <app_url>
   ```

2. **Take initial snapshot** of the landing page:
   ```bash
   playwright-cli -s=<session-name> snapshot
   ```

3. **Capture a visual baseline screenshot**:
   ```bash
   playwright-cli -s=<session-name> screenshot --filename=<output_dir>/screenshots/landing.png
   ```

4. **Detect login requirement** — parse the snapshot YAML to check for:
   - Password input: `textbox` role nodes with password-like names
   - Text content matching: "Sign In", "Log In", "Login", "Sign Up"
   - URL containing: `/login`, `/signin`, `/auth` (check via):
     ```bash
     playwright-cli -s=<session-name> eval "window.location.href"
     ```
   - Cookie consent / SSO redirect pages

5. **If login detected → AUTH CHECKPOINT**:
   - Display to user: "Authentication required. Please log in to the
     application in the browser window, then confirm here."
   - Wait for user confirmation
   - After confirmation, verify authentication:
     - Check current URL is no longer `/login`:
       ```bash
       playwright-cli -s=<session-name> eval "window.location.href"
       ```
     - Take a new snapshot to verify authenticated content is visible:
       ```bash
       playwright-cli -s=<session-name> snapshot
       ```
     - If still on login page, prompt again
   - Session cookies and storage are automatically retained within the named session

6. **If no login detected**: Proceed to Phase 2.

### Phase 2: Page Crawl & Navigation Map

**Goal**: Discover all accessible pages and build a navigation map.

1. **Start from the authenticated landing page** (or `app_url` if no auth).

2. **Crawl strategy** — take an accessibility snapshot and parse it:
   ```bash
   playwright-cli -s=<session-name> snapshot
   ```
   From the snapshot YAML:
   - Extract all `link` role nodes (these are `<a>` links)
   - Filter to same-domain links only (respect `app_url` base domain)
   - Identify `navigation` role nodes (sidebar menus, header menus, breadcrumbs)
   - Track all unique URLs discovered from `url` attributes on link nodes

3. **For each discovered page**:
   - Navigate to the URL:
     ```bash
     playwright-cli -s=<session-name> goto <url>
     ```
   - Wait for page load, then capture snapshot and screenshot:
     ```bash
     playwright-cli -s=<session-name> snapshot --filename=<output_dir>/snapshots/{page-slug}.yaml
     playwright-cli -s=<session-name> screenshot --filename=<output_dir>/screenshots/{page-slug}.png
     ```
   - Parse the snapshot to record page metadata:
     ```json
     {
       "url": "/vehicles",
       "title": "Vehicle Management",
       "page_type": "list",
       "nav_source": "sidebar",
       "load_time_ms": 450,
       "has_forms": false,
       "has_tables": true,
       "has_modals": false
     }
     ```
   - Extract links from the snapshot to discover more pages

4. **Build site-map.json** using the `build-site-map.py` helper script:
   ```bash
   python scripts/build-site-map.py <output_dir>/snapshots --base-url <app_url> --output <output_dir>/site-map.json
   ```
   Or manually aggregate into:
   ```json
   {
     "base_url": "https://app.example.com",
     "total_pages": 15,
     "pages": [...],
     "navigation": {
       "sidebar": ["Dashboard", "Vehicles", "Bookings", "Users", "Settings"],
       "header": ["Profile", "Notifications", "Logout"]
     }
   }
   ```

5. **Depth limit**: Crawl max 3 levels deep from the landing page. Stay within
   `max_pages` limit.

### Phase 3: Interaction Inventory

**Goal**: For each discovered page, catalog all interactive elements.

1. **For each route in the site map**, navigate and capture a fresh snapshot:
   ```bash
   playwright-cli -s=<session-name> goto <url>
   playwright-cli -s=<session-name> snapshot
   ```

2. **Parse the snapshot YAML** to extract interactive elements. Classify each by role:

   | Snapshot Role | Classification |
   |---|---|
   | `link` | navigation |
   | `button` | action (further classify: submit, toggle, trigger) |
   | `textbox`, `searchbox` | form-input |
   | `combobox`, `listbox` | form-select |
   | `checkbox`, `radio` | form-choice |
   | `tab`, `tabpanel` | tab-navigation |
   | `dialog` | modal-trigger (if hidden) |
   | `menu`, `menubar`, `menuitem` | menu-navigation |

3. **For each interactive element**, record from the snapshot:
   - `ref`: playwright-cli element reference (integer used for `click`, `fill`, etc.)
   - `role`: ARIA role from snapshot
   - `name`: accessible name from snapshot
   - `type`: classification from table above
   - `attributes`: relevant attributes (placeholder, required, disabled, checked)
   - `page_url`: the route where this element was found

4. **Explore dropdowns** to discover all options:
   - For custom dropdowns, click to open and re-snapshot:
     ```bash
     playwright-cli -s=<session-name> click <ref>
     playwright-cli -s=<session-name> snapshot
     ```
   - Record all visible option values, then close:
     ```bash
     playwright-cli -s=<session-name> press Escape
     ```

5. **Identify form groups** from the snapshot hierarchy:
   - Group elements within `form` role containers
   - Identify submit buttons associated with each form
   - Count required vs optional fields

6. **Build per-page inventory** in this format:

```json
{
  "page_url": "/vehicles/new",
  "page_type": "form",
  "forms": [
    {
      "form_id": "create-vehicle-form",
      "action": "/api/vehicles",
      "method": "POST",
      "fields": [
        {
          "ref": 12,
          "name": "name",
          "type": "text",
          "label": "Vehicle Name",
          "placeholder": "Enter vehicle name",
          "required": true,
          "maxlength": 100
        },
        {
          "ref": 14,
          "name": "type",
          "type": "select",
          "label": "Vehicle Type",
          "options": ["Heavy Duty", "Light", "Medium"],
          "required": true
        },
        {
          "ref": 16,
          "name": "plate_number",
          "type": "text",
          "label": "Plate Number",
          "placeholder": "e.g. AB1234",
          "required": true,
          "pattern": "[A-Z]{2}[0-9]{4}"
        }
      ],
      "submit_button": {"ref": 18, "text": "Create Vehicle", "type": "submit"}
    }
  ],
  "buttons": [
    {"ref": 19, "text": "Cancel", "type": "button", "action": "navigation"},
    {"ref": 20, "text": "Delete", "type": "button", "action": "destructive"}
  ],
  "links": [
    {"ref": 5, "text": "Back to list", "href": "/vehicles"}
  ],
  "tables": [],
  "tabs": [],
  "modals": [],
  "tooltips": [],
  "notifications": []
}
```

7. **Output**: Write `interaction-inventory.json` to the output directory.

**Element extraction rules**:
- **Forms**: Parse snapshot for `form` role containers. For each, extract
  child `textbox`, `combobox`, `checkbox` nodes with their `ref`, `name`,
  `required`, `disabled`, and `placeholder` attributes.
- **Buttons**: All `button` role nodes with visible `name` text.
  Classify as: navigation, action, destructive, submit.
- **Tables**: `table`/`grid` role nodes — extract column headers, row count.
- **Tabs**: `tab` role nodes and their associated `tabpanel` content areas.
- **Modals**: `dialog` role nodes — click trigger elements to reveal:
  ```bash
  playwright-cli -s=<session-name> click <trigger-ref>
  playwright-cli -s=<session-name> snapshot
  ```
- **Dropdowns**: `combobox`/`listbox` nodes — click to reveal options, re-snapshot.

### Phase 4: Smart Sampling for Dynamic Content

**Goal**: Efficiently explore dynamic content without exhaustive crawling.

See [references/smart-sampling-rules.md](references/smart-sampling-rules.md) for detailed rules.

| Content Type | Sampling Strategy | playwright-cli Commands |
|---|---|---|
| **Paginated lists** | Page 1, one middle page, last page | `click <next-ref>` then `snapshot` |
| **Tabs** | All tabs (click each, record content differences) | `click <tab-ref>` then `snapshot` |
| **Accordions** | Expand all sections | `click <accordion-ref>` then `snapshot` |
| **Infinite scroll** | First 2 scroll loads | `eval "window.scrollTo(0, document.body.scrollHeight)"` then `snapshot` |
| **Modals** | All discoverable trigger paths | `click <trigger-ref>` then `snapshot`, close via `press Escape` |
| **Dropdowns** | Record all options without selecting (unless shadow mode) | `click <dropdown-ref>` then `snapshot`, close via `press Escape` |
| **Search/Filter** | Record available filter options, don't execute searches | `snapshot` (read-only observation) |
| **Sortable columns** | Record sortable column names | `snapshot` (read-only observation) |
| **Date pickers** | Record date range constraints if visible | `click <picker-ref>` then `snapshot` |

**Example: Exploring tabs on a page**:
```bash
# Click each tab by its ref from the snapshot
playwright-cli -s=<session-name> click <tab-ref>
# Capture the new content state
playwright-cli -s=<session-name> snapshot
# Screenshot the tab content
playwright-cli -s=<session-name> screenshot --filename=<output_dir>/screenshots/<page>-tab-<name>.png
```

**Example: Opening and recording a modal**:
```bash
# Click the modal trigger button
playwright-cli -s=<session-name> click <trigger-ref>
# Capture modal content
playwright-cli -s=<session-name> snapshot
playwright-cli -s=<session-name> screenshot --filename=<output_dir>/screenshots/<page>-modal-<name>.png
# Close the modal
playwright-cli -s=<session-name> press Escape
```

**Mode-specific behavior for writes**:

| Action | read-only | user-guided | shadow | playwright-cli Command |
|---|---|---|---|---|
| Navigate pages | Yes | Yes | Yes | `goto <url>` or `click <ref>` |
| Click tabs/accordions | Yes | Yes | Yes | `click <ref>` |
| Read form field attributes | Yes | Yes | Yes | `snapshot` (parse attributes) |
| Open modals (non-destructive) | Yes | Yes | Yes | `click <ref>` |
| Fill form fields | No | Ask user | Yes | `fill <ref> <text>` |
| Submit forms | No | Ask user | Yes | `click <submit-ref>` |
| Click delete buttons | No | Ask user | No (too risky) | — |
| Test validation by submitting invalid data | No | Ask user | Yes | `fill <ref> <invalid>` then `click <submit-ref>` |
| Create test records | No | Ask user | Yes | `fill` + `click` sequence |

### Phase 5: SPA DOM-State Discovery

**Goal**: Detect significant DOM changes that indicate a new "page" or feature
state, especially in SPAs where URL may not change.

See [references/exploration-strategies.md](references/exploration-strategies.md) for detailed SPA handling.

1. **Baseline DOM state** — take an accessibility snapshot of the current page:
   ```bash
   playwright-cli -s=<session-name> snapshot --filename=<output_dir>/snapshots/baseline.yaml
   ```

2. **After each interaction** (click, tab switch, modal open), capture a new state:
   ```bash
   playwright-cli -s=<session-name> click <ref>
   playwright-cli -s=<session-name> snapshot --filename=<output_dir>/snapshots/state-<n>.yaml
   ```
   - Parse and compare structural differences with previous snapshot
     (use `parse-snapshot.py` to extract structured data for comparison)
   - Check if the URL changed:
     ```bash
     playwright-cli -s=<session-name> eval "window.location.href"
     ```
   - If significant structural change detected (>30% DOM nodes different):
     - This is a new feature state
     - Take screenshot:
       ```bash
       playwright-cli -s=<session-name> screenshot --filename=<output_dir>/screenshots/state-<n>.png
       ```
     - Record as a separate page/state in the site map
     - Add to interaction inventory

3. **DOM change significance detection**:
   - **Major change** (new page): >50% of content nodes changed
   - **Medium change** (new state): 30-50% changed (e.g., tab content, modal)
   - **Minor change** (<30%): Filter/sort result, dropdown toggle — NOT a new state

4. **Handle SPA hash-based routing**: Normalize URLs by treating `#/route` as paths.
   Track `history.pushState` changes via URL checks after each click.

5. **Component correlation**: If `component-tree.json` from codebase analysis
   is available (`existing_discovery` input), cross-reference DOM states with
   component names to improve feature identification.

### Phase 6: Scenario Candidate Extraction

**Goal**: Generate functional test scenario candidates from all discovered
pages, forms, and interactions.

**Candidate generation rules**:

| Discovery | Candidate Type |
|---|---|
| Each form | Positive (valid submission) + Negative (validation errors) |
| Each required field | Negative (omit field) |
| Each field with constraints | Boundary (min/max length, min/max value) |
| Each table with actions | CRUD operations |
| Each navigation path | Navigation flow test |
| Each modal trigger | Modal open/close/submit test |
| Each authenticated page | Auth access test |
| Each role-specific element | Role-based access test |

**Scenario candidate format**:

```json
{
  "candidate_id": "URL-001",
  "feature": "Vehicle Management",
  "action": "Create new vehicle via form",
  "description": "Fill and submit vehicle creation form at /vehicles/new with 3 required fields",
  "source": "url",
  "source_evidence": "Page: /vehicles/new, Form: create-vehicle-form, Screenshot: screenshots/vehicles-new.png",
  "confidence": 0.85,
  "discovered_fields": ["name", "type", "plate_number"],
  "discovered_validations": [
    {"field": "name", "rule": "required, maxlength:100"},
    {"field": "plate_number", "rule": "required, pattern:[A-Z]{2}[0-9]{4}"}
  ],
  "discovered_endpoints": [],
  "video_timestamp": "",
  "screenshot_ref": "screenshots/vehicles-new.png",
  "component_path": ""
}
```

---

## Constraints

1. **Domain scope**: Only explore URLs under the provided `app_url` domain.
   Never follow external links.
2. **Rate limiting**: Add 500ms delay between navigation actions to avoid
   overwhelming the application.
3. **Page limit**: Stop after `max_pages` pages/states discovered.
4. **No login bypass**: Never attempt to guess credentials or bypass
   authentication. Always use the auth checkpoint.
5. **Session isolation**: Always use a named session (`-s=<session-name>`) to
   avoid conflicts with other browser sessions.
6. **Cleanup**: Close the playwright-cli session on completion or error:
   ```bash
   playwright-cli -s=<session-name> close
   ```
7. **Evidence capture**: Every explored page must have a screenshot and
   snapshot stored as evidence.
8. **Headed mode**: Always use `--headed` flag when opening the browser so
   users can observe and intervene if needed.

## Error Handling

| Error | Behavior |
|---|---|
| App URL unreachable | Fail with clear error and connectivity check |
| Page load timeout | Skip page, log warning, continue with next |
| Auth checkpoint timeout | Prompt user again (max 3 attempts), then skip URL pipeline |
| JavaScript errors on page | Check via `playwright-cli -s=<session-name> console error`, log errors, continue |
| playwright-cli crash | Save all artifacts collected so far, report partial results |
| Session conflicts | If the named session is already in use, append a timestamp to the session name |
| Modal stuck open | `playwright-cli -s=<session-name> press Escape`, wait 1s, try clicking close button, skip if still stuck |
| Infinite redirect loop | Detect after 5 redirects, skip page |

## Related Skills

| Skill | Relationship |
|---|---|
| **codebase-functional-analyzer** | Parallel — component-tree.json helps with SPA DOM correlation |
| **functional-scenario-merger** | Downstream — consumes scenario-candidates.jsonl |
| **functional-test-orchestrator** | Orchestrator — invokes after auth checkpoint in Phase 3 |