---
name: playwright-cli-web-discovery
description: >
  Discovers and inventories web application structure using Microsoft's
  playwright-cli for live browser exploration. Captures site maps, interactive
  elements, API surfaces, and authentication flows from any running web
  application URL. Use when you need to explore a web app's routes,
  interactions, network requests, or auth patterns before regression analysis.
  Produces structured JSON outputs (site-map.json, interaction-inventory.json,
  api-surface.json, auth-flows.json) suitable for downstream regression
  analysis and scenario generation. Works with SPAs, MPAs, and authenticated
  applications.
license: Apache-2.0
compatibility: >
  Requires playwright-cli installed globally or via npx
  (@playwright/cli@latest). Node.js 18+ required. Works with any web
  application accessible via HTTP/HTTPS. Best with VS Code Copilot or
  agents supporting Bash tool execution.
metadata:
  author: regression-testcase-generation
  version: "1.0"
allowed-tools: Bash(playwright-cli:*) Bash(npx:*) Bash(node:*)
---

# Playwright-CLI Web Discovery

## When to Use This Skill

Activate this skill when you need to:
- Explore a live web application and map its routes, pages, and navigation structure
- Inventory all interactive elements (buttons, forms, inputs, links) on each page
- Capture the API surface (XHR/fetch requests) observed during navigation
- Detect authentication flows, protected routes, and session management patterns
- Produce structured JSON outputs for downstream regression analysis
- Create a baseline site map for change detection or monitoring

## Prerequisites

Before starting, verify `playwright-cli` is available:

```bash
playwright-cli --help
```

If not installed, install via:

```bash
npm install -g @playwright/cli@latest
```

## User Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| **URL** | Yes | — | Base URL of the web application to explore |
| **Session name** | No | `web-discovery` | Named session for playwright-cli (`-s=<name>`) |
| **Exploration depth** | No | 2 | Maximum link traversal depth from the landing page |
| **Auth config** | No | none | Authentication credentials or pre-auth steps |
| **Timeout** | No | 30000 | Page load timeout in milliseconds |
| **Exclude patterns** | No | none | URL patterns to skip (e.g., external links, logout) |
| **Output dir** | No | `./discovery-output` | Directory for output JSON files and screenshots |

## Safety Rules

1. **Read-only exploration** — NEVER submit forms, click delete/destructive buttons,
   or perform state-changing actions unless explicitly instructed
2. **Respect rate limits** — Add 500ms delay between navigation actions
3. **Stay in scope** — Only explore URLs under the provided base URL domain
4. **Session isolation** — Always use a named session (`-s=<name>`) to avoid
   conflicts with other browser sessions
5. **Clean up** — Close the session when exploration is complete

## 5-Phase Exploration Workflow

### Phase 1: Open & Orient

**Goal**: Establish a browser session and capture the initial page state.

1. Open the target URL in a named session:
   ```bash
   playwright-cli -s=<session-name> open <url>
   ```

