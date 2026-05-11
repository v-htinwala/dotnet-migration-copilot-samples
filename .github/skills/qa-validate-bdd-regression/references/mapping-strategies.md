# Mapping Strategies

Strategies for mapping BDD feature files to regression test scenarios.

## Strategy 1: Component Name Match (Strongest Signal)

Extract class/component names from regression `target_files` and match against BDD feature conventions.

### Extraction Rules

| Regression Target File | Extracted Component | BDD Feature Pattern |
|---|---|---|
| `...processor/ArtistStatsProcessor.java` | `ArtistStatsProcessor` | `processor/artist-stats-*.feature` |
| `...filter/YearRangeFilter.java` | `YearRangeFilter` | `filter/year-range-*.feature` |
| `...route/AnalyticsRouteBuilder.java` | `AnalyticsRouteBuilder` | `route/analytics-*.feature` |
| `...transform/SongToJsonTransformer.java` | `SongToJsonTransformer` | `transform/song-json-*.feature` |

### Name Normalization

1. Strip path prefix → class name only (e.g., `ArtistStatsProcessor`)
2. Split CamelCase → words (e.g., `Artist`, `Stats`, `Processor`)
3. Convert to kebab-case → `artist-stats-processor`
4. Match against feature file stem using fuzzy prefix/contains

### Confidence: HIGH when class name words appear in feature filename.

---

## Strategy 2: Category Match (Medium Signal)

Map BDD feature directory (category) to regression scenario component types.

| BDD Category (Directory) | Regression Component Types |
|---|---|
| `comparator/` | Classes matching `*Comparator.java` |
| `enricher/` | Classes matching `*Enricher.java` |
| `filter/` | Classes matching `*Filter.java` |
| `formatter/` | Classes matching `*Formatter.java` |
| `processor/` | Classes matching `*Processor.java`, `*Analyzer.java` |
| `report/` | Classes matching `*Report*.java`, `*Generator.java` |
| `route/` | Classes matching `*RouteBuilder.java` |
| `strategy/` | Classes matching `*Strategy.java` |
| `transform/` | Classes matching `*Transformer.java` |
| `validator/` | Classes matching `*Validator.java`, `*Checker.java` |

### Confidence: MEDIUM — category alone narrows but doesn't uniquely identify.

---

## Strategy 3: Behavioral Keyword Match (Supporting Signal)

Compare text from BDD Given/When/Then steps against regression `expected_behaviors`.

### Keyword Extraction

From BDD steps:
```
Given artist filter configured with pattern "beatles"
When the filter evaluates the song
Then the song passes the filter
```
→ Keywords: `artist`, `filter`, `pattern`, `evaluates`, `passes`

From regression behaviors:
```
"ArtistFilter matches partial artist name (case-insensitive contains)"
```
→ Keywords: `ArtistFilter`, `matches`, `partial`, `artist`, `name`, `case-insensitive`

### Overlap Scoring

```
overlap_score = |BDD_keywords ∩ Regression_keywords| / |BDD_keywords ∪ Regression_keywords|
```

- ≥ 0.6 → HIGH confidence
- ≥ 0.3 → MEDIUM confidence  
- ≥ 0.2 → LOW confidence
- < 0.2 → No match

### Stop Words (exclude from matching)

`the`, `a`, `an`, `is`, `are`, `was`, `were`, `be`, `been`, `being`, `have`, `has`,
`had`, `do`, `does`, `did`, `will`, `would`, `shall`, `should`, `may`, `might`,
`can`, `could`, `must`, `and`, `or`, `but`, `not`, `no`, `for`, `with`, `from`,
`to`, `of`, `in`, `on`, `at`, `by`, `that`, `this`, `it`, `its`

---

## Strategy 4: Route Match (Integration Signal)

Map BDD route features to regression scenarios via `target_routes`.

### Route Name Convention

| BDD Route Feature | Expected Route Name Pattern |
|---|---|
| `route/analytics-pipeline.feature` | `analytics-*` |
| `route/export-pipeline.feature` | `export-*` |
| `route/reporting-pipeline.feature` | `reporting-*` |
| `route/transform-pipeline.feature` | `transform-*` |

### Matching

1. Extract route prefix from BDD feature filename: `{name}-pipeline.feature` → prefix = `{name}`
2. Match against regression `target_routes` containing that prefix
3. Confidence: HIGH when route prefix matches.

---

## Composite Confidence Scoring

Combine all strategies:

```
composite_confidence = max(
  component_name_confidence,
  category_confidence + keyword_overlap_bonus,
  route_confidence
)
```

Where `keyword_overlap_bonus`:
- +1 level if keyword overlap ≥ 0.4 AND category matches
- No bonus otherwise

Final mapping confidence:
- **High**: Component name match OR (Category + High keyword overlap) OR Route match
- **Medium**: Category match + Medium keyword overlap
- **Low**: Category match only OR Low keyword overlap only
- **None**: No strategies produce a match
