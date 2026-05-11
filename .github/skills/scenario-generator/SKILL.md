---
name: scenario-generator
description: >
  Transforms regression analysis into structured UAT test scenarios optimized
  for functional test case generation. Takes risk-scored flows, video-to-code
  correlation, and coverage gaps from regression-analyzer and produces
  prioritized scenario definitions with business-focused expected behaviors,
  test data recommendations, and coverage requirements. Outputs canonical
  20-field JSONL schema compatible with uat-test-case-generator,
  uat-test-reviewer, and scenario-merger, plus a human-readable Markdown
  summary. Includes journey_id grouping and extended traceability fields
  (video_timestamp, screenshot_path, api_endpoint, component_path). Use when
  you need to convert video + codebase regression analysis into actionable UAT
  scenarios, bridge visual evidence with testable business requirements, or
  prioritize test effort across discovered user flows.
license: MIT
compatibility: Requires Python 3.8+ for helper scripts. Consumes output from regression-analyzer skill (regression-analysis.json, flow-graph.json,correlation-map.json). Output is compatible with uat-test-case-generator and uat-test-reviewer input formats.
metadata:
  author: uat-automation
  version: "2.0"
  category: testing
---

# Scenario Generator (Video + Codebase → UAT Scenarios)

## Purpose

Transform regression analysis output into structured, business-focused UAT test
scenarios. This skill bridges the gap between **technical analysis** (risk-scored
flows, code correlation) and **tester-ready deliverables** (scenario descriptions,
expected behaviors, test data recommendations).

> **Key Differentiator**: This skill produces scenarios grounded in both visual
> evidence (video frames showing actual UI states) and code analysis (business
> rules, validation logic, API contracts). Every scenario traces back to what
> was observed AND what the code implements.

## When to Use This Skill

Activate this skill when you need to:
- Convert regression analysis into UAT test scenarios
- Generate business-focused expected behaviors from technical flow data
- Produce scenario definitions compatible with `uat-test-case-generator`
- Create a prioritized scenario backlog from video + codebase analysis
- Bridge visual demo evidence with testable business requirements
- Identify test data requirements for each scenario

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| **regression-analysis.json** | Yes | — | Risk-scored flows from regression-analyzer |
| **flow-graph.json** | Yes | — | User flow chains with video timestamps from regression-analyzer |
| **correlation-map.json** | Yes | — | Frame-to-file mappings from regression-analyzer |
| **Codebase path** | No | — | Source code for extracting business rules and validation details |
| **Business context** | No | none | Additional business requirements or user stories |
| **Requirement IDs** | No | none | Comma-separated ticket IDs for traceability |
| **Output dir** | No | `./scenario-output` | Directory for output files |

## UAT Qualification Gate

Every generated scenario and expected behavior **MUST** pass all 6 UAT criteria:

| # | Criterion | Pass Example | Fail Example |
|---|-----------|--------------|--------------|
| 1 | **Business user perspective** | "Fill in the customer name field" | "Set input[name='custName'] value" |
| 2 | **Validates business requirements** | "Order total reflects applied discount" | "DB trigger updates total column" |
| 3 | **Real-world scenarios** | "Manager approves employee leave request" | "PUT /api/leave/:id with status=approved" |
| 4 | **Executable by end users** | "Verify confirmation message appears" | "Assert HTTP 200 in response" |
| 5 | **Verifies business value** | "Customer receives order confirmation" | "Email microservice queue depth = 1" |
| 6 | **Focuses on what, not how** | "Dashboard shows updated sales figures" | "React state re-renders SalesChart" |

---

## 4-Phase Generation Workflow

### Phase 1: Scenario Definition

**Goal**: Create a structured scenario for each identified flow.

1. **Load regression analysis**: Read `regression-analysis.json` to get flows
   with risk scores, categories, route/API data, video evidence, and business rules.

2. **For each flow**, generate a scenario with these fields:

   | Field | Source | Description |
   |---|---|---|
   | `scenario_id` | Auto-generated | Unique identifier: `SCN-{PREFIX}-{NNN}` |
   | `name` | Flow name | Human-readable scenario name |
   | `description` | Flow description + video context | Narrative of what this scenario tests |
   | `priority` | Risk level from analysis | `Critical`, `High`, `Medium`, `Low` |
   | `test_type` | Flow categories | Primary: `Functional`, `End-to-End`, `Business Rules` |
   | `coverage_area` | Business context | `Business Process`, `User Role`, `Module/Feature`, `Compliance` |
   | `journey_id` | Auto-generated | Groups related scenarios: `J-{PREFIX}-{FLOW}` |
   | `target_routes` | Flow routes | URL paths the scenario covers |
   | `target_files` | Correlation map | Source files to reference |
   | `api_endpoints` | Flow APIs | API methods exercised |
   | `video_evidence` | Frame references | Frames showing the UI states |
   | `video_timestamp` | Manifest timestamps | MM:SS reference in source video |
   | `screenshot_path` | Discovery screenshots | Path to relevant screenshot |
   | `api_endpoint` | Primary API | Main API endpoint for this scenario |
   | `component_path` | Correlation map | Primary source component path |
   | `business_rules` | Code analysis | Validation and logic rules to verify |
   | `expected_behaviors` | Phase 2 | Testable assertion descriptions |
   | `test_data_requirements` | Phase 3 | Data needed to execute the scenario |
   | `estimated_test_cases` | Calculated | Expected number of test cases |
   | `requirement_ids` | User-provided or auto-generated | Traceability tags |

