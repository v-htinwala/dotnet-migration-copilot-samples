---
name: javascript-typescript-regression-testcase-generation
description: >
  Generates regression test cases for JavaScript and TypeScript codebases. Selects
  existing tests and generates new tests based on change-based, risk-based, and
  coverage-based qualification criteria. Supports npm, yarn, and pnpm workspaces,
  Jest/Vitest, and Istanbul/c8 coverage. Generates both unit-level (mocked) and
  integration-level (supertest, MSW, Testcontainers) regression tests. Supports
  user-supplied test data (fixtures, mock data, golden files), configurable
  business criticality, user-defined regression scenarios with requirement
  traceability, and CI/CD integration with artifact generation, test sharding,
  and flaky test detection. Use when the user asks to generate regression tests,
  select regression test cases, prioritize tests based on code changes, or
  improve regression test coverage for JavaScript or TypeScript projects.
license: Apache-2.0
compatibility: >
  Best with VS Code Copilot or agents supporting the runSubagent tool for parallel
  multi-package processing. Falls back to sequential file-by-file processing on other
  platforms. Requires Python 3.8+ for helper scripts. Node.js 16+ required.
  npm, yarn, or pnpm must be installed.
metadata:
  author: regression-testcase-generation
  version: "1.0"
allowed-tools: Bash(python:*) Bash(npm:*) Bash(npx:*) Bash(yarn:*) Bash(pnpm:*) Bash(git:*) Read
---

# JavaScript/TypeScript Regression Test Case Generation

## When to Use This Skill

Activate this skill when the user wants to:
- Generate regression tests for a JS/TS codebase based on recent code changes
- Select and prioritize existing tests to run for a set of changes
- Identify coverage gaps in changed code and generate tests to fill them
- Assess risk of changed files and focus testing on high-risk areas
- Build a regression test suite for a pull request or release candidate
- Analyze the impact of changes across a monorepo / workspace project

## User Inputs

Before starting, collect the following from the user:

| Input | Required | Default | Description |
|---|---|---|---|
| **Codebase path** | Yes | Current workspace root | JS/TS project root |
| **Change source** | No | `git diff HEAD~1` | Git ref, branch, or manual file list |
| **Impact depth** | No | 2 | Dependency traversal levels |
| **Risk threshold** | No | `medium` | Minimum risk level: `low`/`medium`/`high`/`critical` |
| **Coverage threshold** | No | 80% | Minimum coverage on changed code |
| **Criteria mode** | No | `all` | Which criteria: `change`, `risk`, `coverage`, or `all` |
| **Max tests** | No | unlimited | Cap on total tests to select/generate |
| **Config file** | No | `.regression-config.json` | Path to override config |
| **Test framework** | No | Jest | Auto-detected from package.json (Jest or Vitest) |
| **Test level** | No | `unit` | `unit`, `integration`, or `both`. Controls whether to generate mock-only tests, API/integration tests (supertest, MSW), or both |
| **Test data dir** | No | `__fixtures__` | Path to fixture files (JSON, CSV) for data-driven tests |
| **Expected outputs dir** | No | none | Path to golden/snapshot files for output comparison assertions |
| **Data format** | No | `json` | Format of fixture data: `json`, `csv` |
| **Business criticality map** | No | none | JSON mapping of file/directory glob patterns to criticality levels (overrides path heuristics) |
| **Regression scenarios** | No | none | Path to a YAML file defining user regression scenarios (see Regression Scenarios section) |
| **Requirement IDs** | No | none | Comma-separated ticket/requirement IDs for traceability tags |
| **CI mode** | No | `false` | When `true`, generate CI artifacts (JUnit XML, JSON manifest) in `report_dir` |
| **Report dir** | No | `./regression-reports` | Output directory for CI report artifacts |
| **Report formats** | No | `junit-xml,json` | Artifact formats: `junit-xml`, `json`, `markdown` |
| **Test splitting** | No | `1` | Number of shards for parallel CI execution |
| **Flaky threshold** | No | `2` | Retry count — tests that fail then pass are marked `flaky` |

## Safety Rules — CRITICAL

These rules are **non-negotiable** and must be followed at all times:

1. **NEVER modify, rename, or refactor any existing source file.** Only create
   new files as test files or append new test cases to existing test files.
2. **NEVER alter existing test methods.** When adding to an existing test file,
   only append new test cases — do not change existing ones.
3. **All file writes MUST target test file patterns only.** Valid patterns:
   - `*.test.ts`, `*.test.tsx`, `*.test.js`, `*.test.jsx`
   - `*.spec.ts`, `*.spec.tsx`, `*.spec.js`, `*.spec.jsx`
   - `__tests__/*.ts`, `__tests__/*.js`
