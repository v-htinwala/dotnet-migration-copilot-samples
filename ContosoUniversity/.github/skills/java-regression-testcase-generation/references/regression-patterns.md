# Java Regression Testing Patterns

## Common Regression Scenarios

### 1. Service Layer Changes
When a `@Service` class method is modified, generate regression tests that:
- Verify the method still produces correct output for all known input combinations
- Check that downstream consumers receive the same data contracts
- Validate that exception behavior is preserved
- Confirm mock interactions with dependencies remain correct

### 2. Controller/API Endpoint Changes
When a `@RestController` or `@Controller` method is modified:
- Verify HTTP status codes remain unchanged for existing request patterns
- Check response body structure (field names, types, nullability)
- Validate request parameter validation rules still apply
- Test authentication/authorization behavior is preserved
- **For `test_level=integration`**: use `@WebMvcTest` + `MockMvc` instead of mocking (see Integration Patterns below)

### 3. Repository/Data Access Changes
When a `@Repository` or DAO method is modified:
- Verify query results match expected data
- Check that CRUD operations maintain data integrity
- Validate transaction boundaries
- Test optimistic locking and concurrency behavior
- **For `test_level=integration`**: use `@DataJpaTest` with embedded H2 or Testcontainers (see Integration Patterns below)

### 4. Entity/Model Changes
When a JPA `@Entity` or data model class is modified:
- Verify serialization/deserialization produces expected results
- Check that field validations (`@NotNull`, `@Size`, etc.) still apply
- Test equals/hashCode contract consistency
- Validate builder or constructor behavior

### 5. Configuration Changes
When Spring configuration or `@Bean` definitions change:
- Verify bean wiring produces expected application context
- Check that profiles and conditional beans resolve correctly
- Test property binding and validation
- **For `test_level=integration`**: use `@SpringBootTest` to verify full context loading (see Integration Patterns below)

## JUnit 5 Regression Test Structure

```java
@ExtendWith(MockitoExtension.class)
@Tag("regression")
@DisplayName("Regression: UserService after PR #123")
class UserServiceRegressionTest {

    @Mock private UserRepository userRepository;
    @Mock private EmailService emailService;
    @InjectMocks private UserService userService;

    // --- Behavior Preservation Tests ---

    @Test
    @DisplayName("createUser still returns user with generated ID")
    void testCreateUser_behaviorPreserved_returnsUserWithId() {
        // Arrange - same setup as before the change
        when(userRepository.save(any())).thenAnswer(inv -> {
            User u = inv.getArgument(0);
            u.setId(1L);
            return u;
        });

        // Act
        User result = userService.createUser(new CreateUserRequest("test@example.com", "Test", "pass"));

        // Assert - verify same behavior as before
        assertNotNull(result);
        assertNotNull(result.getId());
        assertEquals("test@example.com", result.getEmail());
    }

    // --- Backward Compatibility Tests ---

    @Test
    @DisplayName("findById returns Optional.empty for non-existent ID (backward compat)")
    void testFindById_nonExistentId_returnsEmpty() {
        when(userRepository.findById(999L)).thenReturn(Optional.empty());

        Optional<User> result = userService.findById(999L);

        assertTrue(result.isEmpty());
    }

    // --- Exception Contract Tests ---

    @Test
    @DisplayName("createUser still throws ValidationException for null request")
    void testCreateUser_nullRequest_throwsValidationException() {
        assertThrows(ValidationException.class, () -> userService.createUser(null));
    }

    // --- Integration Point Regression ---

    @Test
    @DisplayName("createUser still calls emailService.sendWelcomeEmail")
    void testCreateUser_success_sendsWelcomeEmail() {
        when(userRepository.save(any())).thenReturn(new User());

        userService.createUser(new CreateUserRequest("test@example.com", "Test", "pass"));

        verify(emailService, times(1)).sendWelcomeEmail("test@example.com");
    }
}
```

## Mockito Patterns for Regression Testing

### Verify Unchanged Interactions
```java
// Verify that the method still calls the same dependencies
verify(repository, times(1)).save(any(User.class));
verify(emailService, times(1)).sendWelcomeEmail(anyString());
verifyNoMoreInteractions(repository, emailService);
```

