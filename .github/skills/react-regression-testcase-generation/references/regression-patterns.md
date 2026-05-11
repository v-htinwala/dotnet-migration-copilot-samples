# React Regression Testing Patterns

## Common Regression Scenarios

### 1. Component Rendering Changes
When a React component's render logic, JSX, or CSS is modified:
- Verify the component still renders expected content via `render()` + `screen` queries
- Check that all visible text/elements are still present using `screen.getByText()`, `screen.getByRole()`
- Validate conditional rendering still works for all states
- Test accessibility attributes (`aria-*`, roles) are preserved
- Confirm snapshot consistency (if using snapshot testing)

### 2. Hook Changes
When a custom hook is modified:
- Use `renderHook()` from `@testing-library/react` to test in isolation
- Verify return values and state updates are preserved
- Test side effects (e.g., `useEffect` cleanup) still execute correctly
- Check that dependent components still receive correct data

### 3. Context Provider Changes
When a React Context Provider is modified:
- Wrap component renders with the Provider and verify consumer behavior
- Test context value updates propagate correctly to consumers
- Validate default context values when no Provider is present
- Check that multiple nested Providers work correctly

### 4. Redux/Zustand/State Management Changes
When global state logic is modified:
- Test reducers produce correct state transitions
- Verify selectors return expected derived state
- Test thunks/sagas/effects trigger correct side effects
- Use `configureStore()` mock with `Provider` wrapper for component tests
- Verify action dispatch and state subscription behavior

### 5. React Router Changes
When routing logic, route components, or navigation is modified:
- Use `MemoryRouter` wrapper with initial entries for route testing
- Verify route params are parsed correctly
- Test navigation events and redirects
- Validate route guards and protected routes
- Check lazy-loaded route components render correctly

### 6. Form Handling Changes
When form logic, validation, or submission is modified:
- Use `userEvent.type()` to simulate user input
- Use `fireEvent.submit()` for form submission
- Verify validation messages appear for invalid input
- Test controlled vs uncontrolled form behavior
- Validate form reset behavior

### 7. Error Boundary Changes
When error handling or error boundary components are modified:
- Test that thrown errors are caught by the boundary
- Verify fallback UI renders correctly
- Test error recovery behavior
- Validate error reporting/logging

### 8. API Integration Changes
When API calls, data fetching, or server communication is modified:
- Use MSW (`msw`) for HTTP mocking: `server.use(http.get(...))`
- For Next.js API routes: use `supertest` for Express-style testing
- Verify request payloads and headers
- Test error response handling

### 9. Suspense/Lazy Loading Changes
When lazy loading or Suspense boundaries are modified:
- Use `waitFor()` for async rendering assertions
- Test loading states with Suspense fallback UI
- Verify lazy-loaded components render after loading

### 10. Ref Forwarding Changes
When `React.forwardRef` or ref usage is modified:
- Use `React.createRef()` to test ref assignment
- Verify imperative handle methods via `useImperativeHandle`
- Test ref forwarding through HOCs

## React Testing Library Regression Test Structure

### Jest Variant
```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// @requirement REQ-xxx
describe('Regression: UserProfile after PR #123', () => {
  const user = userEvent.setup();

  // --- Mocks ---
  const mockFetch = jest.fn();
  const mockNavigate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  // --- Behavior Preservation Tests ---

  describe('rendering behavior', () => {
    test('still renders user name and email', () => {
      render(<UserProfile user={{ name: 'Alice', email: 'alice@test.com' }} />);

      expect(screen.getByText('Alice')).toBeInTheDocument();
      expect(screen.getByText('alice@test.com')).toBeInTheDocument();
    });

    test('still shows loading state when data is fetching', () => {
      render(<UserProfile user={null} isLoading={true} />);

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });

  // --- Interaction Tests ---

  describe('user interactions', () => {
    test('still calls onEdit when edit button is clicked', async () => {
      const onEdit = jest.fn();
      render(<UserProfile user={{ name: 'Alice' }} onEdit={onEdit} />);

      await user.click(screen.getByRole('button', { name: /edit/i }));
      expect(onEdit).toHaveBeenCalledTimes(1);
    });
  });

  // --- Exception/Error Tests ---

  describe('error handling', () => {
    test('still shows error message on failed fetch', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<UserProfile userId={1} fetchUser={mockFetch} />);

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });
    });
  });
});
```

### Vitest Variant
```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, test, expect, vi, beforeEach } from 'vitest';

describe('Regression: UserProfile after PR #123', () => {
  const user = userEvent.setup();
  const mockFetch = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('still renders user name and email', () => {
    render(<UserProfile user={{ name: 'Alice', email: 'alice@test.com' }} />);

    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('alice@test.com')).toBeInTheDocument();
  });
});
```

