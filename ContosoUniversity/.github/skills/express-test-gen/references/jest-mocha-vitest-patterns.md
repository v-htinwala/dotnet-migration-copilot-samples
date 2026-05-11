# Jest / Mocha / Vitest Patterns for Express.js

## Jest Setup

### jest.config.ts

```typescript
import type { Config } from 'jest';

const config: Config = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src'],
  testMatch: ['**/*.test.{ts,js}'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  setupFilesAfterSetup: ['<rootDir>/jest.setup.ts'],
  collectCoverageFrom: [
    'src/**/*.{ts,js}',
    '!src/**/*.test.{ts,js}',
    '!src/**/*.d.ts',
    '!src/types/**',
    '!src/server.ts',
  ],
  coverageThreshold: {
    global: {
      statements: 85,
      branches: 85,
      functions: 85,
      lines: 85,
    },
  },
  coverageReporters: ['text', 'text-summary', 'json', 'json-summary', 'lcov'],
};

export default config;
```

### jest.setup.ts

```typescript
// Set test environment variables
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-secret';
process.env.DATABASE_URL = 'mock://test';
```

### Jest Mocking

```typescript
// Mock entire module
jest.mock('../services/user.service');

// Mock with implementation
jest.mock('../services/user.service', () => ({
  getAll: jest.fn(),
  getById: jest.fn(),
  create: jest.fn(),
  update: jest.fn(),
  delete: jest.fn(),
}));

// Mock with partial implementation
jest.mock('../services/user.service', () => {
  const actual = jest.requireActual('../services/user.service');
  return {
    ...actual,
    getAll: jest.fn(),
  };
});

// Inline mock
const mockFn = jest.fn();
mockFn.mockReturnValue('result');
mockFn.mockResolvedValue({ data: 'async result' });
mockFn.mockRejectedValue(new Error('fail'));

// Spy
jest.spyOn(userService, 'getAll').mockResolvedValue([]);

// Reset
beforeEach(() => {
  jest.clearAllMocks();
});
```

### Jest Assertions

```typescript
expect(value).toBe(42);
expect(value).toEqual({ a: 1 });
expect(value).toBeTruthy();
expect(value).toBeFalsy();
expect(value).toBeNull();
expect(value).toBeUndefined();
expect(value).toBeDefined();
expect(array).toHaveLength(3);
expect(array).toContain(item);
expect(object).toHaveProperty('key', 'value');
expect(string).toMatch(/pattern/);
expect(fn).toThrow();
expect(fn).toThrow(CustomError);
expect(fn).toThrowError('message');
expect(mockFn).toHaveBeenCalled();
expect(mockFn).toHaveBeenCalledTimes(2);
expect(mockFn).toHaveBeenCalledWith('arg1', 'arg2');
expect(mockFn).toHaveBeenLastCalledWith('arg');
```

## Mocha / Chai / Sinon Setup

### .mocharc.yml

```yaml
require:
  - ts-node/register
spec: "src/**/*.test.ts"
timeout: 5000
exit: true
```

### Chai Assertions

```typescript
import { expect } from 'chai';

expect(value).to.equal(42);
expect(value).to.deep.equal({ a: 1 });
expect(value).to.be.true;
expect(value).to.be.null;
expect(value).to.be.undefined;
expect(value).to.exist;
expect(array).to.have.lengthOf(3);
expect(array).to.include(item);
expect(object).to.have.property('key', 'value');
expect(string).to.match(/pattern/);
expect(fn).to.throw();
expect(fn).to.throw(CustomError);
expect(fn).to.throw('message');
```

### Sinon Mocking

```typescript
import sinon from 'sinon';

// Stub
const stub = sinon.stub(userService, 'getAll');
stub.resolves([user1, user2]);
stub.rejects(new Error('fail'));
stub.returns('value');

// Spy
const spy = sinon.spy(userService, 'getAll');

// Fake
const fake = sinon.fake.resolves([user1]);
sinon.replace(userService, 'getAll', fake);

// Restore all
afterEach(() => {
  sinon.restore();
});

// Assertions
sinon.assert.called(stub);
sinon.assert.calledOnce(stub);
sinon.assert.calledWith(stub, 'arg');
sinon.assert.notCalled(stub);

// Or with Chai
expect(stub.calledOnce).to.be.true;
expect(stub.calledWith('arg')).to.be.true;

// With sinon-chai plugin
expect(stub).to.have.been.calledOnce;
expect(stub).to.have.been.calledWith('arg');
```

### Sinon Timers

```typescript
let clock: sinon.SinonFakeTimers;

beforeEach(() => {
  clock = sinon.useFakeTimers();
});

afterEach(() => {
  clock.restore();
});

it('should expire token after 1 hour', async () => {
  const token = await authService.createToken();
  clock.tick(3600 * 1000); // Advance 1 hour
  expect(authService.isValid(token)).to.be.false;
});
```

## Vitest Setup

### vitest.config.ts

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
    include: ['src/**/*.test.{ts,js}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'json-summary', 'lcov'],
      include: ['src/**/*.{ts,js}'],
      exclude: ['src/**/*.test.{ts,js}', 'src/server.ts'],
      thresholds: {
        statements: 85,
        branches: 85,
        functions: 85,
        lines: 85,
      },
    },
  },
});
```

### Vitest Mocking

```typescript
import { vi, describe, it, expect, beforeEach } from 'vitest';

vi.mock('../services/user.service', () => ({
  getAll: vi.fn(),
  getById: vi.fn(),
}));

const mockFn = vi.fn();
mockFn.mockReturnValue('result');
mockFn.mockResolvedValue({ data: 'test' });
```

## Coverage Commands

```bash
# Jest
npx jest --coverage
npx jest --coverage --coverageReporters=text,json-summary

# Mocha + c8
npx c8 mocha
npx c8 --reporter=text,lcov mocha

# Mocha + Istanbul/nyc
npx nyc mocha
npx nyc --reporter=text,lcov mocha

# Vitest
npx vitest run --coverage
```
