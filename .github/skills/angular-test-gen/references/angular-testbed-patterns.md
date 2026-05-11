# Angular TestBed Patterns

Comprehensive patterns for configuring TestBed across Angular component types.

## Basic Component (Standalone)

```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MyComponent } from './my.component';

describe('MyComponent', () => {
  let component: MyComponent;
  let fixture: ComponentFixture<MyComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MyComponent], // Standalone components go in imports
    }).compileComponents();

    fixture = TestBed.createComponent(MyComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
```

## NgModule Component

```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MyComponent } from './my.component';
import { SharedModule } from '@app/shared/shared.module';

describe('MyComponent', () => {
  let component: MyComponent;
  let fixture: ComponentFixture<MyComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [MyComponent],
      imports: [SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(MyComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });
});
```

## Component with Service Dependencies

```typescript
describe('UserListComponent', () => {
  let component: UserListComponent;
  let fixture: ComponentFixture<UserListComponent>;
  let userServiceSpy: jasmine.SpyObj<UserService>;

  beforeEach(async () => {
    userServiceSpy = jasmine.createSpyObj('UserService', ['getUsers', 'deleteUser']);
    userServiceSpy.getUsers.and.returnValue(of([
      { id: 1, name: 'Alice' },
      { id: 2, name: 'Bob' },
    ]));

    await TestBed.configureTestingModule({
      imports: [UserListComponent],
      providers: [
        { provide: UserService, useValue: userServiceSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(UserListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should display users', () => {
    const rows = fixture.nativeElement.querySelectorAll('.user-row');
    expect(rows.length).toBe(2);
    expect(rows[0].textContent).toContain('Alice');
  });

  it('should call deleteUser when delete button clicked', () => {
    userServiceSpy.deleteUser.and.returnValue(of(undefined));
    const deleteBtn = fixture.nativeElement.querySelector('.delete-btn');
    deleteBtn.click();
    fixture.detectChanges();

    expect(userServiceSpy.deleteUser).toHaveBeenCalledWith(1);
  });
});
```

## Component with Router

```typescript
import { RouterTestingModule } from '@angular/router/testing';
import { Router } from '@angular/router';

describe('NavComponent', () => {
  let component: NavComponent;
  let fixture: ComponentFixture<NavComponent>;
  let router: Router;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        NavComponent,
        RouterTestingModule.withRoutes([
          { path: 'dashboard', component: DashboardComponent },
          { path: 'users', component: UserListComponent },
        ]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(NavComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
  });

  it('should navigate to dashboard', () => {
    const spy = spyOn(router, 'navigate');
    component.goToDashboard();
    expect(spy).toHaveBeenCalledWith(['/dashboard']);
  });
});
```

## Component with ActivatedRoute

```typescript
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { of } from 'rxjs';

describe('UserDetailComponent', () => {
  let component: UserDetailComponent;
  let fixture: ComponentFixture<UserDetailComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserDetailComponent],
      providers: [
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: of(convertToParamMap({ id: '42' })),
            queryParamMap: of(convertToParamMap({ tab: 'profile' })),
            snapshot: {
              paramMap: convertToParamMap({ id: '42' }),
            },
          },
        },
        { provide: UserService, useValue: jasmine.createSpyObj('UserService', ['getUserById']) },
      ],
    }).compileComponents();

    const userService = TestBed.inject(UserService) as jasmine.SpyObj<UserService>;
    userService.getUserById.and.returnValue(of({ id: 42, name: 'Alice' }));

    fixture = TestBed.createComponent(UserDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should load user by route param', () => {
    expect(component.user?.name).toBe('Alice');
  });
});
```

