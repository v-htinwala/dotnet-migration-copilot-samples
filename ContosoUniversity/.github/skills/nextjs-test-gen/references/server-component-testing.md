# Server Component Testing Patterns

Testing React Server Components (RSC), Server Actions, `generateMetadata`,
and `generateStaticParams` in Next.js 16.

## Key Principles

1. **RSCs are async functions that return JSX** — test them by calling the function directly
2. **RSCs run on the server** — no browser APIs, no hooks, no `useState`/`useEffect`
3. **Mock server-side dependencies** — database clients, `fetch`, `cookies()`, `headers()`
4. **Do NOT render RSCs with RTL `render()`** — call them as functions and assert the returned JSX, or render with appropriate async handling

## Testing Async Server Components

### Basic RSC test pattern

```typescript
// Source: app/users/page.tsx
// export default async function UsersPage() { ... }

import UsersPage from '@/app/users/page'

vi.mock('@/lib/db', () => ({
  getUsers: vi.fn(),
}))

import { getUsers } from '@/lib/db'

describe('UsersPage', () => {
  it('renders user list', async () => {
    vi.mocked(getUsers).mockResolvedValue([
      { id: '1', name: 'Alice' },
      { id: '2', name: 'Bob' },
    ])

    const result = await UsersPage()

    // Assert on the JSX structure
    // Option 1: Render the result with RTL
    render(result)
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()
  })

  it('renders empty state when no users', async () => {
    vi.mocked(getUsers).mockResolvedValue([])

    const result = await UsersPage()
    render(result)

    expect(screen.getByText('No users found')).toBeInTheDocument()
  })

  it('handles database errors', async () => {
    vi.mocked(getUsers).mockRejectedValue(new Error('DB connection failed'))

    // Depending on error handling strategy:
    // If the component catches errors:
    const result = await UsersPage()
    render(result)
    expect(screen.getByText('Failed to load users')).toBeInTheDocument()

    // If it throws (caught by error.tsx boundary):
    await expect(UsersPage()).rejects.toThrow('DB connection failed')
  })
})
```

### RSC with params

```typescript
// Source: app/posts/[slug]/page.tsx
// export default async function PostPage({ params }: { params: { slug: string } }) { ... }

import PostPage from '@/app/posts/[slug]/page'

it('renders post by slug', async () => {
  vi.mocked(getPostBySlug).mockResolvedValue({
    title: 'Hello World',
    content: 'Post content here',
  })

  // In Next.js 15+, params is a Promise
  const result = await PostPage({ params: Promise.resolve({ slug: 'hello-world' }) })
  render(result)

  expect(screen.getByRole('heading')).toHaveTextContent('Hello World')
  expect(getPostBySlug).toHaveBeenCalledWith('hello-world')
})
```

### RSC with searchParams

```typescript
// Source: app/search/page.tsx
// export default async function SearchPage({ searchParams }: { searchParams: { q?: string } }) { ... }

import SearchPage from '@/app/search/page'

it('searches with query parameter', async () => {
  vi.mocked(searchPosts).mockResolvedValue([
    { id: '1', title: 'React Testing' },
  ])

  // In Next.js 15+, searchParams is a Promise
  const result = await SearchPage({
    searchParams: Promise.resolve({ q: 'testing' }),
  })
  render(result)

  expect(searchPosts).toHaveBeenCalledWith('testing')
  expect(screen.getByText('React Testing')).toBeInTheDocument()
})
```

## Testing Server Actions

### Basic server action

```typescript
// Source: app/actions/posts.ts
// 'use server'
// export async function createPost(prevState: any, formData: FormData) { ... }

vi.mock('@/lib/db', () => ({
  insertPost: vi.fn(),
}))
vi.mock('next/cache', () => ({
  revalidatePath: vi.fn(),
  revalidateTag: vi.fn(),
}))

import { createPost } from '@/app/actions/posts'
import { insertPost } from '@/lib/db'
import { revalidatePath } from 'next/cache'

describe('createPost', () => {
  it('creates a post and revalidates', async () => {
    vi.mocked(insertPost).mockResolvedValue({ id: '1' })

    const formData = new FormData()
    formData.append('title', 'New Post')
    formData.append('content', 'Post content')

    const result = await createPost(null, formData)

    expect(insertPost).toHaveBeenCalledWith({
      title: 'New Post',
      content: 'Post content',
    })
    expect(revalidatePath).toHaveBeenCalledWith('/posts')
    expect(result).toEqual({ success: true, id: '1' })
  })

  it('returns validation errors for missing fields', async () => {
    const formData = new FormData()
    // Missing title and content

    const result = await createPost(null, formData)

    expect(result).toEqual({
      success: false,
      errors: {
        title: 'Title is required',
        content: 'Content is required',
      },
    })
    expect(insertPost).not.toHaveBeenCalled()
  })

  it('handles database failures gracefully', async () => {
    vi.mocked(insertPost).mockRejectedValue(new Error('Unique constraint'))

    const formData = new FormData()
    formData.append('title', 'Duplicate Post')
    formData.append('content', 'Content')

    const result = await createPost(null, formData)

    expect(result).toEqual({
      success: false,
      errors: { title: 'A post with this title already exists' },
    })
  })
})
```

### Server action with authentication