2. Wait for the page to fully load, then capture the initial snapshot:
   ```bash
   playwright-cli -s=<session-name> snapshot
   ```
   This returns a YAML accessibility tree of the page. Parse it to identify:
   - Page title (`document` node's `name` attribute)
   - Top-level landmarks (navigation, main, footer, etc.)
   - All interactive elements with their `ref` identifiers

3. Capture a visual baseline screenshot:
   ```bash
   playwright-cli -s=<session-name> screenshot --filename=<output-dir>/screenshots/landing.png
   ```

4. Record the initial state:
   - Current URL
   - Page title
   - Element count (from snapshot)
   - Timestamp

### Phase 2: Discover Routes

**Goal**: Map all reachable routes by following navigation links.

1. From the Phase 1 snapshot, extract all link elements:
   - Look for `link` role nodes in the snapshot YAML
   - Extract `ref`, `name` (link text), and `url` attributes
   - Filter out external links (different domain) and excluded patterns

2. For each discovered link, navigate and capture:
   ```bash
   playwright-cli -s=<session-name> click <ref>
   ```
   Wait for navigation to settle, then:
   ```bash
   playwright-cli -s=<session-name> snapshot
   ```
   Record:
   - New URL (from snapshot or `playwright-cli -s=<session-name> eval "window.location.href"`)
   - Page title
   - Element count
   - Parent route (where the link was found)

3. Track visited URLs to avoid re-visiting (handle SPA hash routes and query params)

4. If the exploration depth is > 1, recurse: extract links from each newly
   discovered page and follow those too, up to the configured depth

5. For SPAs that don't change the URL on navigation:
   - Track content changes by comparing snapshot element counts and structure
   - Use the link text as a route identifier
   - Watch for `history.pushState` via URL changes

6. Build the route graph:
   - Nodes: each unique URL/page discovered
   - Edges: navigation links between pages
   - Metadata: page title, element count, screenshot path

7. Output: Write `site-map.json` to the output directory.
   See [references/output-schemas.md](references/output-schemas.md) for the schema.

### Phase 3: Inventory Interactions

**Goal**: Enumerate all interactive elements on each discovered route.

1. For each route in the site map, navigate to the page:
   ```bash
   playwright-cli -s=<session-name> goto <url>
   ```
   Then capture a fresh snapshot:
   ```bash
   playwright-cli -s=<session-name> snapshot
   ```

2. Parse the snapshot to extract interactive elements. Classify each by type:

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

3. For each interactive element, record:
   - `ref`: playwright-cli element reference
   - `role`: ARIA role from snapshot
   - `name`: accessible name from snapshot
   - `type`: classification from table above
   - `attributes`: relevant attributes (placeholder, required, disabled, etc.)
   - `page_url`: the route where this element was found

4. Identify form groups:
   - Group elements within `<form>` containers
   - Identify submit buttons associated with each form
   - Count required vs optional fields

5. Output: Write `interaction-inventory.json` to the output directory.
   See [references/output-schemas.md](references/output-schemas.md) for the schema.

### Phase 4: Capture API Surface

**Goal**: Record all network requests (XHR/fetch) observed during exploration.

1. Enable network monitoring. For each route, after navigating:
   ```bash
   playwright-cli -s=<session-name> network
   ```
   This captures ongoing network activity. Record all requests.

2. Also trigger interactions that may fire API calls:
   - Click buttons that appear to load data
   - Submit search forms
   - Toggle filters or dropdowns
   Monitor network during these actions.

3. For each observed API request, record:
   - `method`: HTTP method (GET, POST, PUT, DELETE, PATCH)
   - `url_pattern`: URL with path parameters abstracted (e.g., `/api/users/:id`)
   - `url_example`: actual URL observed
   - `status`: HTTP response status code
   - `content_type`: response content type
   - `triggered_by`: the page/action that triggered this request
   - `request_body_shape`: JSON keys if POST/PUT (no actual values)
   - `response_body_shape`: top-level JSON keys of response (no actual values)

4. Deduplicate endpoints:
   - Group by `method` + `url_pattern`
   - Merge observations from different pages
   - Identify parameterized routes (e.g., `/api/items/123` → `/api/items/:id`)

5. Classify endpoints:
   - `data-fetch`: GET requests returning JSON data
   - `mutation`: POST/PUT/DELETE/PATCH requests
   - `auth`: endpoints containing `auth`, `login`, `session`, `token`
   - `static`: requests for images, fonts, CSS, JS bundles (exclude from output)

6. Output: Write `api-surface.json` to the output directory.
   See [references/output-schemas.md](references/output-schemas.md) for the schema.

### Phase 5: Detect Auth Flows

**Goal**: Identify authentication mechanisms and protected routes.

1. Check for login pages:
   - Look for routes with URLs containing `login`, `signin`, `auth`
   - Look for forms with password fields in the interaction inventory
   - Look for "Login", "Sign In" buttons

2. Check for protected routes (redirects):
   - Navigate to routes that returned redirects during Phase 2
   - Record redirect chains (e.g., `/dashboard` → `/login?redirect=/dashboard`)
   - Identify which routes require authentication

3. Inspect storage for auth tokens:
   ```bash
   playwright-cli -s=<session-name> localstorage-list
   ```
   ```bash
   playwright-cli -s=<session-name> cookie-list
   ```
   ```bash
   playwright-cli -s=<session-name> sessionstorage-list
   ```
   Look for common auth token patterns:
   - `token`, `access_token`, `jwt`, `session`, `auth` in localStorage/sessionStorage keys
   - `session`, `sid`, `token`, `auth` in cookie names

4. Check for OAuth/SSO patterns:
   - Look for redirects to external identity providers
   - Look for `/callback`, `/oauth`, `/sso` routes

5. Record auth flow patterns:
   - `form-based`: login form on the same domain
   - `oauth`: redirect to external provider
   - `token-based`: JWT in localStorage/cookies
   - `session-based`: server-side session cookies
   - `none`: no authentication detected

6. Output: Write `auth-flows.json` to the output directory.
   See [references/output-schemas.md](references/output-schemas.md) for the schema.

### Session Cleanup

After all phases complete:
```bash
playwright-cli -s=<session-name> close
```

## Output Files Summary

| File | Description |
|---|---|
| `site-map.json` | Route graph with pages, titles, hierarchy, and navigation links |
| `interaction-inventory.json` | Per-page interactive element map with refs and classifications |
| `api-surface.json` | Observed API endpoints with methods, patterns, and response shapes |
| `auth-flows.json` | Detected authentication patterns and protected routes |
| `screenshots/` | Visual captures of each discovered page |

## Error Handling

- **Timeout**: If a page fails to load within the timeout, skip it and log the error.
  Continue with remaining routes.
- **Auth required**: If exploration is blocked by auth, log the protected route
  and continue exploring public routes. Report auth requirements in output.
- **Network errors**: Retry failed navigations once. If still failing, skip and log.
- **Session conflicts**: If the named session is already in use, append a timestamp
  to the session name.

## Tips for Effective Exploration

- Start with a **shallow exploration** (depth=1) to get a quick overview,
  then increase depth for thorough discovery
- For authenticated apps, provide auth config so protected routes can be explored
- Use **exclude patterns** to skip logout URLs, external links, and repetitive
  paginated pages
- For SPAs with client-side routing, pay attention to URL hash and pushState changes
- Review screenshots after discovery to verify the exploration captured meaningful pages
