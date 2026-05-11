# Phase 2: Exploration-Driven Test Case Generation

Detailed workflow for generating **functional UAT test cases** by interacting with the live web application using Playwright CLI.

> **Remember**: You are a Senior UAT Tester. Interact with the app like a real user — try everything, break things, document what you find.

---

## Overview

Phase 2 processes one feature at a time. For each feature, you EXPLORE the live app via Playwright, then generate test cases based on what you observe.

```
FOR EACH FEATURE:
  1. Navigate to the feature URL via Playwright
  2. Snapshot to discover all interactive elements
  3. Interact with elements like a Senior UAT Tester
  4. Generate test cases based on observed behavior
  5. Write test cases to JSONL file IMMEDIATELY
  6. Report progress
  7. Move to next feature
```

---

## Step-by-Step Workflow

### Step 2.1: Announce Feature Start

```
═══════════════════════════════════════════════════════════════
[N/Total] FEATURE: <Feature Name>
Type: <feature_type> | URL: <feature_url>
Purpose: <what users do here>
═══════════════════════════════════════════════════════════════
```

### Step 2.2: Explore the Feature via Playwright

```bash
# Navigate to the feature
playwright-cli open <FEATURE_URL>

# Take a snapshot to understand ALL elements on the page
playwright-cli snapshot --filename=snapshots/feature-<name>.yaml

# Capture the initial state
playwright-cli screenshot --filename=screenshots/feature-<name>-initial.png
```

**From the snapshot, identify:**
- All input fields (text, email, date, number)
- All dropdowns/select menus
- All buttons (submit, cancel, delete, etc.)
- All links and navigation elements
- All data displays (tables, cards, lists)
- All status indicators
- All error/success message areas

### Step 2.3: Plan Test Coverage

Based on what you discovered, plan the test scenarios:

| Scenario Type | What to Test | How to Discover |
|---------------|--------------|-----------------|
| **Positive** | User completes task successfully | Fill form correctly, click submit |
| **Negative** | User sees appropriate errors | Submit empty form, enter invalid data |
| **Validation** | Form/input validation | Try each field with invalid values |
| **Boundary** | Edge cases | Empty data, max length, special chars |
| **Usability** | Loading, feedback, disabled states | Observe transitions, check disabled elements |
| **Cross-Feature** | Interactions between features | Create record, then search for it |

Display the test plan before generating:

```
   Test Plan for <Feature Name>:
   ┌─────────────────────┬─────────────────────────────────────┐
   │ Scenario Type       │ What to Cover                       │
   ├─────────────────────┼─────────────────────────────────────┤
   │ Positive (Happy)    │ Create, edit, save, complete        │
   │ Negative (Errors)   │ Invalid data, business rule blocks  │
   │ Validation          │ Required fields, format errors      │
   │ Boundary            │ Empty list, max characters          │
   │ Usability           │ Loading states, disabled buttons    │
   └─────────────────────┴─────────────────────────────────────┘
```

### Step 2.4: Interact and Observe (Senior Tester Approach)

This is where the Senior UAT Tester mindset matters most. Don't just test the obvious — try everything.

#### 2.4.1: Try the Wrong Thing First (Negative Discovery)

```bash
# Submit empty form — what validation appears?
playwright-cli click <submit-button-ref>
playwright-cli snapshot --filename=snapshots/<feature>-empty-submit.yaml
playwright-cli screenshot --filename=screenshots/<feature>-empty-submit.png

# Enter invalid email format
playwright-cli fill <email-ref> "not-an-email"
playwright-cli click <submit-button-ref>
playwright-cli snapshot --filename=snapshots/<feature>-invalid-email.yaml

# Enter very long text
playwright-cli fill <name-ref> "AAAAAAAAAA... (200+ chars)"
playwright-cli snapshot

# Enter special characters
playwright-cli fill <name-ref> "<script>alert('xss')</script>"
playwright-cli snapshot

# Try SQL injection patterns
playwright-cli fill <name-ref> "'; DROP TABLE users; --"
playwright-cli snapshot
```

#### 2.4.2: Do It Right (Positive Discovery)

```bash
# Fill form with valid data
playwright-cli fill <name-ref> "Test Customer 001"
playwright-cli fill <email-ref> "test@example.com"
playwright-cli select <region-ref> "Americas"
playwright-cli screenshot --filename=screenshots/<feature>-filled.png

# Submit
playwright-cli click <submit-button-ref>
playwright-cli snapshot --filename=snapshots/<feature>-success.yaml
playwright-cli screenshot --filename=screenshots/<feature>-success.png
```

#### 2.4.3: Explore Edge Cases

```bash
# Check what happens with no data in a list
# Check pagination with few vs many records
# Check sort on each column
# Check filter combinations
# Check what happens when you navigate away with unsaved changes
# Check double-click on submit button
# Check browser back button behavior
```

#### 2.4.4: Check Responsive Behavior

