---
name: react-playwright-regression-testcase-generation
description: >
  Generates Playwright end-to-end regression test cases for React codebases.
  Selects existing tests and generates new tests based on change-based,
  risk-based, and coverage-based qualification criteria. Supports React
  projects with Playwright Test (auto-detected from package.json / playwright.config.*).
  Generates both page-level (navigation, page.locator, expect) and
  component-level (mount, component testing) regression tests. Supports
  Next.js App Router detection for special handling. Supports user-supplied
  test data (fixtures, JSON seeds), configurable business criticality,
  user-defined regression scenarios with requirement traceability, and CI/CD
  integration with artifact generation, test sharding, and flaky test detection.
  Use when the user asks to generate Playwright regression tests, select
  Playwright regression test cases, prioritize E2E tests based on code changes,
  or improve Playwright regression test coverage for React projects.
license: Apache-2.0
compatibility: >
  Best with VS Code Copilot or agents supporting the runSubagent tool for
  parallel processing. Falls back to sequential file-by-file processing on
  other platforms. Requires Python 3.8+ for helper scripts.
  Node.js 16+ and React 17+ must be installed. Playwright Test must be
  installed (`@playwright/test`). Run `npx playwright install` to install
  browser binaries.
metadata:
  author: regression-testcase-generation
  version: "1.0"
allowed-tools: Bash(python:*) Bash(npx:*) Bash(npm:*) Bash(yarn:*) Bash(pnpm:*) Bash(git:*) Read
---

# React Playwright Regression Test Case Generation

## When to Use This Skill

Activate this skill when the user wants to:
- Generate Playwright end-to-end regression tests for a React codebase based on recent code changes
- Select and prioritize existing Playwright tests to run for a set of changes
- Identify coverage gaps in changed code and generate Playwright tests to fill them
- Assess risk of changed files and focus E2E testing on high-risk areas
- Build a Playwright regression test suite for a pull request or release candidate
- Analyze the impact of changes across a React project and create browser-based regression tests
- Generate Playwright component tests for isolated component regression testing

## User Inputs

Before starting, collect the following from the user:

| Input | Required | Default | Description |
|---|---|---|---|
| **Codebase path** | Yes | Current workspace root | React project root (must contain `package.json`) |
| **Change source** | No | `git diff HEAD~1` | Git ref, branch, or manual file list |
| **Impact depth** | No | 2 | Dependency traversal levels |
| **Risk threshold** | No | `medium` | Minimum risk level: `low`/`medium`/`high`/`critical` |
| **Coverage threshold** | No | 80% | Minimum coverage on changed code |
| **Criteria mode** | No | `all` | Which criteria: `change`, `risk`, `coverage`, or `all` |
| **Max tests** | No | unlimited | Cap on total tests to select/generate |
| **Config file** | No | `.regression-config.json` | Path to override config |
| **Base URL** | No | `http://localhost:3000` | Dev server URL for E2E tests |
| **Test level** | No | `e2e` | `e2e` (page-level navigation, locators, assertions) or `component` (Playwright component testing with `mount()`) or `both` |
| **Browser targets** | No | `chromium` | Browsers to test: `chromium`, `firefox`, `webkit`, or comma-separated list |
| **Headless** | No | `true` | Run browsers in headless mode |
| **Test data dir** | No | `__fixtures__/` or `__mocks__/` | Path to fixture files (JSON) for data-driven tests |
| **Expected outputs dir** | No | none | Path to golden files / screenshot baselines for visual comparison |
| **Data format** | No | `json` | Format of fixture data: `json` or `csv` |
| **Business criticality map** | No | none | JSON mapping of file/path glob patterns to criticality levels |
| **Regression scenarios** | No | none | Path to a YAML file defining user regression scenarios (see Regression Scenarios section) |
| **Requirement IDs** | No | none | Comma-separated ticket/requirement IDs for traceability tags |
| **CI mode** | No | `false` | When `true`, generate CI artifacts (JUnit XML, HTML report, JSON manifest) in `report_dir` |
| **Report dir** | No | `./regression-reports` | Output directory for CI report artifacts |
| **Report formats** | No | `junit-xml,html,json` | Artifact formats: `junit-xml`, `html`, `json`, `markdown` |
| **Test splitting** | No | `1` | Number of shards for parallel CI execution |
| **Flaky threshold** | No | `2` | Retry count — tests that fail then pass are marked `flaky` |
| **Screenshot on failure** | No | `true` | Capture screenshots on test failure |
| **Trace on failure** | No | `true` | Capture Playwright traces on test failure |
| **API mocking** | No | `route` | API mocking strategy: `route` (Playwright route interception) or `msw` (Mock Service Worker) |

## Safety Rules — CRITICAL

These rules are **non-negotiable** and must be followed at all times:

