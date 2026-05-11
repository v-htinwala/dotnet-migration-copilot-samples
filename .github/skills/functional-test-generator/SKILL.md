---
name: functional-test-generator
description: >
  Generates comprehensive functional test cases from merged scenario candidates.
  Uses a batched workflow that processes one module at a time, writing results
  incrementally to prevent context overflow for large projects. Automatically
  estimates output volume and selects the right batching strategy (inline for
  small inputs, module-batched for medium, scenario-batched for large). Supports
  resume on interruption via progress tracking. Produces the full 35-field test
  case schema covering core identification, classification, test content,
  validation detail, boundary detail, state & API, traceability, and execution
  tracking columns. Auto-generates test data using standard patterns (boundary
  values, security inputs, format variations) with optional user overrides via
  test-data-overrides.json. Test ID scheme is FT-{MODULE}-{SEQ}. Outputs
  functional-tests.jsonl and generation-report.json. Accepts
  merged-scenarios.jsonl from functional-scenario-merger as primary input.
license: MIT
compatibility: >
  Works with any skills-compatible coding agent with file system read/write
  access. No external dependencies.
metadata:
  author: functional-test-automation
  version: "2.1"
  category: testing
  user-invokable: "false"
---

# Functional Test Generator

## Purpose

Transform merged scenario candidates into fully specified functional test cases
using the 35-field test case schema. For each merged scenario, generate multiple
test cases spanning Positive, Negative, Boundary, Validation, Security, and
Integration categories. Auto-generate realistic test data and expected results.

This skill is the **core value producer** of the entire pipeline — all upstream
work (video analysis, URL exploration, codebase analysis, scenario merging)
feeds into this step.

## When to Use This Skill

- After the functional-scenario-merger has produced `merged-scenarios.jsonl`
- After the human checkpoint has approved/modified the feature map
- When the user wants functional test cases in structured JSONL format

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `merged_scenarios` | Yes | — | Path to `merged-scenarios.jsonl` from scenario merger |
| `output_dir` | Yes | — | Output directory for test artifacts |
| `test_data_overrides` | No | — | Path to `test-data-overrides.json` for domain-specific values |
| `app_name` | No | auto-detect | Application name for test IDs and report |
| `max_tests_per_scenario` | No | 15 | Maximum test cases generated per scenario |

## Outputs

| File | Format | Description |
|---|---|---|
| `functional-tests.jsonl` | JSONL | All generated test cases (35 fields each) — written incrementally per batch |
| `generation-report.json` | JSON | Statistics per feature, category, priority |
| `batch-schedule.json` | JSON | Planned batch list with volume estimates |
| `.generation-progress.json` | JSON | Resume state — completed batches, counters, status |

---

## 35-Field Test Case Schema

See [references/schema-reference.md](references/schema-reference.md) for the
complete schema with data types, defaults, and examples.

### Field Groups

| Group | Fields | Count |
|---|---|---|
| Core Identification | `test_id`, `test_name`, `feature`, `module` | 4 |
| Classification | `test_category`, `priority`, `user_role` | 3 |
| Test Content | `preconditions`, `test_steps`, `expected_result`, `test_data` | 4 |
| Validation Detail | `field_name`, `validation_rule`, `valid_input`, `invalid_input`, `error_message` | 5 |
| Boundary Detail | `boundary_min`, `boundary_max` | 2 |
| State & API | `state_before`, `state_after`, `side_effects`, `api_endpoint`, `http_method`, `status_code`, `api_only` | 7 |
| Traceability | `source`, `source_evidence`, `confidence`, `screenshot_ref`, `video_timestamp`, `component_path` | 6 |
| Execution Tracking | `status`, `actual_result`, `defect_id`, `executed_by`, `execution_date` | 4¹ |

¹ Schema defines 5 execution tracking fields; `actual_result` is shared with
test_steps.actual_field.

**Total: 35 fields** (30 generated + 5 execution tracking pre-populated as empty)

---

## 7-Phase Generation Workflow (Batched)

> **Why batched?** A single merged-scenarios file can produce 100–500+ test
> cases at ~1000 chars each — easily exceeding 100K characters of JSONL output.
> Generating everything in one pass risks context overflow, truncation, or
> stalling. The batched workflow processes **one module at a time**, writing
> results incrementally, so the skill works reliably for any project size.

### Phase 1: Load Merged Scenarios & Plan Batches

