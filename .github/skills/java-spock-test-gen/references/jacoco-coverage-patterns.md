# JaCoCo Coverage Patterns

Setup, configuration, and report parsing for JaCoCo code coverage with Spock tests.

## Maven Setup

### pom.xml — JaCoCo Plugin

```xml
<build>
  <plugins>
    <plugin>
      <groupId>org.jacoco</groupId>
      <artifactId>jacoco-maven-plugin</artifactId>
      <version>0.8.12</version>
      <executions>
        <!-- Prepare agent for test execution -->
        <execution>
          <id>prepare-agent</id>
          <goals>
            <goal>prepare-agent</goal>
          </goals>
        </execution>
        <!-- Generate report after tests -->
        <execution>
          <id>report</id>
          <phase>test</phase>
          <goals>
            <goal>report</goal>
          </goals>
        </execution>
        <!-- Optional: enforce thresholds -->
        <execution>
          <id>check</id>
          <goals>
            <goal>check</goal>
          </goals>
          <configuration>
            <rules>
              <rule>
                <element>BUNDLE</element>
                <limits>
                  <limit>
                    <counter>INSTRUCTION</counter>
                    <value>COVEREDRATIO</value>
                    <minimum>0.85</minimum>
                  </limit>
                  <limit>
                    <counter>BRANCH</counter>
                    <value>COVEREDRATIO</value>
                    <minimum>0.85</minimum>
                  </limit>
                </limits>
              </rule>
            </rules>
          </configuration>
        </execution>
      </executions>
    </plugin>
  </plugins>
</build>
```

### Running with Maven

```bash
# Run tests + generate coverage report
mvn clean test jacoco:report --no-transfer-progress

# Run tests + check thresholds (fails build if below)
mvn clean test jacoco:check --no-transfer-progress

# Run specific tests with coverage
mvn test jacoco:report -Dtest="com.example.auth.*Spec" --no-transfer-progress
```

### Report locations (Maven)

| Format | Path |
|--------|------|
| HTML | `target/site/jacoco/index.html` |
| CSV | `target/site/jacoco/jacoco.csv` |
| XML | `target/site/jacoco/jacoco.xml` |
| Exec | `target/jacoco.exec` |

## Gradle Setup

### build.gradle

```groovy
plugins {
    id 'jacoco'
}

jacoco {
    toolVersion = "0.8.12"
}

test {
    useJUnitPlatform()
    finalizedBy jacocoTestReport
}

jacocoTestReport {
    dependsOn test

    reports {
        xml.required = true
        csv.required = true
        html.required = true
    }
}

// Optional: enforce thresholds
jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit {
                counter = 'INSTRUCTION'
                value = 'COVEREDRATIO'
                minimum = 0.85
            }
            limit {
                counter = 'BRANCH'
                value = 'COVEREDRATIO'
                minimum = 0.85
            }
        }
    }
}

check.dependsOn jacocoTestCoverageVerification
```

### Running with Gradle

```bash
# Run tests + generate report
./gradlew clean test jacocoTestReport --no-daemon

# Run tests + verify thresholds
./gradlew clean test jacocoTestCoverageVerification --no-daemon

# Specific tests
./gradlew test jacocoTestReport --tests "com.example.auth.*" --no-daemon
```

### Report locations (Gradle)

| Format | Path |
|--------|------|
| HTML | `build/reports/jacoco/test/html/index.html` |
| CSV | `build/reports/jacoco/test/jacocoTestReport.csv` |
| XML | `build/reports/jacoco/test/jacocoTestReport.xml` |
| Exec | `build/jacoco/test.exec` |

## Parsing CSV Reports

The CSV format is easiest to parse programmatically:

```
GROUP,PACKAGE,CLASS,INSTRUCTION_MISSED,INSTRUCTION_COVERED,BRANCH_MISSED,BRANCH_COVERED,LINE_MISSED,LINE_COVERED,COMPLEXITY_MISSED,COMPLEXITY_COVERED,METHOD_MISSED,METHOD_COVERED
myapp,com.example.auth,AuthService,15,85,4,12,5,30,3,10,1,8
myapp,com.example.user,UserService,25,75,8,8,10,25,5,8,2,6
```

**Calculate percentages**:
```
instruction_pct = INSTRUCTION_COVERED / (INSTRUCTION_MISSED + INSTRUCTION_COVERED) * 100
branch_pct = BRANCH_COVERED / (BRANCH_MISSED + BRANCH_COVERED) * 100
line_pct = LINE_COVERED / (LINE_MISSED + LINE_COVERED) * 100
method_pct = METHOD_COVERED / (METHOD_MISSED + METHOD_COVERED) * 100
```

