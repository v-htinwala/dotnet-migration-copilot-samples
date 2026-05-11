---
name: video-uat-journey-analyzer
description: >
  Analyzes extracted video frames grouped by scene using multimodal capability
  to produce structured user journey descriptions and UAT scenario candidates
  written in business language. Takes frame images and a manifest from
  video-uat-frame-extract, identifies UI pages/states per scene, detects user
  actions and transitions from the end-user perspective, infers business intent,
  and outputs journeys.jsonl and scenario-candidates.jsonl tagged source "video".
  Focuses on what the user accomplishes (business goals, acceptance criteria)
  rather than technical implementation details. Supports optional OCR enrichment
  for capturing visible UI labels and optional transcript correlation for
  narration context. Use when converting application walkthrough video frames
  into business-oriented UAT scenario candidates for the scenario-merger.
license: MIT
compatibility: >
  Requires video-uat-frame-extract skill output (frames/ directory and
  manifest.json). Works with any skills-compatible coding agent with multimodal
  (image reading) capability. OCR mode requires no additional dependencies —
  leverages the model's multimodal text extraction from images.
metadata:
  author: uat-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
---

# Video UAT Journey Analyzer

## Purpose

Analyze extracted video frames (grouped by scene) using the model's multimodal
capability to produce **UAT scenario candidates written in business language**.
This skill bridges raw video frames and testable business scenarios by observing
what the **end user accomplishes** — their goals, workflows, and acceptance
criteria — rather than the technical implementation underneath.

> **Key Differentiator vs Functional**: This skill extracts **business intent**
> (what the user achieves, why it matters) rather than technical detail (field
> names, API endpoints, validation rules). The UAT pipeline needs scenarios
> written in language that business stakeholders and end users can understand,
> review, and sign off on.

> **Multimodal approach**: Uses the model's ability to directly read images.
> The model observes frames like an end user watching a demo — noticing what
> they can do, what outcomes they see, and whether the experience meets their
> expectations.

## When to Use This Skill

