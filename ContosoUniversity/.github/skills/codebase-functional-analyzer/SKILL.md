---
name: codebase-functional-analyzer
description: >
  Performs deep static analysis of application codebases to extract API
  endpoints, frontend routes, component hierarchies, database models, middleware
  chains, and authentication requirements. Uses a detected tech stack profile
  (from tech-stack-detector) to apply framework-specific parsing strategies for
  React, Next.js, Angular, Vue, Express, Django, Spring Boot, FastAPI, Laravel,
  Rails, ASP.NET, and more. Outputs structured catalogs (api-catalog.jsonl,
  route-map.json, component-tree.json, models.json) and functional test scenario
  candidates. Use when generating functional test cases from source code, mapping
  application architecture for test coverage, or extracting endpoint and
  validation metadata for test data generation.
license: MIT
compatibility: >
  Works with any skills-compatible coding agent with file system read access.
  No external dependencies required — analysis is purely static file reading
  and pattern matching. Requires tech-stack-detector output (stack-profile.json)
  as input for framework-specific parsing.
metadata:
  author: functional-test-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
---

# Codebase Functional Analyzer

## Purpose

Perform deep static analysis of an application codebase to extract everything
needed for comprehensive functional test case generation: API endpoints with
HTTP methods and middleware, frontend routes and navigation structure, component
hierarchies for SPA discovery, database models and relationships, validation
rules, and authentication/authorization requirements.

This skill uses the `stack-profile.json` from tech-stack-detector to select the
correct framework-specific parsing strategy. For catalogued frameworks, it
applies precise extraction patterns. For unknown frameworks, it falls back to
heuristic pattern matching.

## When to Use This Skill

- Extract API endpoint catalog from backend code
- Map frontend route structure for navigation testing
- Build component tree for SPA feature discovery
- Extract database model schemas for test data generation
- Identify validation rules for boundary test cases
- Detect auth/role requirements for access control testing
- Feed codebase-sourced scenario candidates into the merger

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `codebase_path` | Yes | — | Root directory of the application codebase |
| `tech_stack` | Yes | — | Path to `stack-profile.json` from tech-stack-detector |
| `output_dir` | Yes | — | Output directory for analysis artifacts |
| `batch_size` | No | `25` | Max scenario candidates per batch flush. Candidates are grouped by feature and flushed in batches to reduce I/O overhead. |

## Outputs

| File | Format | Description |
|---|---|---|
| `api-catalog.jsonl` | JSONL | One line per API endpoint with method, handler, middleware, auth |
| `route-map.json` | JSON | Frontend route tree with page types and component mappings |
| `component-tree.json` | JSON | Component hierarchy for SPAs (React, Angular, Vue) |
| `models.json` | JSON | Database models/entities with fields, types, and validations |
| `scenario-candidates.jsonl` | JSONL | Functional test scenario candidates tagged `source: "codebase"` (written in batches) |
| `batch-progress.json` | JSON | Batch processing stats: batch count, per-feature breakdown, timing |

---

## 5-Phase Workflow

### Phase 1: API Endpoint Extraction

**Goal**: Build a complete catalog of API endpoints by applying framework-
specific parsing patterns from the detected tech stack.

**Per-endpoint extraction target**:

```json
{
  "endpoint": "/api/vehicles",
  "method": "POST",
  "handler": "createVehicle",
  "handler_file": "src/routes/vehicles.ts",
  "handler_line": 42,
  "middleware": ["auth", "validate", "rateLimiter"],
  "auth_required": true,
  "auth_roles": ["admin", "fleet-manager"],
  "request_body_fields": [
    {"name": "name", "type": "string", "required": true, "validation": "max:100"},
    {"name": "type", "type": "enum", "required": true, "values": ["Heavy", "Light", "Medium"]},
    {"name": "plate_number", "type": "string", "required": true, "validation": "regex:^[A-Z]{2}[0-9]{4}$"}
  ],
  "response_codes": [201, 400, 401, 403, 409],
  "query_params": [],
  "path_params": [],
  "related_model": "Vehicle"
}
```

**Framework-specific parsing** (see [references/framework-parsers.md](references/framework-parsers.md)):

