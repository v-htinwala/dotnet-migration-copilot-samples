# Angular Regression Testing Patterns

## Common Regression Scenarios

### 1. Component Changes
When an Angular component class or template is modified, generate regression tests that:
- Verify the component still renders expected content via `ComponentFixture` + `detectChanges()`
- Check `@Input()` bindings still pass data correctly to the template
- Validate `@Output()` events still emit expected values
- Test lifecycle hooks (`ngOnInit`, `ngOnChanges`, `ngOnDestroy`) still execute correctly
- Confirm template bindings and interpolation produce expected DOM output

### 2. Service Changes
When an `@Injectable` service is modified:
- Verify the method still produces correct output for all known input combinations
- Check that downstream consumers (components, other services) receive the same data contracts
- Validate that error/exception behavior is preserved
- Confirm Observable chains return expected values and complete correctly
- Test HTTP services via `HttpClientTestingModule` + `HttpTestingController`
- **For `test_level=integration`**: use `HttpClientTestingModule` with real `HttpTestingController` (see Integration Patterns below)

### 3. Guard/Resolver Changes
When a route guard (`CanActivate`, `CanDeactivate`, `CanLoad`) or resolver is modified:
- Verify the guard still returns the correct boolean/`UrlTree` for authenticated/unauthenticated users
- Test with `RouterTestingModule` and `ActivatedRouteSnapshot` mocks
- Validate redirect behavior is preserved
- Check resolver still returns expected data before route activation

### 4. Interceptor Changes
When an `HttpInterceptor` is modified:
- Verify the interceptor still modifies requests/responses as expected
- Test header injection (e.g., auth token) is preserved
- Validate error handling and retry behavior
- Use `HttpClientTestingModule` with interceptor verification

### 5. Pipe Changes
When a custom `@Pipe` is modified:
- Verify transform method produces correct output for known inputs
- Test with null/undefined inputs
- Validate parameterized pipe behavior
- Direct pipe instantiation tests (no TestBed needed)

### 6. Directive Changes
When a custom directive is modified:
- Use TestBed with a host component pattern
- Verify the directive still modifies DOM elements as expected
- Test structural directives for correct template rendering
- Validate attribute directive behavior on host elements

### 7. Reactive Forms Changes
When form-related code is modified:
- Verify `FormBuilder`/`FormGroup`/`FormControl` setup is preserved
- Test validators still enforce correct rules
- Validate cross-field validators produce expected results
- Check form submission behavior is preserved

### 8. NgRx/State Management Changes
When NgRx store, actions, reducers, effects, or selectors are modified:
- Test reducers produce correct state transitions
- Verify selectors return expected derived state
- Test effects trigger correct actions and side effects
- Use `provideMockStore` for component tests with store dependencies

## Angular TestBed Regression Test Structure

### Jasmine (Default)
```typescript
describe('Regression: UserService after PR #123', () => {
  let service: UserService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [UserService]
    });
    service = TestBed.inject(UserService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  // --- Behavior Preservation Tests ---

  it('should still return user by ID', () => {
    const mockUser = { id: 1, email: 'test@example.com', name: 'Test' };

    service.getUserById(1).subscribe(user => {
      expect(user).toEqual(mockUser);
    });

    const req = httpMock.expectOne('/api/users/1');
    expect(req.request.method).toBe('GET');
    req.flush(mockUser);
  });

  // --- Exception Contract Tests ---

  it('should still throw error for non-existent user', () => {
    service.getUserById(999).subscribe({
      error: (err) => {
        expect(err.status).toBe(404);
      }
    });

    const req = httpMock.expectOne('/api/users/999');
    req.flush('Not found', { status: 404, statusText: 'Not Found' });
  });

  // --- Integration Point Regression ---

  it('should still call the correct API endpoint', () => {
    service.createUser({ email: 'new@example.com', name: 'New' }).subscribe();

    const req = httpMock.expectOne('/api/users');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ email: 'new@example.com', name: 'New' });
    req.flush({ id: 2 });
  });
});
```

