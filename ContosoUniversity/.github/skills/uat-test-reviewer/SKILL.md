---
name: uat-test-reviewer
description: >
  Reviews UAT test cases for both coverage completeness AND UAT alignment
  quality. Validates that generated tests are true end-to-end business workflow
  tests — not functional tests with UAT naming. Applies a dual-axis review:
  (1) Coverage — are all qualified scenarios represented in the test suite?
  (2) Alignment — does each test case conform to UAT standards (end-to-end
  scope, workflow granularity, business language, goal-oriented pass criteria)?
  Detects functional-test contamination patterns (single-action tests,
  element-level verification, data count assertions, UI mechanism tests) and
  flags them for consolidation or removal. Outputs coverage-report.json with
  alignment scores and gaps.jsonl for gap-fill regeneration. Use when reviewing
  UAT test output before final delivery, or as part of the iterative review
  loop managed by review-loop-controller.
license: MIT
compatibility: >
  Consumes test-cases.jsonl from uat-test-case-generator (20-field schema) and
  unified-scenarios.jsonl from uat-qualification-gate. Outputs coverage-report
  and gaps JSONL compatible with the review loop controller.
metadata:
  author: uat-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
---

# UAT Test Reviewer

## Purpose

Review generated UAT test cases across two dimensions:

1. **Coverage**: Are all qualified scenarios and business requirements tested?
2. **Alignment**: Is each test case a true UAT test — end-to-end, workflow-
   scoped, business-language, goal-oriented — or has functional-test thinking
   leaked into the output?

> **Key Principle**: A UAT suite can achieve 100% scenario coverage while being
> entirely composed of functional-level checks. Coverage alone is insufficient.
> This reviewer catches the alignment problem that coverage metrics miss.

## When to Use This Skill

- After `uat-test-case-generator` has produced `test-cases.jsonl`
- As part of the review loop managed by `review-loop-controller`
- When auditing existing UAT test suites for quality
- When checking for functional-test contamination in UAT deliverables

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `generated_tests_path` | Yes | -- | Path to `test-cases.jsonl` (20-field schema) or Excel workbook |
| `qualified_scenarios_path` | Yes | -- | Path to `unified-scenarios.jsonl` from qualification gate |
| `business_requirements` | No | -- | Business requirements or acceptance criteria document |
| `feature_map_path` | No | -- | Path to unified feature map from all sources |
| `codebase_path` | No | -- | Application codebase path (for deeper gap analysis) |
| `output_dir` | Yes | -- | Output directory for review artifacts |

## Outputs

| File | Format | Description |
|---|---|---|
| `coverage-report.json` | JSON | Coverage + alignment analysis with per-test scores |
| `gaps.jsonl` | JSONL | Coverage gaps and alignment failures for regeneration |

---

## Dual-Axis Review: Coverage + Alignment

### Axis 1: Coverage Review

Standard coverage review — are all scenarios tested?

For each qualified scenario in `unified-scenarios.jsonl`:
1. Find matching test cases by `journey_id` + `feature` + action similarity
2. Check if at least one test case covers the scenario's workflow
3. If no match: **coverage gap** with severity based on scenario priority

| Scenario Priority | Gap Severity |
|---|---|
| P1 | Critical |
| P2 | High |
| P3 | Medium |
| P4 | Low |

When `business_requirements` are provided:
- Cross-reference each stated requirement against test coverage
- Any uncovered business requirement is a **Critical** gap regardless of
  scenario priority — business requirements are the primary UAT benchmark

### Axis 2: Alignment Review

**This is what distinguishes the UAT reviewer from the functional reviewer.**

For each generated test case, evaluate a 4-dimension alignment score:

| Dimension | Weight | Score 0 (Failing) | Score 1 (Passing) |
|---|---|---|---|
| **Scope** | 0.30 | Test stays within one feature | Test spans 2+ features in end-to-end workflow |
| **Granularity** | 0.30 | Steps describe individual UI clicks | Steps describe user-meaningful milestones |
| **Language** | 0.20 | Uses QA verbs: "verify", "confirm", "validate" | Uses business verbs: "accomplish", "achieve", "complete" |
| **Pass criteria** | 0.20 | Expected result describes UI state ("popup displayed") | Expected result describes goal achievement ("user can select appropriate skills") |

