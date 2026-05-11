# Playwright Regression Testing Patterns

## Common Regression Scenarios

### 1. Page Navigation & Rendering Changes
When a page component's render logic, JSX, or layout is modified:
- Navigate to the page via `page.goto()` and verify expected content
- Check that all visible text/elements are still present using `page.locator()` and `expect(locator)`
- Validate conditional rendering still works for all states
- Test accessibility attributes via `expect(locator).toHaveAttribute('aria-*', ...)`
- Use `expect(page).toHaveScreenshot()` for visual regression (when baselines exist)

### 2. Component Interaction Changes
When a component's interactive behavior is modified:
- Use `locator.click()`, `locator.fill()`, `locator.selectOption()` to simulate user actions
- Verify state changes are reflected in the DOM via `expect(locator).toHaveText()`
- Test keyboard navigation with `page.keyboard.press()`
- Validate focus management with `expect(locator).toBeFocused()`

### 3. Form Handling Changes
When form logic, validation, or submission is modified:
- Use `locator.fill()` to populate form fields
- Use `locator.click()` on submit buttons
- Verify validation messages appear via `expect(page.locator('.error')).toBeVisible()`
- Intercept form submission API calls via `page.route()` to verify payloads
- Test form reset and clear behaviors

### 4. API Integration Changes
When API calls, data fetching, or server communication is modified:
- Use `page.route()` to intercept and mock API responses
- Verify correct API endpoints are called via `page.waitForRequest()`
- Test error response handling by mocking error responses
- Validate loading states with `expect(locator).toBeVisible()` during API calls
- Use `page.waitForResponse()` to synchronize on network activity

### 5. Routing & Navigation Changes
When routing logic, links, or navigation is modified:
- Verify `page.goto()` reaches the correct page
- Test link clicks with `locator.click()` and verify `page.url()` changes
- Validate URL parameters are parsed correctly
- Test browser back/forward navigation with `page.goBack()`/`page.goForward()`
- Verify redirect behavior for protected routes

### 6. Authentication Flow Changes
When auth logic, login/logout, or session management is modified:
- Test login flow: fill credentials, submit, verify redirect to authenticated page
- Test logout flow: click logout, verify redirect to login page
- Use `page.context().storageState()` to persist/restore auth state between tests
- Verify protected routes redirect unauthenticated users

### 7. Modal/Dialog Changes
When modal, dialog, or overlay components are modified:
- Test modal open/close behavior with `expect(locator).toBeVisible()` / `toBeHidden()`
- Verify modal content renders correctly
- Test escape key dismissal with `page.keyboard.press('Escape')`
- Verify backdrop click dismissal
- Test focus trapping within the modal

### 8. Table/List/Data Display Changes
When data tables, lists, or grid components are modified:
- Verify correct number of rows/items via `locator.count()`
- Test sorting by clicking column headers and verifying order
- Test filtering by entering filter text and verifying visible rows
- Test pagination by clicking page buttons and verifying content changes
- Verify empty state rendering

### 9. Error Boundary & Error State Changes
When error handling or error display components are modified:
- Mock failing API calls via `page.route()` and verify error UI
- Test retry buttons and error recovery flows
- Verify error messages are user-friendly and accessible

### 10. Responsive Layout Changes
When CSS, layout, or responsive behavior is modified:
- Test at multiple viewport sizes via `page.setViewportSize()`
- Verify mobile menu behavior
- Test responsive table/grid layouts
- Verify hidden/shown elements at different breakpoints

## Playwright E2E Regression Test Structure

```typescript
import { test, expect, Page } from '@playwright/test';

// @requirement REQ-xxx
test.describe('Regression: UserProfile page after PR #123', () => {
  let page: Page;

  test.beforeEach(async ({ page: p }) => {
    page = p;
  });

  // --- Behavior Preservation Tests ---

  test.describe('rendering behavior', () => {
    test('still renders user name and email', async ({ page }) => {
      // Mock the user API
      await page.route('**/api/users/1', (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ id: 1, name: 'Alice', email: 'alice@test.com' }),
        })
      );

      await page.goto('/users/1');

      await expect(page.getByText('Alice')).toBeVisible();
      await expect(page.getByText('alice@test.com')).toBeVisible();
    });

    test('still shows loading state when data is fetching', async ({ page }) => {
      // Delay the API response to observe loading state
      await page.route('**/api/users/1', async (route) => {
        await new Promise((r) => setTimeout(r, 2000));
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ id: 1, name: 'Alice' }),
        });
      });

      await page.goto('/users/1');

      await expect(page.getByText('Loading...')).toBeVisible();
    });
  });

  // --- Interaction Tests ---

  test.describe('user interactions', () => {
    test('still navigates to edit page when edit button is clicked', async ({ page }) => {
      await page.route('**/api/users/1', (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ id: 1, name: 'Alice' }),
        })
      );

      await page.goto('/users/1');
      await page.getByRole('button', { name: /edit/i }).click();

      await expect(page).toHaveURL(/\/users\/1\/edit/);
    });
  });

  // --- Error Handling Tests ---

  test.describe('error handling', () => {
    test('still shows error message on failed fetch', async ({ page }) => {
      await page.route('**/api/users/1', (route) =>
        route.fulfill({ status: 500, body: 'Internal Server Error' })
      );

      await page.goto('/users/1');

      await expect(page.getByText(/error/i)).toBeVisible();
    });
  });
});
```

