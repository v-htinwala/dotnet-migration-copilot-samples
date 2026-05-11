# Output Schemas — codebase-functional-analyzer

JSON schemas and examples for all output artifacts.

---

## 1. api-catalog.jsonl

One line per API endpoint. Each line is a valid JSON object.

### Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `endpoint` | string | Yes | URL path (e.g., `/api/vehicles`) |
| `method` | string | Yes | HTTP method: GET, POST, PUT, PATCH, DELETE |
| `handler` | string | Yes | Handler function/method name |
| `handler_file` | string | Yes | Source file path relative to codebase root |
| `handler_line` | number | No | Line number in source file |
| `middleware` | string[] | No | Middleware chain names |
| `auth_required` | boolean | Yes | Whether authentication is required |
| `auth_roles` | string[] | No | Required roles (empty if no role check) |
| `request_body_fields` | object[] | No | Request body field definitions |
| `response_codes` | number[] | No | Expected HTTP status codes |
| `query_params` | object[] | No | Query parameter definitions |
| `path_params` | object[] | No | URL path parameter definitions |
| `related_model` | string | No | Primary database model name |

### Request Body Field Schema

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Field name |
| `type` | string | Data type: string, number, boolean, enum, date, email, etc. |
| `required` | boolean | Whether field is required |
| `max_length` | number | Maximum string length (if applicable) |
| `min_length` | number | Minimum string length (if applicable) |
| `min_value` | number | Minimum numeric value |
| `max_value` | number | Maximum numeric value |
| `validation_regex` | string | Regex pattern for validation |
| `values` | string[] | Enum values (if type is enum) |
| `default` | any | Default value |

### Example

```jsonl
{"endpoint":"/api/vehicles","method":"GET","handler":"listVehicles","handler_file":"src/routes/vehicles.ts","handler_line":15,"middleware":["auth"],"auth_required":true,"auth_roles":[],"request_body_fields":[],"response_codes":[200,401],"query_params":[{"name":"page","type":"number","required":false,"default":1},{"name":"limit","type":"number","required":false,"default":20}],"path_params":[],"related_model":"Vehicle"}
{"endpoint":"/api/vehicles","method":"POST","handler":"createVehicle","handler_file":"src/routes/vehicles.ts","handler_line":42,"middleware":["auth","validate"],"auth_required":true,"auth_roles":["admin","fleet-manager"],"request_body_fields":[{"name":"name","type":"string","required":true,"max_length":100},{"name":"type","type":"enum","required":true,"values":["Heavy Duty","Light","Medium"]},{"name":"plate_number","type":"string","required":true,"validation_regex":"^[A-Z]{2}[0-9]{4}$"}],"response_codes":[201,400,401,403,409],"query_params":[],"path_params":[],"related_model":"Vehicle"}
{"endpoint":"/api/vehicles/:id","method":"GET","handler":"getVehicle","handler_file":"src/routes/vehicles.ts","handler_line":78,"middleware":["auth"],"auth_required":true,"auth_roles":[],"request_body_fields":[],"response_codes":[200,401,404],"query_params":[],"path_params":[{"name":"id","type":"uuid"}],"related_model":"Vehicle"}
```

---

## 2. route-map.json

Frontend route tree structure.

### Schema

```json
{
  "framework": "string — React Router | Next.js Pages | Next.js App | Angular | Vue Router | SvelteKit",
  "routes": [
    {
      "path": "string — URL path pattern",
      "component": "string — component/page name",
      "component_file": "string — source file path",
      "layout": "string | null — layout wrapper component",
      "auth_required": "boolean",
      "params": [
        {"name": "string", "type": "string — dynamic | catchAll | optional"}
      ],
      "meta": {"title": "string", "description": "string"},
      "children": ["(recursive route objects)"]
    }
  ],
  "navigation_menus": [
    {
      "location": "string — sidebar | header | footer",
      "items": ["string — menu label"],
      "source_file": "string — file containing navigation definition"
    }
  ]
}
```

---

## 3. component-tree.json

Component hierarchy for SPAs.

### Schema

