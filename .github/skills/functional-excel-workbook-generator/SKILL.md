---
name: functional-excel-workbook-generator
description: >
  Generates professional Excel workbooks for functional test cases using the
  35-field test case schema. Produces an 8-sheet workbook with Summary Dashboard,
  All Test Cases (35 columns with 7 color-coded groups), per-feature sheets,
  API-Only Tests, Traceability Matrix, Coverage Matrix (feature x category),
  Risk Heatmap (priority x confidence), and Dropdown Values. Consumes
  functional-tests.jsonl from functional-test-generator with FT-{MOD}-{SEQ}
  test IDs. Supports character-based batching for large test suites (500+
  test cases). Use when producing Excel deliverables from the functional test
  pipeline, or when the user needs a formatted functional test case workbook
  with coverage and risk analysis sheets.
license: MIT
compatibility: >
  Requires Python 3.8+ and openpyxl (pip install openpyxl). Works with any
  skills-compatible coding agent with file system read/write access.
metadata:
  author: functional-test-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
---

# Functional Excel Workbook Generator

## Purpose

Generate professional Excel workbooks (.xlsx) from functional test cases produced
by the `functional-test-generator` skill. This skill transforms the JSONL output
(35-field schema, FT-{MOD}-{SEQ} IDs) into a formatted, multi-sheet workbook
designed for QA engineers and test leads.

> **Key Differentiator vs UAT Excel**: This skill uses the **35-field functional
> test schema** with 7 color-coded column groups, **per-feature sheet grouping**
> (not per-journey), and includes functional-specific sheets: **Coverage Matrix**
> (feature x category), **Risk Heatmap** (priority x confidence), and
> **API-Only Tests**. The UAT version uses a 20-field schema with per-journey
> grouping and business-oriented metrics.

## When to Use This Skill

- Producing the final Excel deliverable from the functional test pipeline
- Converting `functional-tests.jsonl` (35-field schema) to a formatted workbook
- Generating Coverage Matrix to identify category gaps per feature
- Generating Risk Heatmap to identify high-priority low-confidence areas
- Creating per-feature test case sheets for module-level review
- Isolating API-only test cases for backend testing teams

## Prerequisites

```bash
pip install openpyxl
```

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `test_cases` | Yes | -- | Path to `functional-tests.jsonl` from functional-test-generator |
| `output_dir` | Yes | `functional-tests/` | Output directory |
| `app_name` | No | auto-detect | Application name for filename and dashboard title |
| `batch_chars` | No | `8000` | Max characters per batch for incremental writes |

## Outputs

| File | Format | Description |
|---|---|---|
| `Functional_Test_Cases_{AppName}_{Date}.xlsx` | XLSX | Complete 8-sheet workbook |

---

## 35-Field Schema

The functional test JSONL uses 35 fields organized into 7 groups:

| Group | Color | Fields | Count |
|---|---|---|---|
| **Core Identification** | Blue `#4472C4` | test_id, test_name, feature, module | 4 |
| **Classification** | Green `#70AD47` | test_category, priority, user_role | 3 |
| **Test Content** | White `#FFFFFF` | preconditions, test_steps, expected_result, test_data | 4 |
| **Validation Detail** | Orange `#ED7D31` | field_name, validation_rule, valid_input, invalid_input, error_message, boundary_min, boundary_max | 7 |
| **State & API** | Purple `#7030A0` | state_before, state_after, side_effects, api_endpoint, http_method, status_code, api_only | 7 |
| **Traceability** | Gray `#A5A5A5` | source, source_evidence, confidence, screenshot_ref, video_timestamp, component_path | 6 |
| **Execution Tracking** | Yellow `#FFC000` | status, actual_result, defect_id, executed_by, execution_date | 4¹ |

¹ Total: 35 fields (30 generated + 5 execution tracking pre-populated as empty).

See [references/functional-test-excel-config.md](references/functional-test-excel-config.md)
for the complete column mapping (A-AJ), widths, and formatting rules.

---

## 8-Sheet Workbook Structure

### Sheet 1: Summary Dashboard

