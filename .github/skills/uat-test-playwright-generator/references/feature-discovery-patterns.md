# Feature Discovery Patterns (Live Web App)

Patterns for identifying **user-facing features** by exploring a running web application using Playwright CLI.

> **Remember**: You are a Senior UAT Tester. Explore EVERY corner of the app like a real user would.

---

## What is a Feature?

A **feature** is a functional capability that users interact with. Features answer the question: "What can users DO in this application?"

| Feature Type | What Users Do | How to Discover via Playwright |
|--------------|---------------|-------------------------------|
| Login/Authentication | Sign in, sign out, reset password | Check landing page for login form |
| Dashboard/Home | View summary, access quick actions | Navigate after login, snapshot main page |
| List/Browse | View, search, filter, sort data | Look for data grids, tables, card layouts |
| Form/Create | Enter data, create new records | Click "Add New" / "Create" buttons |
| Edit/Update | Modify existing records | Click "Edit" icons/buttons on records |
| Detail View | View complete information | Click on a record/row in a list |
| Workflow/Process | Multi-step business processes | Look for stepper components, status flows |
| Reports | View or export data summaries | Check for report/export menu items |
| Settings | Configure preferences | Look for settings/preferences in user menu |
| File Management | Upload, download, manage files | Look for upload buttons, attachment sections |
| Notifications | View alerts and messages | Check notification bell/icon in header |

---

## Feature Discovery Process (Playwright-Driven)

### Step 1: Explore the Landing Page

```bash
playwright-cli open <APP_URL> --headed
playwright-cli snapshot --filename=snapshots/00-landing.yaml
playwright-cli screenshot --filename=screenshots/00-landing.png
```

**What to identify:**
- Is this a login page? A public homepage? A dashboard?
- What navigation elements are visible?
- Are there any call-to-action buttons?

### Step 2: Authenticate (if required)

```bash
# If login page detected
playwright-cli fill <email-ref> "test@example.com"
playwright-cli fill <password-ref> "password"
playwright-cli click <login-button-ref>
playwright-cli snapshot --filename=snapshots/01-after-login.yaml
playwright-cli screenshot --filename=screenshots/01-after-login.png
```

### Step 3: Map ALL Navigation

**This is the most critical step.** Click EVERY navigation item to discover all pages.

```bash
# Snapshot to see all nav elements
playwright-cli snapshot --filename=snapshots/02-navigation.yaml

# For EACH menu item:
playwright-cli click <menu-item-ref>
playwright-cli snapshot --filename=snapshots/nav-<page-name>.yaml
playwright-cli screenshot --filename=screenshots/nav-<page-name>.png
```

**Navigation elements to explore:**
- Main menu / sidebar items
- Sub-menus (hover or click to expand)
- Header links (profile, settings, help)
- Footer links
- Breadcrumb navigation
- Tab navigation within pages
- Dropdown menus

### Step 4: Analyze Each Page

For each discovered page, take a snapshot and identify:

| Element Type | What to Look For | Playwright Discovery |
|-------------|------------------|---------------------|
| **Input fields** | Text boxes, text areas | `<input>`, `<textarea>` in snapshot |
| **Dropdowns** | Select menus, combo boxes | `<select>`, custom dropdown components |
| **Buttons** | Action triggers | `<button>`, `<a>` with action labels |
| **Tables/Grids** | Data display | `<table>`, grid components |
| **Search bars** | Text search inputs | Input with search icon/placeholder |
| **Filters** | Filter panels, chips | Filter controls, faceted search |
| **Pagination** | Page navigation | Next/Prev buttons, page numbers |
| **Modals** | Hidden dialogs | Click action buttons to reveal |
| **Tabs** | Content sections | Tab headers, click to switch |
| **File inputs** | Upload areas | `<input type="file">`, drag-drop zones |
| **Checkboxes** | Toggle options | `<input type="checkbox">` |
| **Radio buttons** | Single selection | `<input type="radio">` |
| **Date pickers** | Date selection | Date input fields, calendar widgets |
| **Rich text editors** | Content editing | WYSIWYG editor areas |

