# Excel Templates Reference

Pre-built templates for common Excel workbook patterns.

## Template 1: UAT Test Case Workbook

Best for: User Acceptance Testing documentation with execution tracking.

### Sheet Structure

| Sheet | Purpose |
|-------|---------|
| Test Cases | All test cases with tracking columns |
| Summary Dashboard | Metrics by feature area and priority |
| Dropdown Values | Lists for data validation |

### Test Cases Sheet Columns

| Column | Width | Description |
|--------|-------|-------------|
| Test Case ID | 14 | TC-XXX-NNN format |
| Title | 45 | Descriptive test name |
| Feature Area | 22 | Module/component name |
| Priority | 10 | Critical/High/Medium/Low |
| Preconditions | 40 | Setup requirements |
| Test Steps | 55 | Numbered user actions |
| Test Data | 40 | Anonymized test data |
| Expected Result | 40 | Success criteria |
| Validation Points | 45 | What to verify |
| Cycle 1 Status | 12 | Not Run/Pass/Fail/Blocked |
| Cycle 1 Date | 12 | Execution date |
| Cycle 1 Tester | 15 | Tester name |
| Cycle 2 Status | 12 | Second cycle status |
| Cycle 2 Date | 12 | Second cycle date |
| Cycle 2 Tester | 15 | Second cycle tester |
| Regression Status | 12 | Regression test status |
| Regression Date | 12 | Regression date |
| Regression Tester | 15 | Regression tester |
| Defect ID | 12 | Bug tracking reference |
| Defect Severity | 12 | Critical/Major/Minor/Trivial |
| Comments | 30 | Tester notes |

### Implementation

```python
from excel_workbook_generator.scripts.generate_excel import generate_uat_workbook

test_cases = [
    # (id, title, feature_area, priority, preconditions, 
    #  test_steps, test_data, expected_result, validation_points)
    (
        "TC-FORM-001",
        "Submit form with valid data",
        "User Registration",
        "Critical",
        "User is on registration page",
        "1. Enter username\n2. Enter email\n3. Enter password\n4. Click Submit",
        "Username: TEST_USER_001\nEmail: test.user@example.com",
        "Form submitted successfully, confirmation displayed",
        "Success message shown; User created in database"
    ),
]

feature_areas = [
    ("User Registration", 10),
    ("Login", 8),
    ("Dashboard", 15),
]

generate_uat_workbook("UAT_Test_Cases.xlsx", test_cases, feature_areas)
```

---

## Template 2: Simple Data Export

Best for: Data exports, lists, inventories, simple reports.

### Sheet Structure

| Sheet | Purpose |
|-------|---------|
| Data | Main content with headers and rows |

### Implementation

```python
from excel_workbook_generator.scripts.generate_excel import generate_workbook

config = {
    "output_file": "data_export.xlsx",
    "sheets": [
        {
            "name": "Data",
            "headers": ["ID", "Name", "Category", "Status", "Created Date"],
            "col_widths": [10, 35, 20, 15, 15],
            "rows": [
                ("001", "Item Alpha", "Category A", "Active", "2026-01-30"),
                ("002", "Item Beta", "Category B", "Pending", "2026-01-29"),
                ("003", "Item Gamma", "Category A", "Active", "2026-01-28"),
            ]
        }
    ]
}

generate_workbook(config)
```

---

## Template 3: Multi-Sheet Report

Best for: Reports with multiple data categories and summary.

### Sheet Structure

| Sheet | Purpose |
|-------|---------|
| Summary | Overview metrics and KPIs |
| Category 1 | First data category |
| Category 2 | Second data category |
| Reference | Lookup values |

### Implementation

