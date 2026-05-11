# Express.js Layer Testing Patterns

Per-layer testing strategies for Express.js applications.

## Route / Router Layer

### Testing with Supertest (Preferred)

```typescript
import request from 'supertest';
import app from '../app';

jest.mock('../services/user.service', () => ({
  userService: {
    getAll: jest.fn(),
    getById: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
  },
}));

import { userService } from '../services/user.service';
const mockUserService = jest.mocked(userService);

describe('User Routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('GET /api/users', () => {
    it('should return 200 with users', async () => {
      mockUserService.getAll.mockResolvedValue([
        { id: 1, name: 'Alice', email: 'alice@test.com' },
        { id: 2, name: 'Bob', email: 'bob@test.com' },
      ]);

      const response = await request(app)
        .get('/api/users')
        .expect('Content-Type', /json/)
        .expect(200);

      expect(response.body).toHaveLength(2);
      expect(response.body[0].name).toBe('Alice');
    });

    it('should return empty array', async () => {
      mockUserService.getAll.mockResolvedValue([]);

      const response = await request(app).get('/api/users').expect(200);

      expect(response.body).toEqual([]);
    });
  });

  describe('POST /api/users', () => {
    it('should create and return 201', async () => {
      const newUser = { name: 'Alice', email: 'alice@test.com' };
      mockUserService.create.mockResolvedValue({ id: 1, ...newUser });

      const response = await request(app)
        .post('/api/users')
        .send(newUser)
        .expect(201);

      expect(response.body.id).toBe(1);
      expect(mockUserService.create).toHaveBeenCalledWith(
        expect.objectContaining(newUser)
      );
    });
  });
});
```

### Testing Isolated Router

```typescript
import express from 'express';
import request from 'supertest';
import { userRouter } from '../routes/user.routes';

describe('User Router (isolated)', () => {
  let app: express.Express;

  beforeEach(() => {
    app = express();
    app.use(express.json());
    app.use('/api/users', userRouter);
    app.use((err: Error, req: any, res: any, next: any) => {
      res.status(500).json({ error: err.message });
    });
  });

  it('should handle GET /api/users', async () => {
    await request(app).get('/api/users').expect(200);
  });
});
```

## Controller Layer

### Controller with req/res Mocks

```typescript
import { Request, Response, NextFunction } from 'express';
import { userController } from '../controllers/user.controller';

describe('UserController', () => {
  let req: Partial<Request>;
  let res: Partial<Response>;
  let next: NextFunction;

  beforeEach(() => {
    req = { params: {}, query: {}, body: {} };
    res = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn().mockReturnThis(),
      send: jest.fn().mockReturnThis(),
      sendStatus: jest.fn().mockReturnThis(),
    };
    next = jest.fn();
    jest.clearAllMocks();
  });

  describe('getAll', () => {
    it('should return 200 with users', async () => {
      mockUserService.getAll.mockResolvedValue([{ id: 1, name: 'Alice' }]);

      await userController.getAll(req as Request, res as Response, next);

      expect(res.status).toHaveBeenCalledWith(200);
      expect(res.json).toHaveBeenCalledWith([{ id: 1, name: 'Alice' }]);
    });

    it('should call next on error', async () => {
      const error = new Error('DB connection failed');
      mockUserService.getAll.mockRejectedValue(error);

      await userController.getAll(req as Request, res as Response, next);

      expect(next).toHaveBeenCalledWith(error);
      expect(res.json).not.toHaveBeenCalled();
    });
  });

  describe('getById', () => {
    it('should return user when found', async () => {
      req.params = { id: '1' };
      mockUserService.getById.mockResolvedValue({ id: 1, name: 'Alice' });

      await userController.getById(req as Request, res as Response, next);

      expect(res.status).toHaveBeenCalledWith(200);
      expect(res.json).toHaveBeenCalledWith({ id: 1, name: 'Alice' });
    });

    it('should return 404 when not found', async () => {
      req.params = { id: '999' };
      mockUserService.getById.mockResolvedValue(null);

      await userController.getById(req as Request, res as Response, next);

      expect(res.status).toHaveBeenCalledWith(404);
    });
  });

  describe('create', () => {
    it('should create user and return 201', async () => {
      req.body = { name: 'Alice', email: 'alice@test.com' };
      mockUserService.create.mockResolvedValue({ id: 1, ...req.body });

      await userController.create(req as Request, res as Response, next);

      expect(res.status).toHaveBeenCalledWith(201);
      expect(res.json).toHaveBeenCalledWith(
        expect.objectContaining({ id: 1, name: 'Alice' })
      );
    });
  });

  describe('delete', () => {
    it('should return 204 on success', async () => {
      req.params = { id: '1' };
      mockUserService.delete.mockResolvedValue(true);

      await userController.delete(req as Request, res as Response, next);

      expect(res.sendStatus).toHaveBeenCalledWith(204);
    });
  });
});
```

