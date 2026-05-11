# Test Category Rules — functional-test-generator

Rules for generating test cases in each category from merged scenarios.

---

## Category Overview

| Category | Purpose | Min Tests | Trigger |
|---|---|---|---|
| **Positive** | Verify happy path works | 1 per action | Always generated |
| **Negative** | Verify error handling | 1 per required field | Has required fields |
| **Boundary** | Verify edge values accepted/rejected | 2 per constrained field | Has min/max constraints |
| **Validation** | Verify format/pattern rules | 1 per validation rule | Has validation_rule |
| **Security** | Verify injection resistance | 1 per text input + auth tests | Has text fields or auth |
| **Integration** | Verify cross-component behavior | 1 per cross-module ref | Has multiple modules/endpoints |

---

## Positive Tests

### Generation Rules

For each merged scenario with a CRUD action:

| Action Type | Test Name Pattern | Priority |
|---|---|---|
| Create | "Create {entity} with all valid fields" | P1 |
| Create | "Create {entity} with minimum required fields only" | P2 |
| Read (single) | "View {entity} details" | P2 |
| Read (list) | "List all {entities}" | P2 |
| Read (search) | "Search {entities} by {search_field}" | P2 |
| Update | "Update {entity} {field} successfully" | P1 |
| Delete | "Delete {entity} successfully" | P1 |

### Steps Pattern (Create)

```
1. Navigate to {feature} page → {feature} list displayed
2. Click 'Add/Create {entity}' → Creation form/dialog opens
3. Fill all required fields with valid data → Fields accept input
4. Fill optional fields (if any) → Fields accept input
5. Click 'Save/Submit/Create' → Success message, redirected to list
6. Verify {entity} appears in list → New {entity} visible with correct data
```

### Steps Pattern (Update)

```
1. Navigate to {feature} page → {feature} list displayed
2. Select existing {entity} → {entity} detail/edit view opens
3. Modify {field} to new valid value → Field accepts input
4. Click 'Save/Update' → Success message
5. Verify updated value persisted → {field} shows new value
```

### Steps Pattern (Delete)

```
1. Navigate to {feature} page → {feature} list displayed
2. Note current count of {entities} → Count is N
3. Select {entity} to delete → Selection confirmed
4. Click 'Delete' and confirm → Success/confirmation message
5. Verify {entity} removed from list → Count is N-1
```

---

## Negative Tests

### Generation Rules

For each required field in the scenario:

| Field Condition | Test Name Pattern | Priority |
|---|---|---|
| Required field omitted | "Submit {action} without required '{field}'" | P2 |
| Invalid format | "Submit {action} with invalid '{field}' format" | P3 |
| Invalid type | "Submit {action} with wrong type for '{field}'" | P3 |
| Duplicate value | "Submit {action} with duplicate '{field}'" | P2 (if unique) |

### Steps Pattern (Missing Required Field)

```
1. Navigate to {feature} creation form → Form displayed
2. Fill all fields EXCEPT '{field}' → Other fields filled
3. Click 'Save/Submit' → Form submission attempted
4. Verify error message → Error: "{field} is required"
5. Verify form not submitted → No new record created
```

### Expected Error Messages

| Condition | Template |
|---|---|
| Missing required field | `"{field_label} is required"` |
| Invalid email format | `"Please enter a valid email address"` |
| Invalid phone format | `"Please enter a valid phone number"` |
| Value too short | `"{field_label} must be at least {min} characters"` |
| Value too long | `"{field_label} must not exceed {max} characters"` |
| Invalid date | `"Please enter a valid date"` |
| Duplicate value | `"{field_label} already exists"` |

> Note: Actual error messages will vary. Use the generic template but add
> a note: "Actual error text may differ — verify error is displayed."

---

## Boundary Tests

### Generation Rules

For each field with min/max constraints:

| Boundary | Test Value | Expected | Priority |
|---|---|---|---|
| At minimum | `min_value` | Accepted | P3 |
| At maximum | `max_value` | Accepted | P3 |
| Below minimum | `min_value - 1` | Rejected | P3 |
| Above maximum | `max_value + 1` | Rejected | P3 |
| Zero (if applicable) | `0` or `""` | Depends on constraint | P3 |
| Empty (if optional) | `""` or `null` | Accepted | P3 |

### String Length Boundaries

```
Field: name (min: 1, max: 100)

Test 1: name = "A" (1 char — min boundary) → Accepted
Test 2: name = "A" × 100 (100 chars — max boundary) → Accepted
Test 3: name = "" (0 chars — below min) → Rejected
Test 4: name = "A" × 101 (101 chars — above max) → Rejected
```

