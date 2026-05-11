# Batched Excel Generation Guide

> **Use this guide when generating workbooks with large data to prevent timeouts.**

## Why Batching is Required

LLM context windows have character limits. Generating large inline Python arrays causes timeouts because:
1. The LLM must hold entire data structure in context
2. Single-save operations block until complete
3. Memory pressure increases with data size

## Character-Based Batching (Critical)

> ⚠️ **Batch by CHARACTER LENGTH, not row count!**
> 5 UAT test cases with 1200 chars each = 6,000 chars = TIMEOUT RISK

### Character Thresholds

| Estimated Total Characters | Strategy |
|---------------------------|----------|
| < 5,000 chars | Generate inline, single save |
| 5,000 - 15,000 chars | Write to JSON file, then generate |
| > 15,000 chars | **Batched processing required** |

### Character Estimation Formula

```
Estimated chars = num_rows × avg_chars_per_row

Typical avg_chars_per_row:
- Simple data export: 100-200 chars/row
- UAT test cases: 500-1500 chars/row (due to steps, preconditions)
- Detailed reports: 300-800 chars/row
```

### Quick Estimation Table

| Data Type | Chars/Row | 10 Rows | 50 Rows | 100 Rows |
|-----------|-----------|---------|---------|----------|
| Simple list | ~150 | 1.5K ✅ | 7.5K 📄 | 15K ⚠️ |
| Data export | ~300 | 3K ✅ | 15K ⚠️ | 30K 🔴 |
| **UAT test case** | ~1000 | 10K 📄 | 50K 🔴 | 100K 🔴 |
| Detailed report | ~600 | 6K 📄 | 30K 🔴 | 60K 🔴 |

**Legend**: ✅ Inline OK | 📄 Use JSON | ⚠️ Consider batch | 🔴 **Must batch**

---

## Anti-Patterns (NEVER Do These)

### ❌ WRONG: Generating Inline Python for Large Data

```python
# This causes timeout with 100+ rows or high-char content
rows = [
    ("TC-001", "Test 1", "Module A", ...),  # Row 1
    ("TC-002", "Test 2", "Module A", ...),  # Row 2
    # ... hundreds more rows inline
]
```

### ✅ CORRECT: File-Based or Batched Approach

```python
# Write data to JSON first, then process
import json
with open("test_cases.json", "w") as f:
    json.dump(test_cases_list, f)

# Then use script to generate Excel from JSON
from scripts.generate_excel import generate_from_json
generate_from_json("test_cases.json", "output.xlsx")
```

---

## Batched Generation Pattern

### Step 1: Create Workbook with Headers

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

def create_workbook_with_headers(filepath: str, sheet_name: str, headers: list, col_widths: list):
    """Create workbook with formatted headers only."""
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="4472C4")
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    
    for col, (header, width) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col)].width = width
    
    ws.freeze_panes = "A2"
    wb.save(filepath)
    wb.close()
```

### Step 2: Append Rows in Batches

```python
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Side

def append_rows_batch(filepath: str, rows: list, sheet_name: str = None):
    """Append a batch of rows to existing workbook."""
    wb = load_workbook(filepath)
    ws = wb.active if sheet_name is None else wb[sheet_name]
    
    start_row = ws.max_row + 1
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    wrap_align = Alignment(wrap_text=True, vertical="top")
    
    for i, row_data in enumerate(rows):
        for col, value in enumerate(row_data, 1):
            cell = ws.cell(row=start_row + i, column=col, value=value)
            cell.border = thin_border
            cell.alignment = wrap_align
    
    wb.save(filepath)
    wb.close()
    return len(rows)
```

### Step 3: Character-Aware Batch Size Calculation

```python
MAX_CHARS_PER_BATCH = 4000

def estimate_characters(rows: list) -> tuple:
    """Estimate total and average characters per row."""
    total = sum(sum(len(str(cell)) for cell in row) for row in rows)
    avg = total // len(rows) if rows else 0
    return total, avg

def calculate_batch_size(rows: list) -> int:
    """Calculate optimal batch size based on character content."""
    if not rows:
        return 50
    
    total_chars, avg_chars = estimate_characters(rows)
    
    if avg_chars == 0:
        return 50
    
    batch_size = MAX_CHARS_PER_BATCH // avg_chars
    return max(1, min(batch_size, 100))  # Between 1 and 100
```

### Complete Example: UAT Test Cases

```python
def generate_uat_workbook_batched(filepath: str, all_test_cases: list):
    """Generate UAT workbook using character-aware batching."""
    
    headers = [
        "Test Case ID", "Title", "Feature Area", "Priority", "Preconditions",
        "Test Steps", "Test Data", "Expected Result", "Status", "Comments"
    ]
    col_widths = [14, 45, 22, 10, 40, 55, 40, 40, 12, 30]
    
    # Step 1: Estimate characters
    total_chars, avg_chars = estimate_characters(all_test_cases)
    print(f"Total: {total_chars} chars, Avg: {avg_chars} chars/row")
    
    # Step 2: Calculate batch size
    batch_size = calculate_batch_size(all_test_cases)
    print(f"Batch size: {batch_size} rows")
    
    # Step 3: Create workbook with headers
    create_workbook_with_headers(filepath, "Test Cases", headers, col_widths)
    
    # Step 4: Append in batches
    total_written = 0
    for i in range(0, len(all_test_cases), batch_size):
        batch = all_test_cases[i:i + batch_size]
        written = append_rows_batch(filepath, batch)
        total_written += written
        print(f"  Batch {i//batch_size + 1}: Written {written} rows")
    
    print(f"✓ Generated: {filepath} with {total_written} rows")
```

---

## Why 5 UAT Test Cases Need Batching

```python
# 5 UAT test cases - looks small, right?
test_cases = [
    ("TC-001", "Long title...", "Module", "High", 
     "Long preconditions text about 200 chars...",
     "1. Step one\n2. Step two\n3. Step three... about 400 chars",
     "Test data about 150 chars...",
     "Expected result about 200 chars...",
     "Validation points about 150 chars..."),
    # ... 4 more similar rows
]

# Character analysis:
total_chars, avg_chars = estimate_characters(test_cases)
# Output: Total: 6,500 chars, Avg: 1,300 chars/row

# Even with just 5 rows, we need batching!
batch_size = calculate_batch_size(test_cases)
# Output: Recommended batch size: 3 rows (4000 / 1300 ≈ 3)

# 5 test cases = 2 batches, NOT 1!
```

---

## Script Reference

Use [scripts/batched_excel.py](../scripts/batched_excel.py) for production batched generation:

```bash
# Demo with simple data
python scripts/batched_excel.py --demo

# Demo with high chars/row (UAT-like)
python scripts/batched_excel.py --demo-uat
```