## Playwright Component Test Pattern

```typescript
import { test, expect } from '@playwright/experimental-ct-react';
import { UserProfile } from '../components/UserProfile';

test.describe('Regression: UserProfile component', () => {
  test('still renders user name and email', async ({ mount }) => {
    const component = await mount(
      <UserProfile user={{ name: 'Alice', email: 'alice@test.com' }} />
    );

    await expect(component.getByText('Alice')).toBeVisible();
    await expect(component.getByText('alice@test.com')).toBeVisible();
  });

  test('still renders empty state for null user', async ({ mount }) => {
    const component = await mount(<UserProfile user={null} isLoading={false} />);

    await expect(component.getByText('No user data')).toBeVisible();
  });

  test('still calls onEdit when edit button is clicked', async ({ mount }) => {
    let editCalled = false;
    const component = await mount(
      <UserProfile
        user={{ name: 'Alice' }}
        onEdit={() => { editCalled = true; }}
      />
    );

    await component.getByRole('button', { name: /edit/i }).click();
    expect(editCalled).toBe(true);
  });
});
```

## API Mocking Patterns for Regression Testing

### Playwright Route Interception (Recommended for E2E)
```typescript
test.describe('API mocking via route interception', () => {
  test.beforeEach(async ({ page }) => {
    // Mock GET /api/users — default success response
    await page.route('**/api/users', (route) => {
      if (route.request().method() === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, name: 'Alice', email: 'alice@test.com' },
            { id: 2, name: 'Bob', email: 'bob@test.com' },
          ]),
        });
      }
      return route.continue();
    });

    // Mock POST /api/users
    await page.route('**/api/users', (route) => {
      if (route.request().method() === 'POST') {
        return route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({ id: 3, name: 'Charlie' }),
        });
      }
      return route.continue();
    });
  });

  test('fetches and renders users', async ({ page }) => {
    await page.goto('/users');
    await expect(page.getByText('Alice')).toBeVisible();
    await expect(page.getByText('Bob')).toBeVisible();
  });
});
```

### Intercepting and Verifying Request Payloads
```typescript
test('submits correct data to API', async ({ page }) => {
  let capturedBody: any;

  await page.route('**/api/users', async (route) => {
    if (route.request().method() === 'POST') {
      capturedBody = route.request().postDataJSON();
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ id: 3, ...capturedBody }),
      });
    } else {
      await route.continue();
    }
  });

  await page.goto('/users/new');
  await page.getByLabel('Name').fill('Charlie');
  await page.getByLabel('Email').fill('charlie@test.com');
  await page.getByRole('button', { name: /submit/i }).click();

  expect(capturedBody).toEqual(
    expect.objectContaining({ name: 'Charlie', email: 'charlie@test.com' })
  );
});
```

### Simulating Error Responses
```typescript
test('handles API server error', async ({ page }) => {
  await page.route('**/api/users', (route) =>
    route.fulfill({ status: 500, body: 'Internal Server Error' })
  );

  await page.goto('/users');

  await expect(page.getByText(/error/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /retry/i })).toBeVisible();
});
```

## Authentication Flow Test Pattern

```typescript
import { test, expect } from '@playwright/test';

test.describe('Regression: Authentication flow', () => {
  test('still allows login with valid credentials', async ({ page }) => {
    await page.route('**/api/auth/login', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ token: 'fake-jwt-token', user: { name: 'Alice' } }),
      })
    );

    await page.goto('/login');
    await page.getByLabel('Email').fill('alice@test.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: /sign in/i }).click();

    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Alice')).toBeVisible();
  });

  test('still redirects unauthenticated users to login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });

  test('still logs out and redirects to login', async ({ page }) => {
    // Set up authenticated state
    await page.goto('/login');
    // ... login flow ...

    await page.getByRole('button', { name: /logout/i }).click();
    await expect(page).toHaveURL(/\/login/);
  });
});
```

## Reusable Auth State Pattern

