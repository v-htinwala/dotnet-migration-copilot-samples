---
name: angular-test-gen
description: >
  Generate comprehensive unit tests for Angular projects using Jasmine/Karma
  or Jest. Auto-detects test framework, Angular version, and project structure.
  Produces TypeScript spec files with TestBed configuration, component
  harnesses, HttpClientTestingModule, and RouterTestingModule. Covers
  components, services, pipes, directives, guards, resolvers, interceptors,
  and utility classes. Use when the user needs Angular unit tests, spec
  file generation, code coverage improvement, TestBed tests, service tests,
  or test scaffolding for an Angular project.
license: Proprietary
compatibility: >
  Requires Node.js 18+. Works with Jasmine/Karma or Jest.
  Expects an Angular 16+ project with angular.json.
metadata:
  author: specification-project
  version: "1.0"
---

# Angular Unit Test Generator

Generate high-quality unit tests for Angular projects with automatic
framework detection, comprehensive TestBed configuration, and
coverage-driven gap filling.


## SOURCE CODE PROTECTION -- HARD RULE

**All agents using this skill must ONLY create or modify test files.** Source/production code files must NEVER be modified, edited, or created.

- Only write files under test directories (`src/test/`, `tests/`, `__tests__/`, or matching `*.test.*`/`*.spec.*`/`*Tests.*` patterns)
- NEVER modify files under `src/main/` (Java), `src/` non-test directories (JS/TS), or the main project source directory (.NET)
- If the source code has compilation errors or bugs, report the issue and skip the file -- do not attempt to fix source code
- This rule is absolute and non-negotiable -- no exceptions for "obvious bugs", "typos", or "quick fixes"

## Workflow

### Step 1: Framework Detection

Determine the test runner from project configuration:

**Jasmine/Karma detection** (check in order):
1. `karma.conf.js` or `karma.conf.ts` exists
2. `@angular-devkit/build-angular:karma` in `angular.json` → `test` architect
3. `jasmine-core` and `karma` in `package.json` → `devDependencies`
4. `src/test.ts` bootstrap file exists

**Jest detection** (check in order):
1. `jest.config.ts`, `jest.config.js` exists
2. `@angular-builders/jest` in `package.json` → `devDependencies`
3. `jest-preset-angular` in `package.json`
4. `@angular-devkit/build-angular:jest` in `angular.json` (Angular 16+)

**If both present**: prefer Jest (faster, better watch mode, snapshot support).
**If neither present**: default to Jasmine/Karma and note that setup is needed.

**Angular version detection**:
1. Check `@angular/core` version in `package.json`
2. Determines available APIs: signals (16+), standalone (15+), inject() (14+)

### Step 2: Project Structure Detection

Scan the Angular workspace to understand the project layout:

**Workspace indicators**:
- `angular.json` → `projects` section for monorepo/multi-project
- `src/app/` for standard single-project structure
- `libs/` for Nx workspace libraries

**Module structure detection**:
- Standalone components (no NgModule): Angular 15+
- NgModule-based: traditional Angular structure
- Mixed: both patterns coexist

### Step 3: File Classification

Scan source files and classify each into a testing category:

| Category | Detection Rule | Test Pattern |
|----------|---------------|-------------|
| Component | `@Component` decorator, `.component.ts` suffix | TestBed with component fixture, template assertions, event testing |
| Service | `@Injectable` decorator, `.service.ts` suffix | TestBed or direct instantiation, mock dependencies with `jasmine.createSpyObj` |
| Pipe | `@Pipe` decorator, `.pipe.ts` suffix | Direct instantiation, test `transform()` with various inputs |
| Directive | `@Directive` decorator, `.directive.ts` suffix | Test host component, verify DOM changes |
| Guard | `@Injectable` with `CanActivate`/etc, `.guard.ts` suffix | Mock `ActivatedRouteSnapshot` and `RouterStateSnapshot`, test return values |
| Resolver | `@Injectable` with `Resolve`, `.resolver.ts` suffix | Mock services, test data fetching |
| Interceptor | `@Injectable` with `HttpInterceptor`, `.interceptor.ts` suffix | Mock `HttpHandler`, test request/response transformation |
| Module | `@NgModule`, `.module.ts` suffix | Skip — test individual declarations instead |
| Model / Interface | `.model.ts`, `.interface.ts` suffix | Skip unless contains logic; test factory methods if any |
| Utility | `.util.ts`, `.helper.ts`, static methods | Test as pure functions with multiple inputs |
| Store (NgRx) | `@ngrx/store` actions/reducers/selectors/effects | Test reducers as pure functions, effects with `provideMockActions` |

