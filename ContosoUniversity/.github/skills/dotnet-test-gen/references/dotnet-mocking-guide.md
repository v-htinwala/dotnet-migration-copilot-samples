# .NET Mocking Guide

Comprehensive patterns for mocking with Moq and NSubstitute in .NET tests.

## Moq

### Creating Mocks

```csharp
// Basic mock
var userRepoMock = new Mock<IUserRepository>();

// Mock with strict behavior (throws on unexpected calls)
var strictMock = new Mock<IUserRepository>(MockBehavior.Strict);

// Mock with default behavior (returns default values)
var looseMock = new Mock<IUserRepository>(MockBehavior.Loose); // default
```

### Setup — Return Values

```csharp
// Fixed return
userRepoMock
    .Setup(r => r.GetByIdAsync(1))
    .ReturnsAsync(new User { Id = 1, Name = "Alice" });

// Return based on input
userRepoMock
    .Setup(r => r.GetByIdAsync(It.IsAny<int>()))
    .ReturnsAsync((int id) => new User { Id = id, Name = $"User{id}" });

// Return sequence
userRepoMock
    .SetupSequence(r => r.GetByIdAsync(It.IsAny<int>()))
    .ReturnsAsync(new User { Id = 1, Name = "First" })
    .ReturnsAsync(new User { Id = 2, Name = "Second" })
    .ReturnsAsync((User?)null);

// Return null
userRepoMock
    .Setup(r => r.GetByIdAsync(999))
    .ReturnsAsync((User?)null);
```

### Setup — Exceptions

```csharp
userRepoMock
    .Setup(r => r.GetByIdAsync(-1))
    .ThrowsAsync(new ArgumentException("Invalid ID"));

userRepoMock
    .Setup(r => r.SaveAsync(It.IsAny<User>()))
    .ThrowsAsync(new DbUpdateException("Duplicate key"));
```

### Setup — Void Methods

```csharp
// Void method with callback
emailMock
    .Setup(e => e.Send(It.IsAny<string>(), It.IsAny<string>()))
    .Callback<string, string>((to, body) =>
    {
        // Capture arguments for later assertion
    });

// Void async method
emailMock
    .Setup(e => e.SendAsync(It.IsAny<EmailMessage>()))
    .Returns(Task.CompletedTask);
```

### Argument Matchers

```csharp
// Any value
It.IsAny<string>()
It.IsAny<int>()
It.IsAny<User>()

// Specific condition
It.Is<string>(s => s.Contains("@"))
It.Is<int>(i => i > 0)
It.Is<User>(u => u.Name == "Alice" && u.IsActive)

// Range
It.IsInRange(1, 100, Range.Inclusive)

// Regex
It.IsRegex(@"^[a-z]+@[a-z]+\.[a-z]+$")

// Not null
It.IsNotNull<string>()
```

### Verify — Interaction Checking

```csharp
// Called exactly once
userRepoMock.Verify(
    r => r.SaveAsync(It.Is<User>(u => u.Name == "Alice")),
    Times.Once);

// Never called
userRepoMock.Verify(
    r => r.DeleteAsync(It.IsAny<int>()),
    Times.Never);

// Called at least once
emailMock.Verify(
    e => e.SendAsync(It.IsAny<EmailMessage>()),
    Times.AtLeastOnce);

// Called exactly N times
loggerMock.Verify(
    l => l.Log(It.IsAny<string>()),
    Times.Exactly(3));

// Called between N and M times
cacheMock.Verify(
    c => c.GetAsync(It.IsAny<string>()),
    Times.Between(1, 5, Range.Inclusive));

// Verify no other calls were made
userRepoMock.VerifyNoOtherCalls();
```

### Properties

```csharp
// Setup property getter
configMock.Setup(c => c.ConnectionString).Returns("Server=test;");

// Setup property with SetupGet/SetupSet
configMock.SetupGet(c => c.Timeout).Returns(30);
configMock.SetupSet(c => c.Timeout = It.IsInRange(1, 300, Range.Inclusive));

// Track property value changes
configMock.SetupProperty(c => c.Timeout, 30); // Initial value = 30
```

### Mock Reset

```csharp
// Reset all setups and invocations
userRepoMock.Reset();

// Reset invocations only (keep setups)
userRepoMock.Invocations.Clear();
```

## NSubstitute

### Creating Substitutes

```csharp
using NSubstitute;

// Create substitute
var userRepo = Substitute.For<IUserRepository>();

// Substitute for class (calls real constructor)
var service = Substitute.For<UserService>(userRepo);

// Substitute for multiple interfaces
var combo = Substitute.For<IUserRepository, IDisposable>();
```

### Return Values

