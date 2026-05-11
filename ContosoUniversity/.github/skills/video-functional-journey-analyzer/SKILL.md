---
name: video-functional-journey-analyzer
description: >
  Analyzes extracted video frames grouped by scene using multimodal capability
  to produce structured functional test scenario candidates with technical
  detail. Takes frame images and a manifest from video-functional-frame-extract,
  identifies UI pages/states per scene, detects user actions and transitions,
  extracts technical detail (field names, validation indicators, API patterns,
  error messages), and outputs journeys.jsonl and scenario-candidates.jsonl
  tagged source "video" with discovered_fields, discovered_validations, and
  discovered_endpoints. OCR enrichment is enabled by default to capture exact
  field names and validation text for downstream functional test generation.
  Supports optional transcript correlation for adding narration context. Use
  when converting application walkthrough video frames into technically detailed
  functional test scenario candidates for the functional-scenario-merger.
license: MIT
compatibility: >
  Requires video-functional-frame-extract skill output (frames/ directory and
  manifest.json). Works with any skills-compatible coding agent with multimodal
  (image reading) capability. OCR mode requires no additional dependencies —
  leverages the model's multimodal text extraction from images.
metadata:
  author: functional-test-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
---

# Video Functional Journey Analyzer

## Purpose

Analyze extracted video frames (grouped by scene) using the model's multimodal
capability to produce **functional test scenario candidates with full technical
detail**. This skill bridges raw video frames and testable functional scenarios
by extracting the technical specifics (field names, validation rules, API
patterns, error messages, status codes) that downstream skills need to generate
deterministic, repeatable functional test cases.

> **Key Differentiator vs UAT**: This skill extracts **technical identifiers**
> (exact field names, validation text, HTTP patterns) rather than business intent.
> The functional pipeline needs precise technical detail to generate the 35-field
> test case schema. OCR is enabled by default because functional tests require
> exact field names, not inferred descriptions.

> **Multimodal approach**: Uses the model's ability to directly read images.
> The model observes frames like a QA engineer inspecting a UI for testable
> elements — fields, buttons, validation messages, form attributes, error states.

## When to Use This Skill

- Convert video walkthrough frames into **technically detailed** scenario candidates
- Identify UI pages, states, and transitions with field-level precision
- Extract exact field names, validation indicators, and error messages via OCR
- Produce scenario candidates with `discovered_fields`, `discovered_validations`,
  and `discovered_endpoints` for the functional-scenario-merger
- Feed scenario candidates tagged `source: "video"` to the
  `functional-scenario-merger` skill
- **OCR mode (default ON)**: When exact UI text (field names, button labels,
  validation messages, error text) is needed for functional test case generation
- **Transcript mode**: When audio transcript enriches the technical context

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `frames_dir` | Yes | -- | Directory containing extracted frames (PNG) from video-functional-frame-extract |
| `manifest_path` | Yes | -- | Path to `manifest.json` from video-functional-frame-extract |
| `output_dir` | Yes | `functional-tests/intermediate/video` | Output directory |
| `ocr_enabled` | No | `true` | Enable OCR text extraction from frames (default ON for functional pipeline) |
| `transcript_path` | No | -- | Path to `transcript.json` from video-audio-extractor for narration correlation |

## Outputs

| File | Format | Description |
|---|---|---|
| `journeys.jsonl` | JSONL | Structured user journeys with scene references and technical detail |
| `scenario-candidates.jsonl` | JSONL | Functional test scenario candidates tagged with `source: "video"` |

---

## 5-Phase Workflow

### Phase 1: Scene Grouping

**Goal**: Read `manifest.json` and group frames into scenes.

1. **Load manifest**: Parse `manifest.json` for frame list with:
   - Frame filename
   - Timestamp (seconds from video start)
   - Similarity score to previous frame

2. **Group by scene**: Consecutive frames with similarity scores **above** the
   threshold (default 0.3) belong to the same scene. A drop below threshold
   marks a scene transition.

3. **Scene metadata**: For each scene, record:
   ```jsonc
   {
     "scene_id": "S-001",
     "start_frame": "frame_000001.png",
     "end_frame": "frame_000008.png",
     "start_timestamp": "00:05",
     "end_timestamp": "00:22",
     "frame_count": 8,
     "transition_frames": ["frame_000001.png", "frame_000008.png"]
   }
   ```

4. **Cap frames per scene**: If a scene has >10 transition frames, split into
   sub-scenes of max 10 frames each.

### Phase 2: Scene Analysis (Per Scene)

**Goal**: Read key transition frames and identify UI elements, page types,
user actions, and **technical attributes** relevant to functional testing.

For each scene batch (max 10 frames):

1. **Read frames** directly via multimodal capability (model reads images).