```typescript
vi.mock('next/headers', () => ({
  cookies: vi.fn(),
}))

import { cookies } from 'next/headers'

it('rejects unauthenticated requests', async () => {
  const mockCookies = { get: vi.fn().mockReturnValue(null) }
  vi.mocked(cookies).mockReturnValue(mockCookies as any)

  const formData = new FormData()
  formData.append('title', 'Test')

  const result = await createPost(null, formData)
  expect(result).toEqual({ success: false, errors: { auth: 'Not authenticated' } })
})
```

### Server action with redirect

```typescript
vi.mock('next/navigation', () => ({
  redirect: vi.fn(),
}))

import { redirect } from 'next/navigation'

it('redirects after successful creation', async () => {
  vi.mocked(insertPost).mockResolvedValue({ id: '42', slug: 'new-post' })

  const formData = new FormData()
  formData.append('title', 'New Post')
  formData.append('content', 'Content')

  await createPost(null, formData)

  expect(redirect).toHaveBeenCalledWith('/posts/new-post')
})
```

## Testing generateMetadata

```typescript
// Source: app/posts/[slug]/page.tsx
// export async function generateMetadata({ params }: { params: { slug: string } }) { ... }

import { generateMetadata } from '@/app/posts/[slug]/page'

describe('generateMetadata', () => {
  it('returns metadata for a valid post', async () => {
    vi.mocked(getPostBySlug).mockResolvedValue({
      title: 'My Post',
      description: 'A great post',
      image: '/og/my-post.png',
    })

    const metadata = await generateMetadata({
      params: Promise.resolve({ slug: 'my-post' }),
    })

    expect(metadata).toEqual(
      expect.objectContaining({
        title: 'My Post',
        description: 'A great post',
        openGraph: expect.objectContaining({
          images: ['/og/my-post.png'],
        }),
      })
    )
  })

  it('returns default metadata for unknown post', async () => {
    vi.mocked(getPostBySlug).mockResolvedValue(null)

    const metadata = await generateMetadata({
      params: Promise.resolve({ slug: 'nonexistent' }),
    })

    expect(metadata).toEqual(
      expect.objectContaining({
        title: 'Not Found',
      })
    )
  })
})
```

## Testing generateStaticParams

```typescript
// Source: app/posts/[slug]/page.tsx
// export async function generateStaticParams() { ... }

import { generateStaticParams } from '@/app/posts/[slug]/page'

describe('generateStaticParams', () => {
  it('returns params for all published posts', async () => {
    vi.mocked(getAllPostSlugs).mockResolvedValue([
      'first-post',
      'second-post',
    ])

    const params = await generateStaticParams()

    expect(params).toEqual([
      { slug: 'first-post' },
      { slug: 'second-post' },
    ])
  })

  it('returns empty array when no posts exist', async () => {
    vi.mocked(getAllPostSlugs).mockResolvedValue([])

    const params = await generateStaticParams()
    expect(params).toEqual([])
  })
})
```

## Testing Layout Components

```typescript
// Source: app/dashboard/layout.tsx
// export default async function DashboardLayout({ children }: { children: React.ReactNode }) { ... }

import DashboardLayout from '@/app/dashboard/layout'

it('renders layout with navigation and children', async () => {
  vi.mocked(getSession).mockResolvedValue({ user: { name: 'Alice' } })

  const result = await DashboardLayout({
    children: <div>Page Content</div>,
  })
  render(result)

  expect(screen.getByRole('navigation')).toBeInTheDocument()
  expect(screen.getByText('Alice')).toBeInTheDocument()
  expect(screen.getByText('Page Content')).toBeInTheDocument()
})

it('redirects when not authenticated', async () => {
  vi.mocked(getSession).mockResolvedValue(null)

  await DashboardLayout({ children: <div>Page Content</div> })

  expect(redirect).toHaveBeenCalledWith('/login')
})
```

## Testing Loading Components

```typescript
// Source: app/dashboard/loading.tsx
// export default function Loading() { ... }

import Loading from '@/app/dashboard/loading'

it('renders skeleton UI', () => {
  render(<Loading />)

  // Assert on the loading skeleton structure
  expect(screen.getByRole('status')).toBeInTheDocument()
  // Or check for specific skeleton elements
  expect(screen.getAllByTestId('skeleton-line')).toHaveLength(3)
})
```

## Testing Error Components

```typescript
// Source: app/dashboard/error.tsx
// 'use client'
// export default function Error({ error, reset }: { error: Error; reset: () => void }) { ... }

import Error from '@/app/dashboard/error'

it('displays error message and reset button', () => {
  const mockReset = vi.fn()

  render(<Error error={new Error('Something went wrong')} reset={mockReset} />)

  expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
})

it('calls reset when retry button is clicked', async () => {
  const user = userEvent.setup()
  const mockReset = vi.fn()

  render(<Error error={new Error('Error')} reset={mockReset} />)

  await user.click(screen.getByRole('button', { name: /try again/i }))
  expect(mockReset).toHaveBeenCalledTimes(1)
})
```

## Testing Not-Found Components

```typescript
// Source: app/not-found.tsx
import NotFound from '@/app/not-found'

it('renders 404 page with link to home', () => {
  render(<NotFound />)

  expect(screen.getByText('404')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: /home/i })).toHaveAttribute('href', '/')
})
```

## Mocking server-only

If your server components import from modules marked with `'server-only'`:

```typescript
// At the top of your test file, before other imports
vi.mock('server-only', () => ({}))
```

This prevents the `server-only` guard from throwing during tests.