### Jest Variant
```typescript
describe('Regression: UserService after PR #123', () => {
  let service: UserService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [UserService]
    });
    service = TestBed.inject(UserService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  test('still returns user by ID', () => {
    const mockUser = { id: 1, email: 'test@example.com', name: 'Test' };

    service.getUserById(1).subscribe(user => {
      expect(user).toEqual(mockUser);
    });

    const req = httpMock.expectOne('/api/users/1');
    expect(req.request.method).toBe('GET');
    req.flush(mockUser);
  });
});
```

## Component Test Patterns

### Component with Service Dependency
```typescript
describe('Regression: UserListComponent', () => {
  let component: UserListComponent;
  let fixture: ComponentFixture<UserListComponent>;
  let mockUserService: jasmine.SpyObj<UserService>;

  beforeEach(async () => {
    mockUserService = jasmine.createSpyObj('UserService', ['getUsers', 'deleteUser']);

    await TestBed.configureTestingModule({
      declarations: [UserListComponent],
      providers: [
        { provide: UserService, useValue: mockUserService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(UserListComponent);
    component = fixture.componentInstance;
  });

  it('should still render user list after data loads', () => {
    mockUserService.getUsers.and.returnValue(of([
      { id: 1, name: 'Alice' },
      { id: 2, name: 'Bob' }
    ]));

    fixture.detectChanges();

    const items = fixture.nativeElement.querySelectorAll('.user-item');
    expect(items.length).toBe(2);
    expect(items[0].textContent).toContain('Alice');
  });

  it('should still show loading state initially', () => {
    mockUserService.getUsers.and.returnValue(new Subject());
    fixture.detectChanges();

    const loading = fixture.nativeElement.querySelector('.loading');
    expect(loading).toBeTruthy();
  });
});
```

### Component with @Input/@Output
```typescript
describe('Regression: UserCardComponent', () => {
  let component: UserCardComponent;
  let fixture: ComponentFixture<UserCardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [UserCardComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(UserCardComponent);
    component = fixture.componentInstance;
  });

  it('should still render user name from @Input', () => {
    component.user = { id: 1, name: 'Alice', email: 'alice@example.com' };
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.user-name').textContent).toContain('Alice');
  });

  it('should still emit delete event from @Output', () => {
    component.user = { id: 1, name: 'Alice', email: 'alice@example.com' };
    fixture.detectChanges();

    spyOn(component.delete, 'emit');
    fixture.nativeElement.querySelector('.delete-btn').click();

    expect(component.delete.emit).toHaveBeenCalledWith(1);
  });
});
```

## Mocking Patterns for Regression Testing

### Jasmine — jasmine.createSpyObj
```typescript
// Create spy object with methods
const mockService = jasmine.createSpyObj('UserService', ['getUsers', 'createUser', 'deleteUser']);
mockService.getUsers.and.returnValue(of(mockUsers));
mockService.createUser.and.returnValue(of(newUser));

// Verify interactions
expect(mockService.getUsers).toHaveBeenCalled();
expect(mockService.createUser).toHaveBeenCalledWith(jasmine.objectContaining({ email: 'test@example.com' }));
```

### Jest — jest.fn / jest.mock
```typescript
// Create mock service
const mockService = {
  getUsers: jest.fn().mockReturnValue(of(mockUsers)),
  createUser: jest.fn().mockReturnValue(of(newUser)),
  deleteUser: jest.fn().mockReturnValue(of(undefined)),
};

// Verify interactions
expect(mockService.getUsers).toHaveBeenCalled();
expect(mockService.createUser).toHaveBeenCalledWith(expect.objectContaining({ email: 'test@example.com' }));
```

### TestBed.overrideProvider
```typescript
TestBed.overrideProvider(UserService, { useValue: mockUserService });
```

