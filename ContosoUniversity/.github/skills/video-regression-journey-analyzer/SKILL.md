---
name: video-regression-journey-analyzer
description: >
  Analyzes extracted video frames grouped by scene using multimodal capability
  to produce structured regression test scenario candidates focused on
  technical behavior verification. Takes frame images and a manifest from
  video-regression-frame-extract, identifies UI components/states per scene,
  detects interactions and state transitions from a testing perspective, maps
  observable behavior to testable assertions, and outputs interaction-flows.jsonl
  and regression-scenario-candidates.jsonl tagged source "video-regression".
  Focuses on component behavior, validation logic, state management, error
  handling, and conditional rendering rather than business intent. Supports
  optional OCR enrichment for extracting field labels, validation messages,
  and error codes. Use when converting application walkthrough video frames
  into technical regression test scenario candidates for the regression
  orchestrator or scenario-merger.
license: MIT
compatibility: >
  Requires video-regression-frame-extract skill output (frames/ directory and
  manifest.json). Works with any skills-compatible coding agent with multimodal
  (image reading) capability. OCR mode requires no additional dependencies —
  leverages the model's multimodal text extraction from images.
metadata:
  author: regression-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
---

# Video Regression Journey Analyzer

## Purpose

Analyze extracted video frames (grouped by scene) using the model's multimodal
capability to produce **regression test scenario candidates focused on
technical behavior verification**. This skill bridges raw video frames and
testable regression scenarios by observing **how the application behaves** —
component rendering, state transitions, validation logic, error handling,
and interaction feedback — rather than business intent.

> **Key Differentiator vs UAT**: This skill extracts **technical behavior**
> (component states, validation rules, error handling, conditional rendering,
> interaction feedback) rather than business intent (user goals, acceptance
> criteria). The regression pipeline needs scenarios that verify specific
> component behavior hasn't changed — field validations fire correctly,
> error states render properly, loading states appear, and navigation
> transitions complete.

> **Multimodal approach**: Uses the model's ability to directly read images.
> The model observes frames like a QA engineer reviewing a recorded test
> session — noticing component states, validation feedback, error messages,
> and interaction results that could regress.

## When to Use This Skill

- Convert video walkthrough frames into **technical regression** scenarios
- Identify component interactions, state transitions, and validation behavior
- Map observable UI behavior to **testable assertions**
- Produce scenario candidates for the `regression-orchestrator` or `scenario-merger`
- Feed scenario candidates tagged `source: "video-regression"` downstream
- **OCR mode (recommended)**: Extract validation messages, field labels, error
  codes, and button text for precise assertion generation
- **Transcript mode**: When developer narration provides implementation context

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `frames_dir` | Yes | -- | Directory containing extracted frames (PNG) from video-regression-frame-extract |
| `manifest_path` | Yes | -- | Path to `manifest.json` from video-regression-frame-extract |
| `output_dir` | Yes | `regression-output/phase-1-video` | Output directory |
| `ocr_enabled` | No | `true` | Enable OCR text extraction from frames (default ON for regression — exact field labels and validation messages needed for assertions) |
| `transcript_path` | No | -- | Path to `transcript.json` from video-audio-extractor for developer narration correlation |
| `source_map_path` | No | -- | Path to source file mapping (route-to-component map) for linking scenarios to source files |

## Outputs

| File | Format | Description |
|---|---|---|
| `interaction-flows.jsonl` | JSONL | Structured interaction flows with component states and scene references |
| `regression-scenario-candidates.jsonl` | JSONL | Regression scenario candidates tagged with `source: "video-regression"` |

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

**Goal**: Read key transition frames and identify **component behavior, state
transitions, and testable interactions** — using technical testing language.

For each scene batch (max 10 frames):

1. **Read frames** directly via multimodal capability (model reads images).

2. **Identify page type and components**: Classify from a testing perspective:
   | Type | Testing Focus | Regression Relevance |
   |---|---|---|
   | `list-view` | Table rendering, sorting, filtering, pagination | Row count, column headers, sort indicators, empty state |
   | `form` | Input validation, field states, submit behavior | Required fields, validation messages, disabled states |
   | `detail-view` | Data display, conditional rendering | Field values, computed displays, null handling |
   | `dashboard` | Widget rendering, data aggregation displays | Stat cards, chart renders, loading states |
   | `modal/dialog` | Overlay rendering, focus trap, action buttons | Open/close behavior, button states, backdrop |
   | `drawer/panel` | Side panel rendering, content loading | Slide animation, content population, close |
   | `login/auth` | Authentication flow, input validation | Error messages, redirect behavior, token handling |
   | `navigation` | Route transitions, active state indicators | Active menu item, breadcrumb updates, URL changes |
   | `settings` | Form persistence, toggle states | Save confirmation, reset behavior, dirty state |
   | `error-page` | Error boundary rendering, recovery actions | Error code display, retry button, navigation fallback |
   | `loading` | Skeleton/spinner states, progressive loading | Loading indicator presence, transition to loaded |