## Service Layer

```typescript
describe('UserService', () => {
  let userService: UserService;
  let mockUserRepo: jest.Mocked<UserRepository>;
  let mockEmailService: jest.Mocked<EmailService>;

  beforeEach(() => {
    mockUserRepo = {
      findAll: jest.fn(),
      findById: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      delete: jest.fn(),
    } as any;
    mockEmailService = {
      sendWelcome: jest.fn(),
    } as any;

    userService = new UserService(mockUserRepo, mockEmailService);
  });

  describe('createUser', () => {
    it('should create user and send welcome email', async () => {
      const input = { name: 'Alice', email: 'alice@test.com', password: 'pass123' };
      mockUserRepo.create.mockResolvedValue({ id: 1, ...input });
      mockEmailService.sendWelcome.mockResolvedValue(undefined);

      const result = await userService.createUser(input);

      expect(result.id).toBe(1);
      expect(mockUserRepo.create).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'Alice' })
      );
      expect(mockEmailService.sendWelcome).toHaveBeenCalledWith('alice@test.com');
    });

    it('should not send email if creation fails', async () => {
      mockUserRepo.create.mockRejectedValue(new Error('Duplicate email'));

      await expect(
        userService.createUser({ name: 'Alice', email: 'dup@test.com', password: 'pass' })
      ).rejects.toThrow('Duplicate email');

      expect(mockEmailService.sendWelcome).not.toHaveBeenCalled();
    });

    it('should hash password before saving', async () => {
      mockUserRepo.create.mockImplementation(async (data) => ({ id: 1, ...data }));

      await userService.createUser({
        name: 'Alice',
        email: 'alice@test.com',
        password: 'plaintext',
      });

      expect(mockUserRepo.create).toHaveBeenCalledWith(
        expect.objectContaining({
          password: expect.not.stringMatching('plaintext'),
        })
      );
    });
  });
});
```

## Middleware Layer

### Authentication Middleware

```typescript
describe('authMiddleware', () => {
  let req: Partial<Request>;
  let res: Partial<Response>;
  let next: NextFunction;

  beforeEach(() => {
    req = { headers: {} };
    res = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn().mockReturnThis(),
    };
    next = jest.fn();
  });

  it('should call next with valid token', () => {
    req.headers = { authorization: 'Bearer valid-token' };
    (jwt.verify as jest.Mock).mockReturnValue({ userId: '1', role: 'user' });

    authMiddleware(req as Request, res as Response, next);

    expect(next).toHaveBeenCalled();
    expect((req as any).user).toEqual({ userId: '1', role: 'user' });
  });

  it('should return 401 without token', () => {
    authMiddleware(req as Request, res as Response, next);

    expect(res.status).toHaveBeenCalledWith(401);
    expect(res.json).toHaveBeenCalledWith(
      expect.objectContaining({ message: expect.any(String) })
    );
    expect(next).not.toHaveBeenCalled();
  });

  it('should return 401 with expired token', () => {
    req.headers = { authorization: 'Bearer expired-token' };
    (jwt.verify as jest.Mock).mockImplementation(() => {
      throw new jwt.TokenExpiredError('expired', new Date());
    });

    authMiddleware(req as Request, res as Response, next);

    expect(res.status).toHaveBeenCalledWith(401);
  });
});
```