4. **Before writing any file**, verify the target path matches a test file pattern.
5. **If a test reveals a bug in the source code**, report it in the final summary
   but do NOT fix it.
6. **After test generation**, run `git diff --name-only` on non-test paths. If
   any source files were modified, flag this as a violation and revert.

## Master Workflow

### For Agents With Subagent Support (VS Code Copilot, Claude Code, etc.)

Use the orchestrator + subagent pattern. See the custom agents in
`.github/agents/` for VS Code, or follow this delegation model:

#### Phase 1: Setup
- Collect user inputs (codebase path, change source, thresholds, test level, CI mode)
- Load `.regression-config.json` if present; merge with user inputs
- Validate codebase path contains JS/TS source files
- Record `git status` for integrity checks later
- Detect package manager (`package-lock.json` → npm, `yarn.lock` → yarn, `pnpm-lock.yaml` → pnpm)
- Detect test framework from `package.json` devDependencies (Jest vs Vitest)
- Detect workspace configuration from `package.json` `workspaces` field or `pnpm-workspace.yaml`
- Scan for user-provided test data directories (fixtures, mock data, expected outputs); validate fixture files exist and index by domain entity
- Load regression scenarios YAML file if provided; validate scenarios reference existing source files
- If `test_level` is `integration` or `both`, verify `supertest` or `msw` is in devDependencies; warn if missing
- Extract `business_criticality.overrides` from config for use in Phase 4

#### Phase 2: Change Detection
- Delegate to **change-analyzer** subagent
- Runs `scripts/analyze-changes.py` with the change source
- Returns `changes.json`: list of changed `.ts`/`.js`/`.tsx`/`.jsx` files with diff stats
- If user provided manual file list, skip git analysis and use that

#### Phase 3: Impact Analysis (Parallel per workspace package)
- **change-analyzer** subagent runs `scripts/build-dependency-graph.py`
- Parses ESM `import` and CJS `require()` statements, resolves `tsconfig.json` path aliases
- Traverses dependents up to `impact_depth` levels
- Returns `impact.json`: changed files + all transitively impacted files
- Runs `scripts/list-existing-tests.py` to map impacted source files to existing test files
- Returns `test-map.json`: source file -> existing test file(s) mapping

#### Phase 4: Risk Scoring (Parallel per workspace package)
- Delegate to **risk-scorer** subagent
- Runs `scripts/calculate-risk-scores.py` for each impacted file
- Pass `--criticality-map` with user-provided business criticality overrides from config
- Computes cyclomatic complexity, change frequency, defect history, business criticality
- User-defined criticality overrides take precedence over path-heuristic defaults
- Returns `risk-scores.json`: per-file risk score + level

#### Phase 5: Test Selection & Prioritization
- Delegate to **test-selector** subagent
- Runs `scripts/select-tests.py` with all JSON manifests + qualification config
- If regression scenarios file is provided, pass `--scenarios` flag to boost priority of scenario-targeted files
- Applies combined scoring formula
- Returns `selected-tests.json`: prioritized list of existing tests to run
- Also returns `coverage-gaps.json`: files/methods needing new tests

#### Phase 6: Gap Test Generation (Parallel, Batched 3-5)
- For each coverage gap, spawn **regression-test-generator** subagent
- Each receives: source file, export summary, gap details, Jest/Vitest reference, test level, matching fixtures, matching regression scenarios, requirement IDs
- For `test_level=unit`: generate mock-based tests (default, same as before)
- For `test_level=integration`: generate supertest/MSW-based API integration tests as appropriate — place in `__tests__/integration/` or colocated with `.integration.test.ts` suffix
- For `test_level=both`: generate separate unit tests (`.test.ts`) and integration tests (`.integration.test.ts`)
- When user-provided fixture files match the target entity, generator uses `fs.readFileSync`/`import` fixture loading instead of inline hardcoded data
- When regression scenarios target this file, generator creates nested `describe` blocks per scenario with descriptive test names matching the scenario narrative
- When requirement IDs are provided, generator adds JSDoc `@requirement REQ-xxx` tags and includes the ID in test descriptions
- Write test files colocated with source or in `__tests__/` directory
- **Safety**: verify all writes target test file patterns only

