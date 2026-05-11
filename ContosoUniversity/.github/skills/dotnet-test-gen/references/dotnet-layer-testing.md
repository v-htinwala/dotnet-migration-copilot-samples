# .NET Layer Testing Patterns

Per-layer testing strategies for ASP.NET Core applications.

## Controller Layer

### REST Controller — Happy Path + Error Handling

```csharp
public class ProductControllerTests
{
    private readonly Mock<IProductService> _serviceMock;
    private readonly ProductController _controller;

    public ProductControllerTests()
    {
        _serviceMock = new Mock<IProductService>();
        _controller = new ProductController(_serviceMock.Object);
    }

    [Fact]
    public async Task GetAll_ReturnsOkWithProducts()
    {
        _serviceMock.Setup(s => s.GetAllAsync())
            .ReturnsAsync(new List<ProductDto>
            {
                new() { Id = 1, Name = "Widget", Price = 9.99m },
                new() { Id = 2, Name = "Gadget", Price = 19.99m },
            });

        var result = await _controller.GetAll();

        var ok = result.Should().BeOfType<OkObjectResult>().Subject;
        var products = ok.Value.Should().BeAssignableTo<IEnumerable<ProductDto>>().Subject;
        products.Should().HaveCount(2);
    }

    [Fact]
    public async Task GetAll_NoProducts_ReturnsOkWithEmptyList()
    {
        _serviceMock.Setup(s => s.GetAllAsync())
            .ReturnsAsync(new List<ProductDto>());

        var result = await _controller.GetAll();

        var ok = result.Should().BeOfType<OkObjectResult>().Subject;
        var products = ok.Value.Should().BeAssignableTo<IEnumerable<ProductDto>>().Subject;
        products.Should().BeEmpty();
    }

    [Fact]
    public async Task GetById_Exists_ReturnsOk()
    {
        _serviceMock.Setup(s => s.GetByIdAsync(1))
            .ReturnsAsync(new ProductDto { Id = 1, Name = "Widget" });

        var result = await _controller.GetById(1);

        var ok = result.Should().BeOfType<OkObjectResult>().Subject;
        var product = ok.Value.Should().BeOfType<ProductDto>().Subject;
        product.Name.Should().Be("Widget");
    }

    [Fact]
    public async Task GetById_NotFound_ReturnsNotFound()
    {
        _serviceMock.Setup(s => s.GetByIdAsync(999))
            .ReturnsAsync((ProductDto?)null);

        var result = await _controller.GetById(999);

        result.Should().BeOfType<NotFoundResult>();
    }

    [Fact]
    public async Task Create_ValidInput_ReturnsCreated()
    {
        var request = new CreateProductRequest("Widget", 9.99m);
        _serviceMock.Setup(s => s.CreateAsync(request))
            .ReturnsAsync(new ProductDto { Id = 1, Name = "Widget", Price = 9.99m });

        var result = await _controller.Create(request);

        var created = result.Should().BeOfType<CreatedAtActionResult>().Subject;
        created.StatusCode.Should().Be(201);
    }

    [Fact]
    public async Task Create_InvalidModel_ReturnsBadRequest()
    {
        _controller.ModelState.AddModelError("Name", "Name is required");

        var result = await _controller.Create(new CreateProductRequest("", -1));

        result.Should().BeOfType<BadRequestObjectResult>();
    }

    [Fact]
    public async Task Delete_Exists_ReturnsNoContent()
    {
        _serviceMock.Setup(s => s.DeleteAsync(1)).ReturnsAsync(true);

        var result = await _controller.Delete(1);

        result.Should().BeOfType<NoContentResult>();
        _serviceMock.Verify(s => s.DeleteAsync(1), Times.Once);
    }

    [Fact]
    public async Task Delete_NotFound_ReturnsNotFound()
    {
        _serviceMock.Setup(s => s.DeleteAsync(999)).ReturnsAsync(false);

        var result = await _controller.Delete(999);

        result.Should().BeOfType<NotFoundResult>();
    }
}
```

### Controller with Pagination

```csharp
[Fact]
public async Task GetAll_WithPagination_ReturnsPagedResult()
{
    var pagedResult = new PagedResult<ProductDto>
    {
        Items = new List<ProductDto> { new() { Id = 1, Name = "Widget" } },
        TotalCount = 50,
        Page = 1,
        PageSize = 10,
    };
    _serviceMock.Setup(s => s.GetPagedAsync(1, 10)).ReturnsAsync(pagedResult);

    var result = await _controller.GetAll(page: 1, pageSize: 10);

    var ok = result.Should().BeOfType<OkObjectResult>().Subject;
    var paged = ok.Value.Should().BeOfType<PagedResult<ProductDto>>().Subject;
    paged.TotalCount.Should().Be(50);
    paged.Items.Should().HaveCount(1);
}
```

