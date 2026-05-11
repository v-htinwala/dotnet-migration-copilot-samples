# Flow Identification Patterns

Heuristics for identifying logical user flows from raw web discovery data.

## Flow Detection Heuristics

### 1. Creation Flow (Form → Submit → Result)

**Pattern**: A page with a form that submits data and redirects to a result page.

**Detection signals**:
- Page A has a form with multiple input fields and a submit button
- Page A's form submit triggers a POST/PUT mutation endpoint
- After submission, navigation leads to Page B (list or detail page)
- The site map shows Page A linking to Page B

**Example**:
- `/orders/new` (form with fields) → POST `/api/orders` → redirect to `/orders`
- `/register` (registration form) → POST `/api/users` → redirect to `/login`

**Naming convention**: `{Entity} Creation Flow`

### 2. Data Management Flow (CRUD)

**Pattern**: A set of routes that together provide Create, Read, Update, Delete operations.

**Detection signals**:
- A list page (table/list elements) with GET endpoint for the collection
- A create page (form) with POST endpoint
- An edit page (form with pre-filled data) with PUT/PATCH endpoint
- Delete actions (buttons) with DELETE endpoint
- All endpoints share the same resource path base (e.g., `/api/orders/*`)

**Example**:
- `/orders` (list) + `/orders/new` (create) + `/orders/:id` (edit) + DELETE `/api/orders/:id`

**Naming convention**: `{Entity} Management Flow`

### 3. Authentication Flow

**Pattern**: Login form → auth API → authenticated redirect.

**Detection signals**:
- Page with password input field
- Form submit triggers an auth-classified API endpoint
- Successful auth redirects to a different page (dashboard, home)
- Protected routes redirect to the login page

**Example**:
- `/login` (email + password form) → POST `/api/auth/login` → redirect to `/dashboard`
- `/logout` → POST `/api/auth/logout` → redirect to `/login`

**Naming convention**: `Authentication Flow` or `Login/Logout Flow`

### 4. Data Browsing Flow (List + Filter + Sort + Paginate)

**Pattern**: A page with a data table and various controls for browsing data.

**Detection signals**:
- Page has table-like structure (multiple rows of similar elements)
- Sort controls (clickable column headers)
- Filter controls (text inputs, dropdowns near the table)
- Pagination controls (next/prev buttons, page numbers)
- GET API endpoint with query parameters (sort, filter, page)

**Example**:
- `/admin/users` with sort/filter/pagination → GET `/api/users?page=1&sort=name&order=asc`

**Naming convention**: `{Entity} Browsing Flow`

### 5. Search Flow

**Pattern**: Search input → results display → result interaction.

**Detection signals**:
- Search input (role: searchbox) or search form
- Search triggers GET API with query parameter
- Results area updates with matching items
- Results are clickable/navigable

**Example**:
- Search bar → GET `/api/search?q=term` → results list → click result → `/items/:id`

**Naming convention**: `Search & Results Flow`

### 6. Modal Interaction Flow

**Pattern**: Trigger button → modal opens → action in modal → modal closes.

**Detection signals**:
- Button that reveals a dialog element
- Dialog contains action buttons (confirm, cancel)
- Dialog may contain a form
- API call from within the dialog

**Example**:
- "Delete" button → confirmation modal → "Confirm Delete" → DELETE `/api/items/:id` → modal closes

**Naming convention**: `{Action} Confirmation Flow` or `{Entity} Modal Flow`

### 7. Multi-Step Wizard Flow

**Pattern**: Sequential pages/steps with next/back navigation.

**Detection signals**:
- Multiple pages with step indicators
- Next/Back/Previous buttons
- Progress indicators (step 1 of 3)
- Data accumulates across steps

**Example**:
- `/checkout/shipping` → `/checkout/payment` → `/checkout/review` → `/checkout/confirmation`

**Naming convention**: `{Process} Wizard Flow`

### 8. Settings/Configuration Flow

**Pattern**: Settings page with toggle switches and save actions.

**Detection signals**:
- Page with many toggle/checkbox/switch elements
- Save/Update button
- PUT/PATCH API calls on save
- Section-based layout (profile, notifications, security)

**Example**:
- `/settings/profile` (form fields) + `/settings/notifications` (toggles) → PUT `/api/user/settings`

**Naming convention**: `{Section} Settings Flow`

## Flow Chaining Rules

### Connecting Routes Into Flows

1. **Direct navigation**: Route A links to Route B via `navigation_graph`
2. **API dependency**: Route A and Route B both call the same API resource
3. **Form→result**: Route A has a form; Route B is the redirect target after submission
4. **Back-navigation**: Route B has a "Back" or breadcrumb link to Route A
5. **Shared context**: Routes under the same URL prefix (e.g., `/orders/*`)

### Handling Orphan Routes

Routes that don't fit into any flow are classified as:
- **Landing pages**: depth 0, many outbound links
- **Static pages**: no interactive elements, no API calls (e.g., About, Terms)
- **Utility pages**: standalone functionality (e.g., 404, loading states)

Report orphan routes separately in `flow-graph.json`.

## Confidence Scoring

Each identified flow has a confidence level:

| Confidence | Criteria |
|---|---|
| **High** | 3+ detection signals match; clear route chain in navigation graph |
| **Medium** | 2 detection signals match; partial route chain |
| **Low** | 1 detection signal matches; flow inferred from URL patterns only |

Include confidence in the flow output to help prioritize regression testing.
