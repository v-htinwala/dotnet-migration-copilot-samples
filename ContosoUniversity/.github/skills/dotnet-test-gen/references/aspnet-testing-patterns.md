# ASP.NET Core Testing Patterns

Testing ASP.NET Core applications with WebApplicationFactory, TestServer,
and integration testing patterns.

## WebApplicationFactory — Integration Testing

### Basic Setup

```csharp
using Microsoft.AspNetCore.Mvc.Testing;

public class ApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public ApiTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task GetUsers_ReturnsSuccessStatusCode()
    {
        var response = await _client.GetAsync("/api/users");

        response.EnsureSuccessStatusCode();
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }
}
```

### Custom Factory with Mocked Services

```csharp
public class CustomWebApplicationFactory : WebApplicationFactory<Program>
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            // Remove real DbContext
            var descriptor = services.SingleOrDefault(
                d => d.ServiceType == typeof(DbContextOptions<AppDbContext>));
            if (descriptor != null) services.Remove(descriptor);

            // Add in-memory database
            services.AddDbContext<AppDbContext>(options =>
                options.UseInMemoryDatabase("TestDb"));

            // Replace external services with mocks
            var emailMock = new Mock<IEmailService>();
            emailMock
                .Setup(e => e.SendAsync(It.IsAny<EmailMessage>()))
                .Returns(Task.CompletedTask);
            services.AddSingleton(emailMock.Object);
        });

        builder.UseEnvironment("Testing");
    }
}

// Usage
public class UserApiTests : IClassFixture<CustomWebApplicationFactory>
{
    private readonly HttpClient _client;
    private readonly CustomWebApplicationFactory _factory;

    public UserApiTests(CustomWebApplicationFactory factory)
    {
        _factory = factory;
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task CreateUser_ReturnsCreated()
    {
        var request = new CreateUserRequest("Alice", "alice@test.com");
        var content = new StringContent(
            JsonSerializer.Serialize(request),
            Encoding.UTF8,
            "application/json");

        var response = await _client.PostAsync("/api/users", content);

        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var user = await response.Content.ReadFromJsonAsync<UserDto>();
        user!.Name.Should().Be("Alice");
    }
}
```

### Seed Test Data

```csharp
protected override void ConfigureWebHost(IWebHostBuilder builder)
{
    builder.ConfigureServices(services =>
    {
        var sp = services.BuildServiceProvider();
        using var scope = sp.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        db.Database.EnsureCreated();

        db.Users.AddRange(
            new User { Id = 1, Name = "Alice", Email = "alice@test.com" },
            new User { Id = 2, Name = "Bob", Email = "bob@test.com" });
        db.SaveChanges();
    });
}
```

### Authenticated Requests

```csharp
// Option 1: Add auth header directly
_client.DefaultRequestHeaders.Authorization =
    new AuthenticationHeaderValue("Bearer", "test-jwt-token");

// Option 2: Custom authentication handler
public class TestAuthHandler : AuthenticationHandler<AuthenticationSchemeOptions>
{
    public TestAuthHandler(
        IOptionsMonitor<AuthenticationSchemeOptions> options,
        ILoggerFactory logger,
        UrlEncoder encoder)
        : base(options, logger, encoder) { }

    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        var claims = new[]
        {
            new Claim(ClaimTypes.Name, "testuser"),
            new Claim(ClaimTypes.Role, "Admin"),
        };
        var identity = new ClaimsIdentity(claims, "Test");
        var principal = new ClaimsPrincipal(identity);
        var ticket = new AuthenticationTicket(principal, "Test");

        return Task.FromResult(AuthenticateResult.Success(ticket));
    }
}

// Register in factory
builder.ConfigureServices(services =>
{
    services.AddAuthentication("Test")
        .AddScheme<AuthenticationSchemeOptions, TestAuthHandler>("Test", _ => { });
});
```

## Controller Unit Testing (without WebApplicationFactory)

### Testing with Mocked Dependencies