## Custom Hook Test Pattern
```typescript
import { renderHook, act } from '@testing-library/react';

describe('Regression: useCounter hook', () => {
  test('still increments count', () => {
    const { result } = renderHook(() => useCounter(0));

    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(1);
  });

  test('still resets to initial value', () => {
    const { result } = renderHook(() => useCounter(5));

    act(() => {
      result.current.increment();
      result.current.reset();
    });

    expect(result.current.count).toBe(5);
  });
});
```

## Context Provider Test Pattern
```typescript
describe('Regression: AuthContext', () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <AuthProvider initialUser={{ name: 'Alice', role: 'admin' }}>
      {children}
    </AuthProvider>
  );

  test('still provides user data to consumers', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.user?.name).toBe('Alice');
    expect(result.current.isAuthenticated).toBe(true);
  });

  test('still provides logout function', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });
});
```

## Redux Store Test Pattern
```typescript
import { configureStore } from '@reduxjs/toolkit';
import { Provider } from 'react-redux';

describe('Regression: CartComponent with Redux', () => {
  const createTestStore = (preloadedState = {}) =>
    configureStore({
      reducer: { cart: cartReducer },
      preloadedState,
    });

  const renderWithStore = (ui: React.ReactElement, store = createTestStore()) => {
    return render(<Provider store={store}>{ui}</Provider>);
  };

  test('still displays cart items from store', () => {
    const store = createTestStore({
      cart: {
        items: [
          { id: 1, name: 'Widget', quantity: 2, price: 9.99 },
        ],
      },
    });

    renderWithStore(<CartComponent />, store);

    expect(screen.getByText('Widget')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });
});
```

## React Router Test Pattern
```typescript
import { MemoryRouter, Route, Routes } from 'react-router-dom';

describe('Regression: UserDetailPage routing', () => {
  test('still renders user detail for route param', () => {
    render(
      <MemoryRouter initialEntries={['/users/123']}>
        <Routes>
          <Route path="/users/:id" element={<UserDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/user 123/i)).toBeInTheDocument();
  });

  test('still redirects to login for unauthenticated users', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/login/i)).toBeInTheDocument();
  });
});
```

## Mocking Patterns for Regression Testing

### Jest — jest.mock / jest.fn
```typescript
// Mock entire module
jest.mock('./api/userApi', () => ({
  fetchUsers: jest.fn().mockResolvedValue([
    { id: 1, name: 'Alice' },
    { id: 2, name: 'Bob' },
  ]),
  createUser: jest.fn().mockResolvedValue({ id: 3, name: 'Charlie' }),
}));

// Mock with factory function
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    back: jest.fn(),
  }),
  usePathname: () => '/test',
}));

// Spy on object method
jest.spyOn(window, 'fetch').mockResolvedValue({
  ok: true,
  json: async () => mockData,
} as Response);
```

### Vitest — vi.mock / vi.fn
```typescript
// Mock entire module
vi.mock('./api/userApi', () => ({
  fetchUsers: vi.fn().mockResolvedValue([
    { id: 1, name: 'Alice' },
    { id: 2, name: 'Bob' },
  ]),
}));

// Spy
vi.spyOn(window, 'fetch').mockResolvedValue({
  ok: true,
  json: async () => mockData,
} as Response);
```

### MSW (Mock Service Worker) Handlers
```typescript
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  http.get('/api/users', () => {
    return HttpResponse.json([
      { id: 1, name: 'Alice' },
      { id: 2, name: 'Bob' },
    ]);
  }),
  http.post('/api/users', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: 3, ...body }, { status: 201 });
  }),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## Error Boundary Test Pattern
```typescript
describe('Regression: ErrorBoundary', () => {
  const ThrowError = () => {
    throw new Error('Test error');
  };

  test('still catches errors and shows fallback UI', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary fallback={<div>Something went wrong</div>}>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    consoleSpy.mockRestore();
  });
});
```

## Form Handling Test Pattern
```typescript
describe('Regression: LoginForm', () => {
  const user = userEvent.setup();

  test('still validates required fields', async () => {
    render(<LoginForm onSubmit={jest.fn()} />);

    await user.click(screen.getByRole('button', { name: /submit/i }));

    expect(screen.getByText(/email is required/i)).toBeInTheDocument();
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
  });

  test('still calls onSubmit with form data', async () => {
    const onSubmit = jest.fn();
    render(<LoginForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'secret123');
    await user.click(screen.getByRole('button', { name: /submit/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'secret123',
    });
  });
});
```

## Suspense/Lazy Loading Test Pattern
```typescript
describe('Regression: LazyDashboard', () => {
  test('still shows loading fallback while component loads', async () => {
    render(
      <Suspense fallback={<div>Loading...</div>}>
        <LazyDashboard />
      </Suspense>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });
  });
});
```

## Common React Regression Risks

| Risk | Detection | Mitigation |
|---|---|---|
| Props contract break | Prop types or destructuring changed | Test all consumer components with existing props |
| Hook return value change | Return type or shape modified | Test with `renderHook()` |
| Context value change | Provider value shape modified | Test consumer components receiving context |
| Event handler regression | Handler logic or binding changed | Test with `userEvent.click/type/etc.` |
| Conditional render change | Display conditions modified | Test all rendering branches |
| API contract break | Request/response shape changed | Test with MSW handlers |
| Route config change | Path or guard logic modified | Test with MemoryRouter |
| State update regression | setState or reducer logic changed | Test state transitions |
| Effect cleanup regression | useEffect cleanup changed | Test mount/unmount cycle |
| Ref forwarding break | forwardRef or ref usage changed | Test with createRef |

## Data-Driven Regression Tests

### JSON Fixture Loading (Jest)
```typescript
import fixtureData from '../__fixtures__/users.json';