3. **Identify testable elements** — describe in technical testing language:
   - **Input fields**: Label, type, placeholder, required indicator, validation state
   - **Buttons**: Label, enabled/disabled state, loading state, variant (primary/secondary)
   - **Tables**: Column headers, row count, sort indicators, filter controls, pagination
   - **Validation messages**: Exact text, severity (error/warning/info), associated field
   - **Status indicators**: Badge text, color/variant, tooltip content
   - **Navigation**: Active menu item, breadcrumb trail, URL route hint
   - **Conditional UI**: Elements that appear/disappear based on state (empty states,
     permission-gated sections, feature flags)

4. **Detect state transitions**: Compare frames within the scene:
   - What interaction triggered the change? (click, type, submit, navigate)
   - What **component state changed**? (field validation, button enabled/disabled,
     row added/removed, modal opened/closed)
   - What **visual feedback** was shown? (success toast, error border, loading spinner)
   - Were there **side effects**? (list refreshed, counter updated, badge changed)

5. **Output per scene** (regression format):
   ```jsonc
   {
     "scene_id": "S-003",
     "page_type": "form",
     "page_title": "Create Vehicle",
     "route_hint": "/vehicles/new",
     "components": [
       {"type": "text-input", "label": "Vehicle Name", "required": true, "validation": "required"},
       {"type": "select", "label": "Vehicle Type", "options": ["Heavy Duty", "Light", "Medium"]},
       {"type": "text-input", "label": "Plate Number", "required": true},
       {"type": "button", "label": "Create", "variant": "primary", "state": "enabled"},
       {"type": "button", "label": "Cancel", "variant": "secondary"}
     ],
     "testable_states": [
       "Form renders with all required fields",
       "Vehicle Type dropdown populates with 3 options",
       "Create button is enabled when required fields are filled",
       "Cancel button navigates back to vehicle list"
     ],
     "transitions": [
       {
         "from_frame": "frame_000042.png",
         "to_frame": "frame_000045.png",
         "trigger": "click Create button",
         "state_before": "form filled with valid data",
         "state_after": "success toast visible, redirected to vehicle list",
         "assertions": [
           "Success message contains 'Vehicle created'",
           "Vehicle list includes new entry",
           "Form is no longer visible"
         ]
       }
     ],
     "confidence": 0.85
   }
   ```

### Phase 3: OCR Enrichment (Recommended — `ocr_enabled: true` by default)

**Goal**: Extract visible UI text to generate precise regression assertions.
Regression tests need exact field labels, validation messages, error codes,
and button text to write effective assertions.

> This phase is **enabled by default** (`ocr_enabled: true`). Regression tests
> assert against exact text content — validation messages, field labels, error
> codes, button labels. OCR provides the precise text needed for assertions.

For each scene's key transition frames:

1. **Extract field labels and placeholders**:
   ```json
   "ocr_fields": [
     {"label": "Vehicle Name", "placeholder": "Enter vehicle name", "required_indicator": "*"},
     {"label": "Plate Number", "placeholder": "ABC-1234", "required_indicator": "*"}
   ]
   ```

2. **Extract validation messages**:
   ```json
   "ocr_validations": [
     {"field": "Vehicle Name", "message": "Vehicle name is required", "severity": "error"},
     {"field": "Plate Number", "message": "Invalid plate format", "severity": "error"}
   ]
   ```

3. **Extract button labels and states**:
   ```json
   "ocr_buttons": [
     {"label": "Create Vehicle", "variant": "primary", "appears_enabled": true},
     {"label": "Cancel", "variant": "secondary", "appears_enabled": true}
   ]
   ```

4. **Extract table headers and row data**:
   ```json
   "ocr_table": {
     "headers": ["Name", "Type", "Plate", "Status"],
     "visible_row_count": 8,
     "pagination_info": "Showing 1-8 of 24"
   }
   ```

