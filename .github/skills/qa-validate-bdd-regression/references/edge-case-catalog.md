# Edge Case Catalog

Common edge cases to check for during BDD vs. regression validation. Use this catalog to verify both BDD and regression scenarios cover critical boundary conditions.

## Universal Edge Cases

These apply across all component types:

| Edge Case | Check In BDD | Check In Regression | Priority |
|---|---|---|---|
| **Null input** | Given step with null value | Expected behavior mentions null handling | High |
| **Empty string input** | Given step with empty/blank value | Expected behavior mentions empty handling | High |
| **Boundary values** | Scenario with min/max values | Expected behavior with boundary conditions | High |
| **Out-of-range values** | Scenario with values outside valid range | Expected behavior for rejection | Medium |
| **Special characters** | Scenario with quotes, ampersands, angle brackets | Expected behavior for escaping | Medium |
| **Concurrent access** | Scenario with thread safety | Expected behavior for consistency | Medium |
| **Empty collection** | Scenario with no input records | Expected behavior for empty processing | Medium |
| **Single item** | Scenario with exactly one record | Expected behavior for single-item handling | Low |
| **Duplicate input** | Scenario with repeated data | Expected behavior for deduplication | Medium |
| **Large input** | Scenario with high volume | Expected behavior for scalability | Low |

## Domain-Specific Edge Cases

### Filters
| Edge Case | Description |
|---|---|
| Null field being filtered | Filter target field is null |
| Empty pattern/keyword | Filter pattern is empty string |
| Case sensitivity | Mixed case input vs. pattern |
| Exact vs. partial match | Substring vs. full string matching |
| Wildcard/regex patterns | Pattern contains special regex chars |

### Processors / Analyzers
| Edge Case | Description |
|---|---|
| First record (initialization) | No prior state exists |
| Running averages | Numeric precision across many records |
| Year/date boundaries | Year = 0, negative year, future year |
| Reset/clear state | Processor state after reset |
| Lookup miss | Query for non-existent entry |

### Transformers
| Edge Case | Description |
|---|---|
| Special character escaping | JSON: `\`, `"`, `\n`, `\t`; XML: `&`, `<`, `>`, `"`, `'` |
| Null field in output | Output format handles null gracefully |
| Timestamp presence | Export records include timestamps |
| Format metadata | Output tagged with correct format type |

### Validators
| Edge Case | Description |
|---|---|
| Multiple simultaneous errors | Record with 3+ validation failures |
| Boundary values (inclusive) | Values at exact boundary (e.g., year=1900, rank=100) |
| Valid rate calculation | Ratio of valid to total records |
| Error message specificity | Each validation failure has distinct message |

### Aggregation Strategies
| Edge Case | Description |
|---|---|
| First aggregation (null old exchange) | Initial aggregation creates new state |
| Concurrent aggregation | Multiple exchanges aggregating simultaneously |
| Top/best tracking | Correct identification of min/max entries |
| Group with single member | Aggregation group with exactly one record |

### Routes / Pipelines
| Edge Case | Description |
|---|---|
| Empty input file | Pipeline processes empty CSV |
| Malformed records | Pipeline handles parse errors gracefully |
| Multicast fan-out | All branches receive records |
| Error propagation | Errors in one branch don't stop others |

## Validation Status Values

When checking edge cases across BDD and regression:

| Status | Symbol | Meaning |
|---|---|---|
| Both tested | ✅ | Edge case has BDD scenario AND regression expected behavior |
| BDD only | ⚠️ | Edge case has BDD scenario but no regression expected behavior |
| Regression only | ⚠️ | Edge case has regression expected behavior but no BDD scenario |
| Neither tested | ❌ | Critical gap — edge case not tested anywhere |
