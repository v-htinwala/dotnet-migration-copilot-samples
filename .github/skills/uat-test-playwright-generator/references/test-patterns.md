# UAT Test Patterns Reference (Senior Tester Approach)

Comprehensive testing patterns for common web application scenarios, written from the perspective of a **Senior UAT Tester** exploring a live application via Playwright CLI.

> **Mindset**: Don't just test what's obvious. A Senior Tester explores every corner, tries every edge case, and thinks about what real users would do — including their mistakes.

---

## 1. Authentication Patterns

### 1.1 Login Flow Tests

A Senior Tester doesn't just check "can I log in?" — they test every authentication scenario.

#### Positive Tests

```bash
# TC-AUTH-001: Valid Login
playwright-cli open https://[app-url]/login
playwright-cli snapshot --filename=snapshots/login-page.yaml
playwright-cli screenshot --filename=screenshots/TC-AUTH-001-initial.png
playwright-cli fill [email-ref] "valid_user@example.com"
playwright-cli fill [password-ref] "ValidPassword123!"
playwright-cli click [login-button-ref]
playwright-cli snapshot --filename=snapshots/after-login.yaml
playwright-cli screenshot --filename=screenshots/TC-AUTH-001-result.png
# VERIFY: Dashboard loads; User name in header; Menu visible
```

#### Negative Tests

```bash
# TC-AUTH-002: Invalid Credentials
playwright-cli fill [email-ref] "invalid@example.com"
playwright-cli fill [password-ref] "wrongpassword"
playwright-cli click [login-button-ref]
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/TC-AUTH-002-error.png
# VERIFY: Error message displayed; User stays on login page; Password cleared

# TC-AUTH-003: Empty Fields
playwright-cli click [login-button-ref]  # Submit without entering anything
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/TC-AUTH-003-validation.png
# VERIFY: Required field validation messages; Form not submitted

# TC-AUTH-004: SQL Injection Attempt
playwright-cli fill [email-ref] "' OR 1=1 --"
playwright-cli fill [password-ref] "' OR 1=1 --"
playwright-cli click [login-button-ref]
playwright-cli snapshot
# VERIFY: Login fails gracefully; No error stack trace exposed

# TC-AUTH-005: XSS Attempt
playwright-cli fill [email-ref] "<script>alert('xss')</script>"
playwright-cli click [login-button-ref]
playwright-cli snapshot
# VERIFY: Input sanitized; No script execution
```

#### Boundary Tests

```bash
# TC-AUTH-006: Very Long Email
playwright-cli fill [email-ref] "a]@example.com"  # 300+ chars
playwright-cli click [login-button-ref]
playwright-cli snapshot
# VERIFY: Handled gracefully (truncated or error)

# TC-AUTH-007: Special Characters in Password
playwright-cli fill [email-ref] "user@example.com"
playwright-cli fill [password-ref] "P@$$w0rd!#%^&*()"
playwright-cli click [login-button-ref]
playwright-cli snapshot
# VERIFY: Special characters accepted in password
```

### 1.2 Logout & Session Tests

```bash
# TC-AUTH-008: Successful Logout
playwright-cli click [user-menu-ref]
playwright-cli click [logout-ref]
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/TC-AUTH-008-logout.png
# VERIFY: Redirected to login; Session terminated

# TC-AUTH-009: Back Button After Logout
playwright-cli click [user-menu-ref]
playwright-cli click [logout-ref]
# Press browser back
playwright-cli eval "await page.goBack()"
playwright-cli snapshot
# VERIFY: Cannot access protected pages after logout

# TC-AUTH-010: Password Reset
playwright-cli click [forgot-password-ref]
playwright-cli snapshot
playwright-cli fill [email-ref] "user@example.com"
playwright-cli click [submit-ref]
playwright-cli screenshot --filename=screenshots/TC-AUTH-010-reset.png
# VERIFY: Confirmation message; Email sent notification
```

---

## 2. Form Handling Patterns

### 2.1 Data Entry — Senior Tester Approach