5. **Extract status/error messages**:
   ```json
   "ocr_messages": [
     {"text": "Vehicle created successfully", "type": "success-toast"},
     {"text": "Error: Duplicate plate number", "type": "error-alert"}
   ]
   ```

6. **Merge with scene analysis**: Use OCR text to generate precise assertions
   (e.g., `expect(screen.getByText('Vehicle created successfully')).toBeVisible()`).

### Phase 3b: Transcript Correlation (Optional — when `transcript_path` provided)

**Goal**: Correlate timestamped transcript segments with scenes to capture
developer/tester narration about implementation details.

1. **Load transcript**: Parse `transcript.json` from video-audio-extractor.

2. **Match segments to scenes**: For each scene, find transcript segments whose
   time range overlaps with the scene's timestamp range.

3. **Extract technical context from narration**: Look for mentions of:
   - Component names ("this is the VehicleForm component")
   - Validation rules ("it validates that plate numbers match the format")
   - State management ("this updates the vehicle store")
   - Edge cases ("watch what happens when the list is empty")
   - Known issues ("this button should be disabled when...")

4. **Add narration context**:
   ```json
   "narration": "Now I'll show the validation — when you leave the name blank and hit create",
   "narration_technical_context": "Form validation on required field, error state rendering"
   ```

5. **Boost confidence**: Scenes with matching technical narration get +0.10
   confidence boost (capped at 1.0).

### Phase 3c: Source Map Correlation (Optional — when `source_map_path` provided)

**Goal**: Link observed routes/pages to source files for targeted regression.

1. **Load source map**: Parse route-to-component mapping.

2. **Match routes to components**: Use `route_hint` from scene analysis to find
   the corresponding source files.

3. **Add source references**:
   ```json
   "source_files": [
     "components/vehicles/VehicleForm.tsx",
     "app/vehicles/new/page.tsx"
   ]
   ```

### Phase 4: Interaction Flow Construction

**Goal**: Chain scene analyses into sequential interaction flows that map to
testable regression paths.

1. **Group related scenes** into logical interaction flows:
   - Scenes following a CRUD operation (create → list refresh → detail view)
   - Scenes demonstrating form validation (empty submit → errors → fix → success)
   - Scenes showing navigation paths (menu click → page load → component render)
   - Scenes showing error recovery (error state → retry → success)
   - Scenes showing conditional UI (toggle → elements appear/disappear)

2. **Build flow records** (regression format):
   ```jsonc
   {
     "flow_id": "F-VEH-CREATE",
     "flow_name": "Vehicle Creation Form Submission",
     "flow_type": "crud-create",
     "components_under_test": [
       "VehicleForm",
       "VehicleList",
       "SuccessToast"
     ],
     "route_sequence": ["/vehicles", "/vehicles/new", "/vehicles"],
     "scenes": ["S-001", "S-002", "S-003", "S-004"],
     "interactions": [
       "Navigate to /vehicles — list view renders with existing vehicles",
       "Click 'Add Vehicle' — form renders with empty fields",
       "Fill required fields (name, type, plate) — no validation errors",
       "Click Create — success toast, redirect to list with new entry"
     ],
     "state_changes": [
       {"component": "VehicleList", "before": "N rows", "after": "N+1 rows"},
       {"component": "VehicleForm", "before": "visible", "after": "unmounted"},
       {"component": "SuccessToast", "before": "hidden", "after": "visible"}
     ],
     "start_timestamp": "00:15",
     "end_timestamp": "01:45"
   }
   ```

3. **Write `interaction-flows.jsonl`**: One flow per line.

### Phase 5: Regression Scenario Candidate Extraction

**Goal**: From each interaction flow, produce regression scenario candidates
tagged with `source: "video-regression"` and focused on technical behavior
verification.

Extract candidates from these patterns:

| Pattern | Regression Test Type | Priority |
|---|---|---|
| **Component renders correctly** | Render/snapshot test | High |
| **Form validation fires** | Validation logic test | High |
| **State transition completes** | Integration test | High |
| **Error state renders** | Error handling test | High |
| **Navigation completes** | Route/navigation test | Medium |
| **Conditional UI toggles** | Conditional render test | Medium |
| **Loading state appears** | Async behavior test | Medium |
| **Data displays correctly** | Data binding test | Medium |
| **List updates after mutation** | CRUD side-effect test | High |
| **Modal/dialog lifecycle** | Component lifecycle test | Medium |

