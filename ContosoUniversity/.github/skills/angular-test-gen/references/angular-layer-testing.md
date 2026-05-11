# Angular Layer Testing Patterns

Per-layer testing strategies for Angular applications.

## Component Layer

### Smart (Container) Component

```typescript
describe('UserDashboardComponent', () => {
  let component: UserDashboardComponent;
  let fixture: ComponentFixture<UserDashboardComponent>;
  let userServiceSpy: jasmine.SpyObj<UserService>;

  beforeEach(async () => {
    userServiceSpy = jasmine.createSpyObj('UserService', ['getUsers', 'deleteUser']);
    userServiceSpy.getUsers.and.returnValue(of([
      { id: 1, name: 'Alice', role: 'admin' },
      { id: 2, name: 'Bob', role: 'user' },
    ]));

    await TestBed.configureTestingModule({
      imports: [UserDashboardComponent],
      providers: [{ provide: UserService, useValue: userServiceSpy }],
    }).compileComponents();

    fixture = TestBed.createComponent(UserDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should load and display users on init', () => {
    expect(userServiceSpy.getUsers).toHaveBeenCalled();
    const rows = fixture.nativeElement.querySelectorAll('.user-row');
    expect(rows.length).toBe(2);
  });

  it('should show loading state', () => {
    component.loading = true;
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.spinner')).toBeTruthy();
  });

  it('should show error state on service failure', () => {
    userServiceSpy.getUsers.and.returnValue(throwError(() => new Error('Server error')));

    // Re-trigger load
    component.ngOnInit();
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.error-message')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('.error-message').textContent)
      .toContain('Server error');
  });

  it('should show empty state when no users', () => {
    userServiceSpy.getUsers.and.returnValue(of([]));
    component.ngOnInit();
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.empty-state')).toBeTruthy();
  });

  it('should delete user and refresh list', () => {
    userServiceSpy.deleteUser.and.returnValue(of(undefined));
    userServiceSpy.getUsers.and.returnValue(of([{ id: 2, name: 'Bob', role: 'user' }]));

    component.onDelete(1);
    fixture.detectChanges();

    expect(userServiceSpy.deleteUser).toHaveBeenCalledWith(1);
    const rows = fixture.nativeElement.querySelectorAll('.user-row');
    expect(rows.length).toBe(1);
  });
});
```

### Presentational (Dumb) Component

```typescript
describe('UserCardComponent', () => {
  let component: UserCardComponent;
  let fixture: ComponentFixture<UserCardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserCardComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(UserCardComponent);
    component = fixture.componentInstance;
  });

  it('should render user details', () => {
    component.user = { id: 1, name: 'Alice', email: 'alice@test.com' };
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.name').textContent).toContain('Alice');
    expect(fixture.nativeElement.querySelector('.email').textContent).toContain('alice@test.com');
  });

  it('should emit edit event', () => {
    component.user = { id: 1, name: 'Alice', email: 'alice@test.com' };
    fixture.detectChanges();

    spyOn(component.edit, 'emit');
    fixture.nativeElement.querySelector('.edit-btn').click();

    expect(component.edit.emit).toHaveBeenCalledWith(component.user);
  });

  it('should apply active class when user is active', () => {
    component.user = { id: 1, name: 'Alice', email: 'a@t.com', active: true };
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.user-card').classList).toContain('active');
  });

  it('should not render when user is null', () => {
    component.user = null as any;
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.user-card')).toBeFalsy();
  });
});
```

## Service Layer

### Data Service with HTTP

```typescript
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
    httpMock.verify();
  });

  it('should get all users', () => {
    const mockUsers = [{ id: 1, name: 'Alice' }];

    service.getUsers().subscribe(users => {
      expect(users).toEqual(mockUsers);
    });

    const req = httpMock.expectOne('/api/users');
    expect(req.request.method).toBe('GET');
    req.flush(mockUsers);
  });

  it('should handle 404 error', () => {
    service.getUserById(999).subscribe({
      next: () => fail('should have errored'),
      error: (error) => {
        expect(error.status).toBe(404);
      },
    });

    const req = httpMock.expectOne('/api/users/999');
    req.flush('Not found', { status: 404, statusText: 'Not Found' });
  });
});
```

