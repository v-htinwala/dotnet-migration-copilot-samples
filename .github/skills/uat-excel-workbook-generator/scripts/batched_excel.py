"""
Batched Excel Workbook Generator
Generates Excel workbooks using incremental writes to prevent timeouts.

USAGE:
    from batched_excel import (
        create_workbook_with_headers,
        append_rows_batch,
        add_sheet_to_workbook,
        finalize_workbook,
        calculate_batch_size,
        estimate_characters
    )

PURPOSE:
    Prevents timeouts when generating large Excel files by:
    1. Creating workbook with headers first (small operation)
    2. Calculating batch size based on CHARACTER LENGTH (not row count!)
    3. Appending rows in character-limited batches
    4. Saving after each batch (prevents memory accumulation)

CRITICAL INSIGHT:
    LLM context limits are CHARACTER-BASED, not row-based!
    - 5 UAT test cases × 1500 chars = 7,500 chars = NEEDS BATCHING
    - 100 simple rows × 50 chars = 5,000 chars = borderline
    
    Always estimate characters FIRST, then determine batch size.

CHARACTER THRESHOLDS:
    - < 5,000 chars: Safe for inline generation
    - 5,000 - 15,000 chars: Use JSON intermediate file
    - > 15,000 chars: MUST use batched append
    
MAX_CHARS_PER_BATCH = 8,000 (optimized for fewer saves while staying safe)
"""

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from typing import List, Tuple, Dict, Any, Optional
import os

# Configuration - CHARACTER-BASED (not row-based!)
MAX_CHARS_PER_BATCH = 8000  # Optimized: increased from 4000 for fewer saves
DEFAULT_CHARS_PER_ROW = 500  # Default estimate if unknown


def estimate_characters(rows: List[Tuple]) -> Tuple[int, int]:
    """
    Estimate total characters and average per row.
    
    Args:
        rows: List of row tuples
    
    Returns:
        (total_chars, avg_chars_per_row)
    """
    if not rows:
        return 0, DEFAULT_CHARS_PER_ROW
    
    total = sum(sum(len(str(field)) for field in row) for row in rows)
    avg = total // len(rows)
    
    return total, avg


def calculate_batch_size(rows: List[Tuple], max_chars: int = MAX_CHARS_PER_BATCH) -> int:
    """
    Calculate optimal batch size based on CHARACTER LENGTH.
    
    Args:
        rows: Sample rows to estimate from
        max_chars: Maximum characters per batch
    
    Returns:
        Recommended batch size (number of rows)
    """
    if not rows:
        return 10
    
    # Sample first few rows to estimate
    sample_size = min(5, len(rows))
    sample = rows[:sample_size]
    
    _, avg_chars = estimate_characters(sample)
    
    # Calculate batch size with safety margin
    batch_size = max(1, int(max_chars / max(avg_chars, 100)))
    
    # Cap at reasonable limits
    return min(batch_size, 50)  # Never more than 50 rows even if small


def create_styles() -> Dict[str, Any]:
    """Create common styles for Excel formatting."""
    return {
        'header_font': Font(bold=True, color="FFFFFF", size=11),
        'header_fill': PatternFill("solid", fgColor="4472C4"),
        'title_font': Font(bold=True, size=14),
        'section_font': Font(bold=True, size=12),
        'wrap_alignment': Alignment(wrap_text=True, vertical="top"),
        'center_alignment': Alignment(horizontal="center", vertical="center", wrap_text=True),
        'thin_border': Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
    }


def create_workbook_with_headers(
    filepath: str,
    sheet_name: str,
    headers: List[str],
    col_widths: List[int] = None
) -> str:
    """
    Phase 1: Create a new workbook with formatted headers only.
    
    Args:
        filepath: Path to save the Excel file
        sheet_name: Name of the first sheet
        headers: List of column header strings
        col_widths: Optional list of column widths (default: 15 for all)
    
    Returns:
        Path to the created file
    """
    if col_widths is None:
        col_widths = [15] * len(headers)
    
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    styles = create_styles()
    
    # Add formatted headers
    for col, (header, width) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = styles['header_font']
        cell.fill = styles['header_fill']
        cell.alignment = styles['center_alignment']
        cell.border = styles['thin_border']
        ws.column_dimensions[get_column_letter(col)].width = width
    
    ws.freeze_panes = "A2"
    
    wb.save(filepath)
    wb.close()
    
    print(f"✓ Created workbook: {filepath}")
    print(f"  Sheet: {sheet_name} | Headers: {len(headers)} columns")
    
    return filepath


