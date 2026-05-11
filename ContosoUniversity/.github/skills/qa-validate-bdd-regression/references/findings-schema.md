# Findings Schema

Schema for validation findings produced by `qa-validate-bdd-regression`.

## Finding Object

Each finding in `validation-report.json` must have these fields:

### Required Fields

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique finding ID. Format: `BDD-VAL-{NNN}` (e.g., `BDD-VAL-001`) |
| `dimension` | enum | One of: `coverage`, `consistency`, `correctness`, `traceability`, `completeness` |
| `severity` | enum | One of: `high`, `medium`, `low` |
| `category` | string | See category table below |
| `message` | string | Human-readable description of the finding |
| `recommendation` | string | Actionable suggestion to resolve the gap |
| `priority_score` | number | Computed score from gap prioritization formula (0.0-10.0) |
| `priority_tier` | enum | One of: `P0`, `P1`, `P2`, `P3` |

### Optional Fields

| Field | Type | Description |
|---|---|---|
| `bdd_feature` | string | Path to the `.feature` file (relative to features root) |
| `regression_scenario` | string | Name of the regression scenario |
| `requirement_id` | string | Requirement ID (e.g., `REG-ANALYTICS-001`) |
| `bdd_scenario_title` | string | Title of specific BDD scenario within the feature |
| `expected_behavior` | string | Text of the regression expected behavior |
| `target_file` | string | Path to the source file referenced |

## Categories

| Category | Dimension | Default Severity |
|---|---|---|
| `orphaned-bdd` | coverage | high |
| `orphaned-regression` | coverage | high |
| `uncovered-behavior` | coverage | medium |
| `behavioral-conflict` | consistency | high |
| `edge-case-gap` | correctness | medium |
| `edge-case-missing` | correctness | high |
| `naming-inconsistency` | consistency | low |
| `scope-mismatch` | consistency | low |
| `missing-target-file` | traceability | high |
| `orphaned-requirement` | traceability | medium |
| `broken-chain` | traceability | high |
| `shallow-coverage` | completeness | medium |
| `uncovered-component` | completeness | high |
| `uncovered-pipeline` | completeness | high |
| `critical-path-gap` | completeness | high |

## Summary Object

The `summary` section in the JSON report:

```json
{
  "total_findings": 3,
  "by_severity": {
    "high": 0,
    "medium": 2,
    "low": 1
  },
  "by_dimension": {
    "coverage": 0,
    "consistency": 1,
    "correctness": 1,
    "traceability": 0,
    "completeness": 1
  },
  "by_category": {
    "edge-case-gap": 1,
    "uncovered-behavior": 1,
    "naming-inconsistency": 1
  },
  "by_priority_tier": {
    "P0": 0,
    "P1": 0,
    "P2": 2,
    "P3": 1
  },
  "metrics": {
    "forward_coverage_pct": 100,
    "backward_coverage_pct": 100,
    "behavior_coverage_pct": 92,
    "component_coverage_pct": 100,
    "pipeline_coverage_pct": 100,
    "traceability_completeness_pct": 100
  },
  "overall_status": "PASS_WITH_FINDINGS"
}
```

## Validation Dimensions Object

The `validation_dimensions` section:

```json
{
  "coverage": {
    "forward": { "covered": 26, "total": 26, "pct": 100 },
    "backward": { "covered": 8, "total": 8, "pct": 100 },
    "behavior": { "covered": 85, "total": 92, "pct": 92.4 }
  },
  "consistency": {
    "aligned": 24,
    "compatible": 1,
    "divergent": 1,
    "conflicting": 0
  },
  "correctness": {
    "edge_cases_both": 12,
    "edge_cases_bdd_only": 1,
    "edge_cases_regression_only": 0,
    "edge_cases_neither": 0
  },
  "traceability": {
    "complete_chains": 26,
    "broken_chains": 0,
    "orphaned_requirements": 0,
    "missing_target_files": 0
  },
  "completeness": {
    "components_covered": 35,
    "components_total": 35,
    "pipelines_covered": 4,
    "pipelines_total": 4,
    "critical_path_gaps": 0
  }
}
```