A Senior Tester tests EVERY field, not just the happy path.

#### Complete Form Submission (Positive)

```bash
playwright-cli open https://[app-url]/form
playwright-cli snapshot --filename=snapshots/form-initial.yaml

# Fill ALL fields
playwright-cli fill [name-ref] "John Doe"
playwright-cli fill [email-ref] "john.doe@example.com"
playwright-cli fill [phone-ref] "+1234567890"
playwright-cli select [country-ref] "US"
playwright-cli fill [address-ref] "123 Main Street"
playwright-cli check [terms-ref]
playwright-cli screenshot --filename=screenshots/TC-FORM-001-filled.png
playwright-cli click [submit-ref]
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/TC-FORM-001-success.png
# VERIFY: Success message; Data saved; Redirected or form cleared
```

#### Field-by-Field Validation (Negative)

```bash
# TC-FORM-002: Empty Required Fields
playwright-cli click [submit-ref]  # Submit empty form
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/TC-FORM-002-required.png
# VERIFY: Error on EACH required field; Count errors vs required fields

# TC-FORM-003: Invalid Email Format
playwright-cli fill [email-ref] "not-an-email"
playwright-cli click [submit-ref]
playwright-cli snapshot
# VERIFY: Email format error displayed

# TC-FORM-004: Invalid Phone Format
playwright-cli fill [phone-ref] "abc123"
playwright-cli click [submit-ref]
playwright-cli snapshot
# VERIFY: Phone format error displayed
```

#### Boundary Tests

```bash
# TC-FORM-005: Maximum Field Length
playwright-cli fill [name-ref] "A".repeat(500)
playwright-cli snapshot
# VERIFY: Input truncated or max length error

# TC-FORM-006: Special Characters
playwright-cli fill [name-ref] "O'Brien-Smith & Co. <Ltd>"
playwright-cli click [submit-ref]
playwright-cli snapshot
# VERIFY: Special characters handled; No XSS; Saves correctly

# TC-FORM-007: Unicode/International Characters
playwright-cli fill [name-ref] "José García Müller 田中太郎"
playwright-cli click [submit-ref]
playwright-cli snapshot
# VERIFY: International characters saved and displayed correctly

# TC-FORM-008: Leading/Trailing Whitespace
playwright-cli fill [name-ref] "   John Doe   "
playwright-cli click [submit-ref]
playwright-cli snapshot
# VERIFY: Whitespace trimmed or handled appropriately
```

#### Usability Tests

```bash
# TC-FORM-009: Tab Order
playwright-cli press Tab  # Navigate through fields
playwright-cli snapshot
# VERIFY: Tab moves through fields in logical order

# TC-FORM-010: Cancel/Discard Changes
playwright-cli fill [name-ref] "Unsaved Data"
playwright-cli click [cancel-ref]
playwright-cli snapshot
# VERIFY: Confirmation prompt (if applicable); Changes discarded

# TC-FORM-011: Double Submit Prevention
playwright-cli fill [name-ref] "Test"
playwright-cli click [submit-ref]
playwright-cli click [submit-ref]  # Rapid double click
playwright-cli snapshot
# VERIFY: Only one record created; Button disabled after first click
```

### 2.2 File Upload

```bash
# TC-FILE-001: Valid File Upload
playwright-cli upload ./test-files/valid-document.pdf
playwright-cli snapshot
playwright-cli click [upload-submit-ref]
playwright-cli screenshot --filename=screenshots/TC-FILE-001-upload.png
# VERIFY: File in list; Size and name correct; Success message

# TC-FILE-002: Invalid File Type
playwright-cli upload ./test-files/invalid-file.exe
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/TC-FILE-002-invalid.png
# VERIFY: Error about unsupported type; File not uploaded

# TC-FILE-003: Oversized File
playwright-cli upload ./test-files/large-file-50mb.zip
playwright-cli snapshot
# VERIFY: Size limit error; File not uploaded

# TC-FILE-004: Empty File
playwright-cli upload ./test-files/empty-file.txt
playwright-cli snapshot
# VERIFY: Handled gracefully (error or accepted)
```

