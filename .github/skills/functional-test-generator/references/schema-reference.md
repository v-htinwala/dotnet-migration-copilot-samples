# Schema Reference — functional-test-generator

Complete 35-field test case schema with data types, defaults, and examples.

---

## Full Schema Definition

### Group 1: Core Identification (4 fields)

| # | Field | Type | Required | Default | Description |
|---|---|---|---|---|---|
| 1 | `test_id` | string | Yes | — | Unique ID: `FT-{MODULE}-{SEQ}` (e.g., `FT-VEH-001`) |
| 2 | `test_name` | string | Yes | — | Descriptive test name (human-readable) |
| 3 | `feature` | string | Yes | — | Feature/module being tested |
| 4 | `module` | string | Yes | — | Application module code |

**test_id rules**:
- Format: `FT-{MODULE_CODE}-{SEQ}`
- MODULE_CODE: 3-4 uppercase letters derived from module name
- SEQ: Zero-padded 3-digit sequential within module (001, 002, …)
- Must be unique across the entire test suite
- Examples: `FT-VEH-001`, `FT-AUTH-015`, `FT-BOOK-003`

**Module code derivation**:
| Module | Code | Notes |
|---|---|---|
| Authentication | AUTH | 4 chars for clarity |
| Vehicles | VEH | |
| Bookings | BOOK | 4 chars for clarity |
| Users | USR | |
| Dashboard | DASH | 4 chars for clarity |
| Settings | SET | |
| Reports | RPT | |
| Fleet | FLT | |
| Notifications | NOTF | 4 chars for clarity |
| Payments | PAY | |

### Group 2: Classification (3 fields)

| # | Field | Type | Required | Default | Values |
|---|---|---|---|---|---|
| 5 | `test_category` | string | Yes | — | `Positive`, `Negative`, `Boundary`, `Security`, `Integration`, `Validation` |
| 6 | `priority` | string | Yes | — | `P1` (Critical), `P2` (High), `P3` (Medium), `P4` (Low) |
| 7 | `user_role` | string | Yes | `"End User"` | Role required to execute |

**Priority guidelines**:
| Level | Meaning | Typical Categories |
|---|---|---|
| P1 | Critical — must pass for release | Security, Positive (CRUD), Auth |
| P2 | High — important for quality | Negative (required fields), Integration, Validation |
| P3 | Medium — nice to verify | Boundary, Negative (format), Validation (minor) |
| P4 | Low — edge cases | Rare boundary conditions, cosmetic validations |

### Group 3: Test Content (4 fields)

| # | Field | Type | Required | Default | Description |
|---|---|---|---|---|---|
| 8 | `preconditions` | string[] | Yes | `[]` | Setup requirements before execution |
| 9 | `test_steps` | object[] | Yes | `[]` | Ordered steps: `[{step_number, action, expected}]` |
| 10 | `expected_result` | string | Yes | — | Overall expected outcome |
| 11 | `test_data` | object | Yes | `{}` | Input data for the test |

**test_steps format**:
```json
[
  {
    "step_number": 1,
    "action": "Navigate to the Vehicles page",
    "expected": "Vehicles list page is displayed with existing vehicles"
  },
  {
    "step_number": 2,
    "action": "Click 'Add Vehicle' button",
    "expected": "Vehicle creation form opens with empty fields"
  }
]
```

**preconditions examples**:
- `"User is logged in as Fleet Manager"`
- `"At least one vehicle exists in the system"`
- `"User has 'Admin' role permissions"`
- `"Application is running and accessible"`

### Group 4: Validation Detail (5 fields)

| # | Field | Type | Required | Default | Description |
|---|---|---|---|---|---|
| 12 | `field_name` | string | No | `""` | Specific field under test |
| 13 | `validation_rule` | string | No | `""` | Rule being tested |
| 14 | `valid_input` | string | No | `""` | Input that should pass |
| 15 | `invalid_input` | string | No | `""` | Input that should fail |
| 16 | `error_message` | string | No | `""` | Expected error text on failure |

**Usage**: Populated primarily for Validation and Negative test categories.

**Examples**:
```json
{
  "field_name": "plate_number",
  "validation_rule": "Required, pattern: [A-Z]{2}[0-9]{4}",
  "valid_input": "AB1234",
  "invalid_input": "1234AB",
  "error_message": "Plate number must be 2 letters followed by 4 digits"
}
```

### Group 5: Boundary Detail (2 fields)

| # | Field | Type | Required | Default | Description |
|---|---|---|---|---|---|
| 17 | `boundary_min` | string | No | `""` | Minimum valid value or length |
| 18 | `boundary_max` | string | No | `""` | Maximum valid value or length |

**Usage**: Populated for Boundary test category.

### Group 6: State & API (7 fields)

| # | Field | Type | Required | Default | Description |
|---|---|---|---|---|---|
| 19 | `state_before` | string | No | `""` | System state before action |
| 20 | `state_after` | string | No | `""` | Expected state after action |
| 21 | `side_effects` | string | No | `""` | Observable side effects |
| 22 | `api_endpoint` | string | No | `""` | Related API endpoint |
| 23 | `http_method` | string | No | `""` | `GET`/`POST`/`PUT`/`PATCH`/`DELETE` |
| 24 | `status_code` | string | No | `""` | Expected HTTP status code |
| 25 | `api_only` | boolean | No | `false` | True if test is API-only |

**status_code patterns**:
| Scenario | Expected Code |
|---|---|
| Successful create | 201 |
| Successful read | 200 |
| Successful update | 200 |
| Successful delete | 200 or 204 |
| Validation error | 400 or 422 |
| Authentication required | 401 |
| Authorization denied | 403 |
| Resource not found | 404 |
| Duplicate/conflict | 409 |

### Group 7: Traceability (6 fields)

| # | Field | Type | Required | Default | Description |
|---|---|---|---|---|---|
| 26 | `source` | string | Yes | — | `video`/`url`/`codebase`/`merged` |
| 27 | `source_evidence` | string | No | `""` | Specific evidence references |
| 28 | `confidence` | number | Yes | — | 0.0-1.0 from merged scenario |
| 29 | `screenshot_ref` | string | No | `""` | Path to relevant screenshot |
| 30 | `video_timestamp` | string | No | `""` | Timestamp in source video (MM:SS) |
| 31 | `component_path` | string | No | `""` | Source file path from codebase |

### Group 8: Execution Tracking (4 fields)

| # | Field | Type | Required | Default | Description |
|---|---|---|---|---|---|
| 32 | `status` | string | Yes | `"Not Executed"` | `Not Executed`/`Pass`/`Fail`/`Blocked`/`Skipped` |
| 33 | `actual_result` | string | No | `""` | What actually happened (tester fills) |
| 34 | `defect_id` | string | No | `""` | Linked defect/bug ID |
| 35 | `executed_by` | string | No | `""` | Tester name |

> Note: The spec mentions `execution_date` as a 5th tracking field. Map it as
> field 35b or embed it within `actual_result` context. If the downstream Excel
> workbook generator needs a separate column, the orchestrator will handle the
> column mapping.

---

## Schema Validation Rules

When generating test cases, validate:

| Rule | Check |
|---|---|
| test_id uniqueness | No two test cases share the same test_id |
| test_id format | Matches `FT-[A-Z]{3,4}-\d{3}` regex |
| test_category value | One of the 6 allowed values |
| priority value | One of P1, P2, P3, P4 |
| status default | Always "Not Executed" |
| test_steps not empty | At least 2 steps per test case |
| confidence range | 0.0 ≤ confidence ≤ 1.0 |
| api_only boolean | Must be true or false, not string |