1. **NEVER modify, rename, or refactor any existing source file.** Only create
   new files in test directories or append new test methods to existing test files.
2. **NEVER alter existing test methods.** When adding to an existing test file,
   only append new `test.describe`/`test` blocks — do not change existing ones.
3. **All file writes MUST target test files only.** Valid patterns:
   - `*.spec.ts`, `*.spec.tsx` (Playwright convention)
   - `*.e2e.ts`, `*.e2e.tsx` (E2E convention)
   - `e2e/*.spec.ts`, `e2e/*.ts`
   - `tests/*.spec.ts`, `tests/*.ts`
   - `*.ct.ts`, `*.ct.tsx` (Playwright component test convention)
4. **Before writing any file**, verify the target path does NOT match a source
   file pattern (i.e., must match a test pattern).
5. **NEVER modify** `.tsx`, `.ts`, `.jsx`, `.js`, `.css`, `.scss`, `package.json`, or config files.
6. **If a test reveals a bug in the source code**, report it in the final summary
   but do NOT fix it.
7. **After test generation**, run `git diff --name-only` on non-test paths. If
   any source files were modified, flag this as a violation and revert.

## Master Workflow

### For Agents With Subagent Support (VS Code Copilot, Claude Code, etc.)

Use the orchestrator + subagent pattern. See the custom agents in
`.github/agents/` for VS Code, or follow this delegation model:

#### Phase 1: Setup
- Collect user inputs (codebase path, change source, thresholds, test level, CI mode, base URL, browsers)
- Load `.regression-config.json` if present; merge with user inputs
- Validate codebase path contains `package.json` and React source files
- Record `git status` for integrity checks later
- Detect framework type: check `package.json` for `react` dependency
- Detect if Next.js: check for `next` dependency and `app/` or `pages/` directory
- Detect Playwright: check `package.json` for `@playwright/test` dependency; check for `playwright.config.*`
- If `@playwright/test` is not installed, warn the user and suggest `npm install -D @playwright/test`
- If Playwright component testing is requested, verify `@playwright/experimental-ct-react` is available
- Scan for user-provided test data directories (fixtures); validate fixture files exist and index by domain entity
- Load regression scenarios YAML file if provided; validate scenarios reference existing source files
- Detect existing Playwright test directory structure (e.g., `e2e/`, `tests/`, project root)
- Extract `business_criticality.overrides` from config for use in Phase 4

#### Phase 2: Change Detection
- Delegate to **change-analyzer** subagent
- Runs `scripts/analyze-changes.py` with the change source
- Returns `changes.json`: list of changed `.tsx`, `.ts`, `.jsx`, `.js` files with diff stats
- If user provided manual file list, skip git analysis and use that

#### Phase 3: Impact Analysis
- **change-analyzer** subagent runs `scripts/build-dependency-graph.py`
- Parses ESM `import` and CJS `require()` statements
- Resolves imports via `tsconfig.json` `paths` aliases
- Detects monorepo workspace structure from `package.json` `workspaces`
- Returns `impact.json`: changed files + all transitively impacted files
- Runs `scripts/list-existing-tests.py` to map impacted source files to existing Playwright test files
- Returns `test-map.json`: source file -> existing test file(s) mapping (recognizes `*.spec.ts`, `*.e2e.ts`, `*.ct.ts`)

#### Phase 4: Risk Scoring
- Delegate to **risk-scorer** subagent
- Runs `scripts/calculate-risk-scores.py` for each impacted file
- Pass `--criticality-map` with user-provided business criticality overrides from config
- Computes cyclomatic complexity, change frequency, defect history, business criticality
- Path heuristics: `**/hooks/**` (high), `**/context/**` (high), `**/api/**` (high), `**/pages/**` (high), `**/app/**` (high), `**/components/**` (medium), `**/utils/**` (low), `**/types/**` (low)
- User-defined criticality overrides take precedence over path-heuristic defaults
- Returns `risk-scores.json`: per-file risk score + level

#### Phase 5: Test Selection & Prioritization
- Delegate to **test-selector** subagent
- Runs `scripts/select-tests.py` with all JSON manifests + qualification config
- If regression scenarios file is provided, pass `--scenarios` flag to boost priority of scenario-targeted files
- Applies combined scoring formula
- Returns `selected-tests.json`: prioritized list of existing Playwright tests to run
- Also returns `coverage-gaps.json`: files/methods needing new tests

