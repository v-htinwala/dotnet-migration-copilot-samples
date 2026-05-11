# Phase 0: Journey Input Processing

> **NEW**: Accept natural language user journey descriptions from UAT testers and use them to guide exploration.

---

## Overview

Phase 0 is an **optional** preprocessing step that transforms natural language journey descriptions into a prioritized exploration plan. When UAT testers provide journey descriptions, the agent uses them as **starting points** for targeted exploration, then discovers additional scenarios around each journey step.

```
WITH JOURNEYS:
  Journeys + URL → Phase 0 (Parse + Analyze) → Phase 1 (Targeted Discovery) → Phase 2 → Phase 3

WITHOUT JOURNEYS:
  URL only → Phase 1 (Full Discovery) → Phase 2 → Phase 3
```

---

## Step 0.0: Requirements Analysis (UAT Foundation)

> Before parsing journeys, establish the **business context**. This is how Senior UAT Testers operate — they always start from requirements.

### What to Extract from Journey Input

When UAT testers provide journey descriptions, analyze them for:

| Element | What to Identify | Example |
|---------|-----------------|---------|
| **Business requirements** | What business goal does this journey serve? | "Customer must be able to place an order" |
| **User stories** | Who is the user and what do they want? | "As a customer, I want to search for products" |
| **Acceptance criteria** | What defines success? | "Order confirmation must display order number" |
| **User personas/roles** | Who executes this journey? | Customer, Admin, Manager |
| **Business processes** | What business workflow is this? | Order processing, user onboarding |
| **Compliance needs** | Any regulatory or audit requirements? | Data privacy, access control |

### Enriching Journey Steps with Business Context

For each parsed journey step, add:

```json
{
  "step": 1,
  "action": "logs in",
  "feature_type": "Authentication",
  "priority": "Critical",
  "user_role": "Customer",
  "business_objective": "Users must authenticate to access personalized shopping experience",
  "coverage_area": "Business Process",
  "acceptance_criteria": "User sees dashboard with their name after successful login"
}
```

This business context flows into Phase 2 test generation, where each test case gets:
- `user_role` from the persona identified here
- `business_objective` from the requirement identified here
- `coverage_area` from the business domain identified here
- `test_type` based on whether the step is standalone (Functional) or part of a cross-module journey (End-to-End)

---

## Journey Input Format

UAT testers describe user journeys in simple, natural language.

### Accepted Formats

**Simple sentence:**
```
User logs in, searches for a laptop, adds it to cart, and completes checkout.
```

**Numbered list:**
```
1. Customer creates an account
2. Customer browses the product catalog
3. Customer adds items to wishlist
4. Customer purchases items from wishlist
```

**Persona-based:**
```
ADMIN:
- Admin logs in with admin credentials
- Admin navigates to user management
- Admin creates a new user account
- Admin assigns roles to the user

CUSTOMER:
- Customer receives account credentials
- Customer logs in for the first time
- Customer resets password
```

**Scenario format:**
```
Scenario: New customer onboarding
Given: Customer visits the website for the first time
Journey: Sign up → Verify email → Complete profile → Browse products → Make first purchase
```

---

## Journey Parsing

### Step 0.1: Extract Actions and Objects

Parse the journey into discrete steps with actions (verbs) and objects (nouns):

| Journey Text | Action (Verb) | Object (Noun) | Feature Type |
|--------------|---------------|---------------|--------------|
| "logs in" | Login | Credentials | Authentication |
| "searches for laptop" | Search | Product | Search |
| "adds to cart" | Add | Cart | Cart Management |
| "completes checkout" | Complete | Checkout | Workflow |
| "creates account" | Create | Account | Registration |
| "browses catalog" | Browse | Catalog | List/Search |

### Step 0.2: Map to Feature Types

Use this mapping to identify which features each journey step involves:

