# xUnit / NUnit / MSTest Patterns for ASP.NET Core

## xUnit Setup

### Test Project `.csproj`

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <IsPackable>false</IsPackable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.9.0" />
    <PackageReference Include="xunit" Version="2.7.0" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.5.7" />
    <PackageReference Include="Moq" Version="4.20.70" />
    <PackageReference Include="FluentAssertions" Version="6.12.0" />
    <PackageReference Include="coverlet.collector" Version="6.0.1" />
  </ItemGroup>

  <ItemGroup>
    <ProjectReference Include="..\..\src\MyApp\MyApp.csproj" />
  </ItemGroup>
</Project>
```

### xUnit Attributes

```csharp
// Single test case
[Fact]
public async Task MethodName_Scenario_ExpectedBehavior()
{
    // Arrange / Act / Assert
}

// Parameterized — inline data
[Theory]
[InlineData("input1", "expected1")]
[InlineData("input2", "expected2")]
public void MethodName_WithInput_ReturnsExpected(string input, string expected)
{
    // ...
}

// Parameterized — member data
[Theory]
[MemberData(nameof(GetTestData))]
public void MethodName_WithMemberData_ReturnsExpected(string input, int expected)
{
    // ...
}

public static IEnumerable<object[]> GetTestData()
{
    yield return new object[] { "abc", 3 };
    yield return new object[] { "", 0 };
    yield return new object[] { "hello world", 11 };
}

// Parameterized — class data
[Theory]
[ClassData(typeof(UserTestData))]
public void MethodName_WithClassData_ReturnsExpected(User user, bool expected)
{
    // ...
}
```

### xUnit Lifecycle

```csharp
// Per-test setup/teardown
public class MyTests : IDisposable
{
    private readonly MyService _sut;

    public MyTests()
    {
        // Constructor runs before each test (like [SetUp])
        _sut = new MyService();
    }

    public void Dispose()
    {
        // Runs after each test (like [TearDown])
    }
}

// Shared context across tests in a class
public class MyTests : IClassFixture<DatabaseFixture>
{
    private readonly DatabaseFixture _fixture;

    public MyTests(DatabaseFixture fixture)
    {
        _fixture = fixture;
    }
}

// Shared context across multiple test classes
[CollectionDefinition("Database")]
public class DatabaseCollection : ICollectionFixture<DatabaseFixture> { }

[Collection("Database")]
public class UserServiceTests
{
    // ...
}
```

### xUnit Assertions (Native)

```csharp
Assert.Equal(expected, actual);
Assert.NotEqual(unexpected, actual);
Assert.True(condition);
Assert.False(condition);
Assert.Null(value);
Assert.NotNull(value);
Assert.Empty(collection);
Assert.NotEmpty(collection);
Assert.Contains(expected, collection);
Assert.DoesNotContain(unexpected, collection);
Assert.Single(collection);
Assert.IsType<ExpectedType>(obj);
Assert.IsAssignableFrom<BaseType>(obj);
Assert.Throws<ArgumentException>(() => method());
await Assert.ThrowsAsync<InvalidOperationException>(() => asyncMethod());
Assert.InRange(actual, low, high);
Assert.Collection(collection,
    item => Assert.Equal("first", item.Name),
    item => Assert.Equal("second", item.Name));
```

## NUnit Setup

### NUnit Attributes

```csharp
using NUnit.Framework;

[TestFixture]
public class UserServiceTests
{
    private Mock<IUserRepository> _repoMock;
    private UserService _sut;

    [SetUp]
    public void SetUp()
    {
        _repoMock = new Mock<IUserRepository>();
        _sut = new UserService(_repoMock.Object);
    }

    [TearDown]
    public void TearDown()
    {
        // Cleanup
    }

    [Test]
    public async Task CreateUser_ValidInput_ReturnsUser()
    {
        // Arrange / Act / Assert
    }

