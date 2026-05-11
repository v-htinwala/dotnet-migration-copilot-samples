---
name: qa-validate-bdd-regression
description: >
  Validates BDD Gherkin scenarios against regression test case definitions.
  Performs five-dimensional analysis: coverage (forward/backward), consistency
  (behavioral alignment), correctness (edge case gaps, conflicts), traceability
  (BDD ↔ regression ↔ requirement IDs ↔ target files), and completeness
  (pipeline/component/critical-path coverage). Stack-agnostic: works with any
  Gherkin .feature files and YAML/JSON regression scenario definitions.
  Triggers: "validate BDD against regression", "check BDD coverage",
  "BDD regression alignment", "traceability matrix", "BDD gap analysis",
  "validate feature files against regression scenarios".
license: Apache-2.0
compatibility: >
  Stack-agnostic. Reads .feature files (Gherkin) and regression scenario
  definitions (YAML or JSON). Produces markdown and/or JSON validation reports.
  No runtime deps. Works with Cucumber, SpecFlow, Behave, or any BDD framework.
metadata:
  author: GenAI CoE
  version: "1.0.0"
  role: qa
  priority: P1
keywords:
  - bdd
  - gherkin
  - regression
  - validation
  - traceability
  - coverage
  - gap analysis
  - feature file
  - scenario alignment
  - test coverage matrix
---

# qa-validate-bdd-regression

Validate BDD Gherkin `.feature` files against regression test case definitions. Produce a multi-dimensional validation report with coverage matrices, traceability maps, consistency findings, and gap analysis.

## Response Style (mandatory)

Terse. Technical substance stays. Fluff dies.

- Drop articles (a/an/the), filler (just/really/basically/actually/simply), pleasantries, hedging.
- Fragments OK. Short synonyms. Technical terms exact. Code blocks unchanged. Errors quoted exact.
- Pattern: `[thing] [action] [reason]. [next step].`
- Abbreviate: DB, auth, config, req, res, fn, impl, ctrl, svc, repo.
- Arrows for causality: `X → Y`.
- Drop terse mode for: security warnings, destructive confirms, multi-step sequences where order matters, user repeats question. Resume after.

## When to Use This Skill

Activate when the user wants to:
- Validate BDD feature files against regression test scenarios
- Check if all BDD scenarios have regression coverage (and vice versa)
- Build a traceability matrix from BDD features to requirement IDs
- Identify behavioral conflicts between BDD and regression definitions
- Assess completeness of test coverage across pipelines/components
- Audit edge case coverage across BDD and regression test suites
- Generate a gap analysis report for BDD vs. regression alignment

**Trigger Phrases:**
- "validate BDD against regression"
- "check BDD coverage against regression tests"
- "BDD regression alignment"
- "traceability matrix"
- "BDD gap analysis"
- "validate feature files against regression scenarios"
- "are BDD scenarios covered by regression tests"

## User Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| **Feature files path** | Yes | `src/test/resources/features/` | Directory containing `.feature` files (recursive scan) |
| **Regression scenarios path** | Yes | `discovery-output/regression-scenarios.yml` | YAML or JSON file defining regression test scenarios |
| **Source code root** | No | `src/main/java/` | Root directory for verifying target file existence |
| **Output directory** | No | `assessment-output/{run-id}/qa-validate-bdd-regression/` | Where to write validation report artifacts |
| **Output formats** | No | `markdown` | Comma-separated: `markdown`, `json`, or `both` |
| **Validation dimensions** | No | `all` | Comma-separated: `coverage`, `consistency`, `correctness`, `traceability`, `completeness`, or `all` |
| **Run ID** | No | Date-based (e.g., `20260420`) | Unique identifier for assessment run |

## Safety Rules — CRITICAL

1. **READ-ONLY**: Never modify `.feature` files, regression scenario files, or source code.
2. **Report findings only**: Generate validation reports. Do not create or alter tests.
3. **No false positives**: Only flag genuine gaps/conflicts. When behavior semantically aligns but uses different wording, classify as ALIGNED, not a gap.
4. **Preserve structure**: Do not reorganize, rename, or restructure any project files.

## Workflow

Execute phases sequentially. Each phase depends on the prior phase's output.

### Phase 1: Discovery & Inventory

**Goal**: Build a normalized inventory of all BDD features and regression scenarios.

#### Step 1.1: Scan BDD Feature Files

