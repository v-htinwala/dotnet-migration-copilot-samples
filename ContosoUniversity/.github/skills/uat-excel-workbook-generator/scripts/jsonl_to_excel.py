"""
JSONL to Excel Converter for UAT Test Cases

Converts canonical 20-field JSONL to formatted Excel workbook with:
- Journey-based sheet grouping
- Traceability Matrix sheet
- Source breakdown in Summary Dashboard
- Hidden empty optional columns
- Resume capability via .progress file
- 8000-char batches for incremental saves

USAGE:
    python jsonl_to_excel.py unified-scenarios.jsonl --output uat-tests.xlsx --batch-chars 8000

    # Resume after failure (automatically detects .progress file):
    python jsonl_to_excel.py unified-scenarios.jsonl --output uat-tests.xlsx

JSONL SCHEMA (canonical 20-field, one JSON object per line):
    {
        "test_id": "UAT-VEH-001",
        "test_name": "Verify vehicle creation with valid data",
        "feature": "Vehicle Management",
        "journey_id": "J-VEH-CRUD",
        "test_type": "Functional",
        "coverage_area": "BusinessProcess",
        "priority": "P1",
        "user_role": "Fleet Manager",
        "preconditions": ["User is logged in", "At least one vehicle type exists"],
        "test_steps": [
            {"step_number": 1, "action": "Navigate to Vehicle page", "expected": "Vehicle list displayed"}
        ],
        "expected_result": "New vehicle appears in the vehicle list",
        "test_data": {"vehicle_name": "Truck-001", "vehicle_type": "Heavy Duty"},
        "business_objective": "Ensure fleet managers can add vehicles",
        "source": "merged",
        "source_evidence": "frame_042 + /vehicles route",
        "requirement_id": "REQ-VEH-101",
        "video_timestamp": "01:23",
        "screenshot_path": "phase-2-url/screenshots/vehicles.png",
        "api_endpoint": "POST /api/vehicles",
        "component_path": "src/pages/vehicles/CreateVehicle.tsx"
    }
"""

import json
import os
import argparse
from typing import List, Dict, Any, Tuple, Optional, Set
from collections import defaultdict, OrderedDict
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# Configuration
MAX_CHARS_PER_BATCH = 8000
PROGRESS_FILE_SUFFIX = ".progress"

# ============================================================================
# Canonical 20-field schema
# ============================================================================
# Ordered by section: Core -> Classification -> Content -> Traceability -> Extended
CANONICAL_FIELDS = [
    # Core identification
    "test_id", "test_name", "feature", "journey_id",
    # Classification
    "test_type", "coverage_area", "priority", "user_role",
    # Test content
    "preconditions", "test_steps", "expected_result", "test_data",
    "business_objective",
    # Source traceability
    "source", "source_evidence", "requirement_id",
    # Extended traceability
    "video_timestamp", "screenshot_path", "api_endpoint", "component_path"
]

CANONICAL_HEADERS = [
    # Core identification
    "Test ID", "Test Name", "Feature", "Journey ID",
    # Classification
    "Test Type", "Coverage Area", "Priority", "User Role",
    # Test content
    "Preconditions", "Test Steps", "Expected Result", "Test Data",
    "Business Objective",
    # Source traceability
    "Source", "Source Evidence", "Requirement ID",
    # Extended traceability
    "Video Timestamp", "Screenshot Path", "API Endpoint", "Component Path"
]

CANONICAL_COL_WIDTHS = [
    # Core
    16, 45, 22, 16,
    # Classification
    14, 18, 10, 16,
    # Content
    40, 55, 40, 35, 35,
    # Traceability
    10, 30, 16,
    # Extended
    14, 30, 22, 35
]

# Status/tracking columns appended after schema columns
TRACKING_HEADERS = ["Status", "Tester", "Execution Date", "Comments"]
TRACKING_COL_WIDTHS = [14, 16, 14, 30]

# Priority colors
PRIORITY_FILLS = {
    "P1": PatternFill("solid", fgColor="FF6B6B"),   # Red
    "P2": PatternFill("solid", fgColor="FFA94D"),    # Orange
    "P3": PatternFill("solid", fgColor="FFD93D"),    # Yellow
    "P4": PatternFill("solid", fgColor="6BCB77"),    # Green
}


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


# ============================================================================
# Field serialization for complex types
# ============================================================================

def serialize_preconditions(value: Any) -> str:
    """Convert preconditions to string (handles both string and list)."""
    if isinstance(value, list):
        return "\n".join(f"- {item}" for item in value)
    return str(value) if value else ""


