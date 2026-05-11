---
name: uat-qualification-gate
description: >
  Applies the 8-criteria UAT Qualification Gate to merged scenario candidates,
  filtering and transforming them into qualified UAT test scenarios. Evaluates
  each scenario for business perspective, requirement validation, real-world
  relevance, tester executability, business value verification, outcome focus,
  end-to-end workflow scope, and workflow-level granularity. Rewrites borderline
  scenarios, consolidates granular scenarios into broader workflows, downgrades
  weak ones, removes non-UAT candidates. Assigns priorities based on
  confirmation count, business criticality, usage frequency, and risk factors.
  Applies complexity tier filtering (quick/standard/comprehensive). Use when
  qualifying merged scenarios from scenario-merger before test case generation,
  or when filtering scenarios by UAT appropriateness and priority.
license: MIT
compatibility: >
  Consumes merged-scenarios.jsonl from scenario-merger skill. Outputs JSONL
  compatible with uat-test-case-generator and uat-test-playwright-generator.
metadata:
  author: uat-automation
  version: "1.0"
  category: testing
---

# UAT Qualification Gate

## Purpose

Apply the 8-criteria UAT Qualification Gate to scenario candidates, filtering
and transforming them into qualified UAT test scenarios ready for test case
generation.

> **Key Principle**: Not every discovered scenario belongs in a UAT suite. This
> gate ensures only business-appropriate, workflow-scoped, tester-executable,
> value-verifying scenarios proceed to test generation. Crucially, the gate also
> filters out scenarios that are too granular or narrow in scope — these belong
> in functional test suites, not UAT.

## When to Use This Skill

- Qualifying merged scenarios from `scenario-merger` before test generation
- Filtering scenario candidates by UAT appropriateness
- Assigning priorities based on multi-factor analysis
- Applying complexity tier filtering (quick/standard/comprehensive)
- Rewriting borderline technical scenarios into business language

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `scenarios_path` | Yes | -- | Path to merged scenarios JSONL file |
| `complexity_tier` | Yes | `standard` | `quick` (P1), `standard` (P1+P2), `comprehensive` (P1-P4) |
| `output_dir` | Yes | `uat-output/phase-4-merge` | Output directory |

## Outputs

| File | Format | Description |
|---|---|---|
| `unified-scenarios.jsonl` | JSONL | Qualified scenarios that pass the gate |
| `qualification-report.json` | JSON | Per-scenario gate results and statistics |

---

## The 8-Criteria UAT Qualification Gate

Every scenario candidate is evaluated against ALL 8 criteria. Criteria 1-6
evaluate **content quality**. Criteria 7-8 evaluate **scope and granularity**
— the most common root cause of UAT test cases that read like functional tests.

| # | Criterion | Question | Pass Example | Fail Example |
|---|---|---|---|---|
| 1 | **Business user perspective** | Written from a user's point of view? | "Fleet manager creates vehicle" | "POST /api/vehicles returns 201" |
| 2 | **Validates a requirement** | Verifies a specific business requirement? | Linked to REQ-VEH-101 | No requirement linkage |
| 3 | **Real-world scenario** | Represents a realistic usage pattern? | "Search vehicles by plate number" | "Click button ref=42" |
| 4 | **Executable by a tester** | Can a QA tester execute without dev assistance? | Clear preconditions and steps | Requires database manipulation |
| 5 | **Verifies business value** | Does passing confirm the system delivers value? | "Manager can track fleet status" | "Component renders correctly" |
| 6 | **Describes 'what' not 'how'** | Focuses on outcomes, not implementation? | "Vehicle appears in list" | "Redux store updates" |
| 7 | **End-to-end workflow scope** | Does this span a complete user workflow across 2+ features? | "Discover skills, evaluate details, select best fit for project" | "Open skill detail popup" (single feature, single action) |
| 8 | **Workflow-level granularity** | Are the steps high-level user goals, not individual UI actions? | "Review skill capabilities to assess fit" | "Click info button, verify popup displays, read description section" |

> **Why criteria 7 and 8 are critical**: A scenario like "User opens skill
> detail popup using the info button" can pass criteria 1-6 (business language,
> real-world, executable, verifies value, describes what). But it is a
> **single-action, single-feature check** — a functional test wearing UAT
> clothing. Criteria 7 and 8 catch this by requiring end-to-end scope and
> workflow-level granularity.

### Non-UAT Keyword Detection

Scenarios containing these keywords likely fail the gate:

| Category | Keywords |
|---|---|
| **Technical implementation** | API, endpoint, HTTP, status code, response, request, payload |
| **Code-level** | function, method, class, component, render, state, props |
| **Database** | SQL, query, table, column, record, INSERT, UPDATE, SELECT |
| **Infrastructure** | server, deploy, container, docker, CI/CD, pipeline |
| **Developer tools** | console, debugger, network tab, devtools, logs |

These scenarios should be rewritten or removed.

### Non-UAT Scope Detection