## Parsing XML Reports (Detailed)

XML provides line-level detail needed for gap-filling:

```xml
<report name="myapp">
  <package name="com/example/auth">
    <class name="com/example/auth/AuthService" sourcefilename="AuthService.java">
      <method name="authenticate" desc="(Ljava/lang/String;Ljava/lang/String;)Lcom/example/auth/User;" line="25">
        <counter type="INSTRUCTION" missed="0" covered="15"/>
        <counter type="BRANCH" missed="2" covered="4"/>
        <counter type="LINE" missed="0" covered="8"/>
      </method>
      <method name="validateToken" desc="(Ljava/lang/String;)Z" line="45">
        <counter type="INSTRUCTION" missed="12" covered="3"/>
        <counter type="BRANCH" missed="3" covered="1"/>
        <counter type="LINE" missed="5" covered="2"/>
      </method>
    </class>
    <sourcefile name="AuthService.java">
      <line nr="25" mi="0" ci="4" mb="0" cb="0"/>
      <line nr="26" mi="0" ci="3" mb="0" cb="2"/>
      <line nr="27" mi="0" ci="2" mb="1" cb="1"/>  <!-- Partial branch -->
      <line nr="45" mi="4" ci="0" mb="2" cb="0"/>  <!-- Fully uncovered -->
      <line nr="46" mi="3" ci="0" mb="1" cb="0"/>  <!-- Fully uncovered -->
    </sourcefile>
  </package>
</report>
```

**Key XML elements**:
- `<method>` — per-method coverage counters
- `<sourcefile>` → `<line>` — per-line detail
  - `mi` = missed instructions, `ci` = covered instructions
  - `mb` = missed branches, `cb` = covered branches
- Lines with `mi > 0` = partially or fully uncovered
- Lines with `mb > 0` = uncovered branches (if/else arms)

## Identifying Gap Files

### Algorithm

1. Parse CSV for overall class-level metrics
2. Filter classes where any metric < threshold
3. Sort by `INSTRUCTION_MISSED` descending (highest impact first)
4. For top N classes, parse XML for line-level detail
5. Map uncovered lines to methods using `<method>` elements
6. Generate gap data for the generator subagent

### Example gap output

```json
{
  "filePath": "src/main/java/com/example/auth/AuthService.java",
  "className": "com.example.auth.AuthService",
  "currentCoverage": {
    "instruction": 70.0,
    "branch": 50.0,
    "line": 72.0,
    "method": 87.5
  },
  "uncoveredRanges": [
    {
      "type": "branch",
      "location": { "startLine": 27, "endLine": 30 },
      "description": "else branch in authenticate — invalid password path",
      "methodName": "authenticate"
    },
    {
      "type": "method",
      "location": { "startLine": 45, "endLine": 55 },
      "description": "validateToken — entirely uncovered",
      "methodName": "validateToken"
    }
  ]
}
```

## Exclusions

### Exclude from coverage (common patterns)

**Maven** — in JaCoCo plugin configuration:
```xml
<configuration>
  <excludes>
    <exclude>**/config/**</exclude>
    <exclude>**/dto/**</exclude>
    <exclude>**/exception/**</exclude>
    <exclude>**/*Application.*</exclude>
    <exclude>**/generated/**</exclude>
  </excludes>
</configuration>
```

**Gradle**:
```groovy
jacocoTestReport {
    afterEvaluate {
        classDirectories.setFrom(files(classDirectories.files.collect {
            fileTree(dir: it, exclude: [
                '**/config/**',
                '**/dto/**',
                '**/exception/**',
                '**/*Application.*',
                '**/generated/**'
            ])
        }))
    }
}
```

## Metrics Mapping

JaCoCo uses different terminology than JavaScript coverage tools:

| JaCoCo Counter | Meaning | JS Equivalent |
|----------------|---------|---------------|
| INSTRUCTION | Bytecode instructions executed | ~Statements |
| BRANCH | Decision points (if/switch arms) | Branches |
| LINE | Source code lines | Lines |
| METHOD | Methods entered | Functions |
| COMPLEXITY | Cyclomatic complexity paths | N/A |

**Threshold guidance**: For the orchestrator's default 85% target, apply to INSTRUCTION, BRANCH, LINE, and METHOD counters.
