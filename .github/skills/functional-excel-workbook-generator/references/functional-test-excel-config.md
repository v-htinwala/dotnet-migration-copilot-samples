# Functional Test Excel Configuration

Configuration reference for producing functional test case Excel workbooks
using the `excel-workbook-generator` skill. This document specifies the
35-field column mapping, 8-sheet structure, formatting rules, and data
validation for the functional test pipeline.

---

## Schema: 35-Field Functional Test Case

### Column Mapping (All Test Cases Sheet)

| Column | Field | Header Label | Width | Color Group |
|---|---|---|---|---|
| A | `test_id` | Test ID | 14 | Blue (Core) |
| B | `test_name` | Test Name | 40 | Blue (Core) |
| C | `feature` | Feature | 24 | Blue (Core) |
| D | `module` | Module | 16 | Blue (Core) |
| E | `test_category` | Category | 14 | Green (Classification) |
| F | `priority` | Priority | 10 | Green (Classification) |
| G | `user_role` | User Role | 18 | Green (Classification) |
| H | `preconditions` | Preconditions | 40 | White (Content) |
| I | `test_steps` | Test Steps | 60 | White (Content) |
| J | `expected_result` | Expected Result | 40 | White (Content) |
| K | `test_data` | Test Data | 35 | White (Content) |
| L | `field_name` | Field Name | 18 | Orange (Validation) |
| M | `validation_rule` | Validation Rule | 30 | Orange (Validation) |
| N | `valid_input` | Valid Input | 20 | Orange (Validation) |
| O | `invalid_input` | Invalid Input | 20 | Orange (Validation) |
| P | `error_message` | Error Message | 30 | Orange (Validation) |
| Q | `boundary_min` | Boundary Min | 14 | Orange (Validation) |
| R | `boundary_max` | Boundary Max | 14 | Orange (Validation) |
| S | `state_before` | State Before | 30 | Purple (State & API) |
| T | `state_after` | State After | 30 | Purple (State & API) |
| U | `side_effects` | Side Effects | 30 | Purple (State & API) |
| V | `api_endpoint` | API Endpoint | 28 | Purple (State & API) |
| W | `http_method` | HTTP Method | 12 | Purple (State & API) |
| X | `status_code` | Status Code | 12 | Purple (State & API) |
| Y | `api_only` | API Only | 10 | Purple (State & API) |
| Z | `source` | Source | 12 | Gray (Traceability) |
| AA | `source_evidence` | Source Evidence | 30 | Gray (Traceability) |
| AB | `confidence` | Confidence | 12 | Gray (Traceability) |
| AC | `screenshot_ref` | Screenshot Ref | 30 | Gray (Traceability) |
| AD | `video_timestamp` | Video Timestamp | 16 | Gray (Traceability) |
| AE | `component_path` | Component Path | 40 | Gray (Traceability) |
| AF | `status` | Execution Status | 16 | Yellow (Execution) |
| AG | `actual_result` | Actual Result | 40 | Yellow (Execution) |
| AH | `defect_id` | Defect ID | 14 | Yellow (Execution) |
| AI | `executed_by` | Executed By | 18 | Yellow (Execution) |
| AJ | `execution_date` | Execution Date | 14 | Yellow (Execution) |

### Color Scheme

| Group | Fill Color (Hex) | Font Color | Fields |
|---|---|---|---|
| Core Identification | `#4472C4` (Blue) | White | A-D |
| Classification | `#70AD47` (Green) | White | E-G |
| Test Content | `#FFFFFF` (White) | Black | H-K |
| Validation Detail | `#ED7D31` (Orange) | White | L-R |
| State & API | `#7030A0` (Purple) | White | S-Y |
| Traceability | `#A5A5A5` (Gray) | White | Z-AE |
| Execution Tracking | `#FFC000` (Yellow) | Black | AF-AJ |

---

## 8-Sheet Workbook Structure

### Sheet 1: Summary Dashboard

| Row | Content |
|---|---|
| 1 | Title: "Functional Test Cases — {AppName}" |
| 2 | Generated: {date}, Sources: {sources_list} |
| 4-5 | **Totals**: Total tests, Features, Modules |
| 7-12 | **By Priority**: P1/P2/P3/P4 counts + bar chart |
| 14-20 | **By Category**: Positive/Negative/Boundary/Validation/Security/Integration |
| 22-28 | **By Source**: video/url/codebase/merged counts |
| 30-34 | **Confidence Distribution**: High/Medium/Low |
| 36-42 | **Coverage Metrics**: Features covered, avg tests per feature, fields per test |

### Sheet 2: All Test Cases

All test cases in a single flat table with all 35 columns (A-AJ).

**Formatting**:
- Header row: Bold, colored fill per group, freeze top row
- Auto-filter enabled on all columns
- Data validation dropdowns on columns E, F, AF (category, priority, status)
- Conditional formatting on column AF (status):
  - "Pass" → Green fill
  - "Fail" → Red fill
  - "Blocked" → Yellow fill
  - "Skipped" → Light gray fill
  - "Not Executed" → No fill (default)
- Conditional formatting on column AB (confidence):
  - ≥ 0.9 → Green fill
  - 0.7-0.89 → Yellow fill
  - < 0.7 → Red fill
- Auto-width on columns, max width 60 characters
- Text wrapping on columns H, I, J, K (content fields)

### Sheet 3-N: Feature Sheets (one per feature)

For each unique `feature` value, create a sheet named after the feature
(truncated to 31 chars for Excel sheet name limit).

**Content**: Same columns as "All Test Cases" but filtered to only that
feature's tests. Include feature summary header rows:

| Row | Content |
|---|---|
| 1 | Feature: {feature_name} |
| 2 | Module: {module}, Tests: {count}, Avg Confidence: {avg} |
| 4+ | Test case rows (same columns as All Test Cases) |

### Sheet N+1: API-Only Tests

Filter: `api_only == true`

**Content**: Same columns as "All Test Cases" but only API-only tests.
If no API-only tests exist, include a note: "No API-only test cases generated."

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

Purpose: Quick lookup from test case to its evidence sources.

### Sheet N+3: Coverage Matrix

Feature × Category matrix:

| Feature | Positive | Negative | Boundary | Validation | Security | Integration | Total |
|---|---|---|---|---|---|---|---|
| Vehicle Mgmt | 5 | 8 | 4 | 6 | 3 | 2 | 28 |
| Authentication | 3 | 4 | 2 | 3 | 4 | 1 | 17 |
| ... | ... | ... | ... | ... | ... | ... | ... |

Conditional formatting:
- 0 → Red fill (coverage gap)
- 1-2 → Yellow fill (low coverage)
- 3+ → Green fill (adequate)

### Sheet N+4: Risk Heatmap

Feature × (Priority + Confidence) matrix:

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

| Column A | Column B | Column C | Column D |
|---|---|---|---|
| **Priority** | **Category** | **Status** | **HTTP Method** |
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

## Filename Convention

```
Functional_Test_Cases_{AppName}_{YYYY-MM-DD}.xlsx
```

- **AppName**: Sanitized (no spaces, no special chars), e.g., `FleetManager`
- **Date**: Generation date in ISO format
- **Directory**: `functional-tests/`

## Batching

For large test suites (>500 test cases), write in batches of 100 rows
to prevent memory issues. The excel-workbook-generator already supports
batched writing via its `write_batch.py` script.