Scenarios matching these **scope patterns** fail criteria 7 or 8, even if
their language passes criteria 1-6:

| Scope Pattern | Example | Why It Fails | Action |
|---|---|---|---|
| **Single-action test** | "User navigates to the Stages tab" | One UI action, no workflow | Merge into broader journey or remove |
| **Element-level verification** | "User views tags in the detail popup" | Checks one UI element | Merge into feature evaluation workflow |
| **Data count assertion** | "User verifies ~250 skills are displayed" | Quantity check, not user goal | Remove (belongs in functional tests) |
| **UI mechanism test** | "Search results update dynamically as user types" | Tests interaction pattern, not goal | Remove (belongs in functional tests) |
| **Error/edge-case isolation** | "User searches for a non-existent skill" | Negative test in isolation | Merge as one step in a search workflow, or remove |
| **Single-feature-only** | "User opens and closes the skill detail popup" | Stays within one feature | Compose with upstream/downstream features |

> **Key insight**: If a scenario describes something that would be a single
> test step within a larger workflow, it is too granular for UAT. It should be
> merged into the workflow it belongs to, not tested independently.

---

## 4-Step Qualification Process

### Step 1: Evaluate Each Scenario

For each scenario in the input JSONL, evaluate against all 8 criteria:

```jsonc
{
  "scenario_name": "Create new vehicle",
  "criteria_results": {
    "business_perspective": { "pass": true, "note": "Written as Fleet Manager action" },
    "validates_requirement": { "pass": true, "note": "Maps to vehicle creation workflow" },
    "real_world_scenario": { "pass": true, "note": "Realistic fleet management task" },
    "executable_by_tester": { "pass": true, "note": "Clear steps with observable outcomes" },
    "verifies_business_value": { "pass": true, "note": "Confirms fleet management capability" },
    "what_not_how": { "pass": true, "note": "Describes outcome, not implementation" },
    "end_to_end_scope": { "pass": true, "note": "Spans vehicle creation through list confirmation" },
    "workflow_granularity": { "pass": true, "note": "Steps describe user goals, not individual clicks" }
  },
  "criteria_passed": 8,
  "criteria_failed": 0,
  "qualification": "QUALIFIED"
}
```

### Step 2: Transform Failing Scenarios

| Criteria Failed | Action | Example |
|---|---|---|
| **1-2 criteria** (close) | **Rewrite** to pass | "POST /api/vehicles returns 201" -> "Submitting the vehicle form saves the vehicle successfully" |
| **3-4 criteria** | **Downgrade** to P4 priority | Technical scenario kept but lowest priority |
| **5-8 criteria** | **Remove** | Unit-test-level, single-action, or infrastructure checks |
| **Fails only #7 or #8** (scope/granularity) | **Mark for consolidation** | Single-action scenarios flagged for Step 2b merging |

**Rewrite rules**:
- Replace API references with user-visible actions
- Replace technical assertions with observable outcomes
- Replace code references with business terminology
- Add user role context if missing
- Add business objective if missing

### Step 2b: Consolidate Granular Scenarios

**This step is critical for preventing functional-test contamination.**

After individual evaluation, scan the remaining scenarios for granularity
problems — multiple scenarios that target the same feature area with
single-action or single-element scope.

**Consolidation algorithm**:

1. **Group by feature + journey_id**: Collect scenarios sharing the same
   feature domain or journey.

2. **Detect granular clusters**: If a group has 3+ scenarios that each
   describe a single action within the same feature (e.g., "open popup",
   "view description", "view tags", "view triggers", "close popup"), flag
   the entire group for consolidation.

3. **Merge into workflow**: Replace the cluster with one or two broader
   workflow scenarios. The individual actions become steps within the
   workflow, not standalone scenarios.

   **Before consolidation** (6 separate scenarios):
   - "User opens skill detail popup"
   - "User views skill description"
   - "User views skill tags"
   - "User views triggering phrases"
   - "User views inputs and outputs"
   - "User closes skill detail popup"

   **After consolidation** (1 workflow scenario):
   - "User evaluates a skill's capabilities by reviewing its full details
     including description, tags, triggers, and input/output requirements"

4. **Update test steps**: The consolidated scenario's steps become the
   high-level workflow milestones, not the granular UI actions.

5. **Log consolidation**: Record which scenarios were merged and why in
   the qualification report.

### Step 3: Assign Priorities

Priority is determined by weighted factors:

| Factor | Weight | P1 Signal | P4 Signal |
|---|---|---|---|
| **Confirmation count** | 0.3 | Confirmed by all 3 sources | Single source only |
| **Business criticality** | 0.3 | Auth, payment, core CRUD | Settings, help pages |
| **Usage frequency** | 0.2 | Repeated in video journeys | Seen once |
| **Risk factors** | 0.2 | Complex business logic in code | Simple static page |

**Priority assignment**:

| Priority | Criteria |
|---|---|
| **P1 (Critical)** | Score >= 0.8 OR auth/payment flows OR confirmed by all sources |
| **P2 (High)** | Score >= 0.6 OR confirmed by 2+ sources with high business criticality |
| **P3 (Medium)** | Score >= 0.4 OR secondary features with some cross-source confirmation |
| **P4 (Low)** | Score < 0.4 OR single-source with low criticality OR downgraded scenarios |

**Business criticality mapping**:

| Criticality | Features |
|---|---|
| Critical | Authentication, authorization, payment, checkout, core entity CRUD |
| High | Search, filtering, reporting, user management, notifications |
| Medium | Settings, preferences, profile, help, about |
| Low | Cosmetic, tooltips, animations, footer links |

---

## Complexity Tier Filtering

After priority assignment, filter by the user's chosen complexity tier:

| Tier | Priority Filter | Typical Result |
|---|---|---|
| **Quick** | P1 only | 5-15 scenarios (critical path) |
| **Standard** | P1 + P2 | 15-30 scenarios (critical + important) |
| **Comprehensive** | P1 + P2 + P3 + P4 | 30-60 scenarios (full coverage) |

---

## Output Format

### unified-scenarios.jsonl

Each qualified scenario in canonical 20-field format:

```jsonc
{
  "test_id": "UAT-VEH-001",
  "test_name": "Create new vehicle with valid data",
  "feature": "Vehicle Management",
  "journey_id": "J-VEH-CRUD",

  "test_type": "Acceptance",
  "coverage_area": "BusinessProcess",
  "priority": "P1",
  "user_role": "Fleet Manager",

  "preconditions": [
    "User is logged in as Fleet Manager",
    "At least one vehicle type exists"
  ],
  "test_steps": [
    {
      "step_number": 1,
      "action": "Access the fleet management area to view existing vehicles",
      "expected": "User can see the current fleet inventory"
    },
    {
      "step_number": 2,
      "action": "Add a new vehicle to the fleet with required details",
      "expected": "Vehicle creation process completes successfully"
    },
    {
      "step_number": 3,
      "action": "Confirm the new vehicle appears in the fleet inventory",
      "expected": "User can verify the vehicle was added and is ready for assignment"
    }
  ],
  "expected_result": "Fleet manager can add a new vehicle to the fleet and confirm it is available for operations",
  "test_data": { "vehicle_name": "Truck-001", "vehicle_type": "Heavy Duty" },
  "business_objective": "Enable fleet managers to maintain accurate fleet inventory by adding new vehicles as they are acquired",

  "source": "merged",
  "source_evidence": "frame_042 + /vehicles route + CreateVehicle.tsx",
  "requirement_id": "REQ-VEH-101",

  "video_timestamp": "01:23",
  "screenshot_path": "phase-2-url/screenshots/vehicles.png",
  "api_endpoint": "POST /api/vehicles",
  "component_path": "src/pages/vehicles/CreateVehicle.tsx"
}
```

### qualification-report.json

```jsonc
{
  "generated_at": "2026-02-24T10:30:00Z",
  "complexity_tier": "standard",
  "input_scenarios": 28,
  "qualification_results": {
    "qualified": 18,
    "rewritten": 4,
    "consolidated": 8,
    "consolidated_into": 2,
    "downgraded_to_p4": 1,
    "removed": 3
  },
  "after_tier_filter": {
    "tier": "standard",
    "p1_count": 8,
    "p2_count": 10,
    "total_output": 18
  },
  "per_scenario": [
    {
      "scenario_name": "Create new vehicle",
      "criteria_passed": 8,
      "qualification": "QUALIFIED",
      "priority": "P1",
      "included_in_output": true
    }
  ],
  "consolidated_scenarios": [
    {
      "merged_from": ["Open skill popup", "View description", "View tags", "View triggers", "View inputs/outputs", "Close popup"],
      "merged_into": "User evaluates skill capabilities by reviewing full details",
      "reason": "6 single-action scenarios targeting same feature consolidated into 1 workflow"
    }
  ],
  "removed_scenarios": [
    {
      "scenario_name": "Verify Redux store update on save",
      "criteria_passed": 1,
      "reason": "Unit-test-level check, fails 7 of 8 UAT criteria"
    },
    {
      "scenario_name": "User scrolls through skill catalog",
      "criteria_passed": 4,
      "reason": "Fails criteria 7 (single-action, no workflow scope) and 8 (UI mechanism, not user goal)"
    }
  ]
}
```

## Error Handling

| Issue | Resolution |
|---|---|
| Scenarios file not found | Report error -- scenario-merger must run first |
| Invalid JSONL format | Skip invalid lines, log warning, continue |
| All scenarios fail gate | Output empty JSONL, report warning, suggest reviewing inputs |
| Unknown complexity tier | Default to `standard` with warning |

## Related Skills

- **scenario-merger** -- Produces merged scenarios consumed by this skill
- **uat-test-case-generator** -- Generates detailed test cases from qualified scenarios
- **uat-test-playwright-generator** -- Generates Playwright tests from qualified scenarios
- **uat-test-reviewer** -- Reviews generated tests for coverage gaps
