---
name: functional-test-reviewer
description: >
  Reviews functional test cases against qualified scenarios and all source
  artifacts (video, URL, codebase) to identify coverage gaps. Validates test
  cases conform to the 35-field schema, checks category distribution (Positive,
  Negative, Boundary, Validation, Security, Integration) per feature, verifies
  confidence inheritance, and classifies gaps by severity (Critical, High,
  Medium, Low). Outputs a coverage report with per-feature percentages and a
  gaps JSONL file for gap-fill regeneration. Use when reviewing functional
  test output for completeness before final delivery, or as part of the
  iterative review loop managed by functional-review-loop-controller.
license: MIT
compatibility: >
  Consumes functional-tests.jsonl from functional-test-generator and
  qualified-scenarios.jsonl from functional-qualification-gate. Outputs
  coverage-report.json and gaps.jsonl for the review loop controller.
metadata:
  author: functional-test-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
---

# Functional Test Reviewer

## Purpose

Review generated functional test cases for coverage completeness, schema
conformance, and category distribution. Compare tests against qualified
scenarios and all available source artifacts to identify gaps. Classify gaps
by severity to drive iterative gap-fill regeneration.

> **Key Principle**: Every qualified scenario should have adequate test coverage
> across applicable categories. The reviewer ensures no critical function goes
> untested, no category is systematically missing, and the 35-field schema is
> fully populated for all tests.

## When to Use This Skill

- After functional-test-generator has produced `functional-tests.jsonl`
- As part of the review loop managed by `functional-review-loop-controller`
- When auditing existing functional test suites for completeness
- When checking that generated tests cover all qualified scenarios

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `generated_tests_path` | Yes | -- | Path to `functional-tests.jsonl` (35-field schema) |
| `qualified_scenarios_path` | Yes | -- | Path to `qualified-scenarios.jsonl` from qualification gate |
| `feature_map_path` | No | -- | Path to `feature-map.json` from scenario merger |
| `codebase_path` | No | -- | Application codebase path (for deeper gap analysis) |
| `output_dir` | Yes | -- | Output directory for review artifacts |
| `severity_filter` | No | `all` | Minimum severity to include in gaps output: `all`, `critical`, `high` |

## Outputs

| File | Format | Description |
|---|---|---|
| `coverage-report.json` | JSON | Coverage analysis: per-feature %, per-category %, gap summary |
| `gaps.jsonl` | JSONL | Each uncovered scenario/category as a gap record for regeneration |

---

## 5-Phase Review Workflow

### Phase 1: Ingest & Parse Test Cases

1. **Load `functional-tests.jsonl`**: Parse all generated test cases.
2. **Load `qualified-scenarios.jsonl`**: Parse all qualified scenarios as the
   coverage baseline.
3. **Load `feature-map.json`** (if provided): Use for feature-level context.
4. **Build lookup indexes**:
   - Tests grouped by `feature` + `module`
   - Tests grouped by `test_category`
   - Scenarios grouped by `merged_id`
5. **Count totals**: Total tests, total scenarios, per-feature counts.

### Phase 2: Schema Validation

Validate every test case against the 35-field schema:

| Field Group | Required Fields | Validation |
|---|---|---|
| Core Identification | `test_id`, `test_name`, `feature`, `module` | Non-empty, valid ID format `FT-{MOD}-{SEQ}` |
| Classification | `test_category`, `priority`, `user_role` | Category in {Positive, Negative, Boundary, Validation, Security, Integration} |
| Test Content | `preconditions`, `test_steps`, `expected_result` | Non-empty, test_steps has step_number + action + expected |
| Traceability | `source`, `confidence` | Source in {merged, video, url, codebase}, confidence 0.0-1.0 |
| Execution Tracking | `status` | Defaults to "Not Executed" |

**Schema violations** are logged but do not block the review. They appear in
the coverage report under `schema_issues`.

### Phase 3: Coverage Analysis