1. **Parse `merged-scenarios.jsonl`** line by line.
2. **Load `test-data-overrides.json`** if provided.
3. **Group scenarios by module/feature** for test ID sequencing.
4. **Build module code map**: Map feature → module → module code:
   - Extract first 3-4 uppercase characters
   - Ensure uniqueness across all modules
   - Example: "Vehicle Management" → "Vehicles" → "VEH"
5. **Initialize counters**: Per-module test ID sequence counters starting at 001.

### Phase 2: Estimate Volume & Select Strategy

**Goal**: Decide whether batching is needed and plan the batch schedule.

1. **Estimate output volume using adaptive heuristic**:

   Instead of assuming `max_tests_per_scenario` for every scenario, compute
   a per-scenario estimate based on its actual data richness:

   ```
   For each scenario, compute:
     fields       = len(discovered_fields)
     validations  = len(discovered_validations)
     has_endpoint = len(discovered_endpoints) > 0
     has_component = component_path is not empty

     est_tests_for_scenario =
       2                                     // Positive (happy path base)
       + min(fields, 3)                      // Negative (1 per required field, cap at 3)
       + (validations × 2)                   // Validation (valid + invalid per rule)
       + (fields > 0 ? 2 : 0)               // Security (XSS + injection if text fields)
       + (has_endpoint AND has_component ? 1 : 0)  // Integration (API↔UI)
       + (validations > 0 ? 2 : 0)          // Boundary (only if constraints exist)

     // Clamp to max_tests_per_scenario
     est_tests_for_scenario = min(est_tests_for_scenario, max_tests_per_scenario)

   total_est_tests = sum of est_tests_for_scenario across all scenarios
   est_chars = total_est_tests × 1000       (avg 35-field JSON line)
   ```

   > **Why adaptive?** The flat formula (`scenarios × 15 × 1000`) over-estimates
   > by 2-3× for scenarios with few validations/fields, causing unnecessary batch
   > splits and extra LLM round-trips. The adaptive formula typically produces
   > 5–8 tests per sparse scenario vs the assumed 15.

2. **Select strategy** based on estimated character output:

   | Estimated Total Chars | Strategy | Batch Unit |
   |---|---|---|
   | < 50,000 | **Inline** — generate all at once | All modules in one pass |
   | 50,000 – 200,000 | **Module-batched** — one module per pass | Each module = one batch |
   | > 200,000 | **Scenario-batched** — split large modules too | Max 10 scenarios per batch |

   > **Threshold rationale**: Modern LLM context windows comfortably handle
   > 120–150K chars of structured JSONL output per pass. The previous thresholds
   > (30K inline, 100K module-batched, 5 scenarios max) were overly conservative,
   > creating 2-3× more batches than necessary.

3. **Build batch schedule**: An ordered list of batches, each containing:
   ```jsonc
   {
     "batch_id": "B-001",
     "module": "VEH",
     "feature": "Vehicle Management",
     "scenario_ids": ["MRG-VEH-001", "MRG-VEH-002", ...],
     "scenario_count": 7,
     "est_tests": 42,         // sum of per-scenario adaptive estimates
     "est_chars": 42000,
     "applicable_categories": ["Positive", "Negative", "Security"]  // pre-computed
   }
   ```

4. **Pre-compute applicable categories per batch** (category applicability
   pre-check):

   For each batch, scan its scenarios and determine which categories will
   produce tests. Skip categories with no applicable scenarios to avoid
   wasted generation effort:

   | Category | Skip When |
   |---|---|
   | Validation | **All** scenarios in batch have `discovered_validations.length === 0` |
   | Boundary | **No** scenario in batch has fields with min/max constraints in `discovered_validations` |
   | Integration | **No** scenario in batch has both `discovered_endpoints` AND `component_path` |
   | Negative | **All** scenarios in batch have `discovered_fields.length === 0` |
   | Positive | Never skipped — always generated |
   | Security | Never skipped — always generated (at minimum auth bypass test) |

   Record the `applicable_categories` list in each batch entry. During Phase 4
   generation, only iterate the applicable categories for each batch.

5. **Write batch schedule** to `{output_dir}/batch-schedule.json` for
   observability and resume support.

### Phase 3: Check for Resume State

**Goal**: Support resuming after interruption.

1. **Check for `{output_dir}/.generation-progress.json`**:
   ```json
   {
     "completed_batches": ["B-001", "B-002"],
     "last_test_id_seq": {"VEH": 32, "DASH": 8},
     "tests_written": 40,
     "status": "in-progress"
   }
   ```
