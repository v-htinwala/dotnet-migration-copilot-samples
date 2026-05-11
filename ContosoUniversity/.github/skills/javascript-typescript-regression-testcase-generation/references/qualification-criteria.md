# Qualification Criteria Reference

## Overview

The regression test selection system uses **three combined qualification criteria** to determine which tests to run and which new tests to generate. This approach ensures comprehensive coverage while focusing testing effort where it matters most.

## The Three Criteria Layers

### A. Change-Based Selection

**Purpose**: Identify what code changed and what depends on it.

**Process**:
1. Detect changed files from `git diff` (or user-provided list)
2. Build a dependency graph from import/reference analysis
3. Traverse dependents up to `impact_depth` levels (default: 2)
4. Map each impacted file to its existing test file(s)

**Output**: `changes.json` (changed files) + `impact.json` (impacted files) + `test-map.json` (source-to-test mapping)

### B. Risk-Based Selection

**Purpose**: Prioritize testing on high-risk code.

**Risk Factors**:

| Factor | Source | Default Weight |
|---|---|---|
| Cyclomatic complexity | Static analysis (regex-based) | 0.3 |
| Change frequency | `git log --follow --oneline` over N days | 0.3 |
| Defect history | `git log --grep="fix&#124;bug&#124;defect"` | 0.2 |
| Business criticality | User-defined overrides (glob patterns) → file-path heuristics fallback | 0.2 |

**Risk Levels**:
- `low`: 0-25
- `medium`: 26-50
- `high`: 51-75
- `critical`: 76-100

**Output**: `risk-scores.json` (per-file risk score and level)

### C. Coverage-Based Selection

**Purpose**: Identify gaps where changed code lacks test coverage.

**Process**:
1. Parse existing coverage reports (format depends on language)
2. Filter to changed/impacted files only
3. Identify methods/functions with zero or low coverage
4. Flag uncovered items for new test generation

**Output**: `coverage-gaps.json` (uncovered methods/lines per file)

## Combined Scoring Formula

```
final_score(file) =
    (change_weight * change_relevance) +
    (risk_weight * normalized_risk) +
    (coverage_weight * (1 - current_coverage))
```

Default weights:
- `change_weight`: 0.4
- `risk_weight`: 0.35
- `coverage_weight`: 0.25

Files are ranked by `final_score` descending. Tests are selected for all files above the threshold, ordered by priority.

## Configuration: `.regression-config.json`

Users can override defaults via a configuration file in the project root:

```json
{
  "qualification": {
    "change_based": {
      "enabled": true,
      "impact_depth": 2,
      "include_indirect_dependents": true,
      "change_source": "git diff HEAD~1"
    },
    "risk_based": {
      "enabled": true,
      "min_risk_level": "medium",
      "complexity_threshold": 10,
      "change_frequency_window_days": 90,
      "weights": {
        "complexity": 0.3,
        "change_frequency": 0.3,
        "defect_history": 0.2,
        "business_criticality": 0.2
      },
      "business_criticality": {
        "overrides": {
          "src/payment/**": "critical",
          "src/auth/**": "critical",
          "src/services/orderService.ts": "high"
        },
        "default_level": "medium"
      }
    },
    "coverage_based": {
      "enabled": true,
      "min_coverage_on_changed_code": 80,
      "generate_for_uncovered": true,
      "coverage_format": "auto"
    }
  },
  "test_level": "unit",
  "test_data": {
    "fixtures_dir": "__fixtures__",
    "expected_outputs_dir": "__fixtures__/expected",
    "data_format": "json"
  },
  "traceability": {
    "scenarios_file": "regression-scenarios.yml",
    "requirement_tags": true,
    "tag_prefix": "REQ-",
    "scenario_priority_boost": 20
  },
  "exclusions": {
    "directories": ["node_modules", ".git", "dist", "build", "target"],
    "file_patterns": ["*.generated.*", "*.designer.*", "migrations/*"]
  },
  "execution": {
    "batch_size": 5,
    "max_retries": 3,
    "timeout_seconds": 600,
    "ci_mode": false,
    "report_dir": "./regression-reports",
    "report_formats": ["junit-xml", "json"],
    "test_splitting": {
      "enabled": false,
      "total_shards": 1,
      "shard_index": 0
    },
    "flaky_detection": {
      "enabled": true,
      "retry_count": 2,
      "quarantine_flaky": false
    }
  }
}
```

## User Override Priority

1. **Direct input** when invoking the skill (highest priority)
2. **Config file** (`.regression-config.json`)
3. **Built-in defaults** (lowest priority)

## Criteria Mode

The `criteria_mode` setting controls which criteria are active:

- `all` (default): All three criteria combined
- `change`: Only change-based selection
- `risk`: Only risk-based selection
- `coverage`: Only coverage-based selection

When a single criterion is selected, its weight becomes 1.0 and the others are disabled.
