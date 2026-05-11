---
name: functional-qualification-gate
description: >
  Applies a 6-criteria Functional Test Qualification Gate to merged scenario
  candidates, filtering and transforming them into qualified functional test
  scenarios. Evaluates each scenario for testable input/output, determinism,
  appropriate scope, observable expected results, specific function coverage,
  and appropriate technical detail. Assigns priorities using weighted scoring
  across source confidence, technical completeness, business criticality, and
  risk factors. Applies complexity tier filtering (quick/standard/comprehensive).
  Filters out scenarios below confidence thresholds and flags vague or
  infrastructure-level scenarios for removal. Use when qualifying merged
  scenarios from functional-scenario-merger before functional test case
  generation.
license: MIT
compatibility: >
  Consumes merged-scenarios.jsonl from functional-scenario-merger skill.
  Outputs JSONL compatible with functional-test-generator.
metadata:
  author: functional-test-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
---

# Functional Qualification Gate

## Purpose

Apply the 6-criteria Functional Test Qualification Gate to merged scenario
candidates, filtering and transforming them into qualified functional test
scenarios ready for test case generation.

> **Key Principle**: Not every discovered scenario belongs in a functional test
> suite. This gate ensures only testable, well-scoped, technically grounded
> scenarios proceed to test generation. Unlike the UAT gate (which filters OUT
> technical detail), the functional gate validates that scenarios HAVE sufficient
> technical detail for deterministic, repeatable test cases.

## When to Use This Skill

- Qualifying merged scenarios from `functional-scenario-merger` before
  functional test generation
- Filtering scenario candidates by functional testability
- Assigning priorities based on multi-factor weighted analysis
- Applying complexity tier filtering (quick/standard/comprehensive)
- Removing vague, infrastructure-level, or untestable scenarios
- Enforcing confidence thresholds from source confirmation

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `scenarios_path` | Yes | -- | Path to `merged-scenarios.jsonl` from functional-scenario-merger |
| `complexity_tier` | Yes | `standard` | `quick` (P1), `standard` (P1+P2), `comprehensive` (P1-P4) |
| `output_dir` | Yes | `functional-tests/` | Output directory |
| `confidence_threshold` | No | `0.20` | Minimum confidence to pass gate (scenarios below are removed) |

## Outputs

| File | Format | Description |
|---|---|---|
| `qualified-scenarios.jsonl` | JSONL | Scenarios that pass the functional gate |
| `qualification-report.json` | JSON | Per-scenario gate results and statistics |

---

## The 6-Criteria Functional Test Qualification Gate

Every scenario candidate is evaluated against ALL 6 criteria:

| # | Criterion | Question | Pass Example | Fail Example |
|---|---|---|---|---|
| 1 | **Has testable input/output** | Does the scenario define concrete inputs that produce verifiable outputs? | "Submit form with Name='Test', Type='Heavy' -> vehicle created with status 201" | "The system should work properly" |
| 2 | **Is deterministic** | Will the same inputs always produce the same outputs? | "Search vehicles by plate 'AB1234' -> returns matching vehicle" | "System generates a random report" (no fixed expected output) |
| 3 | **Appropriately scoped** | Is it a functional test (not unit-level or integration/E2E)? | "Create vehicle with valid data -> success response" | "React useState hook updates correctly" (unit) or "Full user journey from login to checkout" (E2E) |
| 4 | **Has observable expected result** | Can the outcome be verified without inspecting source code? | "Error message 'Name is required' displayed" | "Internal state variable set to true" |
| 5 | **Covers a specific function/behavior** | Does it test exactly one function or behavior? | "Delete vehicle by ID -> vehicle removed from list" | "Test the entire Vehicle Management module" (too broad) |
| 6 | **Appropriate technical detail** | Does it include sufficient technical context (fields, endpoints, validations) without being infrastructure-level? | "POST /api/vehicles with body {name, type} -> 201 Created" | "Deploy container to K8s and verify pod status" (infrastructure) |

---

## Keyword Detection

### Out-of-Scope Keywords (Flag for Removal)

Scenarios containing these keywords are likely NOT functional tests:

