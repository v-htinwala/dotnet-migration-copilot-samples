---
name: uat-test-playwright-generator
description: >
  Acts as a Senior UAT Tester to generate comprehensive UAT test cases by
  exploring running web applications using Playwright CLI. Accepts natural
  language user journey descriptions from UAT testers or pre-qualified scenarios
  from uat-qualification-gate, discovers features by interacting with the app
  like a real user, and produces Excel test artifacts with business-focused test
  steps. Supports journey-based file organization (per-journey .spec.ts files
  when journey_id is present) and selective re-exploration (accepts
  existing_discovery from playwright-cli-web-discovery to avoid redundant
  crawling). Outputs canonical 20-field JSONL schema with extended traceability
  fields: journey_id, video_timestamp, screenshot_path, api_endpoint,
  component_path. Use when creating acceptance tests from a live web app URL,
  generating UAT documentation, or preparing testing deliverables. Invoke when
  user mentions "generate UAT from URL", "test web app", "acceptance tests",
  "explore app", "user journey", or "UAT from website".
license: Apache-2.0
compatibility: Requires playwright-cli (npm install -g @playwright/cli). Works with Claude Code, GitHub Copilot, or any skills-compatible coding agent.
metadata:
  author: uat-automation
  version: "4.0"
  category: testing
allowed-tools: Bash(playwright-cli:*)
---

# UAT Test Case Generator (Live Web App)

Generate **comprehensive, functional** User Acceptance Testing (UAT) test cases by exploring running web applications using Playwright CLI — acting as a **Senior UAT Tester**.

## Design Philosophy

> **You are a Senior UAT Tester.** You explore every corner of the application like a real user would, thinking about edge cases, error scenarios, and business workflows.
>
> **UAT validates "Did we build the RIGHT thing?"** — not "Did we build the thing right?"

This skill generates test cases in plain business language describing:
- **What** the user does (actions on the live app)
- **What** the user sees (expected visible results)
- **Why** it matters (business value and business requirements)
- **What could go wrong** (negative, boundary, edge cases)
- **Who** executes the test (user role / persona)
- **What type** of test it is (Functional, End-to-End, Business Rules, etc.)

## UAT Qualification Gate

Every generated test case **MUST** pass all 6 criteria to qualify as UAT:

| # | Criterion | Pass | Fail |
|---|-----------|------|------|
| 1 | **Business user perspective** | "Click the 'Save' button" | "Trigger handleSave()" |
| 2 | **Validates business requirements** | "Invoice total matches line items" | "DB column sum = API response" |
| 3 | **Real-world scenarios** | "Customer searches for a laptop" | "Call GET /api/products" |
| 4 | **Executable by end users** | "Verify success message appears" | "Check HTTP 201 in Network tab" |
| 5 | **Verifies business value** | "Order confirmation displays on screen" | "Assert email microservice invoked" |
| 6 | **Focuses on "what" not "how"** | "User sees updated name in header" | "React state re-rendered" |

**If a test case fails any criterion, rewrite it before including in output.** See [references/uat-qualification.md](references/uat-qualification.md) for the complete qualification model including non-UAT keyword detection.

## Test Classification

### By Priority (Business-Aligned)

| Priority | Criteria |
|----------|----------|
| **Critical (P1)** | Core business functions, revenue-impacting, regulatory compliance, blocks all users |
| **High (P2)** | Important workflows, frequently used features, impacts many users |
| **Medium (P3)** | Secondary features, edge cases, workarounds available |
| **Low (P4)** | Nice-to-have functionality, cosmetic, rarely used |

### By Test Type

| Type | Description |
|------|-------------|
| **Functional** | Validates a specific business function (default) |
| **End-to-End** | Complete user journey across modules |
| **Integration** | Cross-system workflows visible to users |
| **Usability** | User experience and intuitiveness |
| **Business Rules** | Validation of business logic and calculations |
| **Regression** | Previously working functionality still works |

### By Coverage Area

| Area | Description |
|------|-------------|
| **Business Process** | Core business workflows (invoice approval, order processing) |
| **User Role** | Role-specific tests (admin, manager, end-user) |
| **Module/Feature** | Specific application module (default) |
| **Compliance** | Regulatory, security, audit requirements |

## When to Use

- Creating UAT test cases from a **live web application URL**
- Processing **natural language user journey descriptions** from UAT testers
- Producing Excel-based test artifacts for acceptance testing
- Comprehensive feature discovery through real user interaction

## Prerequisites