### Numeric Boundaries

```
Field: quantity (min: 1, max: 999)

Test 1: quantity = 1 → Accepted (min)
Test 2: quantity = 999 → Accepted (max)
Test 3: quantity = 0 → Rejected (below min)
Test 4: quantity = 1000 → Rejected (above max)
Test 5: quantity = -1 → Rejected (negative)
```

---

## Validation Tests

### Generation Rules

For each field with a discovered validation rule:

| Rule Type | Test Count | Tests |
|---|---|---|
| Regex/pattern | 2 | One valid match, one invalid non-match |
| Enum/select | 2 | One valid option, one invalid option |
| Email format | 3 | Valid, missing @, missing domain |
| Date format | 2 | Valid format, invalid format |
| Required + format | 3 | Empty, valid format, invalid format |
| Cross-field | 2 | Valid combination, invalid combination |

### Cross-Field Validation

When two fields have a dependency:

```
Rule: end_date must be after start_date

Test 1 (valid): start_date = "2026-03-01", end_date = "2026-03-15" → Accepted
Test 2 (invalid): start_date = "2026-03-15", end_date = "2026-03-01" → Rejected
```

---

## Security Tests

### Generation Rules

| Test Type | Trigger | Priority |
|---|---|---|
| XSS in text field | Field accepts free text input | P1 |
| SQL injection in search | Field is used for search/filter | P1 |
| Auth bypass | Scenario has `auth_required: true` | P1 |
| Role escalation | Scenario has specific `user_role` | P1 |
| CSRF token | Scenario has POST/PUT/DELETE endpoint | P2 |
| Path traversal | Field accepts file paths | P1 |

### XSS Test Steps

```
1. Navigate to {feature} form → Form displayed
2. Enter XSS payload in '{field}': "<script>alert('XSS')</script>" → Field accepts/sanitizes input
3. Submit form → Form submitted
4. View the saved record → Payload is NOT executed, shown as plain text or sanitized
```

### SQL Injection Test Steps

```
1. Navigate to {feature} search/filter → Search interface displayed
2. Enter SQL payload: "' OR 1=1 --" in search field → Search executed
3. Verify results → Only legitimate results returned, no data leak
4. Verify no error → No database error exposed to user
```

### Auth Bypass Test Steps

```
1. Log out of the application → User is unauthenticated
2. Navigate directly to {protected_url} → Access denied or redirected
3. Verify → Login page displayed or 401/403 response
```

### Role Escalation Test Steps

```
1. Log in as {lower_role} (e.g., "End User") → Dashboard displayed
2. Navigate to {admin_feature_url} → Access attempted
3. Verify → Access denied message or 403 response
4. Verify no data exposed → No sensitive data visible
```

---

## Integration Tests

### Generation Rules

| Trigger | Test Description | Priority |
|---|---|---|
| Create followed by List | "Created {entity} appears in {entity} list" | P2 |
| API + UI consistency | "API response matches UI display for {entity}" | P2 |
| Cross-module reference | "{entity_A} references {entity_B} correctly" | P2 |
| Cascade delete | "Deleting {parent} handles {child} records" | P1 |
| State propagation | "Updating {entity} status reflects in {related}" | P2 |

### Steps Pattern (Create → List Integration)

```
1. Create a new {entity} via form → Entity created successfully
2. Navigate to {entity} list page → List displayed
3. Verify new {entity} appears → Entity visible with correct data
4. Verify count incremented → List count = previous + 1
```

### Steps Pattern (API ↔ UI Consistency)

```
1. Query {endpoint} directly → API returns {entity} data
2. Navigate to {entity} page in UI → UI displays {entity}
3. Compare API response fields with UI display → All fields match
```

---

## Test Deduplication Rules

Avoid generating duplicate tests:

| Overlap | Resolution |
|---|---|
| Negative (missing required) vs Validation (required rule) | Keep as Validation, drop Negative duplicate |
| Boundary (empty string) vs Negative (missing required) | Keep as Boundary, drop Negative duplicate |
| Security (XSS in field) already covered by Validation | Keep both — different concerns |
| Two Create positive tests from different sources | Keep one, use highest-confidence source |

**Dedup key**: `{feature} + {action} + {field_name} + {test_category} + {boundary_type}`

If the dedup key matches, keep the test with:
1. Higher confidence score
2. More detailed test data
3. More specific expected result