```bash
# Mobile viewport
playwright-cli resize 375 812
playwright-cli snapshot --filename=snapshots/<feature>-mobile.yaml
playwright-cli screenshot --filename=screenshots/<feature>-mobile.png

# Tablet viewport
playwright-cli resize 768 1024
playwright-cli screenshot --filename=screenshots/<feature>-tablet.png

# Back to desktop
playwright-cli resize 1920 1080
```

### Step 2.5: Generate Functional Test Cases

Based on your observations, write test cases in plain business language:

**Good Test Case Example:**
```
TC-CUST-001 | Create a new customer with all required fields
Feature Area: Customer Management
Priority: Critical
Preconditions: User is logged in; User is on the Customer List page
Test Steps:
1. Navigate to the Customer List page
2. Click the 'Add New Customer' button
3. Enter Customer Name: "Test Customer 001"
4. Select Region: "Americas"
5. Enter Email: "test.customer@example.com"
6. Click the 'Save' button
7. Observe the success message
8. Verify the new customer appears in the list
Test Data: Name: Test Customer 001, Region: Americas, Email: test.customer@example.com
Expected Result: Customer is created and appears in the customer list
Validation Points: Success message displays; Customer visible in list; Name shows correctly
Playwright Commands:
  playwright-cli open <url>/customers
  playwright-cli click e15
  playwright-cli fill e20 "Test Customer 001"
  playwright-cli select e25 "Americas"
  playwright-cli fill e30 "test.customer@example.com"
  playwright-cli click e35
Screenshots: TC-CUST-001-form.png; TC-CUST-001-success.png
```

### Step 2.6: Write to JSONL Immediately

> ⚠️ **CRITICAL: Write test cases to JSONL after each batch, NOT at the end!**

```python
import json

def write_test_cases_to_jsonl(filepath: str, test_cases: list):
    """Append test cases to JSONL file — call after each batch!"""
    with open(filepath, 'a', encoding='utf-8') as f:
        for tc in test_cases:
            f.write(json.dumps(tc, ensure_ascii=False) + '\n')
```

### Step 2.7: Report Batch Progress

After each batch of test cases:

```
   Batch Complete:
      ✓ Generated <N> test cases (TC-XXX-001 to TC-XXX-NNN)
      ✓ Written to JSONL: uat_<project>.jsonl
      ✓ Screenshots captured: <count>
      Test coverage: <scenarios covered>
      Running total: <cumulative_count> test cases
```

### Step 2.8: Feature Completion Summary

After all test cases for a feature are generated:

```
───────────────────────────────────────────────────────────────
FEATURE COMPLETE: <Feature Name>
   User scenarios covered:
     ✓ Positive: <count> — happy path workflows
     ✓ Negative: <count> — error handling
     ✓ Validation: <count> — input validation
     ✓ Boundary: <count> — edge cases
     ✓ Usability: <count> — loading, feedback, states
   Total test cases: <total> (TC-XXX-001 to TC-XXX-NNN)
   Screenshots: <count> evidence files
   ✓ All test cases written to: uat_<project>.jsonl
───────────────────────────────────────────────────────────────
```

---

## Test Case Categories

### Positive Tests (Happy Path)

**Focus:** User successfully completes their task

| User Goal | How to Discover via Playwright | Test Case |
|-----------|-------------------------------|-----------|
| Create a record | Fill form correctly → click Save | Fill form → Save succeeds |
| Edit a record | Click Edit → modify → Save | Changes saved correctly |
| Delete a record | Click Delete → Confirm | Record removed from list |
| Complete a workflow | Follow all steps | Process completes |
| Search for data | Enter criteria → search | Results displayed |

### Negative Tests (Error Handling)

**Focus:** User makes mistakes and sees helpful error messages

| Scenario | How to Discover via Playwright | Test Case |
|----------|-------------------------------|-----------|
| Missing required data | Click Submit with empty fields | Error messages appear |
| Invalid data format | Enter "not-an-email" in email field | Format error shown |
| Business rule violation | Try blocked action | Business error shown |
| No results | Search with gibberish text | "No results" message |

### Validation Tests

**Focus:** Form input validation

| Field Type | How to Discover | Test Cases |
|------------|-----------------|------------|
| Required text | Submit empty → observe error | Empty → Error; Filled → No error |
| Email | Enter "abc" → observe | Invalid format → Error |
| Date | Enter past date → observe | Past date → Error (if not allowed) |
| Number range | Enter 0 or 999999 → observe | Out of range → Error |
| Character limit | Enter 500 chars → observe | Exceed limit → Error or truncation |

### Boundary Tests (Edge Cases)

**Focus:** Unusual but valid situations

| Boundary | How to Discover | Test Case |
|----------|-----------------|-----------|
| Empty data | Navigate to list with no records | "No data" message |
| Maximum characters | Fill field to max | Saves correctly or truncates |
| Special characters | Enter `<>&"'` | Handled correctly, no XSS |
| First/last page | Navigate pagination extremes | Buttons disable appropriately |
| Rapid clicks | Double-click submit | No duplicate submissions |

### Usability Tests