```bash
npm install -g @playwright/cli
playwright-cli install-browser
```

## Input Formats

### URL Only
```
Generate UAT tests for https://app.example.com
```

### URL + User Journeys (Recommended)
```
URL: https://app.example.com

User Journeys:
1. Customer logs in, searches for product, adds to cart, completes checkout
2. Admin manages users, creates reports, exports data
```

When journeys are provided, the skill uses them as starting points for targeted exploration. See [references/journey-input-guide.md](references/journey-input-guide.md) for details.

### URL + Pre-Qualified Scenarios (Orchestrator Pipeline)
```
URL: https://app.example.com
Scenarios: uat-output/phase-4-merge/unified-scenarios.jsonl
Existing Discovery: uat-output/phase-2-url/
```

When `unified-scenarios.jsonl` is provided from the uat-qualification-gate,
the skill skips full feature discovery and generates tests directly from
qualified scenarios, using selective re-exploration for additional detail.

### Selective Re-Exploration (existing_discovery parameter)

When `existing_discovery` is provided (path to Phase 2 URL discovery artifacts):

1. **Load existing artifacts**: Read `site-map.json` and
   `interaction-inventory.json` from the discovery phase.
2. **Skip already-discovered routes**: Do not re-crawl routes that have
   complete interaction inventories.
3. **Selectively re-explore**: Only re-explore routes where additional element
   detail is needed (form field attributes, dynamic states, validation messages,
   dropdown options).
4. **Merge results**: Combine new element details with existing discovery data.

This avoids redundant crawling when the orchestrator pipeline has already
performed full URL discovery in Phase 2.

### Journey-Based File Organization

When `journey_id` is present in input scenarios, output is organized per-journey:

```
playwright-tests/
├── journeys/
│   ├── vehicle-crud.spec.ts      # All tests for J-VEH-CRUD
│   ├── booking-flow.spec.ts      # All tests for J-BOOK-FLOW
│   ├── auth-session.spec.ts      # All tests for J-AUTH-SESSION
│   └── ...
└── playwright.config.ts
```

Each `.spec.ts` file contains:
- All test cases for that journey as `test()` blocks
- Shared `beforeEach` for auth/navigation setup
- Page Object Model references where applicable
- Assertions based on `expected_result` and `test_steps`

When `journey_id` is **not** present, fall back to per-feature file organization.

## Workflow Overview

| Phase | Goal | Output |
|-------|------|--------|
| **0** | Journey Parsing (if journeys provided) | Prioritized feature map from user journeys |
| **1** | Feature Discovery (Live Exploration) | FEATURE_MAP with all features discovered |
| **2** | Test Case Generation (Playwright Interaction) | JSONL file with test cases |
| **3** | Excel Consolidation | Excel workbook with Summary Dashboard |

---

## Phase 0: Journey Input Processing (Optional)

> ✅ Use when UAT testers provide natural language journey descriptions.

Parse journey descriptions into prioritized feature exploration plan:

```
Input: "User logs in, searches for laptop, adds to cart, completes checkout"

Parsed:
| Step | Action | Feature Type | Priority |
|------|--------|--------------|----------|
| 1 | logs in | Authentication | Critical |
| 2 | searches for laptop | Search | High |
| 3 | adds to cart | Cart Management | High |
| 4 | completes checkout | Checkout Workflow | Critical |
```

**Journey-Guided Exploration**: Use parsed steps as entry points, then discover additional scenarios around each step. See [references/journey-input-guide.md](references/journey-input-guide.md).

---

## Phase 1: Feature Discovery

> ⛔ Do NOT generate test cases. ONLY explore and identify features.

### Exploration Strategy

```bash
# Open application
playwright-cli open <APP_URL> --headed

# Snapshot landing page
playwright-cli snapshot --filename=snapshots/00-landing.yaml
playwright-cli screenshot --filename=screenshots/00-landing.png
```

**Systematically explore:**
- Main navigation menu — click every item
- Sidebar menus — expand all sections
- Header/footer links
- Dropdown menus — reveal sub-items

For each navigation item:
```bash
playwright-cli click <element-ref>
playwright-cli snapshot --filename=snapshots/nav-<page-name>.yaml
playwright-cli screenshot --filename=screenshots/nav-<page-name>.png
```

### Feature Types

| Type | Description |
|------|-------------|
| Login/Authentication | Sign in, SSO, MFA |
| Dashboard | Summary views, home pages |
| List/Search | Data grids, filtering |
| Form | Create/edit screens |
| Workflow | Multi-step processes |
| File Management | Upload/download |
| Settings | User configuration |

