# Batched Excel Generation Guide

> **Use this guide when converting JSONL to Excel in Phase 3.**

---

## Why Batching is Required

LLM context windows have character limits. Generating large inline Python arrays causes timeouts because:
1. The LLM must hold entire data structure in context
2. Single-save operations block until complete
3. Memory pressure increases with data size

---

## Character-Based Batching

> ⚠️ **Batch by CHARACTER LENGTH, not row count!**
> 5 UAT test cases with 1200 chars each = 6,000 chars = TIMEOUT RISK

### Character Thresholds

| Estimated Total Characters | Strategy |
|---------------------------|----------|
| < 5,000 chars | Generate inline, single save |
| 5,000 - 15,000 chars | Write to JSON file, then process |
| > 15,000 chars | **Batched processing required** |

### Character Estimation

```
Estimated chars = num_rows × avg_chars_per_row

Typical avg_chars_per_row:
- Simple data export: 100-200 chars/row
- UAT test cases: 500-1500 chars/row (due to steps, preconditions)
- Detailed reports: 300-800 chars/row
```

### Quick Reference

| Data Type | Chars/Row | 10 Rows | 50 Rows | 100 Rows |
|-----------|-----------|---------|---------|----------|
| Simple list | ~150 | 1.5K ✅ | 7.5K 📄 | 15K ⚠️ |
| Data export | ~300 | 3K ✅ | 15K ⚠️ | 30K 🔴 |
| **UAT test case** | ~1000 | 10K 📄 | 50K 🔴 | 100K 🔴 |
| Detailed report | ~600 | 6K 📄 | 30K 🔴 | 60K 🔴 |

**Legend**: ✅ Inline OK | 📄 Use JSON | ⚠️ Consider batch | 🔴 **Must batch**

---

## JSONL to Excel Conversion

Use the provided `scripts/jsonl_to_excel.py` script:

```bash
python scripts/jsonl_to_excel.py uat_project.jsonl --output UAT_Test_Cases.xlsx --batch-chars 8000
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output` | Output Excel filename | `output.xlsx` |
| `--batch-chars` | Characters per batch | `8000` |
| `--resume` | Resume from progress file | Auto-detected |

### What the Script Does

1. Reads JSONL line-by-line (memory efficient)
2. Groups test cases by `feature_area` into separate sheets
3. Processes in character-based batches
4. Saves incrementally to prevent data loss
5. Creates "Summary Dashboard" with priority breakdown
6. Tracks progress in `.progress` file for resume capability

---

## Resume on Failure

If the conversion fails midway:

```bash
# Just run the same command again — it resumes from last saved batch
python scripts/jsonl_to_excel.py uat_project.jsonl --output UAT_Test_Cases.xlsx
```

The script reads the `.progress` file and continues from where it left off.

---

## Output Structure

### Sheet: All Test Cases
All test cases in order of generation.

### Sheet: [Feature Name]
Test cases grouped by feature area (one sheet per feature).

### Sheet: Summary Dashboard

| Column | Description |
|--------|-------------|
| Feature Area | Feature/module name |
| Total | Total test cases |
| Critical | Critical priority count |
| High | High priority count |
| Medium | Medium priority count |
| Low | Low priority count |
| Not Started | Count not yet started |
| Completed | Count completed |
| % Complete | Completion percentage |

### Sheet: Dropdown Values
Status and Priority options for data validation in Excel.

---

## Manual Batching (If Script Unavailable)

If you can't use the script, process manually in batches:

```python
import json
from openpyxl import Workbook, load_workbook

BATCH_SIZE = 8000  # characters

def process_jsonl_batched(jsonl_file, output_file):
    # Create workbook with headers
    wb = Workbook()
    ws = wb.active
    ws.title = "All Test Cases"
    
    headers = ["Test Case ID", "Title", "Feature Area", "Priority", 
               "Preconditions", "Test Steps", "Test Data", "Expected Result",
               "Validation Points", "Playwright Commands", "Screenshots", 
               "Status", "Comments"]
    ws.append(headers)
    wb.save(output_file)
    
    # Process in batches
    batch = []
    batch_chars = 0
    
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            tc = json.loads(line)
            row = [
                tc.get("test_case_id", ""),
                tc.get("title", ""),
                tc.get("feature_area", ""),
                tc.get("priority", ""),
                tc.get("preconditions", ""),
                tc.get("test_steps", ""),
                tc.get("test_data", ""),
                tc.get("expected_result", ""),
                tc.get("validation_points", ""),
                tc.get("playwright_commands", ""),
                tc.get("screenshots", ""),
                tc.get("status", "Not Started"),
                tc.get("comments", "")
            ]
            
            row_chars = sum(len(str(cell)) for cell in row)
            
            if batch_chars + row_chars > BATCH_SIZE and batch:
                # Write current batch
                wb = load_workbook(output_file)
                ws = wb.active
                for r in batch:
                    ws.append(r)
                wb.save(output_file)
                print(f"✓ Wrote batch of {len(batch)} rows")
                batch = []
                batch_chars = 0
            
            batch.append(row)
            batch_chars += row_chars
    
    # Write final batch
    if batch:
        wb = load_workbook(output_file)
        ws = wb.active
        for r in batch:
            ws.append(r)
        wb.save(output_file)
        print(f"✓ Wrote final batch of {len(batch)} rows")
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Script not found | Install from `scripts/jsonl_to_excel.py` |
| Memory error | Reduce `--batch-chars` to 4000 |
| Encoding error | Ensure JSONL is UTF-8 encoded |
| Excel file locked | Close Excel before running |
| Resume not working | Delete `.progress` file and restart |