## Service Layer

### Service with Business Logic

```csharp
public class PricingServiceTests
{
    private readonly Mock<IProductRepository> _productRepoMock;
    private readonly Mock<IDiscountService> _discountMock;
    private readonly Mock<IAuditLogService> _auditMock;
    private readonly PricingService _sut;

    public PricingServiceTests()
    {
        _productRepoMock = new Mock<IProductRepository>();
        _discountMock = new Mock<IDiscountService>();
        _auditMock = new Mock<IAuditLogService>();
        _sut = new PricingService(
            _productRepoMock.Object,
            _discountMock.Object,
            _auditMock.Object);
    }

    [Fact]
    public async Task CalculatePrice_WithPercentageDiscount_AppliesDiscount()
    {
        _productRepoMock.Setup(r => r.GetByIdAsync(1))
            .ReturnsAsync(new Product { Id = 1, BasePrice = 100m });
        _discountMock.Setup(d => d.GetDiscountAsync(1))
            .ReturnsAsync(new Discount { Type = DiscountType.Percentage, Value = 20 });

        var price = await _sut.CalculatePriceAsync(1);

        price.Should().Be(80m);
        _auditMock.Verify(
            a => a.LogPriceCalculation(1, 100m, 80m),
            Times.Once);
    }

    [Fact]
    public async Task CalculatePrice_FixedDiscountExceedsPrice_FloorsAtZero()
    {
        _productRepoMock.Setup(r => r.GetByIdAsync(1))
            .ReturnsAsync(new Product { Id = 1, BasePrice = 10m });
        _discountMock.Setup(d => d.GetDiscountAsync(1))
            .ReturnsAsync(new Discount { Type = DiscountType.Fixed, Value = 15 });

        var price = await _sut.CalculatePriceAsync(1);

        price.Should().Be(0m);
    }

    [Fact]
    public async Task CalculatePrice_ProductNotFound_Throws()
    {
        _productRepoMock.Setup(r => r.GetByIdAsync(999))
            .ReturnsAsync((Product?)null);

        var act = () => _sut.CalculatePriceAsync(999);

        await act.Should().ThrowAsync<ProductNotFoundException>();
        _auditMock.Verify(a => a.LogPriceCalculation(
            It.IsAny<int>(), It.IsAny<decimal>(), It.IsAny<decimal>()),
            Times.Never);
    }
}
```

### Service with Transactions / Events

```csharp
public class TransferServiceTests
{
    private readonly Mock<IAccountRepository> _accountRepoMock;
    private readonly Mock<ITransactionRepository> _txnRepoMock;
    private readonly Mock<IEventBus> _eventBusMock;
    private readonly TransferService _sut;

    public TransferServiceTests()
    {
        _accountRepoMock = new Mock<IAccountRepository>();
        _txnRepoMock = new Mock<ITransactionRepository>();
        _eventBusMock = new Mock<IEventBus>();
        _sut = new TransferService(
            _accountRepoMock.Object,
            _txnRepoMock.Object,
            _eventBusMock.Object);
    }

    [Fact]
    public async Task Transfer_ValidAccounts_TransfersFunds()
    {
        var from = new Account { Id = 1, Balance = 1000m };
        var to = new Account { Id = 2, Balance = 500m };
        _accountRepoMock.Setup(r => r.GetByIdAsync(1)).ReturnsAsync(from);
        _accountRepoMock.Setup(r => r.GetByIdAsync(2)).ReturnsAsync(to);

        await _sut.TransferAsync(1, 2, 200m);

        _accountRepoMock.Verify(
            r => r.UpdateAsync(It.Is<Account>(a => a.Id == 1 && a.Balance == 800m)),
            Times.Once);
        _accountRepoMock.Verify(
            r => r.UpdateAsync(It.Is<Account>(a => a.Id == 2 && a.Balance == 700m)),
            Times.Once);
        _txnRepoMock.Verify(r => r.AddAsync(It.IsAny<Transaction>()), Times.Once);
        _eventBusMock.Verify(
            e => e.PublishAsync(It.IsAny<TransferCompletedEvent>()),
            Times.Once);
    }

    [Fact]
    public async Task Transfer_InsufficientFunds_ThrowsAndNoSideEffects()
    {
        var from = new Account { Id = 1, Balance = 50m };
        _accountRepoMock.Setup(r => r.GetByIdAsync(1)).ReturnsAsync(from);

        var act = () => _sut.TransferAsync(1, 2, 200m);

        await act.Should().ThrowAsync<InsufficientFundsException>();
        _accountRepoMock.Verify(r => r.UpdateAsync(It.IsAny<Account>()), Times.Never);
        _txnRepoMock.Verify(r => r.AddAsync(It.IsAny<Transaction>()), Times.Never);
    }
}
```