| Framework | Route Pattern to Search |
|---|---|
| Express | `app.get()`, `app.post()`, `router.get()`, `router.use()` |
| Next.js | `pages/api/*.ts` files, `app/*/route.ts` files, exported functions |
| Django | `urlpatterns` in `urls.py`, `ViewSet` and `APIView` classes |
| Spring Boot | `@RequestMapping`, `@GetMapping`, `@PostMapping` annotations |
| FastAPI | `@app.get()`, `@router.post()`, Pydantic models in signatures |
| Laravel | `Route::get()` in `routes/web.php` and `routes/api.php` |
| Rails | `resources`, `get`, `post` in `config/routes.rb` |
| ASP.NET | `[HttpGet]`, `[HttpPost]`, `[Route]` attributes |

**Middleware chain extraction**: For each endpoint, trace the middleware chain:
1. Global middleware (app-level `app.use()` or framework equivalent)
2. Router-level middleware
3. Route-specific middleware
4. Tag `auth_required: true` when auth middleware is in the chain

### Phase 2: Frontend Route Discovery

**Goal**: Map all frontend routes/pages and their navigation structure.

**Output structure** (`route-map.json`):

```json
{
  "routes": [
    {
      "path": "/dashboard",
      "component": "DashboardPage",
      "component_file": "src/pages/Dashboard.tsx",
      "layout": "MainLayout",
      "auth_required": true,
      "children": [],
      "params": [],
      "meta": {"title": "Dashboard"}
    },
    {
      "path": "/vehicles",
      "component": "VehicleList",
      "component_file": "src/pages/vehicles/index.tsx",
      "auth_required": true,
      "children": [
        {"path": "/vehicles/new", "component": "CreateVehicle"},
        {"path": "/vehicles/:id", "component": "VehicleDetail"},
        {"path": "/vehicles/:id/edit", "component": "EditVehicle"}
      ]
    }
  ],
  "navigation_menus": [
    {
      "location": "sidebar",
      "items": ["Dashboard", "Vehicles", "Bookings", "Users", "Settings"]
    }
  ]
}
```

**Framework-specific route discovery**:
| Framework | Strategy |
|---|---|
| React (React Router) | Search for `<Route>`, `createBrowserRouter`, route config arrays |
| Next.js (Pages) | File-based: enumerate `pages/` directory structure |
| Next.js (App Router) | File-based: enumerate `app/` with `page.tsx` files |
| Angular | `RouterModule.forRoot()`, lazy-loaded modules |
| Vue Router | Route config arrays, file-based in Nuxt |
| SvelteKit | File-based: `src/routes/` with `+page.svelte` |

### Phase 3: Component Tree Building

**Goal**: Build the component hierarchy for SPAs to enable DOM-state correlation
with URL-based discovery.

**Output structure** (`component-tree.json`):

```json
{
  "root": "App",
  "components": [
    {
      "name": "VehicleList",
      "file": "src/components/vehicles/VehicleList.tsx",
      "type": "page",
      "children": ["VehicleTable", "VehicleFilters", "CreateVehicleButton"],
      "props": ["vehicles", "onFilter", "onSort"],
      "state": ["selectedVehicle", "filterCriteria"],
      "api_calls": ["/api/vehicles GET"]
    },
    {
      "name": "VehicleForm",
      "file": "src/components/vehicles/VehicleForm.tsx",
      "type": "form",
      "children": ["FormField", "TypeSelector", "SubmitButton"],
      "props": ["vehicle", "onSubmit", "mode"],
      "state": ["formData", "errors", "isSubmitting"],
      "api_calls": ["/api/vehicles POST", "/api/vehicles/:id PUT"],
      "form_fields": ["name", "type", "plate_number", "registration_date"]
    }
  ]
}
```

**Extraction rules**:
1. Scan all component files (`.tsx`, `.jsx`, `.vue`, `.svelte`, `.component.ts`)
2. Track import relationships to build parent-child tree
3. Identify form components (components with `<form>`, `<input>`, `useState` for form state)
4. Track API calls within components (`fetch`, `axios`, `useSWR`, `useQuery`)
5. Label component types: `page`, `form`, `list`, `detail`, `modal`, `layout`, `widget`

### Phase 4: Database Model Extraction

**Goal**: Extract database model definitions to understand data structure, field
types, and validation constraints.

**Output structure** (`models.json`):

