# Express.js Mocking Guide

Comprehensive patterns for mocking services, databases, middleware,
and external dependencies in Express.js tests.

## Module Mocking (Jest)

### Mock Entire Module

```typescript
// Mock before import
jest.mock('../services/user.service');
import { UserService } from '../services/user.service';

const mockUserService = jest.mocked(UserService);
mockUserService.prototype.getAll = jest.fn().mockResolvedValue([]);
```

### Mock with Factory

```typescript
jest.mock('../services/user.service', () => ({
  UserService: jest.fn().mockImplementation(() => ({
    getAll: jest.fn().mockResolvedValue([]),
    getById: jest.fn().mockResolvedValue(null),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
  })),
}));
```

### Mock Singleton/Instance

```typescript
// If service is exported as an instance
jest.mock('../services/user.service', () => ({
  userService: {
    getAll: jest.fn(),
    getById: jest.fn(),
    create: jest.fn(),
  },
}));

import { userService } from '../services/user.service';
const mockUserService = jest.mocked(userService);
```

## req / res / next Mocking

### Manual Mock Objects

```typescript
function createMockReq(overrides = {}): Partial<Request> {
  return {
    params: {},
    query: {},
    body: {},
    headers: {},
    get: jest.fn(),
    ...overrides,
  };
}

function createMockRes(): Partial<Response> {
  const res: Partial<Response> = {};
  res.status = jest.fn().mockReturnValue(res);
  res.json = jest.fn().mockReturnValue(res);
  res.send = jest.fn().mockReturnValue(res);
  res.sendStatus = jest.fn().mockReturnValue(res);
  res.set = jest.fn().mockReturnValue(res);
  res.cookie = jest.fn().mockReturnValue(res);
  res.clearCookie = jest.fn().mockReturnValue(res);
  res.redirect = jest.fn().mockReturnValue(res);
  res.locals = {};
  return res;
}

const mockNext: NextFunction = jest.fn();
```

### Usage in Controller Tests

```typescript
describe('UserController', () => {
  let req: Partial<Request>;
  let res: Partial<Response>;
  let next: NextFunction;

  beforeEach(() => {
    req = createMockReq();
    res = createMockRes();
    next = jest.fn();
    jest.clearAllMocks();
  });

  it('should return users', async () => {
    mockUserService.getAll.mockResolvedValue([{ id: 1, name: 'Alice' }]);

    await userController.getAll(req as Request, res as Response, next);

    expect(res.status).toHaveBeenCalledWith(200);
    expect(res.json).toHaveBeenCalledWith([{ id: 1, name: 'Alice' }]);
  });

  it('should call next with error on failure', async () => {
    const error = new Error('DB error');
    mockUserService.getAll.mockRejectedValue(error);

    await userController.getAll(req as Request, res as Response, next);

    expect(next).toHaveBeenCalledWith(error);
  });
});
```

## Database Mocking

### Mongoose

```typescript
// Option 1: Mock model methods directly
jest.mock('../models/user.model');
import { User } from '../models/user.model';

(User.find as jest.Mock).mockResolvedValue([mockUser]);
(User.findById as jest.Mock).mockResolvedValue(mockUser);
(User.create as jest.Mock).mockResolvedValue(mockUser);
(User.findByIdAndUpdate as jest.Mock).mockResolvedValue(mockUser);
(User.findByIdAndDelete as jest.Mock).mockResolvedValue(mockUser);

// Option 2: mockingoose
import mockingoose from 'mockingoose';
import { User } from '../models/user.model';

mockingoose(User).toReturn([mockUser], 'find');
mockingoose(User).toReturn(mockUser, 'findOne');
mockingoose(User).toReturn(mockUser, 'save');

// Reset
mockingoose.resetAll();
```

### Prisma Client

