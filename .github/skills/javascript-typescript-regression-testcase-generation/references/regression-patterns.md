# JavaScript/TypeScript Regression Testing Patterns

## Common Regression Scenarios

### 1. Service/Module Export Changes
When a module's exported functions or classes are modified:
- Verify all exported functions still produce correct output for known inputs
- Check that downstream importers receive the same API contracts
- Validate that error/exception behavior is preserved
- Confirm mock interactions with dependencies remain correct

### 2. Express/Fastify Route Handler Changes
When a route handler or middleware is modified:
- Verify HTTP status codes remain unchanged for existing request patterns
- Check response body structure (field names, types, nullability)
- Validate request parameter validation rules still apply
- Test authentication/authorization middleware behavior is preserved
- **For `test_level=integration`**: use `supertest` with the actual Express/Fastify app instead of mocking (see Integration Patterns below)

### 3. React Component Changes
When a React component is modified:
- Verify rendered output matches expected structure (snapshot regression)
- Check that props are handled the same way
- Validate event handlers fire correctly
- Test conditional rendering logic is preserved
- Verify hooks behavior hasn't changed

### 4. Data Access/Repository Changes
When a database access layer or API client is modified:
- Verify query results match expected data
- Check that CRUD operations maintain data integrity
- Validate error handling for network/database failures
- Test retry and timeout behavior
- **For `test_level=integration`**: use Testcontainers or in-memory DB (SQLite) for real data layer testing (see Integration Patterns below)

### 5. TypeScript Type/Interface Changes
When TypeScript types or interfaces are modified:
- Verify that consumers still compile (type-level regression)
- Check that runtime validators (zod, yup, io-ts) still work
- Test serialization/deserialization with changed types

### 6. Configuration/Environment Changes
When config loading or environment handling changes:
- Verify default values are preserved
- Check that environment variable parsing is unchanged
- Test fallback behavior
- **For `test_level=integration`**: verify app boots correctly with real config loading (see Integration Patterns below)

## Jest Regression Test Structure

```javascript
// userService.test.ts
import { UserService } from '../userService';
import { UserRepository } from '../userRepository';
import { EmailService } from '../emailService';

jest.mock('../userRepository');
jest.mock('../emailService');

describe('Regression: UserService', () => {
  let userService: UserService;
  let mockUserRepo: jest.Mocked<UserRepository>;
  let mockEmailService: jest.Mocked<EmailService>;

  beforeEach(() => {
    jest.clearAllMocks();
    mockUserRepo = new UserRepository() as jest.Mocked<UserRepository>;
    mockEmailService = new EmailService() as jest.Mocked<EmailService>;
    userService = new UserService(mockUserRepo, mockEmailService);
  });

  // --- Behavior Preservation Tests ---

  describe('createUser - behavior preservation', () => {
    test('still returns user with generated ID', async () => {
      // Arrange
      mockUserRepo.save.mockResolvedValue({ id: '1', email: 'test@example.com' });

      // Act
      const result = await userService.createUser({ email: 'test@example.com', name: 'Test' });

      // Assert
      expect(result).toBeDefined();
      expect(result.id).toBeDefined();
      expect(result.email).toBe('test@example.com');
    });
  });

  // --- Backward Compatibility Tests ---

  describe('findById - backward compatibility', () => {
    test('returns null for non-existent ID', async () => {
      mockUserRepo.findById.mockResolvedValue(null);

      const result = await userService.findById('999');

      expect(result).toBeNull();
    });
  });

  // --- Exception Contract Tests ---

  describe('createUser - exception contracts', () => {
    test('still throws ValidationError for null request', async () => {
      await expect(userService.createUser(null as any))
        .rejects
        .toThrow('ValidationError');
    });
  });

  // --- Integration Point Regression ---

  describe('createUser - dependency interactions', () => {
    test('still calls emailService.sendWelcomeEmail', async () => {
      mockUserRepo.save.mockResolvedValue({ id: '1', email: 'test@example.com' });

      await userService.createUser({ email: 'test@example.com', name: 'Test' });

      expect(mockEmailService.sendWelcomeEmail).toHaveBeenCalledTimes(1);
      expect(mockEmailService.sendWelcomeEmail).toHaveBeenCalledWith('test@example.com');
    });
  });
});
```

## Jest Mocking Patterns for Regression Testing

### Module Mocking
```javascript
// Mock an entire module
jest.mock('../services/paymentService');

// Mock with implementation
jest.mock('../services/paymentService', () => ({
  processPayment: jest.fn().mockResolvedValue({ success: true }),
}));
```