2. **Identify page type**: Classify as one of:
   | Type | Description | Functional Testing Relevance |
   |---|---|---|
   | `list` | Data grid, table, search results | CRUD Read, pagination, sorting, filtering |
   | `form` | Create/edit form with input fields | CRUD Create/Update, validation, field constraints |
   | `detail` | Single record detail view | CRUD Read, data display verification |
   | `dashboard` | Summary view with charts/metrics | Aggregation, widget rendering |
   | `modal` | Overlay dialog | Confirmation flows, inline edit, delete confirmation |
   | `drawer` | Side panel overlay | Detail panel, quick edit |
   | `login` | Authentication page | Auth flow, credential validation, session management |
   | `navigation` | Menu or route transition | Route transitions, nav state |
   | `settings` | Configuration page | Preference persistence, form validation |
   | `error` | Error state or empty state | Error handling, empty state fallback |

3. **Identify visible technical elements** — extract with precision:
   - **Form fields**: Field name/label, input type (text, select, checkbox, date),
     placeholder text, required indicator (*), maxlength indicator
   - **Buttons**: Exact label text, button type (submit, cancel, delete, action)
   - **Tables**: Column headers (exact text), row count, action columns,
     pagination controls
   - **Validation indicators**: Required asterisks, field highlighting,
     inline error messages, character counters
   - **Status indicators**: HTTP status codes if visible, toast/alert messages,
     loading states, success/error banners
   - **Navigation items**: Menu labels, breadcrumb paths, tab labels
   - **Data values**: Enum values in dropdowns, status badge text, counts/totals

4. **Detect transitions**: Compare frames within the scene:
   - What changed between frames?
   - What user action likely caused the transition?
   - What was the **technically observable** result?
   - Were any validation messages shown?
   - Did the URL appear to change (visible in browser address bar)?

5. **Output per scene** (functional format):
   ```jsonc
   {
     "scene_id": "S-003",
     "page_type": "form",
     "page_title": "Create Vehicle",
     "route_hint": "/vehicles/new",
     "visible_fields": [
       {"name": "name", "type": "text", "label": "Vehicle Name", "required": true, "placeholder": "Enter vehicle name"},
       {"name": "type", "type": "select", "label": "Vehicle Type", "options": ["Heavy Duty", "Light", "Medium"], "required": true},
       {"name": "plate_number", "type": "text", "label": "Plate Number", "required": true, "placeholder": "e.g. AB1234"}
     ],
     "visible_buttons": [
       {"label": "Create Vehicle", "type": "submit"},
       {"label": "Cancel", "type": "navigation"}
     ],
     "visible_validation": [
       {"field": "name", "indicator": "required asterisk"},
       {"field": "plate_number", "indicator": "required asterisk, placeholder pattern hint"}
     ],
     "visible_errors": [],
     "visible_data": {
       "table_headers": [],
       "status_values": [],
       "enum_values": {"type": ["Heavy Duty", "Light", "Medium"]}
     },
     "transitions": [
       {
         "from_frame": "frame_000042.png",
         "to_frame": "frame_000045.png",
         "action": "User filled form fields and clicked 'Create Vehicle' submit button",
         "result": "Success toast appeared, page redirected to vehicle list showing new record",
         "validation_triggered": false,
         "error_messages": []
       }
     ],
     "confidence": 0.85
   }
   ```

### Phase 3: OCR Enrichment (Default ON)

**Goal**: Extract exact text from key frames to capture UI labels, field names,
validation messages, and data values with high fidelity for functional test
generation.

> In the functional pipeline, OCR is **enabled by default** (`ocr_enabled: true`)
> because functional test cases require exact field names and validation text for
> the 35-field schema (field_name, validation_rule, error_message, valid_input,
> invalid_input columns). Skip only when `ocr_enabled` is explicitly set to
> `false`.

For each scene's key transition frames:

1. **Extract field labels and attributes**: Read input field labels, placeholder
   text, and infer HTML input types from visual appearance.
   ```json
   "ocr_fields": [
     {"label": "Vehicle Name", "name_hint": "name", "placeholder": "Enter vehicle name", "type": "text", "required": true, "maxlength_hint": null},
     {"label": "Vehicle Type", "name_hint": "type", "type": "select", "options": ["Heavy Duty", "Light", "Medium"], "required": true},
     {"label": "Plate Number", "name_hint": "plate_number", "placeholder": "e.g., AB1234", "type": "text", "required": true, "pattern_hint": "[A-Z]{2}[0-9]{4}"}
   ]
   ```

2. **Extract button labels**: Read all visible button text exactly as displayed.
   ```json
   "ocr_buttons": ["Create Vehicle", "Cancel", "Delete", "Export CSV"]
   ```

