# Spring Layer Testing Patterns with Spock

Per-layer testing strategies for Spring Boot applications using Spock.

## Controller Layer

### REST Controller — Happy Path + Error Handling

```groovy
@WebMvcTest(ProductController)
class ProductControllerSpec extends Specification {

    @Autowired
    MockMvc mockMvc

    @MockBean
    ProductService productService

    def "GET /api/products should return list"() {
        given:
        productService.findAll() >> [
            new ProductDTO(id: 1, name: "Widget", price: 9.99),
            new ProductDTO(id: 2, name: "Gadget", price: 19.99)
        ]

        expect:
        mockMvc.perform(get("/api/products"))
            .andExpect(status().isOk())
            .andExpect(jsonPath('$.length()').value(2))
            .andExpect(jsonPath('$[0].name').value("Widget"))
    }

    def "GET /api/products should return empty list when none exist"() {
        given:
        productService.findAll() >> []

        expect:
        mockMvc.perform(get("/api/products"))
            .andExpect(status().isOk())
            .andExpect(jsonPath('$.length()').value(0))
    }

    @Unroll
    def "POST /api/products should validate #field"() {
        given:
        def body = new ObjectMapper().writeValueAsString(request)

        expect:
        mockMvc.perform(post("/api/products")
            .contentType("application/json")
            .content(body))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath('$.errors[0].field').value(field))

        where:
        request                                    | field
        [name: "", price: 9.99]                    | "name"
        [name: "Widget", price: -1]                | "price"
        [name: null, price: 9.99]                  | "name"
    }
}
```

### Controller with Pagination

```groovy
def "GET /api/products supports pagination"() {
    given:
    def page = new PageImpl<>(
        [new ProductDTO(id: 1, name: "Widget")],
        PageRequest.of(0, 10),
        50
    )
    productService.findAll(_ as Pageable) >> page

    expect:
    mockMvc.perform(get("/api/products?page=0&size=10"))
        .andExpect(status().isOk())
        .andExpect(jsonPath('$.content.length()').value(1))
        .andExpect(jsonPath('$.totalElements').value(50))
        .andExpect(jsonPath('$.totalPages').value(5))
}
```

## Service Layer

### Service with Business Logic

```groovy
class PricingServiceSpec extends Specification {

    def productRepository = Mock(ProductRepository)
    def discountService = Stub(DiscountService)
    def auditLog = Mock(AuditLogService)

    @Subject
    def pricingService = new PricingService(productRepository, discountService, auditLog)

    def "should apply percentage discount"() {
        given: "a product with base price"
        def product = new Product(id: 1, name: "Widget", basePrice: 100.00)
        productRepository.findById(1L) >> Optional.of(product)

        and: "a 20% discount applies"
        discountService.getDiscount(1L) >> new Discount(type: DiscountType.PERCENTAGE, value: 20)

        when:
        def price = pricingService.calculatePrice(1L)

        then: "price is discounted"
        price == 80.00

        and: "the calculation is audited"
        1 * auditLog.logPriceCalculation(1L, 100.00, 80.00)
    }

    def "should apply fixed discount without going below zero"() {
        given:
        def product = new Product(id: 1, basePrice: 10.00)
        productRepository.findById(1L) >> Optional.of(product)
        discountService.getDiscount(1L) >> new Discount(type: DiscountType.FIXED, value: 15)

        when:
        def price = pricingService.calculatePrice(1L)

        then: "price floors at zero"
        price == 0.00
    }

    def "should throw when product not found"() {
        given:
        productRepository.findById(999L) >> Optional.empty()

        when:
        pricingService.calculatePrice(999L)

        then:
        thrown(ProductNotFoundException)
        0 * auditLog._  // nothing logged for missing products
    }
}
```

### Service with Transaction / Event Patterns

```groovy
class TransferServiceSpec extends Specification {

    def accountRepository = Mock(AccountRepository)
    def transactionRepository = Mock(TransactionRepository)
    def eventPublisher = Mock(ApplicationEventPublisher)

    @Subject
    def transferService = new TransferService(accountRepository, transactionRepository, eventPublisher)

    def "should transfer funds between accounts"() {
        given:
        def from = new Account(id: 1, balance: 1000.00)
        def to = new Account(id: 2, balance: 500.00)
        accountRepository.findById(1L) >> Optional.of(from)
        accountRepository.findById(2L) >> Optional.of(to)

        when:
        transferService.transfer(1L, 2L, 200.00)

        then: "source debited"
        1 * accountRepository.save({ Account a -> a.id == 1 && a.balance == 800.00 })

        then: "destination credited"
        1 * accountRepository.save({ Account a -> a.id == 2 && a.balance == 700.00 })

        then: "transaction recorded"
        1 * transactionRepository.save(_ as Transaction)

        then: "event published"
        1 * eventPublisher.publishEvent(_ as TransferCompletedEvent)
    }

    def "should reject transfer with insufficient funds"() {
        given:
        def from = new Account(id: 1, balance: 50.00)
        accountRepository.findById(1L) >> Optional.of(from)

        when:
        transferService.transfer(1L, 2L, 200.00)

        then:
        thrown(InsufficientFundsException)
        0 * accountRepository.save(_)
        0 * transactionRepository.save(_)
    }
}
```

## Repository Layer

### Custom Query Testing