### Step 5: Discover Hidden Features

A Senior UAT Tester doesn't stop at what's visible. Explore:

```bash
# Click action buttons to find modals/dialogs
playwright-cli click <add-button-ref>
playwright-cli snapshot --filename=snapshots/modal-create.yaml

# Expand accordions/collapsible sections
playwright-cli click <accordion-header-ref>
playwright-cli snapshot --filename=snapshots/expanded-section.yaml

# Check right-click context menus (if applicable)
# Check hover states for tooltips
# Look for hidden menu items that appear on scroll
```

---

## Feature Types and Test Focus

### Authentication Features

**How to Discover:**
- Landing page has login form
- Look for "Forgot Password", "Register", "Sign Up" links
- Check for SSO/social login buttons

**Test Focus:**
- Valid login succeeds → dashboard loads
- Invalid login shows error message
- Empty fields show validation
- Password reset workflow
- Session timeout behavior
- Logout clears session

**Estimated Tests:** 10-15

### Dashboard Features

**How to Discover:**
- First page after login
- Contains summary cards, charts, quick actions
- May have widgets or configurable sections

**Test Focus:**
- Dashboard loads with correct data
- Summary numbers are visible
- Quick action buttons work
- Charts/graphs render
- Refresh updates data
- **Cross-validate summary card counts/totals against actual list page data** (e.g., "Total Assets: 25" must match the count on the Assets list page)

**Estimated Tests:** 8-12

### List/Search Features

**How to Discover:**
- Pages with data tables or card grids
- Search input fields
- Filter panels or dropdowns
- Sort indicators on column headers
- Pagination controls

**Test Focus:**
- List loads with data
- Search returns correct results
- Filters narrow results — **test EACH filter option individually** (e.g., filter by Category A, then Category B, then Category C)
- Sorting works correctly
- Pagination navigates properly
- Empty state handled ("No results")
- Clicking a record opens details

**Estimated Tests:** 15-20

### Form Features (Create/Edit)

**How to Discover:**
- "Add New" / "Create" buttons on list pages
- "Edit" icons/buttons on records
- Pages with multiple input fields and a Save/Submit button

**Test Focus:**
- Required field validation
- Format validation (email, phone, date)
- Dropdown options load correctly
- Cascading dropdowns work
- Date pickers function
- Save succeeds with valid data
- Cancel discards changes
- Special characters handled
- **Test EACH option in every dropdown/radio group individually** (e.g., if a Category dropdown has Hardware, Software, Mobile, Peripheral — create a test case for each)
- **Verify default values** on checkboxes, date fields, and numeric inputs when the form first opens
- **Boundary values on numeric fields** (min/max for ratings, quantities, percentages)
- **Deep modal exploration**: If the form opens in a modal with sub-elements (line items, tax/shipping, calculated totals), snapshot inside the modal and test each sub-element

**Estimated Tests:** 15-25 (depending on form complexity)

### Detail View Features

**How to Discover:**
- Click on a record in a list
- Pages showing complete information for one item
- May have Edit/Delete buttons, related items tabs

**Test Focus:**
- All fields display correctly
- Edit opens edit form
- Delete shows confirmation
- Related items load
- Back navigation works
- **Empty/unassigned state**: Test what the detail view shows when optional fields are empty or related data is unassigned (e.g., "Assigned Employee: None")
- **Cancel on delete confirmation**: Test both confirming AND cancelling the delete dialog

**Estimated Tests:** 10-15

### Workflow Features

**How to Discover:**
- Stepper/wizard components
- Status indicators (badges, progress bars)
- Approve/Reject buttons
- Multi-page forms

**Test Focus:**
- Process starts correctly
- Steps complete in order
- Cannot skip required steps
- Status updates visible
- Approval/rejection works
- **Walk each branching option**: If a wizard step has selectable categories or paths, walk through with EACH option — not just one

**Estimated Tests:** 15-25

### File Management Features

**How to Discover:**
- Upload buttons or drag-drop zones
- Attachment sections on detail pages
- Download links/buttons

**Test Focus:**
- Valid files upload successfully
- Invalid file types rejected
- Download works
- Delete with confirmation
- File size limits enforced

