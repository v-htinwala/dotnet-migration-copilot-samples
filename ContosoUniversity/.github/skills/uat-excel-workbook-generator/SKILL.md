---
name: uat-excel-workbook-generator
description: >
  Generates professional Excel workbooks for UAT test cases using the canonical
  20-field test case schema. Produces a multi-sheet workbook with Summary
  Dashboard (priority, source, feature, journey breakdowns), All Test Cases
  (20 columns), per-journey sheets (grouped by journey_id), Traceability
  Matrix (test to source evidence mapping), and Dropdown Values. Consumes
  unified-scenarios.jsonl or uat-tests.jsonl from uat-test-case-generator
  with UAT-{MOD}-{SEQ} test IDs. Supports character-based batching for large
  test suites. Automatically hides empty optional columns. Use when producing
  Excel deliverables from the UAT test pipeline, or when the user needs a
  formatted UAT test case workbook with journey grouping and business metrics.
license: MIT
compatibility: >
  Requires Python 3.8+ and openpyxl (pip install openpyxl). Works with any
  skills-compatible coding agent with file system read/write access.
metadata:
  author: uat-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
---

# UAT Excel Workbook Generator

## Purpose

Generate professional Excel workbooks (.xlsx) from UAT test cases produced by
the `uat-test-case-generator` skill. This skill transforms the JSONL output
(20-field schema, UAT-{MOD}-{SEQ} IDs) into a formatted, multi-sheet workbook
designed for business stakeholders, product owners, and UAT testers.

> **Key Differentiator vs Functional Excel**: This skill uses the **20-field
> UAT schema** with business-oriented columns (business_objective, test_type,
> coverage_area), **per-journey sheet grouping** (not per-feature), and
> includes business-focused metrics in the Summary Dashboard. The functional
> version uses a 35-field schema with per-feature sheets, Coverage Matrix,
> Risk Heatmap, and API-Only Tests.

## When to Use This Skill

- Producing the final Excel deliverable from the UAT test pipeline
- Converting UAT test JSONL (20-field schema) to a formatted workbook
- Creating per-journey test case sheets for business stakeholder review
- Generating Traceability Matrix for requirements-to-test mapping
- Producing Summary Dashboard with business metrics (priority, coverage area)

## Prerequisites

```bash
pip install openpyxl
```

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `test_cases` | Yes | -- | Path to JSONL file (20-field schema) from uat-test-case-generator |
| `output_dir` | Yes | `uat-output/` | Output directory |
| `app_name` | No | auto-detect | Application name for filename and dashboard title |
| `batch_chars` | No | `8000` | Max characters per batch for incremental writes |

## Outputs

| File | Format | Description |
|---|---|---|
| `UAT_Test_Cases_{AppName}_{Date}.xlsx` | XLSX | Multi-sheet workbook with journey grouping |

---

## 20-Field Schema

The UAT test JSONL uses 20 fields organized into 5 sections:

| Section | Fields | Count |
|---|---|---|
| **Core** | test_id, test_name, feature, journey_id | 4 |
| **Classification** | test_type, coverage_area, priority, user_role | 4 |
| **Content** | preconditions, test_steps, expected_result, test_data, business_objective | 5 |
| **Traceability** | source, source_evidence, requirement_id | 3 |
| **Extended** | video_timestamp, screenshot_path, api_endpoint, component_path | 4 |

**Total: 20 fields**

### Column Rendering Order

1. **Core**: test_id, test_name, feature, journey_id
2. **Classification**: test_type, coverage_area, priority, user_role
3. **Content**: preconditions, test_steps, expected_result, test_data, business_objective
4. **Traceability**: source, source_evidence, requirement_id
5. **Extended**: video_timestamp, screenshot_path, api_endpoint, component_path

Optional empty columns (e.g., video_timestamp when no video source) are
hidden automatically to keep the workbook clean for stakeholder review.

---

## Workbook Structure

### Sheet 1: Summary Dashboard

| Row | Content |
|---|---|
| 1 | Title: "UAT Test Cases — {AppName}" |
| 2 | Generated: {date}, Sources: {sources_list} |
| 4-5 | **Totals**: Total tests, Features, Journeys |
| 7-12 | **By Priority**: P1/P2/P3/P4 counts |
| 14-20 | **By Coverage Area**: Business Process / UI / Data / Integration |
| 22-28 | **By Source**: video/url/codebase/merged counts |
| 30-36 | **By Feature**: Test count per feature |
| 38-44 | **By Journey**: Test count per journey |

### Sheet 2: All Test Cases

All test cases in a single flat table with all 20 columns.

**Formatting**:
- Header row: Bold, blue fill `#4472C4`, white font, freeze top row
- Auto-filter enabled on all columns
- Data validation dropdowns on: priority, test_type, status columns
- Text wrapping on content columns: preconditions, test_steps, expected_result
- Auto-width, max 60 characters
- Hidden columns for empty optional fields

### Sheets 3-N: Journey Sheets (one per journey_id)

For each unique `journey_id` value, create a sheet named after the journey
(truncated to 31 chars for Excel limit).

| Row | Content |
|---|---|
| 1 | Journey: {journey_id} |
| 2 | Feature: {feature}, Tests: {count} |
| 4+ | Test case rows (same columns as All Test Cases) |