### Feature Discovery Output

```
═══════════════════════════════════════════════════════════════
APPLICATION: <App Name> (<APP_URL>)
═══════════════════════════════════════════════════════════════

FEATURES DISCOVERED:
┌────┬─────────────────────┬────────────┬──────────────┬─────────────┐
│ ID │ Feature Name        │ Type       │ URL/Route    │ Est. Tests  │
├────┼─────────────────────┼────────────┼──────────────┼─────────────┤
│ 1  │ Authentication      │ Login      │ /login       │ 12          │
│ 2  │ Dashboard           │ Dashboard  │ /dashboard   │ 10          │
└────┴─────────────────────┴────────────┴──────────────┴─────────────┘

TOTAL ESTIMATED TEST CASES: <total>
═══════════════════════════════════════════════════════════════
```

---

## Phase 2: Test Case Generation

> ⛔ Process ONE feature at a time. Interact with the LIVE APP to discover behaviors.

### Test Case Principles (UAT-First)

1. **User-Centric**: "Click the 'Save' button" not "Trigger handleSave()"
2. **Observable**: "Success message displays" not "Database record inserted"
3. **No Jargon**: "Search for customer" not "Call GET /api/customers"
4. **Playwright-Verified**: Include CLI commands for each test
5. **Business-Focused**: Validates business requirements and user goals
6. **End-User Executable**: Can be run by business testers without dev tools
7. **Classified**: Every test has a type, coverage area, priority, and user role

### Coverage Requirements (UAT Scope)

> **UAT is high-level, workflow-oriented** — focus on whether the user can
> accomplish their business goal, not on exhaustive field-level validation.

| Category | What to Test | Min |
|----------|-------------|-----|
| **Happy path** | End-to-end business workflows that deliver user value | 3-5 |
| **Key error paths** | Errors a business user would realistically encounter | 1-2 |
| **Role-based access** | Different user roles can access their intended features | 1-2 |
| **Business rules** | Critical business logic outcomes (calculations, approvals, status changes) | 1-3 |

**Out of scope for UAT** (these belong in functional testing):
- Individual field boundary testing (min/max, special chars)
- Per-field validation messages
- Individual dropdown option testing
- Loading states, disabled states, UI micro-interactions

### Exploration Guidelines

See [references/anti-patterns.md](references/anti-patterns.md) for common mistakes to avoid.

Key rules:
- Focus on **complete user journeys**, not individual UI elements
- Test the **primary success path** and **one key failure path** per workflow
- Verify the user can **achieve their stated business objective**
- Test role-based access where different user roles have different capabilities
- Confirm **business-critical outcomes** are visible to the user (e.g., order confirmation, successful save)

### Processing Modes

Choose based on agent capabilities:

| Mode | When | Reference |
|------|------|-----------|
| **Streaming** (Default) | Always works | [references/phase2b-streaming-mode.md](references/phase2b-streaming-mode.md) |
| **Subagent** (If available) | `runSubagent` tool exists | [references/phase2a-subagent-mode.md](references/phase2a-subagent-mode.md) |

**Both modes write to JSONL after each batch** to prevent timeout.

### Example Exploration

```bash
# Navigate to feature
playwright-cli open <APP_URL>/create-customer
playwright-cli snapshot --filename=snapshots/create-customer.yaml

# Try empty submit (negative)
playwright-cli click <submit-ref>
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/validation-errors.png

# Fill correctly (positive)
playwright-cli fill <name-ref> "Test Customer 001"
playwright-cli fill <email-ref> "test@example.com"
playwright-cli click <submit-ref>
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/success.png
```

### Test Case Schema (Canonical 20-Field JSONL)

```json
{
  "test_id": "UAT-AUTH-001",
  "test_name": "Login with valid corporate credentials",
  "feature": "Authentication",
  "journey_id": "J-AUTH-SESSION",

  "test_type": "Functional",
  "coverage_area": "Business Process",
  "priority": "P1",
  "user_role": "End User",

  "preconditions": ["User has valid corporate account", "App accessible at <URL>"],
  "test_steps": [
    { "step_number": 1, "action": "Navigate to login page", "expected": "Login form is displayed" },
    { "step_number": 2, "action": "Enter corporate email", "expected": "Email field accepts input" },
    { "step_number": 3, "action": "Enter password", "expected": "Password field accepts input" },
    { "step_number": 4, "action": "Click Sign In", "expected": "Dashboard loads with welcome message" }
  ],
  "expected_result": "User sees dashboard with welcome message and their name in the header",
  "test_data": { "email": "testuser@example.com", "password": "ValidPass123!" },
  "business_objective": "Verify users can access the system to perform daily tasks",

  "source": "url",
  "source_evidence": "/login route discovery",
  "requirement_id": "REQ-AUTH-001",

  "video_timestamp": "",
  "screenshot_path": "phase-2-url/screenshots/login.png",
  "api_endpoint": "POST /api/auth/login",
  "component_path": ""
}
```