### Step 4: Test Generation Patterns

For each file category, follow the patterns below. Adapt based on detected
framework (Jasmine vs Jest).

**Jasmine spec structure**:
```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MyComponent } from './my.component';

describe('MyComponent', () => {
  let component: MyComponent;
  let fixture: ComponentFixture<MyComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      // For standalone components (Angular 15+):
      imports: [MyComponent],
      // For NgModule components:
      // declarations: [MyComponent],
      // imports: [SharedModule],
      providers: [
        { provide: MyService, useValue: jasmine.createSpyObj('MyService', ['getData']) }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(MyComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('rendering', () => {
    // Template assertions
  });

  describe('interactions', () => {
    // User interaction tests
  });

  describe('edge cases', () => {
    // Null, undefined, empty, error states
  });
});
```

**Jest spec structure** (differences from Jasmine):
```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MyComponent } from './my.component';

// Jest uses jest.fn() instead of jasmine.createSpy()
// Jest uses jest.spyOn() instead of spyOn()

describe('MyComponent', () => {
  // Same TestBed setup pattern
  // Assertions: expect(x).toBe(y) — same API
  // Mocks: jest.fn(), jest.spyOn()
});
```

For detailed patterns per category, see the reference files:
- [Jasmine/Karma patterns](references/jasmine-karma-patterns.md)
- [Angular TestBed patterns](references/angular-testbed-patterns.md)
- [Angular mocking guide](references/angular-mocking-guide.md)
- [Angular layer testing](references/angular-layer-testing.md)
- [Istanbul coverage patterns](references/istanbul-coverage-patterns.md)

### Step 5: Naming and Placement

**Angular convention** (co-located specs):
- Source: `src/app/users/user.service.ts` → Test: `src/app/users/user.service.spec.ts`
- Source: `src/app/shared/pipes/format.pipe.ts` → Test: `src/app/shared/pipes/format.pipe.spec.ts`

**File naming rules**:
- Always use `.spec.ts` extension (Angular CLI convention)
- Spec file name mirrors source file name exactly
- Co-located in the same directory as the source file

### Step 6: Custom Instructions Resolution

Check for custom instructions in priority order:

1. **User runtime prompt** — inline instructions in the chat message
2. **Module-specific instructions** — `.github/test-gen-instructions/{module-name}.md`
3. **File-type instructions** — `.github/test-gen-instructions/components.md`, `services.md`, etc.
4. **Global instructions** — `.github/test-gen-instructions/global.md`
5. **SKILL.md defaults** — patterns defined in this file and references

Higher priority overrides lower when they conflict.

### Step 7: Coverage Strategy

**Istanbul/Karma metrics** (all four, threshold applies independently):
- Statements
- Branches (most commonly missed — prioritize)
- Functions
- Lines

**Coverage analysis**:
1. Run `ng test --code-coverage` to generate Istanbul report
2. Parse `coverage/lcov.info` or `coverage/coverage-summary.json`
3. For files below threshold, extract uncovered line/branch ranges
4. Map uncovered lines to functions for targeted test generation
5. Prioritize files with largest absolute gap

**Gap-filling strategy**:
- Focus on uncovered **branches** first (if/else, switch, ternary, `ngIf` template branches)
- Then uncovered **functions** (dead code check — if truly unused, skip)
- Then remaining **lines** (usually error handling paths, subscription callbacks)

See [Istanbul patterns](references/istanbul-coverage-patterns.md) for detailed setup.

### Step 8: Verification Checklist

After generating specs, verify each file passes these structural checks:

- [ ] No empty test bodies (`it('...', () => {})` with no assertions)
- [ ] No tautological assertions (`expect(true).toBeTruthy()`, `expect(1).toBe(1)`)
- [ ] Every test has at least one `expect()` call
- [ ] Spy objects that are created are also verified (`toHaveBeenCalled`, `toHaveBeenCalledWith`)
- [ ] Components that are rendered have `fixture.detectChanges()` before assertions
- [ ] Async tests use `fakeAsync/tick`, `waitForAsync`, or `done` callback
- [ ] `HttpClientTestingModule` is used for HTTP calls, not real `HttpClientModule`
- [ ] Edge cases are covered: null inputs, empty arrays, error throws, HTTP errors
- [ ] Custom instruction compliance: correct imports, correct providers, correct mock patterns
- [ ] No `xit`, `xdescribe`, or `pending()` unless explicitly allowed
- [ ] TestBed providers are reset properly between tests (no shared mutable state)
