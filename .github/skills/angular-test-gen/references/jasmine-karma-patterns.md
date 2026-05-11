# Jasmine/Karma Patterns for Angular

## Setup

### karma.conf.js

```javascript
module.exports = function (config) {
  config.set({
    basePath: '',
    frameworks: ['jasmine', '@angular-devkit/build-angular'],
    plugins: [
      require('karma-jasmine'),
      require('karma-chrome-launcher'),
      require('karma-jasmine-html-reporter'),
      require('karma-coverage'),
      require('@angular-devkit/build-angular/plugins/karma'),
    ],
    client: {
      jasmine: {},
      clearContext: false,
    },
    coverageReporter: {
      dir: require('path').join(__dirname, './coverage'),
      subdir: '.',
      reporters: [
        { type: 'html' },
        { type: 'text-summary' },
        { type: 'lcov' },
        { type: 'json-summary' },
      ],
      check: {
        global: {
          statements: 85,
          branches: 85,
          functions: 85,
          lines: 85,
        },
      },
    },
    reporters: ['progress', 'kjhtml'],
    browsers: ['ChromeHeadless'],
    singleRun: true,
    restartOnFileChange: true,
  });
};
```

## Jasmine APIs

### Spies

```typescript
// Create a spy object with multiple methods
const serviceSpy = jasmine.createSpyObj('UserService', [
  'getUsers',
  'getUserById',
  'createUser',
  'deleteUser',
]);

// Configure return values
serviceSpy.getUsers.and.returnValue(of([mockUser1, mockUser2]));
serviceSpy.getUserById.and.returnValue(of(mockUser1));
serviceSpy.createUser.and.returnValue(of(mockUser1));

// Configure async return
serviceSpy.getUsers.and.returnValue(Promise.resolve([mockUser1]));

// Configure throw
serviceSpy.getUserById.and.throwError(new Error('Not found'));

// Return different values on successive calls
serviceSpy.getUserById.and.returnValues(of(user1), of(user2), throwError(() => new Error()));

// Spy on existing method
spyOn(component, 'onSubmit');
spyOn(component, 'onSubmit').and.callThrough(); // Call real implementation too
spyOn(component, 'onSubmit').and.callFake((data) => { /* custom */ });

// Spy on property
spyOnProperty(component, 'isLoggedIn', 'get').and.returnValue(true);
```

### Assertions

```typescript
// Equality
expect(value).toBe(42);              // Strict equality (===)
expect(value).toEqual({ a: 1 });     // Deep equality
expect(value).not.toBe(0);

// Truthiness
expect(value).toBeTruthy();
expect(value).toBeFalsy();
expect(value).toBeNull();
expect(value).toBeUndefined();
expect(value).toBeDefined();

// Comparison
expect(value).toBeGreaterThan(0);
expect(value).toBeLessThan(100);
expect(value).toBeCloseTo(3.14, 2);

// Strings
expect(name).toContain('lic');
expect(name).toMatch(/^[A-Z]/);

// Arrays
expect(list).toContain(item);
expect(list).toHaveSize(3);

// Errors
expect(() => service.validate(null)).toThrow();
expect(() => service.validate(null)).toThrowError('Invalid input');
expect(() => service.validate(null)).toThrowError(ValidationError);

// Spy verification
expect(serviceSpy.getUsers).toHaveBeenCalled();
expect(serviceSpy.getUsers).toHaveBeenCalledTimes(1);
expect(serviceSpy.getUsers).toHaveBeenCalledWith('param');
expect(serviceSpy.deleteUser).not.toHaveBeenCalled();

// Jasmine matchers for complex objects
expect(result).toEqual(jasmine.objectContaining({ name: 'Alice' }));
expect(list).toEqual(jasmine.arrayContaining([item1, item2]));
expect(callback).toHaveBeenCalledWith(jasmine.any(String));
```

### Async Testing

```typescript
import { fakeAsync, tick, flush, flushMicrotasks } from '@angular/core/testing';

// fakeAsync + tick — for timers, debounce, setTimeout
it('should debounce search', fakeAsync(() => {
  component.onSearchInput('test');
  tick(300); // Advance virtual time
  fixture.detectChanges();

  expect(serviceSpy.search).toHaveBeenCalledWith('test');
}));

// fakeAsync + flush — drain all pending async
it('should complete all async', fakeAsync(() => {
  component.loadData();
  flush(); // Drain all macrotasks
  fixture.detectChanges();

  expect(component.data).toBeDefined();
}));

// waitForAsync — for real async operations
import { waitForAsync } from '@angular/core/testing';

it('should load data', waitForAsync(() => {
  component.loadData();
  fixture.whenStable().then(() => {
    fixture.detectChanges();
    expect(component.data.length).toBe(3);
  });
}));

// done callback — for manual async control
it('should emit event', (done) => {
  component.dataLoaded.subscribe(data => {
    expect(data).toBeTruthy();
    done();
  });
  component.loadData();
});
```

### Clock / Timer Mocking

```typescript
it('should handle setTimeout', fakeAsync(() => {
  component.startPolling();
  tick(5000); // Advance 5 seconds
  expect(serviceSpy.poll).toHaveBeenCalledTimes(5);

  component.stopPolling();
  tick(5000);
  expect(serviceSpy.poll).toHaveBeenCalledTimes(5); // No more calls
}));

it('should handle setInterval', fakeAsync(() => {
  component.startInterval();
  tick(1000);
  expect(component.count).toBe(1);
  tick(2000);
  expect(component.count).toBe(3);
  component.stopInterval();
  discardPeriodicTasks(); // Clean up intervals
}));
```

## Jest Angular Setup (Alternative)

### jest.config.ts

```typescript
import type { Config } from 'jest';

const config: Config = {
  preset: 'jest-preset-angular',
  setupFilesAfterSetup: ['<rootDir>/setup-jest.ts'],
  testPathIgnorePatterns: ['<rootDir>/node_modules/', '<rootDir>/dist/'],
  moduleNameMapper: {
    '^@app/(.*)$': '<rootDir>/src/app/$1',
    '^@env/(.*)$': '<rootDir>/src/environments/$1',
  },
  collectCoverageFrom: [
    'src/app/**/*.ts',
    '!src/app/**/*.module.ts',
    '!src/app/**/*.spec.ts',
    '!src/app/**/index.ts',
  ],
  coverageThreshold: {
    global: {
      statements: 85,
      branches: 85,
      functions: 85,
      lines: 85,
    },
  },
};

export default config;
```

### setup-jest.ts

```typescript
import 'jest-preset-angular/setup-jest';
```

### Jest-specific APIs in Angular

```typescript
// Mock module
jest.mock('@app/services/user.service');

// Spy
jest.spyOn(component, 'onSubmit');

// Timer mocks
jest.useFakeTimers();
jest.advanceTimersByTime(300);
jest.useRealTimers();
```

## Coverage Commands

```bash
# Karma/Istanbul
ng test --code-coverage --watch=false --browsers=ChromeHeadless

# Jest
npx jest --coverage --ci

# Specific project in workspace
ng test my-app --code-coverage
```