#### Phase 6: Gap Test Generation (Parallel, Batched 3-5)
- For each coverage gap, spawn **regression-test-generator** subagent
- Each receives: source file, component/page metadata, gap details, Playwright testing reference, test level, matching fixtures, matching regression scenarios, requirement IDs, base URL, browser targets, API mocking strategy
- For `test_level=e2e`: generate tests using `page.goto()`, `page.locator()`, `expect(page)`, `expect(locator)`, Playwright route interception for API mocking
- For `test_level=component`: generate tests using `mount()` from `@playwright/experimental-ct-react`, component-level assertions
- For `test_level=both`: generate separate E2E and component test files in `*.spec.ts` and `*.ct.ts`
- When user-provided fixture files match the target entity, generator loads fixture data via import or inline parameterized tests
- When regression scenarios target this file, generator creates nested `test.describe` blocks per scenario with descriptive test names matching the scenario narrative
- When requirement IDs are provided, generator adds `// REQ-xxx` comments and test annotations
- Write test files following project convention (e.g., `e2e/`, `tests/`, co-located)
- **Safety**: verify all writes target test file patterns only

#### Phase 7: Execution & Verification
- Spawn **regression-verifier** subagent
- Runs `scripts/run-regression-tests.py` with selected + generated tests
- Playwright: `npx playwright test --reporter=list,junit`
- If `test_splitting` > 1, use Playwright's built-in sharding: `--shard=N/M`
- Returns test results + optional coverage (via Istanbul instrumented build or Playwright coverage API)
- Captures traces and screenshots on failure when configured
- **Flaky test detection**: if a test fails then passes on retry, classify as `flaky` (not `passed`). Report flaky tests separately.
- On failures: re-spawn generator with error context (max 3 retries)
- Coverage gate: if changed-code coverage < threshold, generate more tests (max 2 iterations)
- If `ci_mode=true`: generate CI artifacts (JUnit XML, HTML report, JSON manifest) in `report_dir`

#### Phase 8: Report
- Run `git diff --name-only` — verify zero source file modifications
- Output final summary:
  - Changed files detected
  - Impact analysis: N files impacted
  - Risk distribution: N critical, N high, N medium, N low
  - Tests selected: N existing Playwright tests (prioritized list)
  - Tests generated: N new test files (e2e: N, component: N)
  - Execution results: passed/failed/skipped/flaky
  - Flaky tests: list of tests that failed then passed on retry
  - Coverage on changed code: X% (threshold: Y%)
  - Screenshots/traces: paths to failure artifacts
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
   b. Load `references/playwright-regression-patterns.md`
   c. Generate the complete Playwright test file
   d. Write the test file as `*.spec.ts` (E2E) or `*.ct.ts` (component)
   e. **Drop the source file from context** before moving to the next
7. Run `scripts/run-regression-tests.py` -> fix failures (max 3 retries)
8. Run `scripts/check-coverage.py` -> if below threshold, generate more (max 2 iterations)
9. Produce the summary report

**Context management rules for sequential mode:**
- Never load more than 1 source file at a time
- Use JSON manifests for navigation, not raw source
- Complete one module before moving to the next

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
- **target_routes** — URL paths to navigate to for E2E regression
- **expected_behaviors** — list of assertions in natural language
- **requirement_ids** — linked ticket/requirement IDs
- **priority** — `critical`, `high`, or `medium`

Scenarios boost the priority of targeted files in the selection scoring formula
(configurable boost, default: +20 points). The generator creates nested `test.describe`
blocks per scenario with descriptive test names matching the scenario narrative.

### Requirement Traceability

When `requirement_ids` are provided (via user input, scenario file, or config):
- Each generated test file gets `// @requirement REQ-xxx` comments
- Each test uses Playwright annotations: `test.info().annotations.push({ type: 'requirement', description: 'REQ-xxx' })`
- Each test's description includes the requirement ID: `[REQ-xxx]`
- The final report includes a traceability matrix: requirements → test files

## Test File Naming Conventions

| Source File | E2E Test File | Component Test File |
|---|---|---|
| `UserProfile.tsx` | `UserProfile.spec.ts` | `UserProfile.ct.tsx` |
| `useAuth.ts` | `auth-flow.spec.ts` | N/A (hooks tested via component) |
| `app/orders/page.tsx` | `orders.spec.ts` | `orders-page.ct.tsx` |
| `CartContext.tsx` | `cart-flow.spec.ts` | `CartContext.ct.tsx` |
| `Header.tsx` | `header.spec.ts` | `Header.ct.tsx` |

## CI/CD Integration

When `ci_mode` is enabled, the skill generates CI-ready artifacts and supports
parallel execution across pipeline workers.

### Test Runner Commands

**Playwright E2E**:
```bash
npx playwright test --reporter=list,junit --output=regression-reports/test-results
```

**Playwright Component Testing**:
```bash
npx playwright test -c playwright-ct.config.ts --reporter=list,junit
```

### Report Artifacts

Generated in `report_dir` (default: `./regression-reports/`):

