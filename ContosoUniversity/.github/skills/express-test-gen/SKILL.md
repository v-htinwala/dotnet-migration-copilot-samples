---
name: express-test-gen
description: >
  Generate comprehensive unit tests for Express.js projects using Jest,
  Mocha/Chai, or Vitest. Auto-detects test framework, TypeScript usage,
  and project structure. Produces test files with Supertest for HTTP
  assertions, proper middleware testing, and service/controller isolation.
  Covers routes, controllers, services, middleware, validators, models
  (Mongoose/Sequelize/Prisma), and utility modules. Use when the user needs
  Express API tests, route tests, middleware tests, code coverage improvement,
  Supertest tests, or test scaffolding for an Express.js or Node.js project.
license: Proprietary
compatibility: >
  Requires Node.js 18+. Works with Jest, Mocha/Chai, or Vitest.
  Expects an Express 4.x or 5.x project with package.json.
metadata:
  author: specification-project
  version: "1.0"
---

# Express.js Unit Test Generator

Generate high-quality unit tests for Express.js projects with automatic
framework detection, comprehensive mocking, and coverage-driven gap filling.


## SOURCE CODE PROTECTION -- HARD RULE

**All agents using this skill must ONLY create or modify test files.** Source/production code files must NEVER be modified, edited, or created.

- Only write files under test directories (`src/test/`, `tests/`, `__tests__/`, or matching `*.test.*`/`*.spec.*`/`*Tests.*` patterns)
- NEVER modify files under `src/main/` (Java), `src/` non-test directories (JS/TS), or the main project source directory (.NET)
- If the source code has compilation errors or bugs, report the issue and skip the file -- do not attempt to fix source code
- This rule is absolute and non-negotiable -- no exceptions for "obvious bugs", "typos", or "quick fixes"

## Workflow

### Step 1: Framework Detection

Determine the test runner from project configuration:

**Jest detection** (check in order):
1. `jest` in `package.json` → `devDependencies`
2. `jest.config.ts`, `jest.config.js`, `jest.config.mjs` exists
3. `"test": "jest"` in `package.json` → `scripts`
4. `"jest"` key in `package.json`

**Mocha detection** (check in order):
1. `mocha` in `package.json` → `devDependencies`
2. `.mocharc.yml`, `.mocharc.json`, `.mocharc.js` exists
3. `"test": "mocha"` in `package.json` → `scripts`
4. `chai` in `devDependencies` (commonly paired with Mocha)

**Vitest detection** (check in order):
1. `vitest` in `package.json` → `devDependencies`
2. `vitest.config.ts`, `vitest.config.js` exists
3. `"test": "vitest"` in `package.json` → `scripts`

**If multiple present**: prefer Jest (most common in Express ecosystem).
**If none present**: default to Jest and note that setup is needed.

**TypeScript detection**:
1. `typescript` in `devDependencies`
2. `tsconfig.json` exists
3. Source files have `.ts` extension
4. `ts-jest` or `ts-node` in `devDependencies`

**Supertest detection**:
1. `supertest` in `devDependencies`
2. If not present: note that it should be installed for HTTP testing

### Step 2: Project Structure Detection

Scan the project to understand the Express application layout:

**App initialization patterns**:
- `app.js` / `app.ts` — Express app instance
- `server.js` / `server.ts` — HTTP server startup (separate from app)
- `index.js` / `index.ts` — combined app + server
- Key: identify where `express()` is called and exported

**Directory patterns** (detect from existing structure):
- `routes/` or `routers/` — route definitions
- `controllers/` — request handlers (separated from routes)
- `services/` — business logic layer
- `middleware/` or `middlewares/` — Express middleware
- `models/` — database models (Mongoose, Sequelize, Prisma)
- `validators/` — input validation (Joi, Zod, express-validator)
- `utils/` or `helpers/` — utility functions
- `config/` — configuration files

### Step 3: File Classification

Scan source files and classify each into a testing category:

| Category | Detection Rule | Test Pattern |
|----------|---------------|-------------|
| Route / Router | `express.Router()`, `app.get/post/put/delete` | Supertest against mounted router, mock controller/service |
| Controller | In `controllers/`, exports request handler functions `(req, res, next)` | Mock req/res objects or use Supertest, mock service layer |
| Service | In `services/`, business logic functions | Mock repositories/clients, test business logic directly |
| Middleware | In `middleware/`, `(req, res, next)` signature | Mock req/res/next, test side effects and flow control |
| Validator | Joi/Zod schemas, express-validator chains | Test with valid/invalid inputs, assert validation errors |
| Model (Mongoose) | `mongoose.model()`, `Schema({})` | Mock with `mockingoose` or test with MongoDB Memory Server |
| Model (Sequelize) | `sequelize.define()`, extends `Model` | Mock with `sequelize-mock` or in-memory SQLite |
| Model (Prisma) | `PrismaClient` usage | Mock with `jest-mock-extended` on PrismaClient |
| Error Handler | `(err, req, res, next)` — 4-arg middleware | Test with various error types, assert response format |
| Configuration | Env/config loading, `dotenv` usage | Test with env variable overrides |
| Utility | In `utils/`, pure functions | Test as pure functions with multiple inputs |

