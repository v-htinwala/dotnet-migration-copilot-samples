---
name: java-spring-unit-testing
description: >
  This skill should be used when the user asks to "generate unit tests",
  "write JUnit tests", "create test cases for Java", "test my Spring service",
  "test my controller", "test my RestClient", "add Mockito tests",
  "unit test this class", "test Spring 6 class", or needs guidance on
  generating high-quality JUnit 5 + Mockito unit tests for Java 21 /
  Spring Framework 6.x codebases. Covers @Service, @RestController,
  @Repository, MapStruct mappers, validators, security filters, schedulers,
  and event listeners. Excludes POJOs, entities, DTOs, and config-only classes.
version: 0.1.0
---

# Java 21 / Spring 6.x Unit Test Generation

Generate focused, high-quality unit tests using **JUnit 5** and **Mockito** for
Java 21 Spring Framework 6.x codebases. Tests must prove business-rule
correctness, mapping accuracy, and integration-point behaviour — not just that
code runs without NPEs.


## SOURCE CODE PROTECTION -- HARD RULE

**All agents using this skill must ONLY create or modify test files.** Source/production code files must NEVER be modified, edited, or created.

- Only write files under test directories (`src/test/`, `tests/`, `__tests__/`, or matching `*.test.*`/`*.spec.*`/`*Tests.*` patterns)
- NEVER modify files under `src/main/` (Java), `src/` non-test directories (JS/TS), or the main project source directory (.NET)
- If the source code has compilation errors or bugs, report the issue and skip the file -- do not attempt to fix source code
- This rule is absolute and non-negotiable -- no exceptions for "obvious bugs", "typos", or "quick fixes"

## Scope Rules

### MUST test

- `@Service` classes (business logic, orchestration)
- `@RestController` endpoints (request/response mapping, status codes, error responses)
- `@Repository` custom query methods (not Spring Data auto-generated CRUD)
- MapStruct or manual DTO ↔ Entity mappers (field-by-field value assertions)
- Custom validators (`ConstraintValidator` implementations)
- Spring Security filters and auth components
- `@Scheduled` methods (invocation and side-effects)
- `@EventListener` methods (event handling and downstream calls)

### MUST skip

- POJOs, entities, DTOs, records, enums (no standalone tests)
- Config classes (`@Configuration`, `@Bean` factories)
- Constants / utility classes with only static final fields
- Auto-generated code (Lombok, MapStruct implementations — test the *interface* contract instead)

## Core Quality Rules

Apply every rule to every generated test. Violations are defects.

### 1. No hollow assertions

```java
// FORBIDDEN — proves nothing
assertNotNull(result);
assertTrue(result instanceof Foo);

// REQUIRED — prove the actual value
assertEquals("expected-value", result.getName());
assertThat(result.getItems()).containsExactly(item1, item2);
```

Replace every `assertNotNull(x)` with a value-level assertion on `x`.
Replace every `assertTrue(x instanceof T)` with `assertInstanceOf(T.class, x)` plus value assertions.

### 2. No try-catch exception swallowing

```java
// FORBIDDEN — hides failure details and masks unexpected exceptions
try {
    service.process(invalidInput);
    fail("expected exception");
} catch (BusinessException e) {
    assertEquals("msg", e.getMessage());
}

// REQUIRED — separate, explicit error scenario
@Test
void process_invalidInput_throwsBusinessException() {
    assertThrows(BusinessException.class,
        () -> service.process(invalidInput));
}

// Or with message verification:
@Test
void process_invalidInput_throwsWithMessage() {
    var ex = assertThrows(BusinessException.class,
        () -> service.process(invalidInput));
    assertEquals("Invalid input: xyz", ex.getMessage());
}
```

Each error scenario gets its own `@Test` method with `assertThrows`.

### 3. No redundant tests

Before writing a test, check: does another test already exercise this exact input → output path? If yes, skip it. Common redundancies to avoid:

- Multiple tests differing only by field name on the same happy-path flow
- Null-check tests when null is impossible (constructor-injected, `@NonNull`)
- Default-value tests for fields with no default logic