| File | Format | Purpose |
|---|---|---|
| `regression-results.xml` | JUnit XML | CI dashboard integration (GitHub Actions, Azure DevOps) |
| `regression-results.json` | JSON | Machine-readable full results with metadata |
| `regression-summary.md` | Markdown | Human-readable summary for PR comments |
| `report/index.html` | HTML | Playwright HTML report with traces and screenshots |
| `traces/` | Trace ZIP | Playwright trace files for failed tests |
| `screenshots/` | PNG | Screenshot captures for failed tests |

### Test Splitting (Sharding)

For parallel CI execution, Playwright has built-in sharding support:
- Configure via `test_splitting` (total shards) — each CI worker runs with `--shard=N/M`
- Playwright distributes tests across shards automatically
- Each shard produces its own report artifacts for aggregation
- Use `npx playwright merge-reports` to combine shard results

### Flaky Test Handling

- Configure retries in `playwright.config.ts` or via `--retries` CLI flag
- Tests that fail then pass on retry are classified as `flaky`
- Flaky tests are reported separately from passed/failed in results
- Set `flaky_detection.quarantine_flaky=true` in config to exclude known-flaky tests from blocking the pipeline
- Use Playwright's `test.fixme()` or `test.skip()` annotations for quarantined tests

### Pipeline Examples

#### GitHub Actions
```yaml
jobs:
  regression-tests:
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 18
      - run: npm ci
      - run: npx playwright install --with-deps chromium
      - name: Run regression shard
        run: |
          npx playwright test --shard=${{ matrix.shard }}/4 \
            --reporter=junit,html \
            --output=regression-reports/test-results
        env:
          PLAYWRIGHT_JUNIT_OUTPUT_NAME: regression-reports/regression-results-${{ matrix.shard }}.xml
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: regression-reports-${{ matrix.shard }}
          path: |
            regression-reports/
            playwright-report/
            test-results/
      - uses: dorny/test-reporter@v1
        if: always()
        with:
          name: Playwright Regression (Shard ${{ matrix.shard }})
          path: regression-reports/regression-results-${{ matrix.shard }}.xml
          reporter: java-junit
  
  merge-reports:
    needs: regression-tests
    if: always()
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - uses: actions/download-artifact@v4
        with:
          pattern: regression-reports-*
          merge-multiple: true
          path: all-reports/
      - run: npx playwright merge-reports --reporter=html ./all-reports
      - uses: actions/upload-artifact@v4
        with:
          name: merged-regression-report
          path: playwright-report/
```

#### Azure DevOps
```yaml
jobs:
  - job: RegressionTests
    strategy:
      matrix:
        shard1: { SHARD: '1/2' }
        shard2: { SHARD: '2/2' }
    steps:
      - task: NodeTool@0
        inputs:
          versionSpec: '18.x'
      - script: npm ci
      - script: npx playwright install --with-deps chromium
      - script: |
          npx playwright test --shard=$(SHARD) \
            --reporter=junit,html \
            --output=regression-reports/test-results
        env:
          PLAYWRIGHT_JUNIT_OUTPUT_NAME: regression-reports/regression-results.xml
      - task: PublishTestResults@2
        condition: always()
        inputs:
          testResultsFormat: JUnit
          testResultsFiles: regression-reports/regression-results.xml
          testRunTitle: Playwright Regression (Shard $(SHARD))
      - task: PublishPipelineArtifact@1
        condition: always()
        inputs:
          targetPath: playwright-report/
          artifactName: playwright-report-$(SHARD)
```

## Scripts Reference

All scripts are in the `scripts/` directory. Run with Python 3.8+.

| Script | Purpose | Key Input | Output |
|---|---|---|---|
| `analyze-changes.py` | Parse git diff for changed React files | `<codebase> [--ref HEAD~1]` | `changes.json` |
| `build-dependency-graph.py` | Build ESM/CJS import dependency graph | `<codebase> --depth <N>` | `impact.json` |
| `calculate-risk-scores.py` | Compute risk per source file | `<files-json> --window 90 [--criticality-map <json>]` | `risk-scores.json` |
| `list-existing-tests.py` | Map React source files to Playwright test files | `<module-path>` | `test-map.json` (includes `testType: e2e&#124;component`) |
| `select-tests.py` | Apply criteria, rank, select | `--changes <json> --risks <json> [--scenarios <yaml>] [--shard N/M]` | `selected-tests.json` |
| `run-regression-tests.py` | Execute selected tests via Playwright | `<module> --test-runner playwright [--ci-mode] [--shard N/M] [--retries N]` | `results.json` |
| `check-coverage.py` | Coverage gaps on changed code | `<report> --threshold <N>` | `coverage-gaps.json` |

## Language-Specific Reference

Load the Playwright regression patterns reference when generating tests:

- [Playwright Regression Patterns](references/playwright-regression-patterns.md)
- [Qualification Criteria](references/qualification-criteria.md)

## Test Templates

Skeleton templates are available in `assets/test-templates/`. Use them as a
starting point and fill in the specific test logic based on the source code analysis.