Recursively scan the feature files directory for all `.feature` files:

```
Pattern: {feature_files_path}/**/*.feature
```

For each `.feature` file, extract:

| Field | Source | Example |
|---|---|---|
| `file_path` | Relative file path | `filter/artist-filter.feature` |
| `category` | Parent directory name | `filter` |
| `feature_name` | `Feature:` line text | `Artist pattern filtering` |
| `tags` | `@tag` annotations on Feature line | `@java @service @smoke` |
| `scenario_count` | Count of `Scenario:` + `Scenario Outline:` | 6 |
| `scenarios` | List of scenario titles | `["Artist matching substring...", ...]` |
| `regression_tagged` | Count of scenarios with `@regression` tag | 2 |
| `has_background` | Whether `Background:` section exists | true |
| `given_keywords` | Domain terms from Given steps | `["filter", "pattern", "song"]` |
| `when_keywords` | Domain terms from When steps | `["evaluates", "processes"]` |
| `then_keywords` | Domain terms from Then steps | `["passes", "rejected", "count"]` |

Produce: `bdd-inventory.json` — array of feature objects.

#### Step 1.2: Parse Regression Scenarios

Parse the regression scenarios file (YAML or JSON):

For each scenario, extract:

| Field | Source | Example |
|---|---|---|
| `name` | Scenario `name` field | `AnalyticsMulticastFlow` |
| `description` | Scenario `description` | `CSV file → parse → ...` |
| `priority` | Scenario `priority` | `critical` |
| `target_files` | List of target source files | `["...ArtistStatsProcessor.java"]` |
| `target_routes` | List of route IDs | `["analytics-artist"]` |
| `expected_behaviors` | List of behavior strings | `["accumulates song count..."]` |
| `requirement_ids` | List of requirement IDs | `["REG-ANALYTICS-001"]` |
| `component_names` | Extracted class names from target files | `["ArtistStatsProcessor"]` |

Produce: `regression-inventory.json` — array of scenario objects.

#### Step 1.3: Build Mapping Index

Create a mapping index using multiple matching strategies:

1. **Component Name Match**: Extract class names from regression `target_files` and match against BDD feature names/keywords.
2. **Category Match**: Map BDD categories (filter, processor, route, etc.) to regression scenario component types.
3. **Behavioral Keyword Match**: Compare BDD step keywords (Given/When/Then text) against regression `expected_behaviors` text using semantic overlap scoring.
4. **Route Match**: Map BDD route feature files to regression scenarios by `target_routes`.

Produce: `mapping-index.json` — bidirectional mapping of BDD features ↔ regression scenarios.

**Mapping Confidence Levels**:

| Level | Criteria |
|---|---|
| **High** | Component name directly matches + category matches + behavioral keywords overlap ≥ 60% |
| **Medium** | Category matches + behavioral keywords overlap ≥ 30% |
| **Low** | Only category matches OR only keyword overlap ≥ 20% |
| **None** | No match found |

---

### Phase 2: Coverage Analysis

**Goal**: Determine bidirectional coverage between BDD features and regression scenarios.

#### Step 2.1: Forward Coverage (BDD → Regression)

For each BDD feature, check if it maps to at least one regression scenario:

```
Status:
  ✅ Covered    — Maps to 1+ regression scenarios with High or Medium confidence
  ⚠️ Weak       — Maps only with Low confidence
  ❌ Uncovered  — No mapping found
```

Compute:
- `forward_coverage_pct` = (Covered + Weak) / Total BDD features × 100
- `forward_strong_pct` = Covered / Total BDD features × 100
- `orphaned_bdd_features` = list of uncovered features

#### Step 2.2: Backward Coverage (Regression → BDD)

For each regression scenario, check if it has at least one mapped BDD feature:

```
Status:
  ✅ Covered    — 1+ BDD features map to this scenario
  ❌ Uncovered  — No BDD features map here
```

Compute:
- `backward_coverage_pct` = Covered / Total regression scenarios × 100
- `orphaned_regression_scenarios` = list of uncovered scenarios

#### Step 2.3: Cross-Reference Coverage

For each regression scenario `expected_behavior`, check if a corresponding BDD scenario exists:

```
Status:
  ✅ Tested     — BDD scenario explicitly tests this behavior
  ⚠️ Implicit   — BDD scenario partially or implicitly covers this behavior
  ❌ Untested   — No BDD scenario tests this specific behavior
```