| Action Keywords | Feature Type | Expected Elements |
|-----------------|--------------|-------------------|
| login, sign in, authenticate | Authentication | Login form, credentials fields |
| register, sign up, create account | Registration | Registration form, terms checkbox |
| search, find, look for | Search | Search bar, results list |
| browse, view, list | List/Search | Data grid, filters, pagination |
| add, create, new | Form/Create | Create form, input fields |
| edit, update, modify | Form/Edit | Edit form, save button |
| delete, remove | Delete Confirmation | Delete button, confirm dialog |
| checkout, purchase, buy | Workflow | Multi-step form, payment |
| settings, configure, preferences | Settings | Settings page, toggles |
| upload, attach | File Management | File input, upload button |

### Step 0.3: Build Priority Map

Generate a prioritized feature list based on journey sequence:

```json
{
  "journey_id": "J-001",
  "journey_text": "User logs in, searches for laptop, adds to cart, completes checkout",
  "user_role": "Customer",
  "business_process": "Online Purchase",
  "parsed_steps": [
    {
      "step": 1,
      "action": "logs in",
      "feature_type": "Authentication",
      "priority": "Critical",
      "expected_url_pattern": "/login",
      "user_role": "Customer",
      "business_objective": "Users must authenticate to access personalized shopping",
      "coverage_area": "Business Process",
      "test_type": "Functional"
    },
    {
      "step": 2,
      "action": "searches for laptop",
      "feature_type": "Search",
      "priority": "High",
      "expected_url_pattern": "/search",
      "user_role": "Customer",
      "business_objective": "Users must find products to make purchases",
      "coverage_area": "Module/Feature",
      "test_type": "Functional"
    },
    {
      "step": 3,
      "action": "adds to cart",
      "feature_type": "Cart Management",
      "priority": "High",
      "expected_url_pattern": "/cart",
      "user_role": "Customer",
      "business_objective": "Users must collect items before checkout",
      "coverage_area": "Business Process",
      "test_type": "Functional"
    },
    {
      "step": 4,
      "action": "completes checkout",
      "feature_type": "Checkout Workflow",
      "priority": "Critical",
      "expected_url_pattern": "/checkout",
      "user_role": "Customer",
      "business_objective": "Users must complete purchase — revenue-generating",
      "coverage_area": "Business Process",
      "test_type": "End-to-End"
    }
  ]
}
```

> **Note**: The entire journey (steps 1→4) is also an **End-to-End** test scenario. While each step generates Functional tests, the complete journey should also produce at least one End-to-End test covering the full flow.

---

## Priority Assignment Rules

| Criterion | Priority | Rationale |
|-----------|----------|-----------|
| Entry/exit points in journey | Critical | User can't start or complete without them |
| Revenue-generating features | Critical | Directly impacts business income |
| Regulatory/compliance features | Critical | Legal or audit requirements |
| Frequently used daily workflows | High | Impacts many users regularly |
| Middle steps in journey | High | Part of user flow |
| Features with workarounds available | Medium | Users can work around issues |
| Branching/optional steps | Medium | Secondary paths |
| Cosmetic/nice-to-have | Low | Minimal business impact |

---

## Output: Journey-Guided Feature Map

Phase 0 produces a `JOURNEY_FEATURE_MAP` that guides Phase 1 exploration:

```
═══════════════════════════════════════════════════════════════
JOURNEY ANALYSIS COMPLETE
═══════════════════════════════════════════════════════════════

INPUT JOURNEYS: 2
UNIQUE FEATURES IDENTIFIED: 6
USER ROLES IDENTIFIED: Customer, Admin

JOURNEY-GUIDED FEATURE MAP:

┌────┬─────────────────────┬────────────┬──────────────┬─────────────┬──────────────┬──────────────┐
│ ID │ Feature Name        │ Type       │ Priority     │ Coverage    │ User Role    │ From Journey │
├────┼─────────────────────┼────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ 1  │ Authentication      │ Login      │ Critical     │ Business Pr │ Customer     │ J-001 Step 1 │
│ 2  │ Product Search      │ Search     │ High         │ Module/Feat │ Customer     │ J-001 Step 2 │
│ 3  │ Shopping Cart       │ Cart       │ High         │ Business Pr │ Customer     │ J-001 Step 3 │
│ 4  │ Checkout            │ Workflow   │ Critical     │ Business Pr │ Customer     │ J-001 Step 4 │
│ 5  │ User Registration   │ Form       │ Critical     │ Business Pr │ New User     │ J-002 Step 1 │
│ 6  │ Admin Dashboard     │ Dashboard  │ High         │ User Role   │ Admin        │ J-002 Step 3 │
└────┴─────────────────────┴────────────┴──────────────┴──────────────┴──────────────┴──────────────┘

Phase 1 will explore these features in priority order.
Additional features discovered during exploration will be added.
═══════════════════════════════════════════════════════════════
```

---

## Integration with Phase 1

When journeys are provided, Phase 1 becomes **targeted exploration**:

1. **Start with journey features** — Navigate to URLs identified from journeys
2. **Validate journey steps** — Confirm the journey is achievable
3. **Discover adjacent features** — While exploring, note additional features
4. **Expand feature map** — Add discovered features not in original journeys

### Example Flow

```bash
# Journey step: "User logs in"
# Expected: /login page with credentials form

playwright-cli open https://app.example.com/login --headed
playwright-cli snapshot --filename=snapshots/journey-step-1-login.yaml

# Validate: Does this match the journey expectation?
# - Login form present? ✓
# - Can user enter credentials? ✓
# - Login button visible? ✓

# Discovery: What else is on this page?
# - "Forgot Password" link → Add to feature map
# - "Register" link → Add to feature map
# - Social login buttons → Add to feature map
```

---

## Multiple Journeys

When multiple journeys are provided:

1. Parse each journey separately
2. Merge overlapping features (e.g., both journeys include "login")
3. Keep the highest priority for shared features
4. Process all unique features in Phase 1

### Example: Overlapping Journeys

```
Journey 1: "Customer logs in, browses products, makes purchase"
Journey 2: "Admin logs in, manages inventory, generates reports"

Merged Feature Map:
- Authentication (Critical) — both journeys
- Product Catalog (High) — Journey 1
- Checkout (Critical) — Journey 1
- Admin Dashboard (High) — Journey 2
- Inventory Management (High) — Journey 2
- Reports (High) — Journey 2
```

---

## When Journeys Are Not Provided

If the user provides only a URL without journey descriptions:

1. Skip Phase 0
2. Proceed directly to Phase 1 (Full Discovery)
3. Explore the entire application systematically
4. Discover features through navigation exploration

---

## Sample Journey Processing

### Input

```
User Journey: "A customer visits the store, searches for wireless headphones, 
compares two products, adds the cheaper one to cart, applies a coupon code, 
and completes purchase with credit card."
```

### Parsed Output

| Step | Action | Feature | Priority | URL Pattern | Elements to Find |
|------|--------|---------|----------|-------------|------------------|
| 1 | visits store | Landing | High | / | Navigation, search |
| 2 | searches headphones | Search | High | /search | Search bar, results |
| 3 | compares products | Comparison | Medium | /compare | Compare button, side-by-side |
| 4 | adds to cart | Cart | High | /cart | Add button, cart view |
| 5 | applies coupon | Discount | Medium | /cart | Coupon field, apply button |
| 6 | completes purchase | Checkout | Critical | /checkout | Payment form, submit |

### Test Case Implications

For step 5 "applies a coupon code", generate tests for:
- Valid coupon applied successfully
- Invalid coupon shows error
- Expired coupon shows appropriate message
- Coupon field validation (empty, special chars)
- Coupon removal after adding
- Multiple coupon attempts

This is **journey-guided exploration** — the journey tells us WHERE to test, and Senior Tester thinking tells us WHAT to test.