2. **If progress file exists and `status ≠ complete`**:
   - Skip already-completed batches
   - Resume test ID counters from `last_test_id_seq`
   - Append to existing `functional-tests.jsonl` (do NOT overwrite)
   - Log: "Resuming from batch B-003 (40 tests already written)"
3. **If no progress file** (fresh run):
   - Create empty `functional-tests.jsonl`
   - Initialize progress tracking
   - Log: "Starting fresh generation — {N} batches planned"

### Phase 4: Generate Test Cases per Batch (loop)

**This phase loops once per batch.** Each iteration processes one batch
(one module or a subset of scenarios), generates its test cases, writes them
to the output file, and updates progress — all before moving to the next batch.

> **Parallel module processing**: When using module-batched strategy and
> the orchestrator supports subagent parallelism, independent module batches
> MAY be processed in parallel (each module has its own ID sequence space).
> Only the final cross-module Integration batch must run after all module
> batches complete. See "Parallel Execution" note below.

#### Step 4a: Load Batch Scenarios

Read only the scenarios belonging to the current batch from the merged file.

#### Step 4b: Generate Test Cases for This Batch

For each scenario in the batch, generate test cases across the **applicable
categories only** (as pre-computed in Phase 2, Step 4). Skip categories
that were marked as not applicable for this batch.

See [references/test-category-rules.md](references/test-category-rules.md) for
detailed rules per category.

**Category: Positive (happy path)** — Priority P1/P2:
- One test case per primary action (Create, Read, Update, Delete)
- Use valid test data
- Expected result: success state
- Example: "Create vehicle with all valid fields → vehicle created successfully"

**Category: Negative (error handling)** — Priority P2/P3:
- **Skip if** scenario has `discovered_fields.length === 0`
- One test case per required field (omit each required field individually)
- One test case for invalid format per validated field
- Expected result: appropriate error message
- Example: "Submit vehicle form without required 'name' field → error: Name is required"

**Category: Boundary (edge values)** — Priority P3:
- **Skip if** scenario has no fields with min/max constraints in `discovered_validations`
- One test case per field with min/max constraints
- Test: min value, max value, min-1, max+1, zero, empty
- See [references/test-data-patterns.md](references/test-data-patterns.md)
- Example: "Enter vehicle name at max length (100 chars) → accepted"

**Category: Validation (format rules)** — Priority P2/P3:
- **Skip if** scenario has `discovered_validations.length === 0`
- One test case per validation rule (regex, format, enum constraint)
- Test valid and invalid inputs for each rule
- Example: "Enter plate number matching pattern [A-Z]{2}[0-9]{4} → accepted"

**Category: Security** — Priority P1:
- XSS injection test for each text input field
- SQL injection test for each search/filter field
- Auth bypass test if auth_required (access without login)
- Role escalation test if specific roles required
- See [references/test-data-patterns.md](references/test-data-patterns.md)

**Category: Integration** — Priority P2:
- **Skip if** scenario has only one endpoint OR no `component_path`
- Cross-module interaction tests (if scenario references multiple modules)
- API + UI consistency tests (if both endpoint and component known)
- State transition tests (create → list → appears in list)

#### Step 4c: Auto-Generate Test Data for This Batch

For each test case in this batch, generate appropriate test data:

1. **Check overrides first**: If `test-data-overrides.json` has a matching
   `{Feature}.{field}` key, use those values
2. **Apply standard patterns**: Use the auto-generation patterns from
   [references/test-data-patterns.md](references/test-data-patterns.md)
3. **Infer from merged scenario**: Use `discovered_validations` to derive
   valid/invalid inputs and boundary values
4. **Generate test_steps**: Build numbered step-by-step actions:
   ```json
   [
     {"step_number": 1, "action": "Navigate to Vehicles page", "expected": "Vehicles list is displayed"},
     {"step_number": 2, "action": "Click 'Add Vehicle' button", "expected": "Vehicle creation form opens"},
     {"step_number": 3, "action": "Fill in Name: 'Test Vehicle 001'", "expected": "Field accepts input"},
     {"step_number": 4, "action": "Click 'Save'", "expected": "Success message displayed, vehicle appears in list"}
   ]
   ```

#### Step 4d: Assign Test IDs & Priority for This Batch

1. **Test ID**: `FT-{MODULE_CODE}-{SEQ}`
   - MODULE_CODE: 3-4 char uppercase (e.g., VEH, AUTH, BOOK)
   - SEQ: Zero-padded 3-digit sequential within module (001, 002, …)
   - Continue from the last sequence number (from progress or 001 if first batch)
   - Example: `FT-VEH-001`, `FT-AUTH-015`