Compute: `behavior_coverage_pct` per regression scenario.

Produce: `coverage-analysis.json`.

---

### Phase 3: Consistency & Correctness Audit

**Goal**: Identify behavioral conflicts, edge case gaps, and naming inconsistencies.

#### Step 3.1: Behavioral Alignment Check

For each BDD ↔ regression mapping, compare expected behaviors:

| Check | How | Severity |
|---|---|---|
| **Contradictory outcomes** | BDD says "returns null" vs. regression says "throws error" for same input | 🔴 High |
| **Divergent edge case handling** | BDD handles null one way, regression documents different handling | 🟡 Medium |
| **Scope mismatch** | BDD tests unit behavior, regression tests integration flow for same component | 🟢 Low (informational) |
| **Missing edge case** | Regression documents edge case, no BDD scenario covers it (or vice versa) | 🟡 Medium |

Classification rules:
- **ALIGNED**: BDD and regression test the same behavior with semantically equivalent expectations.
- **COMPATIBLE**: BDD and regression test related behaviors; no conflict but not exact match.
- **DIVERGENT**: BDD and regression have different expectations for the same input/condition.
- **CONFLICTING**: BDD and regression have contradictory expectations (one passes, other would fail).

#### Step 3.2: Edge Case Matrix

Build a matrix of edge cases across the codebase:

| Edge Case | Source | BDD Feature(s) | Regression Scenario(s) | Status |
|---|---|---|---|---|
| Null input X | Domain knowledge | feature-a | scenario-1 | ✅ Both |
| Boundary Y | Domain knowledge | feature-b | (none) | ⚠️ BDD only |
| Error Z | Domain knowledge | (none) | scenario-2 | ⚠️ Regression only |
| Concurrent access | Domain knowledge | (none) | (none) | ❌ Neither |

Status values:
- `✅ Both` — tested in BDD and regression
- `⚠️ BDD only` — tested in BDD, not in regression
- `⚠️ Regression only` — tested in regression, not in BDD
- `❌ Neither` — not tested anywhere (critical gap)

#### Step 3.3: Naming Consistency

Check for naming inconsistencies between BDD and regression:
- Component names (e.g., "ArtistFilter" vs. "artist-filter")
- Route names (e.g., "analytics-artist" consistent across both)
- Behavior descriptions (e.g., "case-insensitive" vs. "ignoring case")

Flag only genuine inconsistencies that could cause confusion, not stylistic differences.

Produce: `consistency-findings.json`.

---

### Phase 4: Traceability Verification

**Goal**: Validate end-to-end traceability chains.

#### Step 4.1: Bidirectional Traceability Chain

For each BDD feature, verify the full chain exists:

```
BDD Feature → Regression Scenario → Target Files → Requirement ID
```

Check:
1. BDD feature maps to at least one regression scenario (**Phase 2 output**)
2. Regression scenario has `target_files` that exist in the source tree
3. Regression scenario has `requirement_ids` assigned
4. No orphaned requirement IDs (all IDs map back to at least one BDD feature)

#### Step 4.2: Target File Verification

For each `target_file` in regression scenarios:
1. Verify the file exists at the specified path under `source_code_root`
2. If file doesn't exist, flag as `missing_target` (🔴 High severity)
3. If file exists, verify the class name matches the expected component

#### Step 4.3: Requirement ID Validation

1. Collect all unique requirement IDs from regression scenarios
2. Verify each requirement ID maps to at least one BDD feature (via scenario mapping)
3. Check for duplicate requirement IDs across scenarios
4. Flag orphaned requirement IDs

Produce: `traceability-matrix.json`.

---

### Phase 5: Completeness Assessment

**Goal**: Evaluate whether all critical paths, components, and flows are tested.

#### Step 5.1: Component Coverage

Inventory all components referenced by regression scenarios and check BDD coverage:

| Component Type | Expected Sources | Check |
|---|---|---|
| Routes | `target_routes` from regression | Each route has a BDD route feature |
| Processors | `target_files` matching `*Processor.java` | Each processor has a BDD processor feature |
| Filters | `target_files` matching `*Filter.java` | Each filter has a BDD filter feature |
| Transformers | `target_files` matching `*Transformer.java` | Each transformer has a BDD transform feature |
| Validators | `target_files` matching `*Validator*.java` | Each validator has a BDD validator feature |
| Strategies | `target_files` matching `*Strategy.java` | Each strategy has a BDD strategy feature |
| Other | Remaining target files | Best-effort matching |