### Sheet N+1: Traceability Matrix

| Column | Content |
|---|---|
| A | Test ID |
| B | Test Name |
| C | Requirement ID |
| D | Source |
| E | Source Evidence |
| F | Video Timestamp |
| G | API Endpoint |
| H | Component Path |

Maps each test case to its requirements and source evidence for
stakeholder traceability review.

### Sheet N+2: Dropdown Values

Reference data for data validation. These MUST use UAT-appropriate categories,
NOT functional test categories.

| Priority | Test Type | Coverage Area | Status |
|---|---|---|---|
| P1 | Acceptance | BusinessProcess | Not Executed |
| P2 | End-to-End Workflow | UserGoal | Pass |
| P3 | Business Rule Validation | BusinessRule | Fail |
| P4 | Role-Based Access | | Blocked |
| | | | Skipped |

> **CRITICAL**: Never use functional test categories in UAT workbooks:
> - test_type must NOT contain: "Functional", "Negative", "Boundary",
>   "Security", "UI" — these belong in the functional-excel-workbook-generator
> - coverage_area must NOT contain: "Module", "UI", "Data" — these are
>   functional scoping concepts, not UAT

---

## Data Transformation Rules

### Array Fields → Cell Text

| Field | Transformation |
|---|---|
| `preconditions` | Join with newline: `"1. User has valid account\n2. User is on home page"` |
| `test_steps` | Format as numbered steps: `"1. Navigate to login → Login form displayed\n2. Enter credentials → Fields populated"` |
| `test_data` | Format as key-value: `"email: testuser@example.com\npassword: ********"` |

### Empty Fields

Leave blank. Do not display "null", "undefined", or "N/A".

---

## Generation Workflow

### Step 1: Estimate Volume & Select Strategy

| Estimated Total Chars | Strategy |
|---|---|
| < 5,000 | Inline openpyxl generation |
| 5,000 - 15,000 | Script-based generation |
| > 15,000 | **Batched processing** (mandatory) |

### Step 2: Parse JSONL & Build Indexes

1. Parse JSONL file line by line
2. Group test cases by `journey_id` (for per-journey sheets)
3. Build per-feature counts (for Summary Dashboard)
4. Build per-source counts (for Summary Dashboard)

### Step 3: Generate Workbook

1. Create "Summary Dashboard" with business metrics
2. Create "All Test Cases" sheet with 20 columns
3. Create per-journey sheets (one per unique `journey_id`)
4. Create "Traceability Matrix" sheet
5. Create "Dropdown Values" reference sheet
6. Apply data validation, auto-filters, column hiding
7. Save workbook

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

## JSONL-to-Excel Script Usage

```bash
# Convert JSONL to Excel with journey-based sheets
python scripts/jsonl_to_excel.py uat-tests.jsonl --output UAT_Test_Cases.xlsx --batch-chars 8000

# Resume after failure (detects .progress file)
python scripts/jsonl_to_excel.py uat-tests.jsonl --output UAT_Test_Cases.xlsx
```

---

## Filename Convention

```
UAT_Test_Cases_{AppName}_{YYYY-MM-DD}.xlsx
```

- **AppName**: Sanitized, e.g., `FleetManager`
- **Date**: Generation date in ISO format
- **Directory**: `uat-output/`

---

## Constraints

1. **20-field schema only**: This skill expects UAT test JSONL with the
   20-field schema. Do not use for 35-field functional JSONL — use
   `functional-excel-workbook-generator` instead.
2. **Per-journey grouping**: Sheets are grouped by `journey_id` field, not
   `feature`. Each unique journey gets its own sheet.
3. **UAT- prefix expected**: Test IDs should follow `UAT-{MOD}-{SEQ}` format.
4. **Business-oriented dashboard**: Summary Dashboard shows business metrics
   (coverage area, journey distribution) not technical metrics (category
   distribution, confidence heatmap).
5. **Auto-hide empty columns**: Optional columns with no data across all rows
   are hidden automatically to keep the workbook clean for stakeholders.
6. **Batch by character length**: UAT test rows average 1000+ chars due to
   business_objective and test_steps content.

## Error Handling

| Error | Behavior |
|---|---|
| JSONL file not found | Fail with clear error — uat-test-case-generator must run first |
| Empty JSONL file | Generate workbook with Summary only (0 test cases) |
| Malformed JSONL line | Skip line, log warning, continue |
| Missing fields in record | Use empty defaults, log warning |
| Journey name > 31 chars | Truncate for sheet name, note full name in header |
| openpyxl not installed | Fail with `pip install openpyxl` instruction |

## Related Skills

| Skill | Relationship |
|---|---|
| **uat-test-case-generator** | Upstream — produces UAT test JSONL (20-field) |
| **uat-test-reviewer** | Upstream — may produce gap-fill tests |
| **uat-test-orchestrator** | Orchestrator — invokes this skill for Excel output |
| **scenario-merger** | Upstream — produces merged scenarios consumed by generator |

## References

- [references/batching-guide.md](references/batching-guide.md) — Character-based batching for large test suites
- [references/excel-templates.md](references/excel-templates.md) — Pre-built workbook templates
- [references/formatting-guide.md](references/formatting-guide.md) — Styles, formulas, and formatting patterns