```typescript
// auth.setup.ts — Run once to create authenticated state
import { test as setup, expect } from '@playwright/test';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('admin@test.com');
  await page.getByLabel('Password').fill('admin123');
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page).toHaveURL('/dashboard');

  // Save signed-in state
  await page.context().storageState({ path: '.auth/user.json' });
});

// Use in tests:
// test.use({ storageState: '.auth/user.json' });
```

## Form Handling Test Pattern

```typescript
test.describe('Regression: Registration Form', () => {
  test('still validates required fields', async ({ page }) => {
    await page.goto('/register');
    await page.getByRole('button', { name: /submit/i }).click();

    await expect(page.getByText(/email is required/i)).toBeVisible();
    await expect(page.getByText(/password is required/i)).toBeVisible();
  });

  test('still validates email format', async ({ page }) => {
    await page.goto('/register');
    await page.getByLabel('Email').fill('invalid-email');
    await page.getByRole('button', { name: /submit/i }).click();

    await expect(page.getByText(/invalid email/i)).toBeVisible();
  });

  test('still submits form data on valid input', async ({ page }) => {
    let capturedBody: any;
    await page.route('**/api/register', async (route) => {
      capturedBody = route.request().postDataJSON();
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ id: 1 }),
      });
    });

    await page.goto('/register');
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('SecurePass123!');
    await page.getByLabel('Confirm Password').fill('SecurePass123!');
    await page.getByRole('button', { name: /submit/i }).click();

    expect(capturedBody).toEqual(
      expect.objectContaining({ email: 'test@example.com' })
    );
  });
});
```

## Modal/Dialog Test Pattern

```typescript
test.describe('Regression: Confirmation Dialog', () => {
  test('still opens on delete button click', async ({ page }) => {
    await page.goto('/items');
    await page.getByRole('button', { name: /delete/i }).first().click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText(/are you sure/i)).toBeVisible();
  });

  test('still closes on cancel', async ({ page }) => {
    await page.goto('/items');
    await page.getByRole('button', { name: /delete/i }).first().click();

    const dialog = page.getByRole('dialog');
    await dialog.getByRole('button', { name: /cancel/i }).click();
    await expect(dialog).toBeHidden();
  });

  test('still closes on Escape key', async ({ page }) => {
    await page.goto('/items');
    await page.getByRole('button', { name: /delete/i }).first().click();

    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(dialog).toBeHidden();
  });
});
```

## Table/Data Display Test Pattern

```typescript
test.describe('Regression: Users Table', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/users*', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: [
            { id: 1, name: 'Alice', email: 'alice@test.com' },
            { id: 2, name: 'Bob', email: 'bob@test.com' },
            { id: 3, name: 'Charlie', email: 'charlie@test.com' },
          ],
          total: 3,
        }),
      })
    );
  });

  test('still renders correct number of rows', async ({ page }) => {
    await page.goto('/users');
    const rows = page.locator('table tbody tr');
    await expect(rows).toHaveCount(3);
  });

  test('still sorts by name when column header is clicked', async ({ page }) => {
    await page.goto('/users');
    await page.getByRole('columnheader', { name: /name/i }).click();

    const firstRow = page.locator('table tbody tr').first();
    await expect(firstRow).toContainText('Alice');
  });

  test('still filters rows by search input', async ({ page }) => {
    await page.goto('/users');
    await page.getByPlaceholder(/search/i).fill('Alice');

    const rows = page.locator('table tbody tr');
    await expect(rows).toHaveCount(1);
    await expect(rows.first()).toContainText('Alice');
  });
});
```

## Responsive Layout Test Pattern

```typescript
test.describe('Regression: Responsive Layout', () => {
  test('still shows mobile menu on small viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    await expect(page.getByRole('button', { name: /menu/i })).toBeVisible();
    await expect(page.getByRole('navigation')).toBeHidden();

    await page.getByRole('button', { name: /menu/i }).click();
    await expect(page.getByRole('navigation')).toBeVisible();
  });

  test('still shows full navigation on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/');

    await expect(page.getByRole('navigation')).toBeVisible();
  });
});
```

## Visual Regression Test Pattern

```typescript
test.describe('Regression: Visual snapshots', () => {
  test('homepage visual regression', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveScreenshot('homepage.png', {
      maxDiffPixelRatio: 0.01,
    });
  });

  test('dashboard visual regression (authenticated)', async ({ page }) => {
    // Mock auth and data
    await page.route('**/api/dashboard', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ stats: { users: 100, orders: 50 } }),
      })
    );

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('dashboard.png', {
      maxDiffPixelRatio: 0.02,
    });
  });

  test('component-level visual regression', async ({ page }) => {
    await page.goto('/test-button-avatar');

    const card = page.locator('[data-testid="stat-card"]').first();
    await expect(card).toHaveScreenshot('stat-card.png');
  });
});
```