#### Phase 7: Execution & Verification (Parallel per workspace package)
- Spawn **regression-verifier** subagent per package
- Runs `scripts/run-regression-tests.py` with selected + generated tests
- Jest: `npx jest --testPathPattern` / Vitest: `npx vitest run`
- For `test_level=integration` or `both`: also run integration test files (`.integration.test.{ts,js}`)
- If `test_splitting` > 1, partition selected tests across shards using `--shard-index` and `--total-shards` flags
- Returns test results + Istanbul/c8 coverage on changed code
- **Flaky test detection**: if a test fails then passes on retry, classify as `flaky` (not `passed`). Report flaky tests separately.
- On failures: re-spawn generator with error context (max 3 retries)
- Coverage gate: if changed-code coverage < threshold, generate more tests (max 2 iterations)
- If `ci_mode=true`: generate CI artifacts (JUnit XML, JSON manifest) in `report_dir`

#### Phase 8: Report
- Run `git diff --name-only` — verify zero source file modifications
- Output final summary:
  - Changed files detected
  - Impact analysis: N files impacted across M packages
  - Risk distribution: N critical, N high, N medium, N low
  - Tests selected: N existing tests (prioritized list)
  - Tests generated: N new test files (unit: N, integration: N)
  - Execution results: passed/failed/skipped/flaky
  - Flaky tests: list of tests that failed then passed on retry
  - Coverage on changed code: X% (threshold: Y%)
  - Requirement traceability: N requirements covered, M scenarios tested
  - Source integrity: pass/fail
  - CI artifacts: list of generated report files and paths (when `ci_mode=true`)

### For Agents Without Subagent Support (Sequential Fallback)

Follow the same 8-phase workflow but process everything sequentially:

1. Run `scripts/analyze-changes.py` -> read output
2. Run `scripts/build-dependency-graph.py` -> read output
3. Run `scripts/list-existing-tests.py` -> read output
4. Run `scripts/calculate-risk-scores.py` -> read output
5. Run `scripts/select-tests.py` -> read output
6. For each coverage gap (one at a time):
   a. Read ONLY that source file + its direct dependency interfaces
   b. Load `references/regression-patterns.md`
   c. Generate the complete test file
   d. Write the test file next to the source or in `__tests__/`
   e. **Drop the source file from context** before moving to the next
7. Run `scripts/run-regression-tests.py` -> fix failures (max 3 retries)
8. Run `scripts/check-coverage.py` -> if below threshold, generate more (max 2 iterations)
9. Produce the summary report

**Context management rules for sequential mode:**
- Never load more than 1 source file at a time
- Use JSON manifests for navigation, not raw source
- Complete one package before moving to the next

## User Override Mechanism

Users override defaults in **three ways** (priority order):

1. **Direct input** when invoking the skill (highest priority)
2. **Config file** (`.regression-config.json` in project root)
3. **Built-in defaults** (lowest priority)

## Regression Scenarios & Requirement Traceability

Users can define specific regression scenarios and link tests to requirements/tickets.

### Regression Scenarios File

Provide a YAML file (via `regression_scenarios` input or `.regression-config.json`) defining
critical scenarios that must be tested. See `assets/regression-scenarios.example.yml` for format.

Each scenario specifies:
- **name** — short identifier
- **description** — what behavior must be preserved
- **target_files** — glob patterns matching source files this scenario covers
- **expected_behaviors** — list of assertions in natural language
- **requirement_ids** — linked ticket/requirement IDs
- **priority** — `critical`, `high`, or `medium`

Scenarios boost the priority of targeted files in the selection scoring formula
(configurable boost, default: +20 points). The generator creates nested `describe`
blocks per scenario with descriptive test names matching the scenario narrative.

### Requirement Traceability

When `requirement_ids` are provided (via user input, scenario file, or config):
- Each generated test file gets a JSDoc `@requirement REQ-xxx` tag at the top
- Each `describe`/`it` block includes the requirement ID: `[REQ-xxx]`
- The final report includes a traceability matrix: requirements → test files

## Test File Naming Conventions

| Source File | Unit Test File | Integration Test File |
|---|---|---|
| `userService.ts` | `userService.test.ts` | `userService.integration.test.ts` |
| `OrderController.tsx` | `OrderController.test.tsx` | `OrderController.integration.test.tsx` |
| `utils/helpers.js` | `utils/helpers.test.js` | `utils/helpers.integration.test.js` |
| `src/api/users.ts` | `src/api/__tests__/users.test.ts` | `src/api/__tests__/users.integration.test.ts` |

## Multi-Package Project Handling

### npm/yarn Workspaces
- Parse `package.json` `"workspaces"` field for package glob patterns
- Each workspace package is processed independently
- Tests run per-package: `npx jest --testPathPattern <package>`
- Coverage per-package via Jest `--collectCoverageFrom`
- Process order: packages with fewest dependencies first

