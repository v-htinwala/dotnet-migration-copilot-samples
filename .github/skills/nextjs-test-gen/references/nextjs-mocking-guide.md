# Next.js Mocking Guide

Comprehensive patterns for mocking Next.js internals in unit tests.
Applies to both Vitest and Jest — examples use `vi.*` / `jest.*` interchangeably.

## next/navigation

### useRouter

```typescript
import { useRouter } from 'next/navigation'

// In test setup (Vitest)
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  usePathname: vi.fn(),
  useSearchParams: vi.fn(),
  useParams: vi.fn(),
  redirect: vi.fn(),
  notFound: vi.fn(),
  useSelectedLayoutSegment: vi.fn(),
  useSelectedLayoutSegments: vi.fn(),
}))

// In individual test
import { useRouter } from 'next/navigation'
const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  refresh: vi.fn(),
  prefetch: vi.fn(),
}
vi.mocked(useRouter).mockReturnValue(mockRouter as any)

// Assert navigation
await user.click(screen.getByRole('link', { name: 'Dashboard' }))
expect(mockRouter.push).toHaveBeenCalledWith('/dashboard')
```

### usePathname

```typescript
import { usePathname } from 'next/navigation'

vi.mocked(usePathname).mockReturnValue('/dashboard/settings')

// Test active link styling
render(<NavLink href="/dashboard/settings">Settings</NavLink>)
expect(screen.getByRole('link')).toHaveClass('active')
```

### useSearchParams

```typescript
import { useSearchParams } from 'next/navigation'

vi.mocked(useSearchParams).mockReturnValue(
  new URLSearchParams('?page=2&sort=name') as any
)

render(<PaginatedList />)
expect(screen.getByText('Page 2')).toBeInTheDocument()
```

### useParams

```typescript
import { useParams } from 'next/navigation'

vi.mocked(useParams).mockReturnValue({ id: '123', slug: 'test-post' })

render(<PostPage />)
await waitFor(() => {
  expect(screen.getByText('Post: test-post')).toBeInTheDocument()
})
```

### redirect and notFound

```typescript
import { redirect, notFound } from 'next/navigation'

// For server components / server actions
it('redirects unauthenticated users', async () => {
  mockGetSession.mockResolvedValue(null)

  await ProfilePage()

  expect(redirect).toHaveBeenCalledWith('/login')
})

it('returns 404 for unknown post', async () => {
  mockGetPost.mockResolvedValue(null)

  await PostPage({ params: { slug: 'nonexistent' } })

  expect(notFound).toHaveBeenCalled()
})
```

## next/headers

### cookies()

```typescript
vi.mock('next/headers', () => ({
  cookies: vi.fn(),
  headers: vi.fn(),
}))

import { cookies } from 'next/headers'

// Mock the cookies store
const mockCookieStore = {
  get: vi.fn(),
  getAll: vi.fn(),
  set: vi.fn(),
  delete: vi.fn(),
  has: vi.fn(),
}
vi.mocked(cookies).mockReturnValue(mockCookieStore as any)

// Test cookie reading
mockCookieStore.get.mockReturnValue({ name: 'token', value: 'abc123' })

const result = await getAuthToken()
expect(result).toBe('abc123')
expect(mockCookieStore.get).toHaveBeenCalledWith('token')
```

### headers()

```typescript
import { headers } from 'next/headers'

const mockHeaderStore = {
  get: vi.fn(),
  has: vi.fn(),
  entries: vi.fn(),
  forEach: vi.fn(),
}
vi.mocked(headers).mockReturnValue(mockHeaderStore as any)

// Test reading a header
mockHeaderStore.get.mockImplementation((name: string) => {
  const map: Record<string, string> = {
    'x-forwarded-for': '192.168.1.1',
    'user-agent': 'Test Agent',
    authorization: 'Bearer token123',
  }
  return map[name] ?? null
})

const ip = await getClientIp()
expect(ip).toBe('192.168.1.1')
```

## next/cache

### revalidatePath and revalidateTag

