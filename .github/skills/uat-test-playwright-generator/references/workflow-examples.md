# Workflow Examples (Senior UAT Tester)

Complete end-to-end workflow examples showing how a **Senior UAT Tester** explores and generates test cases from a live web application using Playwright CLI.

> **Key Difference**: These workflows follow the 3-Phase methodology — Feature Discovery first, then Test Case Generation, then Excel output.

---

## Workflow 1: E-commerce Application

### Phase 1: Feature Discovery

```bash
# Step 1: Open the application
playwright-cli open https://shop.example.com --headed
playwright-cli snapshot --filename=snapshots/00-landing.yaml
playwright-cli screenshot --filename=screenshots/00-landing.png

# Step 2: Explore navigation
playwright-cli snapshot  # Identify all nav elements

# Click each menu item to discover pages
playwright-cli click e15  # Home
playwright-cli snapshot --filename=snapshots/nav-home.yaml

playwright-cli click e16  # Products
playwright-cli snapshot --filename=snapshots/nav-products.yaml

playwright-cli click e17  # Cart
playwright-cli snapshot --filename=snapshots/nav-cart.yaml

playwright-cli click e18  # Account
playwright-cli snapshot --filename=snapshots/nav-account.yaml

# Step 3: Explore sub-pages
playwright-cli click e22  # Product category
playwright-cli snapshot --filename=snapshots/nav-category.yaml

playwright-cli click e45  # Individual product
playwright-cli snapshot --filename=snapshots/nav-product-detail.yaml

# Step 4: Check for forms and actions
playwright-cli click e67  # Add to cart button
playwright-cli snapshot --filename=snapshots/cart-after-add.yaml

playwright-cli click e70  # Checkout button
playwright-cli snapshot --filename=snapshots/checkout-form.yaml
```

**Feature Map Output:**

```
═══════════════════════════════════════════════════════════════
APPLICATION: E-commerce Shop (https://shop.example.com)
═══════════════════════════════════════════════════════════════

┌────┬─────────────────────┬────────────┬──────────────┬─────────────┐
│ ID │ Feature Name        │ Type       │ URL/Route    │ Est. Tests  │
├────┼─────────────────────┼────────────┼──────────────┼─────────────┤
│ 1  │ Authentication      │ Login      │ /login       │ 12          │
│ 2  │ Product Catalog     │ List/Search│ /products    │ 18          │
│ 3  │ Product Details     │ Detail     │ /products/:id│ 10          │
│ 4  │ Shopping Cart       │ Workflow   │ /cart        │ 15          │
│ 5  │ Checkout            │ Form       │ /checkout    │ 25          │
│ 6  │ Order Confirmation  │ Detail     │ /orders/:id  │ 8           │
│ 7  │ User Account        │ Settings   │ /account     │ 12          │
│ 8  │ Search              │ Search     │ /search      │ 10          │
└────┴─────────────────────┴────────────┴──────────────┴─────────────┘

TOTAL ESTIMATED TEST CASES: 110
═══════════════════════════════════════════════════════════════
```

### Phase 2: Test Case Generation (Feature by Feature)

#### Feature 1: Authentication

```bash
# Explore login page
playwright-cli open https://shop.example.com/login
playwright-cli snapshot --filename=snapshots/auth-login.yaml
playwright-cli screenshot --filename=screenshots/auth-login.png

# Try empty submit (negative discovery)
playwright-cli click e9  # Login button
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/auth-empty-submit.png
# OBSERVED: Validation errors on email and password fields

# Try invalid credentials (negative discovery)
playwright-cli fill e5 "invalid@example.com"
playwright-cli fill e7 "wrongpassword"
playwright-cli click e9
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/auth-invalid-creds.png
# OBSERVED: "Invalid email or password" error message

# Try valid login (positive discovery)
playwright-cli fill e5 "testuser@example.com"
playwright-cli fill e7 "ValidPass123!"
playwright-cli click e9
playwright-cli snapshot --filename=snapshots/auth-after-login.yaml
playwright-cli screenshot --filename=screenshots/auth-success.png
# OBSERVED: Redirected to homepage; User name in header

# Check for forgot password link
playwright-cli open https://shop.example.com/login
playwright-cli click e10  # Forgot password link
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/auth-forgot-password.png
# OBSERVED: Password reset form with email field
```

