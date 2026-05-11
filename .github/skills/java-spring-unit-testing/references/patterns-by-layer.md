# Test Patterns by Spring Layer

Layer-specific patterns for generating tests. Each section covers the mock
setup, assertion strategy, and common pitfalls for that layer.

---

## 1. @Service (Business Logic)

### Setup

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock private OrderRepository orderRepository;
    @Mock private PaymentClient paymentClient;
    @Mock private EventPublisher eventPublisher;
    @InjectMocks private OrderService orderService;
}
```

### What to test

| Scenario type | What to assert |
|---|---|
| Business calculation | Computed values (totals, discounts, taxes) |
| Orchestration | `verify` that downstream services are called with correct args |
| Conditional logic | Each branch produces the correct output |
| Mapping before save | `ArgumentCaptor` on `repository.save()` to inspect entity fields |
| Exception propagation | `assertThrows` for each distinct error condition |

### Pattern: Capture-and-Assert

When a service transforms input before delegating:

```java
@Test
void createOrder_mapsFieldsAndSaves() {
    // Arrange
    var request = new CreateOrderRequest("SKU-1", 3, "USD");
    when(orderRepository.save(any(Order.class)))
        .thenAnswer(inv -> {
            var o = inv.getArgument(0, Order.class);
            o.setId(1L);
            return o;
        });

    // Act
    var result = orderService.createOrder(request);

    // Assert — verify mapped entity
    var captor = ArgumentCaptor.forClass(Order.class);
    verify(orderRepository).save(captor.capture());
    var saved = captor.getValue();
    assertEquals("SKU-1", saved.getSku());
    assertEquals(3, saved.getQuantity());
    assertEquals("USD", saved.getCurrency());

    // Assert — verify return value
    assertEquals(1L, result.getId());
}
```

### Pattern: Branch Coverage

```java
@Test
void applyDiscount_premiumCustomer_gets20Percent() {
    var customer = new Customer(CustomerType.PREMIUM);
    var result = orderService.applyDiscount(customer, BigDecimal.valueOf(100));
    assertEquals(BigDecimal.valueOf(80), result);
}

@Test
void applyDiscount_regularCustomer_gets0Percent() {
    var customer = new Customer(CustomerType.REGULAR);
    var result = orderService.applyDiscount(customer, BigDecimal.valueOf(100));
    assertEquals(BigDecimal.valueOf(100), result);
}
```

---

## 2. @RestController (Web Layer)

### Setup — Option A: Unit test (preferred for fast feedback)

```java
@ExtendWith(MockitoExtension.class)
class OrderControllerTest {

    @Mock private OrderService orderService;
    @InjectMocks private OrderController orderController;
}
```

### Setup — Option B: MockMvc (when testing request mapping, validation, serialization)

```java
@WebMvcTest(OrderController.class)
class OrderControllerMvcTest {

    @Autowired private MockMvc mockMvc;
    @MockBean private OrderService orderService;

    @Test
    void getOrder_returnsOrderJson() throws Exception {
        when(orderService.findById(1L)).thenReturn(new OrderDto("ORD-1", 100));

        mockMvc.perform(get("/api/orders/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.orderId").value("ORD-1"))
            .andExpect(jsonPath("$.amount").value(100));
    }
}
```

### What to test

| Scenario type | What to assert |
|---|---|
| Happy path | Status code + response body fields |
| Validation failure | 400 status + error message structure |
| Not found | 404 status + error body |
| Server error | 500 handling (if custom `@ExceptionHandler`) |
| Request mapping | Correct HTTP method + path bind to handler |

### Pattern: Validation Error Response

```java
@Test
void createOrder_blankSku_returns400() throws Exception {
    var body = """
        {"sku": "", "quantity": 3}
        """;

    mockMvc.perform(post("/api/orders")
            .contentType(MediaType.APPLICATION_JSON)
            .content(body))
        .andExpect(status().isBadRequest())
        .andExpect(jsonPath("$.errors[0].field").value("sku"));
}
```

### Pattern: Exception Handler Coverage

```java
@Test
void getOrder_notFound_returns404WithMessage() throws Exception {
    when(orderService.findById(999L))
        .thenThrow(new NotFoundException("Order 999 not found"));

    mockMvc.perform(get("/api/orders/999"))
        .andExpect(status().isNotFound())
        .andExpect(jsonPath("$.message").value("Order 999 not found"));
}
```

---

## 3. @Repository (Custom Queries)

### What to test

Only custom query methods — `@Query` annotated methods, specification-based
queries, criteria API usage. **Do not** test auto-generated `findById`,
`save`, `deleteById`, etc.

### Setup

```java
@DataJpaTest
class OrderRepositoryTest {