def serialize_test_steps(value: Any) -> str:
    """Convert test_steps to string (handles both string and list of objects)."""
    if isinstance(value, list):
        lines = []
        for step in value:
            if isinstance(step, dict):
                num = step.get('step_number', '')
                action = step.get('action', '')
                expected = step.get('expected', '')
                line = f"{num}. {action}"
                if expected:
                    line += f"\n   Expected: {expected}"
                lines.append(line)
            else:
                lines.append(str(step))
        return "\n".join(lines)
    return str(value) if value else ""


def serialize_test_data(value: Any) -> str:
    """Convert test_data to string (handles both string and dict)."""
    if isinstance(value, dict):
        return "\n".join(f"{k}: {v}" for k, v in value.items())
    return str(value) if value else ""


def serialize_field(field_name: str, value: Any) -> str:
    """Serialize a field value to a string appropriate for Excel."""
    if value is None:
        return ""
    if field_name == 'preconditions':
        return serialize_preconditions(value)
    if field_name == 'test_steps':
        return serialize_test_steps(value)
    if field_name == 'test_data':
        return serialize_test_data(value)
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


# ============================================================================
# File reading and grouping
# ============================================================================

def read_jsonl_file(filepath: str) -> List[Dict]:
    """Read all test cases from JSONL file."""
    test_cases = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                tc = json.loads(line)
                test_cases.append(tc)
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON at line {line_num}: {e}")
    return test_cases


def find_non_empty_columns(test_cases: List[Dict], fields: List[str]) -> Set[str]:
    """Find which fields have at least one non-empty value across all records."""
    non_empty = set()
    for tc in test_cases:
        for field in fields:
            val = tc.get(field)
            if val is not None and val != "" and val != [] and val != {}:
                non_empty.add(field)
    return non_empty


def group_by_field(test_cases: List[Dict], field: str,
                   default: str = "Uncategorized") -> OrderedDict:
    """Group test cases by a given field value."""
    grouped = OrderedDict()
    for tc in test_cases:
        key = tc.get(field, default) or default
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(tc)
    return grouped


# ============================================================================
# Row conversion
# ============================================================================

def tc_to_row(tc: Dict, active_fields: List[str]) -> Tuple:
    """Convert a test case dict to a tuple using only active (non-hidden) fields."""
    return tuple(serialize_field(f, tc.get(f, "")) for f in active_fields)


def estimate_chars(rows: List[Tuple]) -> Tuple[int, int]:
    """Estimate total characters and average per row."""
    if not rows:
        return 0, 500
    total = sum(sum(len(str(f)) for f in row) for row in rows)
    avg = total // len(rows)
    return total, avg


def calculate_batch_size(rows: List[Tuple],
                         max_chars: int = MAX_CHARS_PER_BATCH) -> int:
    """Calculate optimal batch size based on character length."""
    if not rows:
        return 10
    sample = rows[:min(5, len(rows))]
    _, avg_chars = estimate_chars(sample)
    batch_size = max(1, int(max_chars / max(avg_chars, 100)))
    return min(batch_size, 50)


# ============================================================================
# Progress tracking
# ============================================================================

def load_progress(progress_file: str) -> Optional[Dict]:
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_progress(progress_file: str, progress: Dict):
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2)


def delete_progress(progress_file: str):
    if os.path.exists(progress_file):
        os.remove(progress_file)


# ============================================================================
# Sheet creation helpers
# ============================================================================

def sanitize_sheet_name(name: str) -> str:
    """Sanitize sheet name for Excel (max 31 chars, no special chars)."""
    for ch in ['/', '\\', '*', '?', '[', ']', ':']:
        name = name.replace(ch, '-')
    return name[:31]


def create_data_sheet(
    filepath: str,
    sheet_name: str,
    headers: List[str],
    col_widths: List[int],
    rows: List[Tuple],
    batch_size: int,
    is_first_sheet: bool = False,
    styles: Dict = None
) -> int:
    """Create or append a data sheet with batched row writing."""
    if styles is None:
        styles = create_styles()

    safe_name = sanitize_sheet_name(sheet_name)

    if is_first_sheet:
        wb = Workbook()
        ws = wb.active
        ws.title = safe_name
    else:
        wb = load_workbook(filepath)
        if safe_name in wb.sheetnames:
            ws = wb[safe_name]
        else:
            ws = wb.create_sheet(safe_name)

    # Write headers
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

    # Append rows in batches
    total_written = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        wb = load_workbook(filepath)
        ws = wb[safe_name]
        start_row = ws.max_row + 1

        for j, row_data in enumerate(batch):
            for col, value in enumerate(row_data, 1):
                cell = ws.cell(row=start_row + j, column=col, value=value)
                cell.alignment = styles['wrap_alignment']
                cell.border = styles['thin_border']

        wb.save(filepath)
        wb.close()
        total_written += len(batch)

    return total_written