### Argument Capture for Regression Validation
```java
ArgumentCaptor<User> captor = ArgumentCaptor.forClass(User.class);
verify(repository).save(captor.capture());
User savedUser = captor.getValue();
// Verify the saved object has expected fields
assertEquals("test@example.com", savedUser.getEmail());
assertNotNull(savedUser.getCreatedAt());
```

### Verify Exception Propagation
```java
// Verify that dependency exceptions are still propagated correctly
when(repository.save(any())).thenThrow(new DataAccessException("DB error"));
assertThrows(ServiceException.class, () -> service.createUser(request));
```

## Parameterized Regression Tests

```java
@ParameterizedTest
@MethodSource("provideRegressionInputs")
@Tag("regression")
@DisplayName("processOrder produces consistent results across input variants")
void testProcessOrder_regressionInputs(OrderRequest input, OrderResult expected) {
    when(inventoryService.checkStock(any())).thenReturn(true);
    when(pricingService.calculate(any())).thenReturn(expected.getTotal());

    OrderResult result = orderService.processOrder(input);

    assertEquals(expected.getStatus(), result.getStatus());
    assertEquals(expected.getTotal(), result.getTotal());
}

static Stream<Arguments> provideRegressionInputs() {
    return Stream.of(
        Arguments.of(
            new OrderRequest("PROD-1", 1),
            new OrderResult("CONFIRMED", BigDecimal.valueOf(29.99))
        ),
        Arguments.of(
            new OrderRequest("PROD-2", 5),
            new OrderResult("CONFIRMED", BigDecimal.valueOf(149.95))
        )
    );
}
```

## JaCoCo Configuration

### Maven (pom.xml)
```xml
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.11</version>
    <executions>
        <execution>
            <goals><goal>prepare-agent</goal></goals>
        </execution>
        <execution>
            <id>report</id>
            <phase>test</phase>
            <goals><goal>report</goal></goals>
        </execution>
    </executions>
</plugin>
```

### Gradle (build.gradle)
```groovy
plugins {
    id 'jacoco'
}

test {
    useJUnitPlatform()
    finalizedBy jacocoTestReport
}

jacocoTestReport {
    reports {
        xml.required = true
    }
}
```

## Running Selected Tests

### Maven
```bash
# Run specific test class
mvn test -Dtest=UserServiceRegressionTest -B -q

# Run multiple test classes
mvn test -Dtest=UserServiceRegressionTest,OrderServiceRegressionTest -B -q

# Run specific test method
mvn test -Dtest=UserServiceRegressionTest#testCreateUser_behaviorPreserved -B -q

# Run tests matching a pattern
mvn test -Dtest="*RegressionTest" -B -q

# Run in a specific module
mvn test -pl module-core -Dtest=UserServiceRegressionTest -B -q
```

### Gradle
```bash
# Run specific test class
gradle test --tests "com.example.UserServiceRegressionTest"

# Run specific test method
gradle test --tests "com.example.UserServiceRegressionTest.testCreateUser*"

# Run in a specific module
gradle :module-core:test --tests "com.example.UserServiceRegressionTest"
```

## Common Java Regression Risks

| Risk | Detection | Mitigation |
|---|---|---|
| Serialization changes | JSON field rename/remove in DTOs | Test serialization round-trip |
| Interface contract break | Method signature change in interfaces | Test all known implementors |
| Thread safety regression | Synchronized block removed/changed | Test concurrent access |
| Spring bean wiring change | `@Bean` or `@Component` modified | Test ApplicationContext loading |
| Exception type change | Catch block or throws clause modified | Test exception types explicitly |
| Default value change | Constructor or field default modified | Test with default construction |
| Null handling change | Null check added/removed | Test with null inputs |
| Collection ordering | Sort/order logic modified | Test element ordering |

## Data-Driven Regression Tests

When user-provided test data is available, prefer loading data from fixture files
over hardcoded inline values.

### SQL Seed Data with @DataJpaTest
```java
@DataJpaTest
@Tag("regression")
@Sql({"classpath:schema.sql", "classpath:test-data.sql"})
class OrderRepositoryRegressionTest {

    @Autowired
    private OrderRepository orderRepository;

    @Test
    @DisplayName("findByStatus returns seeded orders after query refactoring")
    void testFindByStatus_withSeededData_returnsExpected() {
        List<Order> orders = orderRepository.findByStatus("PENDING");
        assertFalse(orders.isEmpty());
        assertTrue(orders.stream().allMatch(o -> "PENDING".equals(o.getStatus())));
    }
}
```

