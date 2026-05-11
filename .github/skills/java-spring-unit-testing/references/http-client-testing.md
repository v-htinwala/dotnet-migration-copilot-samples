# HTTP Client Testing Patterns

Detailed mock/verify patterns for all three Spring HTTP clients:
**RestClient** (Spring 6.1+), **WebClient** (reactive), and **RestTemplate** (legacy).

---

## 1. RestClient (Spring 6.1+)

RestClient uses a fluent builder API. The mock chain must match every builder
step in the source code.

### Mock Setup Pattern

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock private RestClient restClient;
    @Mock private RestClient.RequestHeadersUriSpec<?> requestHeadersUriSpec;
    @Mock private RestClient.RequestHeadersSpec<?> requestHeadersSpec;
    @Mock private RestClient.ResponseSpec responseSpec;

    @InjectMocks private UserService userService;

    @BeforeEach
    void setUp() {
        // Chain: restClient.get() → .uri(...) → .retrieve() → .body(...)
        when(restClient.get()).thenReturn(requestHeadersUriSpec);
        when(requestHeadersUriSpec.uri(anyString())).thenReturn(requestHeadersSpec);
        when(requestHeadersSpec.retrieve()).thenReturn(responseSpec);
    }
}
```

### Happy Path — GET

```java
@Test
void fetchUser_returnsDeserializedUser() {
    var expected = new UserDto("u-1", "Alice", "alice@example.com");
    when(responseSpec.body(UserDto.class)).thenReturn(expected);

    var result = userService.fetchUser("u-1");

    assertEquals("u-1", result.getId());
    assertEquals("Alice", result.getName());
    assertEquals("alice@example.com", result.getEmail());
    verify(requestHeadersUriSpec).uri("/api/users/u-1");
}
```

### Happy Path — POST with Request Body

```java
@Mock private RestClient.RequestBodyUriSpec requestBodyUriSpec;
@Mock private RestClient.RequestBodySpec requestBodySpec;

@Test
void createUser_sendsBodyAndReturnsCreated() {
    var request = new CreateUserRequest("Bob", "bob@example.com");
    var response = new UserDto("u-2", "Bob", "bob@example.com");

    when(restClient.post()).thenReturn(requestBodyUriSpec);
    when(requestBodyUriSpec.uri("/api/users")).thenReturn(requestBodySpec);
    when(requestBodySpec.contentType(MediaType.APPLICATION_JSON)).thenReturn(requestBodySpec);
    when(requestBodySpec.body(request)).thenReturn(requestBodySpec);
    when(requestBodySpec.retrieve()).thenReturn(responseSpec);
    when(responseSpec.body(UserDto.class)).thenReturn(response);

    var result = userService.createUser(request);

    assertEquals("u-2", result.getId());
    assertEquals("Bob", result.getName());
    verify(requestBodySpec).body(request);
}
```

### Error — 4xx Response

```java
@Test
void fetchUser_404_throwsNotFoundException() {
    when(responseSpec.body(UserDto.class))
        .thenThrow(new HttpClientErrorException(HttpStatus.NOT_FOUND, "Not Found"));

    assertThrows(NotFoundException.class,
        () -> userService.fetchUser("unknown-id"));
}
```

### Error — 5xx Response

```java
@Test
void fetchUser_500_throwsServiceException() {
    when(responseSpec.body(UserDto.class))
        .thenThrow(new HttpServerErrorException(HttpStatus.INTERNAL_SERVER_ERROR));

    assertThrows(ExternalServiceException.class,
        () -> userService.fetchUser("u-1"));
}
```

### Verifying Headers

```java
@Test
void fetchUser_sendsAuthorizationHeader() {
    when(responseSpec.body(UserDto.class)).thenReturn(new UserDto("u-1", "Alice", "a@b.com"));

    // If the source code adds headers:
    // restClient.get().uri(...).header("Authorization", "Bearer token").retrieve()...
    when(requestHeadersSpec.header(eq("Authorization"), eq("Bearer test-token")))
        .thenReturn(requestHeadersSpec);

    userService.fetchUserWithAuth("u-1", "test-token");

    verify(requestHeadersSpec).header("Authorization", "Bearer test-token");
}
```

---

## 2. WebClient (Reactive)

WebClient returns `Mono` / `Flux`. Mock the reactive chain and use
`StepVerifier` or `.block()` for assertions.

### Mock Setup Pattern

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock private WebClient webClient;
    @Mock private WebClient.RequestHeadersUriSpec<?> requestHeadersUriSpec;
    @Mock private WebClient.RequestHeadersSpec<?> requestHeadersSpec;
    @Mock private WebClient.ResponseSpec responseSpec;

    @InjectMocks private UserService userService;

    @BeforeEach
    @SuppressWarnings("unchecked")
    void setUp() {
        when(webClient.get()).thenReturn(requestHeadersUriSpec);
        when(requestHeadersUriSpec.uri(anyString())).thenReturn(requestHeadersSpec);
        when(requestHeadersSpec.retrieve()).thenReturn(responseSpec);
    }
}
```

### Happy Path — GET returning Mono

```java
@Test
void fetchUser_returnsUser() {
    var expected = new UserDto("u-1", "Alice", "alice@example.com");
    when(responseSpec.bodyToMono(UserDto.class)).thenReturn(Mono.just(expected));

    var result = userService.fetchUser("u-1").block();

    assertEquals("u-1", result.getId());
    assertEquals("Alice", result.getName());
}
```

