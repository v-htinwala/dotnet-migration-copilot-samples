---
name: playwright-cli-regression-scenario-generator
description: >
  Transforms regression analysis into structured regression-scenarios.yml
  compatible with the existing regression-orchestrator agent. Takes risk-scored
  flows and interaction data from playwright-cli-regression-analyzer and
  generates scenario definitions with names, target files, target routes,
  expected behaviors, requirement IDs, and priority levels. Produces both
  YAML (.yml) and natural language (.md) outputs for maximum compatibility
  with the regression orchestrator's input formats. Use when you need to
  convert web discovery analysis into actionable regression test scenarios
  for the existing regression testing workflow.
license: Apache-2.0
compatibility: >
  Requires Python 3.8+ for helper scripts. Output format is compatible
  with regression-orchestrator.agent.md input #11 (regression scenarios).
  Supports both YAML and Markdown output formats.
metadata:
  author: regression-testcase-generation
  version: "1.0"
allowed-tools: Bash(python:*) Bash(node:*) Read
---

# Playwright-CLI Regression Scenario Generator

## When to Use This Skill

Activate this skill when you need to:
- Convert regression analysis into structured `regression-scenarios.yml`
- Generate scenario definitions compatible with the regression-orchestrator agent
- Transform flow and risk data into testable expected behaviors
- Produce both YAML and natural language scenario descriptions
- Bridge web discovery outputs into the existing 8-phase regression workflow

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| **regression-analysis.json** | Yes | — | Risk-scored flows from playwright-cli-regression-analyzer |
| **flow-graph.json** | Yes | — | User flow chains from analyzer |
| **interaction-inventory.json** | No | — | For detailed behavior extraction |
| **api-surface.json** | No | — | For API behavior assertions |
| **Requirement IDs** | No | none | Comma-separated ticket IDs for traceability |
| **Business criticality overrides** | No | none | Override flow priorities |
| **Output dir** | No | `./discovery-output` | Directory for output files |

## 3-Phase Generation Workflow

### Phase 1: Scenario Generation

**Goal**: Create a structured scenario for each identified flow.

1. **Load regression analysis**: Read `regression-analysis.json` to get flows
   with risk scores, categories, and route/API data.

2. **For each flow**, generate a scenario with these fields:

   | Field | Source | Description |
   |---|---|---|
   | `name` | Flow name (PascalCase) | Unique scenario identifier |
   | `description` | Flow description + routes | Human-readable scenario narrative |
   | `target_files` | Source correlation or route-based patterns | Glob patterns for source files |
   | `target_routes` | Flow routes | URL paths for E2E testing |
   | `api_endpoints` | Flow API endpoints | API methods and patterns to mock/intercept |
   | `expected_behaviors` | Phase 2 extraction | Assertion descriptions |
   | `requirement_ids` | User-provided or auto-generated | Traceability tags |
   | `priority` | Risk level from analysis | `critical`, `high`, `medium`, `low` |

3. **Naming convention**: Convert flow names to PascalCase scenario names:
   - "Order Management Flow" → `OrderManagementFlow`
   - "Authentication Flow" → `AuthenticationFlow`
   - "Search & Results Flow" → `SearchResultsFlow`

4. **Target files**: If source file correlation was performed (Phase 4 of analyzer),
   use the resolved `target_files`. Otherwise, generate route-based patterns:
   - `/orders` → `"src/**/orders/**"`, `"src/**/Order*.{tsx,ts}"`
   - `/api/users` → `"src/**/users/**"`, `"src/**/api/users*"`

5. **Priority mapping**: Use the flow's risk level directly:
   - `critical` (score >= 75) → `priority: critical`
   - `high` (score >= 50) → `priority: high`
   - `medium` (score >= 25) → `priority: medium`
   - `low` (score < 25) → `priority: low`
   - Apply business criticality overrides if provided

### Phase 2: Expected Behavior Extraction

**Goal**: Convert interaction inventory into testable assertion descriptions.

For each route in a flow, generate expected behaviors from the interaction data:

#### Page Rendering Behaviors
- For each route: `"Page at {route} should render successfully"`
- For pages with headings: `"Page at {route} should display heading '{heading text}'"`
- For pages with specific content: `"Page at {route} should show {content description}"`

#### Navigation Behaviors
- For each navigation link: `"Clicking '{link text}' should navigate to {target route}"`
- For breadcrumbs: `"Breadcrumb should show correct hierarchy for {route}"`

