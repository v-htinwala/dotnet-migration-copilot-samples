# Supertest & HTTP Testing Patterns for Express.js

## Basic Setup

### App/Server Separation

**Critical**: Separate `app` creation from `server.listen()` so Supertest can
import the app without binding to a port.

```typescript
// src/app.ts — Express app (import this in tests)
import express from 'express';
import { userRouter } from './routes/user.routes';
import { errorHandler } from './middleware/error.handler';

const app = express();

app.use(express.json());
app.use('/api/users', userRouter);
app.use(errorHandler);

export default app;
```

```typescript
// src/server.ts — HTTP server (NOT imported in tests)
import app from './app';

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Listening on ${PORT}`));
```

### Supertest Import

```typescript
import request from 'supertest';
import app from '../app';
```

## GET Requests

```typescript
describe('GET /api/users', () => {
  it('should return 200 with user list', async () => {
    const response = await request(app)
      .get('/api/users')
      .expect('Content-Type', /json/)
      .expect(200);

    expect(response.body).toBeInstanceOf(Array);
    expect(response.body).toHaveLength(2);
    expect(response.body[0]).toHaveProperty('id');
    expect(response.body[0]).toHaveProperty('name');
  });

  it('should return empty array when no users exist', async () => {
    mockUserService.getAll.mockResolvedValue([]);

    const response = await request(app)
      .get('/api/users')
      .expect(200);

    expect(response.body).toEqual([]);
  });

  it('should support query parameters', async () => {
    const response = await request(app)
      .get('/api/users')
      .query({ page: 1, limit: 10, sort: 'name' })
      .expect(200);

    expect(mockUserService.getAll).toHaveBeenCalledWith(
      expect.objectContaining({ page: '1', limit: '10', sort: 'name' })
    );
  });
});

describe('GET /api/users/:id', () => {
  it('should return 200 with user', async () => {
    const response = await request(app)
      .get('/api/users/1')
      .expect(200);

    expect(response.body.id).toBe(1);
    expect(response.body.name).toBe('Alice');
  });

  it('should return 404 when user not found', async () => {
    mockUserService.getById.mockResolvedValue(null);

    await request(app)
      .get('/api/users/999')
      .expect(404);
  });

  it('should return 400 for invalid ID format', async () => {
    await request(app)
      .get('/api/users/invalid')
      .expect(400);
  });
});
```

## POST Requests

```typescript
describe('POST /api/users', () => {
  const validBody = {
    name: 'Alice',
    email: 'alice@test.com',
    password: 'StrongPass123!',
  };

  it('should create user and return 201', async () => {
    mockUserService.create.mockResolvedValue({ id: 1, ...validBody });

    const response = await request(app)
      .post('/api/users')
      .send(validBody)
      .set('Content-Type', 'application/json')
      .expect(201);

    expect(response.body).toHaveProperty('id');
    expect(response.body.name).toBe('Alice');
    expect(mockUserService.create).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'Alice', email: 'alice@test.com' })
    );
  });

  it('should return 400 for missing required fields', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ name: 'Alice' }) // Missing email and password
      .expect(400);

    expect(response.body).toHaveProperty('errors');
  });

  it('should return 400 for invalid email', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ ...validBody, email: 'not-an-email' })
      .expect(400);

    expect(response.body.errors).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ field: 'email' }),
      ])
    );
  });

  it('should return 409 for duplicate email', async () => {
    mockUserService.create.mockRejectedValue(
      new ConflictError('Email already exists')
    );

    await request(app)
      .post('/api/users')
      .send(validBody)
      .expect(409);
  });
});
```

## PUT / PATCH Requests

```typescript
describe('PUT /api/users/:id', () => {
  it('should update user and return 200', async () => {
    const updateBody = { name: 'Alice Updated' };
    mockUserService.update.mockResolvedValue({ id: 1, ...updateBody });

    const response = await request(app)
      .put('/api/users/1')
      .send(updateBody)
      .expect(200);

    expect(response.body.name).toBe('Alice Updated');
  });

  it('should return 404 when user not found', async () => {
    mockUserService.update.mockRejectedValue(new NotFoundError('User not found'));

    await request(app)
      .put('/api/users/999')
      .send({ name: 'Updated' })
      .expect(404);
  });
});
```

## DELETE Requests

```typescript
describe('DELETE /api/users/:id', () => {
  it('should delete user and return 204', async () => {
    mockUserService.delete.mockResolvedValue(true);

    await request(app)
      .delete('/api/users/1')
      .expect(204);

    expect(mockUserService.delete).toHaveBeenCalledWith('1');
  });

  it('should return 404 when user not found', async () => {
    mockUserService.delete.mockResolvedValue(false);

    await request(app)
      .delete('/api/users/999')
      .expect(404);
  });
});
```

## Authentication Headers

```typescript
describe('Protected routes', () => {
  const validToken = 'Bearer valid-jwt-token';

  it('should return 401 without auth header', async () => {
    await request(app)
      .get('/api/protected')
      .expect(401);
  });

  it('should return 401 with invalid token', async () => {
    await request(app)
      .get('/api/protected')
      .set('Authorization', 'Bearer invalid-token')
      .expect(401);
  });

  it('should return 200 with valid token', async () => {
    await request(app)
      .get('/api/protected')
      .set('Authorization', validToken)
      .expect(200);
  });

  it('should return 403 without required role', async () => {
    await request(app)
      .get('/api/admin')
      .set('Authorization', validToken) // User role, not admin
      .expect(403);
  });
});
```

## File Upload

```typescript
describe('POST /api/upload', () => {
  it('should upload file and return 200', async () => {
    const response = await request(app)
      .post('/api/upload')
      .attach('file', Buffer.from('file content'), 'test.txt')
      .expect(200);

    expect(response.body).toHaveProperty('url');
  });

  it('should reject files larger than limit', async () => {
    const largeBuffer = Buffer.alloc(10 * 1024 * 1024); // 10MB

    await request(app)
      .post('/api/upload')
      .attach('file', largeBuffer, 'large.bin')
      .expect(413);
  });
});
```

## Response Headers

```typescript
it('should set CORS headers', async () => {
  const response = await request(app)
    .get('/api/users')
    .expect(200);

  expect(response.headers['access-control-allow-origin']).toBe('*');
});

it('should set pagination headers', async () => {
  const response = await request(app)
    .get('/api/users?page=2&limit=10')
    .expect(200);

  expect(response.headers['x-total-count']).toBe('50');
  expect(response.headers['x-page']).toBe('2');
});
```

## Testing Error Responses

```typescript
it('should return structured error response', async () => {
  mockUserService.getById.mockRejectedValue(new Error('Database error'));

  const response = await request(app)
    .get('/api/users/1')
    .expect(500);

  expect(response.body).toEqual({
    status: 'error',
    message: expect.any(String),
    // Should NOT expose stack traces in production
  });
  expect(response.body).not.toHaveProperty('stack');
});
```
