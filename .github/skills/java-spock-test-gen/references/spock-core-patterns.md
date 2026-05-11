# Spock Core Patterns

## Setup — Maven

### pom.xml Dependencies

```xml
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>org.spockframework</groupId>
      <artifactId>spock-bom</artifactId>
      <version>2.4-M4-groovy-4.0</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>

<dependencies>
  <dependency>
    <groupId>org.spockframework</groupId>
    <artifactId>spock-core</artifactId>
    <scope>test</scope>
  </dependency>
  <!-- Optional: Spring integration -->
  <dependency>
    <groupId>org.spockframework</groupId>
    <artifactId>spock-spring</artifactId>
    <scope>test</scope>
  </dependency>
</dependencies>

<build>
  <plugins>
    <!-- Groovy compilation -->
    <plugin>
      <groupId>org.codehaus.gmavenplus</groupId>
      <artifactId>gmavenplus-plugin</artifactId>
      <version>3.0.2</version>
      <executions>
        <execution>
          <goals>
            <goal>compileTests</goal>
          </goals>
        </execution>
      </executions>
    </plugin>
    <!-- Surefire must include **/*Spec.groovy -->
    <plugin>
      <groupId>org.apache.maven.plugins</groupId>
      <artifactId>maven-surefire-plugin</artifactId>
      <configuration>
        <includes>
          <include>**/*Spec.groovy</include>
          <include>**/*Test.groovy</include>
        </includes>
      </configuration>
    </plugin>
  </plugins>
</build>
```

### Gradle Dependencies

```groovy
plugins {
    id 'groovy'
    id 'jacoco'
}

dependencies {
    testImplementation platform('org.spockframework:spock-bom:2.4-M4-groovy-4.0')
    testImplementation 'org.spockframework:spock-core'
    testImplementation 'org.spockframework:spock-spring' // Optional
}

test {
    useJUnitPlatform()
}
```

## Specification Structure

### Minimal spec

```groovy
package com.example.util

import spock.lang.Specification

class StringUtilsSpec extends Specification {

    def "capitalize should uppercase first letter"() {
        expect:
        StringUtils.capitalize("hello") == "Hello"
    }
}
```

### Full BDD spec

```groovy
package com.example.order

import spock.lang.Specification
import spock.lang.Subject

class OrderServiceSpec extends Specification {

    def orderRepository = Mock(OrderRepository)
    def paymentGateway = Mock(PaymentGateway)
    def eventPublisher = Mock(EventPublisher)

    @Subject
    def orderService = new OrderService(orderRepository, paymentGateway, eventPublisher)

    def "should place order when payment succeeds"() {
        given: "a valid order request"
        def request = new OrderRequest(
            customerId: "C001",
            items: [new OrderItem(productId: "P1", quantity: 2, price: 25.00)]
        )

        and: "payment will succeed"
        paymentGateway.charge(_ as PaymentRequest) >> new PaymentResult(success: true, transactionId: "TX123")

        when: "the order is placed"
        def order = orderService.placeOrder(request)

        then: "the order is saved"
        1 * orderRepository.save({ Order o ->
            o.customerId == "C001"
            o.status == OrderStatus.CONFIRMED
            o.total == 50.00
        })

        and: "an event is published"
        1 * eventPublisher.publish({ OrderPlacedEvent e ->
            e.orderId != null
            e.customerId == "C001"
        })

        and: "the order is returned with confirmation"
        order.status == OrderStatus.CONFIRMED
        order.transactionId == "TX123"
    }

    def "should reject order when payment fails"() {
        given: "a valid order request"
        def request = new OrderRequest(customerId: "C001", items: [new OrderItem()])

        and: "payment will fail"
        paymentGateway.charge(_ as PaymentRequest) >> new PaymentResult(success: false, error: "Insufficient funds")

        when: "the order is placed"
        orderService.placeOrder(request)

        then: "a payment exception is thrown"
        def ex = thrown(PaymentException)
        ex.message.contains("Insufficient funds")

        and: "no order is saved"
        0 * orderRepository.save(_)

        and: "no event is published"
        0 * eventPublisher.publish(_)
    }
}
```