```json
{
  "models": [
    {
      "name": "Vehicle",
      "file": "src/models/Vehicle.ts",
      "table_name": "vehicles",
      "fields": [
        {"name": "id", "type": "uuid", "primary_key": true, "auto_generated": true},
        {"name": "name", "type": "string", "max_length": 100, "required": true, "unique": false},
        {"name": "type", "type": "enum", "values": ["Heavy Duty", "Light", "Medium"], "required": true},
        {"name": "plate_number", "type": "string", "max_length": 20, "required": true, "unique": true,
         "validation_regex": "^[A-Z]{2}[0-9]{4}$"},
        {"name": "status", "type": "enum", "values": ["Active", "Inactive", "Maintenance"], "default": "Active"},
        {"name": "created_at", "type": "datetime", "auto_generated": true},
        {"name": "updated_at", "type": "datetime", "auto_generated": true}
      ],
      "relationships": [
        {"type": "hasMany", "target": "Booking", "foreign_key": "vehicle_id"},
        {"type": "belongsTo", "target": "Fleet", "foreign_key": "fleet_id"}
      ],
      "indexes": [
        {"fields": ["plate_number"], "unique": true},
        {"fields": ["status", "type"], "unique": false}
      ]
    }
  ]
}
```

**ORM-specific extraction** (see [references/framework-parsers.md](references/framework-parsers.md)):
| ORM | Strategy |
|---|---|
| Prisma | Parse `prisma/schema.prisma` — models, fields, `@unique`, `@relation` |
| TypeORM | Parse `@Entity()` decorated classes — `@Column()`, `@ManyToOne()` |
| Sequelize | Parse `Model.init()` or `sequelize.define()` calls |
| Django ORM | Parse `models.Model` subclasses — `CharField`, `ForeignKey` |
| SQLAlchemy | Parse `db.Model` subclasses — `Column()`, `relationship()` |
| Spring Data JPA | Parse `@Entity` classes — `@Column`, `@OneToMany` |
| ActiveRecord | Parse `create_table` migrations + model validations |
| Eloquent | Parse `$fillable`, `$casts`, migrations |
| Entity Framework | Parse `DbContext` — `DbSet<>`, model configurations |

### Phase 5: Scenario Candidate Generation (Batched)

**Goal**: Generate functional test scenario candidates from all extracted data,
using **feature-based batching** for efficient I/O.

#### Batching Strategy

Candidates are generated and written in batches grouped by feature/module rather
than one-by-one. This significantly reduces I/O overhead for large codebases.

```
┌──────────────────────────────────────────────────────┐
│  Phase 5: Batched Scenario Generation                │
│                                                      │
│  1. Identify features from Phases 1-4 outputs        │
│  2. For each feature:                                │
│     ├─ Collect related endpoints, models, routes     │
│     ├─ Generate ALL candidate types for the feature  │
│     ├─ Accumulate into in-memory batch buffer        │
│     └─ Flush batch when feature completes or buffer  │
│        reaches batch_size (default: 25)              │
│  3. Flush remaining buffer                           │
│  4. Write batch-progress.json                        │
└──────────────────────────────────────────────────────┘
```

**Step 5a — Feature Identification**: Group all Phase 1-4 artifacts by
feature/module. A feature is derived from:
- Route path prefix (e.g., `/api/vehicles` → "Vehicle Management")
- Model name (e.g., `Vehicle` model → "Vehicle Management")
- Component directory (e.g., `src/pages/vehicles/` → "Vehicle Management")
- Controller/handler grouping (e.g., `VehicleController` → "Vehicle Management")

**Step 5b — Batch Generation**: For each feature, generate ALL candidate types
in a single pass, accumulating them into a batch buffer:

| Source | Candidate Type | Example |
|---|---|---|
| Each CRUD endpoint | Positive + Negative | Create, Read, Update, Delete vehicle |
| Each field validation | Boundary + Validation | Name max 100 chars, plate regex pattern |
| Each auth-protected route | Security | Access without token, wrong role |
| Each model relationship | Integration | Create booking for non-existent vehicle |
| Each enum field | Validation | Each valid value + invalid value |
| Each unique constraint | Negative | Duplicate plate_number creation |
| Each required field | Negative | Omit required field |

**Step 5c — Batch Flush**: When a feature completes or the buffer reaches
`batch_size` (default: 25), flush the accumulated candidates to
`scenario-candidates.jsonl` in a single append-write and log progress:

