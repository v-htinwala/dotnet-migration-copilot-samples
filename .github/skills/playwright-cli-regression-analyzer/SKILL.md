---
name: playwright-cli-regression-analyzer
description: >
  Analyzes web discovery outputs to produce risk-scored regression analysis.
  Takes site maps, interaction inventories, API surfaces, and auth flow data
  from playwright-cli-web-discovery and identifies logical user flows,
  scores interaction complexity, maps regression categories, and optionally
  correlates with source files. Produces regression-analysis.json and
  flow-graph.json for downstream scenario generation. Use when you need to
  analyze discovered web structure for regression risk, identify user flows,
  or prioritize testing areas based on interaction complexity.
license: Apache-2.0
compatibility: >
  Requires Python 3.8+ for helper scripts. Works with discovery outputs from
  playwright-cli-web-discovery skill or any compatible JSON files matching
  the output schemas. Optionally uses codebase file search for source file
  correlation.
metadata:
  author: regression-testcase-generation
  version: "1.0"
allowed-tools: Bash(python:*) Bash(node:*) Read
---

# Playwright-CLI Regression Analyzer

## When to Use This Skill

Activate this skill when you need to:
- Analyze web discovery outputs to identify user flows and regression risk areas
- Score interaction complexity across discovered routes
- Classify discovered flows against standard regression categories
- Correlate browser-discovered routes with source code files
- Prioritize which areas of a web application need the most regression testing

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| **site-map.json** | Yes | — | Route graph from playwright-cli-web-discovery |
| **interaction-inventory.json** | Yes | — | Per-page element map from discovery |
| **api-surface.json** | Yes | — | Observed API endpoints from discovery |
| **auth-flows.json** | Yes | — | Authentication patterns from discovery |
| **Codebase path** | No | none | Path to source code for file correlation |
| **Risk weights** | No | defaults | Custom weights for risk scoring factors |
| **Output dir** | No | `./discovery-output` | Directory for output JSON files |

## 4-Phase Analysis Workflow

### Phase 1: Flow Identification

**Goal**: Group discovered routes into logical user flows.

1. **Parse the site map** to understand route hierarchy and navigation structure

2. **Identify flow patterns** using these heuristics:

   | Pattern | Flow Type | Example |
   |---|---|---|
   | Form page → POST API → redirect page | Creation flow | `/orders/new` → POST `/api/orders` → `/orders` |
   | List page + GET API + filter elements | Data management flow | `/items` with GET `/api/items?sort=...` |
   | Login form → POST auth → redirect | Authentication flow | `/login` → POST `/api/auth/login` → `/dashboard` |
   | CRUD API endpoints for same resource | Resource management flow | GET/POST/PUT/DELETE `/api/users` |
   | Table + sort + filter + pagination | Data browsing flow | `/admin/users` with sorting, filtering controls |
   | Form with validation + submit | Input flow | `/register` with required fields and submit |
   | Navigation menu → multiple pages | Navigation flow | Header nav linking to `/`, `/about`, `/contact` |
   | Modal trigger → dialog content → action | Modal interaction flow | "Delete" button → confirmation dialog → DELETE API |

3. **Build flow chains** by connecting:
   - Routes that link to each other (from `navigation_graph`)
   - Routes that share API endpoints (from `api-surface.json`)
   - Routes with form→result patterns (form submission → redirect)

4. **Name each flow** descriptively:
   - Use the primary resource/entity (e.g., "Order Management Flow")
   - Include the primary action verbs (e.g., "User Registration & Login Flow")

5. **Output**: `flow-graph.json` containing named flows with route chains,
   API dependencies, and interaction dependencies.

### Phase 2: Interaction Complexity Scoring

**Goal**: Score each route and flow for regression testing priority.

Score each route based on these factors:

| Factor | Weight | Scoring Method |
|---|---|---|
| Interactive element count | 0.25 | 0-10 based on count (0: <3, 3: 3-5, 5: 6-10, 8: 11-20, 10: >20) |
| API call count | 0.20 | 0-10 based on endpoints triggered (0: 0, 3: 1, 5: 2-3, 8: 4-5, 10: >5) |
| Form field count | 0.20 | 0-10 based on form fields (0: 0, 3: 1-2, 5: 3-5, 8: 6-10, 10: >10) |
| State management indicators | 0.15 | 0-10 based on dynamic elements (modals, tabs, accordions) |
| Auth requirements | 0.10 | 0 if no auth, 5 if optional, 10 if required |
| Navigation depth | 0.10 | 0-10 based on depth (0: depth 0, 3: depth 1, 5: depth 2, 10: depth 3+) |

**Risk level mapping:**
- `critical`: score >= 75
- `high`: score >= 50
- `medium`: score >= 25
- `low`: score < 25

**Flow-level scoring**: A flow's score is the weighted average of its constituent
routes, with a bonus for multi-route flows (+10 per route beyond the first, max +30).

