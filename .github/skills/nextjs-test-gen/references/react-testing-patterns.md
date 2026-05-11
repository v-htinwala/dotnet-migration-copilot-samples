# React Testing Library Patterns for React 19

## Core Imports

```typescript
import { render, screen, waitFor, within, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
```

## Rendering Components

### Basic render

```typescript
it('renders the component', () => {
  render(<MyComponent title="Hello" />)
  expect(screen.getByText('Hello')).toBeInTheDocument()
})
```

### Render with providers (context, theme, router, etc.)

```typescript
function renderWithProviders(
  ui: React.ReactElement,
  options?: { initialState?: Partial<AppState>; route?: string }
) {
  const { initialState = {}, route = '/' } = options ?? {}

  return render(
    <QueryClientProvider client={new QueryClient()}>
      <ThemeProvider>
        {ui}
      </ThemeProvider>
    </QueryClientProvider>
  )
}

// Usage
it('renders with providers', () => {
  renderWithProviders(<Dashboard />, { route: '/dashboard' })
  expect(screen.getByRole('heading')).toHaveTextContent('Dashboard')
})
```

**If the project has a custom render wrapper** (e.g., `@company/test-utils`),
use it instead of creating a new one. Check `.github/test-gen-instructions/global.md`.

### Render with custom user for userEvent

```typescript
it('handles user interactions', async () => {
  const user = userEvent.setup()
  render(<LoginForm onSubmit={mockSubmit} />)

  await user.type(screen.getByLabelText('Email'), 'test@example.com')
  await user.type(screen.getByLabelText('Password'), 'password123')
  await user.click(screen.getByRole('button', { name: 'Sign in' }))

  expect(mockSubmit).toHaveBeenCalledWith({
    email: 'test@example.com',
    password: 'password123',
  })
})
```

## Query Priority

Follow the RTL query priority (most accessible → least):

1. **`getByRole`** — always prefer; mirrors how assistive tech sees the page
2. **`getByLabelText`** — for form fields
3. **`getByPlaceholderText`** — only if no label
4. **`getByText`** — for non-interactive text content
5. **`getByDisplayValue`** — for filled form inputs
6. **`getByAltText`** — for images
7. **`getByTitle`** — last resort for visible content
8. **`getByTestId`** — escape hatch only (data-testid attribute)

**Avoid**: `container.querySelector`, `container.firstChild`, or any
DOM-specific selectors. These break accessibility and are brittle.

## Async Patterns (React 19)

### waitFor — for async state updates

```typescript
it('loads data asynchronously', async () => {
  render(<UserProfile userId="1" />)

  // Wait for loading to finish
  await waitFor(() => {
    expect(screen.getByText('John Doe')).toBeInTheDocument()
  })

  // Or wait for loading indicator to disappear
  await waitFor(() => {
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
  })
})
```

### findBy queries — shorthand for waitFor + getBy

```typescript
it('loads data', async () => {
  render(<UserProfile userId="1" />)

  const name = await screen.findByText('John Doe')
  expect(name).toBeInTheDocument()
})
```

### React 19 `use()` hook

Components using `use()` to unwrap promises need the promise to resolve
during rendering. Wrap in `<Suspense>`:

```typescript
import { Suspense } from 'react'

it('renders data from use() hook', async () => {
  const dataPromise = Promise.resolve({ name: 'Test' })

  render(
    <Suspense fallback={<div>Loading...</div>}>
      <DataComponent dataPromise={dataPromise} />
    </Suspense>
  )

  await waitFor(() => {
    expect(screen.getByText('Test')).toBeInTheDocument()
  })
})
```

### React 19 transitions and useTransition

```typescript
it('shows pending state during transition', async () => {
  const user = userEvent.setup()
  render(<FilterableList items={items} />)

  await user.type(screen.getByRole('searchbox'), 'react')

  // Transition may show pending UI
  // The final state should show filtered results
  await waitFor(() => {
    expect(screen.getByText('React Patterns')).toBeInTheDocument()
  })
})
```