**Alignment score** = weighted sum of 4 dimensions (0.0 to 1.0)

| Alignment Score | Classification | Action |
|---|---|---|
| >= 0.8 | **Aligned** | No action needed |
| 0.6 - 0.79 | **Borderline** | Flag for rewrite — suggest specific improvements |
| < 0.6 | **Misaligned** | Flag as functional-test contamination — regenerate |

---

## Functional-Test Contamination Detection

The reviewer scans every test case for these specific contamination patterns:

### Pattern 1: Single-Action Tests

**Detection**: Test has only 1-2 steps AND each step describes one UI action.

| Indicator | Example |
|---|---|
| Step count = 1 | "Navigate to the Cards tab" |
| Step count = 2, both are click+verify | "Click info button" → "Verify popup opens" |
| test_name starts with "User navigates..." or "User opens..." | Single-action framing |

**Severity**: High — this is the most common contamination pattern.

### Pattern 2: Element-Level Verification

**Detection**: Expected result or test_steps reference specific UI elements.

| Indicator | Trigger Words in expected_result or steps |
|---|---|
| UI element names | "popup", "modal", "tab", "button", "section", "panel" |
| Display verbs | "displayed", "visible", "rendered", "shown", "appears" |
| Element attributes | "populated", "filled", "contains text", "has content" |

**Severity**: High — verifying UI element presence is functional testing.

### Pattern 3: Data Count Assertions

**Detection**: Expected result or steps contain numeric quantity checks.

| Indicator | Example |
|---|---|
| Approximate counts | "approximately 250 skills" |
| Exact counts | "shows 8 SDLC phases", "Planning shows 2 skills" |
| Completeness checks | "all phases are listed", "no phases are missing" |

**Severity**: Medium — data completeness belongs in functional/integration tests.

### Pattern 4: UI Mechanism Tests

**Detection**: Test verifies how the UI behaves rather than what the user achieves.

| Indicator | Example |
|---|---|
| Dynamic behavior | "results update dynamically as user types" |
| Scroll behavior | "scrolling reveals more cards" |
| Animation/transition | "tab switching is smooth" |
| State mechanism | "active tab indicator changes" |

**Severity**: Medium — UI behavior testing is functional, not UAT.

### Pattern 5: Isolated Negative Tests

**Detection**: Test focuses entirely on an error condition without a broader
workflow context.

| Indicator | Example |
|---|---|
| "non-existent" in name | "User searches for non-existent skill" |
| Error as sole focus | "User sees error message for invalid input" |
| Reset/clear as sole focus | "User clears search to return to full catalog" |

**Severity**: Low — if relevant, should be one step in a broader workflow.

### Pattern 6: Wrong Classification Fields

**Detection**: Schema fields set to functional values.

| Field | Contaminated Value | Correct UAT Value |
|---|---|---|
| `test_type` | "Functional", "Negative", "Boundary", "Security" | "Acceptance" |
| `coverage_area` | "Module", "UI", "Data" | "BusinessProcess" |

**Severity**: High — schema-level contamination signals systemic issues.

---

## 5-Phase Review Workflow

### Phase 1: Ingest & Parse

1. **Load test cases** from JSONL or Excel.
2. **Load qualified scenarios** as coverage baseline.
3. **Load business requirements** (if provided) as primary benchmark.
4. **Build indexes**: Tests by journey, by feature, by coverage_area.

### Phase 2: Coverage Analysis

For each qualified scenario:
1. Find matching test cases by journey + feature + action similarity.
2. Mark as covered or uncovered.
3. For uncovered scenarios, create coverage gap records.

When business requirements are provided:
1. Map each requirement to test cases.
2. Flag uncovered requirements as Critical gaps.

### Phase 3: Alignment Analysis

For each test case:
1. Score across 4 alignment dimensions (scope, granularity, language, criteria).
2. Calculate weighted alignment score.
3. Classify as Aligned / Borderline / Misaligned.
4. Run contamination pattern detection (all 6 patterns).
5. Record specific contamination patterns found.

### Phase 4: Gap & Issue Classification

Produce gap records for both coverage gaps and alignment failures:

**Coverage gap** (scenario not tested):
```json
{
  "gap_id": "GAP-COV-001",
  "gap_type": "missing_coverage",
  "severity": "Critical",
  "feature": "Skill Discovery",
  "journey_id": "J-CARDS-BROWSE",
  "description": "No test covers the skill discovery workflow",
  "source_scenario_id": "UAT-DISC-001",
  "priority": "P1"
}
```

