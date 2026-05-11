# Test Case Templates (Live Web App + Playwright)

Ready-to-use **functional** test case templates written in plain business language for UAT testers, with Playwright CLI commands for verification.

## Writing Principles

These templates follow key principles for UAT test cases:

1. **User-Focused Language**: Test steps describe what the TESTER does, not what the code does
2. **Observable Results**: Expected results describe what the tester should SEE on screen
3. **No Technical Jargon**: No API calls, database queries, or code references
4. **Clear Action Verbs**: Navigate, Click, Enter, Select, Verify, Wait, Observe
5. **Playwright-Verified**: Each test includes CLI commands for automated verification

---

## JSONL Output Format (Intermediate File)

When generating UAT test cases, output to a JSONL file (one JSON object per line) for efficient conversion to Excel.

### File Naming Convention

```
uat_<project_name>.jsonl
```

### Schema (17 Fields)

Each line is a self-contained JSON object with these fields:

```json
{
  "test_case_id": "TC-AUTH-001",
  "title": "Login with valid corporate credentials",
  "feature_area": "Authentication",
  "test_type": "Functional",
  "coverage_area": "Business Process",
  "priority": "Critical",
  "user_role": "End User",
  "business_objective": "Verify users can access the system to perform daily business tasks",
  "preconditions": "User has valid corporate account; Browser allows pop-ups; App is accessible at <URL>",
  "test_steps": "1. Navigate to the application login page\n2. Click the 'Sign In' button\n3. Enter your corporate email address\n4. Enter your password\n5. Complete MFA verification if prompted\n6. Wait for the dashboard to load",
  "test_data": "Email: testuser@company.com / Password: (valid password)",
  "expected_result": "User sees the main dashboard with their name displayed in the header",
  "validation_points": "Login page displays company logo; Dashboard shows user's name; Navigation menu is visible",
  "playwright_commands": "playwright-cli open https://app.example.com/login\nplaywright-cli fill e5 \"testuser@company.com\"\nplaywright-cli fill e7 \"****\"\nplaywright-cli click e9\nplaywright-cli snapshot",
  "screenshots": "TC-AUTH-001-login.png; TC-AUTH-001-dashboard.png",
  "status": "Not Started",
  "comments": ""
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `test_case_id` | string | Yes | Unique ID: `TC-[PREFIX]-NNN` (e.g., TC-AUTH-001) |
| `title` | string | Yes | What the user is trying to accomplish (max 100 chars) |
| `feature_area` | string | Yes | Business feature name for grouping |
| `test_type` | string | Yes | One of: `Functional`, `End-to-End`, `Integration`, `Usability`, `Business Rules`, `Regression` |
| `coverage_area` | string | Yes | One of: `Business Process`, `User Role`, `Module/Feature`, `Compliance` |
| `priority` | string | Yes | One of: `Critical`, `High`, `Medium`, `Low` |
| `user_role` | string | Yes | Persona executing this test (e.g., "End User", "Admin", "Manager") |
| `business_objective` | string | Yes | The business requirement or user goal this test validates |
| `preconditions` | string | Yes | What must be set up BEFORE starting this test (semicolon-separated) |
| `test_steps` | string | Yes | Numbered step-by-step ACTIONS the tester performs (`\n` as separator) |
| `test_data` | string | Yes | Specific values to enter (use test placeholders like TEST_USER_001) |
| `expected_result` | string | Yes | What the tester should SEE when the test passes |
| `validation_points` | string | Yes | Specific items to visually verify (semicolon-separated) |
| `playwright_commands` | string | Yes | Playwright CLI commands that execute/verify this test (`\n` separated) |
| `screenshots` | string | Yes | Screenshot filenames captured as evidence (semicolon-separated) |
| `status` | string | Yes | Default: `Not Started`. Options: `Not Started`, `In Progress`, `Completed`, `Blocked` |
| `comments` | string | Yes | Default: empty string `""` |

### UAT Qualification Reminder

Before writing any test case, verify it passes the **6-point UAT qualification gate** (see [uat-qualification.md](uat-qualification.md)):
1. Business user perspective (not technical)
2. Validates business requirements (not system specs)
3. Uses real-world scenarios and business terminology
4. Executable by actual end users (no dev tools)
5. Verifies business value and user goals
6. Focuses on "what" not "how"

### Writing JSONL (Python Example)

```python
import json