## Locator Best Practices for Regression Tests

| Priority | Locator Strategy | Example | When to Use |
|---|---|---|---|
| 1 | Role-based | `page.getByRole('button', { name: /submit/i })` | Interactive elements |
| 2 | Label-based | `page.getByLabel('Email')` | Form inputs |
| 3 | Text-based | `page.getByText('Welcome')` | Static content |
| 4 | Placeholder | `page.getByPlaceholder('Search...')` | Search/filter inputs |
| 5 | Test ID | `page.getByTestId('user-card')` | When semantic locators aren't available |
| 6 | CSS selector | `page.locator('.card-header')` | Last resort |

## Common Playwright Regression Risks

| Risk | Detection | Mitigation |
|---|---|---|
| Page navigation break | URL or route changed | Test with `page.goto()` + `expect(page).toHaveURL()` |
| Interactive element regression | Button/link behavior changed | Test with `locator.click()` + verify side effects |
| Form validation change | Validation rules modified | Test all valid/invalid input combinations |
| API contract break | Request/response shape changed | Test with `page.route()` mock + verify payloads |
| Layout/responsive break | CSS or layout logic changed | Test at multiple viewport sizes |
| Auth flow regression | Login/logout logic changed | Test complete auth lifecycle |
| Loading state regression | Async timing changed | Use `page.waitForResponse()` or delayed route mocks |
| Modal behavior change | Open/close or focus logic changed | Test open, close, escape, backdrop click |
| Accessibility regression | ARIA attributes or focus changed | Test with `toHaveAttribute('aria-*')` + `toBeFocused()` |
| Visual regression | Style or layout broke | Use `toHaveScreenshot()` comparisons |

## Data-Driven Regression Tests

### Parameterized Tests
```typescript
const testCases = [
  { path: '/users', title: 'Users', expectedHeading: 'User Management' },
  { path: '/orders', title: 'Orders', expectedHeading: 'Order List' },
  { path: '/reports', title: 'Reports', expectedHeading: 'Analytics' },
];

for (const { path, title, expectedHeading } of testCases) {
  test(`still renders ${title} page correctly`, async ({ page }) => {
    await page.goto(path);
    await expect(page.getByRole('heading', { name: expectedHeading })).toBeVisible();
  });
}
```

### JSON Fixture-Driven Tests
```typescript
import fixtureData from '../__fixtures__/users.json';

for (const user of fixtureData) {
  test(`still renders user ${user.name} correctly`, async ({ page }) => {
    await page.route('**/api/users/' + user.id, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(user),
      })
    );

    await page.goto(`/users/${user.id}`);
    await expect(page.getByText(user.name)).toBeVisible();
    await expect(page.getByText(user.email)).toBeVisible();
  });
}
```

## Requirement-Traced Regression Tests

### Scenario-Driven Nested Describe Blocks
```typescript
// @requirement REQ-CART-001
// @requirement REQ-CART-002
test.describe('Regression: Shopping Cart', () => {

  test.describe('Scenario: Cart Total Calculation [REQ-CART-001]', () => {
    test('[REQ-CART-001] should still calculate correct subtotal', async ({ page }) => {
      test.info().annotations.push({ type: 'requirement', description: 'REQ-CART-001' });
      // ...
    });

    test('[REQ-CART-001] should still apply discount codes', async ({ page }) => {
      test.info().annotations.push({ type: 'requirement', description: 'REQ-CART-001' });
      // ...
    });
  });

  test.describe('Scenario: Cart Persistence [REQ-CART-002]', () => {
    test('[REQ-CART-002] should still save cart to localStorage', async ({ page }) => {
      test.info().annotations.push({ type: 'requirement', description: 'REQ-CART-002' });

      await page.goto('/cart');
      // Add item to cart
      // Verify localStorage via page.evaluate()
      const cartData = await page.evaluate(() =>
        JSON.parse(localStorage.getItem('cart') || '{}')
      );
      expect(cartData.items).toHaveLength(1);
    });
  });
});
```

## CI/CD Integration Patterns

### Playwright Config for Regression
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.spec.ts',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI
    ? [
        ['junit', { outputFile: 'regression-reports/regression-results.xml' }],
        ['html', { open: 'never', outputFolder: 'regression-reports/report' }],
        ['json', { outputFile: 'regression-reports/regression-results.json' }],
      ]
    : [['html', { open: 'on-failure' }]],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Flaky Test Detection
```typescript
// Mark known flaky tests for quarantine
// @flaky - intermittent due to animation timing
test.describe('Regression: AnimatedPanel (flaky)', () => {
  test.fixme('should complete entrance animation', async ({ page }) => {
    // Known flaky due to animation timing; quarantined from blocking CI
  });
});
```
