# C# Regression Testing Patterns

## Common Regression Scenarios

### 1. Service Layer Changes
When a service class (registered via DI) is modified, generate regression tests that:
- Verify the method still produces correct output for all known input combinations
- Check that downstream consumers receive the same data contracts
- Validate that exception behavior is preserved
- Confirm mock interactions with dependencies remain correct

### 2. Controller/API Endpoint Changes
When an ASP.NET Core controller method is modified:
- Verify HTTP status codes remain unchanged for existing request patterns
- Check response body structure (field names, types, nullability)
- Validate model validation attributes (`[Required]`, `[StringLength]`, etc.) still apply
- Test authentication/authorization behavior is preserved (`[Authorize]` attributes)
- **For `test_level=integration`**: use `WebApplicationFactory<TEntryPoint>` + `HttpClient` instead of mocking (see Integration Patterns below)

### 3. Repository/Data Access Changes
When an Entity Framework Core repository or DbContext method is modified:
- Verify query results match expected data
- Check that CRUD operations maintain data integrity
- Validate transaction boundaries and `SaveChangesAsync` calls
- Test optimistic concurrency behavior
- **For `test_level=integration`**: use EF Core InMemory provider or Testcontainers (see Integration Patterns below)

### 4. Entity/Model Changes
When an EF Core entity or DTO class is modified:
- Verify serialization/deserialization produces expected JSON results
- Check that data annotations (`[Required]`, `[MaxLength]`, etc.) still apply
- Test equality/comparison behavior
- Validate constructor and factory method behavior

### 5. Configuration and DI Changes
When `Startup.cs`, `Program.cs`, or service registration changes:
- Verify DI container resolves expected services
- Check that middleware pipeline order is preserved
- Test configuration binding and validation
- Validate options pattern (`IOptions<T>`) behavior
- **For `test_level=integration`**: use `WebApplicationFactory` to verify full DI container and middleware pipeline (see Integration Patterns below)

## xUnit Regression Test Structure

```csharp
using Xunit;
using Moq;

[Trait("Category", "Regression")]
public class UserServiceRegressionTests
{
    private readonly Mock<IUserRepository> _userRepository;
    private readonly Mock<IEmailService> _emailService;
    private readonly UserService _sut;

    public UserServiceRegressionTests()
    {
        _userRepository = new Mock<IUserRepository>();
        _emailService = new Mock<IEmailService>();
        _sut = new UserService(_userRepository.Object, _emailService.Object);
    }

    // --- Behavior Preservation Tests ---

    [Fact]
    [Trait("Category", "Regression")]
    public async Task CreateUser_WithValidRequest_ReturnsUserWithGeneratedId()
    {
        // Arrange - same setup as before the change
        _userRepository
            .Setup(r => r.AddAsync(It.IsAny<User>()))
            .ReturnsAsync((User u) => { u.Id = 1; return u; });

        // Act
        var result = await _sut.CreateUserAsync(
            new CreateUserRequest("test@example.com", "Test", "pass"));

        // Assert - verify same behavior as before
        Assert.NotNull(result);
        Assert.True(result.Id > 0);
        Assert.Equal("test@example.com", result.Email);
    }

    // --- Backward Compatibility Tests ---

    [Fact]
    public async Task FindById_NonExistentId_ReturnsNull()
    {
        _userRepository
            .Setup(r => r.GetByIdAsync(999))
            .ReturnsAsync((User?)null);

        var result = await _sut.FindByIdAsync(999);

        Assert.Null(result);
    }

    // --- Exception Contract Tests ---

    [Fact]
    public async Task CreateUser_NullRequest_ThrowsArgumentNullException()
    {
        await Assert.ThrowsAsync<ArgumentNullException>(
            () => _sut.CreateUserAsync(null!));
    }

    // --- Integration Point Regression ---

    [Fact]
    public async Task CreateUser_Success_SendsWelcomeEmail()
    {
        _userRepository
            .Setup(r => r.AddAsync(It.IsAny<User>()))
            .ReturnsAsync(new User { Id = 1 });

        await _sut.CreateUserAsync(
            new CreateUserRequest("test@example.com", "Test", "pass"));

        _emailService.Verify(
            e => e.SendWelcomeEmailAsync("test@example.com"),
            Times.Once);
    }
}
```