```csharp
public class UserControllerTests
{
    private readonly Mock<IUserService> _serviceMock;
    private readonly UserController _controller;

    public UserControllerTests()
    {
        _serviceMock = new Mock<IUserService>();
        _controller = new UserController(_serviceMock.Object);
    }

    [Fact]
    public async Task GetById_UserExists_ReturnsOk()
    {
        _serviceMock
            .Setup(s => s.GetByIdAsync(1))
            .ReturnsAsync(new UserDto { Id = 1, Name = "Alice" });

        var result = await _controller.GetById(1);

        var okResult = result.Should().BeOfType<OkObjectResult>().Subject;
        okResult.StatusCode.Should().Be(200);
        var user = okResult.Value.Should().BeOfType<UserDto>().Subject;
        user.Name.Should().Be("Alice");
    }

    [Fact]
    public async Task GetById_UserNotFound_ReturnsNotFound()
    {
        _serviceMock
            .Setup(s => s.GetByIdAsync(999))
            .ReturnsAsync((UserDto?)null);

        var result = await _controller.GetById(999);

        result.Should().BeOfType<NotFoundResult>();
    }

    [Fact]
    public async Task Create_ValidInput_ReturnsCreatedAtAction()
    {
        var request = new CreateUserRequest("Alice", "alice@test.com");
        _serviceMock
            .Setup(s => s.CreateAsync(request))
            .ReturnsAsync(new UserDto { Id = 1, Name = "Alice" });

        var result = await _controller.Create(request);

        var created = result.Should().BeOfType<CreatedAtActionResult>().Subject;
        created.StatusCode.Should().Be(201);
        created.RouteValues!["id"].Should().Be(1);
    }
}
```

### Testing ModelState Validation

```csharp
[Fact]
public async Task Create_InvalidModel_ReturnsBadRequest()
{
    _controller.ModelState.AddModelError("Name", "Name is required");

    var result = await _controller.Create(new CreateUserRequest("", ""));

    result.Should().BeOfType<BadRequestObjectResult>();
}
```

## Minimal API Testing

```csharp
[Fact]
public async Task MapGet_Users_ReturnsJsonList()
{
    await using var factory = new WebApplicationFactory<Program>();
    var client = factory.CreateClient();

    var response = await client.GetAsync("/api/users");

    response.StatusCode.Should().Be(HttpStatusCode.OK);
    var users = await response.Content.ReadFromJsonAsync<List<UserDto>>();
    users.Should().NotBeNull();
}
```

## Middleware Testing

```csharp
public class ExceptionMiddlewareTests
{
    [Fact]
    public async Task Invoke_WhenExceptionThrown_Returns500()
    {
        // Arrange
        var middleware = new ExceptionHandlingMiddleware(
            next: _ => throw new InvalidOperationException("Test error"),
            NullLogger<ExceptionHandlingMiddleware>.Instance);

        var context = new DefaultHttpContext();
        context.Response.Body = new MemoryStream();

        // Act
        await middleware.InvokeAsync(context);

        // Assert
        context.Response.StatusCode.Should().Be(500);
        context.Response.Body.Seek(0, SeekOrigin.Begin);
        var body = await new StreamReader(context.Response.Body).ReadToEndAsync();
        body.Should().Contain("error");
    }
}
```

## Background Service Testing

```csharp
public class DataSyncServiceTests
{
    [Fact]
    public async Task ExecuteAsync_ProcessesItems()
    {
        var serviceMock = new Mock<IDataService>();
        serviceMock
            .Setup(s => s.SyncAsync(It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        var sut = new DataSyncService(
            serviceMock.Object,
            NullLogger<DataSyncService>.Instance);

        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(5));

        await sut.StartAsync(cts.Token);
        await Task.Delay(100); // Allow one cycle
        await sut.StopAsync(cts.Token);

        serviceMock.Verify(
            s => s.SyncAsync(It.IsAny<CancellationToken>()),
            Times.AtLeastOnce);
    }
}
```

## SignalR Hub Testing

```csharp
public class ChatHubTests
{
    [Fact]
    public async Task SendMessage_BroadcastsToAll()
    {
        var clientsMock = new Mock<IHubCallerClients>();
        var allClientsMock = new Mock<IClientProxy>();

        clientsMock.Setup(c => c.All).Returns(allClientsMock.Object);

        var hub = new ChatHub { Clients = clientsMock.Object };

        await hub.SendMessage("Alice", "Hello!");

        allClientsMock.Verify(
            c => c.SendCoreAsync(
                "ReceiveMessage",
                It.Is<object[]>(args =>
                    (string)args[0] == "Alice" &&
                    (string)args[1] == "Hello!"),
                It.IsAny<CancellationToken>()),
            Times.Once);
    }
}
```
