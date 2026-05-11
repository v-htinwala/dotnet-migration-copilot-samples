---
name: dotnet-test-gen
description: >
  Generate comprehensive unit tests for .NET / ASP.NET Core projects.
  Auto-detects xUnit, NUnit, or MSTest; Moq or NSubstitute; and produces
  C# test files with proper arrange/act/assert patterns, WebApplicationFactory
  integration slices, FluentAssertions, and Coverlet coverage. Covers
  controllers, services, repositories (EF Core), middleware, background
  services, minimal APIs, and utility classes. Use when the user needs
  unit tests, test generation, code coverage improvement, controller tests,
  service tests, or test scaffolding for a .NET or ASP.NET Core project.
license: Proprietary
compatibility: >
  Requires .NET 8+ SDK. Works with xUnit, NUnit, or MSTest.
  Expects an ASP.NET Core or .NET class library project with
  a separate test project.
metadata:
  author: specification-project
  version: "1.0"
---

# .NET / ASP.NET Core Unit Test Generator

Generate high-quality unit tests for .NET / ASP.NET Core projects with
automatic framework detection, comprehensive mocking, and coverage-driven
gap filling.


## SOURCE CODE PROTECTION -- HARD RULE

**All agents using this skill must ONLY create or modify test files.** Source/production code files must NEVER be modified, edited, or created.

- Only write files under test directories (`src/test/`, `tests/`, `__tests__/`, or matching `*.test.*`/`*.spec.*`/`*Tests.*` patterns)
- NEVER modify files under `src/main/` (Java), `src/` non-test directories (JS/TS), or the main project source directory (.NET)
- If the source code has compilation errors or bugs, report the issue and skip the file -- do not attempt to fix source code
- This rule is absolute and non-negotiable -- no exceptions for "obvious bugs", "typos", or "quick fixes"

## Workflow

### Step 1: Framework & Tooling Detection

Determine the test framework and mocking library from project configuration:

**xUnit detection** (check in order):
1. `xunit` package in `*.csproj` → `<PackageReference>`
2. `xunit.runner.visualstudio` in test project
3. Test files contain `[Fact]` or `[Theory]` attributes

**NUnit detection** (check in order):
1. `NUnit` package in `*.csproj` → `<PackageReference>`
2. `NUnit3TestAdapter` in test project
3. Test files contain `[Test]` or `[TestCase]` attributes

**MSTest detection** (check in order):
1. `MSTest.TestFramework` in `*.csproj`
2. `MSTest.TestAdapter` in test project
3. Test files contain `[TestMethod]` or `[DataTestMethod]` attributes

**If multiple present**: prefer xUnit (most common in ASP.NET Core ecosystem).
**If none present**: default to xUnit and note that setup is needed.

**Mocking library detection**:
1. `Moq` in `*.csproj` → use `Mock<T>`, `Setup()`, `Verify()`
2. `NSubstitute` in `*.csproj` → use `Substitute.For<T>()`, `Received()`
3. If neither: default to Moq

**Assertion library detection**:
1. `FluentAssertions` in `*.csproj` → use `.Should().Be()` style
2. If not present: use framework-native assertions

### Step 2: Project Structure Detection

Scan the solution to understand the project layout:

**Source project indicators**:
- `*.csproj` with `<OutputType>Exe</OutputType>` or `Microsoft.NET.Sdk.Web`
- `Program.cs`, `Startup.cs`, or minimal API entry point
- `Controllers/`, `Services/`, `Models/` directories

**Test project indicators**:
- `*.csproj` referencing a test framework
- `<ProjectReference>` to the source project
- Named `*.Tests`, `*.UnitTests`, or `*.IntegrationTests`

**Convention detection**:
- Separate test project: `src/MyApp/` → `tests/MyApp.Tests/`
- Mirror namespace: `MyApp.Services.UserService` → `MyApp.Tests.Services.UserServiceTests`

### Step 3: File Classification

Scan source files and classify each into a testing category:

| Category | Detection Rule | Test Pattern |
|----------|---------------|-------------|
| Controller | `[ApiController]` / `ControllerBase`, or in `Controllers/` | Mock services, test action methods, assert `IActionResult` types and status codes |
| Minimal API Endpoint | `app.MapGet/MapPost/etc.` in endpoint classes | Use `WebApplicationFactory`, test with `HttpClient`, assert responses |
| Service | In `Services/` or implements `I*Service` interface | Mock repositories/clients, test business logic, assert return values |
| Repository | Implements `IRepository<T>` or uses `DbContext` directly | Use in-memory `DbContext` or SQLite, test CRUD and queries |
| Middleware | Implements `IMiddleware` or `RequestDelegate` pattern | Mock `HttpContext`, test `InvokeAsync`, assert headers/status |
| Background Service | Extends `BackgroundService` / `IHostedService` | Mock dependencies, test `ExecuteAsync` with `CancellationToken` |
| Entity / Model | In `Models/`, `Entities/`, or `Domain/` namespace | Test validation attributes, computed properties, equality |
| DTO | In `DTOs/`, `Requests/`, `Responses/` namespace | Test mapping, AutoMapper profiles; skip if no logic |
| Configuration | In `Configuration/`, implements `IOptions<T>` pattern | Test validation, default values |
| Utility / Extension | In `Helpers/`, `Extensions/`, static methods | Test as pure functions with multiple inputs |
| Filter / Attribute | Implements `IActionFilter`, `IExceptionFilter` | Mock `ActionExecutingContext`, test filter behavior |
| SignalR Hub | Extends `Hub` or `Hub<T>` | Mock `IHubCallerClients`, test hub methods |

