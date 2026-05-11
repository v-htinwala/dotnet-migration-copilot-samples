# Validation Report Template

Use this template structure when generating the markdown validation report.
Variables in `{{double_braces}}` are replaced at generation time.

---

```markdown
# BDD-Regression Test Validation Report
**Date**: {{timestamp}}
**Project**: {{project_name}}
**Scope**: {{bdd_feature_count}} BDD Feature Files vs. {{regression_scenario_count}} Regression Scenarios
**Validation Dimensions**: {{active_dimensions}}

---

## Executive Summary

| Metric | Result | Status |
|--------|--------|--------|
| **Forward Coverage** | {{forward_covered}}/{{bdd_total}} BDD features mapped | {{forward_status}} |
| **Backward Coverage** | {{backward_covered}}/{{regression_total}} regression scenarios mapped | {{backward_status}} |
| **Consistency Findings** | {{consistency_count}} findings | {{consistency_status}} |
| **Traceability Completeness** | {{req_id_covered}}/{{req_id_total}} requirement IDs validated | {{traceability_status}} |
| **Component Coverage** | {{component_covered}}/{{component_total}} components tested | {{component_status}} |
| **Pipeline Coverage** | {{pipeline_covered}}/{{pipeline_total}} pipelines represented | {{pipeline_status}} |
| **Overall Validation Status** | **{{overall_status}}** | {{overall_badge}} |

**Key Findings**:
{{#each key_findings}}
- {{status_icon}} {{description}}
{{/each}}

---

## 1. COVERAGE ANALYSIS

### 1.1 Forward Coverage Matrix (BDD Features → Regression Scenarios)

| # | BDD Feature | Category | Mapped to Regression Scenario | Coverage Status |
|----|------------|----------|-------------------------------|-----------------|
{{#each forward_mappings}}
| {{index}} | {{bdd_feature}} | {{category}} | {{regression_scenario}} | {{status}} |
{{/each}}

**Coverage Result**: **{{forward_covered}}/{{bdd_total}} ({{forward_pct}}%)** 

### 1.2 Backward Coverage Matrix (Regression Scenarios → BDD Features)

| # | Regression Scenario | Priority | BDD Features | Coverage |
|----|-------------------|----------|-------------|----------|
{{#each backward_mappings}}
| {{index}} | {{regression_scenario}} | {{priority}} | {{bdd_features}} | {{status}} |
{{/each}}

**Coverage Result**: **{{backward_covered}}/{{regression_total}} ({{backward_pct}}%)**

### 1.3 Category Coverage Breakdown

| Category | # Features | Regression Scenarios | Coverage % |
|----------|-----------|---------------------|-----------|
{{#each categories}}
| **{{name}}** | {{feature_count}} | {{scenarios}} | {{coverage_pct}}% |
{{/each}}

### 1.4 Coverage Verdict

{{coverage_verdict}}

---

## 2. TRACEABILITY MATRIX

{{#each traceability_groups}}
### 2.{{index}} {{group_name}}

| BDD Feature | Scenario | Req ID | Target Files | Routes | Confidence |
|-------------|----------|--------|---|---|---|
{{#each mappings}}
| {{bdd_feature}} | {{scenario}} | {{req_id}} | {{target_files}} | {{routes}} | {{confidence}} |
{{/each}}
{{/each}}

### Traceability Verdict

{{traceability_verdict}}

---

## 3. CONSISTENCY & CORRECTNESS ANALYSIS

### 3.1 Behavioral Alignment Check

{{#each consistency_findings}}
#### {{status_icon}} {{title}}

| Aspect | BDD Expectation | Regression Expectation | Status |
|--------|---------|-----------|--------|
{{#each details}}
| **{{aspect}}** | {{bdd}} | {{regression}} | {{status}} |
{{/each}}
{{/each}}

### 3.2 Edge Case Coverage Matrix

| Edge Case | BDD Coverage | Regression Coverage | Both Tested | Gap |
|-----------|-------------|-----------|-----|-----|
{{#each edge_cases}}
| **{{name}}** | {{bdd_status}} | {{regression_status}} | {{both}} | {{gap}} |
{{/each}}

### 3.3 Consistency & Correctness Verdict

{{consistency_verdict}}

---

## 4. COMPLETENESS ASSESSMENT

### 4.1 Component Coverage

| Component Type | Count | All Tested? | Test Level |
|--------|-------|-----|-----|
{{#each components}}
| **{{type}}** | {{count}} | {{tested}} | {{level}} |
{{/each}}

### 4.2 Pipeline Coverage

| Pipeline | Route Name | BDD Feature | Regression Scenario | E2E Test | Status |
|----------|-----------|----------|--------|-----|--------|
{{#each pipelines}}
| **{{name}}** | {{route}} | {{bdd_feature}} | {{regression_scenario}} | {{e2e}} | {{status}} |
{{/each}}

### 4.3 Critical Path Analysis

{{#each critical_paths}}
**Critical Path {{index}}: {{name}}**
```
{{flow_diagram}}
```
{{/each}}

### 4.4 Completeness Verdict

{{completeness_verdict}}

---

## 5. DETAILED GAPS & RECOMMENDATIONS

{{#each gap_tiers}}
### 5.{{index}} {{tier_name}} Recommendations

{{#each gaps}}
#### Recommendation #{{rec_index}}: {{title}}

**Finding**: {{finding}}

**Suggested BDD Addition**:
```gherkin
{{suggested_scenario}}
```

**Impact**: {{impact}}
**Effort**: {{effort}}
**Priority**: {{priority_tier}}

---
{{/each}}
{{/each}}

## 6. SUMMARY & NEXT STEPS

### 6.1 Validation Results

| Dimension | Findings | Risk Level | Status |
|-----------|----------|-----------|--------|
{{#each dimension_results}}
| **{{name}}** | {{findings}} | {{risk}} | {{status}} |
{{/each}}

### 6.2 Risk Assessment

| Risk Category | Assessment |
|---------------|-----------|
{{#each risks}}
| **{{category}}** | {{assessment}} |
{{/each}}

### 6.3 Conclusion

{{conclusion}}

---

## Appendix A: File References

### BDD Feature Files ({{bdd_total}} total)
{{#each bdd_files}}
- `{{path}}`
{{/each}}

### Regression Scenarios
- `{{regression_file_path}}` ({{regression_total}} scenarios)

---

**Report Generated**: {{timestamp}}
**Validation Status**: {{overall_status}}
```