## BDD Blocks Reference

### given: / setup:
Preconditions — variable assignments, mock stubbing. Both keywords are identical; `given:` reads better in BDD context.

```groovy
given: "an existing user"
def user = new User(id: 1, name: "Alice", email: "alice@test.com")
userRepository.findById(1) >> Optional.of(user)
```

### when:
The stimulus — exactly one action. Keep it focused on a single method call.

```groovy
when: "the user profile is updated"
def result = userService.updateProfile(1, updateRequest)
```

### then:
Assertions and interaction verifications. Conditions are implicit assertions — any boolean expression that evaluates to `false` fails the test.

```groovy
then: "the user is saved with updated fields"
1 * userRepository.save({ User u ->
    u.name == "Bob"
    u.email == "bob@test.com"
})
result.success == true
```

### expect:
Combines `when:` and `then:` for pure functions and simple assertions. Best for stateless operations.

```groovy
expect: "formatting produces correct output"
formatter.formatCurrency(1000, "USD") == "$1,000.00"
```

### where:
Data tables for parameterized tests. Always the last block. Must be paired with `@Unroll` for readable test names.

```groovy
@Unroll
def "validate returns #expected for email '#email'"() {
    expect:
    validator.isValidEmail(email) == expected

    where:
    email                | expected
    "user@example.com"   | true
    "invalid"            | false
    ""                   | false
    null                 | false
    "user@.com"          | false
    "a@b.c"              | true
}
```

### and:
Continuation of the previous block. Improves readability for complex blocks.

```groovy
then: "the order is saved"
1 * orderRepository.save(_)

and: "a notification is sent"
1 * notificationService.send(_)
```

### cleanup:
Resource cleanup — runs even if the test fails. Use for closing connections, files, etc.

```groovy
cleanup:
connection?.close()
tempFile?.delete()
```

## Lifecycle Methods

```groovy
class MySpec extends Specification {

    // Runs before EACH feature method (like @BeforeEach)
    def setup() {
        // Reset state
    }

    // Runs after EACH feature method (like @AfterEach)
    def cleanup() {
        // Tear down
    }

    // Runs ONCE before the first feature method (like @BeforeAll)
    def setupSpec() {
        // Shared setup (must use @Shared fields)
    }

    // Runs ONCE after the last feature method (like @AfterAll)
    def cleanupSpec() {
        // Shared teardown
    }
}
```

## @Shared Fields

Fields shared across all feature methods (not re-initialized per test):

```groovy
@Shared
def expensiveResource = createExpensiveResource()
```

Use sparingly — shared mutable state can cause test coupling.

## Exception Testing

```groovy
def "should throw on invalid input"() {
    when:
    service.process(null)

    then:
    def ex = thrown(IllegalArgumentException)
    ex.message == "Input must not be null"
}

def "should not throw on valid input"() {
    when:
    service.process("valid")

    then:
    noExceptionThrown()
}
```

## Timeout

```groovy
@Timeout(5) // 5 seconds
def "should complete within time limit"() {
    // ...
}

@Timeout(value = 500, unit = TimeUnit.MILLISECONDS)
def "should respond quickly"() {
    // ...
}
```

## Conditional Execution

```groovy
@Requires({ env.CI })
def "only runs on CI"() { ... }

@IgnoreIf({ os.windows })
def "skip on Windows"() { ... }

@Requires({ jvm.java17Compatible })
def "needs Java 17+"() { ... }
```

## Running Tests

### Maven
```bash
# All tests
mvn test --no-transfer-progress

# Specific spec
mvn test -Dtest="AuthServiceSpec" --no-transfer-progress

# Pattern match
mvn test -Dtest="com.example.auth.*Spec" --no-transfer-progress
```

### Gradle
```bash
# All tests
./gradlew test --no-daemon

# Specific spec
./gradlew test --tests "com.example.auth.AuthServiceSpec" --no-daemon

# Pattern match
./gradlew test --tests "com.example.auth.*" --no-daemon
```
