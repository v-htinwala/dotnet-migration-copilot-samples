# Excel Formatting Guide

Detailed formatting options, styles, formulas, and patterns for Excel generation.

## Cell Styles

### Fonts

```python
from openpyxl.styles import Font

# Common font styles
header_font = Font(bold=True, color="FFFFFF", size=11)
title_font = Font(bold=True, size=14)
normal_font = Font(size=10)
link_font = Font(color="0563C1", underline="single")
```

### Fills (Background Colors)

```python
from openpyxl.styles import PatternFill

# Semantic colors
header_fill = PatternFill("solid", fgColor="4472C4")   # Blue
success_fill = PatternFill("solid", fgColor="C6EFCE")  # Light green
error_fill = PatternFill("solid", fgColor="FFC7CE")    # Light red
warning_fill = PatternFill("solid", fgColor="FFEB9C")  # Light yellow
neutral_fill = PatternFill("solid", fgColor="F2F2F2")  # Light gray
```

### Alignment

```python
from openpyxl.styles import Alignment

center_align = Alignment(horizontal="center", vertical="center")
wrap_align = Alignment(wrap_text=True, vertical="top")
left_align = Alignment(horizontal="left", vertical="top")
```

### Borders

```python
from openpyxl.styles import Border, Side

thin_border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

thick_bottom = Border(bottom=Side(style='thick'))
```

---

## Column Widths

### Fixed Widths

```python
from openpyxl.utils import get_column_letter

column_widths = [15, 40, 20, 12, 50]

for col, width in enumerate(column_widths, 1):
    ws.column_dimensions[get_column_letter(col)].width = width
```

### Auto-Fit (Approximate)

```python
for col in ws.columns:
    max_length = max(len(str(cell.value or "")) for cell in col)
    ws.column_dimensions[col[0].column_letter].width = min(max_length + 2, 50)
```

---

## Freeze Panes

```python
# Freeze header row
ws.freeze_panes = "A2"

# Freeze first column and header
ws.freeze_panes = "B2"
```

---

## Data Validation (Dropdowns)

### Inline List

```python
from openpyxl.worksheet.datavalidation import DataValidation

status_validation = DataValidation(
    type="list",
    formula1='"Not Started,In Progress,Completed,Blocked"',
    allow_blank=True
)
status_validation.error = "Please select from the list"
status_validation.errorTitle = "Invalid Entry"

ws.add_data_validation(status_validation)
status_validation.add("E2:E100")
```

### Reference to Another Sheet

```python
priority_validation = DataValidation(
    type="list",
    formula1="='Dropdown Values'!$A$2:$A$5"
)
ws.add_data_validation(priority_validation)
priority_validation.add("D2:D100")
```

---

## Formulas

### Count Formulas

```python
# COUNTIF - count matching values
ws['B5'] = '=COUNTIF(A:A,"Completed")'

# COUNTIFS - multiple criteria
ws['B6'] = '=COUNTIFS(A:A,"High",B:B,"Completed")'

# COUNTA - count non-empty
ws['B8'] = '=COUNTA(A2:A100)'
```

### Summary Formulas

```python
ws['B10'] = '=SUM(C2:C100)'
ws['B11'] = '=AVERAGE(C2:C100)'

# Percentage with error handling
ws['B12'] = '=IFERROR(B5/(B5+B6),"-")'
ws['B12'].number_format = '0%'
```

### Conditional Formulas

```python
ws['D2'] = '=IF(C2>100,"High","Low")'
ws['D2'] = '=IF(C2>100,"High",IF(C2>50,"Medium","Low"))'
ws['E2'] = '=IFERROR(B2/C2,0)'
```

---

## Common Patterns

### Header Row with Formatting

```python
def create_header_row(ws, headers, row=1):
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill("solid", fgColor="4472C4")
    center_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
```

### Data Rows with Borders

```python
def add_data_rows(ws, data, start_row=2):
    wrap_align = Alignment(wrap_text=True, vertical="top")
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    
    for row_num, row_data in enumerate(data, start_row):
        for col_num, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_num, value=value)
            cell.alignment = wrap_align
            cell.border = thin_border
```

### Summary Dashboard Sheet

```python
def create_summary_sheet(wb, data_sheet_name, categories):
    ws = wb.create_sheet("Summary")
    
    ws['A1'] = "Summary Dashboard"
    ws['A1'].font = Font(bold=True, size=14)
    
    headers = ["Category", "Total", "Completed", "Pending", "% Complete"]
    create_header_row(ws, headers, row=3)
    
    for row, category in enumerate(categories, 4):
        ws.cell(row=row, column=1, value=category)
        ws.cell(row=row, column=2, value=f'=COUNTIF(\'{data_sheet_name}\'!B:B,"{category}")')
        ws.cell(row=row, column=3, value=f'=COUNTIFS(\'{data_sheet_name}\'!B:B,"{category}",\'{data_sheet_name}\'!C:C,"Completed")')
        ws.cell(row=row, column=4, value=f'=B{row}-C{row}')
        ws.cell(row=row, column=5, value=f'=IFERROR(C{row}/B{row},"-")')
        ws.cell(row=row, column=5).number_format = '0%'
```

---

## Output Verification

```python
from openpyxl import load_workbook

def verify_workbook(filepath):
    wb = load_workbook(filepath)
    print(f"Sheets: {wb.sheetnames}")
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        print(f"  {sheet_name}: {ws.max_row} rows, {ws.max_column} columns")
    wb.close()
```