### Business Logic Service

```typescript
describe('PricingService', () => {
  let service: PricingService;
  let productServiceSpy: jasmine.SpyObj<ProductService>;
  let discountServiceSpy: jasmine.SpyObj<DiscountService>;

  beforeEach(() => {
    productServiceSpy = jasmine.createSpyObj('ProductService', ['getById']);
    discountServiceSpy = jasmine.createSpyObj('DiscountService', ['getDiscount']);

    TestBed.configureTestingModule({
      providers: [
        PricingService,
        { provide: ProductService, useValue: productServiceSpy },
        { provide: DiscountService, useValue: discountServiceSpy },
      ],
    });

    service = TestBed.inject(PricingService);
  });

  it('should apply percentage discount', () => {
    productServiceSpy.getById.and.returnValue(of({ id: 1, price: 100 }));
    discountServiceSpy.getDiscount.and.returnValue(of({ type: 'percentage', value: 20 }));

    service.calculateFinalPrice(1).subscribe(price => {
      expect(price).toBe(80);
    });
  });

  it('should not go below zero with fixed discount', () => {
    productServiceSpy.getById.and.returnValue(of({ id: 1, price: 10 }));
    discountServiceSpy.getDiscount.and.returnValue(of({ type: 'fixed', value: 15 }));

    service.calculateFinalPrice(1).subscribe(price => {
      expect(price).toBe(0);
    });
  });
});
```

## Pipe Layer

```typescript
describe('CurrencyFormatPipe', () => {
  let pipe: CurrencyFormatPipe;

  beforeEach(() => {
    pipe = new CurrencyFormatPipe();
  });

  it('should format number as USD', () => {
    expect(pipe.transform(1234.5, 'USD')).toBe('$1,234.50');
  });

  it('should format number as EUR', () => {
    expect(pipe.transform(1234.5, 'EUR')).toBe('€1,234.50');
  });

  it('should handle zero', () => {
    expect(pipe.transform(0, 'USD')).toBe('$0.00');
  });

  it('should handle null', () => {
    expect(pipe.transform(null as any, 'USD')).toBe('');
  });

  it('should handle negative values', () => {
    expect(pipe.transform(-50, 'USD')).toBe('-$50.00');
  });
});
```

## Directive Layer

```typescript
// Test directive with a host component
@Component({
  template: `<input appHighlight [color]="highlightColor">`,
})
class TestHostComponent {
  highlightColor = 'yellow';
}

describe('HighlightDirective', () => {
  let fixture: ComponentFixture<TestHostComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [TestHostComponent],
      imports: [HighlightDirective], // If standalone
    }).compileComponents();

    fixture = TestBed.createComponent(TestHostComponent);
    fixture.detectChanges();
  });

  it('should apply highlight on focus', () => {
    const input = fixture.nativeElement.querySelector('input');
    input.dispatchEvent(new Event('focus'));
    fixture.detectChanges();

    expect(input.style.backgroundColor).toBe('yellow');
  });

  it('should remove highlight on blur', () => {
    const input = fixture.nativeElement.querySelector('input');
    input.dispatchEvent(new Event('focus'));
    input.dispatchEvent(new Event('blur'));
    fixture.detectChanges();

    expect(input.style.backgroundColor).toBe('');
  });
});
```

## Guard Layer

```typescript
describe('AuthGuard', () => {
  let guard: AuthGuard;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(() => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['isAuthenticated']);
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    TestBed.configureTestingModule({
      providers: [
        AuthGuard,
        { provide: AuthService, useValue: authServiceSpy },
        { provide: Router, useValue: routerSpy },
      ],
    });

    guard = TestBed.inject(AuthGuard);
  });

  it('should allow access when authenticated', () => {
    authServiceSpy.isAuthenticated.and.returnValue(true);

    const result = guard.canActivate({} as any, {} as any);

    expect(result).toBeTrue();
  });

  it('should redirect to login when not authenticated', () => {
    authServiceSpy.isAuthenticated.and.returnValue(false);

    const result = guard.canActivate({} as any, {} as any);

    expect(result).toBeFalse();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/login']);
  });
});

// Functional guard (Angular 15+)
describe('authGuard (functional)', () => {
  it('should allow access when authenticated', () => {
    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: { isAuthenticated: () => true } },
        { provide: Router, useValue: jasmine.createSpyObj('Router', ['navigate']) },
      ],
    });

    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as any, {} as any)
    );

    expect(result).toBeTrue();
  });
});
```