### Verify Unchanged Interactions
```javascript
// Verify dependency was called with expected arguments
expect(mockRepo.save).toHaveBeenCalledWith(
  expect.objectContaining({ email: 'test@example.com' })
);
expect(mockRepo.save).toHaveBeenCalledTimes(1);
```

### Verify Error Propagation
```javascript
// Verify that dependency errors are still propagated correctly
mockRepo.save.mockRejectedValue(new Error('DB connection failed'));
await expect(service.createUser(request)).rejects.toThrow('DB connection failed');
```

## Parameterized Regression Tests

```javascript
describe.each([
  ['valid email', 'test@example.com', true],
  ['no @ sign', 'invalid-email', false],
  ['empty string', '', false],
  ['null', null, false],
])('validateEmail(%s)', (description, email, expected) => {
  test(`returns ${expected}`, () => {
    expect(service.validateEmail(email)).toBe(expected);
  });
});
```

## Snapshot Regression Testing

```javascript
// For React components
test('renders correctly after refactoring', () => {
  const { container } = render(<UserProfile user={mockUser} />);
  expect(container).toMatchSnapshot();
});

// For data structures
test('API response shape is unchanged', async () => {
  const response = await service.getUserProfile('123');
  expect(response).toMatchSnapshot();
});
```

## Coverage Configuration

### Jest (jest.config.js)
```javascript
module.exports = {
  collectCoverage: true,
  coverageDirectory: 'coverage',
  coverageReporters: ['json', 'lcov', 'text', 'clover'],
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.test.{js,jsx,ts,tsx}',
    '!src/**/*.spec.{js,jsx,ts,tsx}',
  ],
};
```

### Vitest (vitest.config.ts)
```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    coverage: {
      provider: 'v8', // or 'istanbul'
      reporter: ['json', 'lcov', 'text'],
      include: ['src/**/*.{js,ts,tsx}'],
      exclude: ['src/**/*.test.{ts,tsx}', 'src/**/*.spec.{ts,tsx}'],
    },
  },
});
```

## Running Selected Tests

### Jest
```bash
# Run specific test file
npx jest userService.test.ts

# Run tests matching a pattern
npx jest --testPathPattern=".*Service.*\\.test\\.ts$"

# Run with coverage
npx jest --coverage --collectCoverageFrom='src/services/**/*.ts'

# Run in a specific workspace package
npx jest --projects packages/core
```

### Vitest
```bash
# Run specific test file
npx vitest run src/services/userService.test.ts

# Run tests matching a pattern
npx vitest run --reporter=json "Service"

# Run with coverage
npx vitest run --coverage
```

## Common JS/TS Regression Risks

| Risk | Detection | Mitigation |
|---|---|---|
| Export shape change | Named export renamed/removed | Test import and usage of all exports |
| Promise/async regression | Sync changed to async or vice versa | Test both resolve and reject paths |
| Type narrowing change | TypeScript guard modified | Test all type branches |
| Default export change | Default export replaced | Test import patterns |
| Middleware order change | Express/Koa middleware reordered | Test request pipeline end-to-end |
| React prop change | Component prop added/removed | Snapshot test + prop validation |
| Event handler change | Event listener modified | Test event firing and handling |
| Module side effect | Top-level side effect added/removed | Test module import behavior |
| Null/undefined handling | Optional chaining added/removed | Test with null/undefined inputs |
| Error boundary change | Error handling modified | Test error propagation chain |

## Data-Driven Regression Tests

When user-provided test data is available, prefer loading data from fixture files
over hardcoded inline values.

### JSON Fixture Loading
```typescript
import { readFileSync } from 'fs';
import { join } from 'path';

const loadFixture = <T>(name: string): T =>
  JSON.parse(readFileSync(join(__dirname, '__fixtures__', name), 'utf-8'));

describe('Regression: OrderService (data-driven)', () => {
  const validOrder = loadFixture<OrderRequest>('order-valid.json');

  test('processOrder with fixture data returns expected result', async () => {
    const result = await orderService.processOrder(validOrder);
    expect(result.status).toBe('CONFIRMED');
  });
});
```

### CSV File-Driven Parameterized Tests
```typescript
import { readFileSync } from 'fs';

function loadCsvFixture(filename: string): string[][] {
  const lines = readFileSync(join(__dirname, '__fixtures__', filename), 'utf-8')
    .split('\n')
    .filter(l => l.trim())
    .slice(1); // skip header
  return lines.map(l => l.split(','));
}

const csvData = loadCsvFixture('order-inputs.csv');

describe.each(csvData)(
  'processOrder(%s, %s)',
  (productId, quantity, expectedStatus) => {
    test(`returns ${expectedStatus}`, async () => {
      const result = await orderService.processOrder({
        productId,
        quantity: parseInt(quantity),
      });
      expect(result.status).toBe(expectedStatus);
    });
  }
);
```