For each qualified scenario, check whether adequate test coverage exists:

#### 3a: Scenario-Level Coverage

For each scenario in `qualified-scenarios.jsonl`:
1. Find matching test cases by `feature` + `module` + action similarity
2. Check if at least one test case covers the scenario's primary action
3. If no match found: **gap** with severity based on scenario priority

| Scenario Priority | Gap Severity |
|---|---|
| P1 | Critical |
| P2 | High |
| P3 | Medium |
| P4 | Low |

#### 3b: Category Coverage per Feature

For each feature, check the category distribution:

| Category | Minimum Expected | Gap Severity if Missing |
|---|---|---|
| **Positive** | >= 1 per CRUD action in feature | Critical (no happy path) |
| **Negative** | >= 1 per required field | High (no error handling) |
| **Boundary** | >= 1 if feature has numeric/length constraints | Medium |
| **Validation** | >= 1 per validation rule in scenario | High (no input validation) |
| **Security** | >= 1 if feature has text inputs or auth | Critical (no security tests) |
| **Integration** | >= 1 if feature has cross-module references | Medium |

#### 3c: Confidence Verification

Verify that test case `confidence` is properly inherited from parent scenario:
- Test confidence should be <= scenario confidence
- Tests from inferred data should be -0.05 from scenario confidence
- Flag any test with confidence > its parent scenario as anomalous

#### 3d: Priority Distribution Check

Verify reasonable priority distribution:

| Check | Warning Threshold |
|---|---|
| No P1 tests for a feature with P1 scenarios | Critical gap |
| All tests are P3/P4 for a feature with P1/P2 scenarios | High gap |
| > 80% of tests are one priority level | Warning (skewed distribution) |

### Phase 4: Gap Classification

For each identified gap, produce a structured gap record:

```json
{
  "gap_id": "GAP-VEH-001",
  "feature": "Vehicle Management",
  "module": "Vehicles",
  "gap_type": "missing_scenario",
  "severity": "Critical",
  "description": "No test cases cover vehicle deletion flow",
  "missing_categories": ["Positive", "Negative"],
  "source_scenario_id": "MRG-VEH-005",
  "source_scenario_action": "Delete vehicle",
  "discovered_fields": ["vehicle_id"],
  "discovered_endpoints": [{"endpoint": "/api/vehicles/:id", "method": "DELETE"}],
  "confidence": 0.88,
  "priority": "P1",
  "reason": "P1 scenario with 3-source confirmation has zero test coverage"
}
```

**Gap types**:

| Gap Type | Description |
|---|---|
| `missing_scenario` | Qualified scenario has no matching test cases at all |
| `missing_category` | Feature has tests but missing a critical category |
| `missing_priority` | Feature has no tests at the expected priority level |
| `schema_violation` | Test cases have missing/invalid fields |
| `low_coverage` | Feature has tests but fewer than minimum thresholds |

### Phase 5: Produce Coverage Report

#### coverage-report.json

