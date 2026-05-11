---
name: java-spock-test-gen
description: >
  Generate comprehensive BDD-style unit tests for Java projects using the
  Spock Framework. Auto-detects Maven or Gradle, Spring Boot integration,
  and produces Groovy specification files with given/when/then blocks,
  data-driven where: tables, and built-in Spock mocking. Covers Spring
  controllers, services, repositories, utilities, and configuration classes.
  Use when the user needs Spock tests, BDD test generation, Groovy specs,
  Java code coverage improvement, Spring Boot test slicing, data-driven
  tests, or interaction-based verification for a Java project.
license: Proprietary
compatibility: >
  Requires JDK 17+. Works with Maven or Gradle. Expects Spock Framework
  2.x with Groovy 3.x or 4.x. Optional Spring Boot integration via
  spock-spring module.
metadata:
  author: specification-project
  version: "1.0"
---

# Java / Spock BDD Unit Test Generator

Generate high-quality BDD-style unit tests for Java projects using the
Spock Framework with automatic build tool detection, Spring integration
awareness, and coverage-driven gap filling.


## SOURCE CODE PROTECTION -- HARD RULE

**All agents using this skill must ONLY create or modify test files.** Source/production code files must NEVER be modified, edited, or created.

- Only write files under test directories (`src/test/`, `tests/`, `__tests__/`, or matching `*.test.*`/`*.spec.*`/`*Tests.*` patterns)
- NEVER modify files under `src/main/` (Java), `src/` non-test directories (JS/TS), or the main project source directory (.NET)
- If the source code has compilation errors or bugs, report the issue and skip the file -- do not attempt to fix source code
- This rule is absolute and non-negotiable -- no exceptions for "obvious bugs", "typos", or "quick fixes"

## Workflow

### Step 1: Build Tool & Framework Detection

Determine the build tool and Spock configuration:

**Maven detection**:
1. `pom.xml` exists at project root
2. Check for `org.spockframework:spock-core` in `<dependencies>`
3. Check for `org.codehaus.gmavenplus:gmavenplus-plugin` in `<build><plugins>`
4. Check for `org.spockframework:spock-bom` in `<dependencyManagement>`

**Gradle detection**:
1. `build.gradle` or `build.gradle.kts` exists
2. Check for `org.spockframework:spock-core` in `testImplementation`
3. Check for `id 'groovy'` plugin
4. Check for `org.spockframework:spock-bom` in platform dependencies

**Spring integration detection**:
1. `org.spockframework:spock-spring` in dependencies
2. `spring-boot-starter-test` in dependencies
3. Existing test files with `@SpringBootTest`, `@WebMvcTest`, `@DataJpaTest`

**If Spock not configured**: note that setup is needed and provide
dependency snippets (see references/spock-core-patterns.md).

### Step 2: Source File Classification

Scan `src/main/java/` and classify each file by its architectural layer:

| Category | Detection Rule | Test Pattern |
|----------|---------------|-------------|
| Controller | `@RestController` / `@Controller` annotation, or in `controller`/`web`/`rest` package | Use `@WebMvcTest` with `MockMvc`, mock service layer, test HTTP status/response |
| Service | `@Service` annotation, or in `service` package | Plain Spock spec or `@SpringBootTest`, mock repositories/clients, test business logic |
| Repository | `@Repository` / extends `JpaRepository`, or in `repository`/`dao` package | Use `@DataJpaTest` with embedded DB, test queries and data access |
| Component | `@Component` annotation | Mock dependencies, test component behavior |
| Entity | `@Entity` / `@Table`, or in `entity`/`model`/`domain` package | Test validation, custom methods, equals/hashCode |
| DTO | In `dto`/`request`/`response` package, record or POJO | Test mapping, builder patterns; skip if no logic |
| Config | `@Configuration` / `@EnableWebSecurity`, or in `config` package | Use `@SpringBootTest` with test properties, verify bean creation |
| Utility | In `util`/`helper` package, static methods | Pure function testing with `expect:` blocks and `where:` tables |
| Mapper | `@Mapper` (MapStruct), or in `mapper` package | Test field mappings with `where:` tables |
| Exception | Extends `Exception` / `RuntimeException` | Test constructors and custom fields with `expect:` blocks |