2. **Priority assignment**:

   | Category | Default Priority | Override Condition |
   |---|---|---|
   | Positive (CRUD) | P1 | — |
   | Positive (view/list) | P2 | — |
   | Negative (required field) | P2 | P1 if field is part of auth flow |
   | Negative (format) | P3 | P2 if security-sensitive field |
   | Boundary | P3 | P2 if constraint is business-critical |
   | Validation | P2 | P1 if validation prevents data corruption |
   | Security | P1 | Always P1 |
   | Integration | P2 | P1 if cross-module auth involved |

3. **Confidence inheritance**: Test cases inherit the `confidence` score from
   their parent merged scenario. Adjust downward for tests generated from
   inferred data (-0.05).

#### Step 4e: Write Batch Output & Update Progress

1. **Append** all test cases from this batch to `functional-tests.jsonl`
   (one JSON object per line, append mode — do NOT overwrite the file).
2. **Update** `.generation-progress.json`:
   ```json
   {
     "completed_batches": ["B-001"],
     "last_test_id_seq": {"VEH": 32},
     "tests_written": 32,
     "status": "in-progress"
   }
   ```
3. **Log progress**: "Batch B-001 (Vehicle Management): 32 tests written.
   Progress: 1/6 batches complete."
4. **Proceed to next batch** — loop back to Step 4a.

### Phase 5: Finalize & Write Report

> At this point all batches have completed and `functional-tests.jsonl` already
> contains every test case (written incrementally in Phase 4e). This phase
> produces the summary report and marks generation as complete.

1. **Count totals** from `functional-tests.jsonl` (re-read or use accumulated
   counters from the loop).
2. **Write `generation-report.json`** (see format below).
3. **Update `.generation-progress.json`** with `"status": "complete"`.
4. **Log final summary**: "Generation complete — {N} test cases across {M}
   features, {B} batches."

**functional-tests.jsonl** — one line per test case (already written):

```json
{
  "test_id": "FT-VEH-001",
  "test_name": "Create vehicle with all valid fields",
  "feature": "Vehicle Management",
  "module": "Vehicles",
  "test_category": "Positive",
  "priority": "P1",
  "user_role": "Fleet Manager",
  "preconditions": ["User is logged in as Fleet Manager", "Vehicles page is accessible"],
  "test_steps": [
    {"step_number": 1, "action": "Navigate to Vehicles page", "expected": "Vehicles list displayed"},
    {"step_number": 2, "action": "Click 'Add Vehicle'", "expected": "Creation form opens"},
    {"step_number": 3, "action": "Fill: Name='Test Vehicle', Type='Heavy', Plate='AB1234'", "expected": "Fields accept input"},
    {"step_number": 4, "action": "Click 'Save'", "expected": "Success message, vehicle in list"}
  ],
  "expected_result": "Vehicle is created and appears in the vehicle list",
  "test_data": {"name": "Test Vehicle", "type": "Heavy", "plate_number": "AB1234"},
  "field_name": "",
  "validation_rule": "",
  "valid_input": "",
  "invalid_input": "",
  "error_message": "",
  "boundary_min": "",
  "boundary_max": "",
  "state_before": "Vehicle list has N items",
  "state_after": "Vehicle list has N+1 items",
  "side_effects": "New record in vehicles table",
  "api_endpoint": "/api/vehicles",
  "http_method": "POST",
  "status_code": "201",
  "api_only": false,
  "source": "merged",
  "source_evidence": "video frame_042, URL screenshot vehicles-new.png",
  "confidence": 0.95,
  "screenshot_ref": "screenshots/vehicles-new.png",
  "video_timestamp": "01:23",
  "component_path": "src/pages/vehicles/CreateVehicle.tsx",
  "status": "Not Executed",
  "actual_result": "",
  "defect_id": "",
  "executed_by": "",
  "execution_date": ""
}
```

**generation-report.json**:

```json
{
  "app_name": "FleetManager",
  "generated_at": "2026-02-25T14:30:00Z",
  "total_test_cases": 156,
  "by_feature": {
    "Vehicle Management": 32,
    "Booking System": 28,
    "Authentication": 18,
    "User Management": 22,
    "Dashboard": 8,
    "Reports": 12,
    "Settings": 15,
    "Fleet Management": 21
  },
  "by_category": {
    "Positive": 42,
    "Negative": 38,
    "Boundary": 24,
    "Validation": 22,
    "Security": 18,
    "Integration": 12
  },
  "by_priority": {
    "P1": 48,
    "P2": 56,
    "P3": 40,
    "P4": 12
  },
  "by_source": {
    "merged": 120,
    "video": 8,
    "url": 14,
    "codebase": 14
  },
  "confidence_distribution": {
    "high_0.9_1.0": 52,
    "medium_0.7_0.89": 68,
    "low_0.3_0.69": 36
  },
  "test_data_overrides_applied": 4,
  "scenarios_processed": 42,
  "scenarios_skipped": 0
}
```

