# Spock Mocking Guide

Comprehensive patterns for mocking, stubbing, and spying in Spock specifications.

## Mock vs Stub vs Spy

| Type | Purpose | Interaction Verification | Return Values |
|------|---------|--------------------------|---------------|
| `Mock()` | Verify interactions AND stub returns | Yes — in `then:` blocks | Yes — with `>>` |
| `Stub()` | Only stub return values | No — cannot verify | Yes — with `>>` |
| `Spy()` | Wrap a real object, override selectively | Yes | Calls real method unless stubbed |

**Rule of thumb**: Use `Mock()` when you care what was called. Use `Stub()` when you just need a return value. Use `Spy()` rarely — prefer redesigning for testability.

## Mock() — Full Mocking

### Declaration

```groovy
// Typed mock (recommended)
def userRepository = Mock(UserRepository)

// With constructor args (for non-interface types)
def service = Mock(UserService, constructorArgs: [repository])

// Inline with type
UserRepository userRepository = Mock()
```

### Stubbing Return Values

```groovy
// In given: block (arrangement)
userRepository.findById(1) >> Optional.of(user)

// Multiple calls return different values
userRepository.findById(_) >>> [Optional.of(user1), Optional.of(user2), Optional.empty()]

// Dynamic return based on input
userRepository.findByName(_ as String) >> { String name ->
    name == "admin" ? Optional.of(adminUser) : Optional.empty()
}

// Return null (default for unstubbed methods)
// No setup needed — Mock() returns null/0/false/empty by default
```

### Interaction Verification (in then: blocks)

```groovy
then: "the repository is called exactly once"
1 * userRepository.save(_ as User)

then: "never called"
0 * userRepository.delete(_)

then: "called at least once"
(1.._) * userRepository.findById(_)

then: "called between 2 and 5 times"
(2..5) * notificationService.send(_)

then: "called any number of times (including zero)"
_ * auditLogger.log(_)
```

### Argument Matching

```groovy
// Exact match
1 * service.process("exact-value")

// Any argument
1 * service.process(_)

// Type constraint
1 * service.process(_ as String)

// Closure constraint (most flexible)
1 * service.process({ it.length() > 5 })

// Named argument matching for readability
1 * repository.save({ User u ->
    u.name == "Alice"
    u.email == "alice@test.com"
    u.active == true
})

// Negation
1 * service.process(!null)
1 * service.process(!"forbidden")

// Not matching a type
1 * service.process(!(_ as Integer))
```

### Combined Stubbing + Verification

```groovy
// Stub AND verify in then: block
then:
1 * userRepository.save(_ as User) >> savedUser

// This means: verify it was called once, AND when called, return savedUser
```

### Ordered Interactions

```groovy
then: "login is called before access check"
1 * authService.login(credentials)

then: "access is checked after login"
1 * authService.checkAccess(resource)
// Spock verifies then: blocks in order
```

### Strict vs Lenient Mocking

```groovy
// Strict: fail on any unexpected call (default for Mock())
then:
1 * service.expectedCall()
0 * service._  // No other method on this mock should be called

// Global strictness: no unexpected calls on ANY mock
then:
1 * service.expectedCall()
0 * _._  // No unexpected call on any mock

// Lenient: allow other calls (don't add 0 * constraints)
then:
1 * service.expectedCall()
// Other calls are silently ignored
```

## Stub() — Return Value Only

```groovy
def config = Stub(AppConfig)

// Stub all calls
config.getTimeout() >> 5000
config.getRetryCount() >> 3
config.getFeatureFlag("dark-mode") >> true

// Dynamic stubbing
config.getProperty(_ as String) >> { String key ->
    switch (key) {
        case "timeout": return "5000"
        case "retries": return "3"
        default: return null
    }
}
```

**Cannot verify interactions on Stub() — this will fail:**
```groovy
// WRONG — Stub() does not support interaction verification
then:
1 * config.getTimeout()  // ERROR
```

## Spy() — Partial Mocking

```groovy
def realService = new UserService(repository)
def spiedService = Spy(realService)

// Override specific method
spiedService.sendNotification(_) >> { /* do nothing */ }

// The rest calls real methods
def result = spiedService.createUser(request)  // Real implementation runs

// Verify
then:
1 * spiedService.sendNotification(_ as User)
```

**Alternative: Spy with class**
```groovy
def service = Spy(UserService, constructorArgs: [repository])
```

## Common Mocking Patterns

### Mocking void methods

```groovy
// Void methods don't need >> stubbing
// Just verify the interaction
then:
1 * emailService.sendWelcomeEmail("alice@test.com")
```

### Mocking methods that throw

```groovy
given: "the repository throws on save"
userRepository.save(_ as User) >> { throw new DataAccessException("DB down") }
```

### Mocking Optional returns

```groovy
given: "user exists"
userRepository.findById(1) >> Optional.of(user)

given: "user not found"
userRepository.findById(999) >> Optional.empty()
```

### Mocking List/Collection returns

```groovy
given: "multiple users exist"
userRepository.findAll() >> [user1, user2, user3]

given: "no users"
userRepository.findAll() >> []
```

### Mocking CompletableFuture

```groovy
given: "async operation succeeds"
asyncService.processAsync(_) >> CompletableFuture.completedFuture(result)

given: "async operation fails"
asyncService.processAsync(_) >> CompletableFuture.failedFuture(new RuntimeException("failed"))
```

### Mocking Page (Spring Data)

```groovy
given: "a page of users"
def page = new PageImpl<>([user1, user2], PageRequest.of(0, 10), 2)
userRepository.findAll(_ as Pageable) >> page
```

## Argument Capture

When you need to inspect the exact argument passed to a mock:

```groovy
def "should save user with generated ID"() {
    when:
    service.createUser(request)

    then:
    1 * repository.save(_ as User) >> { User captured ->
        assert captured.id != null
        assert captured.name == "Alice"
        assert captured.createdAt != null
        return captured  // return the captured object if needed
    }
}
```

## Global Mocks (use sparingly)

```groovy
// Mock a static method call (Spock 2.x with groovy-all)
def "should use current time"() {
    given:
    GroovyMock(Instant, global: true)
    Instant.now() >> Instant.parse("2026-01-01T00:00:00Z")

    when:
    def result = service.getTimestamp()

    then:
    result == "2026-01-01T00:00:00Z"
}
```

**Warning**: Global mocks affect all code in the test — use only when necessary and never in parallel test execution.

## Anti-Patterns to Avoid

1. **Don't mix Mockito and Spock mocking** — use Spock's built-in `Mock()`/`Stub()`/`Spy()` exclusively
2. **Don't use `Mock()` when `Stub()` suffices** — if you don't verify interactions, `Stub()` communicates intent better
3. **Don't verify interactions in `given:` blocks** — verifications belong in `then:` blocks only
4. **Don't stub and verify the same interaction separately** — combine in `then:` block: `1 * mock.method() >> value`
5. **Don't mock the class under test** — mock its dependencies, not the subject
6. **Don't over-mock** — if a dependency is simple and deterministic, use the real implementation