### React 19 form actions (useActionState)

```typescript
it('handles form action submission', async () => {
  const user = userEvent.setup()
  render(<ContactForm />)

  await user.type(screen.getByLabelText('Name'), 'Jane Doe')
  await user.type(screen.getByLabelText('Message'), 'Hello')
  await user.click(screen.getByRole('button', { name: 'Send' }))

  // Wait for action to complete
  await waitFor(() => {
    expect(screen.getByText('Message sent!')).toBeInTheDocument()
  })
})

// If testing the action function directly (server action)
it('processes form data', async () => {
  const formData = new FormData()
  formData.append('name', 'Jane Doe')
  formData.append('message', 'Hello')

  const result = await submitContactForm(null, formData)
  expect(result).toEqual({ success: true })
})
```

## Testing Hooks

### renderHook for custom hooks

```typescript
import { renderHook, act } from '@testing-library/react'

it('increments counter', () => {
  const { result } = renderHook(() => useCounter(0))

  expect(result.current.count).toBe(0)

  act(() => {
    result.current.increment()
  })

  expect(result.current.count).toBe(1)
})
```

### Hooks with providers

```typescript
it('reads context value', () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <ThemeProvider theme="dark">{children}</ThemeProvider>
  )

  const { result } = renderHook(() => useTheme(), { wrapper })
  expect(result.current.theme).toBe('dark')
})
```

### Async hooks

```typescript
it('fetches data', async () => {
  mockFetch.mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({ name: 'Test' }),
  })

  const { result } = renderHook(() => useUser('1'))

  // Initial state
  expect(result.current.loading).toBe(true)

  // Wait for fetch to complete
  await waitFor(() => {
    expect(result.current.loading).toBe(false)
  })

  expect(result.current.data).toEqual({ name: 'Test' })
})
```

## Testing Error Boundaries

```typescript
// Suppress console.error for expected errors
const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

it('renders fallback on error', () => {
  const ThrowingComponent = () => {
    throw new Error('Test error')
  }

  render(
    <ErrorBoundary fallback={<div>Something went wrong</div>}>
      <ThrowingComponent />
    </ErrorBoundary>
  )

  expect(screen.getByText('Something went wrong')).toBeInTheDocument()

  consoleSpy.mockRestore()
})
```

## Testing Loading States (Suspense)

```typescript
it('shows loading then content', async () => {
  render(
    <Suspense fallback={<div>Loading...</div>}>
      <AsyncComponent />
    </Suspense>
  )

  // Loading state
  expect(screen.getByText('Loading...')).toBeInTheDocument()

  // Content state
  await waitFor(() => {
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
    expect(screen.getByText('Content loaded')).toBeInTheDocument()
  })
})
```

## Common Assertions

```typescript
// Presence
expect(screen.getByText('Hello')).toBeInTheDocument()
expect(screen.queryByText('Hidden')).not.toBeInTheDocument()

// Visibility
expect(screen.getByText('Visible')).toBeVisible()

// Attributes
expect(screen.getByRole('button')).toBeEnabled()
expect(screen.getByRole('button')).toBeDisabled()
expect(screen.getByRole('link')).toHaveAttribute('href', '/about')

// Form values
expect(screen.getByLabelText('Email')).toHaveValue('test@example.com')
expect(screen.getByRole('checkbox')).toBeChecked()

// CSS classes (use sparingly — prefer behavior-based assertions)
expect(screen.getByText('Error')).toHaveClass('text-red-500')

// Accessible description
expect(screen.getByRole('button')).toHaveAccessibleName('Submit form')
```

## Anti-Patterns to Avoid

1. **Never use `container.innerHTML`** — use `screen` queries
2. **Never use `act()` directly** if `userEvent` or `waitFor` handles it
3. **Never test implementation details** (state values, component instance methods)
4. **Never use `setTimeout` in tests** — use `waitFor` or fake timers
5. **Avoid `getByTestId`** when accessible queries work
6. **Never assert on snapshot alone** — combine with behavior assertions
