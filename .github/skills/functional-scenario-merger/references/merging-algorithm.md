# Merging Algorithm — functional-scenario-merger

Detailed matching and merging logic for combining scenario candidates across
sources.

---

## Candidate Matching

### Matching Pipeline

Candidates from different sources are matched using a tiered approach. Each
tier is tried in order; the first match wins.

```
For each unmatched candidate C:
    1. Try EXACT match (same feature + action, normalized)
    2. Try ENDPOINT match (same API endpoint + method)
    3. Try COMPONENT match (same component_path)
    4. Try FIELD OVERLAP match (>60% field overlap)
    5. Try FUZZY match (>80% feature name similarity + similar action verb)
    6. No match → C is unique to its source
```

### Tier 1: Exact Match

Normalize and compare feature + action pairs.

**Normalization**:
```
normalize_feature("Vehicle Management") → "vehicle"
normalize_feature("User Management Module") → "user"
normalize_feature("Authentication") → "auth"
normalize_feature("Booking System") → "booking"

normalize_action("Create new vehicle") → "create vehicle"
normalize_action("Add a new vehicle") → "create vehicle"
normalize_action("List all vehicles") → "list vehicle"
```

**Feature normalization rules**:
1. Lowercase everything
2. Remove suffix words: "management", "module", "page", "system", "feature"
3. Remove articles: "a", "an", "the"
4. Apply synonym map:
   - auth / authentication / login / signin → "auth"
   - register / signup / sign-up / create account → "register"
   - settings / preferences / configuration / config → "settings"
   - dashboard / home / overview / summary → "dashboard"

**Action normalization rules**:
1. Lowercase everything
2. Map CRUD verbs:
   - create / add / new / insert / register → "create"
   - read / view / get / show / display / list / browse / search → varies by context
   - update / edit / modify / change / put / patch → "update"
   - delete / remove / destroy / archive → "delete"
3. Remove filler words: "a", "an", "the", "new", "all"
4. Keep the object noun: "create vehicle", "list booking", "update user"

**Match condition**: `normalized_feature(A) == normalized_feature(B) AND
normalized_action(A) == normalized_action(B)`

### Tier 2: Endpoint Match

Compare `discovered_endpoints` across candidates.

**Match condition**: Any endpoint in candidate A matches an endpoint in
candidate B where `endpoint_path` AND `http_method` are identical.

```
A.discovered_endpoints = [{"endpoint": "/api/vehicles", "method": "POST"}]
B.discovered_endpoints = [{"endpoint": "/api/vehicles", "method": "POST"}]
→ MATCH
```

**Path normalization**:
- Strip trailing slashes: `/api/vehicles/` → `/api/vehicles`
- Normalize param syntax: `/vehicles/:id` = `/vehicles/{id}` = `/vehicles/<id>`
- Case-insensitive comparison

### Tier 3: Component Match

Compare `component_path` across candidates.

**Match condition**: Same component file path (normalized).

```
A.component_path = "src/pages/vehicles/CreateVehicle.tsx"
B.component_path = "src/pages/vehicles/CreateVehicle.tsx"
→ MATCH
```

### Tier 4: Field Overlap Match

Compare `discovered_fields` arrays.

**Overlap calculation**:
```
fields_A = set(A.discovered_fields)
fields_B = set(B.discovered_fields)
overlap = len(fields_A & fields_B) / len(fields_A | fields_B)  # Jaccard
```

**Match condition**: `overlap > 0.6` AND features belong to similar domains
(both have "vehicle" in feature name, or both reference the same model).

**Guard**: Field overlap alone can produce false positives. Require at least
one additional signal:
- Same or similar feature name (>50% string similarity)
- Same model/entity reference
- Same page URL reference

### Tier 5: Fuzzy Match

Use string similarity (Levenshtein ratio) on feature + action names.

**Match condition**:
```
feature_similarity(A, B) > 0.80
AND action_verb(A) == action_verb(B)  # Same CRUD verb after normalization
```

**Examples**:
- "Vehicle Management" vs "Vehicles" → similarity 0.75 → too low (but
  after normalization both become "vehicle" → exact match in Tier 1)
- "Booking Creation" vs "Create Booking" → verb match ("create" = "create"),
  feature match ("booking"), → MATCH

---

## Merge Strategy

### Union Merge Rules

When two or more candidates match:

| Field | Merge Strategy |
|---|---|
| `feature` | Use most descriptive version (longest after removing generic suffixes) |
| `module` | Derive from feature (e.g., "Vehicle Management" → "Vehicles") |
| `action` | Use most descriptive version |
| `description` | Concatenate unique descriptions from each source |
| `discovered_fields` | **UNION** of all fields |
| `discovered_validations` | **UNION** of all validations (per field) |
| `discovered_endpoints` | **UNION** of all endpoints |
| `video_timestamp` | From video source (empty if no video) |
| `screenshot_ref` | From URL source (empty if no URL) |
| `component_path` | From codebase source (empty if no codebase) |
| `confidence` | Calculated from confirmation count (see confidence scoring) |

### Module Derivation

Auto-derive `module` from `feature` for test ID generation:

| Feature | Module | Module Code |
|---|---|---|
| Vehicle Management | Vehicles | VEH |
| User Management | Users | USR |
| Authentication | Auth | AUTH |
| Booking System | Bookings | BOOK |
| Dashboard | Dashboard | DASH |
| Settings | Settings | SET |
| Fleet Management | Fleet | FLT |
| Reports | Reports | RPT |

**Module code rules**:
- Use first 3-4 characters of module name (uppercase)
- Ensure uniqueness within the project
- If collision, extend to 5 characters or use abbreviation

---

## Handling Single-Source Candidates

Candidates that don't match any other source:

1. **Include in merged output** — never drop single-source candidates
2. **Set confidence**: Based on single-source scoring (0.3-0.69)
3. **Set `sources_found`**: Single source array, e.g., `["codebase"]`
4. **Set `confirmation_count`**: 1
5. **Note in merge report**: Count of single-source candidates per source

### Single-Source Confidence Adjustment

| Source | Base Confidence | Rationale |
|---|---|---|
| Codebase | 0.60 | Code structure is reliable but might not reflect live behavior |
| URL | 0.55 | Live observation is real but may miss hidden features |
| Video | 0.40 | Visual inference is less precise than code/live analysis |

Adjust within range based on evidence quality:
- Has specific field names → +0.05
- Has validation rules → +0.05
- Has endpoint details → +0.05
- Vague description only → -0.10