- Convert video walkthrough frames into **business-oriented** UAT scenarios
- Identify user journeys, goals, and acceptance outcomes from video evidence
- Describe features from the **end-user perspective** (not the developer's)
- Produce scenario candidates for the UAT `scenario-merger` skill
- Feed scenario candidates tagged `source: "video"` to the `scenario-merger`
- **OCR mode (optional)**: When visible UI labels improve scenario clarity
- **Transcript mode**: When audio narration provides business context

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `frames_dir` | Yes | -- | Directory containing extracted frames (PNG) from video-uat-frame-extract |
| `manifest_path` | Yes | -- | Path to `manifest.json` from video-uat-frame-extract |
| `output_dir` | Yes | `uat-output/phase-1-video` | Output directory |
| `ocr_enabled` | No | `false` | Enable OCR text extraction from frames (default OFF for UAT — business language preferred over exact field names) |
| `transcript_path` | No | -- | Path to `transcript.json` from video-audio-extractor for narration correlation |

## Outputs

| File | Format | Description |
|---|---|---|
| `journeys.jsonl` | JSONL | Structured user journeys with scene references and business context |
| `scenario-candidates.jsonl` | JSONL | UAT scenario candidates tagged with `source: "video"` |

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

**Goal**: Read key transition frames and identify what the **user is doing**,
what they see, and what outcome they achieve — using business language.

For each scene batch (max 10 frames):

1. **Read frames** directly via multimodal capability (model reads images).

2. **Identify page type**: Classify from the user's perspective:
   | Type | User's View | UAT Relevance |
   |---|---|---|
   | `list` | "I see a list of my vehicles" | User can view and manage records |
   | `form` | "I'm filling out a form to add something" | User can create or edit records |
   | `detail` | "I'm viewing the details of one item" | User can inspect record information |
   | `dashboard` | "I see my overview/summary" | User gets at-a-glance status |
   | `modal` | "A dialog is asking me to confirm" | User must make a decision |
   | `drawer` | "A side panel opened with more info" | User gets contextual detail |
   | `login` | "I need to sign in" | User can authenticate |
   | `navigation` | "I'm moving to a different section" | User can navigate the application |
   | `settings` | "I'm changing my preferences" | User can configure the application |
   | `error` | "Something went wrong" | User sees clear error feedback |

3. **Identify visible user-facing elements** — describe in business language:
   - Buttons (with visible labels, described as user actions: "Save", "Cancel")
   - Forms (described as "a form to add a new vehicle", not field names)
   - Tables (described as "a list showing vehicles with their status")
   - Navigation items (menu labels as user sees them)
   - Status indicators (what the user understands: "Active", "Pending")
   - Outcomes (success messages, confirmations, error feedback)

4. **Detect transitions**: Compare frames within the scene:
   - What did the user do? (clicked, filled, navigated)
   - What was the **user-visible outcome**?
   - Was the user's goal achieved?
   - Did the user encounter an error or unexpected behavior?

5. **Output per scene** (UAT format):
   ```jsonc
   {
     "scene_id": "S-003",
     "page_type": "form",
     "page_title": "Create Vehicle",
     "route_hint": "/vehicles/new",
     "visible_elements": ["Vehicle name field", "Vehicle type selector", "Plate number field", "Create button", "Cancel button"],
     "user_context": "User is adding a new vehicle to the fleet",
     "data_context": ["Vehicle types available: Heavy Duty, Light, Medium"],
     "transitions": [
       {
         "from_frame": "frame_000042.png",
         "to_frame": "frame_000045.png",
         "action": "User filled in vehicle details and clicked Create",
         "result": "Success message appeared, user returned to vehicle list with new vehicle visible",
         "user_goal_achieved": true
       }
     ],
     "confidence": 0.85
   }
   ```

### Phase 3: OCR Enrichment (Optional — when `ocr_enabled: true`)

**Goal**: Extract visible UI text to improve the clarity of business-language
scenario descriptions. Even in UAT mode, exact button labels and menu names
make scenarios more precise.

> This phase is **skipped by default** (`ocr_enabled: false`). UAT scenarios
> prioritize business language over technical precision. Enable OCR when exact
> UI labels improve scenario clarity for stakeholder review.

For each scene's key transition frames:

1. **Extract button labels**: Read all visible button text.
   ```json
   "ocr_buttons": ["Add Vehicle", "Save", "Cancel", "Delete", "Export"]
   ```

2. **Extract navigation items**: Menu items, breadcrumbs, tab labels.
   ```json
   "ocr_navigation": ["Dashboard", "Vehicles", "Bookings", "Users", "Reports", "Settings"]
   ```

3. **Extract visible messages**: Success messages, error messages, help text.
   ```json
   "ocr_messages": ["Vehicle created successfully", "Are you sure you want to delete?"]
   ```

4. **Extract data context**: Dropdown options, status values — described as
   choices available to the user.
   ```json
   "ocr_data": {
     "available_options": {"Vehicle Type": ["Heavy Duty", "Light", "Medium"]},
     "status_values": ["Active", "Inactive", "Maintenance"]
   }
   ```

5. **Merge with scene analysis**: Use OCR text to make business-language
   descriptions more precise (e.g., "clicks the 'Add Vehicle' button" instead
   of "clicks a button").

### Phase 3b: Transcript Correlation (Optional — when `transcript_path` provided)

**Goal**: Correlate timestamped transcript segments with scenes to add business
context from the narrator.

1. **Load transcript**: Parse `transcript.json` from video-audio-extractor.

2. **Match segments to scenes**: For each scene, find transcript segments whose
   time range overlaps with the scene's timestamp range.

3. **Extract business intent from narration**: Look for narrator mentions of:
   - User goals ("here's how a fleet manager adds a new vehicle")
   - Business reasons ("this helps track the fleet inventory")
   - Acceptance criteria ("notice the success confirmation")
   - User expectations ("the user expects to see the new vehicle in the list")

4. **Add narration context**:
   ```json
   "narration": "Now I'll show you how a fleet manager adds a new vehicle to the system",
   "narration_intent": "Demonstrating vehicle creation workflow for fleet managers"
   ```

5. **Boost confidence**: Scenes with matching narration get +0.10 confidence
   boost (capped at 1.0).

### Phase 4: Journey Construction

**Goal**: Chain scene analyses into sequential user journeys described from
the business perspective.

1. **Group related scenes** into logical business journeys:
   - Scenes following a user goal (create a vehicle, make a booking)
   - Scenes forming a complete business workflow (start to finish)
   - Scenes involving the same business domain (fleet management, reservations)
   - Scenes showing user satisfaction or frustration (success/error paths)

2. **Build journey records** (UAT format):
   ```jsonc
   {
     "journey_id": "J-VEH-CRUD",
     "journey_name": "Fleet Manager Adds and Manages Vehicles",
     "business_intent": "Fleet manager manages vehicle records to maintain accurate fleet inventory",
     "acceptance_criteria": [
       "Fleet manager can add a new vehicle with required details",
       "New vehicle appears in the fleet list after creation",
       "Fleet manager can view vehicle details",
       "Fleet manager can edit vehicle information"
     ],
     "scenes": ["S-001", "S-002", "S-003", "S-004"],
     "actions": [
       "Navigate to Vehicle Management page",
       "View list of existing vehicles in the fleet",
       "Click to add a new vehicle",
       "Fill in vehicle details",
       "Save the new vehicle",
       "Confirm new vehicle appears in the fleet list"
     ],
     "start_timestamp": "00:15",
     "end_timestamp": "01:45",
     "user_role": "Fleet Manager",
     "business_domain": "Fleet Management"
   }
   ```

3. **Write `journeys.jsonl`**: One journey per line.

### Phase 5: Scenario Candidate Extraction

**Goal**: From each journey, produce UAT scenario candidates tagged with
`source: "video"` and written in business language for the `scenario-merger`.

Extract candidates from these patterns:

| Pattern | UAT Relevance |
|---|---|
| **User achieves a goal** | Primary acceptance scenario |
| **User encounters an error** | Error handling from user perspective |
| **User navigates to a feature** | Accessibility and discoverability |
| **User completes a multi-step workflow** | End-to-end business process |
| **User sees expected outcome** | Acceptance criteria verification |
| **User performs a role-specific action** | Role-based access scenario |

**Candidate format** (UAT pipeline):

```jsonc
{
  "candidate_id": "VID-001",
  "test_name": "Fleet manager creates a new vehicle",
  "feature": "Vehicle Management",
  "action": "Add new vehicle to the fleet",
  "description": "Fleet manager fills out the vehicle creation form with vehicle name, type, and plate number, then saves to add the vehicle to the fleet inventory",
  "journey_id": "J-VEH-CRUD",
  "source": "video",
  "source_evidence": "frame_000042",
  "confidence": 0.85,
  "user_role": "Fleet Manager",
  "business_objective": "Maintain accurate fleet inventory by adding new vehicles",
  "acceptance_criteria": [
    "User can access the vehicle creation form",
    "User can fill in required vehicle details",
    "Vehicle is saved and appears in the fleet list",
    "User receives confirmation of successful creation"
  ],
  "preconditions": ["User is logged in as Fleet Manager", "User is on the Vehicle Management page"],
  "test_steps": [
    {
      "step_number": 1,
      "action": "Click the 'Add Vehicle' button",
      "expected": "Vehicle creation form is displayed"
    },
    {
      "step_number": 2,
      "action": "Fill in vehicle name, select vehicle type, and enter plate number",
      "expected": "Form fields accept the input without errors"
    },
    {
      "step_number": 3,
      "action": "Click 'Save' to create the vehicle",
      "expected": "Success confirmation shown, vehicle list displays the new vehicle"
    }
  ],
  "expected_result": "New vehicle is added to the fleet and visible in the vehicle list",
  "video_timestamp": "01:23",
  "screenshot_ref": "",
  "component_path": ""
}
```

Write `scenario-candidates.jsonl`: One candidate per line.

---

## Constraints

1. **NEVER assume actions not visible in frames.** Only describe what can be
   directly observed in the frame images.
2. **Use BUSINESS LANGUAGE, not technical identifiers.** Describe what the user
   does and sees, not the underlying implementation. Say "fill in vehicle name"
   not "enter value in name field with maxlength 100". Say "save the vehicle"
   not "POST to /api/vehicles".
3. **Focus on user goals and outcomes.** Each scenario should answer: "What is
   the user trying to accomplish?" and "How do they know it worked?"
4. **Tag inferred actions with confidence scores.** If inferred (not directly
   visible), mark confidence < 0.7.
5. **Maximum 10 frames per scene batch** sent to the model.
6. **Preserve video timestamps** from the manifest for every scene and candidate.
7. **Include acceptance criteria** for each scenario — what would a business
   stakeholder check to confirm the feature works?
8. **Describe from the user's perspective.** Use phrases like "the user sees",
   "the user can", "the system shows" — not "the component renders" or
   "the API returns".

## Error Handling

| Issue | Resolution |
|---|---|
| `manifest.json` not found | Report error — video-uat-frame-extract must run first |
| Frames directory empty | Report error — no frames to analyze |
| Frame file missing | Skip frame, log warning, continue with remaining |
| Scene has no detectable UI | Mark as "transition/loading", skip journey extraction |
| Cannot determine page type | Mark as "unknown" with confidence 0.3 |

## Related Skills

| Skill | Relationship |
|---|---|
| **video-uat-frame-extract** | Upstream — produces frames/ and manifest.json consumed by this skill |
| **video-audio-extractor** | Upstream — produces transcript.json for optional narration correlation |
| **scenario-merger** | Downstream — receives scenario-candidates.jsonl for UAT cross-source merging |
| **uat-qualification-gate** | Downstream — qualifies merged scenarios for UAT test generation |
| **uat-test-case-generator** | Downstream — generates UAT test cases from qualified scenarios |