### CSV File-Driven Parameterized Tests
```java
@ParameterizedTest
@CsvFileSource(resources = "/fixtures/order-inputs.csv", numLinesToSkip = 1)
@Tag("regression")
@DisplayName("processOrder produces consistent results from CSV fixture")
void testProcessOrder_csvFixture(String productId, int quantity, String expectedStatus) {
    OrderRequest request = new OrderRequest(productId, quantity);
    when(inventoryService.checkStock(any())).thenReturn(true);

    OrderResult result = orderService.processOrder(request);

    assertEquals(expectedStatus, result.getStatus());
}
```

### JSON Fixture Loading with Jackson
```java
@BeforeEach
void setUp() throws Exception {
    ObjectMapper mapper = new ObjectMapper();
    testUser = mapper.readValue(
        getClass().getResourceAsStream("/fixtures/user-valid.json"),
        User.class
    );
}
```

### Golden-File Assertion Pattern
```java
@Test
@Tag("regression")
@DisplayName("toDto still produces expected JSON structure")
void testToDto_goldenFile_matchesExpected() throws Exception {
    UserDto actual = userService.toDto(testUser);
    String actualJson = objectMapper.writerWithDefaultPrettyPrinter()
        .writeValueAsString(actual);

    String expectedJson = Files.readString(
        Path.of("src/test/resources/expected/user-dto.json")
    );

    JSONAssert.assertEquals(expectedJson, actualJson, JSONCompareMode.STRICT);
}
```

## Integration Regression Test Patterns

Use these patterns when `test_level` is `integration` or `both`. Integration tests
use `*IT.java` suffix and verify behavior through the real Spring context.

### @WebMvcTest — Controller Integration
```java
@WebMvcTest(UserController.class)
@Tag("regression")
@DisplayName("Regression: UserController integration after PR #123")
class UserControllerIT {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private UserService userService;

    @Test
    @DisplayName("GET /api/users/{id} still returns 200 with valid user")
    void testGetUser_existingId_returns200() throws Exception {
        when(userService.findById(1L)).thenReturn(Optional.of(new User(1L, "test@example.com")));

        mockMvc.perform(get("/api/users/1")
                .contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.email").value("test@example.com"));
    }

    @Test
    @DisplayName("GET /api/users/{id} still returns 404 for non-existent ID")
    void testGetUser_nonExistentId_returns404() throws Exception {
        when(userService.findById(999L)).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/users/999"))
            .andExpect(status().isNotFound());
    }

    @Test
    @DisplayName("POST /api/users still validates request body")
    void testCreateUser_invalidBody_returns400() throws Exception {
        mockMvc.perform(post("/api/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"email\": \"\", \"name\": null}"))
            .andExpect(status().isBadRequest());
    }
}
```

### @DataJpaTest — Repository Integration
```java
@DataJpaTest
@Tag("regression")
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@DisplayName("Regression: UserRepository queries after schema change")
class UserRepositoryIT {

    @Autowired
    private TestEntityManager entityManager;

    @Autowired
    private UserRepository userRepository;

    @BeforeEach
    void setUp() {
        User user = new User();
        user.setEmail("test@example.com");
        user.setName("Test User");
        entityManager.persistAndFlush(user);
    }

    @Test
    @DisplayName("findByEmail still returns user with matching email")
    void testFindByEmail_existingEmail_returnsUser() {
        Optional<User> found = userRepository.findByEmail("test@example.com");
        assertTrue(found.isPresent());
        assertEquals("Test User", found.get().getName());
    }
}
```

### @SpringBootTest — Full Context Integration
```java
@SpringBootTest
@AutoConfigureMockMvc
@Tag("regression")
@DisplayName("Regression: Full application context after config change")
class ApplicationContextIT {

    @Autowired
    private ApplicationContext context;

    @Autowired
    private MockMvc mockMvc;

    @Test
    @DisplayName("Application context loads successfully after bean changes")
    void testContextLoads() {
        assertNotNull(context);
    }

    @Test
    @DisplayName("All required beans are present")
    void testRequiredBeans_present() {
        assertNotNull(context.getBean(UserService.class));
        assertNotNull(context.getBean(OrderService.class));
    }
}
```