## Guard Test Pattern
```typescript
describe('Regression: AuthGuard', () => {
  let guard: AuthGuard;
  let mockAuthService: jasmine.SpyObj<AuthService>;
  let mockRouter: jasmine.SpyObj<Router>;

  beforeEach(() => {
    mockAuthService = jasmine.createSpyObj('AuthService', ['isAuthenticated']);
    mockRouter = jasmine.createSpyObj('Router', ['createUrlTree']);

    TestBed.configureTestingModule({
      providers: [
        AuthGuard,
        { provide: AuthService, useValue: mockAuthService },
        { provide: Router, useValue: mockRouter }
      ]
    });

    guard = TestBed.inject(AuthGuard);
  });

  it('should still allow access for authenticated users', () => {
    mockAuthService.isAuthenticated.and.returnValue(true);
    const result = guard.canActivate({} as any, {} as any);
    expect(result).toBe(true);
  });

  it('should still redirect unauthenticated users to login', () => {
    mockAuthService.isAuthenticated.and.returnValue(false);
    const mockUrlTree = {} as UrlTree;
    mockRouter.createUrlTree.and.returnValue(mockUrlTree);

    const result = guard.canActivate({} as any, {} as any);
    expect(mockRouter.createUrlTree).toHaveBeenCalledWith(['/login']);
  });
});
```

## Interceptor Test Pattern
```typescript
describe('Regression: TokenInterceptor', () => {
  let httpMock: HttpTestingController;
  let httpClient: HttpClient;
  let mockAuthService: jasmine.SpyObj<AuthService>;

  beforeEach(() => {
    mockAuthService = jasmine.createSpyObj('AuthService', ['getToken']);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        { provide: HTTP_INTERCEPTORS, useClass: TokenInterceptor, multi: true },
        { provide: AuthService, useValue: mockAuthService }
      ]
    });

    httpMock = TestBed.inject(HttpTestingController);
    httpClient = TestBed.inject(HttpClient);
  });

  it('should still add Authorization header', () => {
    mockAuthService.getToken.and.returnValue('test-token');

    httpClient.get('/api/data').subscribe();

    const req = httpMock.expectOne('/api/data');
    expect(req.request.headers.get('Authorization')).toBe('Bearer test-token');
    req.flush({});
  });
});
```

## Pipe Test Pattern
```typescript
describe('Regression: CurrencyFormatPipe', () => {
  let pipe: CurrencyFormatPipe;

  beforeEach(() => {
    pipe = new CurrencyFormatPipe();
  });

  it('should still format positive numbers correctly', () => {
    expect(pipe.transform(1234.56)).toBe('$1,234.56');
  });

  it('should still handle null gracefully', () => {
    expect(pipe.transform(null)).toBe('$0.00');
  });

  it('should still apply custom currency parameter', () => {
    expect(pipe.transform(100, 'EUR')).toBe('€100.00');
  });
});
```

## Directive Test Pattern (Host Component)
```typescript
@Component({
  template: `<div appHighlight [color]="testColor">Test Content</div>`
})
class HostComponent {
  testColor = 'yellow';
}

describe('Regression: HighlightDirective', () => {
  let fixture: ComponentFixture<HostComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [HostComponent, HighlightDirective]
    }).compileComponents();

    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
  });

  it('should still apply background color', () => {
    const div = fixture.nativeElement.querySelector('div');
    expect(div.style.backgroundColor).toBe('yellow');
  });
});
```

## Reactive Forms Test Pattern
```typescript
describe('Regression: RegistrationFormComponent', () => {
  let component: RegistrationFormComponent;
  let fixture: ComponentFixture<RegistrationFormComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReactiveFormsModule],
      declarations: [RegistrationFormComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(RegistrationFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should still validate email field', () => {
    const emailControl = component.form.get('email');
    emailControl?.setValue('invalid');
    expect(emailControl?.valid).toBeFalse();

    emailControl?.setValue('valid@example.com');
    expect(emailControl?.valid).toBeTrue();
  });

  it('should still validate password match', () => {
    component.form.get('password')?.setValue('secret123');
    component.form.get('confirmPassword')?.setValue('different');
    expect(component.form.hasError('passwordMismatch')).toBeTrue();
  });
});
```