def write_test_case_to_jsonl(filepath: str, test_case: dict):
    """Append a single test case to JSONL file."""
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(json.dumps(test_case, ensure_ascii=False) + '\n')
```

### Converting JSONL to Excel

```bash
python jsonl_to_excel.py uat_myproject.jsonl --output UAT_Test_Cases_MyProject.xlsx --batch-chars 8000
```

---

## Action Verb Reference

| Verb | Use When | Example |
|------|----------|---------|
| **Navigate** | Going to a page or section | Navigate to the Customer Dashboard |
| **Click** | Pressing buttons, links, icons | Click the 'Save' button |
| **Enter** | Typing text into fields | Enter "John Smith" in the Name field |
| **Select** | Choosing from dropdowns, checkboxes | Select "Americas" from Region dropdown |
| **Verify** | Confirming expected outcome | Verify the success message appears |
| **Wait** | Allowing time for processing | Wait for the page to load |
| **Observe** | Noting what appears on screen | Observe the confirmation dialog |
| **Clear** | Removing data from fields | Clear the search field |
| **Scroll** | Moving through page content | Scroll down to the Comments section |
| **Upload** | Attaching files | Upload the test document |

---

## Authentication Templates

### TC-AUTH-001: Login with Valid Credentials
```
TC-AUTH-001 | Login with valid credentials
Feature Area: Authentication
Priority: Critical
Preconditions: User has a valid account; App is accessible at <URL>
Test Steps:
1. Navigate to the application login page
2. Observe the login page displays with branding/logo
3. Enter email address in the email field
4. Enter password in the password field
5. Click the 'Sign In' button
6. Wait for the application to load
7. Verify the dashboard or home page displays
Test Data: Email: testuser@example.com, Password: (valid password)
Expected Result: User sees the main dashboard with their name displayed
Validation Points: Login form visible; Dashboard loads after login; User name in header; Menu available
Playwright Commands:
  playwright-cli open <url>/login
  playwright-cli snapshot
  playwright-cli fill <email-ref> "testuser@example.com"
  playwright-cli fill <password-ref> "****"
  playwright-cli click <login-button-ref>
  playwright-cli snapshot
  playwright-cli screenshot --filename=screenshots/TC-AUTH-001-result.png
Screenshots: TC-AUTH-001-login.png; TC-AUTH-001-result.png
```

### TC-AUTH-002: Invalid Credentials
```
TC-AUTH-002 | Login fails with invalid credentials
Feature Area: Authentication
Priority: Critical
Preconditions: App is accessible at <URL>
Test Steps:
1. Navigate to the login page
2. Enter an invalid email address
3. Enter an incorrect password
4. Click the 'Sign In' button
5. Observe the error message displayed
6. Verify user remains on the login page
Test Data: Email: invalid@example.com, Password: wrongpassword
Expected Result: Error message displays (e.g., "Invalid credentials"); user stays on login page
Validation Points: Error message visible; Login form still displayed; No navigation to dashboard
Playwright Commands:
  playwright-cli open <url>/login
  playwright-cli fill <email-ref> "invalid@example.com"
  playwright-cli fill <password-ref> "wrongpassword"
  playwright-cli click <login-button-ref>
  playwright-cli snapshot
  playwright-cli screenshot --filename=screenshots/TC-AUTH-002-error.png
Screenshots: TC-AUTH-002-error.png
```

### TC-AUTH-003: Empty Fields Validation
```
TC-AUTH-003 | Login form validates empty fields
Feature Area: Authentication
Priority: High
Preconditions: App is accessible at <URL>
Test Steps:
1. Navigate to the login page
2. Leave email and password fields empty
3. Click the 'Sign In' button
4. Observe validation error messages
Test Data: (empty fields)
Expected Result: Validation errors appear for required fields; form is not submitted
Validation Points: Error messages for email and password; Form not submitted; User stays on login page
Playwright Commands:
  playwright-cli open <url>/login
  playwright-cli click <login-button-ref>
  playwright-cli snapshot
  playwright-cli screenshot --filename=screenshots/TC-AUTH-003-validation.png
Screenshots: TC-AUTH-003-validation.png
```

## Dashboard/List Templates

### TC-LIST-001: View List with Data
```
TC-LIST-001 | View list page with records
Feature Area: [Feature Name]
Priority: Critical
Preconditions: User is logged in; Records exist in the system
Test Steps:
1. Navigate to the [Feature Name] page from the menu
2. Wait for the page to fully load
3. Observe the data grid/list displaying records
4. Verify column headers are visible
5. Verify pagination controls appear (if applicable)
Test Data: N/A
Expected Result: Page displays with data grid showing records and expected columns
Validation Points: Page title correct; Column headers visible; Data rows appear; Pagination shows count
Playwright Commands:
  playwright-cli open <url>/<feature-path>
  playwright-cli snapshot
  playwright-cli screenshot --filename=screenshots/TC-LIST-001-loaded.png
