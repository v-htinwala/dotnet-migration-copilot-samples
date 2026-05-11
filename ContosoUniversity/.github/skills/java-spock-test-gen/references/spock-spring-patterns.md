# Spock Spring Integration Patterns

Testing Spring Boot applications with Spock using `spock-spring` module.

## Test Annotations Overview

| Annotation | Scope | Speed | Use For |
|------------|-------|-------|---------|
| None (plain Spock) | Unit only | Fastest | Services, utilities with mocked deps |
| `@SpringBootTest` | Full context | Slowest | Integration tests, complex wiring |
| `@WebMvcTest` | Web layer slice | Fast | Controllers with MockMvc |
| `@DataJpaTest` | JPA slice | Medium | Repositories with embedded DB |
| `@WebFluxTest` | Reactive web slice | Fast | Reactive controllers |
| `@JsonTest` | JSON serialization | Fast | DTOs, JSON mapping |

**Prefer plain Spock specs with `Mock()` for unit tests.** Use Spring test slices only when you need the Spring context (e.g., MockMvc, JPA queries).

## Plain Spock (No Spring Context)

Best for **service** and **utility** classes. Fastest execution.

```groovy
class UserServiceSpec extends Specification {

    def userRepository = Mock(UserRepository)
    def passwordEncoder = Mock(PasswordEncoder)
    def eventPublisher = Mock(ApplicationEventPublisher)

    @Subject
    def userService = new UserService(userRepository, passwordEncoder, eventPublisher)

    def "should create user with encoded password"() {
        given: "a registration request"
        def request = new CreateUserRequest(
            name: "Alice",
            email: "alice@test.com",
            password: "plaintext"
        )

        and: "password encoding returns a hash"
        passwordEncoder.encode("plaintext") >> "hashed-password"

        and: "save returns the user with an ID"
        userRepository.save(_ as User) >> { User u -> u.tap { id = 42L } }

        when: "the user is created"
        def result = userService.createUser(request)

        then: "the user is saved with encoded password"
        1 * userRepository.save({ User u ->
            u.name == "Alice"
            u.email == "alice@test.com"
            u.password == "hashed-password"
        })

        and: "an event is published"
        1 * eventPublisher.publishEvent(_ as UserCreatedEvent)

        and: "the response contains the user ID"
        result.id == 42L
    }
}
```

## @WebMvcTest — Controller Testing

```groovy
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest
import org.springframework.boot.test.mock.mockbean.MockBean
import org.springframework.test.web.servlet.MockMvc
import spock.lang.Specification

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*

@WebMvcTest(UserController)
class UserControllerSpec extends Specification {

    @Autowired
    MockMvc mockMvc

    @MockBean
    UserService userService

    def "GET /api/users/{id} should return user"() {
        given: "a user exists"
        def user = new UserDTO(id: 1, name: "Alice", email: "alice@test.com")
        userService.findById(1L) >> user

        when: "the endpoint is called"
        def result = mockMvc.perform(get("/api/users/1")
            .contentType("application/json"))

        then: "200 OK with user data"
        result.andExpect(status().isOk())
              .andExpect(jsonPath('$.name').value("Alice"))
              .andExpect(jsonPath('$.email').value("alice@test.com"))
    }

    def "GET /api/users/{id} should return 404 when not found"() {
        given: "the user does not exist"
        userService.findById(999L) >> { throw new UserNotFoundException(999L) }

        when: "the endpoint is called"
        def result = mockMvc.perform(get("/api/users/999"))

        then: "404 Not Found"
        result.andExpect(status().isNotFound())
              .andExpect(jsonPath('$.message').value("User not found: 999"))
    }

    def "POST /api/users should create user"() {
        given: "a valid request body"
        def requestBody = '{"name": "Alice", "email": "alice@test.com", "password": "secret123"}'

        and: "service returns created user"
        userService.createUser(_ as CreateUserRequest) >> new UserDTO(id: 1, name: "Alice")

        when: "the endpoint is called"
        def result = mockMvc.perform(post("/api/users")
            .contentType("application/json")
            .content(requestBody))

        then: "201 Created"
        result.andExpect(status().isCreated())
              .andExpect(jsonPath('$.id').value(1))
    }

    def "POST /api/users should return 400 for invalid input"() {
        given: "an invalid request body (missing required fields)"
        def requestBody = '{"name": ""}'

        when: "the endpoint is called"
        def result = mockMvc.perform(post("/api/users")
            .contentType("application/json")
            .content(requestBody))

        then: "400 Bad Request with validation errors"
        result.andExpect(status().isBadRequest())
              .andExpect(jsonPath('$.errors').isNotEmpty())
    }
}
```

### With Security

