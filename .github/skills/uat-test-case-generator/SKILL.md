---
name: uat-test-case-generator
description: >
  Generates UAT test cases from qualified scenario candidates using a
  composition-first approach — combining multiple features into end-to-end
  business workflows rather than decomposing features into granular checks.
  Produces high-level, workflow-oriented test cases written in business language
  that validate whether users can accomplish their real-world goals. Accepts
  pre-qualified scenarios from uat-qualification-gate (canonical 20-field JSONL)
  and outputs UAT test cases grouped by journey. Test ID scheme is
  UAT-{MOD}-{SEQ}. Enforces UAT alignment through anti-pattern detection,
  minimum scope rules, and step granularity constraints. Use when generating
  UAT test cases for business stakeholders, product owners, and UAT testers.
license: MIT
compatibility: >
  Works with any skills-compatible coding agent with file system read/write
  access. No external dependencies. Consumes unified-scenarios.jsonl from
  uat-qualification-gate.
metadata:
  author: uat-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
---

# UAT Test Case Generator

## Purpose

Transform qualified UAT scenarios into **end-to-end business workflow test
cases** that validate whether users can accomplish their real-world goals. This
is the core value producer of the UAT pipeline.

> **CRITICAL DISTINCTION — Compose, Never Decompose**
>
> The functional-test-generator **decomposes** each feature into many granular
> checks (Positive, Negative, Boundary, Security, etc. — typically 10-15 tests
> per scenario). This skill does the **opposite**: it **composes** related
> scenarios into fewer, broader workflow tests that chain multiple features
> toward a business outcome.
>
> | Dimension | Functional Generator | THIS Skill (UAT) |
> |---|---|---|
> | Direction | Decompose feature → many checks | Compose features → workflow |
> | Tests per scenario | 10-15 granular checks | 1-2 workflow tests |
> | Step granularity | UI clicks, field fills | User goals, business actions |
> | Total test count | 100-500+ | 8-25 end-to-end scenarios |
> | Pass criteria | System behaves per spec | User achieves their objective |

## When to Use This Skill

- After `uat-qualification-gate` produces `unified-scenarios.jsonl`
- After the Phase 4 human checkpoint has approved scenarios
- When the user needs UAT test cases for business stakeholder sign-off
- When generating test cases for the `uat-excel-workbook-generator`

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `scenarios_jsonl` | Yes | -- | Path to `unified-scenarios.jsonl` from uat-qualification-gate |
| `output_dir` | Yes | -- | Output directory for test artifacts |
| `app_name` | No | auto-detect | Application name for test IDs and report |
| `target_test_count` | No | -- | Target number of UAT tests (guide, not hard limit) |

## Outputs

| File | Format | Description |
|---|---|---|
| `test-cases.jsonl` | JSONL | UAT test cases in canonical 20-field schema |
| `generation-report.json` | JSON | Statistics per journey, priority, coverage area |

---

## The Composition Principle

UAT test cases are **composed upward** from scenarios, not decomposed downward
from features. The key mental model:

```
FUNCTIONAL (wrong for UAT):
  Feature: Skill Detail Popup
    ├── FT-001: Open popup via info button          (single action)
    ├── FT-002: Verify description section displayed (element check)
    ├── FT-003: Verify tags section displayed        (element check)
    ├── FT-004: Verify triggers section displayed    (element check)
    ├── FT-005: Verify inputs/outputs displayed      (element check)
    └── FT-006: Close popup and return to cards      (single action)

UAT (correct):
  Journey: Evaluate Skills for a New Project
    └── UAT-001: As a team lead, discover available skills, review their
        details and tags, compare multiple options, and identify which
        skills fit the project's needs
        Steps:
          1. Browse the skill catalog to see what is available
          2. Search for skills relevant to the project's domain
          3. Open a skill's details to review its description and capabilities
          4. Review several skills to compare their fit
          5. Identify the skills that best match project requirements
        Expected: Team lead can evaluate and select appropriate skills
                  for their project from the available catalog
```

### Composition Rules

1. **Chain across features**: Every UAT test MUST touch 2+ features or modules.
   A test that stays within a single feature is a functional test in disguise.

2. **Start with a user goal, not a feature**: Frame the test as "User
   accomplishes X" not "Feature X works correctly."

3. **Steps are milestones, not clicks**: Each test step should represent a
   meaningful progress point in the workflow, not an individual UI interaction.