```typescript
import { PrismaClient } from '@prisma/client';
import { mockDeep, DeepMockProxy } from 'jest-mock-extended';

// Create mock
const prismaMock = mockDeep<PrismaClient>();

// Mock module
jest.mock('../lib/prisma', () => ({
  prisma: prismaMock,
}));

// Setup return values
prismaMock.user.findMany.mockResolvedValue([mockUser]);
prismaMock.user.findUnique.mockResolvedValue(mockUser);
prismaMock.user.create.mockResolvedValue(mockUser);
prismaMock.user.update.mockResolvedValue(mockUser);
prismaMock.user.delete.mockResolvedValue(mockUser);

// Transaction mock
prismaMock.$transaction.mockImplementation(async (fn) => {
  return fn(prismaMock);
});
```

### Sequelize

```typescript
// Mock model
jest.mock('../models/user.model', () => ({
  User: {
    findAll: jest.fn(),
    findByPk: jest.fn(),
    findOne: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    destroy: jest.fn(),
  },
}));

import { User } from '../models/user.model';

(User.findAll as jest.Mock).mockResolvedValue([mockUser]);
(User.findByPk as jest.Mock).mockResolvedValue(mockUser);
```

## External API Mocking

### axios

```typescript
jest.mock('axios');
import axios from 'axios';

const mockAxios = jest.mocked(axios);

mockAxios.get.mockResolvedValue({
  data: { id: 1, name: 'External Data' },
  status: 200,
});

mockAxios.post.mockResolvedValue({
  data: { success: true },
  status: 201,
});

// Axios instance mock
jest.mock('../lib/api-client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));
```

### node-fetch / fetch

```typescript
// Global fetch mock
const mockFetch = jest.fn();
global.fetch = mockFetch;

mockFetch.mockResolvedValue({
  ok: true,
  status: 200,
  json: () => Promise.resolve({ data: 'test' }),
  text: () => Promise.resolve('OK'),
});

// Failed response
mockFetch.mockResolvedValue({
  ok: false,
  status: 500,
  json: () => Promise.resolve({ error: 'Server error' }),
});
```

## Redis / Cache Mocking

```typescript
jest.mock('../lib/redis', () => ({
  redisClient: {
    get: jest.fn(),
    set: jest.fn(),
    del: jest.fn(),
    setex: jest.fn(),
    exists: jest.fn(),
  },
}));

import { redisClient } from '../lib/redis';

(redisClient.get as jest.Mock).mockResolvedValue(JSON.stringify(cachedData));
(redisClient.set as jest.Mock).mockResolvedValue('OK');
```

## JWT / Auth Mocking

```typescript
jest.mock('jsonwebtoken');
import jwt from 'jsonwebtoken';

(jwt.sign as jest.Mock).mockReturnValue('mock-jwt-token');
(jwt.verify as jest.Mock).mockReturnValue({
  userId: '1',
  email: 'alice@test.com',
  role: 'user',
});

// Verify with error
(jwt.verify as jest.Mock).mockImplementation(() => {
  throw new jwt.JsonWebTokenError('Invalid token');
});

// Token expired
(jwt.verify as jest.Mock).mockImplementation(() => {
  throw new jwt.TokenExpiredError('Token expired', new Date());
});
```

## Environment Variables

```typescript
// Save and restore
const originalEnv = process.env;

beforeEach(() => {
  process.env = { ...originalEnv };
  process.env.NODE_ENV = 'test';
  process.env.JWT_SECRET = 'test-secret';
});

afterEach(() => {
  process.env = originalEnv;
});
```

## Event Emitter Mocking

```typescript
import { EventEmitter } from 'events';

const mockEmitter = new EventEmitter();
jest.spyOn(mockEmitter, 'emit');

// After action
expect(mockEmitter.emit).toHaveBeenCalledWith('user:created', expect.any(Object));
```

## Anti-Patterns to Avoid

1. **Don't import `server.ts` in tests** — import `app.ts` to avoid port binding
2. **Don't use real database connections** — mock or use in-memory alternatives
3. **Don't depend on test execution order** — each test should be independent
4. **Don't share mutable state between tests** — reset in `beforeEach`
5. **Don't mock what you don't own** — wrap third-party APIs in your own module
6. **Don't forget to restore mocks** — use `jest.clearAllMocks()` or `sinon.restore()`
7. **Don't test Express internals** — test your handlers and middleware, not Express itself