3. **Extract validation and error messages**: Capture any visible error/warning
   text with the field it relates to.
   ```json
   "ocr_errors": [
     {"field": "name", "message": "Name is required", "type": "validation"},
     {"field": "plate_number", "message": "Invalid plate number format", "type": "format"}
   ]
   ```

4. **Extract data values relevant to test data generation**:
   ```json
   "ocr_data": {
     "table_headers": ["Name", "Type", "Plate #", "Status", "Actions"],
     "status_values": ["Active", "Inactive", "Maintenance"],
     "dropdown_options": {"type": ["Heavy Duty", "Light", "Medium"]},
     "counts": {"total_vehicles": "24"},
     "pagination": {"current_page": "1", "total_pages": "3"}
   }
   ```

5. **Extract navigation items**: Menu items, breadcrumbs, tab labels.
   ```json
   "ocr_navigation": ["Dashboard", "Vehicles", "Bookings", "Users", "Reports", "Settings"]
   ```

6. **Infer API patterns from observable behavior**: If form submission results
   are visible (success/error toasts, URL changes, redirect behavior), infer:
   ```json
   "inferred_api": {
     "endpoint_hint": "/api/vehicles",
     "method_hint": "POST",
     "status_hint": "201",
     "confidence": 0.5,
     "evidence": "Form submitted to /vehicles/new, success toast shown, redirected to /vehicles"
   }
   ```

7. **Merge with scene analysis**: OCR-extracted fields **replace** visually
   inferred labels when available, since OCR provides exact text.

### Phase 3b: Transcript Correlation (Optional — when `transcript_path` provided)

**Goal**: Correlate timestamped transcript segments with scenes to add context.

1. **Load transcript**: Parse `transcript.json` from video-audio-extractor.

2. **Match segments to scenes**: For each scene, find transcript segments whose
   time range overlaps with the scene's timestamp range.

