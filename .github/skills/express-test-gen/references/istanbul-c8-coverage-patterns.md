# Istanbul / c8 Coverage Patterns for Express.js

Setup, configuration, and report parsing for Istanbul (nyc) and c8 coverage.

## Jest Coverage (Istanbul Built-in)

### jest.config.ts Coverage Settings

```typescript
const config: Config = {
  collectCoverageFrom: [
    'src/**/*.{ts,js}',
    '!src/**/*.test.{ts,js}',
    '!src/**/*.d.ts',
    '!src/types/**',
    '!src/server.ts',
    '!src/**/__mocks__/**',
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'text-summary', 'json', 'json-summary', 'lcov'],
  coverageThreshold: {
    global: {
      statements: 85,
      branches: 85,
      functions: 85,
      lines: 85,
    },
  },
};
```

### Running

```bash
# Run with coverage
npx jest --coverage

# Run specific files with coverage
npx jest --coverage --testPathPattern="services"

# Run with CI-friendly output
npx jest --coverage --ci --coverageReporters=text-summary,json-summary
```

## nyc (Istanbul CLI) — for Mocha

### .nycrc.json

```json
{
  "extends": "@istanbuljs/nyc-config-typescript",
  "all": true,
  "include": ["src/**/*.ts"],
  "exclude": [
    "src/**/*.test.ts",
    "src/**/*.spec.ts",
    "src/types/**",
    "src/server.ts"
  ],
  "reporter": ["text", "text-summary", "json", "json-summary", "lcov", "html"],
  "report-dir": "coverage",
  "check-coverage": true,
  "branches": 85,
  "lines": 85,
  "functions": 85,
  "statements": 85,
  "temp-dir": ".nyc_output"
}
```

### Running

```bash
# Run with nyc
npx nyc mocha

# With TypeScript
npx nyc --require ts-node/register mocha

# Check thresholds (fails if below)
npx nyc check-coverage

# Report only (after a previous run)
npx nyc report --reporter=text
```

## c8 — for Mocha/Vitest (V8 Native Coverage)

### Configuration (package.json)

```json
{
  "c8": {
    "all": true,
    "include": ["src/**/*.ts"],
    "exclude": ["src/**/*.test.ts", "src/types/**", "src/server.ts"],
    "reporter": ["text", "text-summary", "json", "json-summary", "lcov"],
    "report-dir": "coverage",
    "check-coverage": true,
    "branches": 85,
    "lines": 85,
    "functions": 85,
    "statements": 85
  }
}
```

### Running

```bash
# Run with c8
npx c8 mocha

# With TypeScript
npx c8 ts-mocha -p tsconfig.json "src/**/*.test.ts"

# Check thresholds
npx c8 check-coverage

# Vitest (c8 built-in as provider)
npx vitest run --coverage
```

## Report Locations

| Tool | Default Path |
|------|-------------|
| Jest | `coverage/` |
| nyc | `coverage/` (configurable via `.nycrc`) |
| c8 | `coverage/` (configurable) |
| Vitest | `coverage/` |

### Key Report Files

| File | Purpose |
|------|---------|
| `coverage-summary.json` | Per-file metrics summary |
| `coverage-final.json` | Detailed per-file coverage with line/branch maps |
| `lcov.info` | LCOV format for CI tools |
| `index.html` | HTML report for browsing |

## Parsing coverage-summary.json

```json
{
  "total": {
    "lines": { "total": 500, "covered": 425, "skipped": 0, "pct": 85 },
    "statements": { "total": 600, "covered": 510, "skipped": 0, "pct": 85 },
    "functions": { "total": 120, "covered": 102, "skipped": 0, "pct": 85 },
    "branches": { "total": 200, "covered": 150, "skipped": 0, "pct": 75 }
  },
  "src/services/user.service.ts": {
    "lines": { "total": 50, "covered": 45, "skipped": 0, "pct": 90 },
    "statements": { "total": 60, "covered": 54, "skipped": 0, "pct": 90 },
    "functions": { "total": 10, "covered": 9, "skipped": 0, "pct": 90 },
    "branches": { "total": 20, "covered": 12, "skipped": 0, "pct": 60 }
  }
}
```