### @WebFluxTest — Reactive Controller Integration
```java
@WebFluxTest(UserReactiveController.class)
@Tag("regression")
class UserReactiveControllerIT {

    @Autowired
    private WebTestClient webTestClient;

    @MockBean
    private UserReactiveService userService;

    @Test
    @DisplayName("GET /api/users/{id} reactive endpoint still returns user")
    void testGetUser_returnsUser() {
        when(userService.findById(1L)).thenReturn(Mono.just(new User(1L, "test@example.com")));

        webTestClient.get().uri("/api/users/1")
            .exchange()
            .expectStatus().isOk()
            .expectBody()
            .jsonPath("$.email").isEqualTo("test@example.com");
    }
}
```

### Testcontainers — Real Database Testing
```java
@SpringBootTest
@Testcontainers
@Tag("regression")
@DisplayName("Regression: OrderService with real PostgreSQL after migration")
class OrderServiceContainerIT {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private OrderService orderService;

    @Autowired
    private OrderRepository orderRepository;

    @Test
    @Sql("classpath:test-data/orders.sql")
    @DisplayName("processOrder persists order to real database")
    void testProcessOrder_realDb_persistsOrder() {
        OrderRequest request = new OrderRequest("PROD-1", 2);
        Order result = orderService.processOrder(request);

        assertNotNull(result.getId());
        assertTrue(orderRepository.findById(result.getId()).isPresent());
    }
}
```

## Requirement-Traced Regression Tests

When requirement IDs or regression scenarios are provided, use structured
annotations for traceability.

### Requirement Tags
```java
@ExtendWith(MockitoExtension.class)
@Tag("regression")
@Tag("REQ-1234")
@Tag("REQ-1235")
@DisplayName("Regression: PaymentService [REQ-1234] payment processing preserved")
class PaymentServiceRegressionTest {

    @Test
    @Tag("REQ-1234")
    @DisplayName("[REQ-1234] processPayment still deducts from wallet")
    void testProcessPayment_deductsFromWallet() {
        // ...
    }
}
```

### Scenario-Driven Nested Classes
```java
@ExtendWith(MockitoExtension.class)
@Tag("regression")
@DisplayName("Regression: OrderService")
class OrderServiceRegressionTest {

    @Nested
    @Tag("REQ-5001")
    @DisplayName("Scenario: Order workflow data integrity [REQ-5001]")
    class OrderWorkflowDataIntegrity {

        @Test
        @DisplayName("createOrder still generates unique order number")
        void testCreateOrder_generatesUniqueOrderNumber() { /* ... */ }

        @Test
        @DisplayName("cancelOrder still refunds payment")
        void testCancelOrder_refundsPayment() { /* ... */ }
    }

    @Nested
    @Tag("REQ-5002")
    @DisplayName("Scenario: Order backward compatibility [REQ-5002]")
    class OrderBackwardCompatibility {

        @Test
        @DisplayName("legacy API still accepts v1 order format")
        void testLegacyApi_acceptsV1Format() { /* ... */ }
    }
}
```

## CI/CD Integration Patterns

### Maven Surefire — Flaky Test Rerun
```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-surefire-plugin</artifactId>
    <configuration>
        <rerunFailingTestsCount>2</rerunFailingTestsCount>
    </configuration>
</plugin>
```

### Gradle — Test Retry Plugin
```groovy
plugins {
    id 'org.gradle.test-retry' version '1.5.8'
}

test {
    retry {
        maxRetries = 2
        maxFailures = 5
        failOnPassedAfterRetry = false
    }
}
```

### Tagging Flaky Tests for Quarantine
```java
@Tag("flaky")
@Tag("regression")
@RepeatedTest(3)
@DisplayName("processPayment with external gateway (known flaky)")
void testProcessPayment_externalGateway_eventuallySucceeds(RepetitionInfo info) {
    // Known flaky due to external service; quarantined from blocking CI
}
```

### Maven Failsafe — Integration Test Execution
```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-failsafe-plugin</artifactId>
    <executions>
        <execution>
            <goals>
                <goal>integration-test</goal>
                <goal>verify</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```