**Candidate format** (regression pipeline):

```jsonc
{
  "candidate_id": "REG-VID-001",
  "test_name": "VehicleForm renders with required fields and validation",
  "test_type": "component-render",
  "priority": "high",
  "feature": "Vehicle Management",
  "component": "VehicleForm",
  "description": "VehicleForm component renders with Vehicle Name (required, text), Vehicle Type (select, 3 options), and Plate Number (required, text) fields. Create button is enabled. Cancel button is present.",
  "flow_id": "F-VEH-CREATE",
  "source": "video-regression",
  "source_evidence": "frame_000042.png",
  "confidence": 0.85,
  "route": "/vehicles/new",
  "source_file_hint": "components/vehicles/VehicleForm.tsx",
  "preconditions": [
    "User is authenticated",
    "User navigated to /vehicles/new"
  ],
  "test_steps": [
    {
      "step_number": 1,
      "action": "Render VehicleForm component",
      "assertion": "Form renders with 'Vehicle Name' input, 'Vehicle Type' select, 'Plate Number' input"
    },
    {
      "step_number": 2,
      "action": "Check required field indicators",
      "assertion": "Vehicle Name and Plate Number show required indicator (*)"
    },
    {
      "step_number": 3,
      "action": "Check Vehicle Type options",
      "assertion": "Select contains options: Heavy Duty, Light, Medium"
    },
    {
      "step_number": 4,
      "action": "Submit form with empty required fields",
      "assertion": "Validation error 'Vehicle name is required' appears"
    },
    {
      "step_number": 5,
      "action": "Fill all required fields and submit",
      "assertion": "Success toast 'Vehicle created successfully' appears, redirect to /vehicles"
    }
  ],
  "assertions": [
    "expect(screen.getByLabelText('Vehicle Name')).toBeInTheDocument()",
    "expect(screen.getByLabelText('Plate Number')).toBeRequired()",
    "expect(screen.getByRole('option')).toHaveLength(3)",
    "expect(screen.getByText('Vehicle created successfully')).toBeVisible()"
  ],
  "regression_risk": "Form validation logic, required field enforcement, select option population, success feedback rendering",
  "video_timestamp": "01:23",
  "screenshot_ref": "frame_000042.png"
}
```

Write `regression-scenario-candidates.jsonl`: One candidate per line.

---

## Constraints

1. **NEVER assume behavior not visible in frames.** Only describe what can be
   directly observed in the frame images.
2. **Use TECHNICAL TESTING LANGUAGE.** Describe component states, validation
   behavior, and interaction results. Say "form validation error appears below
   Vehicle Name field with text 'Vehicle name is required'" not "the user sees
   something went wrong".
3. **Focus on testable assertions.** Each scenario must produce concrete
   assertions — what to render, what text to check, what state to verify.
4. **Tag inferred behavior with confidence scores.** If inferred (not directly
   visible), mark confidence < 0.7.
5. **Maximum 10 frames per scene batch** sent to the model.
6. **Preserve video timestamps** from the manifest for every scene and candidate.
7. **Include regression risk description** for each scenario — what specific
   behavior could regress and why it matters.
8. **Map to components when possible.** Use route hints and visible component
   structure to suggest source file paths for targeted test generation.
9. **OCR is ON by default.** Regression tests need exact text for assertions.
   Only disable OCR if frames are too low quality for text extraction.

## Error Handling

| Issue | Resolution |
|---|---|
| `manifest.json` not found | Report error — video-regression-frame-extract must run first |
| Frames directory empty | Report error — no frames to analyze |
| Frame file missing | Skip frame, log warning, continue with remaining |
| Scene has no detectable UI | Mark as "transition/loading", extract loading state test if applicable |
| Cannot determine page type | Mark as "unknown" with confidence 0.3 |
| OCR returns empty text | Fall back to visual description only, note reduced assertion precision |

## Related Skills

| Skill | Relationship |
|---|---|
| **video-regression-frame-extract** | Upstream — produces frames/ and manifest.json consumed by this skill |
| **video-audio-extractor** | Upstream — produces transcript.json for optional narration correlation |
| **regression-orchestrator** | Downstream — receives regression-scenario-candidates.jsonl for test generation |
| **scenario-merger** | Downstream — can merge video-regression candidates with other sources |
| **regression-test-generator** | Downstream — generates test code from qualified regression scenarios |
