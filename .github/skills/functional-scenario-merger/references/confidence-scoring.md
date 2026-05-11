# Confidence Scoring — functional-scenario-merger

Rules for assigning confidence scores to merged scenario candidates.

---

## Scoring Model

Confidence represents the likelihood that a scenario candidate accurately
describes a real, testable feature. Higher confidence → higher priority for
test case generation.

### Base Score by Source Count

| Sources Confirming | Base Confidence | Range |
|---|---|---|
| 3 (video + url + codebase) | 0.95 | 0.90 - 1.00 |
| 2 (any two sources) | 0.80 | 0.70 - 0.89 |
| 1 (single source) | 0.50 | 0.30 - 0.69 |

### Adjustment Factors

Apply these adjustments (cumulative) to the base confidence:

| Factor | Adjustment | Condition |
|---|---|---|
| Specific fields discovered | +0.03 | >2 named fields |
| Detailed validation rules | +0.03 | Has regex/min/max constraints |
| API endpoint confirmed | +0.03 | Has endpoint + HTTP method |
| Response codes known | +0.02 | Has specific status codes |
| Auth requirements known | +0.02 | Has auth_required and roles |
| Model/entity mapped | +0.02 | Has database model reference |
| Screenshot evidence | +0.01 | Has screenshot_ref |
| Video timestamp | +0.01 | Has video_timestamp |
| Component path | +0.01 | Has component_path |
| Vague description only | -0.10 | No fields, no validation, no endpoint |
| Fuzzy match used | -0.05 | Matched via Tier 5 (fuzzy) |
| Conflict detected | -0.05 | Has conflict_flag: true |

### Maximum Adjustments

| Sources | Max Upward | Max Downward |
|---|---|---|
| 3 sources | +0.05 (cap at 1.0) | -0.05 (floor at 0.90) |
| 2 sources | +0.09 (cap at 0.89) | -0.10 (floor at 0.70) |
| 1 source | +0.19 (cap at 0.69) | -0.20 (floor at 0.30) |

---

## Source Reliability by Information Type

Different sources are more reliable for different types of information:

| Information Type | Most Reliable Source | Reliability Rating |
|---|---|---|
| API endpoint + method | Codebase | ★★★★★ |
| Validation rules (regex, min/max) | Codebase | ★★★★★ |
| Database model structure | Codebase | ★★★★★ |
| Auth/role requirements | Codebase | ★★★★☆ |
| Form field names + labels | URL | ★★★★★ |
| Form field types (select, text) | URL | ★★★★★ |
| Required field indicators | URL | ★★★★☆ |
| Page layout and navigation | URL | ★★★★☆ |
| User workflow sequence | Video | ★★★★★ |
| Feature importance (what's demoed) | Video | ★★★★☆ |
| Error message text | URL / Video | ★★★★☆ |
| UI label text | Video (with OCR) | ★★★☆☆ |
| Business logic branching | Codebase | ★★★★☆ |

### Cross-Source Confirmation Bonus

When two sources agree on the same specific detail, the merged confidence
for that detail is boosted:

| Agreement Type | Bonus |
|---|---|
| Field name matches across sources | +0.02 per matching field |
| Validation rule matches | +0.03 per matching rule |
| Endpoint matches | +0.05 |
| Feature action matches exactly | +0.03 |

**Cap**: Total bonus from cross-source confirmation capped at +0.10 above
base confidence.

---

## Worked Examples

### Example 1: Three-Source Match (High Confidence)

**Video candidate**: Feature "Vehicle", action "Create", fields ["name", "type"],
timestamp "01:23"

**URL candidate**: Feature "Vehicles", action "Add vehicle", fields ["name",
"type", "plate_number"], screenshot "vehicles-new.png", validation
[{name: required, maxlength:100}]

**Codebase candidate**: Feature "Vehicle Management", action "Create vehicle",
fields ["name", "type", "plate_number", "registration_date", "status"],
endpoint POST /api/vehicles, validations [{name: required, max:100},
{plate_number: regex}]

**Scoring**:
- Base: 0.95 (3 sources)
- +0.03 (>2 fields: 5 unique fields)
- +0.03 (detailed validations)
- +0.03 (API endpoint confirmed)
- +0.02 (response codes from codebase)
- +0.01 (screenshot evidence)
- +0.01 (video timestamp)
- +0.01 (component path)
- Subtotal adjustments: +0.14 → capped at +0.05
- **Final: 1.00** (capped at 1.0)

### Example 2: Two-Source Match (Medium Confidence)

**URL candidate**: Feature "Settings", action "Update profile", fields
["display_name", "email", "avatar"], screenshot "settings-profile.png"

**Codebase candidate**: Feature "User Settings", action "Update user profile",
fields ["display_name", "email", "avatar", "timezone"],
endpoint PUT /api/users/me, validations [{email: required, email}]

**Scoring**:
- Base: 0.80 (2 sources)
- +0.03 (>2 fields)
- +0.03 (validation: email format)
- +0.03 (endpoint confirmed)
- +0.01 (screenshot)
- +0.01 (component path)
- Subtotal adjustments: +0.11 → capped at +0.09
- **Final: 0.89**

### Example 3: Single Source (Low Confidence)

**Codebase candidate**: Feature "Audit Log", action "View audit trail",
endpoint GET /api/admin/audit, auth_required: true, roles: ["admin"],
fields ["timestamp", "user", "action", "resource"]

**Scoring**:
- Base: 0.50 (1 source — codebase → base 0.60)
- +0.03 (>2 fields)
- +0.03 (endpoint)
- +0.02 (auth requirements)
- Subtotal adjustments: +0.08
- **Final: 0.68**

### Example 4: Single Source, Low Quality

**Video candidate**: Feature "Some page", action "User clicks something",
description "User navigates to a page and clicks around", confidence 0.4

**Scoring**:
- Base: 0.40 (1 source — video → base 0.40)
- -0.10 (vague description, no fields/validation/endpoint)
- **Final: 0.30** (floor)
