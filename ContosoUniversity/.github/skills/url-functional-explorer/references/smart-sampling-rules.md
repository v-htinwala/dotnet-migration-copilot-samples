# Smart Sampling Rules — url-functional-explorer

Rules for efficiently exploring dynamic content without exhaustive crawling.

---

## Paginated Lists

**Detection**: Elements matching `.pagination`, `[role="navigation"]` with
page numbers, "Next"/"Previous" buttons, or URL parameters like `?page=`.

**Sampling strategy**:
1. **Page 1**: Always capture (default view)
2. **One middle page**: If total pages > 5, navigate to approximately page N/2
3. **Last page**: Navigate to last page to verify boundary behavior

**What to record**:
- Column headers and types
- Row count per page
- Pagination controls (first/prev/next/last)
- Sort indicators
- Filter options visible
- Action buttons per row (Edit, Delete, View)

**Budget**: 3 page loads maximum per paginated list.

---

## Tabs

**Detection**: `[role="tablist"]`, `[role="tab"]`, `.nav-tabs`, `.tab-bar`,
elements with `aria-selected` attribute.

**Sampling strategy**: Click ALL tabs — each may reveal different content.

**What to record per tab**:
- Tab label text
- Content type (form, list, text, chart)
- Fields or elements unique to that tab
- Whether tab loads content dynamically (lazy loading)

**Budget**: 1 click per tab + snapshot.

---

## Accordions

**Detection**: `[role="button"][aria-expanded]`, `.accordion`, `.collapsible`,
elements with chevron/arrow icons that toggle content.

**Sampling strategy**: Expand ALL accordion sections.

**What to record**:
- Section header text
- Content type when expanded
- Number of sections
- Default expanded/collapsed state

**Budget**: 1 click per section.

---

## Infinite Scroll

**Detection**: Content loads when scrolling to bottom. Indicators:
- Scroll event triggers new content
- "Loading..." spinner at bottom
- No pagination controls visible
- List grows on scroll

**Sampling strategy**: Scroll twice (2 loads).

**What to record**:
- Items per load batch
- Whether load trigger is scroll-based or button-based ("Load More")
- Total items indicator if visible ("Showing 20 of 150")

**Budget**: 2 scroll triggers maximum.

---

## Modals / Dialogs

**Detection**: Elements with `role="dialog"`, `.modal`, `[aria-modal="true"]`,
overlay elements that appear on top of page content.

**Sampling strategy**: Click ALL discoverable modal triggers.

**Trigger discovery**:
1. Buttons with text: "Add", "Create", "New", "Edit", "Delete", "Confirm"
2. Links that don't navigate (no `href` or `href="#"`)
3. Elements with `data-toggle="modal"` or similar attributes
4. Action icons (pencil, trash, plus) in tables or cards

**What to record per modal**:
- Trigger element (what was clicked)
- Modal title/heading
- Modal content type (form, confirmation, info)
- Form fields (if present)
- Action buttons (Submit, Cancel, Confirm, Delete)
- Close mechanism (X button, backdrop click, Escape key)

**Modal close**: After recording, close the modal before proceeding:
1. Click "Cancel" or "Close" button
2. If no close button, press Escape
3. If still open, click backdrop
4. If still stuck, navigate away

**Budget**: 1 open + 1 close per modal trigger.

---

## Dropdowns / Select Menus

**Detection**: `<select>` elements, custom dropdowns with `[role="listbox"]`,
typeahead/autocomplete inputs.

**Sampling strategy**:
- **Native `<select>`**: Read all `<option>` values from DOM (no clicks needed)
- **Custom dropdowns**: Click to open, read all visible options, close
- **Autocomplete**: Record placeholder text and any default suggestions

**What to record**:
- All option values and labels
- Default selected value
- Whether multi-select is supported
- Searchable/filterable indicator

**Budget**: 1 click to open + 1 click to close per custom dropdown.

---

## Date Pickers

**Detection**: `input[type="date"]`, custom date picker widgets,
calendar icon triggers.

**Sampling strategy**: Open the picker, observe constraints.

**What to record**:
- Date format hint (placeholder)
- Min date constraint (if visible)
- Max date constraint (if visible)
- Whether it's a single date or date range picker
- Time component included?

**Budget**: 1 interaction per date picker.

---

## Search & Filter Controls

**Detection**: `input[type="search"]`, search icon with input, filter panels,
sidebar facets.

**Sampling strategy**: DO NOT execute searches. Only observe controls.

**What to record**:
- Search field placeholder text
- Filter categories (dropdown labels, checkbox groups)
- Filter options per category
- Active/applied filters
- Clear/reset button availability

**Budget**: Read-only observation, no actions.

---

## Data Tables

**Detection**: `<table>`, `[role="grid"]`, `.data-table`, `.ag-grid`.

**Sampling strategy**: Observe structure without modifying.

**What to record**:
- Column headers (name, type hint)
- Sortable columns (indicated by sort icons)
- Row count visible
- Row action buttons (Edit, Delete, View, etc.)
- Bulk selection checkboxes
- Column filters
- Export/download buttons
- Row click behavior (does clicking a row navigate somewhere?)

**Budget**: 1 snapshot per table. Click 1 sortable column if in shadow mode.

---

## Budget Summary

| Content Type | Max Actions | Expected Time |
|---|---|---|
| Paginated list | 3 pages | ~5s |
| Tab set | N tabs (typically 3-6) | ~3s per tab |
| Accordion | N sections (typically 3-8) | ~1s per section |
| Infinite scroll | 2 scrolls | ~4s |
| Modal | 2 actions per modal (open + close) | ~3s per modal |
| Dropdown | 2 actions (open + close) | ~1s |
| Date picker | 1 interaction | ~2s |
| Search/filter | 0 actions (read-only) | ~1s |
| Data table | 0-1 actions | ~2s |

**Total budget per page**: Approximately 15-30 seconds for full interaction
inventory depending on page complexity.