---

## 3. CRUD Operation Patterns

### 3.1 Create → Read → Update → Delete (Full Lifecycle)

A Senior Tester tests the COMPLETE lifecycle, not isolated operations.

```bash
# === CREATE ===
playwright-cli open https://[app-url]/items
playwright-cli screenshot --filename=screenshots/TC-CRUD-001-before.png
playwright-cli click [add-new-ref]
playwright-cli snapshot
playwright-cli fill [name-ref] "Test Item for CRUD"
playwright-cli fill [description-ref] "Created for lifecycle testing"
playwright-cli click [save-ref]
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/TC-CRUD-001-created.png
# VERIFY: Item in list; Success message; Correct values

# === READ ===
playwright-cli click [view-item-ref]  # Click the item just created
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/TC-CRUD-002-details.png
# VERIFY: Detail page shows all fields correctly; Back navigation works

# === UPDATE ===
playwright-cli click [edit-ref]
playwright-cli snapshot
playwright-cli fill [name-ref] "Updated Test Item"
playwright-cli click [save-ref]
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/TC-CRUD-003-updated.png
# VERIFY: Updated name in list; Success message; Old value replaced

# === DELETE ===
playwright-cli click [delete-ref]
playwright-cli screenshot --filename=screenshots/TC-CRUD-004-confirm.png
playwright-cli dialog-accept
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/TC-CRUD-004-deleted.png
# VERIFY: Item removed from list; Success message; Count decreased

# === VERIFY DELETION ===
# Search for the deleted item
playwright-cli fill [search-ref] "Updated Test Item"
playwright-cli press Enter
playwright-cli snapshot
# VERIFY: No results found — item truly deleted
```

---

## 4. Navigation Patterns

### 4.1 Comprehensive Navigation Testing

```bash
# TC-NAV-001: All Menu Items
playwright-cli open https://[app-url]
playwright-cli snapshot

# Click EVERY menu item and verify
playwright-cli click [menu-home-ref]
playwright-cli snapshot --filename=snapshots/nav-home.yaml
playwright-cli screenshot --filename=screenshots/TC-NAV-001-home.png

playwright-cli click [menu-about-ref]
playwright-cli snapshot --filename=snapshots/nav-about.yaml
# VERIFY: Each page loads; Active menu highlighted; URL changes

# TC-NAV-002: Breadcrumb Navigation
playwright-cli open https://[app-url]/category/subcategory/item
playwright-cli snapshot
playwright-cli click [breadcrumb-category-ref]
playwright-cli snapshot
# VERIFY: Breadcrumb shows correct path; Clicking navigates correctly

# TC-NAV-003: Pagination
playwright-cli open https://[app-url]/items
playwright-cli click [next-page-ref]
playwright-cli snapshot
playwright-cli click [prev-page-ref]
playwright-cli snapshot
# VERIFY: Items change; Page indicator updates; Buttons disable at edges

# TC-NAV-004: Direct URL Access
playwright-cli open https://[app-url]/protected-page
playwright-cli snapshot
# VERIFY: If not logged in, redirected to login; If logged in, page loads

# TC-NAV-005: 404 Page
playwright-cli open https://[app-url]/nonexistent-page-xyz
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/TC-NAV-005-404.png
# VERIFY: Friendly 404 page; Navigation still works; No raw error
```

---

## 5. Search and Filter Patterns

