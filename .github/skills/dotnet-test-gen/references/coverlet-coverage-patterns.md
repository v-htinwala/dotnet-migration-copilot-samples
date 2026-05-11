# Coverlet Coverage Patterns

Setup, configuration, and report parsing for Coverlet code coverage with .NET tests.

## Installation & Setup

### Via NuGet (per test project)

```xml
<!-- In test project .csproj -->
<ItemGroup>
  <PackageReference Include="coverlet.collector" Version="6.0.1" />
</ItemGroup>
```

### Via Global Tool

```bash
dotnet tool install --global coverlet.console
```

## Running with Coverage

### Using dotnet test (coverlet.collector)

```bash
# Generate Cobertura XML (default)
dotnet test --collect:"XPlat Code Coverage"

# With specific output format
dotnet test --collect:"XPlat Code Coverage" \
  -- DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Format=json,cobertura

# With threshold enforcement
dotnet test --collect:"XPlat Code Coverage" \
  -- DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Format=cobertura \
     DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Threshold=85 \
     DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.ThresholdType=line,branch,method

# Specific test project
dotnet test tests/MyApp.Tests/MyApp.Tests.csproj \
  --collect:"XPlat Code Coverage"
```

### Using coverlet.console (global tool)

```bash
coverlet tests/MyApp.Tests/bin/Debug/net8.0/MyApp.Tests.dll \
  --target "dotnet" \
  --targetargs "test tests/MyApp.Tests/ --no-build" \
  --format cobertura \
  --format json \
  --output ./coverage/
```

### Report Locations

| Method | Default Path |
|--------|-------------|
| `coverlet.collector` | `tests/MyApp.Tests/TestResults/{guid}/coverage.cobertura.xml` |
| `coverlet.console` | `./coverage/coverage.cobertura.xml` |

## runsettings File

Create a `.runsettings` file for consistent configuration:

```xml
<?xml version="1.0" encoding="utf-8" ?>
<RunSettings>
  <DataCollectionRunSettings>
    <DataCollectors>
      <DataCollector friendlyName="XPlat Code Coverage">
        <Configuration>
          <Format>cobertura,json</Format>
          <Exclude>
            [*]MyApp.Migrations.*,
            [*]MyApp.DTOs.*,
            [*]MyApp.Configuration.*,
            [*]MyApp.Program
          </Exclude>
          <Include>[MyApp]*,[MyApp.Core]*</Include>
          <ExcludeByAttribute>
            Obsolete,
            GeneratedCode,
            CompilerGenerated,
            ExcludeFromCodeCoverage
          </ExcludeByAttribute>
          <ExcludeByFile>**/Migrations/*.cs</ExcludeByFile>
          <SingleHit>false</SingleHit>
          <UseSourceLink>true</UseSourceLink>
          <IncludeTestAssembly>false</IncludeTestAssembly>
        </Configuration>
      </DataCollector>
    </DataCollectors>
  </DataCollectionRunSettings>
</RunSettings>
```

Run with:
```bash
dotnet test --settings .runsettings
```

## Parsing Cobertura XML

### XML Structure

```xml
<?xml version="1.0" encoding="utf-8"?>
<coverage line-rate="0.85" branch-rate="0.72" version="1.0" timestamp="1711234567">
  <packages>
    <package name="MyApp" line-rate="0.85" branch-rate="0.72" complexity="120">
      <classes>
        <class name="MyApp.Services.UserService"
               filename="src/MyApp/Services/UserService.cs"
               line-rate="0.9" branch-rate="0.75" complexity="15">
          <methods>
            <method name="CreateUserAsync" signature="..." line-rate="1.0" branch-rate="1.0">
              <lines>
                <line number="25" hits="3" branch="False" />
                <line number="26" hits="3" branch="True" condition-coverage="100% (2/2)" />
              </lines>
            </method>
            <method name="ValidateEmail" signature="..." line-rate="0.6" branch-rate="0.5">
              <lines>
                <line number="45" hits="2" branch="False" />
                <line number="46" hits="2" branch="True" condition-coverage="50% (1/2)" />
                <line number="47" hits="0" branch="False" />
                <line number="48" hits="0" branch="False" />
              </lines>
            </method>
          </methods>
          <lines>
            <line number="25" hits="3" branch="False" />
            <line number="26" hits="3" branch="True" condition-coverage="100% (2/2)" />
            <line number="45" hits="2" branch="False" />
            <line number="46" hits="2" branch="True" condition-coverage="50% (1/2)" />
            <line number="47" hits="0" branch="False" />
            <line number="48" hits="0" branch="False" />
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
```

