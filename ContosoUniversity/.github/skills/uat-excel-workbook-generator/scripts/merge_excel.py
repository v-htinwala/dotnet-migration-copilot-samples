"""
Excel Workbook Merger Script
Merges multiple Excel workbooks into a single file.

USAGE:
    CLI:    python merge_excel.py output.xlsx input1.xlsx input2.xlsx input3.xlsx
    Module: from merge_excel import merge_workbooks
    
STRATEGIES:
    - append: Combine all rows from first sheet of each file into one sheet
    - separate_sheets: Keep each input file as a separate sheet
"""

from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
from typing import List, Optional
import argparse
import os


def merge_workbooks(
    output_file: str,
    input_files: List[str],
    merge_strategy: str = "append",
    primary_sheet: str = "Test Cases"
) -> str:
    """
    Merge multiple Excel workbooks into one.
    
    Args:
        output_file: Path for the merged output file
        input_files: List of input Excel file paths
        merge_strategy: 
            - "append": Combine rows from primary sheet into one sheet
            - "separate_sheets": Keep each file as a separate sheet
        primary_sheet: Name of the sheet to merge (for "append" strategy)
    
    Returns:
        Path to the merged file
    """
    if merge_strategy == "append":
        return _merge_append(output_file, input_files, primary_sheet)
    elif merge_strategy == "separate_sheets":
        return _merge_separate_sheets(output_file, input_files)
    else:
        raise ValueError(f"Unknown merge strategy: {merge_strategy}")


def _merge_append(output_file: str, input_files: List[str], primary_sheet: str) -> str:
    """Merge by appending rows from the primary sheet of each file."""
    
    if not input_files:
        raise ValueError("No input files provided")
    
    # Use first file as base
    base_wb = load_workbook(input_files[0])
    
    if primary_sheet not in base_wb.sheetnames:
        # Try to find the first sheet
        primary_sheet = base_wb.sheetnames[0]
    
    base_ws = base_wb[primary_sheet]
    
    # Get the last row of base worksheet
    last_row = base_ws.max_row
    
    # Append data from other files
    for input_file in input_files[1:]:
        if not os.path.exists(input_file):
            print(f"Warning: File not found, skipping: {input_file}")
            continue
        
        try:
            src_wb = load_workbook(input_file)
            
            if primary_sheet not in src_wb.sheetnames:
                src_sheet = src_wb.sheetnames[0]
            else:
                src_sheet = primary_sheet
            
            src_ws = src_wb[src_sheet]
            
            # Skip header row (row 1), copy data rows
            for row_num in range(2, src_ws.max_row + 1):
                last_row += 1
                for col_num in range(1, src_ws.max_column + 1):
                    src_cell = src_ws.cell(row=row_num, column=col_num)
                    dest_cell = base_ws.cell(row=last_row, column=col_num)
                    dest_cell.value = src_cell.value
                    
                    # Copy styles if present
                    if src_cell.has_style:
                        dest_cell.font = src_cell.font.copy()
                        dest_cell.fill = src_cell.fill.copy()
                        dest_cell.border = src_cell.border.copy()
                        dest_cell.alignment = src_cell.alignment.copy()
            
            src_wb.close()
            print(f"  Merged: {input_file} ({src_ws.max_row - 1} rows)")
            
        except Exception as e:
            print(f"Warning: Error processing {input_file}: {e}")
    
    # Update summary dashboard if it exists
    if "Summary Dashboard" in base_wb.sheetnames:
        _update_summary_dashboard(base_wb, primary_sheet)
    
    base_wb.save(output_file)
    base_wb.close()
    
    print(f"\nMerged {len(input_files)} files into: {output_file}")
    print(f"Total rows: {last_row - 1}")
    
    return output_file


def _merge_separate_sheets(output_file: str, input_files: List[str]) -> str:
    """Merge by keeping each file as a separate sheet."""
    
    if not input_files:
        raise ValueError("No input files provided")
    
    output_wb = Workbook()
    output_wb.remove(output_wb.active)  # Remove default sheet
    
    for input_file in input_files:
        if not os.path.exists(input_file):
            print(f"Warning: File not found, skipping: {input_file}")
            continue
        
        try:
            src_wb = load_workbook(input_file)
            
            # Get base name for sheet naming
            base_name = os.path.splitext(os.path.basename(input_file))[0][:30]
            
            for src_sheet_name in src_wb.sheetnames:
                src_ws = src_wb[src_sheet_name]
                
                # Create unique sheet name
                sheet_name = f"{base_name}_{src_sheet_name}"[:31]
                dest_ws = output_wb.create_sheet(sheet_name)
                
                # Copy all cells
                for row in src_ws.iter_rows():
                    for cell in row:
                        dest_cell = dest_ws.cell(row=cell.row, column=cell.column)
                        dest_cell.value = cell.value
                        
                        if cell.has_style:
                            dest_cell.font = cell.font.copy()
                            dest_cell.fill = cell.fill.copy()
                            dest_cell.border = cell.border.copy()
                            dest_cell.alignment = cell.alignment.copy()
                
                # Copy column widths
                for col_letter, col_dim in src_ws.column_dimensions.items():
                    dest_ws.column_dimensions[col_letter].width = col_dim.width
            
            src_wb.close()
            print(f"  Added sheets from: {input_file}")
            
        except Exception as e:
            print(f"Warning: Error processing {input_file}: {e}")
    
    output_wb.save(output_file)
    output_wb.close()
    
    print(f"\nMerged {len(input_files)} files into: {output_file}")
    
    return output_file


def _update_summary_dashboard(wb: Workbook, data_sheet: str):
    """Update the summary dashboard with recalculated feature counts."""
    if "Summary Dashboard" not in wb.sheetnames:
        return
    
    # The formulas in the summary dashboard should auto-recalculate
    # when the workbook is opened in Excel.
    # This function can be expanded to manually recalculate if needed.
    pass


def verify_merge(output_file: str):
    """Verify the merged workbook and print summary."""
    wb = load_workbook(output_file)
    
    print(f"\nVerification of: {output_file}")
    print("-" * 40)
    print(f"Sheets: {', '.join(wb.sheetnames)}")
    
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        print(f"  {sheet_name}: {ws.max_row} rows, {ws.max_column} columns")
    
    wb.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Merge Excel Workbooks')
    parser.add_argument('output', help='Output merged Excel file')
    parser.add_argument('inputs', nargs='+', help='Input Excel files to merge')
    parser.add_argument('--strategy', '-s', choices=['append', 'separate_sheets'],
                        default='append', help='Merge strategy')
    parser.add_argument('--sheet', default='Test Cases', 
                        help='Primary sheet name for append strategy')
    parser.add_argument('--verify', '-v', action='store_true',
                        help='Verify merged file after creation')
    
    args = parser.parse_args()
    
    print(f"Merging {len(args.inputs)} files...")
    print(f"Strategy: {args.strategy}")
    print("-" * 40)
    
    result = merge_workbooks(
        args.output,
        args.inputs,
        merge_strategy=args.strategy,
        primary_sheet=args.sheet
    )
    
    if args.verify:
        verify_merge(result)