## NgRx Test Patterns

### Reducer Test
```typescript
describe('Regression: UserReducer', () => {
  it('should still add user on AddUser action', () => {
    const initialState = { users: [], loading: false };
    const newUser = { id: 1, name: 'Alice' };
    const action = addUser({ user: newUser });

    const result = userReducer(initialState, action);

    expect(result.users).toEqual([newUser]);
    expect(result.loading).toBeFalse();
  });
});
```

### Selector Test
```typescript
describe('Regression: UserSelectors', () => {
  it('should still select active users', () => {
    const state = {
      users: {
        users: [
          { id: 1, name: 'Alice', active: true },
          { id: 2, name: 'Bob', active: false }
        ],
        loading: false
      }
    };

    const result = selectActiveUsers.projector(state.users);
    expect(result).toEqual([{ id: 1, name: 'Alice', active: true }]);
  });
});
```

### Effect Test
```typescript
describe('Regression: UserEffects', () => {
  let effects: UserEffects;
  let actions$: Observable<Action>;
  let mockUserService: jasmine.SpyObj<UserService>;

  beforeEach(() => {
    mockUserService = jasmine.createSpyObj('UserService', ['getUsers']);

    TestBed.configureTestingModule({
      providers: [
        UserEffects,
        provideMockActions(() => actions$),
        { provide: UserService, useValue: mockUserService }
      ]
    });

    effects = TestBed.inject(UserEffects);
  });

  it('should still dispatch loadUsersSuccess on successful load', () => {
    const users = [{ id: 1, name: 'Alice' }];
    mockUserService.getUsers.and.returnValue(of(users));
    actions$ = hot('-a', { a: loadUsers() });

    const expected = cold('-b', { b: loadUsersSuccess({ users }) });
    expect(effects.loadUsers$).toBeObservable(expected);
  });
});
```

## Common Angular Regression Risks

| Risk | Detection | Mitigation |
|---|---|---|
| Template binding changes | `{{}}` or `[prop]` modified | Test rendered DOM output |
| @Input contract break | Input type or name changed | Test all parent component usage |
| @Output event schema change | Event payload structure modified | Test event emission with spies |
| Service API contract break | Method signature or return type changed | Test all consuming components |
| Guard logic change | Condition or redirect modified | Test auth scenarios explicitly |
| Interceptor header change | Authorization header logic modified | Test request interception |
| Pipe transform change | Transform logic modified | Test with known input/output pairs |
| RxJS operator change | Observable chain restructured | Test async behavior with `fakeAsync`/`waitForAsync` |
| Lifecycle hook change | `ngOnInit`/`ngOnDestroy` modified | Test hooks with lifecycle triggers |
| Route config change | Path or guard assignment modified | Test routing with `RouterTestingModule` |

## Data-Driven Regression Tests

When user-provided test data is available, prefer loading data from fixture files
over hardcoded inline values.

### JSON Fixture Loading
```typescript
import fixtureData from '../../../test-data/users.json';

describe('Regression: UserService (data-driven)', () => {
  it('should process all fixture users correctly', () => {
    fixtureData.forEach((user: any) => {
      const result = service.processUser(user);
      expect(result).toBeTruthy();
      expect(result.id).toBe(user.id);
    });
  });
});
```

### HttpTestingController with Fixture Responses
```typescript
it('should handle fixture response correctly', () => {
  const fixtureResponse = require('../../../test-data/api-responses/users.json');

  service.getUsers().subscribe(users => {
    expect(users.length).toBe(fixtureResponse.length);
  });

  const req = httpMock.expectOne('/api/users');
  req.flush(fixtureResponse);
});
```