    [TestCase("valid@email.com", true)]
    [TestCase("invalid", false)]
    [TestCase("", false)]
    [TestCase(null, false)]
    public void IsValidEmail_WithInput_ReturnsExpected(string? email, bool expected)
    {
        var result = _sut.IsValidEmail(email);
        Assert.That(result, Is.EqualTo(expected));
    }
}
```

### NUnit Assertions

```csharp
Assert.That(actual, Is.EqualTo(expected));
Assert.That(actual, Is.Not.Null);
Assert.That(collection, Is.Empty);
Assert.That(collection, Has.Count.EqualTo(3));
Assert.That(collection, Contains.Item(expected));
Assert.That(actual, Is.InstanceOf<ExpectedType>());
Assert.That(actual, Is.InRange(low, high));
Assert.That(() => method(), Throws.TypeOf<ArgumentException>());
Assert.That(async () => await asyncMethod(),
    Throws.TypeOf<InvalidOperationException>()
          .With.Message.Contains("error"));
```

## MSTest Setup

### MSTest Attributes

```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;

[TestClass]
public class UserServiceTests
{
    private Mock<IUserRepository> _repoMock = null!;
    private UserService _sut = null!;

    [TestInitialize]
    public void Initialize()
    {
        _repoMock = new Mock<IUserRepository>();
        _sut = new UserService(_repoMock.Object);
    }

    [TestCleanup]
    public void Cleanup()
    {
        // Cleanup
    }

    [TestMethod]
    public async Task CreateUser_ValidInput_ReturnsUser()
    {
        // Arrange / Act / Assert
    }

    [DataTestMethod]
    [DataRow("valid@email.com", true)]
    [DataRow("invalid", false)]
    [DataRow("", false)]
    public void IsValidEmail_WithInput_ReturnsExpected(string email, bool expected)
    {
        var result = _sut.IsValidEmail(email);
        Assert.AreEqual(expected, result);
    }
}
```

### MSTest Assertions

```csharp
Assert.AreEqual(expected, actual);
Assert.AreNotEqual(unexpected, actual);
Assert.IsTrue(condition);
Assert.IsFalse(condition);
Assert.IsNull(value);
Assert.IsNotNull(value);
Assert.IsInstanceOfType(obj, typeof(ExpectedType));
Assert.ThrowsException<ArgumentException>(() => method());
await Assert.ThrowsExceptionAsync<InvalidOperationException>(() => asyncMethod());
CollectionAssert.Contains(collection, expected);
CollectionAssert.AreEqual(expected, actual);
CollectionAssert.IsEmpty(collection); // MSTest v3+
```

## FluentAssertions (Cross-framework)

```csharp
using FluentAssertions;

// Basic
result.Should().Be(42);
result.Should().NotBe(0);
result.Should().BeNull();
result.Should().NotBeNull();

// Strings
name.Should().Be("Alice");
name.Should().Contain("lic");
name.Should().StartWith("A");
name.Should().BeNullOrEmpty();
name.Should().MatchRegex(@"^[A-Z]");

// Collections
list.Should().HaveCount(3);
list.Should().Contain(item);
list.Should().BeEmpty();
list.Should().NotBeEmpty();
list.Should().ContainSingle();
list.Should().OnlyContain(x => x.IsActive);
list.Should().BeInAscendingOrder(x => x.Name);
list.Should().BeEquivalentTo(expected);

// Types
obj.Should().BeOfType<UserDto>();
obj.Should().BeAssignableTo<IEntity>();

// Exceptions
act.Should().Throw<ArgumentException>()
    .WithMessage("*invalid*");
await act.Should().ThrowAsync<InvalidOperationException>()
    .WithMessage("*not found*");
act.Should().NotThrow();

// Numeric
value.Should().BeGreaterThan(0);
value.Should().BeInRange(1, 100);
value.Should().BeApproximately(3.14, 0.01);

// DateTime
date.Should().BeBefore(DateTime.UtcNow);
date.Should().BeCloseTo(expected, TimeSpan.FromSeconds(1));

// Object equivalence (deep comparison)
actual.Should().BeEquivalentTo(expected, options => options
    .Excluding(x => x.Id)
    .Excluding(x => x.CreatedAt));
```

## Common Test Commands

```bash
# Run all tests
dotnet test

# Run with verbosity
dotnet test --verbosity normal

# Run specific test project
dotnet test tests/MyApp.Tests/MyApp.Tests.csproj

# Run filtered tests
dotnet test --filter "FullyQualifiedName~UserService"
dotnet test --filter "Category=Unit"

# Run with coverage
dotnet test --collect:"XPlat Code Coverage"
```
