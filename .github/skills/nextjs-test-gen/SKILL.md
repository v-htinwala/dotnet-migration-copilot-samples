---
name: nextjs-test-gen
description: >
  Generate comprehensive unit tests for Next.js 16 and React 19 codebases.
  Auto-detects Vitest or Jest, App Router or Pages Router, and produces
  co-located test files with full mocking of Next.js internals. Covers React
  Server Components, Client Components, Server Actions, API Route Handlers,
  custom hooks, and utility modules. Use when the user needs unit tests,
  test generation, code coverage improvement, React Testing Library tests,
  Vitest tests, Jest tests, component tests, hook tests, or test scaffolding
  for a Next.js or React project.
license: Proprietary
compatibility: >
  Requires Node.js 18+. Works with Vitest or Jest. Expects a Next.js 13+
  project with either App Router (app/) or Pages Router (pages/).
metadata:
  author: specification-project
  version: "1.0"
---

# Next.js / React Unit Test Generator

Generate high-quality unit tests for Next.js 16 / React 19 projects with
automatic framework detection, comprehensive mocking, and coverage-driven
gap filling.


## SOURCE CODE PROTECTION -- HARD RULE

**All agents using this skill must ONLY create or modify test files.** Source/production code files must NEVER be modified, edited, or created.

- Only write files under test directories (`src/test/`, `tests/`, `__tests__/`, or matching `*.test.*`/`*.spec.*`/`*Tests.*` patterns)
- NEVER modify files under `src/main/` (Java), `src/` non-test directories (JS/TS), or the main project source directory (.NET)
- If the source code has compilation errors or bugs, report the issue and skip the file -- do not attempt to fix source code
- This rule is absolute and non-negotiable -- no exceptions for "obvious bugs", "typos", or "quick fixes"

## Workflow

### Step 1: Framework Detection

Determine the test runner from project configuration:

**Vitest detection** (check in order):
1. `vitest` in `package.json` → `devDependencies` or `dependencies`
2. `vitest.config.ts`, `vitest.config.js`, `vitest.config.mts` exists
3. `"test": "vitest"` in `package.json` → `scripts`
4. `vitest` section in `vite.config.ts`

**Jest detection** (check in order):
1. `jest` in `package.json` → `devDependencies`
2. `jest.config.ts`, `jest.config.js`, `jest.config.mjs` exists
3. `"test": "jest"` or `"test": "next jest"` in `package.json` → `scripts`
4. `"jest"` key in `package.json`

**If both present**: prefer Vitest (faster, better ESM support with Next.js 16).
**If neither present**: default to Vitest and note that setup is needed.

### Step 2: Router Detection

**App Router indicators**:
- `app/` directory exists with `layout.tsx` or `page.tsx`
- `app/` contains `loading.tsx`, `error.tsx`, `not-found.tsx`
- `app/**/route.ts` (API route handlers)

**Pages Router indicators**:
- `pages/` directory exists with `_app.tsx` or `_document.tsx`
- `pages/api/` directory exists
- `getServerSideProps`, `getStaticProps` exports in page files

**If both exist**: scan both, classify files by which router they belong to.

### Step 3: File Classification

Scan source files and classify each into a testing category:

| Category | Detection Rule | Test Pattern |
|----------|---------------|-------------|
| React Server Component (RSC) | In `app/`, no `'use client'`, often async function component | Test as async function, mock `fetch`/DB calls, assert returned JSX structure |
| Client Component | Has `'use client'` directive at top | Render with RTL, test interactivity, mock hooks |
| Server Action | Has `'use server'` directive, or function with `'use server'` inside | Test as async function, mock DB/API, assert return values and `revalidatePath`/`revalidateTag` calls |
| API Route Handler | `app/**/route.ts` exporting `GET`/`POST`/etc, or `pages/api/**` | Test handler functions directly, mock `NextRequest`/`NextResponse`, assert status codes and JSON responses |
| Custom Hook | Filename `use*.ts(x)`, exports function starting with `use` | Test with `renderHook` from RTL, test state changes and effects |
| Utility / Service | Everything else: helpers, formatters, validators, API clients, services | Test as pure functions, mock external dependencies |
| Middleware | `middleware.ts` at project root | Test with mock `NextRequest`, assert redirects/rewrites/headers |
| Configuration | `next.config.*`, `tailwind.config.*` | Skip — not unit-testable |

