---
name: functional-scenario-merger
description: >
  Merges functional test scenario candidates from multiple sources (video, URL,
  codebase) into a unified feature map. Performs union of all discovered fields
  per feature, tags each field with its discovery source, assigns confidence
  scores based on source confirmation count (3 sources = 0.9-1.0, 2 = 0.7-0.89,
  1 = 0.3-0.69), and flags conflicts without silent resolution. Outputs
  merged-scenarios.jsonl, feature-map.json for human checkpoint review, and
  merge-report.json with statistics. Use when combining scenario candidates
  from video-journey-analyzer, url-functional-explorer, and
  codebase-functional-analyzer into a single deduplicated, enriched set for
  functional test case generation.
license: MIT
compatibility: >
  Works with any skills-compatible coding agent with file system read/write
  access. No external dependencies.
metadata:
  author: functional-test-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
---

# Functional Scenario Merger

## Purpose

Merge scenario candidates from all available sources (video, URL, codebase) into
a unified, deduplicated feature map. The merger combines discoveries from each
source using a union strategy — when the same feature appears in multiple sources,
ALL discovered fields from every source are combined. Conflicts are flagged but
never silently resolved.

This step is critical for producing comprehensive functional test cases because
each source discovers different aspects:
- **Video**: Reveals user workflows, UI labels, button text, navigation paths
- **URL**: Reveals actual form fields, validation attributes, live page structure
- **Codebase**: Reveals API endpoints, database models, validation rules, auth

The merger creates a richer picture than any single source alone.

## When to Use This Skill

- After one or more source-specific analysis skills have produced scenario
  candidates (at least one `scenario-candidates.jsonl` file required)
- Before functional test case generation
- When combining discoveries from different analysis approaches

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `video_candidates` | No | — | Path to `scenario-candidates.jsonl` from video-journey-analyzer |
| `url_candidates` | No | — | Path to `scenario-candidates.jsonl` from url-functional-explorer |
| `codebase_candidates` | No | — | Path to `scenario-candidates.jsonl` from codebase-functional-analyzer |
| `output_dir` | Yes | — | Output directory |

**Constraint**: At least one candidate file must be provided.

## Outputs

| File | Format | Description |
|---|---|---|
| `merged-scenarios.jsonl` | JSONL | Unified scenario set with union of fields |
| `feature-map.json` | JSON | Feature inventory for human checkpoint review |
| `merge-report.json` | JSON | Statistics: duplicates, conflicts, source counts |

---

## 4-Phase Merging Workflow

### Phase 1: Load & Normalize

**Goal**: Load all candidate JSONL files and normalize to a common format.

1. **Load each file**: Parse each JSONL file line by line.
2. **Tag source origin**: Each candidate already has a `source` field
   ("video", "url", or "codebase"). Verify this is set correctly.
3. **Normalize feature names**: Standardize feature names for matching:
   - Lowercase comparison
   - Strip common suffixes: "Management", "Module", "Page"
   - Map synonyms: "Auth" = "Authentication" = "Login"
   - Record original name for display
4. **Normalize action names**: Standardize actions:
   - "Create new vehicle" = "Add vehicle" = "Create vehicle"
   - "List vehicles" = "View all vehicles" = "Vehicle list"
   - Map CRUD verbs: Create/Add/New, Read/View/Get, Update/Edit/Modify,
     Delete/Remove/Destroy

### Phase 2: Feature Grouping & Matching

**Goal**: Group candidates by feature and match same-feature candidates
across sources.

See [references/merging-algorithm.md](references/merging-algorithm.md) for detailed matching logic.

**Matching hierarchy** (try in order, use first match):

1. **Exact feature + action match**: Same normalized feature AND action
2. **Endpoint match**: Same API endpoint (e.g., `POST /api/vehicles`)
3. **Component match**: Same `component_path` reference
4. **Field overlap**: >60% of `discovered_fields` overlap between candidates
5. **Fuzzy feature match**: Feature names with >80% string similarity AND
   similar action verbs (both are "Create" actions)