| Category | Keywords |
|---|---|
| **Infrastructure** | deploy, container, docker, kubernetes, k8s, CI/CD, pipeline, terraform, helm |
| **Monitoring/Ops** | logs, monitor, alert, metric, dashboard-ops, uptime, health-check endpoint |
| **Build/Compile** | build, compile, bundle, webpack, transpile, minify |
| **Environment** | staging, production, environment variable, config file, secrets |
| **Performance** | load test, stress test, throughput, latency benchmark, concurrent users |

These scenarios should be **removed** (not rewritten) — they belong in different
test suites (infrastructure, performance, ops).

### Vagueness Keywords (Flag for Rewrite)

Scenarios containing these patterns are too vague for functional testing:

| Pattern | Example | Issue |
|---|---|---|
| "should work" / "works correctly" | "Login should work correctly" | No specific expected result |
| "properly" / "appropriate" | "System handles errors properly" | No specific error behavior defined |
| "various" / "different" | "Test with various inputs" | No specific inputs defined |
| "etc." / "and so on" | "Validate name, email, etc." | Incomplete field list |
| No action verb | "Vehicle Management page" | Describes a page, not a testable action |
| No expected result | "User clicks submit button" | Missing what should happen |

These scenarios should be **rewritten** to add specificity before proceeding.

### Technical Detail Keywords (Expected and Valid)

Unlike the UAT gate, these keywords are EXPECTED in functional test scenarios:

| Category | Valid Keywords |
|---|---|
| **API** | endpoint, GET, POST, PUT, DELETE, PATCH, status code, request, response, payload |
| **Validation** | required, maxlength, minlength, pattern, regex, enum, format |
| **Data** | field, column, entity, model, record, row |
| **HTTP** | 200, 201, 400, 401, 403, 404, 422, 500, header, content-type |
| **UI** | form, input, button, dropdown, checkbox, modal, toast, table, pagination |

Presence of these keywords is a **positive signal** for functional tests.

---

## 4-Step Qualification Process

### Step 1: Confidence Threshold Filter

Before evaluating criteria, apply the confidence floor:

| Confidence | Action |
|---|---|
| >= `confidence_threshold` (default 0.20) | Proceed to criteria evaluation |
| < `confidence_threshold` | **Remove** — insufficient evidence from any source |

**Rationale**: Scenarios with extremely low confidence (e.g., a single vague
mention in a video frame) are not worth generating functional tests for.

### Step 2: Evaluate Each Scenario Against 6 Criteria

For each scenario that passes the confidence filter:

```jsonc
{
  "merged_id": "MRG-VEH-001",
  "scenario_name": "Create vehicle with valid data",
  "criteria_results": {
    "testable_io": {
      "pass": true,
      "note": "Has discovered_fields [name, type, plate] and endpoint POST /api/vehicles"
    },
    "deterministic": {
      "pass": true,
      "note": "Fixed inputs produce predictable 201 response"
    },
    "appropriate_scope": {
      "pass": true,
      "note": "Tests single CRUD operation, not unit or E2E"
    },
    "observable_result": {
      "pass": true,
      "note": "Success message visible, vehicle appears in list"
    },
    "specific_function": {
      "pass": true,
      "note": "Tests vehicle creation specifically"
    },
    "appropriate_detail": {
      "pass": true,
      "note": "Has API endpoint, fields, and validations — no infrastructure concerns"
    }
  },
  "criteria_passed": 6,
  "criteria_failed": 0,
  "qualification": "QUALIFIED"
}
```

**Automated evaluation signals** (use these to assess criteria programmatically):

| Criterion | Pass Signals | Fail Signals |
|---|---|---|
| testable_io | Has `discovered_fields` OR `discovered_endpoints` | Both empty |
| deterministic | Has explicit `action` with `expected_result` | Contains "random", "dynamic", "varies" |
| appropriate_scope | Single feature + single action | Multiple features OR no specific action |
| observable_result | Has `expected_result` with observable outcome | Expected result references internal state |
| specific_function | Clear CRUD verb or specific behavior | Describes entire module or page |
| appropriate_detail | Has at least one of: fields, endpoint, validation rule | Only has feature name (no technical context) |