### Golden-File Assertion Pattern
```typescript
import * as fs from 'fs';

it('should still produce expected output structure', () => {
  const actual = service.transformUser(inputUser);
  const expected = JSON.parse(
    fs.readFileSync('src/test-data/expected/user-output.json', 'utf-8')
  );

  expect(actual).toEqual(expected);
});
```

## Integration Regression Test Patterns

Use these patterns when `test_level` is `integration` or `both`.

### HttpClientTestingModule — Service Integration
```typescript
describe('Regression: UserService integration', () => {
  let service: UserService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [UserService]
    });
    service = TestBed.inject(UserService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should make correct API calls end-to-end', () => {
    service.createUser({ name: 'Alice', email: 'alice@example.com' }).subscribe(user => {
      expect(user.id).toBeDefined();
    });

    const req = httpMock.expectOne('/api/users');
    expect(req.request.method).toBe('POST');
    req.flush({ id: 1, name: 'Alice', email: 'alice@example.com' });
  });
});
```

### RouterTestingModule — Component/Guard Integration
```typescript
describe('Regression: AppComponent routing integration', () => {
  let router: Router;
  let location: Location;
  let fixture: ComponentFixture<AppComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        RouterTestingModule.withRoutes([
          { path: '', component: HomeComponent },
          { path: 'users', component: UserListComponent },
          { path: 'login', component: LoginComponent }
        ])
      ],
      declarations: [AppComponent, HomeComponent, UserListComponent, LoginComponent]
    }).compileComponents();

    router = TestBed.inject(Router);
    location = TestBed.inject(Location);
    fixture = TestBed.createComponent(AppComponent);
  });

  it('should still navigate to users page', async () => {
    await router.navigate(['/users']);
    expect(location.path()).toBe('/users');
  });
});
```

### Full Module Integration
```typescript
describe('Regression: UserModule integration', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        UserModule,
        HttpClientTestingModule,
        RouterTestingModule,
        NoopAnimationsModule
      ]
    }).compileComponents();
  });

  it('should create all module components without error', () => {
    const fixture = TestBed.createComponent(UserListComponent);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
```

## Requirement-Traced Regression Tests

When requirement IDs or regression scenarios are provided, use structured
annotations for traceability.

### Scenario-Driven Nested Describe Blocks
```typescript
// @requirement REQ-PAY-001
// @requirement REQ-PAY-002
describe('Regression: PaymentService', () => {

  describe('Scenario: Payment Processing Integrity [REQ-PAY-001]', () => {
    it('[REQ-PAY-001] should still deduct correct amount from wallet', () => {
      // ...
    });

    it('[REQ-PAY-001] should still create transaction record with COMPLETED status', () => {
      // ...
    });
  });

  describe('Scenario: Payment Backward Compatibility [REQ-PAY-002]', () => {
    it('[REQ-PAY-002] should still accept legacy payment format', () => {
      // ...
    });
  });
});
```

## CI/CD Integration Patterns

### Karma — JUnit XML Reporter
Add to `karma.conf.js`:
```javascript
module.exports = function(config) {
  config.set({
    reporters: ['progress', 'junit'],
    junitReporter: {
      outputDir: 'regression-reports',
      outputFile: 'regression-results.xml',
      useBrowserName: false
    }
  });
};
```

### Jest — JUnit Reporter
Add to `jest.config.js`:
```javascript
module.exports = {
  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: 'regression-reports',
      outputName: 'regression-results.xml'
    }]
  ]
};
```

### Flaky Test Detection
```typescript
// Mark known flaky tests for quarantine
// @flaky - intermittent due to async timing
describe('Regression: WebSocketService (flaky)', () => {
  it('should reconnect after connection drop', async () => {
    // Known flaky due to WebSocket timing; quarantined from blocking CI
  });
});
```