# ============================================================================
# Summary Dashboard
# ============================================================================

def add_summary_dashboard(
    filepath: str,
    test_cases: List[Dict],
    journey_counts: Dict[str, int],
    feature_counts: Dict[str, int]
):
    """Add a Summary Dashboard with priority, source, feature, and journey breakdowns."""
    wb = load_workbook(filepath)
    ws = wb.create_sheet("Summary Dashboard", 0)
    styles = create_styles()

    # Title
    ws['A1'] = "UAT Test Cases - Summary Dashboard"
    ws['A1'].font = styles['title_font']
    ws.merge_cells('A1:H1')

    total = len(test_cases)
    ws['A2'] = f"Total Test Cases: {total}"
    ws['A2'].font = Font(italic=True, size=11)

    # ---- Priority Distribution ----
    row = 4
    ws.cell(row=row, column=1, value="Priority Distribution").font = styles['section_font']
    row += 1

    priority_headers = ["Priority", "Count", "Percentage"]
    for col, h in enumerate(priority_headers, 1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.font = styles['header_font']
        cell.fill = styles['header_fill']
        cell.border = styles['thin_border']
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 14

    priority_counter = defaultdict(int)
    for tc in test_cases:
        p = tc.get('priority', 'P2')
        priority_counter[p] += 1

    row += 1
    for priority in ['P1', 'P2', 'P3', 'P4']:
        count = priority_counter.get(priority, 0)
        ws.cell(row=row, column=1, value=priority).border = styles['thin_border']
        if priority in PRIORITY_FILLS:
            ws.cell(row=row, column=1).fill = PRIORITY_FILLS[priority]
            ws.cell(row=row, column=1).font = Font(bold=True)
        ws.cell(row=row, column=2, value=count).border = styles['thin_border']
        pct = f"{count / total * 100:.1f}%" if total > 0 else "0%"
        ws.cell(row=row, column=3, value=pct).border = styles['thin_border']
        row += 1

    # ---- Source Breakdown ----
    row += 1
    ws.cell(row=row, column=1, value="Source Breakdown").font = styles['section_font']
    row += 1

    source_headers = ["Source", "Count", "Percentage"]
    for col, h in enumerate(source_headers, 1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.font = styles['header_font']
        cell.fill = styles['header_fill']
        cell.border = styles['thin_border']

    source_counter = defaultdict(int)
    for tc in test_cases:
        src = tc.get('source', 'unknown')
        source_counter[src] += 1

    row += 1
    for src in sorted(source_counter.keys()):
        count = source_counter[src]
        ws.cell(row=row, column=1, value=src).border = styles['thin_border']
        ws.cell(row=row, column=2, value=count).border = styles['thin_border']
        pct = f"{count / total * 100:.1f}%" if total > 0 else "0%"
        ws.cell(row=row, column=3, value=pct).border = styles['thin_border']
        row += 1

    # ---- Feature Coverage ----
    row += 1
    ws.cell(row=row, column=1, value="Feature Coverage").font = styles['section_font']
    row += 1

    feat_headers = ["Feature", "Total", "P1", "P2", "P3", "P4",
                    "Status", "% Complete"]
    feat_widths = [30, 10, 10, 10, 10, 10, 14, 12]
    for col, (h, w) in enumerate(zip(feat_headers, feat_widths), 1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.font = styles['header_font']
        cell.fill = styles['header_fill']
        cell.border = styles['thin_border']
        if col > 3:
            ws.column_dimensions[get_column_letter(col)].width = w

    # Build per-feature priority counts
    feat_priority = defaultdict(lambda: defaultdict(int))
    for tc in test_cases:
        feat = tc.get('feature', 'Uncategorized')
        p = tc.get('priority', 'P2')
        feat_priority[feat][p] += 1

    row += 1
    feat_start_row = row
    for feat in sorted(feature_counts.keys()):
        ws.cell(row=row, column=1, value=feat).border = styles['thin_border']
        ws.cell(row=row, column=2, value=feature_counts[feat]).border = styles['thin_border']
        for ci, p in enumerate(['P1', 'P2', 'P3', 'P4'], 3):
            ws.cell(row=row, column=ci,
                    value=feat_priority[feat].get(p, 0)).border = styles['thin_border']
            ws.cell(row=row, column=ci).alignment = styles['center_alignment']
        ws.cell(row=row, column=7, value="Not Started").border = styles['thin_border']
        pct_cell = ws.cell(row=row, column=8, value=0)
        pct_cell.border = styles['thin_border']
        pct_cell.number_format = '0%'
        row += 1

    # Totals
    ws.cell(row=row, column=1, value="TOTAL").font = Font(bold=True)
    ws.cell(row=row, column=1).border = styles['thin_border']
    for col in range(2, 7):
        formula = f"=SUM({get_column_letter(col)}{feat_start_row}:{get_column_letter(col)}{row - 1})"
        cell = ws.cell(row=row, column=col, value=formula)
        cell.font = Font(bold=True)
        cell.border = styles['thin_border']

    # ---- Journey Tracking ----
    row += 2
    ws.cell(row=row, column=1, value="Journey Tracking").font = styles['section_font']
    row += 1

    jrn_headers = ["Journey ID", "Test Count", "Status", "% Complete"]
    for col, h in enumerate(jrn_headers, 1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.font = styles['header_font']
        cell.fill = styles['header_fill']
        cell.border = styles['thin_border']

    row += 1
    for jid in sorted(journey_counts.keys()):
        ws.cell(row=row, column=1, value=jid).border = styles['thin_border']
        ws.cell(row=row, column=2, value=journey_counts[jid]).border = styles['thin_border']
        ws.cell(row=row, column=3, value="Not Started").border = styles['thin_border']
        pct_cell = ws.cell(row=row, column=4, value=0)
        pct_cell.border = styles['thin_border']
        pct_cell.number_format = '0%'
        row += 1

    wb.save(filepath)
    wb.close()
    print(f"  Added Summary Dashboard (Priority + Source + Feature + Journey)")


# ============================================================================
# Traceability Matrix
# ============================================================================

def add_traceability_matrix(filepath: str, test_cases: List[Dict]):
    """Add Traceability Matrix sheet mapping test_id to source evidence."""
    wb = load_workbook(filepath)
    ws = wb.create_sheet("Traceability Matrix")
    styles = create_styles()

    trace_headers = [
        "Test ID", "Test Name", "Feature", "Journey ID",
        "Requirement ID", "Source", "Source Evidence",
        "Video Timestamp", "API Endpoint", "Component Path"
    ]
    trace_widths = [16, 40, 22, 16, 16, 12, 35, 14, 25, 35]

    for col, (header, width) in enumerate(zip(trace_headers, trace_widths), 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = styles['header_font']
        cell.fill = styles['header_fill']
        cell.alignment = styles['center_alignment']
        cell.border = styles['thin_border']
        ws.column_dimensions[get_column_letter(col)].width = width

    ws.freeze_panes = "A2"

    for row_num, tc in enumerate(test_cases, 2):
        values = [
            tc.get('test_id', ''),
            tc.get('test_name', ''),
            tc.get('feature', ''),
            tc.get('journey_id', ''),
            tc.get('requirement_id', ''),
            tc.get('source', ''),
            tc.get('source_evidence', ''),
            tc.get('video_timestamp', ''),
            tc.get('api_endpoint', ''),
            tc.get('component_path', '')
        ]
        for col, value in enumerate(values, 1):
            cell = ws.cell(row=row_num, column=col,
                           value=str(value) if value else "")
            cell.alignment = styles['wrap_alignment']
            cell.border = styles['thin_border']

    wb.save(filepath)
    wb.close()
    print(f"  Added Traceability Matrix ({len(test_cases)} entries)")


# ============================================================================
# Dropdown Values sheet
# ============================================================================

def add_dropdown_values_sheet(filepath: str):
    """Add Dropdown Values reference sheet."""
    wb = load_workbook(filepath)
    ws = wb.create_sheet("Dropdown Values")
    styles = create_styles()

    # Priority values
    ws['A1'] = "Priority"
    ws['A1'].font = styles['section_font']
    for i, val in enumerate(["P1", "P2", "P3", "P4"], 2):
        ws.cell(row=i, column=1, value=val)

    # Status values
    ws['C1'] = "Status"
    ws['C1'].font = styles['section_font']
    for i, val in enumerate(["Not Started", "In Progress", "Completed",
                              "Blocked", "Deferred"], 2):
        ws.cell(row=i, column=3, value=val)

    # Test Type values
    ws['E1'] = "Test Type"
    ws['E1'].font = styles['section_font']
    for i, val in enumerate(["Functional", "E2E", "Integration", "Usability",
                              "BusinessRules", "Regression"], 2):
        ws.cell(row=i, column=5, value=val)

    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['E'].width = 15

    wb.save(filepath)
    wb.close()
    print(f"  Added Dropdown Values sheet")


# ============================================================================
# Data validation
# ============================================================================

def add_data_validations(filepath: str, total_rows: int,
                         active_headers: List[str]):
    """Add dropdown data validations to Status and Priority columns."""
    wb = load_workbook(filepath)

    # Find column indices in active headers
    priority_col = None
    status_col = None
    for idx, h in enumerate(active_headers, 1):
        if h == "Priority":
            priority_col = get_column_letter(idx)
        elif h == "Status":
            status_col = get_column_letter(idx)

    end_row = min(total_rows + 10, 1000)

    for sheet_name in wb.sheetnames:
        if sheet_name in ["Summary Dashboard", "Dropdown Values",
                          "Traceability Matrix"]:
            continue

        ws = wb[sheet_name]

        if priority_col:
            dv_priority = DataValidation(
                type="list",
                formula1='"P1,P2,P3,P4"',
                allow_blank=True
            )
            dv_priority.error = "Please select from the list"
            ws.add_data_validation(dv_priority)
            dv_priority.add(f"{priority_col}2:{priority_col}{end_row}")

        if status_col:
            dv_status = DataValidation(
                type="list",
                formula1='"Not Started,In Progress,Completed,Blocked,Deferred"',
                allow_blank=True
            )
            dv_status.error = "Please select from the list"
            ws.add_data_validation(dv_status)
            dv_status.add(f"{status_col}2:{status_col}{end_row}")

    wb.save(filepath)
    wb.close()
    print(f"  Added data validations (Priority: {priority_col}, Status: {status_col})")


# ============================================================================
# Main conversion
# ============================================================================

def convert_jsonl_to_excel(
    jsonl_path: str,
    output_path: str,
    max_chars: int = MAX_CHARS_PER_BATCH
):
    """
    Main conversion function: canonical 20-field JSONL -> Excel with
    journey grouping, traceability matrix, batched processing, and
    resume capability.
    """
    progress_file = output_path + PROGRESS_FILE_SUFFIX
    styles = create_styles()

    print(f"\n{'=' * 60}")
    print(f"JSONL to Excel Converter v3.0")
    print(f"{'=' * 60}")
    print(f"Input:  {jsonl_path}")
    print(f"Output: {output_path}")
    print(f"Batch size: {max_chars:,} chars")
    print(f"{'=' * 60}\n")

    # Check for resume
    progress = load_progress(progress_file)
    if progress:
        print(f"Found progress file - resuming from last checkpoint...")
        print(f"  Last phase: {progress.get('phase', 'N/A')}")

    # Read all test cases
    print(f"Reading JSONL file...")
    test_cases = read_jsonl_file(jsonl_path)
    print(f"  Found {len(test_cases)} test cases")

    if not test_cases:
        print("ERROR: No test cases found in JSONL file")
        return

    # Show journey/feature breakdown
    journeys = group_by_field(test_cases, 'journey_id', 'No Journey')
    features = group_by_field(test_cases, 'feature', 'Uncategorized')
    print(f"  Journeys: {len(journeys)}")
    for jid, tcs in sorted(journeys.items()):
        print(f"    - {jid}: {len(tcs)} test cases")
    print(f"  Features: {len(features)}")
    for feat, tcs in sorted(features.items()):
        print(f"    - {feat}: {len(tcs)} test cases")

    # Determine which optional columns have data
    optional_fields = {
        'video_timestamp', 'screenshot_path', 'api_endpoint',
        'component_path', 'requirement_id'
    }
    non_empty = find_non_empty_columns(test_cases, CANONICAL_FIELDS)

    # Build active field/header/width lists (hide empty optional columns)
    active_fields = []
    active_headers = []
    active_widths = []
    for field, header, width in zip(CANONICAL_FIELDS, CANONICAL_HEADERS,
                                    CANONICAL_COL_WIDTHS):
        if field in optional_fields and field not in non_empty:
            continue
        active_fields.append(field)
        active_headers.append(header)
        active_widths.append(width)

    # Append tracking columns
    all_headers = active_headers + TRACKING_HEADERS
    all_widths = active_widths + TRACKING_COL_WIDTHS

    hidden_count = len(CANONICAL_FIELDS) - len(active_fields)
    if hidden_count > 0:
        hidden_names = [f for f in CANONICAL_FIELDS
                        if f in optional_fields and f not in non_empty]
        print(f"  Hidden {hidden_count} empty optional columns: {hidden_names}")

    # Convert to rows
    tracking_defaults = ("Not Started", "", "", "")
    all_rows = [tc_to_row(tc, active_fields) + tracking_defaults
                for tc in test_cases]

    batch_size = calculate_batch_size(all_rows, max_chars)
    total_chars, avg_chars = estimate_chars(all_rows)

    print(f"\n  Character Analysis:")
    print(f"    Total characters: {total_chars:,}")
    print(f"    Avg chars/row: {avg_chars:,}")
    print(f"    Batch size: {batch_size} rows")
    print(f"    Active columns: {len(all_headers)}")

    # Phase 1: Create "All Test Cases" sheet
    print(f"\n  Phase 1: Creating 'All Test Cases' sheet...")
    count = create_data_sheet(
        output_path, "All Test Cases", all_headers, all_widths,
        all_rows, batch_size, is_first_sheet=True, styles=styles
    )
    print(f"    Written: {count} test cases")

    save_progress(progress_file, {
        'phase': 'all_test_cases_complete',
        'total': len(test_cases)
    })

    # Phase 2: Create per-journey sheets
    journey_counts = {jid: len(tcs) for jid, tcs in journeys.items()}

    print(f"\n  Phase 2: Creating {len(journeys)} journey sheets...")
    for jid, tcs in journeys.items():
        rows = [tc_to_row(tc, active_fields) + tracking_defaults for tc in tcs]
        count = create_data_sheet(
            output_path, jid, all_headers, all_widths,
            rows, batch_size, styles=styles
        )
        print(f"    Sheet '{sanitize_sheet_name(jid)}': {count} test cases")

    # Phase 3: Summary Dashboard
    print(f"\n  Phase 3: Adding Summary Dashboard...")
    feature_counts = {f: len(tcs) for f, tcs in features.items()}
    add_summary_dashboard(output_path, test_cases, journey_counts, feature_counts)

    # Phase 4: Traceability Matrix
    print(f"  Phase 4: Adding Traceability Matrix...")
    add_traceability_matrix(output_path, test_cases)

    # Phase 5: Dropdown Values and Data Validation
    print(f"  Phase 5: Adding Dropdown Values and Data Validation...")
    add_dropdown_values_sheet(output_path)
    add_data_validations(output_path, len(test_cases), all_headers)

    # Cleanup progress
    delete_progress(progress_file)

    # Final verification
    wb = load_workbook(output_path)
    print(f"\n{'=' * 60}")
    print(f"Conversion complete!")
    print(f"{'=' * 60}")
    print(f"Output file: {output_path}")
    print(f"Total test cases: {len(test_cases)}")
    print(f"Sheets: {len(wb.sheetnames)}")
    for name in wb.sheetnames:
        ws = wb[name]
        print(f"  - {name}: {ws.max_row - 1} rows")
    wb.close()
    print(f"{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Convert canonical 20-field JSONL test cases to formatted Excel workbook',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python jsonl_to_excel.py unified-scenarios.jsonl --output uat-tests.xlsx
  python jsonl_to_excel.py data.jsonl --output output.xlsx --batch-chars 10000

  # Resume after failure (automatically detects .progress file):
  python jsonl_to_excel.py data.jsonl --output output.xlsx
        """
    )

    parser.add_argument('jsonl_file', help='Input JSONL file path')
    parser.add_argument('--output', '-o', required=True,
                        help='Output Excel file path')
    parser.add_argument('--batch-chars', type=int, default=MAX_CHARS_PER_BATCH,
                        help=f'Max characters per batch (default: {MAX_CHARS_PER_BATCH})')

    args = parser.parse_args()

    if not os.path.exists(args.jsonl_file):
        print(f"ERROR: JSONL file not found: {args.jsonl_file}")
        return 1

    convert_jsonl_to_excel(args.jsonl_file, args.output, args.batch_chars)
    return 0


if __name__ == "__main__":
    exit(main())