**Generated Test Cases → Write to JSONL immediately:**

```jsonl
{"test_case_id":"TC-AUTH-001","title":"Login with valid credentials","feature_area":"Authentication","priority":"Critical","preconditions":"User has valid account; App accessible","test_steps":"1. Navigate to login page\n2. Enter email: testuser@example.com\n3. Enter password\n4. Click Sign In\n5. Verify dashboard loads","test_data":"Email: testuser@example.com, Password: ValidPass123!","expected_result":"User redirected to homepage with name in header","validation_points":"Homepage loads; User name visible; Menu accessible","playwright_commands":"playwright-cli open https://shop.example.com/login\nplaywright-cli fill e5 \"testuser@example.com\"\nplaywright-cli fill e7 \"ValidPass123!\"\nplaywright-cli click e9","screenshots":"auth-login.png; auth-success.png","status":"Not Started","comments":""}
{"test_case_id":"TC-AUTH-002","title":"Login fails with invalid credentials","feature_area":"Authentication","priority":"Critical","preconditions":"App accessible","test_steps":"1. Navigate to login page\n2. Enter invalid email\n3. Enter wrong password\n4. Click Sign In\n5. Observe error message","test_data":"Email: invalid@example.com, Password: wrongpassword","expected_result":"Error message 'Invalid email or password' displayed; user stays on login page","validation_points":"Error message visible; Login form still shown; No navigation","playwright_commands":"playwright-cli open https://shop.example.com/login\nplaywright-cli fill e5 \"invalid@example.com\"\nplaywright-cli fill e7 \"wrongpassword\"\nplaywright-cli click e9","screenshots":"auth-invalid-creds.png","status":"Not Started","comments":""}
```

```
───────────────────────────────────────────────────────────────
FEATURE COMPLETE: Authentication
   Positive: 3 | Negative: 5 | Validation: 2 | Boundary: 2
   Total: 12 test cases (TC-AUTH-001 to TC-AUTH-012)
   ✓ Written to: uat_ecommerce.jsonl
───────────────────────────────────────────────────────────────
```

#### Feature 4: Shopping Cart (Cross-Feature Example)

```bash
# Navigate to products first
playwright-cli open https://shop.example.com/products
playwright-cli snapshot

# Add item to cart
playwright-cli click e45  # First product
playwright-cli snapshot
playwright-cli click e67  # Add to cart
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/cart-item-added.png
# OBSERVED: Cart count badge updates; "Added to cart" toast message

# Go to cart
playwright-cli click e17  # Cart nav
playwright-cli snapshot --filename=snapshots/cart-with-items.yaml
playwright-cli screenshot --filename=screenshots/cart-view.png
# OBSERVED: Item in cart; Quantity field; Remove button; Subtotal

# Try changing quantity
playwright-cli fill e34 "2"
playwright-cli click e35  # Update
playwright-cli snapshot
# OBSERVED: Subtotal recalculated

# Try quantity 0
playwright-cli fill e34 "0"
playwright-cli click e35
playwright-cli snapshot
# OBSERVED: Item removed or error message

# Try negative quantity
playwright-cli fill e34 "-1"
playwright-cli click e35
playwright-cli snapshot
# OBSERVED: Validation error

# Try empty cart checkout
playwright-cli click e50  # Checkout with empty cart
playwright-cli snapshot
# OBSERVED: "Cart is empty" message or checkout button disabled
```

---

## Workflow 2: SaaS Admin Dashboard

### Phase 1: Feature Discovery