### Step 4: Test Generation Patterns

For each file category, follow the patterns below. Adapt import syntax
based on detected framework (Jest vs Mocha vs Vitest).

**Jest test structure**:
```typescript
import request from 'supertest';
import app from '../app';

describe('GET /api/users', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return 200 with user list', async () => {
    const response = await request(app)
      .get('/api/users')
      .expect(200);

    expect(response.body).toHaveLength(2);
    expect(response.body[0]).toHaveProperty('name');
  });

  it('should return 500 on service error', async () => {
    mockUserService.getAll.mockRejectedValue(new Error('DB error'));

    const response = await request(app)
      .get('/api/users')
      .expect(500);

    expect(response.body).toHaveProperty('error');
  });
});
```

**Mocha/Chai test structure**:
```typescript
import request from 'supertest';
import { expect } from 'chai';
import sinon from 'sinon';
import app from '../app';

describe('GET /api/users', () => {
  afterEach(() => {
    sinon.restore();
  });

  it('should return 200 with user list', async () => {
    const response = await request(app)
      .get('/api/users')
      .expect(200);

    expect(response.body).to.have.lengthOf(2);
    expect(response.body[0]).to.have.property('name');
  });
});
```

For detailed patterns per category, see the reference files:
- [Jest / Mocha / Vitest patterns](references/jest-mocha-vitest-patterns.md)
- [Supertest & HTTP testing patterns](references/supertest-patterns.md)
- [Express mocking guide](references/express-mocking-guide.md)
- [Express layer testing](references/express-layer-testing.md)
- [Istanbul/c8 coverage patterns](references/istanbul-c8-coverage-patterns.md)

### Step 5: Naming and Placement

**Detect project convention** by checking for existing test files:
1. Co-located: `src/services/user.service.ts` → `src/services/user.service.test.ts`
2. `__tests__` directory: `src/services/__tests__/user.service.test.ts`
3. Top-level `test/` or `tests/`: `test/services/user.service.test.ts`

**If no existing tests**: default to co-located (`*.test.ts` next to source).

**File extension rules**:
- TypeScript source → `.test.ts`
- JavaScript source → `.test.js`
- Match source language for test files

### Step 6: Custom Instructions Resolution

Check for custom instructions in priority order:

1. **User runtime prompt** — inline instructions in the chat message
2. **Module-specific instructions** — `.github/test-gen-instructions/{module-name}.md`
3. **File-type instructions** — `.github/test-gen-instructions/routes.md`, `middleware.md`, etc.
4. **Global instructions** — `.github/test-gen-instructions/global.md`
5. **SKILL.md defaults** — patterns defined in this file and references

Higher priority overrides lower when they conflict.

### Step 7: Coverage Strategy

**Istanbul/c8 metrics** (all four, threshold applies independently):
- Statements
- Branches (most commonly missed — prioritize)
- Functions
- Lines

**Coverage analysis**:
1. Run test suite with coverage (`jest --coverage` or `c8 mocha`)
2. Parse `coverage/coverage-summary.json` or `coverage/lcov.info`
3. For files below threshold, extract uncovered line/branch ranges
4. Map uncovered lines to functions for targeted test generation
5. Prioritize files with largest absolute gap

**Gap-filling strategy**:
- Focus on uncovered **branches** first (if/else, switch, ternary, early returns)
- Then uncovered **functions** (dead code check — if truly unused, skip)
- Then remaining **lines** (usually catch blocks, error middleware paths)

See [Istanbul/c8 patterns](references/istanbul-c8-coverage-patterns.md) for detailed setup.

### Step 8: Verification Checklist

After generating tests, verify each file passes these structural checks:

- [ ] No empty test bodies (`it('...', () => {})` with no assertions)
- [ ] No tautological assertions (`expect(true).toBe(true)`)
- [ ] Every test has at least one assertion (`expect()`, `assert()`, or Supertest `.expect()`)
- [ ] Mocks that are created are also verified (`.toHaveBeenCalled()`, `sinon.assert.called()`)
- [ ] Supertest tests assert both status code AND response body
- [ ] Async tests use `async/await` or return a Promise
- [ ] Edge cases are covered: missing params, invalid body, auth failures, DB errors
- [ ] Custom instruction compliance: correct imports, correct mock patterns
- [ ] No `.skip` or `.only` unless explicitly allowed
- [ ] Database connections are properly mocked — no real DB calls in unit tests
- [ ] `app` is imported separately from `server` to avoid port binding in tests