Screenshots: TC-LIST-001-loaded.png
```

### TC-LIST-002: Search Records
```
TC-LIST-002 | Search for records using text filter
Feature Area: [Feature Name]
Priority: Critical
Preconditions: User is on the list page with records loaded
Test Steps:
1. Locate the search field
2. Enter a search term
3. Press Enter or click Search
4. Wait for results to refresh
5. Observe that only matching records appear
6. Clear the search field
7. Verify all records display again
Test Data: Search term: "TEST_SEARCH_001"
Expected Result: Grid shows only matching records; clearing search restores all records
Validation Points: Search field accepts input; Grid refreshes; Only matching records shown; Count updates
Playwright Commands:
  playwright-cli fill <search-ref> "TEST_SEARCH_001"
  playwright-cli press Enter
  playwright-cli snapshot
  playwright-cli screenshot --filename=screenshots/TC-LIST-002-results.png
Screenshots: TC-LIST-002-results.png
```

## Form Templates

### TC-FORM-001: Create a New Record
```
TC-FORM-001 | Create a new [Entity] successfully
Feature Area: [Feature Name]
Priority: Critical
Preconditions: User is logged in with create permission; User is on the list page
Test Steps:
1. Click the 'Add New' or 'Create' button
2. Wait for the form to open
3. Enter [Field 1]: [VALUE]
4. Enter [Field 2]: [VALUE]
5. Select [Dropdown]: [VALUE]
6. Click the 'Save' button
7. Wait for save to complete
8. Observe the success message
9. Verify the new record appears in the list
Test Data: Field 1: TEST_VALUE_001, Field 2: TEST_VALUE_002, Dropdown: Option A
Expected Result: New record is created and appears in the list
Validation Points: Form opens; Fields accept input; Save succeeds; Success message; Record in list
Playwright Commands:
  playwright-cli click <add-button-ref>
  playwright-cli snapshot
  playwright-cli fill <field1-ref> "TEST_VALUE_001"
  playwright-cli fill <field2-ref> "TEST_VALUE_002"
  playwright-cli select <dropdown-ref> "Option A"
  playwright-cli click <save-ref>
  playwright-cli snapshot
  playwright-cli screenshot --filename=screenshots/TC-FORM-001-success.png
Screenshots: TC-FORM-001-form.png; TC-FORM-001-success.png
```

### TC-FORM-002: Required Field Validation
```
TC-FORM-002 | Required field validation shows errors
Feature Area: [Feature Name]
Priority: Critical
Preconditions: Create or Edit form is open
Test Steps:
1. Leave all required fields empty
2. Click the 'Save' button
3. Observe validation error messages below each empty field
4. Verify the form did not save
Test Data: Empty required fields
Expected Result: Validation errors display for each required field; form is not submitted
Validation Points: Red error messages/borders on required fields; Error text states field is required; Save blocked
Playwright Commands:
  playwright-cli click <save-ref>
  playwright-cli snapshot
  playwright-cli screenshot --filename=screenshots/TC-FORM-002-validation.png
Screenshots: TC-FORM-002-validation.png
```

### TC-FORM-003: Edit an Existing Record
```
TC-FORM-003 | Edit an existing [Entity] successfully
Feature Area: [Feature Name]
Priority: High
Preconditions: A record exists; User has edit permission
Test Steps:
1. Locate the record in the list
2. Click the Edit button/icon
3. Wait for the edit form to open
4. Observe fields are populated with current values
5. Change [Field Name] to [New Value]
6. Click 'Save'
7. Observe success message
8. Verify updated value in the list
Test Data: Original: TEST_VALUE_001, New: TEST_VALUE_002
Expected Result: Record is updated; list shows new value
Validation Points: Form pre-populates; Changed field saves; Success message; List updated
Playwright Commands:
  playwright-cli click <edit-ref>
  playwright-cli snapshot
  playwright-cli fill <field-ref> "TEST_VALUE_002"
  playwright-cli click <save-ref>
  playwright-cli snapshot
  playwright-cli screenshot --filename=screenshots/TC-FORM-003-updated.png