### Step 3: Transform Failing Scenarios

| Criteria Failed | Action | Example |
|---|---|---|
| **1-2 criteria** (close) | **Enrich** — add missing technical detail from merged data | Missing endpoint -> infer from `discovered_endpoints` |
| **3-4 criteria** | **Downgrade** to P4 priority | Vague scenario kept but lowest priority |
| **5-6 criteria** | **Remove** | Untestable, infrastructure-level, or completely vague |

**Enrichment rules** (for 1-2 criteria failures):
- Missing testable I/O -> add from `discovered_fields` and `discovered_endpoints`
- Missing expected result -> derive from action verb (Create -> "created successfully",
  Delete -> "removed from list", Update -> "changes saved")
- Too broad scope -> split into individual CRUD actions if possible
- Missing technical detail -> add from `discovered_validations` and `discovered_endpoints`

### Step 4: Assign Priorities via Weighted Scoring

Priority is determined by weighted factors:

| Factor | Weight | P1 Signal | P4 Signal |
|---|---|---|---|
| **Source confidence** | 0.25 | Confidence >= 0.9 (3-source confirmed) | Confidence < 0.5 (single source, weak) |
| **Technical completeness** | 0.25 | Has fields + endpoint + validations | Only has feature name |
| **Business criticality** | 0.30 | Auth, payment, core CRUD, data integrity | Settings, help, about, cosmetic |
| **Risk/complexity** | 0.20 | Complex validation logic, multi-step workflow | Simple read-only page |

**Priority assignment**:

| Priority | Criteria |
|---|---|
| **P1 (Critical)** | Weighted score >= 0.8 OR security-related (auth, injection) OR core CRUD with full technical detail |
| **P2 (High)** | Weighted score >= 0.6 OR multi-source confirmed with good technical detail |
| **P3 (Medium)** | Weighted score >= 0.4 OR secondary features with some technical detail |
| **P4 (Low)** | Weighted score < 0.4 OR single-source with low completeness OR downgraded scenarios |

**Business criticality mapping** (same as functional domain):

| Criticality | Features |
|---|---|
| Critical | Authentication, authorization, payment, checkout, core entity CRUD, data validation |
| High | Search, filtering, reporting, user management, notifications, file upload |
| Medium | Settings, preferences, profile, dashboard widgets, export |
| Low | Help pages, about, tooltips, animations, footer links, cosmetic |

**Technical completeness scoring**:

| Evidence Present | Score Contribution |
|---|---|
| Has `discovered_fields` with 3+ fields | +0.3 |
| Has `discovered_endpoints` with method | +0.3 |
| Has `discovered_validations` | +0.2 |
| Has `screenshot_ref` or `video_timestamp` | +0.1 |
| Has `component_path` | +0.1 |

---

## Complexity Tier Filtering

After priority assignment, filter by the user's chosen complexity tier:

| Tier | Priority Filter | Typical Result |
|---|---|---|
| **Quick** | P1 only | 5-15 scenarios (critical functions) |
| **Standard** | P1 + P2 | 15-40 scenarios (critical + important) |
| **Comprehensive** | P1 + P2 + P3 + P4 | 40-80 scenarios (full coverage) |

---

## Output Format

### qualified-scenarios.jsonl

Each qualified scenario retains the merged-scenario format with added
qualification metadata:

```json
{
  "merged_id": "MRG-VEH-001",
  "feature": "Vehicle Management",
  "module": "Vehicles",
  "action": "Create new vehicle",
  "description": "User fills out vehicle creation form and submits",
  "source": "merged",
  "sources_found": ["video", "url", "codebase"],
  "confirmation_count": 3,
  "confidence": 0.95,
  "discovered_fields": ["name", "type", "plate_number", "registration_date", "status"],
  "field_sources": {
    "name": ["video", "url", "codebase"],
    "type": ["video", "url", "codebase"],
    "plate_number": ["url", "codebase"],
    "registration_date": ["codebase"],
    "status": ["url"]
  },
  "discovered_endpoints": [
    {"endpoint": "/api/vehicles", "method": "POST", "source": "codebase"}
  ],
  "discovered_validations": [
    {"field": "name", "rule": "required, max:100", "source": "codebase"},
    {"field": "plate_number", "rule": "required, pattern:[A-Z]{2}[0-9]{4}", "source": "url"}
  ],
  "video_timestamp": "01:23",
  "screenshot_ref": "screenshots/vehicles-new.png",
  "component_path": "src/pages/vehicles/CreateVehicle.tsx",
  "conflict_flag": false,
  "conflict_details": "",

  "qualification": "QUALIFIED",
  "criteria_passed": 6,
  "priority": "P1",
  "priority_score": 0.92,
  "technical_completeness": 0.9,
  "enriched": false
}
```