## Moq Patterns for Regression Testing

### Verify Unchanged Interactions
```csharp
// Verify that the method still calls the same dependencies
_repository.Verify(r => r.AddAsync(It.IsAny<User>()), Times.Once);
_emailService.Verify(e => e.SendWelcomeEmailAsync(It.IsAny<string>()), Times.Once);
_repository.VerifyNoOtherCalls();
```

### Argument Capture for Regression Validation
```csharp
User? capturedUser = null;
_repository
    .Setup(r => r.AddAsync(It.IsAny<User>()))
    .Callback<User>(u => capturedUser = u)
    .ReturnsAsync((User u) => u);

await _sut.CreateUserAsync(request);

// Verify the saved object has expected fields
Assert.NotNull(capturedUser);
Assert.Equal("test@example.com", capturedUser.Email);
Assert.NotNull(capturedUser.CreatedAt);
```

### Verify Exception Propagation
```csharp
// Verify that dependency exceptions are still propagated correctly
_repository
    .Setup(r => r.AddAsync(It.IsAny<User>()))
    .ThrowsAsync(new DbUpdateException("DB error"));

await Assert.ThrowsAsync<ServiceException>(
    () => _sut.CreateUserAsync(request));
```

## Parameterized Regression Tests (Theory)

```csharp
[Theory]
[Trait("Category", "Regression")]
[InlineData("PROD-1", 1, "CONFIRMED", 29.99)]
[InlineData("PROD-2", 5, "CONFIRMED", 149.95)]
public async Task ProcessOrder_RegressionInputs_ProducesConsistentResults(
    string productId, int quantity, string expectedStatus, decimal expectedTotal)
{
    _inventoryService
        .Setup(i => i.CheckStockAsync(It.IsAny<string>()))
        .ReturnsAsync(true);
    _pricingService
        .Setup(p => p.CalculateAsync(It.IsAny<OrderRequest>()))
        .ReturnsAsync(expectedTotal);

    var result = await _orderService.ProcessOrderAsync(
        new OrderRequest(productId, quantity));

    Assert.Equal(expectedStatus, result.Status);
    Assert.Equal(expectedTotal, result.Total);
}
```

## MemberData Regression Tests

```csharp
public static IEnumerable<object[]> RegressionInputData =>
    new List<object[]>
    {
        new object[] { new OrderRequest("PROD-1", 1), "CONFIRMED" },
        new object[] { new OrderRequest("PROD-2", 5), "CONFIRMED" },
    };

[Theory]
[MemberData(nameof(RegressionInputData))]
public async Task ProcessOrder_MemberDataRegression(OrderRequest input, string expectedStatus)
{
    var result = await _orderService.ProcessOrderAsync(input);
    Assert.Equal(expectedStatus, result.Status);
}
```

## Coverlet/Cobertura Configuration

### .csproj (Test Project)
```xml
<ItemGroup>
    <PackageReference Include="coverlet.collector" Version="6.0.0">
        <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
        <PrivateAssets>all</PrivateAssets>
    </PackageReference>
</ItemGroup>
```

### Running with Coverage
```bash
# Run with Cobertura coverage collection
dotnet test --collect:"XPlat Code Coverage"

# Coverage report appears at TestResults/<guid>/coverage.cobertura.xml
```

## Running Selected Tests

```bash
# Run specific test class
dotnet test --filter "FullyQualifiedName~UserServiceRegressionTests"

# Run multiple test classes
dotnet test --filter "FullyQualifiedName~UserServiceRegressionTests|FullyQualifiedName~OrderServiceRegressionTests"

# Run tests with a specific trait
dotnet test --filter "Category=Regression"

# Run in a specific test project
dotnet test MyProject.Tests/MyProject.Tests.csproj --filter "FullyQualifiedName~UserServiceRegressionTests"

# Run specific test method
dotnet test --filter "FullyQualifiedName~UserServiceRegressionTests.CreateUser_WithValidRequest_ReturnsUserWithGeneratedId"
```

## Common C# Regression Risks

