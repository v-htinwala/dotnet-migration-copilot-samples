---
name: bdd-gherkin-generator
description: >
  Generate BDD scenarios in Gherkin (.feature) from existing codebase. Auto-detect
  stack (Java, .NET, Next.js/React, Python, batch, MVC, UI). Produce one .feature
  per endpoint or use case. Output files only — no step definitions, no runner glue.
  Triggers: "generate BDD", "write gherkin", "create .feature files", "BDD scenarios
  from code", "gherkin from controller", "gherkin from service", "gherkin from UI",
  "gherkin from batch job", "behavior tests from code".
license: MIT
compatibility: >
  Stack-agnostic. Reads source. Writes .feature files only. No runtime deps.
keywords:
  - bdd
  - gherkin
  - feature file
  - cucumber
  - specflow
  - behave
  - scenario
  - given when then
  - acceptance test
  - behavior driven
---

# bdd-gherkin-generator

Generate Gherkin `.feature` files from existing source. One feature per endpoint/use case. No step defs.

## Response Style (mandatory)

Terse. Technical substance stays. Fluff dies.

- Drop articles (a/an/the), filler (just/really/basically/actually/simply), pleasantries, hedging.
- Fragments OK. Short synonyms. Technical terms exact. Code blocks unchanged. Errors quoted exact.
- Pattern: `[thing] [action] [reason]. [next step].`
- Abbreviate: DB, auth, config, req, res, fn, impl, ctrl, svc, repo.
- Arrows for causality: `X → Y`.
- Drop terse mode for: security warnings, destructive confirms, multi-step sequences where order matters, user repeats question. Resume after.

## Workflow

1. Detect stack → see [references/stack-detection.md](references/stack-detection.md).
2. Pick input layer per user req: ctrl/endpoint, svc method, UI component, batch job, MVC route.
3. Map source → scenarios → see [references/scenario-patterns.md](references/scenario-patterns.md).
4. Resolve output path → see [references/output-paths.md](references/output-paths.md).
5. Render via [templates/feature.template](templates/feature.template).
6. Write `.feature`. No step defs. No glue.

## Scenario Coverage Rules

Per use case, minimum 3 scenarios:

- happy path
- error/failure (4xx, exception, validation fail)
- edge case (boundary, empty, null, concurrent, auth-denied)

Add more when source reveals branches. One Scenario per branch. Use `Scenario Outline` + `Examples` when same flow, varied data.

## Gherkin Rules

- `Feature:` = one endpoint/use case/component.
- `Background:` only when 2+ scenarios share setup.
- `Given` = preconditions/state. `When` = single action. `Then` = observable outcome.
- `And`/`But` to extend prior step. No `When` chains — split scenarios.
- Tags: `@<stack> @<layer> @<priority>` (e.g. `@java @rest @smoke`).
- Imperative voice. Past tense banned in `Then`.
- No impl detail in steps. Talk domain, not classes.

## Naming

- File: `<resource>-<action>.feature` kebab-case. Example: `account-create.feature`.
- Feature title: domain phrase. Example: `Feature: Account registration`.
- Scenario title: outcome-led. Example: `Scenario: Registering with duplicate email returns 409`.

## Tag Map

| Layer | Tag |
|---|---|
| REST/API | `@rest` |
| Service/domain | `@service` |
| UI/component | `@ui` |
| Batch/job | `@batch` |
| MVC route | `@mvc` |
| DB/repo | `@persistence` |

Priority: `@smoke` (happy), `@regression` (error/edge), `@security` (authz/authn).

## Out of Scope

- Step definitions. Runner config. Cucumber/SpecFlow/Behave wiring. CI integration. Test data seeding scripts.

## Verify After Generation

- File at correct path per stack.
- Frontmatter `Feature:` present.
- ≥3 scenarios per use case OR justified fewer.
- Each scenario has Given+When+Then.
- No impl leak (class names, method names, SQL) in steps.