Screenshots: TC-FORM-003-edit.png; TC-FORM-003-updated.png
```

## Delete Templates

### TC-DEL-001: Delete with Confirmation
```
TC-DEL-001 | Delete a [Entity] after confirming
Feature Area: [Feature Name]
Priority: High
Preconditions: A record exists; User has delete permission
Test Steps:
1. Locate the record in the list
2. Click the Delete button/icon
3. Observe confirmation dialog appears
4. Click 'Confirm' or 'Yes'
5. Wait for deletion to complete
6. Observe success message
7. Verify record no longer in list
Test Data: Record: TEST_RECORD_DELETE_001
Expected Result: Record removed after confirmation
Validation Points: Confirmation dialog appears; Success message; Record gone from list; Count decreases
Playwright Commands:
  playwright-cli click <delete-ref>
  playwright-cli snapshot
  playwright-cli screenshot --filename=screenshots/TC-DEL-001-confirm.png
  playwright-cli dialog-accept
  playwright-cli snapshot
  playwright-cli screenshot --filename=screenshots/TC-DEL-001-deleted.png
Screenshots: TC-DEL-001-confirm.png; TC-DEL-001-deleted.png
```

## File Upload Templates

### TC-FILE-001: Upload Valid File
```
TC-FILE-001 | Upload an allowed file type
Feature Area: Attachments
Priority: High
Preconditions: User has upload permission; Upload feature is accessible
Test Steps:
1. Navigate to the upload section
2. Click 'Upload' or drag-and-drop area
3. Select a valid file
4. Wait for upload to complete
5. Observe success notification
6. Verify file appears in attachment list
Test Data: File: test_document.pdf (1MB)
Expected Result: File uploads and appears in list with correct name and size
Validation Points: Progress indicator shows; Success notification; File name in list; File size correct
Playwright Commands:
  playwright-cli upload ./test-files/test_document.pdf
  playwright-cli snapshot
  playwright-cli screenshot --filename=screenshots/TC-FILE-001-uploaded.png
Screenshots: TC-FILE-001-uploaded.png
```

## Responsive/Layout Templates

### TC-RESP-001: Mobile Layout
```
TC-RESP-001 | Application displays correctly on mobile viewport
Feature Area: Responsive Layout
Priority: Medium
Preconditions: User is logged in; App is loaded
Test Steps:
1. Resize browser to mobile viewport (375x812)
2. Observe navigation adapts (hamburger menu if applicable)
3. Verify content reflows correctly
4. Verify no horizontal scrollbar
5. Test key interactions work on mobile layout
Test Data: Viewport: 375x812
Expected Result: App is usable on mobile; navigation accessible; content readable
Validation Points: Mobile menu works; Content fits viewport; Touch targets adequate; No horizontal scroll
Playwright Commands:
  playwright-cli resize 375 812
  playwright-cli snapshot
  playwright-cli screenshot --filename=screenshots/TC-RESP-001-mobile.png
Screenshots: TC-RESP-001-mobile.png
```

---

## ID Naming Convention

```
TC-[MODULE]-[NUMBER]

Examples:
TC-AUTH-001     Authentication/Login
TC-DASH-001     Dashboard
TC-LIST-001     List/Search pages
TC-FORM-001     Form/Create/Edit
TC-DEL-001      Delete operations
TC-FILE-001     File upload/download
TC-NAV-001      Navigation
TC-RESP-001     Responsive layout
TC-WORK-001     Workflow/Process
TC-SET-001      Settings/Preferences
```

---

## Execution Results Schema

Each line in `execution-results.jsonl`:

```json
{
  "id": "string (test case ID)",
  "executionId": "string (unique execution instance)",
  "executionDate": "ISO 8601 timestamp",
  "status": "pass | fail | blocked | skipped",
  "duration": "number (milliseconds)",
  "tester": "string",
  "build": "string (application version)",
  "environment": {
    "browser": "string",
    "browserVersion": "string",
    "os": "string",
    "viewport": "string (WxH)"
  },
  "stepResults": [
    {
      "step": "number",
      "status": "pass | fail | blocked | skipped",
      "actual": "string (actual result observed)",
      "screenshot": "string (captured screenshot)"
    }
  ],
  "defects": [
    {
      "defectId": "string",
      "summary": "string",
      "severity": "critical | high | medium | low"
    }
  ],
  "notes": "string"
}
```

## Test Suite Summary Schema

```json
{
  "suiteId": "suite-<date>-<module>",
  "suiteName": "string",
  "application": "string",
  "applicationUrl": "string",
  "executionDate": "ISO 8601",
  "environment": {
    "browser": "string",
    "viewport": "string",
    "os": "string"
  },
  "summary": {
    "total": "number",
    "passed": "number",
    "failed": "number",
    "blocked": "number",
    "skipped": "number",
    "passRate": "number"
  },
  "testCaseFile": "string",
  "resultsFile": "string",
  "defects": []
}
```