```groovy
import org.springframework.security.test.context.support.WithMockUser

@WebMvcTest(AdminController)
class AdminControllerSpec extends Specification {

    @Autowired
    MockMvc mockMvc

    @MockBean
    AdminService adminService

    @WithMockUser(roles = "ADMIN")
    def "admin endpoint should be accessible with ADMIN role"() {
        when:
        def result = mockMvc.perform(get("/api/admin/dashboard"))

        then:
        result.andExpect(status().isOk())
    }

    @WithMockUser(roles = "USER")
    def "admin endpoint should be forbidden for USER role"() {
        when:
        def result = mockMvc.perform(get("/api/admin/dashboard"))

        then:
        result.andExpect(status().isForbidden())
    }

    def "admin endpoint should return 401 without authentication"() {
        when:
        def result = mockMvc.perform(get("/api/admin/dashboard"))

        then:
        result.andExpect(status().isUnauthorized())
    }
}
```

## @DataJpaTest — Repository Testing

```groovy
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager
import spock.lang.Specification

@DataJpaTest
class UserRepositorySpec extends Specification {

    @Autowired
    TestEntityManager entityManager

    @Autowired
    UserRepository userRepository

    def "findByEmail should return user when exists"() {
        given: "a user in the database"
        def user = new User(name: "Alice", email: "alice@test.com", active: true)
        entityManager.persistAndFlush(user)

        when: "searching by email"
        def result = userRepository.findByEmail("alice@test.com")

        then: "the user is found"
        result.isPresent()
        result.get().name == "Alice"
    }

    def "findByEmail should return empty when not found"() {
        when:
        def result = userRepository.findByEmail("nobody@test.com")

        then:
        result.isEmpty()
    }

    def "findActiveUsers should return only active users"() {
        given: "active and inactive users"
        entityManager.persistAndFlush(new User(name: "Active", email: "a@t.com", active: true))
        entityManager.persistAndFlush(new User(name: "Inactive", email: "i@t.com", active: false))

        when:
        def result = userRepository.findActiveUsers()

        then:
        result.size() == 1
        result[0].name == "Active"
    }

    def "should support pagination"() {
        given: "many users"
        (1..25).each { i ->
            entityManager.persistAndFlush(new User(name: "User$i", email: "u$i@t.com", active: true))
        }

        when:
        def page = userRepository.findAll(PageRequest.of(0, 10, Sort.by("name")))

        then:
        page.totalElements == 25
        page.content.size() == 10
        page.totalPages == 3
    }
}
```

## @SpringBootTest — Full Integration

Use sparingly — only when you need the full application context.

```groovy
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.boot.test.mock.mockbean.MockBean
import org.springframework.beans.factory.annotation.Autowired

@SpringBootTest
class OrderIntegrationSpec extends Specification {

    @Autowired
    OrderService orderService

    @MockBean
    PaymentGateway paymentGateway  // Mock external dependency

    @Autowired
    OrderRepository orderRepository  // Real repository with test DB

    def "should create order end-to-end"() {
        given: "payment will succeed"
        paymentGateway.charge(_) >> new PaymentResult(success: true)

        when: "order is placed"
        def order = orderService.placeOrder(new OrderRequest(/* ... */))

        then: "order is persisted"
        def saved = orderRepository.findById(order.id)
        saved.isPresent()
        saved.get().status == OrderStatus.CONFIRMED
    }
}
```

## @JsonTest — Serialization Testing

```groovy
import org.springframework.boot.test.autoconfigure.json.JsonTest
import org.springframework.boot.test.json.JacksonTester
import org.springframework.beans.factory.annotation.Autowired

@JsonTest
class UserDTOJsonSpec extends Specification {

    @Autowired
    JacksonTester<UserDTO> json

    def "should serialize to JSON"() {
        given:
        def dto = new UserDTO(id: 1, name: "Alice", email: "alice@test.com")

        when:
        def result = json.write(dto)

        then:
        result.extractingJsonPathStringValue('$.name') == "Alice"
        result.extractingJsonPathNumberValue('$.id') == 1
    }

    def "should deserialize from JSON"() {
        given:
        def content = '{"id": 1, "name": "Alice", "email": "alice@test.com"}'

        when:
        def result = json.parse(content)

        then:
        result.getObject().name == "Alice"
        result.getObject().id == 1
    }
}
```

## Test Properties

```groovy
@SpringBootTest(properties = [
    "app.feature.dark-mode=true",
    "app.external.api-url=http://mock-server"
])
class FeatureFlagSpec extends Specification {
    // ...
}
```

Or use `@TestPropertySource`:

```groovy
@SpringBootTest
@TestPropertySource(locations = "classpath:test-application.yml")
class ConfigSpec extends Specification {
    // ...
}
```

## @MockBean vs Spock Mock()

| Feature | `@MockBean` | Spock `Mock()` |
|---------|-------------|----------------|
| Spring context aware | Yes — replaces bean | No — manual wiring |
| Interaction verification | Via Mockito (limited) | Full Spock syntax |
| Speed | Slower (context reload) | Faster |
| Use when | Need Spring DI, `@WebMvcTest` | Unit tests, no Spring |

**Recommendation**: Use Spock `Mock()` for unit tests. Use `@MockBean` only in `@WebMvcTest`, `@DataJpaTest`, and `@SpringBootTest` where the Spring context must be involved.