**Canonical schema fields (20 total)**:
- **Core identification**: `test_id`, `test_name`, `feature`, `journey_id`
- **Classification**: `test_type`, `coverage_area`, `priority`, `user_role`
- **Test content**: `preconditions`, `test_steps`, `expected_result`, `test_data`, `business_objective`
- **Source traceability**: `source`, `source_evidence`, `requirement_id`
- **Extended traceability**: `video_timestamp`, `screenshot_path`, `api_endpoint`, `component_path`

See [references/test-case-template.md](references/test-case-template.md) for complete templates.
See [references/uat-qualification.md](references/uat-qualification.md) for qualification rules.

---

---

## Output Structure

```
uat-tests/
├── uat_<project>.jsonl              # Test cases (JSONL)
├── UAT_Test_Cases_<Project>.xlsx    # Excel deliverable (Phase 3)
├── screenshots/                     # Visual evidence
│   ├── 00-landing.png
│   ├── nav-<page>.png
│   └── TC-XXX-NNN-<step>.png
└── snapshots/                       # Page structure
    ├── 00-landing.yaml
    └── nav-<page>.yaml
```

---

## Playwright CLI Quick Reference

See [references/playwright-cli-quick-ref.md](references/playwright-cli-quick-ref.md) for complete command reference.

Essential commands:

```bash
# Open and navigate
playwright-cli open <url> --headed
playwright-cli goto <url>

# Inspect page
playwright-cli snapshot --filename=snapshot.yaml
playwright-cli screenshot --filename=screenshot.png

# Interact with elements (use refs from snapshot)
playwright-cli click <ref>
playwright-cli fill <ref> "text"
playwright-cli select <ref> "option"
playwright-cli check <ref>
playwright-cli press Enter

# Handle dialogs
playwright-cli dialog-accept
playwright-cli dialog-dismiss

# Responsive testing
playwright-cli resize 375 812   # Mobile
playwright-cli resize 1920 1080 # Desktop

# Sessions
playwright-cli list
playwright-cli close-all
```

---

## References

- [references/uat-qualification.md](references/uat-qualification.md) — **UAT qualification criteria, test types, coverage areas, priority definitions**
- [references/journey-input-guide.md](references/journey-input-guide.md) — Natural language journey processing
- [references/feature-discovery-patterns.md](references/feature-discovery-patterns.md) — Feature identification patterns
- [references/phase2-exploration-workflow.md](references/phase2-exploration-workflow.md) — Detailed exploration workflow
- [references/phase2a-subagent-mode.md](references/phase2a-subagent-mode.md) — Subagent mode details
- [references/phase2b-streaming-mode.md](references/phase2b-streaming-mode.md) — Streaming mode details
- [references/test-case-template.md](references/test-case-template.md) — Test case templates
- [references/test-patterns.md](references/test-patterns.md) — Common testing patterns
- [references/workflow-examples.md](references/workflow-examples.md) — Complete workflow examples
- [references/playwright-cli-quick-ref.md](references/playwright-cli-quick-ref.md) — CLI command reference
- [references/batching-guide.md](references/batching-guide.md) — Excel batching guide
- [references/anti-patterns.md](references/anti-patterns.md) — Common mistakes to avoid

### Sample Files

- [assets/sample-test-cases.jsonl](assets/sample-test-cases.jsonl) — Example test cases
- [assets/sample-execution-results.jsonl](assets/sample-execution-results.jsonl) — Example results
- [assets/sample-suite-summary.json](assets/sample-suite-summary.json) — Suite summary example

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Element not found | Run `playwright-cli snapshot` to refresh refs |
| Session timeout | Use `playwright-cli list` to check sessions |
| Screenshot fails | Ensure directory exists |
| Dialog blocking | Use `dialog-accept` or `dialog-dismiss` |
| Dynamic content | Re-snapshot after interactions |