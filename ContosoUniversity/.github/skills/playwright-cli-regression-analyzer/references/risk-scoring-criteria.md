# Risk Scoring Criteria

Scoring rubric for interaction complexity, aligned with the existing
qualification-criteria.md weights from the regression test generation skills.

## Scoring Overview

Each route is scored on a 0-100 scale across 6 factors. The weighted sum
determines the final risk score and risk level.

## Factor Definitions

### Factor 1: Interactive Element Count (Weight: 0.25)

Measures the density of interactive elements on a page.

| Element Count | Score | Rationale |
|---|---|---|
| 0-2 | 0 | Static content, minimal interaction surface |
| 3-5 | 3 | Light interaction (e.g., navigation-only page) |
| 6-10 | 5 | Moderate interaction (e.g., detail page with actions) |
| 11-20 | 8 | Heavy interaction (e.g., dashboard with multiple controls) |
| 21+ | 10 | Very dense interaction (e.g., complex form or admin panel) |

**Source**: `interaction-inventory.json` → `pages[].stats.total_interactive`

### Factor 2: API Call Count (Weight: 0.20)

Measures the number of API endpoints triggered by or related to a route.

| API Calls | Score | Rationale |
|---|---|---|
| 0 | 0 | No API dependency (static page or client-only) |
| 1 | 3 | Single data source |
| 2-3 | 5 | Multiple data sources or CRUD operations |
| 4-5 | 8 | Complex data orchestration |
| 6+ | 10 | Heavy API integration (microservices facade) |

**Source**: `api-surface.json` → endpoints where `triggered_by[].page_url` matches route

### Factor 3: Form Field Count (Weight: 0.20)

Measures the complexity of form interactions on a page.

| Form Fields | Score | Rationale |
|---|---|---|
| 0 | 0 | No forms on page |
| 1-2 | 3 | Simple form (search, login) |
| 3-5 | 5 | Moderate form (contact, settings) |
| 6-10 | 8 | Complex form (registration, multi-section) |
| 11+ | 10 | Very complex form (wizard step, admin config) |

**Source**: `interaction-inventory.json` → `pages[].forms[].total_field_count`

### Factor 4: State Management Indicators (Weight: 0.15)

Measures dynamic UI complexity — elements that change state within the page.

| Indicator | Points |
|---|---|
| Modal/dialog triggers present | +3 |
| Tab navigation present | +2 |
| Accordion/collapsible sections | +2 |
| Toggle switches | +1 each (max +3) |
| Dynamic content areas (menus, dropdowns) | +2 |

Cap at 10.

**Source**: `interaction-inventory.json` → elements with types `modal-trigger`,
`tab-navigation`, `action-toggle`

### Factor 5: Auth Requirements (Weight: 0.10)

Measures authentication complexity associated with the route.

| Auth State | Score | Rationale |
|---|---|---|
| No auth needed | 0 | Public page |
| Auth available but not required | 5 | Mixed-access page |
| Auth required | 10 | Protected page (redirects to login) |

**Source**: `auth-flows.json` → `protected_routes` matching the route URL

### Factor 6: Navigation Depth (Weight: 0.10)

Measures how deep in the navigation hierarchy the route sits.

| Depth | Score | Rationale |
|---|---|---|
| 0 (landing page) | 0 | Most tested page, lowest regression risk |
| 1 | 3 | First-level pages (commonly tested) |
| 2 | 5 | Second-level pages (moderate testing) |
| 3+ | 10 | Deep pages (often under-tested, higher risk) |

**Source**: `site-map.json` → `routes[].depth`

## Final Score Calculation

```
route_score = (
    interactive_elements_score * 0.25 +
    api_calls_score            * 0.20 +
    form_fields_score          * 0.20 +
    state_indicators_score     * 0.15 +
    auth_score                 * 0.10 +
    nav_depth_score            * 0.10
) * 10
```

Result is on a 0-100 scale.

## Risk Level Mapping

| Score Range | Risk Level | Testing Priority |
|---|---|---|
| 75-100 | `critical` | Must have regression tests; test first |
| 50-74 | `high` | Should have regression tests; test in priority order |
| 25-49 | `medium` | Nice to have regression tests; test if time permits |
| 0-24 | `low` | May skip regression tests; test on full regression only |

## Flow-Level Score Aggregation

A flow's score is computed from its constituent routes:

```
flow_score = weighted_avg(route_scores) + multi_route_bonus
```

Where:
- `weighted_avg` uses each route's interactive element count as weight
- `multi_route_bonus` = min(30, (route_count - 1) * 10)

This ensures multi-route flows (which have more points of failure) score
higher than single-route pages with equivalent complexity.

## Alignment with Existing Qualification Criteria

This scoring aligns with the qualification-criteria.md weights:

| Qualification Criteria Factor | Equivalent Analyzer Factor |
|---|---|
| Cyclomatic complexity (0.3) | Interactive element count + State management (0.40) |
| Change frequency (0.3) | n/a (discovery-based, no git history) |
| Defect history (0.2) | n/a (discovery-based, no bug history) |
| Business criticality (0.2) | Auth requirements + Navigation depth (0.20) |

The analyzer fills the "change frequency" and "defect history" gaps with
API call complexity and form field count, which are strong proxies for
regression risk in the absence of git history.