3. **Extract technical hints from narration**: Look for narrator mentions of:
   - Field names or validation rules ("the plate number must be two letters
     followed by four digits")
   - API behavior ("this calls the vehicles API")
   - Error conditions ("if you leave the name empty, you'll see this error")
   - Edge cases ("notice you can't enter more than 100 characters")

4. **Add narration context**:
   ```json
   "narration": "Now I'll show you the vehicle creation form with validation",
   "narration_technical_hints": [
     "plate number format: two letters + four digits",
     "name field has max 100 characters"
   ]
   ```

5. **Boost confidence**: Scenes with matching narration get +0.10 confidence
   boost (capped at 1.0).

### Phase 4: Journey Construction

**Goal**: Chain scene analyses into sequential functional workflows.

1. **Group related scenes** into logical functional workflows:
   - Scenes following a CRUD cycle (create, read, update, delete for same entity)
   - Scenes involving the same entity type (vehicles, bookings, users)
   - Scenes showing validation flows (submit → error → correct → success)
   - Scenes following a navigation path (list → form → confirmation)

2. **Build journey records** (functional format):
   ```jsonc
   {
     "journey_id": "J-VEH-CRUD",
     "journey_name": "Vehicle Management — Create, View, Edit",
     "functional_scope": "CRUD operations on Vehicle entity",
     "scenes": ["S-001", "S-002", "S-003", "S-004"],
     "actions": [
       "Navigate to Vehicle Management page",
       "View list of existing vehicles (table with 5 columns)",
       "Click 'Add Vehicle' button",
       "Fill vehicle creation form (3 required fields: name, type, plate_number)",
       "Submit form via 'Create Vehicle' button",
       "Verify success toast and new record in vehicle list"
     ],
     "discovered_fields": ["name", "type", "plate_number"],
     "discovered_validations": [
       {"field": "name", "rule": "required"},
       {"field": "type", "rule": "required, enum"},
       {"field": "plate_number", "rule": "required, pattern hint"}
     ],
     "start_timestamp": "00:15",
     "end_timestamp": "01:45",
     "entity_type": "Vehicle",
     "workflow_type": "CRUD"
   }
   ```

3. **Write `journeys.jsonl`**: One journey per line.

### Phase 5: Scenario Candidate Extraction

**Goal**: From each journey, produce functional test scenario candidates tagged
with `source: "video"` and populated with technical detail for the
`functional-scenario-merger`.

Extract candidates from these patterns:

| Pattern | Candidate Type | Functional Relevance |
|---|---|---|
| **Form submission (valid)** | Positive test candidate | Happy path CRUD with specific field values |
| **Form submission (invalid)** | Negative/Validation candidate | Validation error handling per field |
| **Each required field** | Negative candidate | Required field omission test |
| **Each field with constraints** | Boundary candidate | Min/max, pattern, enum boundaries |
| **Each table with actions** | CRUD candidates | List, sort, filter, delete operations |
| **Navigation flows** | Navigation candidate | Route transitions, back/forward |
| **Error states visible** | Negative candidate | Error handling, empty states |
| **Auth-protected pages** | Security candidate | Access control verification |

**Candidate format** (functional test pipeline):

```jsonc
{
  "candidate_id": "VID-001",
  "feature": "Vehicle Management",
  "module": "Vehicles",
  "action": "Create new vehicle via form",
  "description": "Submit vehicle creation form at /vehicles/new with 3 required fields: name (text, required), type (select, required, enum: Heavy Duty/Light/Medium), plate_number (text, required, pattern hint: AB1234)",
  "source": "video",
  "source_evidence": "frame_000042.png, scene S-003, timestamp 01:23",
  "confidence": 0.75,
  "discovered_fields": ["name", "type", "plate_number"],
  "discovered_validations": [
    {"field": "name", "rule": "required", "source": "video"},
    {"field": "type", "rule": "required, enum:[Heavy Duty, Light, Medium]", "source": "video"},
    {"field": "plate_number", "rule": "required, pattern_hint:[A-Z]{2}[0-9]{4}", "source": "video"}
  ],
  "discovered_endpoints": [
    {"endpoint": "/api/vehicles", "method": "POST", "source": "video", "confidence": 0.5, "evidence": "inferred from form action and redirect"}
  ],
  "video_timestamp": "01:23",
  "screenshot_ref": "",
  "component_path": "",
  "functional_categories_hint": ["Positive", "Negative", "Validation", "Boundary"],
  "test_steps_hint": [
    {"step_number": 1, "action": "Navigate to /vehicles/new", "expected": "Vehicle creation form displayed with fields: name, type, plate_number"},
    {"step_number": 2, "action": "Fill Name='Test Vehicle', Type='Heavy Duty', Plate='AB1234'", "expected": "Fields accept input, no validation errors"},
    {"step_number": 3, "action": "Click 'Create Vehicle' submit button", "expected": "Success toast, redirect to /vehicles, new record visible in list"}
  ]
}
```

**OCR enrichment impact**: When OCR is enabled (default), `discovered_fields`
contains exact field names extracted from the UI instead of inferred descriptions.
This significantly improves merging accuracy in `functional-scenario-merger` and
produces higher-quality test data in `functional-test-generator`.

**Endpoint inference**: Video-sourced endpoints are always tagged with low
confidence (0.3-0.5) since they are inferred from observable behavior, not
confirmed by code. The `functional-scenario-merger` will boost confidence when
codebase analysis confirms the same endpoint.

Write `scenario-candidates.jsonl`: One candidate per line.

---

## Constraints

1. **NEVER assume technical details not observable in frames.** Only describe
   what can be directly observed or reasonably inferred from visual evidence.
2. **Use TECHNICAL language** — include exact field names, input types,
   validation indicators, button labels, error messages, status codes, and
   URL patterns where observable. Do NOT abstract to business language.
3. **Tag inferred technical details with confidence scores.** Directly observed
   OCR text: confidence 0.8-0.9. Inferred API patterns: confidence 0.3-0.5.
4. **Maximum 10 frames per scene batch** sent to the model.
5. **Preserve video timestamps** from the manifest for every scene and candidate.
6. **Populate `discovered_fields` with exact field names** from OCR when
   available. Use `name_hint` derived from label text (lowercase, underscored).
7. **Populate `discovered_validations`** with any observable validation rules:
   required indicators, maxlength hints, pattern hints from placeholders,
   visible error messages.
8. **Populate `discovered_endpoints`** only when there is observable evidence
   (form action attributes, visible URL changes, network activity hints).
   Always mark as low confidence (video source).

## Error Handling

| Issue | Resolution |
|---|---|
| `manifest.json` not found | Report error — video-functional-frame-extract must run first |
| Frames directory empty | Report error — no frames to analyze |
| Frame file missing | Skip frame, log warning, continue with remaining |
| Scene has no detectable UI | Mark as "transition/loading", skip candidate extraction |
| Cannot determine page type | Mark as "unknown" with confidence 0.3 |
| OCR extraction yields no text | Fall back to visual inference, note lower confidence |
| No technical elements observable | Generate candidate with minimal fields, set confidence 0.4 |

## Related Skills

| Skill | Relationship |
|---|---|
| **video-functional-frame-extract** | Upstream — produces frames/ and manifest.json consumed by this skill |
| **video-audio-extractor** | Upstream — produces transcript.json for optional narration correlation |
| **functional-scenario-merger** | Downstream — receives scenario-candidates.jsonl for cross-source merging |
| **functional-qualification-gate** | Downstream — qualifies merged scenarios after merging |
| **functional-test-generator** | Downstream — generates 35-field test cases from qualified scenarios |