### qualification-report.json

```jsonc
{
  "generated_at": "2026-02-25T10:30:00Z",
  "complexity_tier": "standard",
  "confidence_threshold": 0.20,
  "input_scenarios": 42,
  "confidence_filtered": 1,
  "qualification_results": {
    "qualified": 32,
    "enriched": 5,
    "downgraded_to_p4": 2,
    "removed": 2,
    "confidence_rejected": 1
  },
  "after_tier_filter": {
    "tier": "standard",
    "p1_count": 12,
    "p2_count": 18,
    "p3_filtered_out": 5,
    "p4_filtered_out": 2,
    "total_output": 30
  },
  "priority_distribution": {
    "P1": 12,
    "P2": 18,
    "P3": 5,
    "P4": 2
  },
  "technical_completeness_avg": 0.74,
  "confidence_avg": 0.81,
  "per_scenario": [
    {
      "merged_id": "MRG-VEH-001",
      "scenario_name": "Create vehicle with valid data",
      "criteria_passed": 6,
      "qualification": "QUALIFIED",
      "priority": "P1",
      "priority_score": 0.92,
      "included_in_output": true
    }
  ],
  "removed_scenarios": [
    {
      "merged_id": "MRG-INFRA-001",
      "scenario_name": "Deploy application to staging environment",
      "criteria_passed": 1,
      "reason": "Infrastructure scenario — fails 5 of 6 functional criteria"
    }
  ],
  "enriched_scenarios": [
    {
      "merged_id": "MRG-SET-003",
      "scenario_name": "Update notification preferences",
      "original_criteria_passed": 4,
      "enrichments_applied": ["Added expected result from action verb", "Added endpoint from discovered_endpoints"],
      "final_criteria_passed": 6
    }
  ]
}
```

---

## Comparison with UAT Qualification Gate

| Aspect | UAT Gate | Functional Gate |
|---|---|---|
| **Philosophy** | "Is this a business-user test?" | "Is this a testable function?" |
| **Technical keywords** | Flagged as NON-UAT (remove) | EXPECTED and VALID |
| **Business language** | Required | Helpful but not required |
| **API/endpoint detail** | Stripped or rewritten | Required for full score |
| **Validation rules** | Abstracted to user terms | Preserved with technical specifics |
| **Field-level detail** | Summarized | Fully enumerated |
| **Confidence threshold** | No explicit floor | Applies minimum confidence filter |
| **Priority weighting** | Confirmation (0.3), Criticality (0.3), Frequency (0.2), Risk (0.2) | Confidence (0.25), Completeness (0.25), Criticality (0.30), Risk (0.20) |

---

## Error Handling

| Issue | Resolution |
|---|---|
| Scenarios file not found | Report error — functional-scenario-merger must run first |
| Invalid JSONL format | Skip invalid lines, log warning, continue |
| All scenarios fail gate | Output empty JSONL, report warning, suggest reviewing upstream inputs |
| All scenarios below confidence threshold | Output empty JSONL, report warning with threshold info |
| Unknown complexity tier | Default to `standard` with warning |

## Related Skills

| Skill | Relationship |
|---|---|
| **functional-scenario-merger** | Upstream — produces merged scenarios consumed by this skill |
| **functional-test-generator** | Downstream — generates test cases from qualified scenarios |
| **functional-test-reviewer** | Downstream — reviews generated tests for coverage against qualified scenarios |
| **functional-test-orchestrator** | Orchestrator — invokes this skill after merge checkpoint |