### pnpm Workspaces
- Parse `pnpm-workspace.yaml` for package globs
- Tests run per-package using `pnpm --filter <package> test`

## CI/CD Integration

When `ci_mode` is enabled, the skill generates CI-ready artifacts and supports
parallel execution across pipeline workers.

### Report Artifacts

Generated in `report_dir` (default: `./regression-reports/`):

| File | Format | Purpose |
|---|---|---|
| `regression-results.xml` | JUnit XML | CI dashboard integration (GitHub Actions, Azure DevOps) |
| `regression-results.json` | JSON | Machine-readable full results with metadata |
| `regression-summary.md` | Markdown | Human-readable summary for PR comments |

### Test Splitting (Sharding)

For parallel CI execution, partition selected tests across workers:
- Configure via `test_splitting` (total shards) — each CI worker runs with `--shard-index N --total-shards M`
- Tests are partitioned round-robin by priority score (highest-priority tests spread across shards)
- Each shard's output includes `shardInfo` metadata for aggregation
- Jest natively supports `--shard` flag; Vitest supports `--shard`

### Flaky Test Handling

- Tests that fail then pass on retry (up to `flaky_threshold` attempts) are classified as `flaky`
- Flaky tests are reported separately from passed/failed in results
- Optional quarantine: set `flaky_detection.quarantine_flaky=true` in config to exclude known-flaky tests from blocking the pipeline

### Pipeline Examples

#### GitHub Actions
```yaml
jobs:
  regression-tests:
    strategy:
      matrix:
        shard: [0, 1, 2, 3]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - name: Run regression shard
        run: |
          python scripts/run-regression-tests.py . --test-runner jest \
            --ci-mode --report-dir ./regression-reports \
            --shard-index ${{ matrix.shard }} --total-shards 4
      - uses: actions/upload-artifact@v4
        with:
          name: regression-reports-${{ matrix.shard }}
          path: ./regression-reports/
      - uses: dorny/test-reporter@v1
        with:
          name: Regression Tests (Shard ${{ matrix.shard }})
          path: ./regression-reports/regression-results.xml
          reporter: jest-junit
```

#### Azure DevOps
```yaml
jobs:
  - job: RegressionTests
    strategy:
      matrix:
        shard0: { SHARD_INDEX: 0 }
        shard1: { SHARD_INDEX: 1 }
    steps:
      - script: npm ci
      - script: |
          python scripts/run-regression-tests.py . --test-runner jest \
            --ci-mode --report-dir ./regression-reports \
            --shard-index $(SHARD_INDEX) --total-shards 2
      - task: PublishTestResults@2
        inputs:
          testResultsFormat: JUnit
          testResultsFiles: ./regression-reports/regression-results.xml
          testRunTitle: Regression Tests (Shard $(SHARD_INDEX))
```

## Scripts Reference

All scripts are in the `scripts/` directory. Run with Python 3.8+.

| Script | Purpose | Key Input | Output |
|---|---|---|---|
| `analyze-changes.py` | Parse git diff for changed JS/TS files | `<codebase> [--ref HEAD~1]` | `changes.json` |
| `build-dependency-graph.py` | Build ESM/CJS import dependency graph | `<codebase> --depth <N>` | `impact.json` |
| `calculate-risk-scores.py` | Compute risk per JS/TS file | `<files-json> --window 90 [--criticality-map <json>]` | `risk-scores.json` |
| `list-existing-tests.py` | Map JS/TS source files to test files | `<module-path>` | `test-map.json` (includes `testType: unit&#124;integration`) |
| `select-tests.py` | Apply criteria, rank, select | `--changes <json> --risks <json> [--scenarios <yaml>] [--shard-index N --total-shards M]` | `selected-tests.json` |
| `run-regression-tests.py` | Execute selected tests via Jest/Vitest | `<module> --test-runner <type> [--ci-mode] [--include-integration] [--shard-index N --total-shards M] [--flaky-threshold N]` | `results.json` |
| `check-coverage.py` | Istanbul/lcov coverage gaps on changed code | `<report> --threshold <N>` | `coverage-gaps.json` |

## Language-Specific Reference

Load the JS/TS regression patterns reference when generating tests:

- [JavaScript/TypeScript Regression Patterns](references/regression-patterns.md)
- [Qualification Criteria](references/qualification-criteria.md)

## Test Templates

Skeleton templates are available in `assets/test-templates/`. Use them as a
starting point and fill in the specific test logic based on the source code analysis.