```groovy
@DataJpaTest
class OrderRepositorySpec extends Specification {

    @Autowired
    TestEntityManager em

    @Autowired
    OrderRepository orderRepository

    def setup() {
        // Seed common test data
        def customer = em.persistAndFlush(new Customer(name: "Alice"))

        em.persistAndFlush(new Order(
            customer: customer,
            status: OrderStatus.COMPLETED,
            total: 100.00,
            createdAt: LocalDateTime.of(2026, 1, 15, 10, 0)
        ))
        em.persistAndFlush(new Order(
            customer: customer,
            status: OrderStatus.PENDING,
            total: 50.00,
            createdAt: LocalDateTime.of(2026, 2, 1, 10, 0)
        ))
        em.persistAndFlush(new Order(
            customer: customer,
            status: OrderStatus.COMPLETED,
            total: 200.00,
            createdAt: LocalDateTime.of(2026, 3, 1, 10, 0)
        ))
    }

    def "findByStatus should filter by order status"() {
        when:
        def completed = orderRepository.findByStatus(OrderStatus.COMPLETED)

        then:
        completed.size() == 2
        completed.every { it.status == OrderStatus.COMPLETED }
    }

    def "findByCreatedAtBetween should filter by date range"() {
        when:
        def result = orderRepository.findByCreatedAtBetween(
            LocalDateTime.of(2026, 1, 1, 0, 0),
            LocalDateTime.of(2026, 2, 1, 23, 59)
        )

        then:
        result.size() == 2
    }

    def "calculateTotalRevenue should sum completed orders"() {
        when:
        def revenue = orderRepository.calculateTotalRevenue(OrderStatus.COMPLETED)

        then:
        revenue == 300.00
    }
}
```

## Entity / Domain Layer

### Validation Testing

```groovy
class UserSpec extends Specification {

    def validator = Validation.buildDefaultValidatorFactory().getValidator()

    @Unroll
    def "should reject invalid email '#email'"() {
        given:
        def user = new User(name: "Alice", email: email, password: "valid123!")

        when:
        def violations = validator.validate(user)

        then:
        !violations.isEmpty()
        violations.any { it.propertyPath.toString() == "email" }

        where:
        email << ["", null, "not-an-email", "@no-local.com", "no-domain@"]
    }

    def "should accept valid user"() {
        given:
        def user = new User(name: "Alice", email: "alice@test.com", password: "valid123!")

        when:
        def violations = validator.validate(user)

        then:
        violations.isEmpty()
    }
}
```

### Equals / HashCode Testing

```groovy
class ProductSpec extends Specification {

    def "equals should compare by ID"() {
        expect:
        new Product(id: 1, name: "A") == new Product(id: 1, name: "B")
        new Product(id: 1) != new Product(id: 2)
        new Product(id: 1) != null
    }

    def "hashCode should be consistent with equals"() {
        given:
        def p1 = new Product(id: 1, name: "A")
        def p2 = new Product(id: 1, name: "B")

        expect:
        p1.hashCode() == p2.hashCode()
    }
}
```

## Configuration Layer

```groovy
@SpringBootTest(properties = [
    "app.cache.enabled=true",
    "app.cache.ttl=300"
])
class CacheConfigSpec extends Specification {

    @Autowired
    ApplicationContext context

    def "should create CacheManager bean when enabled"() {
        expect:
        context.containsBean("cacheManager")
    }
}

@SpringBootTest(properties = ["app.cache.enabled=false"])
class CacheConfigDisabledSpec extends Specification {

    @Autowired
    ApplicationContext context

    def "should not create CacheManager when disabled"() {
        expect:
        !context.containsBean("cacheManager")
    }
}
```

## Utility / Static Method Testing

```groovy
class DateUtilsSpec extends Specification {

    @Unroll
    def "formatDate should produce '#expected' for #input"() {
        expect:
        DateUtils.format(input, "yyyy-MM-dd") == expected

        where:
        input                               | expected
        LocalDate.of(2026, 1, 15)           | "2026-01-15"
        LocalDate.of(2026, 12, 31)          | "2026-12-31"
        LocalDate.of(2000, 1, 1)            | "2000-01-01"
    }

    def "formatDate should throw on null input"() {
        when:
        DateUtils.format(null, "yyyy-MM-dd")

        then:
        thrown(IllegalArgumentException)
    }

    def "formatDate should throw on null pattern"() {
        when:
        DateUtils.format(LocalDate.now(), null)

        then:
        thrown(IllegalArgumentException)
    }
}
```

## Mapper Testing

```groovy
class UserMapperSpec extends Specification {

    def mapper = UserMapper.INSTANCE  // MapStruct generated

    @Unroll
    def "toDTO should map #field correctly"() {
        given:
        def entity = new User(id: 1, name: "Alice", email: "alice@test.com", createdAt: LocalDateTime.of(2026, 1, 1, 0, 0))

        when:
        def dto = mapper.toDTO(entity)

        then:
        dto."$field" == expected

        where:
        field       | expected
        "id"        | 1
        "name"      | "Alice"
        "email"     | "alice@test.com"
    }

    def "toEntity should map from DTO"() {
        given:
        def dto = new CreateUserRequest(name: "Bob", email: "bob@test.com")

        when:
        def entity = mapper.toEntity(dto)

        then:
        entity.name == "Bob"
        entity.email == "bob@test.com"
        entity.id == null  // not set from DTO
    }

    def "toDTO should handle null input"() {
        expect:
        mapper.toDTO(null) == null
    }
}
```