```jsonc
{
  "status": "INCOMPLETE",
  "generated_at": "2026-02-25T14:30:00Z",
  "overall_coverage": 82,
  "total_tests": 156,
  "total_qualified_scenarios": 42,
  "scenarios_covered": 35,
  "scenarios_uncovered": 7,
  "schema_issues": 2,
  "per_feature_coverage": [
    {
      "feature": "Vehicle Management",
      "module": "Vehicles",
      "coverage": 100,
      "test_count": 32,
      "scenario_count": 8,
      "scenarios_covered": 8,
      "gap_count": 0,
      "categories": {
        "Positive": 8,
        "Negative": 7,
        "Boundary": 5,
        "Validation": 5,
        "Security": 4,
        "Integration": 3
      }
    },
    {
      "feature": "Booking System",
      "module": "Bookings",
      "coverage": 71,
      "test_count": 20,
      "scenario_count": 7,
      "scenarios_covered": 5,
      "gap_count": 3,
      "categories": {
        "Positive": 6,
        "Negative": 5,
        "Boundary": 3,
        "Validation": 4,
        "Security": 0,
        "Integration": 2
      },
      "category_gaps": ["Security"]
    }
  ],
  "per_category_coverage": {
    "Positive": {"count": 42, "features_covered": 8, "features_total": 8},
    "Negative": {"count": 38, "features_covered": 8, "features_total": 8},
    "Boundary": {"count": 24, "features_covered": 7, "features_total": 8},
    "Validation": {"count": 22, "features_covered": 7, "features_total": 8},
    "Security": {"count": 18, "features_covered": 6, "features_total": 8},
    "Integration": {"count": 12, "features_covered": 5, "features_total": 8}
  },
  "gap_summary": {
    "critical": 2,
    "high": 3,
    "medium": 4,
    "low": 1,
    "total": 10
  },
  "priority_distribution": {
    "P1": 48,
    "P2": 56,
    "P3": 40,
    "P4": 12
  },
  "confidence_distribution": {
    "high_0.9_1.0": 52,
    "medium_0.7_0.89": 68,
    "low_0.3_0.69": 36
  }
}
```

#### gaps.jsonl

One line per gap, formatted as a scenario candidate that can be directly
consumed by `functional-test-generator` for gap-fill regeneration:

```json
{
  "gap_id": "GAP-BOOK-001",
  "feature": "Booking System",
  "module": "Bookings",
  "gap_type": "missing_category",
  "severity": "Critical",
  "description": "No Security tests for Booking System — has text inputs and payment flow",
  "missing_categories": ["Security"],
  "merged_id": "MRG-BOOK-003",
  "action": "Submit booking with payment",
  "discovered_fields": ["customer_name", "booking_date", "payment_amount", "card_number"],
  "discovered_endpoints": [{"endpoint": "/api/bookings", "method": "POST"}],
  "discovered_validations": [
    {"field": "payment_amount", "rule": "required, min:0.01", "source": "codebase"}
  ],
  "confidence": 0.92,
  "priority": "P1",
  "reason": "Feature with payment flow has zero security test coverage"
}
```

---

## Coverage Calculation

**Overall coverage** = (scenarios_covered / total_qualified_scenarios) * 100

**Per-feature coverage** = (scenarios_covered_in_feature / scenarios_in_feature) * 100

A scenario is "covered" when:
1. At least one test case matches its feature + action, AND
2. The matching test(s) include at least Positive category, AND
3. If the scenario has validation rules, at least one Validation test exists

---

## Constraints

1. **Read-only**: Never modify the input test cases or scenarios files.
2. **Deterministic**: Same inputs always produce the same coverage report.
3. **Incremental-friendly**: Output gaps in a format directly consumable by
   `functional-test-generator` for gap-fill without re-running the full pipeline.
4. **Existing tests preserved**: When used in review loop, existing tests
   are never removed or modified — only new gap-fill tests are added.
5. **Schema-tolerant**: Missing fields in test cases are flagged as schema
   issues but don't prevent coverage analysis.

## Error Handling

| Issue | Resolution |
|---|---|
| Test cases file not found | Report error — functional-test-generator must run first |
| Qualified scenarios file not found | Report error — qualification gate must run first |
| Empty test cases file | Output report with 0% coverage, all scenarios as gaps |
| Malformed JSONL line | Skip line, log warning, continue |
| No feature map provided | Derive feature list from test cases and scenarios only |

## Related Skills

| Skill | Relationship |
|---|---|
| **functional-test-generator** | Upstream — produces functional-tests.jsonl for review |
| **functional-qualification-gate** | Upstream — produces qualified-scenarios.jsonl baseline |
| **functional-scenario-merger** | Upstream — produces feature-map.json |
| **excel-workbook-generator** | Downstream — consumes gap-fill tests for workbook update |
| **functional-review-loop-controller** | Controller — invokes this skill iteratively |