```bash
playwright-cli open https://admin.example.com --headed
playwright-cli snapshot --filename=snapshots/00-landing.yaml

# Login
playwright-cli fill e5 "admin@example.com"
playwright-cli fill e6 "AdminPass123!"
playwright-cli click e7
playwright-cli snapshot --filename=snapshots/01-dashboard.yaml
playwright-cli screenshot --filename=screenshots/01-dashboard.png

# Explore sidebar navigation
playwright-cli click e20  # Dashboard
playwright-cli snapshot --filename=snapshots/nav-dashboard.yaml

playwright-cli click e21  # Users
playwright-cli snapshot --filename=snapshots/nav-users.yaml

playwright-cli click e22  # Settings
playwright-cli snapshot --filename=snapshots/nav-settings.yaml

playwright-cli click e23  # Reports
playwright-cli snapshot --filename=snapshots/nav-reports.yaml

playwright-cli click e24  # Audit Log
playwright-cli snapshot --filename=snapshots/nav-audit.yaml

# Explore user management sub-pages
playwright-cli click e21  # Users
playwright-cli click e30  # Add User button
playwright-cli snapshot --filename=snapshots/user-create-form.yaml

# Explore settings sub-sections
playwright-cli click e22  # Settings
playwright-cli click e40  # General tab
playwright-cli snapshot
playwright-cli click e41  # Security tab
playwright-cli snapshot
playwright-cli click e42  # Notifications tab
playwright-cli snapshot
```

**Feature Map:**

```
┌────┬─────────────────────┬────────────┬──────────────┬─────────────┐
│ ID │ Feature Name        │ Type       │ URL/Route    │ Est. Tests  │
├────┼─────────────────────┼────────────┼──────────────┼─────────────┤
│ 1  │ Authentication      │ Login      │ /login       │ 12          │
│ 2  │ Dashboard           │ Dashboard  │ /dashboard   │ 10          │
│ 3  │ User Management     │ CRUD       │ /users       │ 30          │
│ 4  │ General Settings    │ Settings   │ /settings    │ 10          │
│ 5  │ Security Settings   │ Settings   │ /settings    │ 8           │
│ 6  │ Reports             │ Reports    │ /reports     │ 12          │
│ 7  │ Audit Log           │ List       │ /audit       │ 10          │
│ 8  │ Notifications       │ Settings   │ /settings    │ 6           │
└────┴─────────────────────┴────────────┴──────────────┴─────────────┘

TOTAL ESTIMATED TEST CASES: 98
```

### Phase 2: User Management (CRUD Feature Example)

```bash
# Explore user list
playwright-cli open https://admin.example.com/users
playwright-cli snapshot --filename=snapshots/users-list.yaml
playwright-cli screenshot --filename=screenshots/users-list.png

# Identify elements: search bar, add button, table with edit/delete icons, pagination

# === CREATE USER ===
playwright-cli click e30  # Add User
playwright-cli snapshot --filename=snapshots/user-form.yaml
playwright-cli screenshot --filename=screenshots/user-form-empty.png

# Try empty submit
playwright-cli click e50  # Save button
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/user-form-validation.png
# OBSERVED: Required field errors on name, email, role

# Fill valid data
playwright-cli fill e31 "newuser@example.com"
playwright-cli fill e32 "New"
playwright-cli fill e33 "User"
playwright-cli select e34 "Editor"
playwright-cli screenshot --filename=screenshots/user-form-filled.png
playwright-cli click e50  # Save
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/user-created.png
# OBSERVED: Success message; User appears in list

# === SEARCH FOR CREATED USER ===
playwright-cli fill e25 "newuser"
playwright-cli press Enter
playwright-cli snapshot
# OBSERVED: Filtered list shows the new user

# === EDIT USER ===
playwright-cli click e60  # Edit button on the user row
playwright-cli snapshot
playwright-cli select e34 "Admin"  # Change role
playwright-cli click e50  # Save
playwright-cli snapshot
# OBSERVED: Role updated; Success message

# === DELETE USER ===
playwright-cli click e65  # Delete button
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/user-delete-confirm.png
playwright-cli dialog-accept
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/user-deleted.png
# OBSERVED: User removed from list; Success message
```

---

## Workflow 3: Content Management System

### Phase 1: Quick Discovery

```bash
playwright-cli open https://cms.example.com --headed

# Login
playwright-cli fill e5 "editor@example.com"
playwright-cli fill e6 "EditorPass123"
playwright-cli click e7
playwright-cli snapshot --filename=snapshots/cms-dashboard.yaml

# Explore all navigation
playwright-cli click e15  # Articles
playwright-cli snapshot --filename=snapshots/cms-articles.yaml

playwright-cli click e16  # Media Library
playwright-cli snapshot --filename=snapshots/cms-media.yaml

playwright-cli click e17  # Categories
playwright-cli snapshot --filename=snapshots/cms-categories.yaml

playwright-cli click e18  # Users (if admin)
playwright-cli snapshot --filename=snapshots/cms-users.yaml
```