```
Batch 1/8: Vehicle Management — 18 candidates flushed (18 total)
Batch 2/8: Authentication — 12 candidates flushed (30 total)
Batch 3/8: Booking Management — 25 candidates flushed (55 total)
Batch 4/8: Booking Management — 9 candidates flushed (64 total)  ← overflow split
...
```

If a single feature generates more candidates than `batch_size`, it is split
into multiple flush operations (feature-overflow splitting). The split respects
candidate type boundaries — it will not break a group of validation candidates
for the same endpoint across two flushes.

**Step 5d — Batch Progress**: Write `batch-progress.json` alongside the output:

```json
{
  "total_candidates": 142,
  "total_batches": 8,
  "batch_size": 25,
  "features_processed": 6,
  "batches": [
    {"batch": 1, "feature": "Vehicle Management", "candidates": 18, "cumulative": 18},
    {"batch": 2, "feature": "Authentication", "candidates": 12, "cumulative": 30},
    {"batch": 3, "feature": "Booking Management", "candidates": 25, "cumulative": 55},
    {"batch": 4, "feature": "Booking Management", "candidates": 9, "cumulative": 64}
  ],
  "duration_ms": 4200
}
```

#### Per-Candidate Schema

Each candidate in the batch follows this structure:

```json
{
  "candidate_id": "CODE-001",
  "feature": "Vehicle Management",
  "action": "Create new vehicle",
  "description": "POST /api/vehicles with valid vehicle data",
  "source": "codebase",
  "source_evidence": "src/routes/vehicles.ts:42, createVehicle handler",
  "confidence": 0.9,
  "discovered_fields": ["name", "type", "plate_number", "registration_date", "status"],
  "discovered_validations": [
    {"field": "name", "rule": "required, max:100"},
    {"field": "plate_number", "rule": "required, unique, regex:^[A-Z]{2}[0-9]{4}$"}
  ],
  "discovered_endpoints": [
    {"endpoint": "/api/vehicles", "method": "POST", "status_codes": [201, 400, 401, 409]}
  ],
  "video_timestamp": "",
  "screenshot_ref": "",
  "component_path": "src/pages/vehicles/CreateVehicle.tsx"
}
```

---

## Constraints

1. **Read-only**: Never modify the codebase. Only read and analyze files.
2. **File limit**: Process at most 500 source files total. Prioritize route
   files, controllers, models, and validation schemas over utility files.
3. **Framework-first**: Always check `stack-profile.json` before starting.
   If the framework is in the catalog, use the specific parser. Only fall
   back to heuristics for uncatalogued frameworks.
4. **Incremental output**: Write `api-catalog.jsonl` incrementally (one line
   per endpoint as it's discovered) for resume capability.
5. **Batched scenario output**: Write `scenario-candidates.jsonl` in
   feature-grouped batches (default `batch_size: 25`). Never write one
   candidate at a time — accumulate into a buffer and flush per-feature or
   when the buffer reaches `batch_size`. Always write `batch-progress.json`
   alongside.
6. **No execution**: Never run project code, tests, or build scripts.
7. **Scope boundaries**: Analyze only application code. Skip `node_modules/`,
   `vendor/`, `__pycache__/`, build output directories, and test fixtures.

## Error Handling

| Error | Behavior |
|---|---|
| Codebase path not found | Fail with clear error message |
| tech_stack file missing | Fail — tech-stack-detector must run first |
| Unknown framework | Use heuristic analysis, set confidence ≤ 0.5 |
| No routes found | Warn, continue with model and component analysis |
| No models found | Warn, continue with route and component analysis |
| Circular component imports | Break cycles at 5 levels deep, log warning |
| Very large codebase (>500 files) | Prioritize files in routes/, controllers/, models/ directories |
| Batch flush failure | Retry once; on second failure, write remaining buffer to `scenario-candidates-partial.jsonl` and log error in `batch-progress.json` |
| Feature grouping ambiguous | Fall back to file-path-based grouping (controller/route directory name) |

## Related Skills

| Skill | Relationship |
|---|---|
| **tech-stack-detector** | Upstream — provides stack-profile.json |
| **functional-scenario-merger** | Downstream — consumes scenario-candidates.jsonl |
| **url-functional-explorer** | Parallel — component-tree.json helps correlate DOM states with components |
| **functional-test-orchestrator** | Orchestrator — invokes this skill as Phase 2 step 2 |