## Parsing coverage-final.json (Detailed)

```json
{
  "src/services/user.service.ts": {
    "path": "src/services/user.service.ts",
    "statementMap": {
      "0": { "start": { "line": 10, "column": 0 }, "end": { "line": 10, "column": 45 } }
    },
    "s": { "0": 5, "1": 5, "2": 0, "3": 0 },
    "branchMap": {
      "0": {
        "loc": { "start": { "line": 15, "column": 4 }, "end": { "line": 19, "column": 5 } },
        "type": "if",
        "locations": [
          { "start": { "line": 15, "column": 4 }, "end": { "line": 17, "column": 5 } },
          { "start": { "line": 17, "column": 11 }, "end": { "line": 19, "column": 5 } }
        ]
      }
    },
    "b": { "0": [5, 0] },
    "fnMap": {
      "0": {
        "name": "getUsers",
        "decl": { "start": { "line": 10, "column": 2 }, "end": { "line": 10, "column": 10 } },
        "loc": { "start": { "line": 10, "column": 15 }, "end": { "line": 25, "column": 3 } }
      }
    },
    "f": { "0": 5, "1": 0 }
  }
}
```

### Key Fields

- `s` — statement hit counts (key = statementMap index)
- `b` — branch hit counts (array; each element = arm hit count)
- `f` — function hit counts (key = fnMap index)
- `statementMap` / `branchMap` / `fnMap` — source location mappings

### Identifying Uncovered Code

- **Uncovered statements**: `s[key] === 0`
- **Uncovered branches**: `b[key]` contains a `0`
- **Uncovered functions**: `f[key] === 0`

## Identifying Gap Files

### Algorithm

1. Parse `coverage-summary.json` for per-file metrics
2. Filter files where any metric < threshold
3. Sort by uncovered statement count descending (highest impact)
4. For top N files, parse `coverage-final.json` for line-level detail
5. Map uncovered lines to functions using `fnMap`
6. Generate gap data for the generator subagent

### Example Gap Output

```json
{
  "filePath": "src/services/user.service.ts",
  "currentCoverage": {
    "statements": 90.0,
    "branches": 60.0,
    "functions": 90.0,
    "lines": 90.0
  },
  "uncoveredRanges": [
    {
      "type": "branch",
      "location": { "startLine": 15, "endLine": 19 },
      "description": "else branch in getUsers — error handling path",
      "functionName": "getUsers"
    },
    {
      "type": "function",
      "location": { "startLine": 30, "endLine": 45 },
      "description": "deleteUser — entirely uncovered",
      "functionName": "deleteUser"
    }
  ]
}
```

## Exclusions

### Inline Exclusion (Istanbul Hints)

```typescript
/* istanbul ignore next */
function debugHelper() {
  console.log('debug');
}

/* istanbul ignore if */
if (process.env.NODE_ENV === 'development') {
  enableDebugMode();
}

/* istanbul ignore else */
if (condition) {
  doSomething();
} else {
  // Excluded from coverage
}

// For c8, use v8 ignore comments:
/* c8 ignore next */
function debugOnly() {}

/* c8 ignore start */
function entireBlock() {}
/* c8 ignore stop */
```

### File-level Exclusion

In nyc/c8/jest config (see setup sections above), use `exclude` patterns:
```
"exclude": [
  "src/**/*.test.ts",
  "src/types/**",
  "src/server.ts",
  "src/config/**",
  "src/**/*.d.ts"
]
```

## Metrics Mapping

Istanbul/c8 metrics align directly with the orchestrator's expectations:

| Istanbul/c8 Metric | Meaning | Orchestrator Metric |
|---------------------|---------|---------------------|
| Statements | Individual executable statements | Statements |
| Branches | Decision point arms (if/else, switch, ternary, ??) | Branches |
| Functions | Function/method entry points | Functions |
| Lines | Source code lines | Lines |

**Threshold guidance**: For the orchestrator's default 85% target, apply to all four metrics independently.