```json
{
  "framework": "string — React | Angular | Vue | Svelte",
  "root": "string — root component name (usually App)",
  "total_components": "number",
  "components": [
    {
      "name": "string — component name",
      "file": "string — source file path",
      "type": "string — page | form | list | detail | modal | drawer | layout | widget | navigation",
      "children": ["string — child component names"],
      "props": ["string — prop names"],
      "state": ["string — state variable names"],
      "api_calls": ["string — endpoint + method, e.g., '/api/vehicles GET'"],
      "form_fields": ["string — field names (if form component)"],
      "event_handlers": ["string — handler names"]
    }
  ]
}
```

### Component Type Classification

| Type | Heuristics |
|---|---|
| `page` | Mapped to a route, top-level page component |
| `form` | Contains `<form>`, input elements, submit handler |
| `list` | Contains `<table>`, `.map()` rendering, pagination |
| `detail` | Displays single record, uses path param (`:id`) |
| `modal` | Uses dialog/modal library, overlay styling |
| `drawer` | Side panel component |
| `layout` | Wraps other components, provides navigation/header/footer |
| `widget` | Small reusable UI element (button, card, badge) |
| `navigation` | Menu, sidebar, breadcrumb component |

---

## 4. models.json

Database model/entity definitions.

### Schema

```json
{
  "orm": "string — Prisma | TypeORM | Sequelize | Django ORM | SQLAlchemy | JPA | ActiveRecord | Eloquent | EF Core",
  "database": "string | null — PostgreSQL | MySQL | SQLite | MongoDB | etc.",
  "models": [
    {
      "name": "string — model/entity name",
      "file": "string — source file path",
      "table_name": "string — database table name",
      "fields": [
        {
          "name": "string — field name",
          "type": "string — uuid | string | integer | float | boolean | date | datetime | enum | json | text",
          "primary_key": "boolean",
          "auto_generated": "boolean",
          "required": "boolean",
          "unique": "boolean",
          "max_length": "number | null",
          "min_length": "number | null",
          "min_value": "number | null",
          "max_value": "number | null",
          "default": "any | null",
          "values": ["string — enum values (if enum type)"],
          "validation_regex": "string | null"
        }
      ],
      "relationships": [
        {
          "type": "string — hasMany | belongsTo | hasOne | manyToMany",
          "target": "string — related model name",
          "foreign_key": "string — FK column name",
          "cascade": "string | null — DELETE | UPDATE behavior"
        }
      ],
      "indexes": [
        {
          "fields": ["string — indexed column names"],
          "unique": "boolean"
        }
      ],
      "timestamps": "boolean — has created_at/updated_at",
      "soft_delete": "boolean — has deleted_at"
    }
  ]
}
```

---

## 5. scenario-candidates.jsonl

Functional test scenario candidates tagged with `source: "codebase"`.

