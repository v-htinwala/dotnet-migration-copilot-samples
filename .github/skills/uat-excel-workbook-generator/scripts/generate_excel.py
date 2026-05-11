"""
Excel Workbook Generator Script
Generates professional Excel workbooks with formatting, formulas, and data validation.

USAGE:
    As module:  from generate_excel import generate_workbook, generate_uat_workbook
    CLI:        python generate_excel.py --output report.xlsx --template uat
    
TEMPLATES:
    - uat: UAT test case workbook with tracking columns
    - data: Simple data export with headers
    - report: Multi-sheet report with summary
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from typing import List, Tuple, Dict, Any, Optional
import argparse
import json
import os


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


def create_header_row(ws, headers: List[str], col_widths: List[int], styles: Dict, row: int = 1):
    """Create a formatted header row."""
    for col, (header, width) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.font = styles['header_font']
        cell.fill = styles['header_fill']
        cell.alignment = styles['center_alignment']
        cell.border = styles['thin_border']
        ws.column_dimensions[get_column_letter(col)].width = width


def add_data_rows(ws, data: List[Tuple], styles: Dict, start_row: int = 2):
    """Add data rows with formatting."""
    for row_num, row_data in enumerate(data, start_row):
        for col_num, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_num, value=value)
            cell.alignment = styles['wrap_alignment']
            cell.border = styles['thin_border']


# =============================================================================
# UAT TEST CASE WORKBOOK TEMPLATE
# =============================================================================

def generate_uat_workbook(
    output_file: str,
    test_cases: List[Tuple],
    feature_areas: List[Tuple[str, int]]
) -> str:
    """
    Generate a UAT test case workbook with tracking columns.
    
    Args:
        output_file: Path to save the Excel file
        test_cases: List of tuples containing test case data
                   (id, title, feature_area, priority, preconditions,
                    test_steps, test_data, expected_result, validation_points)
        feature_areas: List of tuples (feature_name, count)
    
    Returns:
        Path to the generated file
    """
    wb = Workbook()
    styles = create_styles()
    
    # Sheet 1: Test Cases
    _create_uat_test_cases_sheet(wb, test_cases, styles)
    
    # Sheet 2: Summary Dashboard
    _create_uat_summary_sheet(wb, feature_areas, styles)
    
    # Sheet 3: Dropdown Values
    _create_uat_dropdown_sheet(wb, styles)
    
    wb.save(output_file)
    return output_file


def _create_uat_test_cases_sheet(wb: Workbook, test_cases: List[Tuple], styles: Dict):
    """Create the main Test Cases sheet."""
    ws = wb.active
    ws.title = "Test Cases"
    
    headers = [
        "Test Case ID", "Title", "Feature Area", "Priority", "Preconditions",
        "Test Steps", "Test Data", "Expected Result", "Validation Points",
        "Cycle 1 Status", "Cycle 1 Date", "Cycle 1 Tester",
        "Cycle 2 Status", "Cycle 2 Date", "Cycle 2 Tester",
        "Regression Status", "Regression Date", "Regression Tester",
        "Defect ID", "Defect Severity", "Comments"
    ]
    
    col_widths = [14, 45, 22, 10, 40, 55, 40, 40, 45, 
                  12, 12, 15, 12, 12, 15, 12, 12, 15, 12, 12, 30]
    
    create_header_row(ws, headers, col_widths, styles)
    ws.freeze_panes = "A2"
    
    # Add test cases
    for row_num, tc in enumerate(test_cases, 2):
        for col_num, value in enumerate(tc, 1):
            cell = ws.cell(row=row_num, column=col_num, value=value)
            cell.alignment = styles['wrap_alignment']
            cell.border = styles['thin_border']
        
        # Add default "Not Run" for status columns
        for status_col in [10, 13, 16]:
            cell = ws.cell(row=row_num, column=status_col)
            if not cell.value:
                cell.value = "Not Run"
    
    # Add data validation for status columns
    status_validation = DataValidation(
        type="list",
        formula1="='Dropdown Values'!$A$2:$A$5",
        allow_blank=True
    )
    ws.add_data_validation(status_validation)
    status_validation.add(f"J2:J{len(test_cases) + 1}")
    status_validation.add(f"M2:M{len(test_cases) + 1}")
    status_validation.add(f"P2:P{len(test_cases) + 1}")
    
    return ws


def _create_uat_summary_sheet(wb: Workbook, feature_areas: List[Tuple[str, int]], styles: Dict):
    """Create the Summary Dashboard sheet."""
    ws = wb.create_sheet("Summary Dashboard")
    
    # Title
    ws['A1'] = "UAT Test Cases - Summary Dashboard"
    ws['A1'].font = styles['title_font']
    ws.merge_cells('A1:G1')
    
    # Test Cases by Feature Area
    ws['A3'] = "Test Cases by Feature Area"
    ws['A3'].font = styles['section_font']
    
    feature_headers = ['Feature Area', 'Total', 'Not Run', 'Pass', 'Fail', 'Blocked', 'Pass Rate']
    for col, header in enumerate(feature_headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = styles['header_font']
        cell.fill = styles['header_fill']
        cell.border = styles['thin_border']
        ws.column_dimensions[get_column_letter(col)].width = 18
    
    for row, (feature, count) in enumerate(feature_areas, 5):
        ws.cell(row=row, column=1, value=feature).border = styles['thin_border']
        ws.cell(row=row, column=2, value=count).border = styles['thin_border']
        ws.cell(row=row, column=3, value=f'=COUNTIFS(\'Test Cases\'!C:C,"{feature}",\'Test Cases\'!J:J,"Not Run")').border = styles['thin_border']
        ws.cell(row=row, column=4, value=f'=COUNTIFS(\'Test Cases\'!C:C,"{feature}",\'Test Cases\'!J:J,"Pass")').border = styles['thin_border']
        ws.cell(row=row, column=5, value=f'=COUNTIFS(\'Test Cases\'!C:C,"{feature}",\'Test Cases\'!J:J,"Fail")').border = styles['thin_border']
        ws.cell(row=row, column=6, value=f'=COUNTIFS(\'Test Cases\'!C:C,"{feature}",\'Test Cases\'!J:J,"Blocked")').border = styles['thin_border']
        ws.cell(row=row, column=7, value=f'=IFERROR(D{row}/(D{row}+E{row}),"-")').border = styles['thin_border']
        ws.cell(row=row, column=7).number_format = '0%'
    
    # Total row
    total_row = 5 + len(feature_areas)
    ws.cell(row=total_row, column=1, value="TOTAL").font = Font(bold=True)
    ws.cell(row=total_row, column=1).border = styles['thin_border']
    for col in range(2, 7):
        ws.cell(row=total_row, column=col, value=f'=SUM({get_column_letter(col)}5:{get_column_letter(col)}{total_row-1})').border = styles['thin_border']
    ws.cell(row=total_row, column=7, value=f'=IFERROR(D{total_row}/(D{total_row}+E{total_row}),"-")').border = styles['thin_border']
    ws.cell(row=total_row, column=7).number_format = '0%'
    
    # Priority section
    priority_start = total_row + 3
    ws.cell(row=priority_start, column=1, value="Test Cases by Priority").font = styles['section_font']
    
    for col, header in enumerate(feature_headers, 1):
        header_text = header.replace('Feature Area', 'Priority')
        cell = ws.cell(row=priority_start+1, column=col, value=header_text)
        cell.font = styles['header_font']
        cell.fill = styles['header_fill']
        cell.border = styles['thin_border']
    
    priorities = ['Critical', 'High', 'Medium', 'Low']
    for row_offset, priority in enumerate(priorities):
        row = priority_start + 2 + row_offset
        ws.cell(row=row, column=1, value=priority).border = styles['thin_border']
        ws.cell(row=row, column=2, value=f'=COUNTIF(\'Test Cases\'!D:D,"{priority}")').border = styles['thin_border']
        ws.cell(row=row, column=3, value=f'=COUNTIFS(\'Test Cases\'!D:D,"{priority}",\'Test Cases\'!J:J,"Not Run")').border = styles['thin_border']
        ws.cell(row=row, column=4, value=f'=COUNTIFS(\'Test Cases\'!D:D,"{priority}",\'Test Cases\'!J:J,"Pass")').border = styles['thin_border']
        ws.cell(row=row, column=5, value=f'=COUNTIFS(\'Test Cases\'!D:D,"{priority}",\'Test Cases\'!J:J,"Fail")').border = styles['thin_border']
        ws.cell(row=row, column=6, value=f'=COUNTIFS(\'Test Cases\'!D:D,"{priority}",\'Test Cases\'!J:J,"Blocked")').border = styles['thin_border']
        ws.cell(row=row, column=7, value=f'=IFERROR(D{row}/(D{row}+E{row}),"-")').border = styles['thin_border']
        ws.cell(row=row, column=7).number_format = '0%'
    
    return ws


def _create_uat_dropdown_sheet(wb: Workbook, styles: Dict):
    """Create the Dropdown Values sheet."""
    ws = wb.create_sheet("Dropdown Values")
    
    # Status values
    ws['A1'] = "Status Values"
    ws['A1'].font = Font(bold=True)
    for i, status in enumerate(['Not Run', 'Pass', 'Fail', 'Blocked'], 2):
        ws[f'A{i}'] = status
    
    # Severity values
    ws['C1'] = "Defect Severity"
    ws['C1'].font = Font(bold=True)
    for i, sev in enumerate(['Critical', 'Major', 'Minor', 'Trivial'], 2):
        ws[f'C{i}'] = sev
    
    # Priority values
    ws['E1'] = "Priority"
    ws['E1'].font = Font(bold=True)
    for i, pri in enumerate(['Critical', 'High', 'Medium', 'Low'], 2):
        ws[f'E{i}'] = pri
    
    return ws


# =============================================================================
# GENERIC WORKBOOK GENERATION
# =============================================================================

def generate_workbook(config: Dict[str, Any]) -> str:
    """
    Generate a workbook from configuration dictionary.
    
    Args:
        config: Dictionary containing:
            - output_file: Path to save the Excel file
            - sheets: List of sheet configurations
              - name: Sheet name
              - headers: List of column headers
              - col_widths: List of column widths (optional)
              - rows: List of row data (tuples or lists)
            - freeze_panes: Cell reference for freeze (optional, default "A2")
    
    Returns:
        Path to the generated file
    """
    wb = Workbook()
    styles = create_styles()
    
    sheets = config.get('sheets', [])
    
    for i, sheet_config in enumerate(sheets):
        if i == 0:
            ws = wb.active
            ws.title = sheet_config.get('name', 'Sheet1')
        else:
            ws = wb.create_sheet(sheet_config.get('name', f'Sheet{i+1}'))
        
        headers = sheet_config.get('headers', [])
        col_widths = sheet_config.get('col_widths', [15] * len(headers))
        rows = sheet_config.get('rows', [])
        
        if headers:
            create_header_row(ws, headers, col_widths, styles)
            ws.freeze_panes = config.get('freeze_panes', 'A2')
        
        if rows:
            add_data_rows(ws, rows, styles, start_row=2)
    
    output_file = config.get('output_file', 'workbook.xlsx')
    wb.save(output_file)
    return output_file


def generate_from_json(json_file: str, output_file: str) -> str:
    """Generate workbook from JSON configuration file."""
    with open(json_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    config['output_file'] = output_file
    return generate_workbook(config)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate Excel Workbook')
    parser.add_argument('--output', '-o', default='workbook.xlsx', help='Output Excel file')
    parser.add_argument('--config', '-c', help='JSON configuration file')
    parser.add_argument('--template', '-t', choices=['uat', 'data', 'report'], 
                        default='data', help='Template type')
    args = parser.parse_args()
    
    if args.config and os.path.exists(args.config):
        generate_from_json(args.config, args.output)
        print(f"Generated: {args.output}")
    else:
        # Generate sample workbook
        if args.template == 'uat':
            sample_test_cases = [
                ("TC-FORM-001", "Successful form submission", "Form Module", "Critical",
                 "User is logged in",
                 "1. Navigate to form\n2. Fill required fields\n3. Click Submit\n4. Verify success",
                 "test.user@example.com",
                 "Form submitted successfully, confirmation displayed",
                 "Success message shown; Data saved to database"),
            ]
            sample_features = [("Form Module", 1)]
            generate_uat_workbook(args.output, sample_test_cases, sample_features)
        else:
            sample_config = {
                "output_file": args.output,
                "sheets": [{
                    "name": "Data",
                    "headers": ["ID", "Name", "Status", "Date"],
                    "col_widths": [10, 30, 15, 15],
                    "rows": [
                        ("001", "Sample Item 1", "Active", "2026-01-30"),
                        ("002", "Sample Item 2", "Pending", "2026-01-30"),
                    ]
                }]
            }
            generate_workbook(sample_config)
        
        print(f"Generated: {args.output}")
        print("Use --config to provide your own data configuration.")