### Rate Limiter Middleware

```typescript
describe('rateLimiter', () => {
  it('should allow requests under limit', async () => {
    for (let i = 0; i < 10; i++) {
      await request(app).get('/api/users').expect(200);
    }
  });

  it('should reject requests over limit', async () => {
    // Exhaust the limit
    for (let i = 0; i < 100; i++) {
      await request(app).get('/api/users');
    }

    await request(app).get('/api/users').expect(429);
  });
});
```

### Error Handler Middleware

```typescript
describe('errorHandler', () => {
  let req: Partial<Request>;
  let res: Partial<Response>;
  let next: NextFunction;

  beforeEach(() => {
    req = {};
    res = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn().mockReturnThis(),
    };
    next = jest.fn();
  });

  it('should handle ValidationError with 400', () => {
    const error = new ValidationError('Invalid input');

    errorHandler(error, req as Request, res as Response, next);

    expect(res.status).toHaveBeenCalledWith(400);
    expect(res.json).toHaveBeenCalledWith(
      expect.objectContaining({ message: 'Invalid input' })
    );
  });

  it('should handle NotFoundError with 404', () => {
    const error = new NotFoundError('User not found');

    errorHandler(error, req as Request, res as Response, next);

    expect(res.status).toHaveBeenCalledWith(404);
  });

  it('should handle unknown errors with 500', () => {
    const error = new Error('Something unexpected');

    errorHandler(error, req as Request, res as Response, next);

    expect(res.status).toHaveBeenCalledWith(500);
    expect(res.json).toHaveBeenCalledWith(
      expect.not.objectContaining({ stack: expect.any(String) })
    );
  });
});
```

## Validator Layer

### Joi Validation

```typescript
describe('userValidation', () => {
  describe('createUserSchema', () => {
    it('should pass with valid data', () => {
      const data = { name: 'Alice', email: 'alice@test.com', password: 'Strong123!' };
      const { error } = createUserSchema.validate(data);
      expect(error).toBeUndefined();
    });

    it('should fail with missing name', () => {
      const data = { email: 'alice@test.com', password: 'Strong123!' };
      const { error } = createUserSchema.validate(data);
      expect(error).toBeDefined();
      expect(error!.details[0].path).toEqual(['name']);
    });

    it('should fail with invalid email', () => {
      const data = { name: 'Alice', email: 'not-email', password: 'Strong123!' };
      const { error } = createUserSchema.validate(data);
      expect(error!.details[0].path).toEqual(['email']);
    });
  });
});
```

### Zod Validation

```typescript
describe('userSchema', () => {
  it('should parse valid data', () => {
    const data = { name: 'Alice', email: 'alice@test.com' };
    const result = userSchema.safeParse(data);
    expect(result.success).toBe(true);
  });

  it('should reject invalid email', () => {
    const data = { name: 'Alice', email: 'invalid' };
    const result = userSchema.safeParse(data);
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues[0].path).toEqual(['email']);
    }
  });
});
```

## Utility Layer

```typescript
describe('formatCurrency', () => {
  it.each([
    [1000, 'USD', '$1,000.00'],
    [0, 'USD', '$0.00'],
    [1234.5, 'EUR', '€1,234.50'],
    [-50, 'USD', '-$50.00'],
  ])('should format %i %s as %s', (amount, currency, expected) => {
    expect(formatCurrency(amount, currency)).toBe(expected);
  });

  it('should handle null gracefully', () => {
    expect(formatCurrency(null as any, 'USD')).toBe('$0.00');
  });
});

describe('hashPassword', () => {
  it('should return a hashed string', async () => {
    const hash = await hashPassword('plaintext');
    expect(hash).not.toBe('plaintext');
    expect(hash).toMatch(/^\$2[aby]\$/); // bcrypt format
  });

  it('should produce different hashes for same input', async () => {
    const hash1 = await hashPassword('password');
    const hash2 = await hashPassword('password');
    expect(hash1).not.toBe(hash2); // Different salts
  });
});
```