#### Step 5.2: Pipeline / Flow Coverage

If regression scenarios define `target_routes`:
1. Map routes to end-to-end pipeline flows
2. Verify each pipeline has both a BDD route feature AND regression scenario
3. Check if all pipeline stages (parse → process → output) have BDD coverage

#### Step 5.3: Critical Path Analysis

Identify critical data flows from regression scenario descriptions:
1. Parse flow descriptions (e.g., "CSV → parse → filter → export")
2. Verify each stage in the flow has BDD coverage
3. Flag uncovered stages as critical path gaps

#### Step 5.4: Test Depth Assessment

For each BDD feature, classify test depth:

| Depth | Criteria |
|---|---|
| **Thorough** | ≥ 3 scenarios, includes happy path + error + edge case, has `@regression` tags |
| **Adequate** | ≥ 2 scenarios, includes happy path + at least one error or edge case |
| **Shallow** | 1 scenario only, or only happy path tested |
| **Empty** | Feature file exists but no scenarios defined |

Produce: `completeness-assessment.json`.

---

### Phase 6: Report Generation

**Goal**: Produce the final validation report in requested formats.

#### Step 6.1: Compute Summary Metrics

```json
{
  "forward_coverage_pct": 100,
  "backward_coverage_pct": 100,
  "behavior_coverage_pct": 92,
  "consistency_findings_count": 3,
  "traceability_orphans": 0,
  "component_coverage_pct": 100,
  "pipeline_coverage_pct": 100,
  "critical_path_gaps": 0,
  "overall_status": "PASS | PASS_WITH_FINDINGS | FAIL"
}
```

**Overall Status Rules**:
- `PASS` — All dimensions at 100%, zero findings
- `PASS_WITH_FINDINGS` — All dimensions ≥ 80%, no 🔴 High severity findings
- `FAIL` — Any dimension < 80% OR any 🔴 High severity finding

#### Step 6.2: Generate Markdown Report

Use the [report template](templates/validation-report.template.md) to produce a structured report:

**Required Sections** (in order):

1. **Executive Summary** — Table with key metrics, overall status badge
2. **Coverage Analysis** — Forward matrix, backward matrix, orphan lists
3. **Traceability Matrix** — BDD → Regression → Files → Requirement IDs with confidence levels
4. **Consistency & Correctness Findings** — Behavioral conflicts table, edge case matrix, naming issues
5. **Completeness Assessment** — Component table, pipeline coverage, critical path diagrams, test depth
6. **Detailed Gaps & Recommendations** — Prioritized by severity (High → Medium → Low)
7. **Appendix** — File references, methodology notes

#### Step 6.3: Generate JSON Report (if requested)

Produce `validation-report.json` conforming to the [findings schema](references/findings-schema.md):

```json
{
  "schema_version": "1.0.0",
  "skill_name": "qa-validate-bdd-regression",
  "run_id": "{run-id}",
  "timestamp": "{ISO-8601}",
  "validation_dimensions": {
    "coverage": { ... },
    "consistency": { ... },
    "correctness": { ... },
    "traceability": { ... },
    "completeness": { ... }
  },
  "findings": [],
  "summary": { ... }
}
```

#### Step 6.4: Gap Prioritization

Rank all identified gaps using the following priority scoring:

| Factor | Weight | Values |
|---|---|---|
| Severity | 40% | High=10, Medium=6, Low=3 |
| Coverage Impact | 30% | Uncovered critical path=10, Uncovered component=7, Edge case gap=4, Naming only=1 |
| Fix Effort | 15% | Add 1 BDD scenario=2, Add multiple scenarios=5, Restructure=8 |
| Business Risk | 15% | Data integrity=10, Functional=7, Cosmetic=2 |

```
gap_priority_score = (severity × 0.4) + (coverage_impact × 0.3) + ((10 - fix_effort) × 0.15) + (business_risk × 0.15)
```

Sort gaps descending by `gap_priority_score`. Assign tiers:
- **P0** (Critical): score ≥ 8.0
- **P1** (High): score ≥ 6.0
- **P2** (Medium): score ≥ 4.0
- **P3** (Low): score < 4.0

---

## Output Specification

### Output Directory Structure