```typescript
vi.mock('next/cache', () => ({
  revalidatePath: vi.fn(),
  revalidateTag: vi.fn(),
  unstable_cache: vi.fn((fn) => fn),
}))

import { revalidatePath, revalidateTag } from 'next/cache'

// Test server action revalidation
it('revalidates after mutation', async () => {
  const formData = new FormData()
  formData.append('title', 'New Post')

  await createPost(formData)

  expect(revalidatePath).toHaveBeenCalledWith('/posts')
  expect(revalidateTag).toHaveBeenCalledWith('posts')
})
```

### unstable_cache

```typescript
import { unstable_cache } from 'next/cache'

// The mock passes through — the wrapped function runs directly
it('caches expensive computation', async () => {
  const result = await getCachedPosts()
  expect(mockDb.query).toHaveBeenCalled()
})
```

## next/server

### NextRequest

```typescript
import { NextRequest } from 'next/server'

// Create a mock request
function createMockRequest(
  url: string,
  options?: {
    method?: string
    headers?: Record<string, string>
    body?: any
    cookies?: Record<string, string>
  }
): NextRequest {
  const { method = 'GET', headers = {}, body, cookies = {} } = options ?? {}

  const req = new NextRequest(new URL(url, 'http://localhost:3000'), {
    method,
    headers: new Headers(headers),
    body: body ? JSON.stringify(body) : undefined,
  })

  // Set cookies
  for (const [name, value] of Object.entries(cookies)) {
    req.cookies.set(name, value)
  }

  return req
}

// Usage
it('handles GET request', async () => {
  const req = createMockRequest('/api/users', {
    headers: { authorization: 'Bearer token' },
  })

  const response = await GET(req)
  const data = await response.json()

  expect(response.status).toBe(200)
  expect(data.users).toHaveLength(3)
})
```

### NextResponse

```typescript
// NextResponse is typically used in the source code, not mocked.
// In tests, you assert on the response returned by your handler:

it('returns JSON response', async () => {
  const req = createMockRequest('/api/posts', { method: 'POST', body: { title: 'Test' } })

  const response = await POST(req)

  expect(response.status).toBe(201)
  expect(response.headers.get('content-type')).toContain('application/json')
  const data = await response.json()
  expect(data.id).toBeDefined()
})

// For redirects
it('redirects to login', async () => {
  const req = createMockRequest('/api/protected')
  const response = await GET(req)

  expect(response.status).toBe(307)
  expect(response.headers.get('location')).toBe('/login')
})
```

## next/image

```typescript
vi.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => {
    // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
    return <img {...props} />
  },
}))
```

## next/link

```typescript
vi.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href, ...props }: any) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}))
```

## next/font

```typescript
// Mock font imports (they return CSS class names)
vi.mock('next/font/google', () => ({
  Inter: () => ({ className: 'inter-mock', style: { fontFamily: 'Inter' } }),
  Roboto: () => ({ className: 'roboto-mock', style: { fontFamily: 'Roboto' } }),
}))

vi.mock('next/font/local', () => ({
  __esModule: true,
  default: () => ({ className: 'local-font-mock', style: { fontFamily: 'Local' } }),
}))
```

## Middleware Testing

```typescript
import { NextRequest, NextResponse } from 'next/server'
import { middleware } from './middleware'

it('redirects unauthenticated users', async () => {
  const req = createMockRequest('/dashboard')
  // No auth cookie

  const response = await middleware(req)

  expect(response?.status).toBe(307)
  expect(response?.headers.get('location')).toContain('/login')
})

it('allows authenticated users through', async () => {
  const req = createMockRequest('/dashboard', {
    cookies: { session: 'valid-token' },
  })

  const response = await middleware(req)

  expect(response).toEqual(NextResponse.next())
})

it('adds security headers', async () => {
  const req = createMockRequest('/any-page')
  const response = await middleware(req)

  expect(response?.headers.get('x-frame-options')).toBe('DENY')
})
```

## Dynamic Imports / next/dynamic

```typescript
// If using next/dynamic, mock the component directly
vi.mock('@/components/HeavyChart', () => ({
  __esModule: true,
  default: () => <div data-testid="mock-chart">Chart</div>,
}))
```

## Server-Only Modules

```typescript
// If a module imports 'server-only', mock it to prevent errors
vi.mock('server-only', () => ({}))
```