| Row | Content |
|---|---|
| 1 | Title: "Functional Test Cases — {AppName}" |
| 2 | Generated: {date}, Sources: {sources_list}, Complexity Tier: {tier} |
| 4-5 | **Totals**: Total tests, Features, Modules |
| 7-12 | **By Priority**: P1/P2/P3/P4 counts |
| 14-20 | **By Category**: Positive/Negative/Boundary/Validation/Security/Integration |
| 22-28 | **By Source**: video/url/codebase/merged counts |
| 30-34 | **Confidence Distribution**: High (0.9-1.0) / Medium (0.7-0.89) / Low (<0.7) |
| 36-42 | **Coverage Metrics**: Features covered, avg tests per feature, avg confidence |

### Sheet 2: All Test Cases

All test cases in a single flat table with all 35 columns (A-AJ).

**Formatting**:
- Header row: Bold, colored fill per group (7 colors), freeze top row
- Auto-filter enabled on all columns
- Data validation dropdowns on: test_category (E), priority (F), status (AF)
- Conditional formatting on status (AF):
  - "Pass" → Green, "Fail" → Red, "Blocked" → Yellow, "Skipped" → Light gray
- Conditional formatting on confidence (AB):
  - >= 0.9 → Green, 0.7-0.89 → Yellow, < 0.7 → Red
- Text wrapping on content columns: H, I, J, K
- Auto-width, max 60 characters

### Sheets 3-N: Feature Sheets (one per feature)

For each unique `feature` value, create a sheet named after the feature
(truncated to 31 chars for Excel limit).

| Row | Content |
|---|---|
| 1 | Feature: {feature_name} |
| 2 | Module: {module}, Tests: {count}, Avg Confidence: {avg} |
| 4+ | Test case rows (same 35 columns as All Test Cases) |

### Sheet N+1: API-Only Tests

Filter: `api_only == true`

Contains only API-only test cases (backend tests without UI components).
If none exist, include a note: "No API-only test cases generated."

### Sheet N+2: Traceability Matrix

| Column | Content |
|---|---|
| A | Test ID |
| B | Test Name |
| C | Feature |
| D | Source |
| E | Source Evidence |
| F | Video Timestamp |
| G | Screenshot Ref |
| H | Component Path |
| I | Confidence |

Quick lookup from test case to its evidence sources.

### Sheet N+3: Coverage Matrix

Feature x Category matrix showing test count distribution:

| Feature | Positive | Negative | Boundary | Validation | Security | Integration | Total |
|---|---|---|---|---|---|---|---|
| Vehicle Mgmt | 5 | 8 | 4 | 6 | 3 | 2 | 28 |
| Authentication | 3 | 4 | 2 | 3 | 4 | 1 | 17 |

Conditional formatting:
- 0 → Red fill (coverage gap)
- 1-2 → Yellow fill (low coverage)
- 3+ → Green fill (adequate)

### Sheet N+4: Risk Heatmap

Feature x (Priority + Confidence) matrix:

| Feature | P1 High | P1 Med | P1 Low | P2 High | P2 Med | P2 Low | P3 | P4 |
|---|---|---|---|---|---|---|---|---|
| Vehicle Mgmt | 3 | 2 | 0 | 4 | 3 | 1 | 5 | 2 |

Conditional formatting (red = high risk):
- P1 + Low confidence → Dark Red (critical risk)
- P1 + Medium confidence → Orange (moderate risk)
- P2 + Low confidence → Yellow (needs attention)
- P3/P4 or High confidence → Green (acceptable)

### Sheet N+5: Dropdown Values

Reference data for data validation:

| Priority | Category | Status | HTTP Method |
|---|---|---|---|
| P1 | Positive | Not Executed | GET |
| P2 | Negative | Pass | POST |
| P3 | Boundary | Fail | PUT |
| P4 | Validation | Blocked | PATCH |
| | Security | Skipped | DELETE |
| | Integration | | |

---

## Data Transformation Rules

### Array Fields → Cell Text

| Field | Transformation |
|---|---|
| `preconditions` | Join with newline: `"1. User is logged in\n2. Vehicle page accessible"` |
| `test_steps` | Format as numbered steps: `"1. Navigate to page → List displayed\n2. Click button → Form opens"` |
| `test_data` | Format as key-value: `"name: Test Vehicle\ntype: Heavy\nplate: AB1234"` |

### Boolean Fields

| Value | Display |
|---|---|
| `true` | "Yes" |
| `false` | "No" |

### Confidence Score

Display as percentage: `0.95` → `"95%"` with 2-decimal precision.

### Empty Fields

Leave blank. Do not display "null", "undefined", or "N/A".

---

## Generation Workflow

### Step 1: Estimate Volume & Select Strategy