## Repository Layer (EF Core)

### In-Memory Database Testing

```csharp
public class UserRepositoryTests : IDisposable
{
    private readonly AppDbContext _context;
    private readonly UserRepository _sut;

    public UserRepositoryTests()
    {
        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;
        _context = new AppDbContext(options);
        _sut = new UserRepository(_context);
    }

    public void Dispose() => _context.Dispose();

    [Fact]
    public async Task GetByEmail_UserExists_ReturnsUser()
    {
        _context.Users.Add(new User
        {
            Id = 1, Name = "Alice", Email = "alice@test.com", IsActive = true
        });
        await _context.SaveChangesAsync();

        var result = await _sut.GetByEmailAsync("alice@test.com");

        result.Should().NotBeNull();
        result!.Name.Should().Be("Alice");
    }

    [Fact]
    public async Task GetByEmail_UserNotFound_ReturnsNull()
    {
        var result = await _sut.GetByEmailAsync("nobody@test.com");

        result.Should().BeNull();
    }

    [Fact]
    public async Task GetActiveUsers_ReturnsOnlyActive()
    {
        _context.Users.AddRange(
            new User { Name = "Active", Email = "a@t.com", IsActive = true },
            new User { Name = "Inactive", Email = "i@t.com", IsActive = false });
        await _context.SaveChangesAsync();

        var result = await _sut.GetActiveUsersAsync();

        result.Should().ContainSingle();
        result.First().Name.Should().Be("Active");
    }
}
```

## Entity / Domain Layer

### Validation Testing

```csharp
public class UserValidationTests
{
    private readonly IValidator<User> _validator;

    public UserValidationTests()
    {
        _validator = new UserValidator(); // FluentValidation
    }

    [Theory]
    [InlineData("")]
    [InlineData(null)]
    [InlineData("not-an-email")]
    [InlineData("@no-local.com")]
    public void Validate_InvalidEmail_HasError(string? email)
    {
        var user = new User { Name = "Alice", Email = email! };

        var result = _validator.Validate(user);

        result.IsValid.Should().BeFalse();
        result.Errors.Should().Contain(e => e.PropertyName == "Email");
    }

    [Fact]
    public void Validate_ValidUser_Passes()
    {
        var user = new User
        {
            Name = "Alice",
            Email = "alice@test.com",
            Password = "Strong123!",
        };

        var result = _validator.Validate(user);

        result.IsValid.Should().BeTrue();
    }
}
```

### Data Annotations Validation

```csharp
public class ModelValidationTests
{
    private static IList<ValidationResult> ValidateModel(object model)
    {
        var results = new List<ValidationResult>();
        var context = new ValidationContext(model);
        Validator.TryValidateObject(model, context, results, validateAllProperties: true);
        return results;
    }

    [Fact]
    public void CreateUserRequest_MissingName_FailsValidation()
    {
        var request = new CreateUserRequest { Name = "", Email = "a@b.com" };

        var results = ValidateModel(request);

        results.Should().Contain(r => r.MemberNames.Contains("Name"));
    }
}
```

## AutoMapper Profile Testing

```csharp
public class MappingProfileTests
{
    private readonly IMapper _mapper;

    public MappingProfileTests()
    {
        var config = new MapperConfiguration(cfg =>
            cfg.AddProfile<UserMappingProfile>());
        _mapper = config.CreateMapper();
    }

    [Fact]
    public void Configuration_IsValid()
    {
        var config = new MapperConfiguration(cfg =>
            cfg.AddProfile<UserMappingProfile>());

        config.AssertConfigurationIsValid();
    }

    [Fact]
    public void Map_UserToDto_MapsAllProperties()
    {
        var user = new User { Id = 1, Name = "Alice", Email = "alice@test.com" };

        var dto = _mapper.Map<UserDto>(user);

        dto.Id.Should().Be(1);
        dto.Name.Should().Be("Alice");
        dto.Email.Should().Be("alice@test.com");
    }
}
```
