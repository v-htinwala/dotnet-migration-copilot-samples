# Istanbul Coverage Patterns for Angular

Setup, configuration, and report parsing for Istanbul/Karma code coverage in Angular.

## Karma / Istanbul Setup

### angular.json — Test Architect Configuration

```json
{
  "projects": {
    "my-app": {
      "architect": {
        "test": {
          "builder": "@angular-devkit/build-angular:karma",
          "options": {
            "codeCoverage": true,
            "codeCoverageExclude": [
              "src/test.ts",
              "src/**/*.spec.ts",
              "src/**/*.mock.ts",
              "src/environments/**",
              "src/app/**/*.module.ts",
              "src/app/**/index.ts"
            ]
          }
        }
      }
    }
  }
}
```

### karma.conf.js — Coverage Reporter

```javascript
module.exports = function (config) {
  config.set({
    coverageReporter: {
      dir: require('path').join(__dirname, './coverage/my-app'),
      subdir: '.',
      reporters: [
        { type: 'html' },
        { type: 'text-summary' },
        { type: 'lcov' },
        { type: 'json-summary' },
        { type: 'json' },
      ],
      check: {
        global: {
          statements: 85,
          branches: 85,
          functions: 85,
          lines: 85,
        },
      },
    },
  });
};
```

## Running with Coverage

```bash
# Run tests with coverage
ng test --code-coverage --watch=false --browsers=ChromeHeadless

# Specific project in multi-project workspace
ng test my-app --code-coverage --watch=false --browsers=ChromeHeadless

# With Jest
npx jest --coverage --ci

# With custom output directory
ng test --code-coverage --watch=false --browsers=ChromeHeadless \
  --code-coverage-exclude="src/**/*.mock.ts"
```

## Report Locations

| Format | Path |
|--------|------|
| HTML | `coverage/my-app/index.html` |
| LCOV | `coverage/my-app/lcov.info` |
| JSON Summary | `coverage/my-app/coverage-summary.json` |
| JSON Detail | `coverage/my-app/coverage-final.json` |

## Parsing JSON Summary Report

### coverage-summary.json Structure

```json
{
  "total": {
    "lines": { "total": 500, "covered": 425, "skipped": 0, "pct": 85 },
    "statements": { "total": 600, "covered": 510, "skipped": 0, "pct": 85 },
    "functions": { "total": 120, "covered": 102, "skipped": 0, "pct": 85 },
    "branches": { "total": 200, "covered": 150, "skipped": 0, "pct": 75 }
  },
  "src/app/services/user.service.ts": {
    "lines": { "total": 50, "covered": 45, "skipped": 0, "pct": 90 },
    "statements": { "total": 60, "covered": 54, "skipped": 0, "pct": 90 },
    "functions": { "total": 10, "covered": 9, "skipped": 0, "pct": 90 },
    "branches": { "total": 20, "covered": 12, "skipped": 0, "pct": 60 }
  }
}
```

## Parsing coverage-final.json (Detailed)

### Structure

```json
{
  "src/app/services/user.service.ts": {
    "path": "src/app/services/user.service.ts",
    "statementMap": {
      "0": { "start": { "line": 10, "column": 0 }, "end": { "line": 10, "column": 45 } },
      "1": { "start": { "line": 12, "column": 4 }, "end": { "line": 12, "column": 30 } }
    },
    "s": {
      "0": 5,
      "1": 5,
      "2": 0,
      "3": 0
    },
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
    "b": {
      "0": [5, 0]
    },
    "fnMap": {
      "0": {
        "name": "getUsers",
        "decl": { "start": { "line": 10, "column": 2 }, "end": { "line": 10, "column": 10 } },
        "loc": { "start": { "line": 10, "column": 15 }, "end": { "line": 25, "column": 3 } }
      }
    },
    "f": {
      "0": 5,
      "1": 0
    }
  }
}
```

### Key Fields

- `s` — statement hit counts (key = statementMap index, value = execution count)
- `b` — branch hit counts (array per branch; each element = arm execution count)
- `f` — function hit counts (key = fnMap index, value = execution count)
- `statementMap` — maps statement indices to source locations
- `branchMap` — maps branch indices to source locations with arm locations
- `fnMap` — maps function indices to name and source location

### Identifying Uncovered Code

- **Uncovered statements**: `s[key] === 0`
- **Uncovered branches**: `b[key]` contains a `0` (specific arm not taken)
- **Uncovered functions**: `f[key] === 0`

Map each `0`-count entry back to source location via the corresponding `*Map`.

## Parsing LCOV Report

### lcov.info Structure

```
TN:
SF:src/app/services/user.service.ts
FN:10,getUsers
FN:30,createUser
FNDA:5,getUsers
FNDA:0,createUser
FNF:2
FNH:1
DA:10,5
DA:11,5
DA:15,5
DA:16,5
DA:17,0
DA:30,0
DA:31,0
LF:7
LH:4
BRF:4
BRH:2
BRDA:15,0,0,5
BRDA:15,0,1,0
end_of_record
```

### Key LCOV Fields

| Field | Meaning |
|-------|---------|
| `SF:` | Source file path |
| `FN:line,name` | Function declaration |
| `FNDA:count,name` | Function execution count |
| `DA:line,count` | Line execution count |
| `BRDA:line,block,branch,count` | Branch execution count |
| `LF:` | Lines found (total) |
| `LH:` | Lines hit (covered) |
| `FNF:` | Functions found |
| `FNH:` | Functions hit |
| `BRF:` | Branches found |
| `BRH:` | Branches hit |

### Identifying Gaps from LCOV

- Lines with `DA:line,0` = uncovered lines
- Functions with `FNDA:0,name` = uncovered functions
- Branches with `BRDA:line,block,branch,0` = uncovered branch arms

## Identifying Gap Files

### Algorithm

1. Parse `coverage-summary.json` for per-file metrics
2. Filter files where any metric < threshold
3. Sort by uncovered statement count descending (highest impact first)
4. For top N files, parse `coverage-final.json` for line-level detail
5. Map uncovered lines to functions using `fnMap`
6. Generate gap data for the generator subagent

### Example Gap Output

```json
{
  "filePath": "src/app/services/user.service.ts",
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
      "description": "createUser — entirely uncovered",
      "functionName": "createUser"
    }
  ]
}
```

## Exclusions

### File-level exclusion

In `angular.json` → `codeCoverageExclude`:
```json
"codeCoverageExclude": [
  "src/**/*.spec.ts",
  "src/**/*.mock.ts",
  "src/**/*.module.ts",
  "src/**/index.ts",
  "src/environments/**",
  "src/test.ts"
]
```

### Code-level exclusion (Istanbul hints)

```typescript
/* istanbul ignore next */
function debugOnly() {
  console.log('debug');
}

/* istanbul ignore if */
if (process.env['NODE_ENV'] === 'development') {
  enableDevTools();
}

/* istanbul ignore else */
if (condition) {
  doSomething();
} else {
  // This branch excluded from coverage
}
```

## Metrics Mapping

Istanbul metrics align with the orchestrator's expectations:

| Istanbul Metric | Meaning | Orchestrator Metric |
|-----------------|---------|---------------------|
| Statements | Individual executable statements | Statements |
| Branches | Decision point arms (if/else, switch, ternary) | Branches |
| Functions | Function/method entry points | Functions |
| Lines | Source code lines | Lines |

**Threshold guidance**: For the orchestrator's default 85% target, apply to all four metrics independently.