**No match found**: Candidate is unique to its source — include as-is with
confidence based on single-source scoring.

### Phase 3: Union Merge

**Goal**: For matched candidates, merge ALL discovered information.

For each group of matched candidates:

1. **Merge fields** (UNION):
   ```
   candidate_A.discovered_fields = ["name", "type"]
   candidate_B.discovered_fields = ["name", "type", "plate_number"]
   candidate_C.discovered_fields = ["name", "plate_number", "status"]

   merged.discovered_fields = ["name", "type", "plate_number", "status"]
   ```

2. **Tag field sources**:
   ```json
   "field_sources": {
     "name": ["video", "url", "codebase"],
     "type": ["video", "url"],
     "plate_number": ["url", "codebase"],
     "status": ["codebase"]
   }
   ```

3. **Merge validations** (union of all discovered rules):
   - If same field has validations from multiple sources, include ALL
   - Example: URL says `maxlength: 100`, codebase says `max: 100, required`
     → merged validation: `required, max: 100`

4. **Merge endpoints** (union):
   - Codebase provides `{"endpoint": "/api/vehicles", "method": "POST"}`
   - URL exploration found a form posting to the same endpoint
   - Merge with both sources tagged

5. **Set evidence references**:
   - `video_timestamp` from video candidate
   - `screenshot_ref` from URL candidate
   - `component_path` from codebase candidate

6. **Detect conflicts** (see conflict handling below).

7. **Assign merged ID**: `MRG-{MODULE}-{SEQ}` (e.g., `MRG-VEH-001`).

### Phase 4: Confidence Scoring & Output

**Goal**: Assign confidence scores and produce all output files.

See [references/confidence-scoring.md](references/confidence-scoring.md) for detailed rules.

**Confidence scoring**:

| Source Count | Confidence Range | Rationale |
|---|---|---|
| 3 sources confirm | 0.90 - 1.00 | High confidence — verified across all inputs |
| 2 sources confirm | 0.70 - 0.89 | Good confidence — partial cross-verification |
| 1 source only | 0.30 - 0.69 | Low confidence — unverified single-source discovery |

**Within each range**, adjust based on:
- Quality of evidence (specific field/validation details → higher)
- Source reliability for this type of info (codebase for API details → higher,
  video for UI workflow → higher)
- Matching precision (exact match → higher, fuzzy match → lower)

**Output: merged-scenarios.jsonl**

```json
{
  "merged_id": "MRG-VEH-001",
  "feature": "Vehicle Management",
  "module": "Vehicles",
  "action": "Create new vehicle",
  "description": "User fills out vehicle creation form and submits",
  "source": "merged",
  "sources_found": ["video", "url", "codebase"],
  "confirmation_count": 3,
  "confidence": 0.95,
  "discovered_fields": ["name", "type", "plate_number", "registration_date", "status"],
  "field_sources": {
    "name": ["video", "url", "codebase"],
    "type": ["video", "url", "codebase"],
    "plate_number": ["url", "codebase"],
    "registration_date": ["codebase"],
    "status": ["url"]
  },
  "discovered_endpoints": [
    {"endpoint": "/api/vehicles", "method": "POST", "source": "codebase"}
  ],
  "discovered_validations": [
    {"field": "name", "rule": "required, max:100", "source": "codebase"},
    {"field": "plate_number", "rule": "required, pattern:[A-Z]{2}[0-9]{4}", "source": "url"}
  ],
  "video_timestamp": "01:23",
  "screenshot_ref": "screenshots/vehicles-new.png",
  "component_path": "src/pages/vehicles/CreateVehicle.tsx",
  "conflict_flag": false,
  "conflict_details": ""
}
```

**Output: feature-map.json** (for checkpoint review):