3. **Priority mapping from risk scores**:
   - `critical` (score >= 75) → `Priority: Critical` — Core business, must test first
   - `high` (score >= 50) → `Priority: High` — Important workflows
   - `medium` (score >= 25) → `Priority: Medium` — Secondary features
   - `low` (score < 25) → `Priority: Low` — Nice-to-have coverage

4. **Gap-driven scenarios**: For each `code-only` gap in the regression analysis,
   generate an additional scenario explicitly marked as "Not Demonstrated in Video":
   ```
   SCN-GAP-001: Password Reset Flow
   Priority: High
   Note: This feature exists in code but was not demonstrated in the video.
         All test scenarios are derived from code analysis only.
   ```

### Phase 2: Expected Behavior Extraction

**Goal**: Convert flow data + code analysis into testable, business-language assertions.

For each route in a scenario, generate expected behaviors grouped by category:

#### Page Rendering Behaviors (from video frames)
- For each frame: `"Page at {route} should display {visual description from frame}"`
- For headings: `"Page should show heading '{heading text}'"`
- For key content: `"Page should display {data type} information"`

#### Navigation Behaviors (from flow chains)
- For each transition: `"After {action}, user should see {destination page description}"`
- For breadcrumbs: `"Breadcrumb should show: {expected hierarchy}"`
- For return navigation: `"User should be able to return to {previous page}"`

#### Form Behaviors (from code analysis)
- For required fields: `"Form should indicate '{field name}' is required"`
- For validation: `"Form should show error when '{field name}' contains {invalid input}"`
- For format rules: `"'{field name}' should accept {valid format description}"`
- For submission: `"Submitting the form with valid data should show success confirmation"`
- For cancel: `"Cancelling the form should return to {previous page} without saving"`

#### Data Display Behaviors (from video + code)
- For tables: `"Page should display a list of {entity type} with {column descriptions}"`
- For sorting: `"Clicking column header '{column}' should sort the list"`
- For filtering: `"Using the filter for '{field}' should narrow results"`
- For pagination: `"Pagination should allow navigating between result pages"`
- For counts: `"List should show the total count of {entity type}"`

#### Business Rule Behaviors (from code analysis)
- For status transitions: `"Changing status from '{from}' to '{to}' should {expected effect}"`
- For calculations: `"Total should equal sum of line items {with/without} tax"`
- For permissions: `"Users with '{role}' role should {can/cannot} perform {action}"`
- For uniqueness: `"System should prevent duplicate {entity} with same {field}"`

#### Error Handling Behaviors (from code + gap analysis)
- For required: `"Submitting without required fields should display validation errors"`
- For invalid: `"Entering invalid {data type} should show appropriate error message"`
- For not found: `"Accessing non-existent {entity} should show 'not found' message"`
- For unauthorized: `"Attempting {action} without permission should show access denied"`

#### Authentication Behaviors (from code + video)
- For login: `"Valid credentials should grant access to the application"`
- For logout: `"Logging out should return to the sign-in page"`
- For session: `"Expired session should redirect to login with appropriate message"`
- For protected pages: `"Accessing {protected page} without login should redirect to sign-in"`

### Phase 3: Test Data Requirements

**Goal**: Define specific test data needed for each scenario.

For each scenario, generate test data requirements:

1. **User accounts** needed:
   ```
   - Admin user: admin@example.com (Role: Administrator)
   - Standard user: user@example.com (Role: User)
   - Read-only user: viewer@example.com (Role: Viewer)
   ```

2. **Entity data** needed:
   ```
   - Existing records: At least 10 {entity} records for list/search testing
   - Edge case records: Record with maximum field lengths, special characters
   - Related records: {Parent entity} with associated {child entities}
   ```

3. **Boundary values**:
   ```
   - Empty string for text fields
   - Maximum length string ({N} characters)
   - Special characters: <, >, &, ", ', \
   - Numeric boundaries: 0, -1, MAX_INT
   - Date boundaries: past dates, future dates, today
   ```

