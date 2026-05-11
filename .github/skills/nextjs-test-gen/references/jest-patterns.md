# Jest Patterns for Next.js 16 / React 19

## Setup

### jest.config.ts (using next/jest)

```typescript
import type { Config } from 'jest'
import nextJest from 'next/jest'

const createJestConfig = nextJest({
  dir: './',
})

const config: Config = {
  testEnvironment: 'jsdom',
  setupFilesAfterSetup: ['<rootDir>/jest.setup.ts'],
  testMatch: ['**/*.test.{ts,tsx}'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    'app/**/*.{ts,tsx}',
    '!**/*.test.{ts,tsx}',
    '!**/*.stories.{ts,tsx}',
    '!**/*.d.ts',
    '!**/types/**',
    '!next.config.*',
  ],
  coverageThreshold: {
    global: {
      statements: 85,
      branches: 85,
      functions: 85,
      lines: 85,
    },
  },
  coverageReporters: ['text', 'text-summary', 'json', 'json-summary', 'lcov'],
}

export default createJestConfig(config)
```

### jest.setup.ts

```typescript
import '@testing-library/jest-dom'
```

## Mocking APIs

### jest.mock — Module mocking

```typescript
// Mock an entire module
jest.mock('@/lib/api', () => ({
  fetchUser: jest.fn(),
  fetchPosts: jest.fn(),
}))

// Mock with partial implementation
jest.mock('@/lib/api', () => {
  const actual = jest.requireActual('@/lib/api')
  return {
    ...actual,
    fetchUser: jest.fn(),
  }
})

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
  })),
  usePathname: jest.fn(() => '/'),
  useSearchParams: jest.fn(() => new URLSearchParams()),
  useParams: jest.fn(() => ({})),
  redirect: jest.fn(),
  notFound: jest.fn(),
}))
```

### jest.fn — Function mocking

```typescript
const mockFn = jest.fn()

// With implementation
const mockFn = jest.fn((x: number) => x * 2)

// With resolved value (for async)
const mockFn = jest.fn().mockResolvedValue({ data: 'test' })

// With rejected value
const mockFn = jest.fn().mockRejectedValue(new Error('fail'))

// Chain implementations for sequential calls
const mockFn = jest.fn()
  .mockResolvedValueOnce({ data: 'first' })
  .mockResolvedValueOnce({ data: 'second' })
  .mockRejectedValueOnce(new Error('third call fails'))
```

### jest.spyOn — Spy on existing methods

```typescript
import * as utils from '@/utils/format'

const spy = jest.spyOn(utils, 'formatCurrency')
spy.mockReturnValue('$10.00')

// After test
expect(spy).toHaveBeenCalledWith(1000, 'USD')
spy.mockRestore()
```

### Mock reset patterns

```typescript
beforeEach(() => {
  jest.clearAllMocks()   // Clear call history and results
  // OR
  jest.resetAllMocks()   // Clear + remove implementations
  // OR
  jest.restoreAllMocks() // Restore original implementations (for spyOn)
})
```

### Mocking fetch

```typescript
// Global fetch mock
const mockFetch = jest.fn() as jest.MockedFunction<typeof fetch>
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
} as Response)

// Mock a failed response
mockFetch.mockResolvedValue({
  ok: false,
  status: 404,
  json: () => Promise.resolve({ error: 'Not found' }),
  statusText: 'Not Found',
} as Response)

// Mock a network error
mockFetch.mockRejectedValue(new TypeError('Failed to fetch'))
```

### Timer mocking

```typescript
beforeEach(() => {
  jest.useFakeTimers()
})

afterEach(() => {
  jest.useRealTimers()
})

it('debounces input', async () => {
  // ... trigger debounced action
  jest.advanceTimersByTime(300)
  // ... assert
})
```

## Jest-Specific Considerations for Next.js 16

### SWC Transform

Next.js uses SWC for compilation. The `next/jest` preset handles this
automatically. Do NOT add `ts-jest` or `babel-jest` — they conflict.

### Module Resolution

If using `@/` path aliases, ensure `moduleNameMapper` in jest config matches
`tsconfig.json` → `paths`. The `next/jest` preset reads `tsconfig.json`
automatically in most cases.

### ESM Modules

If you encounter ESM-related errors, add `transformIgnorePatterns`:

```typescript
const config: Config = {
  transformIgnorePatterns: [
    'node_modules/(?!(some-esm-package|another-package)/)',
  ],
}
```

## Coverage Commands

```bash
# Run tests with coverage
npx jest --coverage

# Run specific files with coverage
npx jest --coverage src/auth/

# Run with verbose output
npx jest --coverage --verbose

# Watch mode (development)
npx jest --watch
```

## Environment Variables

```typescript
// In jest.setup.ts or individual test files
const originalEnv = process.env

beforeEach(() => {
  process.env = {
    ...originalEnv,
    NEXT_PUBLIC_API_URL: 'http://localhost:3000',
    DATABASE_URL: 'postgres://test',
  }
})

afterEach(() => {
  process.env = originalEnv
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