**Focus:** User experience quality

| Aspect | How to Discover | Test Case |
|--------|-----------------|-----------|
| Loading states | Observe during page transitions | Spinner/skeleton shows |
| Disabled states | Check buttons before/after conditions | Buttons enable/disable correctly |
| Tooltips | Hover over icons/labels | Helpful text appears |
| Error recovery | After error, fix and retry | Can recover without page reload |
| Feedback | After actions | Toast/message confirms action |

---

## Organizing Test Cases by Feature

Group test cases logically by what users do:

```
FEATURE: Customer Management

User Workflows (discovered via Playwright):
├── View customer list
│   ├── TC-CUST-001: List loads with customer data
│   ├── TC-CUST-002: Empty list shows "No customers" message
│   └── TC-CUST-003: Search customers by name
│
├── Create a new customer
│   ├── TC-CUST-004: Create with all required fields
│   ├── TC-CUST-005: Submit empty form shows validation errors
│   ├── TC-CUST-006: Invalid email format shows error
│   └── TC-CUST-007: Special characters in name handled correctly
│
├── Edit a customer
│   ├── TC-CUST-008: Edit and save changes
│   └── TC-CUST-009: Cancel edit discards changes
│
└── Delete a customer
    ├── TC-CUST-010: Delete with confirmation
    └── TC-CUST-011: Cancel delete keeps record
```

---

## Test Case Writing Guidelines

### Use Clear Action Verbs

| Good | Avoid |
|------|-------|
| Navigate to the Dashboard | Load the dashboard component |
| Click the 'Save' button | Trigger handleSave event |
| Enter "John Smith" in the Name field | Set nameInput.value |
| Select "Americas" from Region dropdown | Dispatch region selection |
| Verify success message appears | Assert toast component visible |

### Write Observable Expected Results

| Good | Avoid |
|------|-------|
| Success message "Customer saved" displays | Database record created |
| Customer "John Smith" appears in list | API returns status 200 |
| Error message shows "Name is required" | Validation exception thrown |
| Page redirects to Customer List | Router navigates to /customers |

### Provide Specific Test Data

| Good | Avoid |
|------|-------|
| Name: "Test Customer 001" | Name: valid string |
| Email: "test@example.com" | Email: valid email |
| Amount: 1500 | Amount: number within range |
| Date: February 15, 2026 | Date: future date |

### Include Playwright Commands

Each test case should include the Playwright CLI commands that execute/verify it:

```
Playwright Commands:
  playwright-cli open https://app.example.com/customers
  playwright-cli click e15  # Add New button
  playwright-cli fill e20 "Test Customer 001"
  playwright-cli click e35  # Save button
  playwright-cli snapshot   # Verify success state
```

---

## ⚠️ Timeout Prevention

### Critical Rule: Write After Each Batch

```
✓ CORRECT:
  Explore feature → Generate batch → Write to JSONL → Next batch

✗ WRONG:
  Explore all → Generate all → Write all at end
```

### Memory-Safe Pattern

```python
for feature in features:
    # 1. Explore feature via Playwright
    explore_feature_via_playwright(feature.url)
    
    # 2. Generate test cases based on observations
    test_cases = generate_functional_tests(feature)
    
    # 3. ⚠️ WRITE IMMEDIATELY — before next feature!
    write_test_cases_to_jsonl("uat_project.jsonl", test_cases)
    
    # 4. Report progress
    print(f"✓ {len(test_cases)} tests written for {feature.name}")
```

---

## Checklist Before Moving to Next Feature

- [ ] Navigated to feature URL via Playwright
- [ ] Took snapshot to discover all elements
- [ ] Tried submitting empty/invalid data (negative tests)
- [ ] Completed the happy path (positive tests)
- [ ] Tested edge cases (boundary tests)
- [ ] Checked validation on all input fields
- [ ] Observed loading states and feedback messages
- [ ] Captured screenshots as evidence
- [ ] All positive scenarios covered (happy paths)
- [ ] All negative scenarios covered (error handling)
- [ ] Validation tests for all required/formatted fields
- [ ] Boundary cases considered (empty, max, special)
- [ ] Test cases written in plain business language
- [ ] Test data is specific (not placeholder)
- [ ] Playwright commands included for each test case
- [ ] **Test cases written to JSONL file** (not held in memory)
- [ ] Progress checkpoint displayed

### Deep Exploration Checklist (Mandatory)

- [ ] Every dropdown/radio group tested with EACH option individually (not just one generic selection)
- [ ] Cancel flows tested on every delete/destructive confirmation dialog
- [ ] Default field values verified on form open (checkboxes, dates, numeric defaults)
- [ ] Numeric input boundary values tested (min and max for every numeric field)
- [ ] Summary/dashboard counts cross-validated against detail list page counts
- [ ] Empty/unassigned states tested alongside populated states
- [ ] Modals explored deeply — sub-elements, calculated fields, line items all snapshotted and tested
- [ ] Multi-step wizards walked with each branching option (not just one path)