### Phase 3: Regression Category Mapping

**Goal**: Classify each flow against the 10 standard regression scenario categories.

Map each identified flow to one or more regression categories based on the
interaction patterns discovered:

| Category | Detection Signals |
|---|---|
| **1. Navigation** | Routes with multiple outbound links, navigation landmarks, menu elements |
| **2. Interaction** | Routes with buttons, clickable elements, hover effects, state toggles |
| **3. Form handling** | Routes with `<form>` groups, validation fields, submit buttons |
| **4. API integration** | Routes triggering API endpoints (data-fetch or mutation) |
| **5. Routing** | Client-side navigation, URL parameter handling, redirect patterns |
| **6. Authentication** | Login/logout flows, protected routes, session management |
| **7. Modal/dialog** | Routes with dialog triggers, hidden dialog elements, overlay patterns |
| **8. Table/data** | Routes with table structures, sort/filter controls, pagination |
| **9. Error boundary** | API endpoints with error status codes, error message elements |
| **10. Responsive layout** | Layout landmarks, viewport-dependent elements |

A single flow may map to multiple categories (e.g., a form that calls an API
maps to both "Form handling" and "API integration").

### Phase 4: Source File Correlation (Optional)

**Goal**: Map discovered routes to actual source code files.

This phase runs only when a codebase path is provided.

1. **Route-to-file mapping**: For each discovered route path, search for:
   - Next.js pages: `app/<route>/page.tsx`, `pages/<route>.tsx`
   - React Router: components matching route paths in router configuration
   - File names matching the route slug (e.g., `/products` → `Products.tsx`)

2. **API-to-handler mapping**: For each API endpoint, search for:
   - Next.js API routes: `app/api/<path>/route.ts`, `pages/api/<path>.ts`
   - Express routes: files containing route handler definitions
   - File names matching API path (e.g., `/api/users` → `users.controller.ts`)

3. **Component-to-file mapping**: For interactive elements, search for:
   - Component names matching element labels
   - Form components, modal components, table components

4. **Output enrichment**: Add `target_files` (glob patterns) to each flow
   in the regression analysis, enabling the downstream scenario generator
   to include file-level targeting.

## Output Files

### regression-analysis.json

```json
{
  "base_url": "https://example.com",
  "analyzed_at": "2026-01-15T10:30:00Z",
  "flows": [
    {
      "id": "flow-1",
      "name": "Order Management Flow",
      "description": "CRUD operations for orders including list, create, edit, delete",
      "routes": ["/orders", "/orders/new", "/orders/:id"],
      "api_endpoints": ["GET /api/orders", "POST /api/orders", "PUT /api/orders/:id", "DELETE /api/orders/:id"],
      "categories": ["form-handling", "api-integration", "table-data"],
      "risk_score": 72,
      "risk_level": "high",
      "target_files": ["src/features/orders/**", "src/api/orders.ts"],
      "interactions": {
        "total_interactive_elements": 24,
        "form_count": 2,
        "api_call_count": 4,
        "requires_auth": true
      }
    }
  ],
  "route_scores": [
    {
      "url": "/orders",
      "risk_score": 65,
      "risk_level": "high",
      "factors": {
        "interactive_elements": 8,
        "api_calls": 5,
        "form_fields": 7,
        "state_indicators": 6,
        "auth_required": 10,
        "nav_depth": 3
      }
    }
  ],
  "stats": {
    "total_flows": 5,
    "critical_flows": 1,
    "high_flows": 2,
    "medium_flows": 1,
    "low_flows": 1,
    "total_categories_covered": 8
  }
}
```

### flow-graph.json

```json
{
  "base_url": "https://example.com",
  "analyzed_at": "2026-01-15T10:30:00Z",
  "flows": [
    {
      "id": "flow-1",
      "name": "Order Management Flow",
      "chain": [
        {
          "url": "/orders",
          "action": "view list",
          "next": ["/orders/new", "/orders/:id"]
        },
        {
          "url": "/orders/new",
          "action": "create order form",
          "api": "POST /api/orders",
          "next": ["/orders"]
        },
        {
          "url": "/orders/:id",
          "action": "edit order",
          "api": "PUT /api/orders/:id",
          "next": ["/orders"]
        }
      ],
      "entry_point": "/orders",
      "exit_points": ["/orders"]
    }
  ],
  "orphan_routes": ["/about", "/help"],
  "stats": {
    "total_flows": 5,
    "max_chain_length": 4,
    "orphan_count": 2
  }
}
```

## Error Handling

- If discovery files are missing or malformed, report which files are invalid
  and analyze with whatever data is available
- If source file correlation fails to find matches, leave `target_files` empty
  and note unresolved routes in the output
- If a route has no interactive elements, assign it a minimum risk score of 5
  (it's still a route that should render correctly)