### Golden-File Assertion Pattern
```typescript
test('toDto output matches golden file', () => {
  const actualDto = userService.toDto(testUser);
  const expectedJson = readFileSync(
    join(__dirname, '__fixtures__/expected/user-dto.json'), 'utf-8');
  expect(JSON.parse(JSON.stringify(actualDto))).toEqual(JSON.parse(expectedJson));
});
```

## Integration Regression Test Patterns

Use these patterns when `test_level` is `integration` or `both`. Integration tests
use `*.integration.test.ts` suffix.

### Supertest — Express/Fastify API Integration
```typescript
// userController.integration.test.ts
import request from 'supertest';
import { createApp } from '../app';

describe('Regression: UserController integration', () => {
  const app = createApp();

  describe('GET /api/users/:id', () => {
    test('returns 200 for existing user', async () => {
      const response = await request(app)
        .get('/api/users/1')
        .expect(200);

      expect(response.body).toHaveProperty('id');
      expect(response.body).toHaveProperty('email');
    });

    test('returns 404 for non-existent user', async () => {
      await request(app)
        .get('/api/users/999')
        .expect(404);
    });
  });

  describe('POST /api/users', () => {
    test('returns 400 for invalid body', async () => {
      await request(app)
        .post('/api/users')
        .send({ email: '', name: null })
        .expect(400);
    });

    test('returns 201 for valid registration', async () => {
      const response = await request(app)
        .post('/api/users')
        .send({ email: 'new@example.com', name: 'New User' })
        .expect(201);

      expect(response.body.id).toBeDefined();
    });
  });
});
```

### MSW (Mock Service Worker) — External API Integration
```typescript
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

const server = setupServer(
  http.get('https://api.external.com/data', () =>
    HttpResponse.json({ items: [{ id: 1, name: 'Test' }] })
  ),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Regression: ExternalApiClient integration', () => {
  test('fetchData returns expected structure', async () => {
    const result = await apiClient.fetchData();
    expect(result.items).toHaveLength(1);
    expect(result.items[0]).toHaveProperty('name');
  });

  test('fetchData handles server error gracefully', async () => {
    server.use(
      http.get('https://api.external.com/data', () =>
        HttpResponse.json({ error: 'Internal' }, { status: 500 })
      ),
    );
    await expect(apiClient.fetchData()).rejects.toThrow();
  });
});
```

### Testcontainers — Real Database Integration
```typescript
import { PostgreSqlContainer } from '@testcontainers/postgresql';
import { Pool } from 'pg';

describe('Regression: UserRepository (Testcontainers)', () => {
  let container: any;
  let pool: Pool;

  beforeAll(async () => {
    container = await new PostgreSqlContainer('postgres:15').start();
    pool = new Pool({ connectionString: container.getConnectionUri() });
    // Run migrations
    // await runMigrations(pool);
  }, 60000);

  afterAll(async () => {
    await pool.end();
    await container.stop();
  });

  test('findByEmail returns user from real database', async () => {
    await pool.query("INSERT INTO users (email, name) VALUES ('test@example.com', 'Test')");
    const repo = new UserRepository(pool);

    const user = await repo.findByEmail('test@example.com');
    expect(user).toBeDefined();
    expect(user?.name).toBe('Test');
  });
});
```

### Next.js API Route Integration
```typescript
import { createMocks } from 'node-mocks-http';
import handler from '../pages/api/users';

describe('Regression: /api/users integration', () => {
  test('GET returns user list', async () => {
    const { req, res } = createMocks({ method: 'GET' });
    await handler(req, res);

    expect(res._getStatusCode()).toBe(200);
    const data = JSON.parse(res._getData());
    expect(Array.isArray(data)).toBe(true);
  });
});
```

## Requirement-Traced Regression Tests

When requirement IDs or regression scenarios are provided, use structured
traceability annotations to link tests back to requirements.

```typescript
/**
 * @regression PaymentProcessingIntegrity
 * @requirement REQ-PAY-001
 */
describe('Regression: PaymentService [REQ-PAY-001]', () => {
  // Scenario: PaymentProcessingIntegrity
  describe('Scenario: PaymentProcessingIntegrity [REQ-PAY-001]', () => {
    test('[REQ-PAY-001] processPayment deducts correct amount from wallet', async () => {
      // ... test implementation
    });

    test('[REQ-PAY-001] processPayment creates transaction with COMPLETED status', async () => {
      // ... test implementation
    });

    test('[REQ-PAY-002] refundPayment restores wallet balance', async () => {
      // ... test implementation
    });
  });
});
```
