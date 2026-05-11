# Angular Mocking Guide

Comprehensive patterns for mocking services, HTTP, Router, and other
Angular dependencies in unit tests.

## jasmine.createSpyObj — Service Mocking

### Basic Service Mock

```typescript
// Create spy with methods
const userServiceSpy = jasmine.createSpyObj('UserService', [
  'getUsers',
  'getUserById',
  'createUser',
  'deleteUser',
]);

// Configure return values
userServiceSpy.getUsers.and.returnValue(of([user1, user2]));
userServiceSpy.getUserById.and.returnValue(of(user1));
userServiceSpy.createUser.and.returnValue(of(newUser));

// Provide in TestBed
providers: [
  { provide: UserService, useValue: userServiceSpy },
]
```

### Spy with Properties

```typescript
// Create spy with both methods and properties
const authServiceSpy = jasmine.createSpyObj('AuthService',
  ['login', 'logout'],           // Methods
  ['isAuthenticated', 'currentUser']  // Properties (getters)
);

// Configure property values
(Object.getOwnPropertyDescriptor(authServiceSpy, 'isAuthenticated')!
  .get as jasmine.Spy).and.returnValue(true);
(Object.getOwnPropertyDescriptor(authServiceSpy, 'currentUser')!
  .get as jasmine.Spy).and.returnValue({ name: 'Alice' });
```

### Spy with Observable Properties

```typescript
import { BehaviorSubject } from 'rxjs';

// For services with observable properties
const authServiceSpy = jasmine.createSpyObj('AuthService', ['login', 'logout']);
const isAuthenticated$ = new BehaviorSubject<boolean>(false);
(authServiceSpy as any).isAuthenticated$ = isAuthenticated$.asObservable();

// In test: change the value
isAuthenticated$.next(true);
fixture.detectChanges();
```

## HttpClientTestingModule

### Basic HTTP Mocking

```typescript
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

describe('UserService', () => {
  let service: UserService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [UserService],
    });

    service = TestBed.inject(UserService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify(); // Ensure no outstanding requests
  });

  it('should fetch users', () => {
    const mockUsers = [
      { id: 1, name: 'Alice' },
      { id: 2, name: 'Bob' },
    ];

    service.getUsers().subscribe(users => {
      expect(users.length).toBe(2);
      expect(users[0].name).toBe('Alice');
    });

    const req = httpMock.expectOne('/api/users');
    expect(req.request.method).toBe('GET');
    req.flush(mockUsers);
  });

  it('should create user with POST', () => {
    const newUser = { name: 'Alice', email: 'alice@test.com' };

    service.createUser(newUser).subscribe(user => {
      expect(user.id).toBe(1);
    });

    const req = httpMock.expectOne('/api/users');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(newUser);
    req.flush({ id: 1, ...newUser });
  });

  it('should handle HTTP error', () => {
    service.getUsers().subscribe({
      next: () => fail('should have failed'),
      error: (error) => {
        expect(error.status).toBe(500);
      },
    });

    const req = httpMock.expectOne('/api/users');
    req.flush('Server error', {
      status: 500,
      statusText: 'Internal Server Error',
    });
  });

  it('should send authorization header', () => {
    service.getProtectedResource().subscribe();

    const req = httpMock.expectOne('/api/protected');
    expect(req.request.headers.get('Authorization')).toBe('Bearer test-token');
    req.flush({});
  });

  it('should handle query parameters', () => {
    service.searchUsers('alice', 1, 10).subscribe();

    const req = httpMock.expectOne(
      req => req.url === '/api/users' &&
             req.params.get('q') === 'alice' &&
             req.params.get('page') === '1'
    );
    req.flush([]);
  });
});
```

### Multiple HTTP Requests

```typescript
it('should load user and their orders', () => {
  service.getUserWithOrders(1).subscribe(result => {
    expect(result.user.name).toBe('Alice');
    expect(result.orders.length).toBe(2);
  });

  const userReq = httpMock.expectOne('/api/users/1');
  userReq.flush({ id: 1, name: 'Alice' });

  const ordersReq = httpMock.expectOne('/api/users/1/orders');
  ordersReq.flush([{ id: 1 }, { id: 2 }]);
});
```

## Router Mocking

### RouterTestingModule

```typescript
import { RouterTestingModule } from '@angular/router/testing';

await TestBed.configureTestingModule({
  imports: [
    MyComponent,
    RouterTestingModule.withRoutes([
      { path: 'users', component: MockUserListComponent },
      { path: 'users/:id', component: MockUserDetailComponent },
    ]),
  ],
}).compileComponents();
```

