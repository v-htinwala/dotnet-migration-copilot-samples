# Scenario Patterns

Source → Gherkin shape. Pick pattern by layer.

## REST Endpoint

Inputs: HTTP verb, path, req schema, res schema, status codes, auth annotations.

```gherkin
Scenario: <verb> <resource> with valid payload returns <2xx>
  Given authenticated <role>
  And payload <field set>
  When client sends <VERB> <path>
  Then response status is <2xx>
  And response body contains <key fields>

Scenario: <verb> <resource> with invalid payload returns <4xx>
  Given payload missing <field>
  When client sends <VERB> <path>
  Then response status is <4xx>
  And error message is "<exact error>"

Scenario: <verb> <resource> unauthenticated returns 401
  Given no auth token
  When client sends <VERB> <path>
  Then response status is 401
```

Branches → one scenario per: each status code, each validation rule, each authz check, each conditional response shape.

## Service / Domain Method

Inputs: method sig, preconditions (assertions, guards), state mutations, events emitted, exceptions thrown.

```gherkin
Scenario: <action> with valid state <observable outcome>
  Given <aggregate> in state <X>
  When <action> invoked with <args>
  Then <aggregate> transitions to state <Y>
  And event <EventName> emitted

Scenario: <action> with invalid state raises error
  Given <aggregate> in state <X>
  When <action> invoked
  Then error "<ExceptionType>" raised
  And state unchanged
```

## UI Component

Inputs: rendered elements, user events (click/input/submit), conditional render, async states (loading/error/empty).

```gherkin
Scenario: User submits form with valid data
  Given user on <page>
  And field <label> filled with "<value>"
  When user clicks "<button>"
  Then <success message> shown
  And user redirected to <route>

Scenario: Form shows validation error on empty required field
  Given user on <page>
  And field <label> empty
  When user clicks "<button>"
  Then validation error "<exact text>" shown under <label>

Scenario: Loading state shown while data fetches
  Given <page> loading
  When request pending
  Then loading indicator visible
```

## Batch / Job

Inputs: trigger (cron, queue, event), input source, processing logic, output sink, retry/failure policy.

```gherkin
Scenario: Job processes batch successfully
  Given <N> records in <source>
  When job <name> triggered
  Then all records processed
  And output written to <sink>
  And job status is "completed"

Scenario: Job retries on transient failure
  Given <source> unavailable
  When job <name> triggered
  Then job retries up to <N> times
  And final status is "failed" if all retries exhaust

Scenario: Job skips already-processed records
  Given record <id> marked processed
  When job <name> triggered
  Then record <id> not reprocessed
```

## MVC Controller (server-rendered)

Inputs: route, action method, model binding, view name, redirect rules.

```gherkin
Scenario: GET <route> renders <view> for authenticated user
  Given authenticated <role>
  When user navigates to <route>
  Then view <view> rendered
  And model contains <key>

Scenario: POST <route> with valid form redirects to <target>
  Given form fields <set>
  When user submits POST <route>
  Then redirect to <target>
  And flash message "<text>" shown

Scenario: GET <route> unauthenticated redirects to login
  Given no session
  When user navigates to <route>
  Then redirect to /login
```

## Persistence Layer (when explicitly requested)

```gherkin
Scenario: Repository persists entity with required fields
  Given entity <type> with <fields>
  When save invoked
  Then entity stored
  And id generated
```

## Coverage Heuristic

Branches in source = scenarios in feature. Each `if`, `switch`, `try/catch`, guard clause, validation rule → 1 scenario. Same flow + varied data → `Scenario Outline`.