```json
{
  "total_features": 8,
  "total_scenarios": 42,
  "source_coverage": {
    "video": 15,
    "url": 28,
    "codebase": 35,
    "all_three": 12,
    "two_sources": 18,
    "single_source": 12
  },
  "features": [
    {
      "feature": "Vehicle Management",
      "module": "Vehicles",
      "scenario_count": 8,
      "confidence_avg": 0.88,
      "sources": ["video", "url", "codebase"],
      "actions": ["Create", "List", "View", "Edit", "Delete"],
      "total_fields": 5,
      "has_conflicts": false
    }
  ],
  "conflicts": []
}
```

**Output: merge-report.json**:

```json
{
  "inputs": {
    "video_candidates": 15,
    "url_candidates": 28,
    "codebase_candidates": 35
  },
  "total_input_candidates": 78,
  "merged_scenarios": 42,
  "duplicates_removed": 36,
  "conflicts_detected": 2,
  "features_discovered": 8,
  "avg_confidence": 0.82,
  "confidence_distribution": {
    "high_0.9_1.0": 12,
    "medium_0.7_0.89": 18,
    "low_0.3_0.69": 12
  }
}
```

---

## Conflict Handling

**Rule**: NEVER silently resolve conflicts. Include ALL conflicting versions
and flag them.

### Conflict Detection

A conflict occurs when two sources provide **contradictory** information for
the same feature + field:

| Conflict Type | Example |
|---|---|
| **Field required vs optional** | URL says `required`, codebase says `optional` |
| **Different max length** | URL says `maxlength: 50`, codebase says `max: 100` |
| **Different enum values** | URL dropdown has 3 options, codebase enum has 5 |
| **Different endpoint** | URL form posts to `/api/v1/...`, codebase has `/api/v2/...` |
| **Auth disagreement** | URL page is publicly accessible, codebase says `auth_required: true` |

### Conflict Output Format

```json
{
  "conflict_flag": true,
  "conflict_details": "Field 'name' max length: url says 50, codebase says 100. Field 'type' enum values differ: url has [Heavy, Light, Medium], codebase has [Heavy Duty, Light, Medium, Extra Heavy, Trailer]."
}
```

### What is NOT a Conflict

- One source has a field, another doesn't → not a conflict (union merge)
- One source has validation details, another doesn't → not a conflict (add both)
- Different confidence levels → not a conflict (average them)
- Different descriptions → not a conflict (concatenate or prefer more detailed)

---

## Constraints

1. **Union, not intersection**: Always merge by UNION. Never drop a field
   because it only appears in one source.
2. **No silent resolution**: Conflicts are flagged with `conflict_flag: true`
   and full `conflict_details`. The human checkpoint (feature map review)
   is where conflicts get resolved.
3. **Preserve all evidence**: Never discard source references (timestamps,
   screenshots, component paths) — merge them all.
4. **Incremental write**: Write `merged-scenarios.jsonl` incrementally for
   resume capability on failure.
5. **Deterministic**: Same inputs always produce the same output (sort
   candidates by merged_id for stable ordering).

## Error Handling

| Error | Behavior |
|---|---|
| No candidate files provided | Fail with clear error |
| All candidate files empty | Output empty merged file + report with 0 counts |
| Malformed JSONL line | Skip line, log warning, continue |
| Candidate missing required fields | Fill defaults, set confidence to 0.3, log warning |
| Very large input (>1000 candidates) | Process in batches of 200, merge batches |

## Related Skills

| Skill | Relationship |
|---|---|
| **video-journey-analyzer** | Upstream — provides video-sourced candidates |
| **url-functional-explorer** | Upstream — provides URL-sourced candidates |
| **codebase-functional-analyzer** | Upstream — provides codebase-sourced candidates |
| **functional-test-generator** | Downstream — consumes merged-scenarios.jsonl |
| **functional-test-orchestrator** | Orchestrator — triggers feature map checkpoint after merge |