```python
from excel_workbook_generator.scripts.generate_excel import generate_workbook

config = {
    "output_file": "multi_report.xlsx",
    "sheets": [
        {
            "name": "Summary",
            "headers": ["Metric", "Value", "Target", "Status"],
            "col_widths": [25, 15, 15, 15],
            "rows": [
                ("Total Records", "=COUNTA('Data A'!A:A)-1", "100", ""),
                ("Completed", "=COUNTIF('Data A'!D:D,\"Completed\")", "80", ""),
            ]
        },
        {
            "name": "Data A",
            "headers": ["ID", "Name", "Value", "Status"],
            "col_widths": [10, 30, 15, 15],
            "rows": [
                ("A001", "Record 1", 100, "Completed"),
                ("A002", "Record 2", 200, "Pending"),
            ]
        },
        {
            "name": "Data B",
            "headers": ["ID", "Description", "Amount", "Category"],
            "col_widths": [10, 40, 15, 20],
            "rows": [
                ("B001", "Transaction 1", 500.00, "Sales"),
                ("B002", "Transaction 2", 750.00, "Services"),
            ]
        }
    ]
}

generate_workbook(config)
```

---

## Template 4: Tracking Log

Best for: Activity logs, audit trails, change tracking.

### Sheet Structure

| Sheet | Purpose |
|-------|---------|
| Log | Chronological activity entries |
| Summary | Counts by type/status |

### Columns

| Column | Width | Description |
|--------|-------|-------------|
| Timestamp | 18 | Date and time |
| User | 20 | Who performed action |
| Action | 15 | Action type |
| Description | 50 | Details |
| Status | 12 | Success/Failed/Warning |
| Reference | 15 | Related ID |

### Implementation

```python
from datetime import datetime
from excel_workbook_generator.scripts.generate_excel import generate_workbook

config = {
    "output_file": "activity_log.xlsx",
    "sheets": [
        {
            "name": "Activity Log",
            "headers": ["Timestamp", "User", "Action", "Description", "Status", "Reference"],
            "col_widths": [18, 20, 15, 50, 12, 15],
            "rows": [
                ("2026-01-30 10:30:00", "admin@example.com", "CREATE", "Created new user account", "Success", "USR-001"),
                ("2026-01-30 10:35:00", "admin@example.com", "UPDATE", "Modified user permissions", "Success", "USR-001"),
            ]
        }
    ]
}

generate_workbook(config)
```

---

## Common Formatting Patterns

### Color Schemes

```python
# Microsoft Blue theme
header_fill = PatternFill("solid", fgColor="4472C4")
alt_row_fill = PatternFill("solid", fgColor="D6DCE5")

# Status colors
pass_fill = PatternFill("solid", fgColor="C6EFCE")      # Light green
fail_fill = PatternFill("solid", fgColor="FFC7CE")      # Light red
warning_fill = PatternFill("solid", fgColor="FFEB9C")   # Light yellow
blocked_fill = PatternFill("solid", fgColor="D9D9D9")   # Light gray

# Priority colors
critical_fill = PatternFill("solid", fgColor="FF0000")  # Red
high_fill = PatternFill("solid", fgColor="FFA500")      # Orange
medium_fill = PatternFill("solid", fgColor="FFFF00")    # Yellow
low_fill = PatternFill("solid", fgColor="00FF00")       # Green
```

### Standard Column Widths

| Content Type | Recommended Width |
|--------------|-------------------|
| ID/Code | 10-15 |
| Short text | 15-20 |
| Name/Title | 30-45 |
| Description | 40-55 |
| Status | 12-15 |
| Date | 12-15 |
| Email | 25-30 |
| Comments | 30-50 |

### Number Formats

```python
# Percentage
cell.number_format = '0%'        # 75%
cell.number_format = '0.0%'      # 75.5%

# Currency
cell.number_format = '$#,##0.00' # $1,234.56

# Date
cell.number_format = 'YYYY-MM-DD'     # 2026-01-30
cell.number_format = 'MM/DD/YYYY'     # 01/30/2026
cell.number_format = 'DD-MMM-YYYY'    # 30-Jan-2026

# Numbers
cell.number_format = '#,##0'          # 1,234
cell.number_format = '#,##0.00'       # 1,234.56
```