    @Autowired private OrderRepository orderRepository;
    @Autowired private TestEntityManager entityManager;

    @Test
    void findByStatusAndDateRange_returnsMatchingOrders() {
        // Arrange — persist test data
        var order1 = entityManager.persist(
            new Order("ORD-1", OrderStatus.PENDING, LocalDate.of(2024, 1, 15)));
        var order2 = entityManager.persist(
            new Order("ORD-2", OrderStatus.COMPLETED, LocalDate.of(2024, 1, 15)));
        entityManager.flush();

        // Act
        var result = orderRepository.findByStatusAndDateRange(
            OrderStatus.PENDING,
            LocalDate.of(2024, 1, 1),
            LocalDate.of(2024, 1, 31));

        // Assert
        assertThat(result).hasSize(1);
        assertEquals("ORD-1", result.get(0).getOrderId());
    }
}
```

---

## 4. MapStruct / Manual Mappers

### What to test

Field-by-field mapping correctness, null handling, collection mapping, nested
object mapping, custom `@Mapping` expressions.

### Pattern: Full-Object Mapping Assertion

```java
@Test
void toDto_mapsAllFields() {
    var entity = new Order();
    entity.setId(1L);
    entity.setCustomerName("Alice");
    entity.setTotal(BigDecimal.valueOf(250.50));
    entity.setCreatedAt(LocalDateTime.of(2024, 3, 15, 10, 30));

    var dto = orderMapper.toDto(entity);

    assertEquals(1L, dto.getId());
    assertEquals("Alice", dto.getCustomerName());
    assertEquals(BigDecimal.valueOf(250.50), dto.getTotal());
    assertEquals("2024-03-15T10:30:00", dto.getCreatedAt()); // if formatted
}
```

### Pattern: Null Source Handling

```java
@Test
void toDto_nullSource_returnsNull() {
    assertNull(orderMapper.toDto(null));
}

@Test
void toDto_nullNestedObject_mapsWithNullField() {
    var entity = new Order();
    entity.setId(1L);
    entity.setAddress(null); // nested object is null

    var dto = orderMapper.toDto(entity);

    assertEquals(1L, dto.getId());
    assertNull(dto.getAddress()); // acceptable — assertNull OK for null-propagation test
}
```

### Pattern: Collection Mapping

```java
@Test
void toDtoList_mapsEachElement() {
    var entities = List.of(
        new Order(1L, "Alice"),
        new Order(2L, "Bob"));

    var dtos = orderMapper.toDtoList(entities);

    assertThat(dtos).hasSize(2);
    assertEquals("Alice", dtos.get(0).getCustomerName());
    assertEquals("Bob", dtos.get(1).getCustomerName());
}
```

---

## 5. Custom Validators (`ConstraintValidator`)

### What to test

Each validation rule boundary, valid input, each invalid variant.

```java
@ExtendWith(MockitoExtension.class)
class PhoneNumberValidatorTest {

    private final PhoneNumberValidator validator = new PhoneNumberValidator();

    @Test
    void isValid_usPhoneFormat_returnsTrue() {
        assertTrue(validator.isValid("+1-555-123-4567", null));
    }

    @Test
    void isValid_tooShort_returnsFalse() {
        assertFalse(validator.isValid("123", null));
    }