| Risk | Detection | Mitigation |
|---|---|---|
| Serialization changes | JSON property rename/remove in DTOs | Test `System.Text.Json` round-trip |
| Interface contract break | Method signature change in interfaces | Test all known implementations |
| Async/await regression | Missing `await`, `ConfigureAwait` change | Test async completion and results |
| DI registration change | `AddScoped`/`AddTransient` swap | Test service resolution |
| Middleware order change | Pipeline configuration modified | Test request processing order |
| Nullable reference change | `?` added/removed on reference types | Test with null inputs |
| EF Core query change | LINQ expression modified | Test query results |
| Exception type change | Catch block or throws modified | Test exception types explicitly |
| Default value change | Property initializer modified | Test with default construction |
| IDisposable regression | Dispose pattern changed | Test resource cleanup |

## Data-Driven Regression Tests

When user-provided test data is available, prefer loading data from fixture files
over hardcoded inline values.

### JSON Fixture Loading
```csharp
private readonly JsonSerializerOptions _jsonOptions = new() { PropertyNameCaseInsensitive = true };

[Fact]
[Trait("Category", "Regression")]
public async Task ProcessOrder_WithFixtureData_ReturnsExpectedResult()
{
    // Load from user-provided fixture file
    var json = await File.ReadAllTextAsync("TestData/Fixtures/order-valid.json");
    var order = JsonSerializer.Deserialize<OrderRequest>(json, _jsonOptions)!;

    var result = await _sut.ProcessOrderAsync(order);

    Assert.Equal("CONFIRMED", result.Status);
}
```

### CSV File-Driven Parameterized Tests (MemberData)
```csharp
public static IEnumerable<object[]> LoadCsvFixture()
{
    var lines = File.ReadAllLines("TestData/Fixtures/order-inputs.csv").Skip(1);
    foreach (var line in lines)
    {
        var parts = line.Split(',');
        yield return new object[] { parts[0], int.Parse(parts[1]), parts[2] };
    }
}

[Theory]
[MemberData(nameof(LoadCsvFixture))]
[Trait("Category", "Regression")]
public async Task ProcessOrder_CsvFixture_ProducesConsistentResults(
    string productId, int quantity, string expectedStatus)
{
    var result = await _orderService.ProcessOrderAsync(
        new OrderRequest(productId, quantity));

    Assert.Equal(expectedStatus, result.Status);
}
```

### Golden-File Assertion Pattern
```csharp
[Fact]
[Trait("Category", "Regression")]
public async Task ToDto_GoldenFile_MatchesExpected()
{
    var actualDto = _sut.ToDto(testUser);
    var actualJson = JsonSerializer.Serialize(actualDto, new JsonSerializerOptions { WriteIndented = true });

    var expectedJson = await File.ReadAllTextAsync("TestData/Expected/user-dto.json");

    Assert.Equal(
        JsonDocument.Parse(expectedJson).RootElement.ToString(),
        JsonDocument.Parse(actualJson).RootElement.ToString());
}
```

## Integration Regression Test Patterns

Use these patterns when `test_level` is `integration` or `both`. Integration tests
use `*IntegrationTests.cs` suffix and are placed in `*.IntegrationTests` projects.

### WebApplicationFactory — Controller Integration
```csharp
public class UserControllerIntegrationTests
    : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public UserControllerIntegrationTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureTestServices(services =>
            {
                // Replace real services with test doubles if needed
                services.AddScoped<IUserRepository, InMemoryUserRepository>();
            });
        }).CreateClient();
    }

    [Fact]
    [Trait("Category", "Regression")]
    public async Task GetUser_ExistingId_Returns200()
    {
        var response = await _client.GetAsync("/api/users/1");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var content = await response.Content.ReadAsStringAsync();
        var user = JsonSerializer.Deserialize<UserDto>(content);
        Assert.NotNull(user);
        Assert.Equal("test@example.com", user.Email);
    }

    [Fact]
    public async Task GetUser_NonExistentId_Returns404()
    {
        var response = await _client.GetAsync("/api/users/999");
        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task CreateUser_InvalidBody_Returns400()
    {
        var content = new StringContent(
            "{\"email\": \"\", \"name\": null}",
            Encoding.UTF8, "application/json");

        var response = await _client.PostAsync("/api/users", content);
        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }
}
```

