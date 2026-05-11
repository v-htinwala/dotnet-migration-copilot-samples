# UAT Qualification Criteria

This reference defines the qualification gate that every generated test case must pass before inclusion in the UAT deliverable.

---

## Core Principle

> **UAT validates "Did we build the RIGHT thing?"**
> System testing validates "Did we build the thing RIGHT?"

UAT test cases must focus on **business value, user goals, and real-world scenarios** — not on system internals, technical implementation, or code behavior.

---

## 6-Point UAT Qualification Gate

A test case **qualifies as UAT** only when it passes ALL six criteria:

| # | Criterion | What It Means | Pass Example | Fail Example |
|---|-----------|---------------|-------------|--------------|
| 1 | **Business user perspective** | Written in business language a tester can understand | "Click the 'Save' button" | "Trigger the handleSave() event" |
| 2 | **Validates business requirements** | Tests business outcomes and acceptance criteria | "Invoice total matches line items" | "Database column sum equals API response" |
| 3 | **Real-world scenarios** | Reflects actual end-user workflows and business terminology | "Customer searches for a laptop" | "Call GET /api/products?q=laptop" |
| 4 | **Executable by end users** | No developer tools, database access, or technical knowledge required | "Verify success message appears" | "Check HTTP 201 response in Network tab" |
| 5 | **Verifies business value** | Checks user goals and business outcomes | "Order confirmation email is referenced on screen" | "Assert email microservice was invoked" |
| 6 | **Focuses on "what" not "how"** | Describes what the user achieves, not how the system implements it | "User sees their updated name in the header" | "React state updated and re-rendered" |

### Applying the Gate During Generation

Before writing each test case to JSONL, mentally verify:

```
✓ Could an actual business user execute this test without developer help?
✓ Does the expected result describe something VISIBLE on screen?
✓ Are all test steps described with business action verbs (Click, Enter, Navigate)?
✓ Is the test case free of technical jargon (API, HTTP, SQL, DOM, JSON)?
✓ Does this test validate a business requirement, not a system behavior?
✓ Does the test focus on WHAT the user achieves, not HOW the system works?
```

---

## Non-UAT Indicator Detection

If any of these keywords appear in test steps or expected results, the test case likely fails UAT qualification and must be rewritten:

### Technical/API Terms (Non-UAT)
```
HTTP status code: 200, 201, 400, 401, 403, 404, 500, 502, 503
API: api endpoint, rest api, graphql, json response, xml response,
  request body, response body, header, content-type, bearer token,
  curl, postman, swagger, http method, webhook payload
```

### Database/Backend Terms (Non-UAT)
```
sql, query, database, table, column, foreign key, index,
stored procedure, trigger, migration, schema, orm, model instance,
INSERT, UPDATE, DELETE, SELECT, JOIN
```

### Developer Tools Terms (Non-UAT)
```
console.log, debugger, devtools, network tab, inspect element,
stack trace, heap, memory leak, cpu usage, profiler
```

### Code-Level Terms (Non-UAT)
```
function, method, class, interface, module import, dependency,
unit test, mock, stub, fixture, assertion, assertEquals,
handleClick, setState, dispatch, reducer, middleware
```

---

## Test Type Classification

Every test case must be assigned one of these UAT test types:

| Type | Description | When to Use | Example |
|------|-------------|------------|---------|
| **Functional** | Validates a specific business function | Single feature/action tests | "Verify user can submit an expense report" |
| **End-to-End** | Complete user journey across modules | Multi-step cross-feature workflows | "Verify order from cart to delivery notification" |
| **Integration** | Cross-system or external service interactions visible to users | Payment, SSO, email notifications | "Verify payment processes through payment gateway" |
| **Usability** | User experience, intuitiveness, accessibility | UX, responsiveness, error guidance | "Verify error messages guide user to correct input" |
| **Business Rules** | Validates business logic, calculations, policies | Discounts, thresholds, approval limits | "Verify 10% discount applies for orders over $100" |
| **Regression** | Previously working functionality still works | After changes/updates | "Verify login still works after password policy change" |

### Default: If the test doesn't clearly match another type, classify it as **Functional**.

---

## Coverage Area Classification

Every test case must be assigned one of these coverage areas:

| Area | Description | Example |
|------|-------------|---------|
| **Business Process** | Core business workflows | Invoice approval, order processing, refund flow |
| **User Role** | Role-specific functionality and permissions | Admin user management, manager approvals |
| **Module/Feature** | Specific application module or screen | Dashboard, reporting, data entry form |
| **Compliance** | Regulatory, security, audit requirements | Data privacy controls, access restrictions, audit trails |

### Default: If the test doesn't clearly match another area, classify it as **Module/Feature**.

---

## Priority Definitions (Business-Aligned)

| Priority | Code | Criteria | Examples |
|----------|------|----------|----------|
| **Critical** | P1 | Core business functions; Revenue-impacting; Regulatory compliance; Blocks all users | Login, checkout, payment processing, data privacy |
| **High** | P2 | Important workflows; Frequently used features; Impacts many users | Search, order management, reporting, user profile |
| **Medium** | P3 | Secondary features; Edge cases; Workarounds available | Advanced filters, export options, notification preferences |
| **Low** | P4 | Nice-to-have functionality; Cosmetic; Rarely used | Theme customization, keyboard shortcuts, tooltips |

### Priority Assignment Rules

1. **Entry/exit points** in a user journey → Critical (user can't start or complete without them)
2. **Revenue-generating features** → Critical (payment, checkout, subscription)
3. **Regulatory/compliance features** → Critical (data privacy, audit, access control)
4. **Frequently used daily workflows** → High
5. **Features with available workarounds** → Medium
6. **Infrequently used or cosmetic features** → Low

---

## UAT vs System Test — Quick Reference

| Aspect | UAT Test ✅ | System Test ❌ |
|--------|------------|---------------|
| **Perspective** | Business user | Developer/QA engineer |
| **Language** | Business terminology | Technical jargon |
| **Validates** | Business requirements | System specifications |
| **Executed by** | End users / business testers | QA engineers / dev team |
| **Expected result** | Visible screen outcome | API response / DB state |
| **Question answered** | "Did we build the right thing?" | "Did we build the thing right?" |
| **Test data** | Business-realistic values | Edge-case technical values |
| **Tools required** | Web browser only | Dev tools, API clients, DB access |

---

## Applying Qualification in the Workflow

### During Phase 0 (Journey Parsing)
- Map journey steps to **business requirements** (not technical specs)
- Assign **coverage areas** based on the business domain of each step
- Identify **user roles** if personas are mentioned

### During Phase 2 (Test Generation)
- For EACH test case, run the 6-point qualification gate mentally
- Assign `test_type` based on the test's scope and purpose
- Assign `coverage_area` based on the business domain
- Assign `priority` using the business-aligned criteria (not just position in journey)
- Rewrite any test that uses non-UAT keywords

### Quality Gate Checklist (Per Feature)
Before marking a feature as complete, verify:

- [ ] All test cases pass the 6-point UAT qualification gate
- [ ] Each test case has a `test_type` assigned
- [ ] Each test case has a `coverage_area` assigned
- [ ] Priority is based on business impact, not just technical importance
- [ ] Test steps use only business action verbs
- [ ] Expected results describe only visible screen outcomes
- [ ] No non-UAT indicator keywords present in any test case