describe('Regression: UserList (data-driven)', () => {
  test.each(fixtureData)('should render user $name correctly', (user) => {
    render(<UserCard user={user} />);
    expect(screen.getByText(user.name)).toBeInTheDocument();
  });
});
```

### Inline Test.each
```typescript
describe('Regression: formatCurrency', () => {
  test.each([
    [1234.56, '$1,234.56'],
    [0, '$0.00'],
    [-100, '-$100.00'],
    [null, '$0.00'],
  ])('should format %s as %s', (input, expected) => {
    expect(formatCurrency(input)).toBe(expected);
  });
});
```

## Integration Regression Test Patterns

Use these patterns when `test_level` is `integration` or `both`.

### MSW Handler-Based API Integration
```typescript
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  http.get('/api/users', () => {
    return HttpResponse.json([
      { id: 1, name: 'Alice', email: 'alice@test.com' },
    ]);
  }),
);

describe('Regression: UserListPage integration', () => {
  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  test('still fetches and renders users from API', async () => {
    render(<UserListPage />);

    await waitFor(() => {
      expect(screen.getByText('Alice')).toBeInTheDocument();
    });
  });

  test('still handles API error gracefully', async () => {
    server.use(
      http.get('/api/users', () => {
        return new HttpResponse(null, { status: 500 });
      }),
    );

    render(<UserListPage />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });
});
```

### Full App/Page-Level Rendering with Providers
```typescript
describe('Regression: App integration', () => {
  const renderApp = (route = '/') => {
    return render(
      <Provider store={createTestStore()}>
        <MemoryRouter initialEntries={[route]}>
          <App />
        </MemoryRouter>
      </Provider>
    );
  };

  test('still renders home page at /', () => {
    renderApp('/');
    expect(screen.getByText('Welcome')).toBeInTheDocument();
  });

  test('still renders user list at /users', async () => {
    renderApp('/users');
    await waitFor(() => {
      expect(screen.getByText('Users')).toBeInTheDocument();
    });
  });
});
```

## Requirement-Traced Regression Tests

### Scenario-Driven Nested Describe Blocks
```typescript
// @requirement REQ-CART-001
// @requirement REQ-CART-002
describe('Regression: ShoppingCart', () => {

  describe('Scenario: Cart Total Calculation [REQ-CART-001]', () => {
    test('[REQ-CART-001] should still calculate correct subtotal', () => {
      // ...
    });

    test('[REQ-CART-001] should still apply discount codes', () => {
      // ...
    });
  });

  describe('Scenario: Cart Persistence [REQ-CART-002]', () => {
    test('[REQ-CART-002] should still save cart to localStorage', () => {
      // ...
    });

    test('[REQ-CART-002] should still restore cart on page reload', () => {
      // ...
    });
  });
});
```

## CI/CD Integration Patterns

### Jest — JUnit Reporter
Add to `jest.config.js`:
```javascript
module.exports = {
  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: 'regression-reports',
      outputName: 'regression-results.xml'
    }]
  ]
};
```

### Vitest — JUnit Reporter
Add to `vitest.config.ts`:
```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    reporters: ['default', 'junit'],
    outputFile: {
      junit: 'regression-reports/regression-results.xml',
    },
  },
});
```

### Flaky Test Detection
```typescript
// Mark known flaky tests for quarantine
// @flaky - intermittent due to animation timing
describe('Regression: AnimatedPanel (flaky)', () => {
  test('should complete entrance animation', async () => {
    // Known flaky due to animation timing; quarantined from blocking CI
  });
});
```