### EF Core InMemory — Repository Integration
```csharp
public class UserRepositoryIntegrationTests : IDisposable
{
    private readonly AppDbContext _context;
    private readonly UserRepository _repository;

    public UserRepositoryIntegrationTests()
    {
        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
            .Options;
        _context = new AppDbContext(options);
        _repository = new UserRepository(_context);

        // Seed test data
        _context.Users.Add(new User { Id = 1, Email = "test@example.com", Name = "Test" });
        _context.SaveChanges();
    }

    [Fact]
    [Trait("Category", "Regression")]
    public async Task FindByEmail_ExistingEmail_ReturnsUser()
    {
        var found = await _repository.FindByEmailAsync("test@example.com");
        Assert.NotNull(found);
        Assert.Equal("Test", found.Name);
    }

    [Fact]
    public async Task FindByEmail_NonExistent_ReturnsNull()
    {
        var found = await _repository.FindByEmailAsync("missing@example.com");
        Assert.Null(found);
    }

    public void Dispose() => _context.Dispose();
}
```

### Testcontainers — Real Database Integration
```csharp
public class OrderServiceContainerTests : IAsyncLifetime
{
    private readonly PostgreSqlContainer _postgres = new PostgreSqlBuilder()
        .WithImage("postgres:15")
        .WithDatabase("testdb")
        .WithUsername("test")
        .WithPassword("test")
        .Build();

    private IServiceProvider _services = null!;

    public async Task InitializeAsync()
    {
        await _postgres.StartAsync();
        var host = Host.CreateDefaultBuilder()
            .ConfigureServices(services =>
            {
                services.AddDbContext<AppDbContext>(opts =>
                    opts.UseNpgsql(_postgres.GetConnectionString()));
                services.AddScoped<IOrderService, OrderService>();
            }).Build();
        _services = host.Services;
    }

    [Fact]
    [Trait("Category", "Regression")]
    public async Task ProcessOrder_RealDb_PersistsOrder()
    {
        using var scope = _services.CreateScope();
        var service = scope.ServiceProvider.GetRequiredService<IOrderService>();

        var result = await service.ProcessOrderAsync(new OrderRequest("PROD-1", 2));

        Assert.NotNull(result.Id);
    }

    public async Task DisposeAsync() => await _postgres.DisposeAsync();
}
```

### Full Application Context Integration
```csharp
public class ApplicationContextIntegrationTests
    : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;

    public ApplicationContextIntegrationTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory;
    }

    [Fact]
    [Trait("Category", "Regression")]
    public void ApplicationContext_LoadsSuccessfully()
    {
        using var scope = _factory.Services.CreateScope();
        var userService = scope.ServiceProvider.GetService<IUserService>();
        Assert.NotNull(userService);
    }

    [Fact]
    public void AllRequiredServices_AreRegistered()
    {
        using var scope = _factory.Services.CreateScope();
        Assert.NotNull(scope.ServiceProvider.GetService<IUserService>());
        Assert.NotNull(scope.ServiceProvider.GetService<IOrderService>());
    }
}
```

## Requirement-Traced Regression Tests

When requirement IDs or regression scenarios are provided, use structured
traceability annotations to link tests back to requirements.

```csharp
[Trait("Category", "Regression")]
[Trait("Requirement", "REQ-PAY-001")]
public class PaymentProcessingRegressionTests
{
    // Scenario: PaymentProcessingIntegrity
    // Nested class per scenario

    [Trait("Requirement", "REQ-PAY-001")]
    public class PaymentProcessingIntegrityScenario
    {
        [Fact(DisplayName = "[REQ-PAY-001] processPayment deducts correct amount from wallet")]
        public async Task ProcessPayment_DeductsCorrectAmount()
        {
            // ... test implementation
        }

        [Fact(DisplayName = "[REQ-PAY-001] processPayment creates transaction with COMPLETED status")]
        public async Task ProcessPayment_CreatesCompletedTransaction()
        {
            // ... test implementation
        }
    }
}
```