**Written in feature-grouped batches** (default `batch_size: 25`). Candidates
are accumulated in memory per-feature, then flushed as a multi-line append.
This reduces I/O from one write per candidate to one write per batch. See
[batch-progress.json](#6-batch-progressjson) for processing stats.

### Schema

Each line is a JSON object matching the shared scenario candidate format:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `candidate_id` | string | Yes | Unique ID: `CODE-{SEQ}` |
| `feature` | string | Yes | Feature/module name |
| `action` | string | Yes | User or system action |
| `description` | string | Yes | Detailed description |
| `source` | string | Yes | Always `"codebase"` |
| `source_evidence` | string | Yes | File path + line number reference |
| `confidence` | number | Yes | 0.0-1.0 detection confidence |
| `discovered_fields` | string[] | Yes | Field names found for this feature |
| `discovered_validations` | object[] | No | Validation rules per field |
| `discovered_endpoints` | object[] | No | Related API endpoints |
| `video_timestamp` | string | No | Always empty for codebase source |
| `screenshot_ref` | string | No | Always empty for codebase source |
| `component_path` | string | No | Frontend component file path |

### Example

```jsonl
{"candidate_id":"CODE-001","feature":"Vehicle Management","action":"Create new vehicle","description":"POST /api/vehicles with valid vehicle data. Handler in createVehicle, auth required (admin, fleet-manager). Validates name (required, max:100), type (enum), plate_number (required, unique, regex).","source":"codebase","source_evidence":"src/routes/vehicles.ts:42","confidence":0.9,"discovered_fields":["name","type","plate_number","registration_date","status"],"discovered_validations":[{"field":"name","rule":"required, max:100"},{"field":"plate_number","rule":"required, unique, regex:^[A-Z]{2}[0-9]{4}$"}],"discovered_endpoints":[{"endpoint":"/api/vehicles","method":"POST","status_codes":[201,400,401,409]}],"video_timestamp":"","screenshot_ref":"","component_path":"src/pages/vehicles/CreateVehicle.tsx"}
{"candidate_id":"CODE-002","feature":"Vehicle Management","action":"List all vehicles","description":"GET /api/vehicles with pagination (page, limit). Auth required. Returns paginated vehicle list.","source":"codebase","source_evidence":"src/routes/vehicles.ts:15","confidence":0.9,"discovered_fields":["page","limit","sortBy","filterStatus"],"discovered_validations":[],"discovered_endpoints":[{"endpoint":"/api/vehicles","method":"GET","status_codes":[200,401]}],"video_timestamp":"","screenshot_ref":"","component_path":"src/pages/vehicles/VehicleList.tsx"}
{"candidate_id":"CODE-003","feature":"Authentication","action":"User login","description":"POST /api/auth/login with email and password credentials. Returns JWT token on success.","source":"codebase","source_evidence":"src/routes/auth.ts:12","confidence":0.85,"discovered_fields":["email","password"],"discovered_validations":[{"field":"email","rule":"required, email"},{"field":"password","rule":"required, min:8"}],"discovered_endpoints":[{"endpoint":"/api/auth/login","method":"POST","status_codes":[200,400,401]}],"video_timestamp":"","screenshot_ref":"","component_path":"src/pages/auth/Login.tsx"}
```

> **Note**: In the example above, CODE-001 and CODE-002 belong to the same
> feature ("Vehicle Management") and would be flushed together in a single
> batch write. CODE-003 belongs to a different feature ("Authentication") and
> would be flushed in a separate batch.

---

## 6. batch-progress.json

Batch processing statistics written alongside `scenario-candidates.jsonl`.

### Schema

```json
{
  "total_candidates": "number — total candidates written across all batches",
  "total_batches": "number — total flush operations performed",
  "batch_size": "number — configured batch_size (default 25)",
  "features_processed": "number — distinct features processed",
  "duration_ms": "number — total Phase 5 duration in milliseconds",
  "batches": [
    {
      "batch": "number — 1-indexed batch sequence number",
      "feature": "string — feature/module name for this batch",
      "candidates": "number — candidates in this batch",
      "cumulative": "number — running total of candidates written so far"
    }
  ]
}
```

### Example

```json
{
  "total_candidates": 142,
  "total_batches": 8,
  "batch_size": 25,
  "features_processed": 6,
  "duration_ms": 4200,
  "batches": [
    {"batch": 1, "feature": "Vehicle Management", "candidates": 18, "cumulative": 18},
    {"batch": 2, "feature": "Authentication", "candidates": 12, "cumulative": 30},
    {"batch": 3, "feature": "Booking Management", "candidates": 25, "cumulative": 55},
    {"batch": 4, "feature": "Booking Management", "candidates": 9, "cumulative": 64},
    {"batch": 5, "feature": "User Management", "candidates": 22, "cumulative": 86},
    {"batch": 6, "feature": "Fleet Management", "candidates": 25, "cumulative": 111},
    {"batch": 7, "feature": "Fleet Management", "candidates": 6, "cumulative": 117},
    {"batch": 8, "feature": "Settings", "candidates": 25, "cumulative": 142}
  ]
}
```

### Batch Flush Rules

1. **Feature-complete flush**: When all candidate types for a feature are
   generated, flush the buffer regardless of size.
2. **Overflow split**: If a single feature generates more candidates than
   `batch_size`, split into multiple flushes at candidate-type boundaries
   (e.g., all CRUD candidates flush, then all validation candidates flush).
3. **Final flush**: Any remaining buffered candidates are flushed after the
   last feature is processed.
4. **Partial recovery**: On flush failure, retry once. On second failure,
   write to `scenario-candidates-partial.jsonl` and record the error in
   `batch-progress.json`.