4. **End with business value confirmation**: The final step must confirm the
   user achieved their business objective, not that a UI element displayed.

---

## Anti-Patterns — Tests That Are NOT UAT

**NEVER generate tests matching these patterns.** If a scenario would produce
one of these, either merge it into a broader workflow or discard it.

### Anti-Pattern 1: Single-Action Tests

Tests that verify one UI interaction in isolation.

| Anti-Pattern Example | Why It Fails |
|---|---|
| "User navigates to the Cards tab" | Single navigation action, no goal |
| "User opens skill detail popup" | Single click, no business outcome |
| "User closes the popup" | Dismissal mechanism, not a user goal |
| "User clicks the search icon" | UI discovery, not a business workflow |

**Fix**: Merge into the broader workflow these actions belong to.

### Anti-Pattern 2: Element-Level Verification

Tests that check whether specific UI elements render correctly.

| Anti-Pattern Example | Why It Fails |
|---|---|
| "User views tags in the detail popup" | Verifying one popup section |
| "User views skill description" | Verifying one content area |
| "User sees skill counts per phase" | Data display check |
| "User identifies skill names on cards" | UI readability check |

**Fix**: These become assertions within a step of a broader workflow test,
not standalone test cases.

### Anti-Pattern 3: Data Count Assertions

Tests that verify specific quantities or completeness.

| Anti-Pattern Example | Why It Fails |
|---|---|
| "Verify approximately 250 skills displayed" | Data integrity check |
| "Verify all 8 SDLC phases are listed" | Completeness assertion |
| "Verify Planning phase shows 2 skills" | Specific count validation |

**Fix**: Remove. Data completeness belongs in functional or integration tests.

### Anti-Pattern 4: UI Mechanism Tests

Tests that verify how the UI behaves rather than what the user achieves.

| Anti-Pattern Example | Why It Fails |
|---|---|
| "Search results update dynamically as user types" | Implementation behavior |
| "User scrolls through the catalog" | Scroll mechanism test |
| "User verifies tab switching works" | Navigation mechanism test |

**Fix**: Remove. These are functional/technical concerns.

### Anti-Pattern 5: Edge Case Isolation

Tests that isolate error paths or boundary conditions.

| Anti-Pattern Example | Why It Fails |
|---|---|
| "User searches for a non-existent skill" | Negative test, not UAT |
| "User clears search to reset results" | State-reset mechanism |

**Fix**: If relevant, include as one step within a broader search workflow
(e.g., "user searches, refines, finds relevant results").

---

## Minimum Scope Rules

Every generated UAT test case MUST satisfy ALL of these:

| Rule | Requirement | Validation |
|---|---|---|
| **Multi-feature** | Spans 2+ features or modules | Check that test_steps reference actions from different feature areas |
| **Min 3 steps** | At least 3 high-level workflow steps | Count test_steps — reject if < 3 |
| **Goal-oriented name** | test_name describes a user accomplishment | Must start with user role + action verb (not "Verify" or "Check") |
| **Business expected result** | expected_result describes user achieving goal | Must NOT contain "displayed", "rendered", "visible", "popup opens" |
| **Coverage = BusinessProcess** | coverage_area is always "BusinessProcess" | Never "Module", "UI", or "Data" |
| **Type = Acceptance** | test_type is always "Acceptance" | Never "Functional", "Negative", "Boundary", "Security" |

---

## Step Granularity Guide

Each test step should describe a **user-meaningful milestone**, not a UI click.

### Step Writing Rules

| Rule | DO | DON'T |
|---|---|---|
| Describe user intent | "Browse available skills to find relevant ones" | "Click the Cards tab" |
| Combine related actions | "Search for skills matching the project's domain" | "Click search icon, type keyword, press Enter" |
| State outcomes as goals | "Identify skills that fit the project requirements" | "Verify cards are displayed with skill names" |
| Use business language | "Review the skill's capabilities and usage context" | "Check that description, tags, and triggers sections are populated" |
| Skip navigation mechanics | "Access the skill catalog" | "Navigate to URL, wait for page load, click Cards tab" |

### Step Granularity Self-Check

For each step, ask: "Would a business stakeholder understand and care about
this step?" If not, it is too granular.

