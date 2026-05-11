# Vitest Patterns for Next.js 16 / React 19

## Setup

### vitest.config.ts

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
    include: ['**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'text-summary', 'json', 'json-summary', 'lcov'],
      include: ['src/**/*.{ts,tsx}', 'app/**/*.{ts,tsx}'],
      exclude: [
        'node_modules/',
        '**/*.test.{ts,tsx}',
        '**/*.stories.{ts,tsx}',
        '**/*.d.ts',
        '**/types/**',
        'next.config.*',
        'vitest.config.*',
      ],
      thresholds: {
        statements: 85,
        branches: 85,
        functions: 85,
        lines: 85,
      },
    },
    css: { modules: { classNameStrategy: 'non-scoped' } },
  },
})
```

### vitest.setup.ts

```typescript
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

afterEach(() => {
  cleanup()
})
```

## Mocking APIs

### vi.mock — Module mocking

```typescript
// Mock an entire module
vi.mock('@/lib/api', () => ({
  fetchUser: vi.fn(),
  fetchPosts: vi.fn(),
}))

// Mock with partial implementation
vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>()
  return {
    ...actual,
    fetchUser: vi.fn(),
  }
})

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  })),
  usePathname: vi.fn(() => '/'),
  useSearchParams: vi.fn(() => new URLSearchParams()),
  useParams: vi.fn(() => ({})),
  redirect: vi.fn(),
  notFound: vi.fn(),
}))
```

### vi.fn — Function mocking

```typescript
const mockFn = vi.fn()

// With implementation
const mockFn = vi.fn((x: number) => x * 2)

// With resolved value (for async)
const mockFn = vi.fn().mockResolvedValue({ data: 'test' })

// With rejected value
const mockFn = vi.fn().mockRejectedValue(new Error('fail'))

// Chain implementations for sequential calls
const mockFn = vi.fn()
  .mockResolvedValueOnce({ data: 'first' })
  .mockResolvedValueOnce({ data: 'second' })
  .mockRejectedValueOnce(new Error('third call fails'))
```

### vi.spyOn — Spy on existing methods

```typescript
import * as utils from '@/utils/format'

const spy = vi.spyOn(utils, 'formatCurrency')
spy.mockReturnValue('$10.00')

// After test
expect(spy).toHaveBeenCalledWith(1000, 'USD')
spy.mockRestore()
```

### Mock reset patterns

```typescript
beforeEach(() => {
  vi.clearAllMocks()   // Clear call history and results
  // OR
  vi.resetAllMocks()   // Clear + remove implementations
  // OR
  vi.restoreAllMocks() // Restore original implementations (for spyOn)
})
```

### Mocking fetch

```typescript
// Global fetch mock
const mockFetch = vi.fn()
global.fetch = mockFetch

beforeEach(() => {
  mockFetch.mockReset()
})

// Mock a successful JSON response
mockFetch.mockResolvedValue({
  ok: true,
  status: 200,
  json: () => Promise.resolve({ id: 1, name: 'Test' }),
  text: () => Promise.resolve('OK'),
  headers: new Headers({ 'content-type': 'application/json' }),
})

// Mock a failed response
mockFetch.mockResolvedValue({
  ok: false,
  status: 404,
  json: () => Promise.resolve({ error: 'Not found' }),
  statusText: 'Not Found',
})

// Mock a network error
mockFetch.mockRejectedValue(new TypeError('Failed to fetch'))
```

### Timer mocking

```typescript
beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

it('debounces input', async () => {
  // ... trigger debounced action
  vi.advanceTimersByTime(300)
  // ... assert
})
```

## Coverage Commands

```bash
# Run tests with coverage
npx vitest run --coverage

# Run specific files with coverage
npx vitest run --coverage src/auth/

# Run with specific reporter
npx vitest run --coverage --reporter=verbose

# Watch mode (no coverage — use for development)
npx vitest --reporter=verbose
```

## Environment Variables

```typescript
// In test file
beforeEach(() => {
  vi.stubEnv('NEXT_PUBLIC_API_URL', 'http://localhost:3000')
  vi.stubEnv('DATABASE_URL', 'postgres://test')
})

afterEach(() => {
  vi.unstubAllEnvs()
})
```

## Snapshot Testing

```typescript
import { render } from '@testing-library/react'

it('matches snapshot', () => {
  const { container } = render(<MyComponent />)
  expect(container).toMatchSnapshot()
})

// Inline snapshots (preferred — self-documenting)
it('renders title', () => {
  const { getByRole } = render(<MyComponent title="Hello" />)
  expect(getByRole('heading')).toMatchInlineSnapshot(`
    <h1>Hello</h1>
  `)
})
```
