# Scenario Templates by Regression Category

Reference templates for generating expected behaviors per regression category.
Each template maps the category (from `playwright-cli-regression-analyzer`)
to the standard behavior patterns used in `regression-scenarios.yml`.

---

## 1. Navigation Regression

**Trigger**: Route count ≥ 2 in flow, navigation links detected.

```yaml
expected_behaviors:
  - "Clicking '{link_text}' navigates to {target_route}"
  - "Browser back button returns to {previous_route}"
  - "Breadcrumb at {route} shows correct hierarchy: {crumb_chain}"
  - "Direct URL entry to {route} renders correct page"
  - "Active navigation item highlights for {route}"
```

**Variables**:
- `link_text` — text content of `<a>` or role=link element
- `target_route` — href or SPA route target
- `previous_route` — the preceding route in the flow
- `crumb_chain` — e.g. "Home > Orders > Detail"

---

## 2. User Interaction Regression

**Trigger**: Interactive element count > 5, or buttons/toggles detected.

```yaml
expected_behaviors:
  - "Button '{button_name}' at {route} performs {action}"
  - "Toggle '{toggle_name}' changes state from {state_a} to {state_b}"
  - "Dropdown '{dropdown_name}' opens on click and shows {option_count} options"
  - "Tab '{tab_name}' switches visible content panel"
  - "Accordion '{section_name}' expands/collapses on click"
```

**Variables**:
- `button_name` — accessible name from snapshot
- `action` — inferred from context (submit, delete, navigate, toggle)
- `state_a`/`state_b` — e.g. "unchecked"/"checked"

---

## 3. Form Handling Regression

**Trigger**: Form elements (textbox, combobox, checkbox) detected on route.

```yaml
expected_behaviors:
  - "Form at {route} renders with fields: {field_list}"
  - "Required field '{field_name}' shows validation error when empty"
  - "Email field '{field_name}' rejects invalid format"
  - "Password field '{field_name}' enforces minimum requirements"
  - "Form submission calls {api_method} {api_endpoint}"
  - "Successful submission shows {success_indicator}"
  - "Validation errors display inline next to invalid fields"
  - "Form preserves input on failed submission"
```

**Variables**:
- `field_list` — comma-separated names from interaction inventory
- `field_name` — individual field label/name
- `api_method` / `api_endpoint` — from correlated API surface
- `success_indicator` — "success message" or "redirects to {route}"

---

## 4. API Integration Regression

**Trigger**: API endpoints associated with route in api-surface.json.

```yaml
expected_behaviors:
  - "Page at {route} loads data from {api_method} {api_pattern}"
  - "Loading state is shown while {api_pattern} request is pending"
  - "{action} triggers {api_method} {api_pattern} with correct payload"
  - "Error response from {api_pattern} displays user-friendly error message"
  - "Network timeout shows retry option or error state"
  - "Empty response from {api_pattern} shows empty state"
```

**Variables**:
- `api_method` — GET, POST, PUT, DELETE, PATCH
- `api_pattern` — abstracted path like `/api/orders/:id`
- `action` — user action triggering the API call

---

## 5. Routing Regression

**Trigger**: Dynamic route parameters (`:id`, query params) detected.

```yaml
expected_behaviors:
  - "Route {route_pattern} resolves with valid parameter"
  - "Route {route_pattern} shows 404 for non-existent resource"
  - "Query parameter {param_name} filters page content correctly"
  - "Route change from {route_a} to {route_b} preserves {shared_state}"
  - "Deep link to {route_with_params} renders correct content"
```

**Variables**:
- `route_pattern` — e.g. `/orders/:id`
- `param_name` — e.g. `page`, `sort`, `filter`
- `shared_state` — e.g. "search query", "selected filters"

---

## 6. Authentication Regression

**Trigger**: Auth flows detected in auth-flows.json.

```yaml
expected_behaviors:
  - "Login form accepts credentials and authenticates user"
  - "Successful login redirects to {post_login_route}"
  - "Failed login shows error message without clearing form"
  - "Protected route {protected_route} redirects to {login_route} without auth"
  - "Authenticated user can access {protected_route}"
  - "Logout clears session and redirects to {login_route}"
  - "Session persists across page reloads"
  - "Expired session redirects to {login_route}"
```

**Variables**:
- `post_login_route` — usually `/dashboard` or `/`
- `protected_route` — routes requiring authentication
- `login_route` — the login page route

---

## 7. Modal & Dialog Regression

**Trigger**: Dialog or modal elements detected in snapshots.

```yaml
expected_behaviors:
  - "Modal triggered by '{trigger_element}' is visible and focused"
  - "Modal can be dismissed via Escape key"
  - "Modal can be dismissed by clicking outside (backdrop click)"
  - "Modal confirm action at {route} performs expected operation"
  - "Modal cancel returns to previous state"
  - "Focus is trapped within modal while open"
  - "Focus returns to trigger element after modal closes"
```

**Variables**:
- `trigger_element` — button or link that opens the modal
- `route` — the page where the modal appears

---

## 8. Table & Data Display Regression

**Trigger**: Table elements or data grids detected.

```yaml
expected_behaviors:
  - "Table at {route} renders data from {api_endpoint}"
  - "Table displays correct column headers: {column_list}"
  - "Clicking column '{column_name}' sorts data ascending"
  - "Clicking column '{column_name}' again toggles to descending"
  - "Filter input filters table rows in real time"
  - "Pagination controls navigate between pages"
  - "Empty state shown when no data matches filters"
  - "Row action '{action_name}' triggers correct operation"
```

**Variables**:
- `column_list` — from table header cells in snapshot
- `column_name` — individual sortable column
- `action_name` — row-level action (edit, delete, view)

---

## 9. Error Boundary Regression

**Trigger**: Error states or fallback content detected; API error codes observed.

```yaml
expected_behaviors:
  - "Page at {route} shows error boundary on component crash"
  - "Error boundary displays user-friendly error message"
  - "Error boundary provides recovery action (retry or navigate)"
  - "404 page renders for non-existent routes"
  - "API error at {route} shows contextual error message"
  - "Network failure shows offline indicator or retry option"
```

---

## 10. Responsive Layout Regression

**Trigger**: Viewport-dependent behavior detected (media queries, responsive elements).

```yaml
expected_behaviors:
  - "Desktop viewport shows full layout with sidebar"
  - "Tablet viewport adapts layout for medium screens"
  - "Mobile viewport collapses navigation to hamburger menu"
  - "Content remains accessible at all viewport sizes"
  - "Touch targets meet minimum size (44x44px) on mobile"
  - "No horizontal scroll at any viewport width"
```

---

## Combining Templates

For a given flow, select templates based on its `regression_categories` from
the analysis output. Combine behaviors from multiple categories, removing
duplicates and contradictions.

**Example**: A flow with categories `["form_handling", "api_integration", "authentication"]`
would combine templates 3, 4, and 6.

**Deduplication rules**:
- If both "Form submission calls API" (template 3) and "Action triggers API"
  (template 4) reference the same endpoint, keep the more specific form version
- If both "Protected route redirects" (template 6) and "Direct URL renders"
  (template 5) reference the same route, keep the auth version for protected routes