| Stakeholder Cares? | Step | Verdict |
|---|---|---|
| Yes | "Evaluate skill details to assess fit for the team" | Correct granularity |
| No | "Click the info (i) button on the third card" | Too granular — merge up |
| Yes | "Compare multiple skills to select the best option" | Correct granularity |
| No | "Verify the popup displays 5 sections" | Too granular — this is a functional assertion |

---

## 4-Phase Generation Workflow

### Phase 1: Load Scenarios & Plan Journeys

1. **Parse `unified-scenarios.jsonl`** line by line.
2. **Group scenarios by `journey_id`** — each journey becomes one or more
   UAT test cases.
3. **Build journey composition map**: Identify which scenarios can be
   composed into single end-to-end tests:
   - Scenarios in the same journey → compose into one workflow test
   - Related scenarios across journeys (same feature domain) → consider
     composing into a cross-journey test
4. **Estimate output**: Target 1-2 UAT tests per journey. For a typical
   application with 5-7 features, expect **8-15 total UAT test cases**.
   If estimate exceeds 25, re-evaluate — you may be decomposing instead
   of composing.

### Phase 2: Compose Workflow Test Cases

For each journey (or journey group), compose a single end-to-end test:

1. **Identify the user's business goal** for this journey.
2. **Chain the journey's scenarios** into a sequential workflow:
   - Order by natural workflow progression (discover → evaluate → decide)
   - Each scenario becomes 1-2 high-level steps (not 1:1 scenario:test)
3. **Write test_steps** as user milestones (see Step Granularity Guide).
4. **Write expected_result** as goal achievement confirmation.
5. **Write business_objective** explaining why this workflow matters.
6. **Set classification fields**:
   - `test_type`: "Acceptance" (always)
   - `coverage_area`: "BusinessProcess" (always)
   - `user_role`: From the journey's primary user role

**Composition template**:

```jsonc
{
  "test_id": "UAT-DISC-001",
  "test_name": "Team lead evaluates and selects skills for a new project",
  "feature": "Skill Discovery",
  "journey_id": "J-CARDS-BROWSE",

  "test_type": "Acceptance",
  "coverage_area": "BusinessProcess",
  "priority": "P1",
  "user_role": "Team Lead",

  "preconditions": [
    "User is logged in as a Team Lead",
    "Skill catalog contains populated skill data"
  ],
  "test_steps": [
    {
      "step_number": 1,
      "action": "Browse the skill catalog to see what skills are available for the project",
      "expected": "User can see the available skills and get an overview of the catalog"
    },
    {
      "step_number": 2,
      "action": "Search for skills relevant to the project's technology domain",
      "expected": "Search results show skills matching the project's needs"
    },
    {
      "step_number": 3,
      "action": "Open several skills to review their descriptions, capabilities, and usage context",
      "expected": "User can understand what each skill does and how it applies to their work"
    },
    {
      "step_number": 4,
      "action": "Compare reviewed skills and identify the best options for the project",
      "expected": "User has enough information to make an informed selection"
    }
  ],
  "expected_result": "Team lead can discover, evaluate, and select the most appropriate skills for their project from the available catalog",
  "test_data": {},
  "business_objective": "Enable project leads to efficiently find and evaluate skills that match their project requirements, reducing time spent on manual capability assessment",

  "source": "merged",
  "source_evidence": "J-CARDS-BROWSE scenarios + J-CARDS-DETAIL scenarios",
  "requirement_id": "",

  "video_timestamp": "",
  "screenshot_path": "",
  "api_endpoint": "",
  "component_path": ""
}
```

### Phase 3: Validate Against Anti-Patterns

**MANDATORY** — run before writing output.

For each generated test case, apply these checks:

| Check | Rule | Action if Failed |
|---|---|---|
| **Feature span** | Test touches 2+ features | Merge with another test from the same domain |
| **Step count** | At least 3 steps | Expand scope or merge with related test |
| **Step granularity** | No step describes a single UI click | Rewrite step to describe user intent |
| **Expected result** | Does not contain "displayed", "visible", "popup", "rendered" | Rewrite to describe goal achievement |
| **Test name** | Starts with user role + action verb, not "Verify" or "Check" | Rewrite to describe user accomplishment |
| **coverage_area** | Equals "BusinessProcess" | Fix to "BusinessProcess" |
| **test_type** | Equals "Acceptance" | Fix to "Acceptance" |
| **Total count** | Suite has 8-25 tests (for typical app) | If > 25, consolidate; if < 8, check for missing journeys |