4. **State prerequisites**:
   ```
   - Records in each status: Draft, Pending, Approved, Rejected
   - Records owned by different users (for permission testing)
   ```

### Phase 4: Output Generation

**Goal**: Write output files compatible with downstream UAT skills.

#### uat-scenarios.jsonl

One scenario per line, compatible with `uat-test-case-generator` Phase 1 input:

```json
{
  "scenario_id": "SCN-USR-001",
  "name": "User Management — Create New User",
  "description": "Validates the complete flow of creating a new user account, including form validation, submission, and confirmation. Demonstrated in video at 0:35-0:48.",
  "priority": "High",
  "test_type": "Functional",
  "coverage_area": "Business Process",
  "journey_id": "J-USR-MGMT",
  "target_routes": ["/users", "/users/new"],
  "target_files": ["app/users/page.tsx", "app/users/new/page.tsx", "app/components/UserForm.tsx"],
  "api_endpoints": ["POST /api/users", "GET /api/users"],
  "video_evidence": {
    "frames": ["frame_000015.jpg", "frame_000016.jpg", "frame_000017.jpg"],
    "timestamps": ["0:35", "0:40", "0:48"],
    "description": "Video shows form being filled and submitted with success confirmation"
  },
  "video_timestamp": "0:35",
  "screenshot_path": "phase-2-url/screenshots/users-new.png",
  "api_endpoint": "POST /api/users",
  "component_path": "app/users/new/page.tsx",
  "business_rules": [
    "Email must be unique across all users",
    "Name field is required (min 2 characters)",
    "Role must be selected from predefined list",
    "Email format must be valid"
  ],
  "expected_behaviors": [
    "Navigate to user list page and see existing users in a table",
    "Click 'Create User' button to open the new user form",
    "Form should show fields: Name, Email, Role",
    "Submitting empty form should show validation errors for required fields",
    "Entering duplicate email should show 'email already exists' error",
    "Filling all fields correctly and submitting should show success confirmation",
    "After creation, new user should appear in the user list",
    "Cancel button should return to user list without creating a record"
  ],
  "test_data_requirements": {
    "accounts": ["Admin user with create permissions"],
    "entities": ["Existing user with email for duplicate testing"],
    "boundary_values": ["Empty name", "Name with 256 characters", "Email without @ symbol"]
  },
  "estimated_test_cases": {
    "positive": 3,
    "negative": 4,
    "boundary": 3,
    "validation": 4,
    "total": 14
  },
  "requirement_ids": ["REQ-USR-001"],
  "source": "regression-analyzer",
  "gap_flag": false
}
```

### Canonical 20-Field Mapping

When scenarios from this skill are consumed by the `scenario-merger` or
`uat-test-case-generator`, the following field mapping applies:

| Scenario Field | Canonical 20-Field | Notes |
|---|---|---|
| `scenario_id` | `test_id` | Prefix changes from SCN- to UAT- during test generation |
| `name` | `test_name` | Direct mapping |
| -- | `feature` | Derived from `target_routes` or first `target_files` module |
| `journey_id` | `journey_id` | Direct mapping (NEW in v2.0) |
| `test_type` | `test_type` | Direct mapping |
| `coverage_area` | `coverage_area` | Direct mapping |
| `priority` | `priority` | Mapped: Critical->P1, High->P2, Medium->P3, Low->P4 |
| -- | `user_role` | Inferred from business rules or set to default role |
| `expected_behaviors` | `preconditions` + `test_steps` | Behaviors split into preconditions and steps |
| -- | `expected_result` | Derived from primary positive expected behavior |
| `test_data_requirements` | `test_data` | Mapped from structured requirements |
| -- | `business_objective` | Derived from scenario description |
| `source` | `source` | Direct mapping |
| `video_evidence.frames[0]` | `source_evidence` | Primary evidence reference |
| `requirement_ids[0]` | `requirement_id` | First requirement ID |
| `video_evidence.timestamps[0]` | `video_timestamp` | First video timestamp (NEW in v2.0) |
| `screenshot_path` | `screenshot_path` | Direct mapping (NEW in v2.0) |
| `api_endpoint` | `api_endpoint` | Primary API endpoint (NEW in v2.0) |
| `component_path` | `component_path` | Primary source component (NEW in v2.0) |

#### uat-scenarios.md

Human-readable Markdown for review by UAT testers and business stakeholders:

```markdown
# UAT Test Scenarios

Generated from: demo.mp4 + codebase analysis
Date: 2026-02-23

## Summary

| Priority | Count | Description |
|----------|-------|-------------|
| Critical | 1 | Core authentication flow |
| High | 3 | User management, order processing |
| Medium | 2 | Settings, notifications |
| Low | 1 | Help pages |

Total estimated test cases: 68

---

## SCN-AUTH-001: User Authentication Flow

**Priority**: Critical
**Test Type**: End-to-End
**Coverage Area**: Business Process
**Routes**: /login, /dashboard, /logout

### Video Evidence
Frames: frame_000001.jpg — frame_000005.jpg (0:00 — 0:08)
Shows: Login page with credentials entry, redirect to dashboard

### Business Rules
- Username and password are required
- Invalid credentials show error message
- Successful login redirects to dashboard
- Session expires after 30 minutes of inactivity

### Expected Behaviors
1. Login page should display username and password fields
2. Submitting empty credentials should show validation errors
3. Entering wrong password should show "Invalid credentials" error
4. Entering valid credentials should redirect to dashboard
5. Dashboard should show user's name in the header
6. Logging out should return to login page

### Test Data Requirements
- Valid user account: testuser@example.com / ValidPass123!
- Invalid credentials for negative testing
- Locked account for lockout testing

### Estimated Test Cases: 12
- Positive: 3 | Negative: 4 | Boundary: 2 | Validation: 3

**Requirement IDs**: REQ-AUTH-001, REQ-AUTH-002

---
```

#### scenario-summary.json

Convenience file for automation and reporting:

```json
{
  "generated_at": "2026-02-23T10:30:00Z",
  "source_video": "demo.mp4",
  "source_analysis": "regression-analysis.json",
  "total_scenarios": 7,
  "by_priority": {
    "critical": 1,
    "high": 3,
    "medium": 2,
    "low": 1
  },
  "by_test_type": {
    "functional": 4,
    "end_to_end": 2,
    "business_rules": 1
  },
  "total_estimated_test_cases": 68,
  "gap_scenarios": 2,
  "total_business_rules": 24,
  "total_expected_behaviors": 85,
  "coverage": {
    "video_demonstrated_flows": 5,
    "code_only_flows": 2,
    "total_routes_covered": 12,
    "total_api_endpoints_covered": 15
  }
}
```

---

## Output Files Summary

| File | Format | Consumer | Purpose |
|---|---|---|---|
| `uat-scenarios.jsonl` | JSONL | uat-test-case-generator, uat-test-reviewer | Machine-readable scenario input |
| `uat-scenarios.md` | Markdown | UAT testers, business stakeholders | Human-readable review document |
| `scenario-summary.json` | JSON | Automation scripts, dashboards | Metrics and summary statistics |

## Scenario Coverage Requirements

Each scenario MUST include at minimum:

| Category | Minimum Expected Behaviors | Purpose |
|----------|---------------------------|---------|
| **Positive** (happy path) | 2-3 per scenario | Verify core functionality works |
| **Negative** (error handling) | 2-3 per scenario | Verify graceful error handling |
| **Boundary** (edge cases) | 1-2 per scenario | Verify limits and edge conditions |
| **Validation** (input rules) | 2-3 per form scenario | Verify input validation from code |

## Behavior Writing Quality Guidelines

- **Be specific**: `"Name field should reject empty input"` not `"Form validates inputs"`
- **Be observable**: Every behavior must describe something a tester can see or verify
- **Include both paths**: For each form, generate success AND failure behaviors
- **Reference video when available**: `"Dashboard should display chart (visible in frame_000008.jpg at 0:15)"`
- **Reference code rules**: `"Email must be unique (enforced by backend validation)"`
- **Limit per scenario**: 5-15 expected behaviors. Split if > 15
- **Consistent language**: Start with subject ("Page", "Form", "Button", "List"), then action ("should display", "should validate", "should navigate", "should show error")

## Error Handling

- **Missing regression-analysis.json**: Report error — regression-analyzer must run first
- **Empty flows list**: Generate scenarios from coverage gaps only (code-only features)
- **No business rules found**: Generate scenarios with page-level and navigation behaviors only; flag as "needs business rule review"
- **No video evidence for a flow**: Mark scenario as "Code-Analysis Only" and note absence of visual verification
- **Codebase path not provided**: Generate scenarios from regression analysis data only (no additional business rule extraction)

## Related Skills

- **regression-analyzer** — Produces the analysis files consumed by this skill
- **video-frame-extract** — Produces the frame images referenced in video evidence
- **uat-test-case-generator** — Generates detailed test cases from these scenarios
- **uat-test-reviewer** — Reviews generated test cases for coverage gaps
- **uat-test-playwright-generator** — Alternative: generates tests from live app exploration

## References

- [references/behavior-extraction-patterns.md](references/behavior-extraction-patterns.md) — Behavior template library
- [references/test-data-patterns.md](references/test-data-patterns.md) — Test data generation guidance
- [references/uat-qualification.md](references/uat-qualification.md) — UAT qualification criteria
- [references/scenario-splitting-guide.md](references/scenario-splitting-guide.md) — When and how to split large scenarios