**Estimated Tests:** 8-12

---

## Building the Feature Map

Create a feature map with this structure:

```
FEATURE_MAP = [
  {
    "id": 1,
    "name": "Authentication",
    "type": "Login",
    "description": "User login, logout, and session management",
    "url": "/login",
    "discovered_elements": ["email input", "password input", "sign-in button", "forgot password link"],
    "estimated_tests": 12,
    "status": "not started"
  },
  {
    "id": 2,
    "name": "Customer Dashboard",
    "type": "Dashboard",
    "description": "View customer summary and quick actions",
    "url": "/dashboard",
    "discovered_elements": ["summary cards", "recent activity table", "quick action buttons"],
    "estimated_tests": 10,
    "status": "not started"
  }
]
```

### Feature Map Fields

| Field | Description | Example |
|-------|-------------|---------|
| `id` | Unique identifier | 1, 2, 3... |
| `name` | Business name of feature | "Customer Management" |
| `type` | Feature type category | CRUD, Login, Dashboard, etc. |
| `description` | What users can do | "Create, view, edit customers" |
| `url` | Route/URL where feature lives | "/customers" |
| `discovered_elements` | Interactive elements found via snapshot | ["search input", "add button", "data grid"] |
| `estimated_tests` | Expected number of test cases | 35 |
| `status` | Processing status | "not started", "in progress", "completed" |

---

## Test Count Estimation

| Feature Type | Test Range | Notes |
|--------------|------------|-------|
| Login/Authentication | 10-15 | Login, logout, errors, timeout |
| Dashboard | 8-12 | Load, navigation, data display |
| Simple Form (<10 fields) | 10-15 | Fields + validation |
| Complex Form (10+ fields) | 20-30 | Fields + validation + workflows |
| List/Search | 15-20 | Load, search, filter, sort, page |
| Detail View | 10-15 | View, edit, delete, related |
| Workflow/Process | 15-25 | Steps, approvals, status |
| File Management | 8-12 | Upload, download, delete |
| Settings | 5-10 | Preferences, save |

---

## Sample Feature Discovery Output

```
═══════════════════════════════════════════════════════════════
APPLICATION: Customer Portal (https://portal.example.com)
EXPLORED BY: Senior UAT Tester (AI Agent)
═══════════════════════════════════════════════════════════════

FEATURES DISCOVERED VIA LIVE EXPLORATION:

┌────┬─────────────────────┬────────────┬──────────────┬─────────────┐
│ ID │ Feature Name        │ Type       │ URL/Route    │ Est. Tests  │
├────┼─────────────────────┼────────────┼──────────────┼─────────────┤
│ 1  │ Authentication      │ Login      │ /login       │ 12          │
│ 2  │ Customer Dashboard  │ Dashboard  │ /dashboard   │ 10          │
│ 3  │ Customer List       │ Search     │ /customers   │ 18          │
│ 4  │ Customer Details    │ Detail     │ /customers/:id│ 12         │
│ 5  │ Create Customer     │ Form       │ /customers/new│ 22         │
│ 6  │ Edit Customer       │ Form       │ /customers/:id/edit│ 20    │
│ 7  │ Attachments         │ File       │ (within detail)│ 10        │
└────┴─────────────────────┴────────────┴──────────────┴─────────────┘

TOTAL ESTIMATED TEST CASES: 104
═══════════════════════════════════════════════════════════════
```

---

## Checklist for Feature Discovery

- [ ] Opened the application URL and captured landing page
- [ ] Authenticated (if required)
- [ ] Clicked EVERY navigation menu item
- [ ] Expanded ALL sub-menus and dropdowns
- [ ] Checked header links (profile, settings, notifications)
- [ ] Checked footer links
- [ ] Identified all major screens/pages
- [ ] Clicked action buttons to discover modals/dialogs
- [ ] Expanded accordions and switched tabs
- [ ] Grouped related screens into features
- [ ] Described what users can DO in each feature
- [ ] Categorized each feature by type
- [ ] Estimated test count per feature
- [ ] Created FEATURE_MAP for processing