Log all validation results. If > 20% of tests fail validation, re-run
Phase 2 with stricter composition.

### Phase 4: Write Output & Report

1. **Write `test-cases.jsonl`**: One JSON object per line, 20-field schema.
2. **Write `generation-report.json`**:

```json
{
  "app_name": "SkilletWeave",
  "generated_at": "2026-02-26T10:00:00Z",
  "total_test_cases": 12,
  "scenarios_consumed": 37,
  "composition_ratio": "3.1 scenarios per test (target: 2-5)",
  "by_journey": {
    "J-CARDS-BROWSE": 2,
    "J-CARDS-DETAIL": 1,
    "J-JOURNEY-VIEW": 2,
    "J-STAGES-BROWSE": 2,
    "J-STAGES-DRILL": 2,
    "J-SEARCH-FIND": 2,
    "J-CROSS-FEATURE": 1
  },
  "by_priority": { "P1": 4, "P2": 5, "P3": 3 },
  "anti_pattern_checks": {
    "single_action_detected": 0,
    "element_verification_detected": 0,
    "data_count_assertions_detected": 0,
    "tests_rewritten": 0,
    "tests_merged": 3
  },
  "alignment_score": {
    "avg_feature_span": 2.4,
    "avg_step_count": 4.2,
    "all_coverage_area_business_process": true,
    "all_test_type_acceptance": true
  }
}
```

---

## Priority Assignment

| Priority | Criteria |
|---|---|
| **P1 (Critical)** | Core business workflow that ALL users must complete (onboarding, primary use case, authentication) |
| **P2 (High)** | Important workflow used by most users regularly (search + evaluate, compare options) |
| **P3 (Medium)** | Secondary workflow for specific user roles or less frequent use cases |
| **P4 (Low)** | Nice-to-have workflows, edge scenarios that still qualify as UAT |

---

## Test ID Convention

```
UAT-{MOD}-{SEQ}
```

- **MOD**: 3-5 char module code derived from journey domain
  - Skill Discovery → DISC
  - Skill Information → INFO
  - SDLC Organization → SDLC
  - Search → SRCH
  - Navigation / Cross-Feature → NAV
- **SEQ**: Zero-padded 3-digit sequential (001, 002, ...)

---

## Constraints

1. **Compose, never decompose.** Each qualified scenario becomes part of a
   broader workflow test — never a standalone test case.
2. **Target 8-25 total tests.** If your output exceeds 25 tests for a
   typical application, you are decomposing. Consolidate.
3. **Every test must span 2+ features.** Single-feature tests are functional
   tests in disguise.
4. **Steps are milestones, not clicks.** If a step describes a single UI
   interaction, rewrite it as a user intent.
5. **Business language only.** Never use: "verify", "confirm", "validate",
   "rendered", "displayed", "DOM", "component", "API", "endpoint".
6. **coverage_area is always "BusinessProcess".** Never "Module" or "UI".
7. **test_type is always "Acceptance".** Never "Functional", "Negative",
   "Boundary", "Security".
8. **expected_result describes goal achievement.** Never describes UI state.
9. **No data count assertions.** Never assert specific quantities, counts, or
   completeness of data.
10. **Test data safety**: Use obvious test values, never real PII.

## Error Handling

| Error | Behavior |
|---|---|
| Empty scenarios JSONL | Output empty test file + report with 0 counts |
| Malformed scenario line | Skip line, log warning, continue |
| Anti-pattern check fails > 20% | Re-run Phase 2 with stricter composition instructions |
| Cannot compose (single isolated scenario) | Generate as standalone with warning flag |

## Related Skills

| Skill | Relationship |
|---|---|
| **uat-qualification-gate** | Upstream — provides qualified scenarios |
| **uat-excel-workbook-generator** | Downstream — consumes test-cases.jsonl |
| **uat-test-reviewer** | Downstream — reviews for coverage gaps |
| **uat-test-orchestrator** | Orchestrator — triggers generation after checkpoint |

## References

- [references/composition-examples.md](references/composition-examples.md) — Before/after examples of composing scenarios into workflow tests
- [references/anti-pattern-catalog.md](references/anti-pattern-catalog.md) — Comprehensive catalog of non-UAT test patterns with fixes