### ActivatedRoute Mock

```typescript
import { ActivatedRoute, convertToParamMap, ParamMap } from '@angular/router';
import { BehaviorSubject, of } from 'rxjs';

// Static params
{
  provide: ActivatedRoute,
  useValue: {
    paramMap: of(convertToParamMap({ id: '42' })),
    queryParamMap: of(convertToParamMap({ sort: 'name' })),
    snapshot: {
      paramMap: convertToParamMap({ id: '42' }),
      queryParamMap: convertToParamMap({ sort: 'name' }),
      data: { title: 'User Detail' },
    },
    data: of({ title: 'User Detail' }),
  },
}

// Dynamic params (change during test)
const paramMapSubject = new BehaviorSubject<ParamMap>(convertToParamMap({ id: '1' }));

{
  provide: ActivatedRoute,
  useValue: {
    paramMap: paramMapSubject.asObservable(),
  },
}

// In test: change route params
paramMapSubject.next(convertToParamMap({ id: '2' }));
fixture.detectChanges();
```

### Router.navigate Mock

```typescript
const routerSpy = jasmine.createSpyObj('Router', ['navigate', 'navigateByUrl']);

providers: [
  { provide: Router, useValue: routerSpy },
]

// Assert
expect(routerSpy.navigate).toHaveBeenCalledWith(['/users', 42]);
```

## Dialog / Modal Mocking

### MatDialog

```typescript
import { MatDialogModule, MatDialog, MatDialogRef } from '@angular/material/dialog';

const dialogRefSpy = jasmine.createSpyObj('MatDialogRef', ['afterClosed', 'close']);
dialogRefSpy.afterClosed.and.returnValue(of(true));

const dialogSpy = jasmine.createSpyObj('MatDialog', ['open']);
dialogSpy.open.and.returnValue(dialogRefSpy);

providers: [
  { provide: MatDialog, useValue: dialogSpy },
]

// Assert
expect(dialogSpy.open).toHaveBeenCalledWith(ConfirmDialogComponent, jasmine.any(Object));
```

## Store Mocking (NgRx)

```typescript
import { provideMockStore, MockStore } from '@ngrx/store/testing';

describe('UserListComponent', () => {
  let store: MockStore;
  const initialState = {
    users: {
      list: [],
      loading: false,
      error: null,
    },
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserListComponent],
      providers: [
        provideMockStore({ initialState }),
      ],
    }).compileComponents();

    store = TestBed.inject(MockStore);
  });

  it('should dispatch loadUsers on init', () => {
    const spy = spyOn(store, 'dispatch');
    fixture.detectChanges();
    expect(spy).toHaveBeenCalledWith(loadUsers());
  });

  it('should display users from store', () => {
    store.setState({
      users: {
        list: [{ id: 1, name: 'Alice' }],
        loading: false,
        error: null,
      },
    });
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.user-name').textContent)
      .toContain('Alice');
  });

  it('should show loading spinner', () => {
    store.setState({
      users: { list: [], loading: true, error: null },
    });
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.spinner')).toBeTruthy();
  });
});
```

## Window / Document / LocalStorage Mocking

```typescript
// Provide as injection token
import { DOCUMENT } from '@angular/common';

const mockDocument = {
  querySelector: jasmine.createSpy('querySelector'),
  addEventListener: jasmine.createSpy('addEventListener'),
};

providers: [
  { provide: DOCUMENT, useValue: mockDocument },
]

// LocalStorage
const localStorageSpy = jasmine.createSpyObj('localStorage', [
  'getItem', 'setItem', 'removeItem', 'clear'
]);
localStorageSpy.getItem.and.callFake((key: string) => {
  const store: Record<string, string> = { token: 'abc123' };
  return store[key] ?? null;
});

// In test setup
spyOn(window.localStorage, 'getItem').and.callFake(localStorageSpy.getItem);
spyOn(window.localStorage, 'setItem').and.callFake(localStorageSpy.setItem);
```

## Anti-Patterns to Avoid

1. **Don't import real `HttpClientModule`** — always use `HttpClientTestingModule`
2. **Don't use real Router** — use `RouterTestingModule` or mock `Router`
3. **Don't share spy state between tests** — reset in `beforeEach`
4. **Don't forget `fixture.detectChanges()`** — Angular won't update the DOM without it
5. **Don't forget `httpMock.verify()`** in `afterEach` — catches unmatched requests
6. **Don't mock the component under test** — mock its dependencies only
7. **Don't import entire feature modules in tests** — import only what's needed
