# Phase 2B: Streaming Mode (Universal Fallback)

> ⚠️ **Use this mode when `runSubagent` tool is NOT available, or as the default approach.**

Streaming mode processes features sequentially in the current context, writing test cases to JSONL immediately after each batch to prevent timeout.

---

## When to Use

- Default mode for all agents
- When `runSubagent` tool is unavailable
- Smaller applications with fewer features
- When you need fine-grained control over exploration

## Key Rules

1. **Feature-based batches** — Group test cases by user workflows
2. **Display batch plan** before processing
3. **Explore via Playwright** — interact with the live app for each batch
4. **Output progress** after EACH batch
5. **⚠️ WRITE TO JSONL IMMEDIATELY** — After generating test cases for each batch, WRITE them to the JSONL file BEFORE proceeding to the next batch. DO NOT accumulate test cases in memory.

---

## ⛔ CRITICAL: Streaming Write Pattern

> **You MUST write test cases to JSONL after EACH BATCH, not at the end!**

```
FOR EACH FEATURE:
  1. Open feature URL in Playwright
  2. Snapshot to discover all elements
  3. FOR EACH BATCH in FEATURE:
     a. Interact with elements in this batch (click, fill, submit)
     b. Observe actual behavior (screenshots, snapshots)
     c. Generate FUNCTIONAL test cases based on observations
     d. ⚠️ WRITE test cases to JSONL file NOW (before next batch)
     e. Output progress checkpoint
     f. THEN proceed to next batch
```

---

## Batching Patterns (Functional Grouping)

| Pattern | What to Group | Test Focus |
|---------|---------------|------------|
| User Journey | Login → Dashboard → Action | End-to-end workflow |
| Feature Screen | Single page/form | All actions on that screen |
| CRUD Operations | Create + Edit + Delete | Full lifecycle of a record |
| Search & Filter | Search + Filter + Sort | Finding and viewing data |

---

## JSONL Output Format

**Filename convention**: `uat_<project_name>.jsonl`

### Mandatory Write After Each Batch

```python
import json

JSONL_FILE = "uat_<project_name>.jsonl"

def write_test_cases_to_jsonl(test_cases: list[dict]):
    """CALL THIS AFTER EACH BATCH — DO NOT WAIT UNTIL END!"""
    with open(JSONL_FILE, 'a', encoding='utf-8') as f:
        for tc in test_cases:
            f.write(json.dumps(tc, ensure_ascii=False) + '\n')
    print(f"✓ Wrote {len(test_cases)} test cases to {JSONL_FILE}")
```

### Test Case Schema

```json
{
  "test_case_id": "TC-AUTH-001",
  "title": "Login with valid credentials",
  "feature_area": "Authentication",
  "priority": "Critical",
  "preconditions": "User has a valid account; Browser is open; App is accessible at <URL>",
  "test_steps": "1. Navigate to the login page\n2. Enter username: testuser@example.com\n3. Enter password: ********\n4. Click the 'Sign In' button",
  "test_data": "Username: testuser@example.com, Password: (valid password)",
  "expected_result": "User is redirected to the dashboard with welcome message",
  "validation_points": "Dashboard displays; User name shows in header; Menu options available",
  "playwright_commands": "playwright-cli open <url>/login\nplaywright-cli fill e5 \"testuser@example.com\"\nplaywright-cli fill e7 \"****\"\nplaywright-cli click e9",
  "screenshots": "TC-AUTH-001-login.png; TC-AUTH-001-dashboard.png",
  "status": "Not Started",
  "comments": ""
}
```

---

## Feature Processing Workflow

### Step 1: Announce Feature Start

```
═══════════════════════════════════════════════════════════════
[N/Total] FEATURE: <Feature Name>
Type: <feature_type> | URL: <feature_url>
Purpose: <what users do here>
═══════════════════════════════════════════════════════════════
```

### Step 2: Explore via Playwright

```bash
playwright-cli open <FEATURE_URL>
playwright-cli snapshot --filename=snapshots/feature-<name>.yaml
playwright-cli screenshot --filename=screenshots/feature-<name>-initial.png
```

### Step 3: Plan Test Coverage

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

### Step 4: Generate and Write Test Cases

For each batch:
1. Interact with elements
2. Observe behavior
3. Generate test cases
4. **Write to JSONL immediately**
5. Report progress

### Step 5: Feature Completion Checkpoint

```
───────────────────────────────────────────────────────────────
FEATURE COMPLETE: <Feature Name>
   Batches processed: <total_batches>
   User workflows covered: <workflow_count>
   Test cases written to JSONL: <total_tests> (TC-XXX-001 to TC-XXX-NNN)
   Screenshots captured: <count>
   JSONL file: uat_<project>.jsonl
   ✓ All test cases for this feature are ALREADY in the JSONL file
───────────────────────────────────────────────────────────────
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
    write_test_cases_to_jsonl(test_cases)
    
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
- [ ] **Test cases written to JSONL file** (not held in memory)
- [ ] Progress checkpoint displayed

---

## Deep Exploration Checklist (Mandatory)

- [ ] Every dropdown/radio group tested with EACH option individually
- [ ] Cancel flows tested on every delete/destructive confirmation dialog
- [ ] Default field values verified on form open
- [ ] Numeric input boundary values tested (min and max)
- [ ] Summary/dashboard counts cross-validated against list page
- [ ] Empty/unassigned states tested alongside populated states
- [ ] Modals explored deeply — sub-elements, calculated fields
- [ ] Multi-step wizards walked with each branching option