```bash
# TC-SEARCH-001: Basic Search
playwright-cli fill [search-ref] "test query"
playwright-cli press Enter
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/TC-SEARCH-001-results.png
# VERIFY: Results match query; Count displayed; Search term highlighted

# TC-SEARCH-002: No Results
playwright-cli fill [search-ref] "xyznonexistent123"
playwright-cli press Enter
playwright-cli snapshot
# VERIFY: "No results" message; Suggestions shown (if applicable)

# TC-SEARCH-003: Special Characters in Search
playwright-cli fill [search-ref] "O'Brien & Co."
playwright-cli press Enter
playwright-cli snapshot
# VERIFY: Search handles special chars; No errors

# TC-SEARCH-004: Empty Search
playwright-cli fill [search-ref] ""
playwright-cli press Enter
playwright-cli snapshot
# VERIFY: All records shown or appropriate message

# TC-FILTER-001: Single Filter
playwright-cli select [category-filter-ref] "Category A"
playwright-cli snapshot
# VERIFY: Only Category A items shown; Filter indicator visible

# TC-FILTER-002: Multiple Filters
playwright-cli select [category-filter-ref] "Category A"
playwright-cli select [status-filter-ref] "Active"
playwright-cli snapshot
# VERIFY: Results match ALL criteria; All filters visible

# TC-FILTER-003: Clear Filters
playwright-cli click [clear-filters-ref]
playwright-cli snapshot
# VERIFY: All records restored; Filter indicators removed

# TC-SORT-001: Column Sort
playwright-cli click [column-header-ref]  # Sort ascending
playwright-cli snapshot
playwright-cli click [column-header-ref]  # Sort descending
playwright-cli snapshot
# VERIFY: Data order changes; Sort indicator visible
```

---

## 6. Error Handling Patterns

```bash
# TC-ERR-001: Network Error Recovery
# (Simulate by disconnecting network briefly)
playwright-cli snapshot
# VERIFY: Error message displayed; Retry option available; No data loss

# TC-ERR-002: Form Error Recovery
playwright-cli click [submit-ref]  # Submit with errors
playwright-cli snapshot
# Fix the errors
playwright-cli fill [required-field-ref] "Valid Value"
playwright-cli click [submit-ref]
playwright-cli snapshot
# VERIFY: Can recover from errors without page reload; Previous valid data preserved
```

---

## 7. Responsive Design Patterns

```bash
# TC-RESP-001: Desktop (1920x1080)
playwright-cli resize 1920 1080
playwright-cli open https://[app-url]
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/TC-RESP-001-desktop.png
# VERIFY: Full navigation visible; Content aligned; All features accessible

# TC-RESP-002: Tablet (768x1024)
playwright-cli resize 768 1024
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/TC-RESP-002-tablet.png
# VERIFY: Navigation adapts; Content reflows; Key features work

# TC-RESP-003: Mobile (375x812)
playwright-cli resize 375 812
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/TC-RESP-003-mobile.png
# VERIFY: Mobile menu works; No horizontal scroll; Touch targets adequate

# Reset to desktop
playwright-cli resize 1920 1080
```

---

## 8. Cross-Feature Interaction Patterns

A Senior Tester tests how features work TOGETHER, not just in isolation.

```bash
# TC-CROSS-001: Create then Search
# 1. Create a new record with unique name
playwright-cli click [add-new-ref]
playwright-cli fill [name-ref] "UniqueTestItem_12345"
playwright-cli click [save-ref]
# 2. Search for it
playwright-cli fill [search-ref] "UniqueTestItem_12345"
playwright-cli press Enter
playwright-cli snapshot
# VERIFY: Newly created item appears in search results

# TC-CROSS-002: Edit then Verify in Detail
# 1. Edit a record
playwright-cli click [edit-ref]
playwright-cli fill [name-ref] "Modified Name"
playwright-cli click [save-ref]
# 2. Open detail view
playwright-cli click [view-ref]
playwright-cli snapshot
# VERIFY: Detail view shows the modified name

# TC-CROSS-003: Filter then Paginate
# 1. Apply a filter
playwright-cli select [filter-ref] "Category A"
# 2. Navigate pages
playwright-cli click [next-page-ref]
playwright-cli snapshot
# VERIFY: Filter persists across pages; Only filtered items shown
```

---

## Usage Notes

1. Replace `[ref]` placeholders with actual element references from `playwright-cli snapshot`
2. Replace `[app-url]` with the actual application URL
3. Create screenshots and snapshots directories before running
4. **Always re-snapshot after interactions** — element refs may change
5. A Senior Tester captures evidence (screenshots) at EVERY verification point