```
assessment-output/{run-id}/qa-validate-bdd-regression/
├── validation-report.md          # Human-readable validation report
├── validation-report.json        # Machine-readable findings (if requested)
├── bdd-inventory.json            # Phase 1: BDD feature inventory
├── regression-inventory.json     # Phase 1: Regression scenario inventory
├── mapping-index.json            # Phase 1: Bidirectional mapping
├── coverage-analysis.json        # Phase 2: Coverage metrics
├── consistency-findings.json     # Phase 3: Consistency audit results
├── traceability-matrix.json      # Phase 4: Traceability chain data
├── completeness-assessment.json  # Phase 5: Completeness metrics
└── references/
    └── (supporting files if needed)
```

### Findings Schema

Each finding in `validation-report.json` must conform to:

```json
{
  "id": "BDD-VAL-001",
  "dimension": "coverage | consistency | correctness | traceability | completeness",
  "severity": "high | medium | low",
  "category": "orphaned-bdd | orphaned-regression | behavioral-conflict | edge-case-gap | missing-traceability | naming-inconsistency | shallow-coverage | missing-target-file | orphaned-requirement",
  "bdd_feature": "path/to/feature.feature",
  "regression_scenario": "ScenarioName",
  "requirement_id": "REG-XXX-001",
  "message": "Description of the finding",
  "recommendation": "Suggested fix",
  "priority_score": 7.5,
  "priority_tier": "P1"
}
```

---

## Issue Categorization

| Category | Dimension | Severity | Description |
|---|---|---|---|
| `orphaned-bdd` | Coverage | high | BDD feature has no regression scenario mapping |
| `orphaned-regression` | Coverage | high | Regression scenario has no BDD feature coverage |
| `uncovered-behavior` | Coverage | medium | Regression expected behavior has no BDD scenario |
| `behavioral-conflict` | Consistency | high | BDD and regression have contradictory expectations |
| `edge-case-gap` | Correctness | medium | Edge case tested in one but not the other |
| `edge-case-missing` | Correctness | high | Critical edge case tested in neither |
| `naming-inconsistency` | Consistency | low | Component/route naming mismatch between BDD and regression |
| `scope-mismatch` | Consistency | low | BDD tests at different level than regression (informational) |
| `missing-target-file` | Traceability | high | Regression target file does not exist in source tree |
| `orphaned-requirement` | Traceability | medium | Requirement ID not traceable to any BDD feature |
| `broken-chain` | Traceability | high | BDD → Regression → File chain is broken |
| `shallow-coverage` | Completeness | medium | BDD feature has only happy-path scenarios |
| `uncovered-component` | Completeness | high | Component has no BDD or regression coverage |
| `uncovered-pipeline` | Completeness | high | Pipeline/route has no end-to-end test coverage |
| `critical-path-gap` | Completeness | high | Stage in critical data flow has no test coverage |

---

## Quality Assurance

After generating the report, verify:

1. **No false orphans**: Re-check all "uncovered" features/scenarios using relaxed keyword matching before finalizing.
2. **Semantic equivalence**: Verify that behavioral "conflicts" are genuine contradictions, not different wording for the same behavior.
3. **File existence**: Confirm all referenced `.feature` files and regression scenario files actually exist at the stated paths.
4. **Metric accuracy**: Verify percentages by manually counting a sample (e.g., spot-check 3-5 mappings).
5. **Report completeness**: Ensure all 7 report sections are present in the markdown output.
6. **No impl leak**: Ensure the report doesn't expose sensitive credentials, internal paths, or security-relevant details.

## Success Criteria

| Criterion | Measurement |
|---|---|
| All BDD features inventoried | Feature count matches filesystem scan |
| All regression scenarios parsed | Scenario count matches YAML/JSON source |
| Mapping index is bidirectional | Every mapping has both forward and backward entries |
| Coverage metrics are accurate | Spot-check 5 mappings manually |
| No false positive conflicts | Every behavioral conflict is a genuine contradiction |
| Traceability chains are complete | Every chain endpoint is verified (file exists, ID maps) |
| Report has all required sections | 7 sections present in markdown output |
| Findings conform to schema | All findings have required fields |
| Gap priorities are correctly scored | Priority formula applied consistently |

## Verify After Generation

- Report file at correct output path.
- Executive summary metrics match detailed section data.
- All coverage percentages round correctly.
- Traceability matrix covers every BDD feature.
- No duplicate findings in the report.
- Gap recommendations are actionable (not vague).
- Priority tiers are correctly assigned per scoring formula.