For detailed per-category patterns, see the reference files:
- [Spock core patterns](references/spock-core-patterns.md)
- [Spock Spring patterns](references/spock-spring-patterns.md)
- [Spock mocking guide](references/spock-mocking-guide.md)
- [Spring layer testing](references/spring-layer-testing.md)
- [JaCoCo coverage patterns](references/jacoco-coverage-patterns.md)

### Step 3: Test Generation Patterns

For each file category, follow Spock BDD conventions.

**Spec file structure**:

```groovy
package com.example.module

import spock.lang.Specification
import spock.lang.Subject
import spock.lang.Unroll

class TargetClassSpec extends Specification {

    // Dependencies as Mocks
    def dependency = Mock(DependencyType)

    // Subject under test
    @Subject
    def subject = new TargetClass(dependency)

    // --- Feature methods ---

    def "should do X when Y"() {
        given: "preconditions"
        // setup

        when: "the action occurs"
        def result = subject.doSomething(input)

        then: "expected outcome"
        1 * dependency.called(input)
        result == expectedValue
    }

    @Unroll
    def "should return #expected for input #input"() {
        expect:
        subject.transform(input) == expected

        where:
        input   | expected
        "abc"   | "ABC"
        ""      | ""
        null    | null
    }

    def "should throw when input is invalid"() {
        when:
        subject.validate(invalidInput)

        then:
        def ex = thrown(IllegalArgumentException)
        ex.message.contains("invalid")
    }
}
```

**BDD block rules**:
- `given:` (or `setup:`) — preconditions, variable assignment, mock stubbing
- `when:` — single stimulus (the action being tested)
- `then:` — assertions + interaction verifications
- `expect:` — combined when+then for pure functions
- `where:` — data tables for parameterized tests (always last block)
- `and:` — continuation of previous block for readability
- `cleanup:` — resource cleanup (runs even if test fails)

### Step 4: Naming and Placement

**File location** — mirror source package under `src/test/groovy/`:
- Source: `src/main/java/com/example/auth/AuthService.java`
- Spec: `src/test/groovy/com/example/auth/AuthServiceSpec.groovy`

**Naming convention** (detect from existing specs, default to):
- `{ClassName}Spec.groovy` (standard Spock)
- Alternative: `{ClassName}Test.groovy` (if project convention)

**File extension**: Always `.groovy` — Spock specs are Groovy classes.

### Step 5: Custom Instructions Resolution

Check for custom instructions in priority order:

1. **User runtime prompt** — inline instructions in the chat message
2. **Module-specific instructions** — `.github/test-gen-instructions/{module-name}.md`
3. **File-type instructions** — `.github/test-gen-instructions/services.md`, `controllers.md`, etc.
4. **Global instructions** — `.github/test-gen-instructions/global.md`
5. **SKILL.md defaults** — patterns defined in this file and references

Higher priority overrides lower when they conflict.

### Step 6: Coverage Strategy

**JaCoCo metrics** (all four, threshold applies independently):
- Instructions (~Statements)
- Branches (most commonly missed — prioritize)
- Lines
- Methods (~Functions)

**Coverage analysis**:
1. Run test suite with JaCoCo via Maven/Gradle
2. Parse CSV/XML report for per-class coverage
3. For classes below threshold, extract uncovered line/branch ranges from XML
4. Map uncovered lines to methods for targeted spec generation
5. Prioritize classes with largest absolute gap

**Gap-filling strategy**:
- Focus on uncovered **branches** first (if/else, switch, ternary, guard clauses)
- Then uncovered **methods** (dead code check — if truly unused, skip)
- Then remaining **lines** (usually catch blocks, error paths)

See [JaCoCo patterns](references/jacoco-coverage-patterns.md) for detailed setup.

### Step 7: Verification Checklist

After generating specs, verify each file passes these structural checks:

- [ ] No empty feature methods (`def "..."() { }` with no assertions in then:/expect:)
- [ ] No tautological conditions (`true`, `1 == 1` in then: blocks)
- [ ] Every feature has at least one assertion or interaction verification
- [ ] Mocks declared with `Mock()` have interaction verification in `then:` blocks
- [ ] Stubs declared with `Stub()` have return values configured with `>>`
- [ ] BDD blocks are correctly ordered (given → when → then, or expect, where last)
- [ ] `@Unroll` methods have `#variable` placeholders in name and 2+ data rows
- [ ] Exception tests use `thrown(ExceptionType)` in `then:` blocks
- [ ] No `@Ignore` or `@PendingFeature` unless explicitly allowed
- [ ] Custom instruction compliance: base class, annotations, mock patterns