    @Test
    void isValid_null_returnsTrue() {
        // Convention: null handling delegated to @NotNull
        assertTrue(validator.isValid(null, null));
    }
}
```

**Note:** For validators, `assertTrue` / `assertFalse` on the boolean return
value IS acceptable — the return type is the contract.

---

## 6. Spring Security Filters / Auth Components

### What to test

Token extraction, authentication object creation, filter chain invocation,
rejection on invalid tokens.

```java
@ExtendWith(MockitoExtension.class)
class JwtAuthFilterTest {

    @Mock private JwtTokenProvider tokenProvider;
    @Mock private HttpServletRequest request;
    @Mock private HttpServletResponse response;
    @Mock private FilterChain filterChain;
    @InjectMocks private JwtAuthFilter jwtAuthFilter;

    @Test
    void doFilter_validToken_setsAuthentication() throws Exception {
        when(request.getHeader("Authorization")).thenReturn("Bearer valid-token");
        when(tokenProvider.validate("valid-token")).thenReturn(true);
        when(tokenProvider.getAuthentication("valid-token"))
            .thenReturn(new UsernamePasswordAuthenticationToken("user", null, List.of()));

        jwtAuthFilter.doFilter(request, response, filterChain);

        verify(filterChain).doFilter(request, response);
        // SecurityContextHolder assertion depends on implementation
    }

    @Test
    void doFilter_noAuthHeader_continuesChainWithoutAuth() throws Exception {
        when(request.getHeader("Authorization")).thenReturn(null);

        jwtAuthFilter.doFilter(request, response, filterChain);

        verify(filterChain).doFilter(request, response);
        verify(tokenProvider, never()).validate(any());
    }

    @Test
    void doFilter_invalidToken_continuesChainWithoutAuth() throws Exception {
        when(request.getHeader("Authorization")).thenReturn("Bearer bad-token");
        when(tokenProvider.validate("bad-token")).thenReturn(false);

        jwtAuthFilter.doFilter(request, response, filterChain);

        verify(filterChain).doFilter(request, response);
        verify(tokenProvider, never()).getAuthentication(any());
    }
}
```

---

## 7. @Scheduled Methods

### What to test

Side-effects of the scheduled method (not the scheduling itself — that is
Spring config).

```java
@ExtendWith(MockitoExtension.class)
class ExpiredOrderCleanupTaskTest {

    @Mock private OrderRepository orderRepository;
    @InjectMocks private ExpiredOrderCleanupTask task;

    @Test
    void cleanupExpiredOrders_deletesOrdersOlderThan30Days() {
        var cutoff = LocalDate.now().minusDays(30);
        var expiredOrders = List.of(new Order("ORD-1"), new Order("ORD-2"));
        when(orderRepository.findByCreatedBefore(cutoff)).thenReturn(expiredOrders);

        task.cleanupExpiredOrders();

        verify(orderRepository).deleteAll(expiredOrders);
    }

    @Test
    void cleanupExpiredOrders_noExpired_doesNotDelete() {
        when(orderRepository.findByCreatedBefore(any())).thenReturn(List.of());

        task.cleanupExpiredOrders();

        verify(orderRepository, never()).deleteAll(any());
    }
}
```

---

## 8. @EventListener Methods

### What to test

Event handling logic and downstream calls triggered by the event.

```java
@ExtendWith(MockitoExtension.class)
class OrderEventListenerTest {

    @Mock private NotificationService notificationService;
    @Mock private AuditService auditService;
    @InjectMocks private OrderEventListener listener;

    @Test
    void onOrderCreated_sendsNotificationAndAudits() {
        var event = new OrderCreatedEvent("ORD-1", "alice@example.com");

        listener.onOrderCreated(event);

        verify(notificationService).sendEmail(
            eq("alice@example.com"),
            contains("ORD-1"));
        verify(auditService).log(eq("ORDER_CREATED"), eq("ORD-1"));
    }
}
```