def append_rows_batch(
    filepath: str,
    rows: List[Tuple],
    sheet_name: str = None,
    batch_id: int = None
) -> int:
    """
    Phase 2: Append a batch of rows to existing workbook.
    
    Args:
        filepath: Path to existing Excel file
        rows: List of row tuples to append
        sheet_name: Target sheet (default: active sheet)
        batch_id: Optional batch identifier for logging
    
    Returns:
        Number of rows written
    """
    if not rows:
        return 0
    
    wb = load_workbook(filepath)
    ws = wb.active if sheet_name is None else wb[sheet_name]
    styles = create_styles()
    
    start_row = ws.max_row + 1
    
    for i, row_data in enumerate(rows):
        for col, value in enumerate(row_data, 1):
            cell = ws.cell(row=start_row + i, column=col, value=value)
            cell.alignment = styles['wrap_alignment']
            cell.border = styles['thin_border']
    
    wb.save(filepath)
    wb.close()
    
    batch_info = f" (Batch {batch_id})" if batch_id else ""
    print(f"  ✓ Appended {len(rows)} rows{batch_info} | Total: {start_row + len(rows) - 2} rows")
    
    return len(rows)


def add_sheet_to_workbook(
    filepath: str,
    sheet_name: str,
    headers: List[str],
    col_widths: List[int] = None,
    rows: List[Tuple] = None
) -> str:
    """
    Add a new sheet with optional data to existing workbook.
    
    Args:
        filepath: Path to existing Excel file
        sheet_name: Name for the new sheet
        headers: List of column headers
        col_widths: Optional column widths
        rows: Optional data rows
    
    Returns:
        Path to the file
    """
    if col_widths is None:
        col_widths = [15] * len(headers)
    
    wb = load_workbook(filepath)
    ws = wb.create_sheet(sheet_name)
    styles = create_styles()
    
    # Add headers
    for col, (header, width) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = styles['header_font']
        cell.fill = styles['header_fill']
        cell.alignment = styles['center_alignment']
        cell.border = styles['thin_border']
        ws.column_dimensions[get_column_letter(col)].width = width
    
    # Add rows if provided
    if rows:
        for row_num, row_data in enumerate(rows, 2):
            for col, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_num, column=col, value=value)
                cell.alignment = styles['wrap_alignment']
                cell.border = styles['thin_border']
    
    ws.freeze_panes = "A2"
    
    wb.save(filepath)
    wb.close()
    
    row_count = len(rows) if rows else 0
    print(f"✓ Added sheet: {sheet_name} | {row_count} rows")
    
    return filepath


def add_data_validation(
    filepath: str,
    sheet_name: str,
    column_letter: str,
    values: List[str],
    start_row: int = 2,
    end_row: int = 1000
):
    """
    Add dropdown data validation to a column.
    
    Args:
        filepath: Path to Excel file
        sheet_name: Target sheet name
        column_letter: Column to apply validation (e.g., "E")
        values: List of allowed values
        start_row: First row to apply validation
        end_row: Last row to apply validation
    """
    wb = load_workbook(filepath)
    ws = wb[sheet_name]
    
    values_str = ",".join(values)
    dv = DataValidation(
        type="list",
        formula1=f'"{values_str}"',
        allow_blank=True
    )
    dv.error = "Please select from the list"
    dv.errorTitle = "Invalid Entry"
    
    ws.add_data_validation(dv)
    dv.add(f"{column_letter}{start_row}:{column_letter}{end_row}")
    
    wb.save(filepath)
    wb.close()
    
    print(f"✓ Added validation to {column_letter}{start_row}:{column_letter}{end_row}")