### Key XML Elements

- `<coverage>` root: `line-rate` and `branch-rate` are overall (0.0–1.0)
- `<class>`: per-file metrics; `filename` maps to source file
- `<method>`: per-method coverage
- `<line>`: per-line detail
  - `hits="0"` = uncovered line
  - `branch="True"` with `condition-coverage="50% (1/2)"` = partial branch coverage

### Parsing JSON Report

Coverlet JSON is structured by module → class → method → line:

```json
{
  "MyApp.dll": {
    "MyApp.Services.UserService": {
      "System.Threading.Tasks.Task CreateUserAsync(CreateUserRequest)": {
        "Lines": { "25": 3, "26": 3, "27": 3 },
        "Branches": [
          { "Line": 26, "Offset": 15, "Path": 0, "Ordinal": 0, "Hits": 3 },
          { "Line": 26, "Offset": 15, "Path": 1, "Ordinal": 1, "Hits": 0 }
        ]
      }
    }
  }
}
```

## Identifying Gap Files

### Algorithm

1. Parse Cobertura XML for overall class-level `line-rate` and `branch-rate`
2. Filter classes where any metric < threshold (convert 0.0–1.0 to percentage)
3. Sort by number of uncovered lines descending (highest impact first)
4. For top N classes, extract uncovered lines (`hits="0"`) and partial branches
5. Map uncovered lines to methods using `<method>` elements
6. Generate gap data for the generator subagent

### Example Gap Output

```json
{
  "filePath": "src/MyApp/Services/UserService.cs",
  "className": "MyApp.Services.UserService",
  "currentCoverage": {
    "line": 90.0,
    "branch": 75.0,
    "method": 100.0
  },
  "uncoveredRanges": [
    {
      "type": "branch",
      "location": { "startLine": 46, "endLine": 48 },
      "description": "else branch in ValidateEmail — invalid format path",
      "methodName": "ValidateEmail"
    },
    {
      "type": "line",
      "location": { "startLine": 47, "endLine": 48 },
      "description": "Error handling in ValidateEmail — entirely uncovered",
      "methodName": "ValidateEmail"
    }
  ]
}
```

## Exclusions

### Attribute-based exclusion

```csharp
// Exclude entire class
[ExcludeFromCodeCoverage]
public class AutoGeneratedDto { }

// Exclude specific method
[ExcludeFromCodeCoverage]
public string ToString() => $"User({Id}, {Name})";
```

### Pattern-based exclusion (in runsettings)

Common patterns to exclude:
- `[*]*.Migrations.*` — EF Core migrations
- `[*]*.DTOs.*` — Data transfer objects
- `[*]*.Program` — Entry point
- `[*]*.Startup` — DI configuration
- `[*]*.Configuration.*` — Config classes

## Metrics Mapping

Coverlet produces metrics compatible with the orchestrator's expectations:

| Coverlet Metric | Meaning | Cobertura Attribute |
|-----------------|---------|---------------------|
| Line | Source code lines executed | `line-rate` |
| Branch | Decision point arms covered | `branch-rate` |
| Method | Methods entered at least once | `method-rate` (JSON only) |
| Statement | Individual statements (JSON) | N/A (approximate via lines) |

**Threshold guidance**: For the orchestrator's default 85% target, apply to line, branch, and method metrics.

## Generating HTML Reports

```bash
# Install ReportGenerator
dotnet tool install --global dotnet-reportgenerator-globaltool

# Generate HTML from Cobertura
reportgenerator \
  -reports:"tests/**/coverage.cobertura.xml" \
  -targetdir:"coverage-report" \
  -reporttypes:Html

# Generate summary + badge
reportgenerator \
  -reports:"tests/**/coverage.cobertura.xml" \
  -targetdir:"coverage-report" \
  -reporttypes:HtmlSummary,Badges
```