## Component with @Input / @Output

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

  it('should display user name', () => {
    component.user = { id: 1, name: 'Alice', email: 'alice@test.com' };
    fixture.detectChanges();

    const nameEl = fixture.nativeElement.querySelector('.user-name');
    expect(nameEl.textContent).toContain('Alice');
  });

  it('should emit selected event when clicked', () => {
    component.user = { id: 1, name: 'Alice', email: 'alice@test.com' };
    fixture.detectChanges();

    spyOn(component.selected, 'emit');
    const card = fixture.nativeElement.querySelector('.user-card');
    card.click();

    expect(component.selected.emit).toHaveBeenCalledWith(component.user);
  });
});
```

## Component with Signals (Angular 16+)

```typescript
describe('CounterComponent', () => {
  let component: CounterComponent;
  let fixture: ComponentFixture<CounterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CounterComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(CounterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should increment count signal', () => {
    expect(component.count()).toBe(0);

    component.increment();
    fixture.detectChanges();

    expect(component.count()).toBe(1);
    expect(fixture.nativeElement.querySelector('.count').textContent).toContain('1');
  });

  it('should compute doubled value', () => {
    component.count.set(5);
    fixture.detectChanges();

    expect(component.doubled()).toBe(10);
  });
});
```

## Component with Forms

### Reactive Forms

```typescript
import { ReactiveFormsModule } from '@angular/forms';

describe('LoginFormComponent', () => {
  let component: LoginFormComponent;
  let fixture: ComponentFixture<LoginFormComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LoginFormComponent, ReactiveFormsModule],
      providers: [
        { provide: AuthService, useValue: jasmine.createSpyObj('AuthService', ['login']) },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be invalid when empty', () => {
    expect(component.loginForm.valid).toBeFalse();
  });

  it('should be valid with correct input', () => {
    component.loginForm.patchValue({
      email: 'test@example.com',
      password: 'password123',
    });
    expect(component.loginForm.valid).toBeTrue();
  });

  it('should show email error on blur', () => {
    const emailInput = fixture.nativeElement.querySelector('#email');
    emailInput.value = 'invalid';
    emailInput.dispatchEvent(new Event('input'));
    emailInput.dispatchEvent(new Event('blur'));
    fixture.detectChanges();

    const error = fixture.nativeElement.querySelector('.email-error');
    expect(error).toBeTruthy();
  });

  it('should call login on valid submit', () => {
    const authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    authService.login.and.returnValue(of({ token: 'abc' }));

    component.loginForm.patchValue({
      email: 'test@example.com',
      password: 'password123',
    });
    component.onSubmit();

    expect(authService.login).toHaveBeenCalledWith('test@example.com', 'password123');
  });
});
```

### Template-driven Forms

```typescript
import { FormsModule } from '@angular/forms';

describe('ContactFormComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ContactFormComponent, FormsModule],
    }).compileComponents();
  });

  it('should bind model to form', fakeAsync(() => {
    fixture.detectChanges();
    tick(); // Allow ngModel to initialize

    const nameInput: HTMLInputElement = fixture.nativeElement.querySelector('#name');
    nameInput.value = 'Alice';
    nameInput.dispatchEvent(new Event('input'));
    tick();

    expect(component.contact.name).toBe('Alice');
  }));
});
```

## Override Providers for Specific Tests

```typescript
it('should handle service error', async () => {
  const errorService = jasmine.createSpyObj('UserService', ['getUsers']);
  errorService.getUsers.and.returnValue(throwError(() => new Error('Server error')));

  TestBed.overrideProvider(UserService, { useValue: errorService });

  // Re-create component with overridden provider
  fixture = TestBed.createComponent(UserListComponent);
  component = fixture.componentInstance;
  fixture.detectChanges();

  expect(fixture.nativeElement.querySelector('.error-message')).toBeTruthy();
});
```

## Template Query Patterns

```typescript
// By CSS selector
fixture.nativeElement.querySelector('.my-class');
fixture.nativeElement.querySelectorAll('li');

// By DebugElement (more Angular-idiomatic)
import { By } from '@angular/platform-browser';

fixture.debugElement.query(By.css('.my-class'));
fixture.debugElement.queryAll(By.css('li'));
fixture.debugElement.query(By.directive(MyDirective));

// Verify element existence
const el = fixture.nativeElement.querySelector('.error');
expect(el).toBeTruthy();     // Element exists
expect(el).toBeFalsy();      // Element does not exist

// Verify text content
expect(el.textContent).toContain('expected text');
expect(el.textContent.trim()).toBe('exact text');

// Verify attributes
expect(el.getAttribute('disabled')).toBeTruthy();
expect(el.classList).toContain('active');

// Verify styles
expect(el.style.display).toBe('none');
```