## Interceptor Layer

```typescript
describe('AuthInterceptor', () => {
  let httpMock: HttpTestingController;
  let http: HttpClient;
  let tokenServiceSpy: jasmine.SpyObj<TokenService>;

  beforeEach(() => {
    tokenServiceSpy = jasmine.createSpyObj('TokenService', ['getToken']);
    tokenServiceSpy.getToken.and.returnValue('test-token');

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        { provide: TokenService, useValue: tokenServiceSpy },
        {
          provide: HTTP_INTERCEPTORS,
          useClass: AuthInterceptor,
          multi: true,
        },
      ],
    });

    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should add Authorization header', () => {
    http.get('/api/data').subscribe();

    const req = httpMock.expectOne('/api/data');
    expect(req.request.headers.get('Authorization')).toBe('Bearer test-token');
    req.flush({});
  });

  it('should not add header when no token', () => {
    tokenServiceSpy.getToken.and.returnValue(null);

    http.get('/api/data').subscribe();

    const req = httpMock.expectOne('/api/data');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });
});
```

## NgRx Layer

### Reducer Testing

```typescript
describe('UserReducer', () => {
  it('should return initial state', () => {
    const result = userReducer(undefined, { type: 'unknown' });
    expect(result).toEqual(initialUserState);
  });

  it('should set loading on loadUsers', () => {
    const result = userReducer(initialUserState, loadUsers());
    expect(result.loading).toBeTrue();
    expect(result.error).toBeNull();
  });

  it('should set users on loadUsersSuccess', () => {
    const users = [{ id: 1, name: 'Alice' }];
    const result = userReducer(initialUserState, loadUsersSuccess({ users }));
    expect(result.list).toEqual(users);
    expect(result.loading).toBeFalse();
  });
});
```

### Selector Testing

```typescript
describe('User Selectors', () => {
  const state = {
    users: {
      list: [
        { id: 1, name: 'Alice', active: true },
        { id: 2, name: 'Bob', active: false },
      ],
      loading: false,
    },
  };

  it('should select all users', () => {
    expect(selectAllUsers.projector(state.users)).toEqual(state.users.list);
  });

  it('should select active users', () => {
    const result = selectActiveUsers.projector(state.users.list);
    expect(result.length).toBe(1);
    expect(result[0].name).toBe('Alice');
  });
});
```

### Effects Testing

```typescript
import { provideMockActions } from '@ngrx/effects/testing';
import { ReplaySubject } from 'rxjs';

describe('UserEffects', () => {
  let effects: UserEffects;
  let actions$: ReplaySubject<Action>;
  let userServiceSpy: jasmine.SpyObj<UserService>;

  beforeEach(() => {
    actions$ = new ReplaySubject<Action>(1);
    userServiceSpy = jasmine.createSpyObj('UserService', ['getUsers']);

    TestBed.configureTestingModule({
      providers: [
        UserEffects,
        provideMockActions(() => actions$),
        { provide: UserService, useValue: userServiceSpy },
      ],
    });

    effects = TestBed.inject(UserEffects);
  });

  it('should dispatch loadUsersSuccess on successful load', (done) => {
    const users = [{ id: 1, name: 'Alice' }];
    userServiceSpy.getUsers.and.returnValue(of(users));

    effects.loadUsers$.subscribe(action => {
      expect(action).toEqual(loadUsersSuccess({ users }));
      done();
    });

    actions$.next(loadUsers());
  });

  it('should dispatch loadUsersFailure on error', (done) => {
    userServiceSpy.getUsers.and.returnValue(throwError(() => new Error('fail')));

    effects.loadUsers$.subscribe(action => {
      expect(action).toEqual(loadUsersFailure({ error: 'fail' }));
      done();
    });

    actions$.next(loadUsers());
  });
});
```