---

## Constraints

1. **Max tests per scenario**: Configurable, default 15. Prevents test
   explosion for complex scenarios.
2. **Deterministic**: Same input always produces the same test cases (sort
   by test_id for stable ordering).
3. **Incremental write — MANDATORY**: Write test cases to
   `functional-tests.jsonl` after **each batch completes** (append mode).
   Never buffer all test cases until the end. This prevents data loss on
   interruption and keeps per-batch output within context limits.
4. **Max output per batch**: A single batch MUST NOT produce more than
   ~120,000 characters of JSONL output (~120 test cases). If a module would
   exceed this, split it into sub-batches of ≤10 scenarios each.
5. **Progress tracking**: Update `.generation-progress.json` after each batch.
   On resume, skip completed batches and continue test ID sequencing.
6. **No duplicate tests**: If a Negative test and a Validation test would test
   the same thing (e.g., empty required field), generate only one and classify
   as the more specific category (Validation).
7. **Execution tracking fields always empty**: Fields `status`, `actual_result`,
   `defect_id`, `executed_by`, `execution_date` are always set to defaults
   ("Not Executed" for status, empty string for others).
8. **Test data safety**: Never generate test data with real PII. Use obvious
   test values: `test@example.com`, `Test User`, `+1-555-000-0000`.
9. **Batch isolation**: Each batch is self-contained. Do not reference test
   cases from other batches within a single batch's generation. Cross-module
   Integration tests should be generated in the last batch.
10. **Category skipping**: Do NOT generate tests for categories that have no
    supporting data in the batch's scenarios (see Phase 2, Step 4). This
    avoids wasted generation effort and reduces per-batch processing time.

## Parallel Execution (Module-Level)

When using **module-batched** or **scenario-batched** strategy, independent
module batches MAY be processed in parallel if the orchestrator supports
subagent parallelism:

- Each module has its own test ID sequence space (`FT-{MODULE}-{SEQ}`), so
  parallel generation produces no ID collisions.
- Each parallel batch appends to a **per-module temp file**
  (`functional-tests-{MODULE}.jsonl`), then Phase 5 concatenates them into
  the final `functional-tests.jsonl` in module-alphabetical order.
- The cross-module **Integration batch** (last batch) MUST wait for all
  module batches to complete before running, as it may reference entities
  from multiple modules.
- Progress tracking updates use per-module entries to avoid write conflicts.

**Parallel batch schedule example** (6 modules, module-batched):

```
┌─ Module VEH (27 scenarios) ──→ functional-tests-VEH.jsonl
├─ Module FE  (13 scenarios) ──→ functional-tests-FE.jsonl
├─ Module SRV ( 8 scenarios) ──→ functional-tests-SRV.jsonl
├─ Module HMV ( 8 scenarios) ──→ functional-tests-HMV.jsonl    ← all in parallel
├─ Module HDR ( 3 scenarios) ──→ functional-tests-HDR.jsonl
├─ Module FTR ( 1 scenario)  ──→ functional-tests-FTR.jsonl
└─ [wait for all] ──→ Integration batch ──→ functional-tests-INTG.jsonl
                   ──→ Concatenate all → functional-tests.jsonl
```

> When the orchestrator does NOT support parallel subagents, fall back to
> sequential module-by-module processing (the default behavior).

## Error Handling

| Error | Behavior |
|---|---|
| Empty merged-scenarios.jsonl | Output empty tests file + report with 0 counts |
| Malformed scenario line | Skip line, log warning, continue |
| Missing fields in scenario | Use empty defaults, lower test data quality, log warning |
| Override file not found | Proceed without overrides, log info |
| Override key doesn't match any field | Ignore unused overrides, log warning |

## Related Skills

| Skill | Relationship |
|---|---|
| **functional-scenario-merger** | Upstream — provides merged-scenarios.jsonl |
| **excel-workbook-generator** | Downstream — consumes functional-tests.jsonl |
| **functional-test-orchestrator** | Orchestrator — triggers generation after merge checkpoint |