### Happy Path — GET returning Flux

```java
@Test
void fetchAllUsers_returnsUserList() {
    var user1 = new UserDto("u-1", "Alice", "a@b.com");
    var user2 = new UserDto("u-2", "Bob", "b@c.com");
    when(responseSpec.bodyToFlux(UserDto.class)).thenReturn(Flux.just(user1, user2));

    StepVerifier.create(userService.fetchAllUsers())
        .assertNext(u -> assertEquals("Alice", u.getName()))
        .assertNext(u -> assertEquals("Bob", u.getName()))
        .verifyComplete();
}
```

### Error — WebClient Error Signal

```java
@Test
void fetchUser_404_propagatesError() {
    when(responseSpec.bodyToMono(UserDto.class))
        .thenReturn(Mono.error(
            WebClientResponseException.create(404, "Not Found",
                HttpHeaders.EMPTY, new byte[0], null)));

    StepVerifier.create(userService.fetchUser("unknown"))
        .expectError(NotFoundException.class)
        .verify();
}
```

### POST with Body

```java
@Mock private WebClient.RequestBodyUriSpec requestBodyUriSpec;
@Mock private WebClient.RequestBodySpec requestBodySpec;

@Test
void createUser_sendsAndReturns() {
    var request = new CreateUserRequest("Bob", "bob@b.com");
    var response = new UserDto("u-2", "Bob", "bob@b.com");

    when(webClient.post()).thenReturn(requestBodyUriSpec);
    when(requestBodyUriSpec.uri("/api/users")).thenReturn(requestBodySpec);
    when(requestBodySpec.bodyValue(request)).thenReturn(requestHeadersSpec);
    when(requestHeadersSpec.retrieve()).thenReturn(responseSpec);
    when(responseSpec.bodyToMono(UserDto.class)).thenReturn(Mono.just(response));

    var result = userService.createUser(request).block();

    assertEquals("u-2", result.getId());
}
```

---

## 3. RestTemplate (Legacy)

RestTemplate is simpler to mock — direct method calls, no builder chain.

### Mock Setup

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock private RestTemplate restTemplate;
    @InjectMocks private UserService userService;
}
```

### Happy Path — GET

```java
@Test
void fetchUser_returnsDeserializedUser() {
    var expected = new UserDto("u-1", "Alice", "alice@example.com");
    when(restTemplate.getForObject("/api/users/u-1", UserDto.class))
        .thenReturn(expected);

    var result = userService.fetchUser("u-1");

    assertEquals("u-1", result.getId());
    assertEquals("Alice", result.getName());
}
```

### Happy Path — POST

```java
@Test
void createUser_postsAndReturnsCreated() {
    var request = new CreateUserRequest("Bob", "bob@b.com");
    var response = new ResponseEntity<>(
        new UserDto("u-2", "Bob", "bob@b.com"), HttpStatus.CREATED);

    when(restTemplate.postForEntity(eq("/api/users"), eq(request), eq(UserDto.class)))
        .thenReturn(response);

    var result = userService.createUser(request);

    assertEquals("u-2", result.getId());
    assertEquals(HttpStatus.CREATED, response.getStatusCode());
}
```

### Error — Exchange with Error

```java
@Test
void fetchUser_404_throwsNotFoundException() {
    when(restTemplate.getForObject("/api/users/unknown", UserDto.class))
        .thenThrow(new HttpClientErrorException(HttpStatus.NOT_FOUND));

    assertThrows(NotFoundException.class,
        () -> userService.fetchUser("unknown"));
}
```

### Verifying Request with Exchange

```java
@Test
void createUser_sendsCorrectHeaders() {
    var captor = ArgumentCaptor.forClass(HttpEntity.class);
    var response = new ResponseEntity<>(new UserDto("u-2", "Bob", "b@b.com"), HttpStatus.CREATED);

    when(restTemplate.exchange(
        eq("/api/users"),
        eq(HttpMethod.POST),
        captor.capture(),
        eq(UserDto.class)))
        .thenReturn(response);

    userService.createUserWithHeaders(new CreateUserRequest("Bob", "b@b.com"), "token-123");

    var captured = captor.getValue();
    assertEquals("Bearer token-123", captured.getHeaders().getFirst("Authorization"));
    assertEquals(MediaType.APPLICATION_JSON, captured.getHeaders().getContentType());
}
```

---

## Common Pitfalls Across All Clients

### Pitfall 1: Incomplete Fluent Chain Mocking (RestClient / WebClient)

If the source code calls `.header(...)` but the test doesn't mock it, the test
throws NPE. **Always trace the full chain in the source code and mock every step.**

### Pitfall 2: Using `any()` for URI Verification

```java
// BAD — doesn't verify the correct endpoint was called
verify(requestHeadersUriSpec).uri(anyString());

// GOOD
verify(requestHeadersUriSpec).uri("/api/users/u-1");
```

### Pitfall 3: Not Testing Error Responses

Every HTTP client interaction should have at least:
- One happy-path test
- One 4xx error test
- One 5xx error test (if the service handles server errors differently)

### Pitfall 4: Ignoring Response Body Parsing

```java
// BAD — only checks status, not the parsed body
assertDoesNotThrow(() -> service.fetchUser("u-1"));

// GOOD — verifies the full parsed response
var result = service.fetchUser("u-1");
assertEquals("Alice", result.getName());
```