### Step 4: Test Generation Patterns

For each file category, follow the patterns below. Adapt based on detected
framework (xUnit vs NUnit vs MSTest) and mocking library (Moq vs NSubstitute).

**xUnit test structure**:
```csharp
using Xunit;
using Moq;
using FluentAssertions;

namespace MyApp.Tests.Services;

public class UserServiceTests
{
    private readonly Mock<IUserRepository> _userRepositoryMock;
    private readonly Mock<IEmailService> _emailServiceMock;
    private readonly UserService _sut;

    public UserServiceTests()
    {
        _userRepositoryMock = new Mock<IUserRepository>();
        _emailServiceMock = new Mock<IEmailService>();
        _sut = new UserService(
            _userRepositoryMock.Object,
            _emailServiceMock.Object);
    }

    [Fact]
    public async Task CreateUser_WithValidInput_ReturnsCreatedUser()
    {
        // Arrange
        var request = new CreateUserRequest("Alice", "alice@test.com");
        _userRepositoryMock
            .Setup(r => r.AddAsync(It.IsAny<User>()))
            .ReturnsAsync(new User { Id = 1, Name = "Alice" });

        // Act
        var result = await _sut.CreateUserAsync(request);

        // Assert
        result.Should().NotBeNull();
        result.Name.Should().Be("Alice");
        _userRepositoryMock.Verify(
            r => r.AddAsync(It.Is<User>(u => u.Name == "Alice")),
            Times.Once);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData(" ")]
    public async Task CreateUser_WithInvalidName_ThrowsValidationException(string? name)
    {
        // Arrange
        var request = new CreateUserRequest(name!, "alice@test.com");

        // Act
        var act = () => _sut.CreateUserAsync(request);

        // Assert
        await act.Should().ThrowAsync<ValidationException>()
            .WithMessage("*Name*required*");
    }
}
```

For detailed patterns per category, see the reference files:
- [xUnit / NUnit / MSTest patterns](references/xunit-nunit-mstest-patterns.md)
- [Moq / NSubstitute mocking guide](references/dotnet-mocking-guide.md)
- [ASP.NET Core testing patterns](references/aspnet-testing-patterns.md)
- [Layer testing patterns](references/dotnet-layer-testing.md)
- [Coverlet coverage patterns](references/coverlet-coverage-patterns.md)

### Step 5: Naming and Placement

**Detect project convention** by checking for existing test files:
1. Separate test project: `tests/MyApp.Tests/Services/UserServiceTests.cs`
2. Mirror structure: source namespace maps to test namespace with `.Tests` suffix

**If no existing tests**: create a test project mirroring the source structure.

**File naming rules**:
- Source: `UserService.cs` → Test: `UserServiceTests.cs`
- Alternative: `UserServiceTest.cs` (if project convention)
- Test class name matches file name exactly

**Namespace convention**:
- Source: `MyApp.Services` → Test: `MyApp.Tests.Services`
- Mirror the source folder hierarchy under the test project

### Step 6: Custom Instructions Resolution

Check for custom instructions in priority order:

1. **User runtime prompt** — inline instructions in the chat message
2. **Module-specific instructions** — `.github/test-gen-instructions/{module-name}.md`
3. **File-type instructions** — `.github/test-gen-instructions/controllers.md`, `services.md`, etc.
4. **Global instructions** — `.github/test-gen-instructions/global.md`
5. **SKILL.md defaults** — patterns defined in this file and references

Higher priority overrides lower when they conflict.

### Step 7: Coverage Strategy

**Coverlet metrics** (all four, threshold applies independently):
- Statements (line-level)
- Branches (most commonly missed — prioritize)
- Lines
- Methods

**Coverage analysis**:
1. Run test suite with Coverlet via `dotnet test --collect:"XPlat Code Coverage"`
2. Parse Cobertura XML or JSON report for per-file coverage
3. For files below threshold, extract uncovered line/branch ranges from XML
4. Map uncovered lines to methods for targeted test generation
5. Prioritize files with largest absolute gap

**Gap-filling strategy**:
- Focus on uncovered **branches** first (if/else, switch, ternary, null-coalescing)
- Then uncovered **methods** (dead code check — if truly unused, skip)
- Then remaining **lines** (usually catch blocks, error paths)

See [Coverlet patterns](references/coverlet-coverage-patterns.md) for detailed setup.

### Step 8: Verification Checklist

After generating tests, verify each file passes these structural checks:

- [ ] No empty test methods (`[Fact] public void ...() { }` with no assertions)
- [ ] No tautological assertions (`Assert.True(true)`, `result.Should().Be(result)`)
- [ ] Every test has at least one assertion call
- [ ] Mocks created with `Mock<T>()` have `.Verify()` calls where interactions matter
- [ ] Controller tests assert `IActionResult` type AND status code
- [ ] Async tests use `async Task` return type and `await` calls
- [ ] Edge cases are covered: null inputs, empty collections, exception paths
- [ ] Custom instruction compliance: correct imports, correct mock patterns
- [ ] No `[Fact(Skip = "...")]` or `[Ignore]` unless explicitly allowed
- [ ] Proper disposal of `HttpClient` and `WebApplicationFactory` in integration tests