```
total_lines = count lines in functional-tests.jsonl
est_chars = total_lines × 1200  (avg 35-field JSON line)
```

| Estimated Total Chars | Strategy |
|---|---|
| < 5,000 | Inline openpyxl generation |
| 5,000 - 15,000 | Script-based generation |
| > 15,000 | **Batched processing** (mandatory) |

### Step 2: Parse JSONL & Build Indexes

1. Parse `functional-tests.jsonl` line by line
2. Group test cases by `feature` (for per-feature sheets)
3. Group test cases where `api_only == true` (for API-Only sheet)
4. Build category counts per feature (for Coverage Matrix)
5. Build priority x confidence counts per feature (for Risk Heatmap)

### Step 3: Generate Workbook

1. Create "Summary Dashboard" sheet with computed metrics
2. Create "All Test Cases" sheet with all 35 columns, color-coded headers
3. Create per-feature sheets (one per unique `feature` value)
4. Create "API-Only Tests" sheet
5. Create "Traceability Matrix" sheet
6. Create "Coverage Matrix" sheet
7. Create "Risk Heatmap" sheet
8. Create "Dropdown Values" reference sheet
9. Apply data validation, conditional formatting, auto-filters
10. Save workbook

### Step 4: Verify Output

```python
from openpyxl import load_workbook

wb = load_workbook("output.xlsx")
print(f"Sheets: {wb.sheetnames}")
for name in wb.sheetnames:
    ws = wb[name]
    print(f"  {name}: {ws.max_row} rows")
```

---

## Filename Convention

```
Functional_Test_Cases_{AppName}_{YYYY-MM-DD}.xlsx
```

- **AppName**: Sanitized (no spaces, no special chars), e.g., `FleetManager`
- **Date**: Generation date in ISO format
- **Directory**: `functional-tests/`

---

## Batching for Large Test Suites

For test suites with >200 test cases or >15,000 characters of JSONL:

1. Parse all JSONL and compute indexes first (in memory)
2. Write "Summary Dashboard" sheet (small, computed)
3. Write "All Test Cases" in batches of 50 rows
4. Write per-feature sheets (one at a time, each is a natural batch)
5. Write analytics sheets (Coverage Matrix, Risk Heatmap — small, computed)
6. Save incrementally after each sheet

See [references/batching-guide.md](references/batching-guide.md) for
character-based batching utilities.

---

## Constraints

1. **35-field schema only**: This skill expects `functional-tests.jsonl` with
   the 35-field schema. Do not use for 20-field UAT JSONL — use
   `uat-excel-workbook-generator` instead.
2. **Per-feature grouping**: Sheets are grouped by `feature` field, not
   `journey_id`. Each unique feature gets its own sheet.
3. **FT- prefix expected**: Test IDs should follow `FT-{MOD}-{SEQ}` format.
4. **Coverage Matrix mandatory**: Always generate the Coverage Matrix sheet,
   even if all cells are filled. This is a key functional testing deliverable.
5. **Risk Heatmap mandatory**: Always generate the Risk Heatmap sheet for
   priority x confidence visibility.
6. **Batch by character length**: Never by row count. Functional test rows
   average 1200+ chars due to the 35-field schema.

## Error Handling

| Error | Behavior |
|---|---|
| JSONL file not found | Fail with clear error — functional-test-generator must run first |
| Empty JSONL file | Generate workbook with Summary only (0 test cases) |
| Malformed JSONL line | Skip line, log warning, continue |
| Missing fields in record | Use empty defaults, log warning |
| Feature name > 31 chars | Truncate for sheet name, note full name in sheet header |
| openpyxl not installed | Fail with `pip install openpyxl` instruction |
| Batch write failure | Save partial workbook, log error with batch number |

## Related Skills

| Skill | Relationship |
|---|---|
| **functional-test-generator** | Upstream — produces functional-tests.jsonl (35-field) |
| **functional-test-reviewer** | Upstream — may produce gap-fill tests to append |
| **functional-test-orchestrator** | Orchestrator — invokes this skill in Phase 6 |
| **functional-review-loop-controller** | Re-invokes this skill if gap-fill tests added |

## References

- [references/functional-test-excel-config.md](references/functional-test-excel-config.md) — Complete 35-field column mapping, color scheme, and sheet specs
- [references/batching-guide.md](references/batching-guide.md) — Character-based batching for large test suites