### 4. Meaningful assertions that prove correctness

Every `@Test` must assert at least one of:

| What to prove | Example assertion |
|---|---|
| Mapping correctness | `assertEquals(source.getEmail(), dto.getEmail())` |
| Parsing correctness | `assertEquals(LocalDate.of(2024,1,1), parsed.getDate())` |
| Business rule | `assertEquals(BigDecimal.valueOf(110), result.getTotalWithTax())` |
| HTTP response shape | `assertEquals(HttpStatus.CREATED, response.getStatusCode())` |
| Interaction happened | `verify(repository).save(captor.capture()); assertEquals(...)` |
| Error contract | `assertThrows(NotFoundException.class, ...)` |

### 5. Verify HTTP client interactions

For **RestClient**, **WebClient**, and **RestTemplate**:

- Verify the correct URI, HTTP method, headers, and body are sent
- Mock the response and assert the parsed result
- Test error responses (4xx, 5xx) as separate `@Test` methods
- Use `ArgumentCaptor` or chained mock verification to inspect request details

See `references/http-client-testing.md` for detailed patterns per client type.

### 6. Test structure

```java
@ExtendWith(MockitoExtension.class)
class FooServiceTest {

    @Mock private BarRepository barRepository;
    @Mock private RestClient restClient;
    @InjectMocks private FooService fooService;

    @Test
    void methodName_stateUnderTest_expectedBehaviour() {
        // Arrange
        ...
        // Act
        var result = fooService.doSomething(input);
        // Assert
        assertEquals(...);
        verify(barRepository).save(any());
    }
}
```

- Use `@ExtendWith(MockitoExtension.class)` + `@Mock` / `@InjectMocks`
- Naming: `methodName_condition_expectedResult`
- Arrange / Act / Assert structure in every test
- One logical assertion group per test (multiple `assertEquals` on the same object is fine)

## Workflow

Follow these steps in order. Complete and verify each step before moving on.

### Step 1 — Identify targets

Read the source file. Classify it (Service / Controller / Repository / Mapper / Validator / Filter / Scheduler / Listener). If it is a POJO/entity/DTO/config, stop — do not generate tests.

### Step 2 — Inventory behaviours

List every public method. For each method, enumerate:

1. Happy-path scenarios (distinct input categories)
2. Edge cases (empty collections, boundary values)
3. Error scenarios (exceptions, validation failures)
4. External interactions to verify (repository calls, HTTP calls, event publishing)

If a method is complex (>3 branches), break it into sub-behaviours and list each.

### Step 3 — Deduplicate

Review the inventory. Remove scenarios that duplicate another scenario's input → output path. Keep the most specific test.

### Step 4 — Generate tests

For each remaining scenario, write one `@Test` method. Apply all Core Quality Rules. If the test class exceeds ~25 tests, split into inner `@Nested` classes by method or feature area.

### Step 5 — Verify interactions

For every mocked dependency call in the source:

- Add `verify(mock).method(...)` with argument matchers or captors
- If the argument matters (e.g., entity being saved), use `ArgumentCaptor` and assert captured values

### Step 6 — Compile check (mental)

Scan the generated test for: missing imports, wrong mock setup for fluent APIs (RestClient builder chains), unconfigured `when(...)` stubs, type mismatches. Fix before presenting.

## Breaking Down Large Classes

When a class under test has >5 public methods or >10 behavioural scenarios:

1. Generate tests for the first 2-3 methods → present for review
2. Continue with the next batch after confirmation
3. Never generate all tests in a single pass for large classes

## Additional Resources

### Reference Files

For detailed patterns, consult:
- **`references/anti-patterns.md`** — Exhaustive catalogue of forbidden test patterns with rationale
- **`references/patterns-by-layer.md`** — Layer-specific test patterns: Service, Controller, Repository, Mapper, Validator, Security, Scheduler, EventListener
- **`references/http-client-testing.md`** — RestClient, WebClient, and RestTemplate mock/verify patterns with fluent API chain setup