def finalize_workbook(filepath: str, add_summary: bool = False, categories: List[Tuple] = None):
    """
    Phase 3: Finalize workbook with optional summary sheet.
    
    Args:
        filepath: Path to Excel file
        add_summary: Whether to add a summary dashboard
        categories: List of (category_name, count) for summary
    """
    if not add_summary or not categories:
        print(f"✓ Workbook finalized: {filepath}")
        return
    
    wb = load_workbook(filepath)
    
    # Create Summary Dashboard
    ws = wb.create_sheet("Summary Dashboard", 0)  # Insert at beginning
    styles = create_styles()
    
    # Title
    ws['A1'] = "Summary Dashboard"
    ws['A1'].font = styles['title_font']
    ws.merge_cells('A1:E1')
    
    # Headers
    summary_headers = ['Category', 'Total', 'Completed', 'Pending', '% Complete']
    for col, header in enumerate(summary_headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = styles['header_font']
        cell.fill = styles['header_fill']
        cell.border = styles['thin_border']
        ws.column_dimensions[get_column_letter(col)].width = 18
    
    # Data rows
    for row, (category, count) in enumerate(categories, 4):
        ws.cell(row=row, column=1, value=category).border = styles['thin_border']
        ws.cell(row=row, column=2, value=count).border = styles['thin_border']
        ws.cell(row=row, column=3, value=0).border = styles['thin_border']
        ws.cell(row=row, column=4, value=count).border = styles['thin_border']
        pct_cell = ws.cell(row=row, column=5, value=f"=IFERROR(C{row}/B{row}, 0)")
        pct_cell.border = styles['thin_border']
        pct_cell.number_format = '0%'
    
    wb.save(filepath)
    wb.close()
    
    print(f"✓ Workbook finalized with Summary Dashboard: {filepath}")


def verify_workbook(filepath: str) -> Dict[str, Any]:
    """
    Verify workbook contents and return summary.
    
    Args:
        filepath: Path to Excel file
    
    Returns:
        Dictionary with verification results
    """
    if not os.path.exists(filepath):
        return {"error": f"File not found: {filepath}"}
    
    wb = load_workbook(filepath)
    
    result = {
        "filepath": filepath,
        "sheets": {},
        "total_rows": 0
    }
    
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        row_count = ws.max_row - 1  # Exclude header
        col_count = ws.max_column
        result["sheets"][sheet_name] = {
            "rows": row_count,
            "columns": col_count
        }
        result["total_rows"] += row_count
    
    wb.close()
    
    print(f"\n{'='*50}")
    print(f"Verification: {filepath}")
    print(f"{'='*50}")
    for sheet, info in result["sheets"].items():
        print(f"  {sheet}: {info['rows']} rows, {info['columns']} columns")
    print(f"{'='*50}")
    print(f"Total data rows: {result['total_rows']}")
    
    return result


# =============================================================================
# CONVENIENCE FUNCTION: Generate workbook from list in batches
# =============================================================================

def generate_workbook_batched(
    filepath: str,
    sheet_name: str,
    headers: List[str],
    col_widths: List[int],
    all_rows: List[Tuple],
    max_chars_per_batch: int = MAX_CHARS_PER_BATCH
) -> str:
    """
    Convenience function: Generate complete workbook using CHARACTER-BASED batching.
    
    Args:
        filepath: Output path
        sheet_name: Main sheet name
        headers: Column headers
        col_widths: Column widths
        all_rows: All data rows
        max_chars_per_batch: Max characters per batch (default 4000)
    
    Returns:
        Path to generated file
    """
    # Step 0: Estimate characters and calculate batch size
    total_chars, avg_chars = estimate_characters(all_rows)
    batch_size = calculate_batch_size(all_rows, max_chars_per_batch)
    
    print(f"Character Analysis:")
    print(f"  Total rows: {len(all_rows)}")
    print(f"  Total characters: {total_chars:,}")
    print(f"  Avg chars/row: {avg_chars}")
    print(f"  Calculated batch size: {batch_size} rows")
    print(f"  Batches needed: {(len(all_rows) + batch_size - 1) // batch_size}")
    print()
    
    # Step 1: Create with headers
    create_workbook_with_headers(filepath, sheet_name, headers, col_widths)
    
    # Step 2: Append in CHARACTER-BASED batches
    total_batches = (len(all_rows) + batch_size - 1) // batch_size
    
    for i in range(0, len(all_rows), batch_size):
        batch = all_rows[i:i + batch_size]
        batch_num = i // batch_size + 1
        batch_chars = sum(sum(len(str(f)) for f in row) for row in batch)
        append_rows_batch(filepath, batch, sheet_name, batch_id=batch_num)
        print(f"    Batch {batch_num}/{total_batches}: {len(batch)} rows, ~{batch_chars:,} chars")
    
    print(f"\n✓ Complete: {filepath}")
    return filepath


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Batched Excel Generator (Character-Based)')
    parser.add_argument('--output', '-o', default='workbook.xlsx', help='Output file')
    parser.add_argument('--verify', '-v', action='store_true', help='Verify after creation')
    parser.add_argument('--demo', action='store_true', help='Generate demo workbook')
    parser.add_argument('--demo-uat', action='store_true', help='Generate UAT-style demo (high chars/row)')
    
    args = parser.parse_args()
    
    if args.demo:
        # Demo: Simple data (low chars per row)
        headers = ["ID", "Name", "Category", "Status", "Value"]
        widths = [10, 30, 15, 12, 12]
        
        sample_rows = [
            (f"ID-{i:03d}", f"Item {i}", f"Cat-{i % 5}", "Active", i * 10)
            for i in range(1, 51)
        ]
        
        print("=== DEMO: Simple Data (low chars/row) ===\n")
        generate_workbook_batched(args.output, "Data", headers, widths, sample_rows)
    
    elif args.demo_uat:
        # Demo: UAT test cases (HIGH chars per row - simulates real scenario)
        headers = ["TC ID", "Title", "Feature", "Priority", "Preconditions", 
                   "Test Steps", "Test Data", "Expected Result", "Validation"]
        widths = [12, 40, 20, 10, 35, 50, 35, 35, 40]
        
        # Each row ~800-1200 characters (realistic UAT test case)
        sample_rows = [
            (
                f"TC-UAT-{i:03d}",
                f"Verify user can complete action {i} with valid data in the system",
                f"Module {chr(65 + i % 5)}",
                ["Critical", "High", "Medium", "Low"][i % 4],
                f"User is logged in with valid credentials. System is in ready state. Previous test case TC-UAT-{i-1:03d} has passed. Test data has been prepared.",
                f"1. Navigate to the {chr(65 + i % 5)} module dashboard\n2. Click on 'New Action' button\n3. Fill in required field A with value 'TEST_VALUE_{i}'\n4. Fill in required field B with date '2026-01-{(i % 28) + 1:02d}'\n5. Select option from dropdown\n6. Click Submit button\n7. Verify confirmation dialog\n8. Click Confirm",
                f"Field A: TEST_VALUE_{i}\nField B: 2026-01-{(i % 28) + 1:02d}\nDropdown: Option {i % 5 + 1}\nUser: test.user{i}@example.com",
                f"Action {i} is created successfully. Confirmation message displays: 'Action created with ID ACTION_{i:04d}'. User is redirected to action list page.",
                f"1. Confirmation toast appears within 3 seconds\n2. New action appears in list with correct status 'Pending'\n3. All entered data is displayed correctly\n4. Audit log shows creation timestamp"
            )
            for i in range(1, 11)  # Only 10 rows but ~10,000 characters!
        ]
        
        print("=== DEMO: UAT Test Cases (HIGH chars/row) ===\n")
        print("Notice: Only 10 rows but requires multiple batches due to character length!\n")
        generate_workbook_batched(args.output, "Test Cases", headers, widths, sample_rows)
    
    if args.verify:
        verify_workbook(args.output)