**Alignment failure** (test exists but is not true UAT):
```json
{
  "gap_id": "GAP-ALN-001",
  "gap_type": "alignment_failure",
  "severity": "High",
  "test_id": "UAT-INFO-001",
  "test_name": "User opens skill detail popup using the info button",
  "alignment_score": 0.35,
  "contamination_patterns": ["single_action", "element_verification"],
  "recommendation": "Merge into broader skill evaluation workflow test",
  "suggested_merge_target": "UAT-DISC-001"
}
```

### Phase 5: Produce Coverage + Alignment Report

```jsonc
{
  "status": "INCOMPLETE",
  "generated_at": "2026-02-26T10:00:00Z",

  // --- Coverage metrics ---
  "overall_coverage": 85,
  "total_tests": 37,
  "total_qualified_scenarios": 20,
  "scenarios_covered": 17,
  "scenarios_uncovered": 3,
  "business_requirements_covered": 8,
  "business_requirements_uncovered": 2,

  // --- Alignment metrics (NEW — distinguishes UAT from functional reviewer) ---
  "alignment": {
    "avg_alignment_score": 0.52,
    "aligned_count": 4,
    "borderline_count": 8,
    "misaligned_count": 25,
    "alignment_rate": "10.8%",
    "contamination_summary": {
      "single_action_tests": 15,
      "element_verification_tests": 6,
      "data_count_assertions": 4,
      "ui_mechanism_tests": 3,
      "isolated_negative_tests": 2,
      "wrong_classification": 20
    }
  },

  "per_journey_coverage": [
    {
      "journey_id": "J-CARDS-BROWSE",
      "coverage": 100,
      "test_count": 8,
      "avg_alignment_score": 0.45,
      "misaligned_tests": 6
    }
  ],

  "gap_summary": {
    "coverage_gaps": { "critical": 1, "high": 2, "medium": 0, "total": 3 },
    "alignment_failures": { "high": 20, "medium": 5, "total": 25 }
  },

  "top_recommendations": [
    "Consolidate 33 single-action tests into 8-12 end-to-end workflow tests",
    "Replace all test_type='Functional' with 'Acceptance'",
    "Replace all coverage_area='Module'/'UI' with 'BusinessProcess'",
    "Rewrite expected results to describe user goal achievement, not UI state"
  ]
}
```

---

## Coverage Calculation

**Overall coverage** = (scenarios_covered / total_qualified_scenarios) * 100

**Alignment rate** = (aligned_count / total_tests) * 100

A healthy UAT suite should have:
- Coverage >= 90%
- Alignment rate >= 80%
- Zero misaligned tests (alignment score < 0.6)
- Zero wrong-classification tests (test_type or coverage_area contaminated)

---

## Constraints

1. **Read-only**: Never modify the input test cases or scenarios files.
2. **Dual-axis mandatory**: Always evaluate BOTH coverage AND alignment.
   A 100% coverage report with 10% alignment is a failing review.
3. **Alignment failures are gaps**: Misaligned tests are included in
   `gaps.jsonl` alongside coverage gaps — they need regeneration.
4. **Business requirements first**: When provided, business requirements
   are the primary coverage benchmark, not discovered features.
5. **Contamination patterns are exhaustive**: Check ALL 6 patterns for
   every test case, not just the first pattern found.

## Error Handling

| Issue | Resolution |
|---|---|
| Test cases file not found | Report error — uat-test-case-generator must run first |
| Qualified scenarios not found | Report error — qualification gate must run first |
| Empty test cases file | Output report with 0% coverage, all scenarios as gaps |
| Malformed JSONL line | Skip line, log warning, continue |
| No business requirements | Evaluate coverage against scenarios only (reduced benchmark) |

## Related Skills

| Skill | Relationship |
|---|---|
| **uat-test-case-generator** | Upstream — produces test-cases.jsonl for review |
| **uat-qualification-gate** | Upstream — produces unified-scenarios.jsonl baseline |
| **uat-excel-workbook-generator** | Downstream — consumes gap-fill tests for workbook update |
| **review-loop-controller** | Controller — invokes this skill iteratively |