### Phase 2: Article Management (Workflow Feature)

```bash
# === CREATE ARTICLE ===
playwright-cli click e15  # Articles
playwright-cli click e25  # New Article
playwright-cli snapshot --filename=snapshots/article-editor.yaml

# Fill article form
playwright-cli fill e30 "Test Article Title"
playwright-cli click e35  # Rich text editor
playwright-cli type "This is the article body content for testing."
playwright-cli select e40 "Technology"  # Category
playwright-cli screenshot --filename=screenshots/article-filled.png

# === SAVE AS DRAFT ===
playwright-cli click e45  # Save Draft
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/article-draft.png
# OBSERVED: "Draft saved" message; Status shows "Draft"

# === PREVIEW ===
playwright-cli click e50  # Preview button
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/article-preview.png
# OBSERVED: Preview opens; Content renders correctly

# === PUBLISH ===
playwright-cli click e55  # Publish button
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/article-publish-confirm.png
playwright-cli click e56  # Confirm publish
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/article-published.png
# OBSERVED: Status changes to "Published"; Published date shown

# === VERIFY ON FRONTEND ===
playwright-cli tab-new https://cms.example.com/articles/test-article-title
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/article-live.png
# OBSERVED: Article visible on public site; Content matches
```

---

## Workflow 4: Multi-Step Form (Wizard)

### Senior Tester Approach to Wizards

```bash
playwright-cli open https://app.example.com/onboarding --headed
playwright-cli snapshot --filename=snapshots/wizard-step1.yaml

# === STEP 1: Personal Info ===
# Try skipping to step 2 without completing step 1
playwright-cli click e20  # Next button
playwright-cli snapshot
# OBSERVED: Validation errors; Cannot proceed

# Fill step 1
playwright-cli fill e10 "John"
playwright-cli fill e11 "Doe"
playwright-cli fill e12 "john@example.com"
playwright-cli click e20  # Next
playwright-cli snapshot --filename=snapshots/wizard-step2.yaml

# === STEP 2: Preferences ===
# Try going back
playwright-cli click e25  # Back button
playwright-cli snapshot
# OBSERVED: Step 1 data preserved

playwright-cli click e20  # Next again
playwright-cli select e30 "Dark"  # Theme
playwright-cli check e31  # Email notifications
playwright-cli click e20  # Next
playwright-cli snapshot --filename=snapshots/wizard-step3.yaml

# === STEP 3: Review & Submit ===
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/wizard-review.png
# OBSERVED: Summary of all entered data

playwright-cli click e40  # Submit
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/wizard-complete.png
# OBSERVED: Success page; "Setup complete" message

# === EDGE CASE: Browser back during wizard ===
playwright-cli open https://app.example.com/onboarding
playwright-cli fill e10 "Jane"
playwright-cli click e20  # Next
playwright-cli eval "await page.goBack()"
playwright-cli snapshot
# OBSERVED: Does step 1 preserve data? Or reset?
```

---

## Output Structure After Workflows

```
uat-tests/
├── uat_<project>.jsonl              # All test cases
├── UAT_Test_Cases_<Project>.xlsx    # Excel deliverable (Phase 3)
├── screenshots/
│   ├── 00-landing.png
│   ├── 01-dashboard.png
│   ├── auth-*.png
│   ├── cart-*.png
│   ├── user-*.png
│   └── ...
└── snapshots/
    ├── 00-landing.yaml
    ├── nav-*.yaml
    ├── auth-*.yaml
    └── ...
```

---

## Tips for Senior UAT Testers

1. **Explore before testing** — Phase 1 discovery prevents missing features
2. **Try the wrong thing first** — negative tests often reveal more bugs than positive ones
3. **Test the full lifecycle** — Create → Search → Edit → Delete → Verify deletion
4. **Check cross-feature interactions** — features don't exist in isolation
5. **Re-snapshot after every interaction** — element refs change after page updates
6. **Capture screenshots at every verification point** — evidence matters
7. **Think like a real user** — what would a confused, impatient, or careless user do?
8. **Write to JSONL after each feature** — don't accumulate in memory
9. **Test responsive layouts** — mobile users are real users
10. **Check error recovery** — can the user fix mistakes without starting over?
