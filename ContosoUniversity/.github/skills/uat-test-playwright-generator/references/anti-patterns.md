# Anti-Patterns in UAT Test Generation

Common mistakes to avoid when generating UAT test cases.

---

## UAT vs System Test Anti-Patterns

> **Critical**: UAT validates "Did we build the RIGHT thing?" — System testing validates "Did we build the thing RIGHT?"
> A test that fails UAT qualification must be rewritten, not included in output.

| ❌ System Test (Non-UAT) | ✅ UAT Test | Why It Fails |
|--------------------------|------------|--------------|
| "Verify API returns 200 status" | "Verify search results display on screen" | Tests system internals, not user experience |
| "Check database record has status=1" | "Verify order shows 'Confirmed' status" | Requires database access, not executable by end users |
| "Assert toast component is rendered in DOM" | "Verify success message appears on screen" | References code/DOM, not business language |
| "Trigger handleSave() and verify state" | "Click 'Save' and verify confirmation" | References code functions, not user actions |
| "Verify JWT token is in localStorage" | "Verify user remains logged in after refresh" | Requires dev tools, not visible to users |
| "Check console.log shows no errors" | "Verify page loads without visible errors" | Requires developer tools |
| "POST /api/orders returns order_id" | "Submit order and verify confirmation number displays" | Tests API, not business workflow |

### Non-UAT Keywords to Watch For

If ANY of these appear in your test steps or expected results, rewrite the test:

```
API/HTTP: status code, endpoint, 200, 201, 400, 401, 403, 404, 500,
  request body, response, header, bearer token, curl, postman
Database: SQL, query, table, column, INSERT, UPDATE, record, schema
Code: function, method, class, setState, dispatch, handleClick, DOM, render
Dev Tools: console, debugger, network tab, inspect, stack trace, localStorage
```

---

## Language Anti-Patterns

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Write technical jargon | Use plain business language |
| Reference code/APIs in test steps | Describe user actions and visible results |
| "Trigger the handleSave() event" | "Click the 'Save' button" |
| "Database record inserted with status=1" | "Success message displays: 'Record saved'" |
| "Call GET /api/customers endpoint" | "Search for customer by name" |
| "Assert toast component visible" | "Verify success message appears" |

---

## Exploration Anti-Patterns

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Skip pages or features | Explore EVERY page, menu, and button like a Senior Tester |
| Only test happy paths | Cover negative, boundary, validation, and edge cases |
| Guess what the app does | Use Playwright to ACTUALLY interact and observe |
| Take a single snapshot and assume | Re-snapshot after every interaction to see changes |
| Test one dropdown option and call it done | Test EACH option in every dropdown/radio group individually |
| Only test "confirm delete" | Test BOTH confirm AND cancel on every destructive dialog |
| Ignore default field values | Verify defaults on checkboxes, dates, and numeric inputs |
| Skip numeric boundary testing | Test min and max values on every numeric input |
| Trust dashboard numbers at face value | Cross-validate summary counts against actual list data |
| Only test populated/assigned states | Also test empty/unassigned states |
| Snapshot a modal once and move on | Explore modal sub-elements: line items, calculated fields |
| Walk a wizard once with one option | Walk multi-step wizards with EACH branching option |

---

## Processing Anti-Patterns

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Multiple features at once | One feature at a time (or one subagent per feature) |
| Write directly to Excel in Phase 2 | **Write to JSONL file** |
| Accumulate all test cases in memory | Use subagents OR stream to JSONL after EACH BATCH |
| Write JSONL at the end of all features | Write JSONL after EACH BATCH (or per subagent) |
| Call Excel skill during generation | Use `jsonl_to_excel.py` in Phase 3 |
| Process all features in main context | Delegate to subagents when available |

---

## Output Anti-Patterns

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Vague test data | Specific values: "Test Customer 001", "test@example.com" |
| Generic expected results | Observable outcomes: "Success message appears", "Name shows in list" |
| Missing Playwright commands | Include `playwright-cli` commands for each test |
| No screenshots as evidence | Capture screenshots at key verification points |

---

## ⚠️ Timeout Prevention Checklist

### If Using Subagent Mode

- [ ] Each feature delegated to separate subagent
- [ ] Subagent writes to JSONL before returning
- [ ] Main agent only tracks progress, doesn't hold test cases

### If Using Streaming Mode

- [ ] Test cases for current batch written to JSONL file
- [ ] Progress checkpoint displayed
- [ ] Memory cleared (not holding test cases from previous batches)

### Warning Signs

If you find yourself doing any of these, STOP immediately:

1. Holding test cases for multiple batches/features in memory
2. Planning to write all test cases "at the end"
3. Generating test cases without interacting with the live app
4. Skipping features because "they seem similar"

### Recovery Actions

If you're in a bad state:

1. **Delegate to a subagent** (if available), or
2. **Write current test cases to JSONL immediately**
3. **Clear memory** and proceed with next batch/feature

---

## Common Mistakes by Feature Type

### Forms

| Mistake | Impact | Fix |
|---------|--------|-----|
| Only test valid submission | Miss validation errors | Test empty submit first |
| Skip optional fields | Miss edge cases | Test with and without optional fields |
| One value per field type | Miss format validation | Test multiple formats (email, phone, date) |

### Lists/Tables

| Mistake | Impact | Fix |
|---------|--------|-----|
| Only test with data | Miss empty state | Test with 0, 1, and many records |
| Skip pagination | Miss navigation bugs | Test first, last, middle pages |
| Skip sorting/filtering | Miss data handling | Test each sort column, each filter |

### Workflows

| Mistake | Impact | Fix |
|---------|--------|-----|
| Only happy path | Miss error recovery | Test cancel at each step |
| Skip step validation | Miss partial completion bugs | Submit incomplete at each step |
| One path through wizard | Miss branching logic | Test every branch option |

### Authentication

| Mistake | Impact | Fix |
|---------|--------|-----|
| Only valid login | Miss security tests | Test invalid, empty, injection attempts |
| Skip session handling | Miss timeout bugs | Test session expiry, multiple tabs |
| Skip logout | Miss cleanup bugs | Test logout clears state, back button |

---

## Quality Checklist

Before marking a feature complete, verify:

**UAT Qualification (Mandatory)**
- [ ] All test cases pass the 6-point UAT qualification gate
- [ ] No non-UAT keywords in test steps or expected results
- [ ] Each test validates a business requirement, not a system behavior
- [ ] Each test is executable by an actual business user

**Classification (Mandatory)**
- [ ] Each test case has `test_type` assigned (Functional/End-to-End/Integration/Usability/Business Rules/Regression)
- [ ] Each test case has `coverage_area` assigned (Business Process/User Role/Module/Feature/Compliance)
- [ ] Each test case has `user_role` assigned (End User/Admin/Manager/etc.)
- [ ] Each test case has `business_objective` describing the business value
- [ ] Priority is based on business impact (revenue, compliance, frequency)

**Coverage (Mandatory)**
- [ ] At least 3 positive (happy path) tests
- [ ] At least 3 negative (error handling) tests
- [ ] At least 2 boundary (edge case) tests
- [ ] At least 3 validation tests (if forms exist)
- [ ] At least 1 usability test (loading, feedback)

**Formatting (Mandatory)**
- [ ] Test IDs are sequential (TC-XXX-001, 002, 003...)
- [ ] All test steps use action verbs (Click, Enter, Navigate, Verify)
- [ ] All expected results describe what user SEES
- [ ] Test data is specific, not placeholder
- [ ] Playwright commands are included
- [ ] Screenshots captured for key states