```csharp
// Fixed return
userRepo.GetByIdAsync(1).Returns(new User { Id = 1, Name = "Alice" });

// Return for any argument
userRepo.GetByIdAsync(Arg.Any<int>())
    .Returns(callInfo => new User { Id = callInfo.Arg<int>() });

// Return sequence
userRepo.GetByIdAsync(Arg.Any<int>())
    .Returns(
        new User { Name = "First" },
        new User { Name = "Second" },
        null);

// Return null
userRepo.GetByIdAsync(999).Returns((User?)null);

// Return async
userRepo.GetByIdAsync(1).Returns(Task.FromResult(new User { Id = 1 }));
```

### Exceptions

```csharp
userRepo.GetByIdAsync(-1)
    .Returns<User>(x => throw new ArgumentException("Invalid ID"));

// Or with ThrowsAsync
userRepo.SaveAsync(Arg.Any<User>())
    .ThrowsAsync(new DbUpdateException("Duplicate key"));
```

### Argument Matchers

```csharp
Arg.Any<string>()
Arg.Is<string>(s => s.Contains("@"))
Arg.Is(42)
Arg.Do<User>(u => capturedUser = u)  // Capture argument
```

### Received — Interaction Checking

```csharp
// Called exactly once
userRepo.Received(1).SaveAsync(Arg.Is<User>(u => u.Name == "Alice"));

// Never called
userRepo.DidNotReceive().DeleteAsync(Arg.Any<int>());

// Called at least once
emailService.Received().SendAsync(Arg.Any<EmailMessage>());

// Called any number of times (just check args)
userRepo.Received(Arg.Any<int>()).GetByIdAsync(Arg.Is<int>(id => id > 0));

// Clear received calls
userRepo.ClearReceivedCalls();
```

## Mocking Common .NET Types

### ILogger<T>

```csharp
// Moq — ILogger is hard to verify directly; use a wrapper or helper
var loggerMock = new Mock<ILogger<UserService>>();

// Verify a log call (Moq — verbose but works)
loggerMock.Verify(
    x => x.Log(
        LogLevel.Error,
        It.IsAny<EventId>(),
        It.Is<It.IsAnyType>((v, t) => v.ToString()!.Contains("failed")),
        It.IsAny<Exception?>(),
        It.IsAny<Func<It.IsAnyType, Exception?, string>>()),
    Times.Once);

// Simpler: use Microsoft.Extensions.Logging.Abstractions.NullLogger
var logger = NullLogger<UserService>.Instance;
```

### IConfiguration

```csharp
// Build in-memory configuration
var config = new ConfigurationBuilder()
    .AddInMemoryCollection(new Dictionary<string, string?>
    {
        ["ConnectionStrings:Default"] = "Server=test;Database=testdb;",
        ["Jwt:Secret"] = "test-secret-key-for-unit-tests",
        ["Jwt:Issuer"] = "test-issuer",
    })
    .Build();
```

### IOptions<T>

```csharp
var options = Options.Create(new JwtSettings
{
    Secret = "test-secret",
    Issuer = "test-issuer",
    ExpiryMinutes = 60,
});
```

### HttpClient / IHttpClientFactory

```csharp
// Mock HttpMessageHandler
var handlerMock = new Mock<HttpMessageHandler>();
handlerMock
    .Protected()
    .Setup<Task<HttpResponseMessage>>(
        "SendAsync",
        ItExpr.IsAny<HttpRequestMessage>(),
        ItExpr.IsAny<CancellationToken>())
    .ReturnsAsync(new HttpResponseMessage
    {
        StatusCode = HttpStatusCode.OK,
        Content = new StringContent(
            JsonSerializer.Serialize(new { Id = 1, Name = "Test" }),
            Encoding.UTF8,
            "application/json"),
    });

var httpClient = new HttpClient(handlerMock.Object)
{
    BaseAddress = new Uri("https://api.test.com/"),
};

// Mock IHttpClientFactory
var factoryMock = new Mock<IHttpClientFactory>();
factoryMock
    .Setup(f => f.CreateClient("ApiClient"))
    .Returns(httpClient);
```

### DbContext (EF Core In-Memory)

```csharp
// In-memory database for testing
var options = new DbContextOptionsBuilder<AppDbContext>()
    .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
    .Options;

await using var context = new AppDbContext(options);
context.Users.Add(new User { Id = 1, Name = "Alice" });
await context.SaveChangesAsync();

var sut = new UserRepository(context);
```

### CancellationToken

```csharp
[Fact]
public async Task Process_WhenCancelled_ThrowsOperationCancelled()
{
    var cts = new CancellationTokenSource();
    cts.Cancel();

    var act = () => _sut.ProcessAsync(cts.Token);

    await act.Should().ThrowAsync<OperationCanceledException>();
}
```

## Anti-Patterns to Avoid

1. **Don't mock what you don't own** — wrap third-party APIs in your own interface
2. **Don't mock value objects / DTOs** — create real instances
3. **Don't verify internal implementation details** — test behavior, not calls
4. **Don't use `MockBehavior.Strict` by default** — it makes tests brittle
5. **Don't mock the class under test** — mock its dependencies only
6. **Don't mock `DbContext` directly** — use `UseInMemoryDatabase` or SQLite in-memory