### Step 4: Test Generation Patterns

For each file category, follow the patterns below. Adapt import syntax
based on detected framework (Vitest vs Jest).

**Import header (Vitest)**:
```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
```

**Import header (Jest)**:
```typescript
// Jest globals are auto-available
```

**Common structure for all tests**:
```typescript
describe('[ModuleName]', () => {
  beforeEach(() => {
    // Reset mocks
  })

  describe('rendering', () => {
    // Component render tests
  })

  describe('interactions', () => {
    // User interaction tests
  })

  describe('edge cases', () => {
    // Null, undefined, empty, error states
  })
})
```

For detailed patterns per category, see the reference files:
- [Vitest patterns](references/vitest-patterns.md)
- [Jest patterns](references/jest-patterns.md)
- [React Testing Library patterns](references/react-testing-patterns.md)
- [Next.js mocking guide](references/nextjs-mocking-guide.md)
- [Server component testing](references/server-component-testing.md)

### Step 5: Naming and Placement

**Detect project convention** by checking for existing test files:
1. Co-located: `src/components/Button.tsx` → `src/components/Button.test.tsx`
2. `__tests__` directory: `src/components/__tests__/Button.test.tsx`
3. Top-level `tests/`: `tests/components/Button.test.tsx`

**If no existing tests**: default to co-located (`*.test.ts(x)` next to source).

**File extension rules**:
- Source has `.tsx` (JSX) → test is `.test.tsx`
- Source has `.ts` (no JSX) → test is `.test.ts`
- Test file imports `render`/`screen` → must be `.test.tsx`

### Step 6: Custom Instructions Resolution

Check for custom instructions in priority order:

1. **User runtime prompt** — inline instructions in the chat message
2. **Module-specific instructions** — `.github/test-gen-instructions/{module-name}.md`
3. **File-type instructions** — `.github/test-gen-instructions/components.md`, `api-routes.md`, etc.
4. **Global instructions** — `.github/test-gen-instructions/global.md`
5. **SKILL.md defaults** — patterns defined in this file and references

Higher priority overrides lower when they conflict. For example, if `global.md`
says "use `@testing-library/react`" but the user prompt says "use `@company/test-utils`",
the user prompt wins.

### Step 7: Coverage Strategy

**Metrics to track** (all four, threshold applies to each independently):
- Statements
- Branches (most commonly missed — prioritize)
- Functions
- Lines

**Coverage gap analysis**:
1. Run full suite with coverage
2. Parse per-file coverage
3. For files below threshold, extract uncovered line ranges
4. Map uncovered lines to functions/branches for targeted test generation
5. Prioritize files with the largest absolute gap (not relative)

**Gap-filling strategy**:
- Focus on uncovered **branches** first (if/else, switch, ternary, optional chaining)
- Then uncovered **functions** (dead code check — if truly unused, skip)
- Then remaining **lines** (usually error handling paths)

### Step 8: Verification Checklist

After generating tests, verify each file passes these structural checks:

- [ ] No empty test bodies (`it('...', () => {})` with no assertions)
- [ ] No tautological assertions (`expect(true).toBe(true)`, `expect(1).toBe(1)`)
- [ ] Every test has at least one `expect()` or `assert` call
- [ ] Mocks that are created are also verified (`toHaveBeenCalled`, `toHaveBeenCalledWith`)
- [ ] Components that are rendered have at least one `screen.*` assertion
- [ ] Async tests use `await`, `waitFor`, or return a Promise
- [ ] Edge cases are covered: null/undefined inputs, empty arrays, error throws
- [ ] Custom instruction compliance: correct imports, correct wrapper components, correct mock patterns
- [ ] No `it.skip`, `xit`, `xdescribe` unless explicitly allowed in instructions
- [ ] No `console.error` or `console.warn` expected during test execution