#### Form Behaviors
- For required fields: `"Form at {route} should validate required field '{field name}'"`
- For email fields: `"Form at {route} should validate email format for '{field name}'"`
- For password fields: `"Form at {route} should enforce password requirements"`
- For submit: `"Form submission at {route} should call {API method} {API endpoint}"`
- For validation: `"Form at {route} should show validation errors for invalid input"`

#### API Integration Behaviors
- For GET endpoints: `"API {method} {pattern} should return data for {route}"`
- For mutation endpoints: `"{action} action should call {method} {pattern}"`
- For error handling: `"Error response from {method} {pattern} should show error message"`

#### Interactive Element Behaviors
- For buttons: `"Button '{button name}' at {route} should {action description}"`
- For toggles: `"Toggle '{name}' should change state when clicked"`
- For dropdowns: `"Dropdown '{name}' should show options when opened"`

#### Modal/Dialog Behaviors
- For modal triggers: `"Modal triggered by '{trigger name}' should be visible"`
- For modal dismiss: `"Modal should be dismissible via Escape key"`
- For modal actions: `"Modal '{name}' confirm action should {expected effect}"`

#### Table/Data Behaviors
- For tables: `"Table at {route} should display data from {API endpoint}"`
- For sorting: `"Clicking column header should sort table data"`
- For filtering: `"Filter input should filter table rows"`
- For pagination: `"Pagination controls should navigate between pages"`

#### Authentication Behaviors
- For login: `"Login form should accept credentials and redirect to {target}"`
- For protected routes: `"Navigating to {route} without auth should redirect to {login}"`
- For logout: `"Logout should clear session and redirect to {login}"`

### Phase 3: Output Generation

**Goal**: Write output files in formats compatible with the regression orchestrator.

#### regression-scenarios.yml

Write the YAML file matching the exact schema expected by the orchestrator
(see [assets/regression-scenarios.example.yml](assets/regression-scenarios.example.yml)):

```yaml
scenarios:
  - name: ScenarioName
    description: >
      Multi-line description of the scenario.
    target_files:
      - "src/features/entity/**"
    target_routes:
      - "/route-path"
    api_endpoints:
      - "GET /api/resource"
    expected_behaviors:
      - "Behavior assertion 1"
      - "Behavior assertion 2"
    requirement_ids:
      - "REQ-XXX-001"
    priority: high
```

#### regression-scenarios.md

Write a natural language Markdown version that the orchestrator can also parse
via its Phase 1 natural language parsing:

```markdown
# Regression Scenarios

## Scenario: Order Management Flow

**Priority**: High
**Routes**: /orders, /orders/new, /orders/:id
**API Endpoints**: GET /api/orders, POST /api/orders

### Expected Behaviors
- Page at /orders should display a list of orders
- Form at /orders/new should validate required fields
- ...

**Requirement IDs**: REQ-ORD-001, REQ-ORD-002
**Target Files**: src/features/orders/**
```

#### orchestrator-inputs.json

Write a convenience file with pre-computed parameters for invoking the
regression orchestrator:

```json
{
  "regression_scenarios": "./discovery-output/regression-scenarios.yml",
  "test_framework": "playwright",
  "test_level": "e2e",
  "base_url": "https://example.com",
  "browser_targets": "chromium",
  "scenario_count": 5,
  "critical_count": 1,
  "high_count": 2,
  "medium_count": 1,
  "low_count": 1
}
```

## Output Files Summary

| File | Format | Consumer |
|---|---|---|
| `regression-scenarios.yml` | YAML | regression-orchestrator (structured input) |
| `regression-scenarios.md` | Markdown | regression-orchestrator (natural language input) |
| `orchestrator-inputs.json` | JSON | Automation scripts or manual handoff |

## Behavior Extraction Quality Guidelines

- **Be specific**: `"Form should validate email"` is too vague.
  Use `"Form at /register should reject 'invalid-email' format for Email field"`
- **Be observable**: Every behavior must be verifiable through browser interaction
  (visible text, navigation, network requests)
- **Include both happy and error paths**: For each form, generate both
  "successful submission" and "validation error" behaviors
- **Limit per scenario**: Aim for 5-15 expected behaviors per scenario.
  More than 15 suggests the flow should be split into sub-flows
- **Use consistent language**: Start with subject ("Page", "Form", "Button",
  "API", "Modal"), then action ("should display", "should navigate",
  "should validate", "should call")
