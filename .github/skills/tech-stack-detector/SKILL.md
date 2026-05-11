---
name: tech-stack-detector
description: >
  Auto-detects the technology stack, frameworks, languages, and tooling from a
  codebase directory. Analyzes package manifests (package.json, pom.xml,
  requirements.txt, Gemfile, composer.json, *.csproj), directory structures,
  import patterns, and configuration files to identify frontend/backend
  frameworks, ORMs, validation libraries, test frameworks, and package managers.
  Supports a fixed catalog of ~20 major frameworks with deep detection and falls
  back to heuristic analysis for unlisted frameworks. Use when preparing for
  codebase analysis, functional test generation, or any task that needs to know
  the tech stack before applying framework-specific parsing strategies.
license: MIT
compatibility: >
  Works with any skills-compatible coding agent with file system read access.
  No external dependencies required — detection is purely file-based analysis.
metadata:
  author: functional-test-automation
  version: "1.0"
  category: testing
  user-invokable: "false"
---

# Tech Stack Detector

## Purpose

Auto-detect the technology stack from a codebase directory to enable framework-
specific analysis in downstream skills. This skill reads package manifests,
configuration files, and directory structures to identify exactly which
frameworks, languages, and tools are in use — then produces a structured
`stack-profile.json` that downstream skills (especially codebase-functional-
analyzer) use to select the correct parsing strategy.

## When to Use This Skill

- Before any codebase analysis that needs framework-specific parsing
- When the user provides a codebase path and the tech stack is unknown
- When generating functional test cases that need framework-aware route/
  validation/endpoint extraction
- When building a project profile for test coverage analysis

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `codebase_path` | Yes | — | Root directory of the application codebase |
| `output_dir` | Yes | — | Output directory for stack-profile.json |

## Outputs

| File | Format | Description |
|---|---|---|
| `stack-profile.json` | JSON | Complete tech stack profile with confidence scores and file evidence |

### Output Schema

```json
{
  "primary_language": "TypeScript",
  "frontend_framework": "React",
  "frontend_meta_framework": "Next.js",
  "backend_framework": "Express",
  "backend_language": "TypeScript",
  "package_manager": "npm",
  "test_framework": "Jest",
  "orm": "Prisma",
  "validation_library": "Zod",
  "css_framework": "Tailwind CSS",
  "auth_library": "NextAuth.js",
  "api_style": "REST",
  "monorepo": false,
  "monorepo_tool": null,
  "detection_confidence": 0.95,
  "file_evidence": {
    "package.json": ["react", "next", "express", "prisma"],
    "tsconfig.json": "TypeScript confirmed",
    "tailwind.config.js": "Tailwind CSS confirmed",
    "prisma/schema.prisma": "Prisma ORM confirmed"
  },
  "detected_frameworks": [
    {
      "name": "React",
      "category": "frontend",
      "version": "18.2.0",
      "confidence": 0.99,
      "evidence": "package.json dependency"
    },
    {
      "name": "Next.js",
      "category": "frontend_meta",
      "version": "14.1.0",
      "confidence": 0.99,
      "evidence": "package.json dependency + next.config.js present"
    },
    {
      "name": "Express",
      "category": "backend",
      "version": "4.18.2",
      "confidence": 0.95,
      "evidence": "package.json dependency"
    }
  ]
}
```

---

## 4-Phase Detection Workflow

### Phase 1: Package Manifest Analysis

**Goal**: Read all package/dependency manifests to identify declared dependencies.

Scan for these files (in priority order):

| File | Ecosystem | Key Dependencies to Check |
|---|---|---|
| `package.json` | Node.js/JavaScript | React, Next.js, Angular, Vue, Nuxt, Svelte, Express, Fastify, NestJS |
| `pom.xml` | Java/Maven | Spring Boot, Spring Web, Hibernate |
| `build.gradle` / `build.gradle.kts` | Java/Gradle | Spring Boot plugin, dependencies |
| `requirements.txt` / `Pipfile` / `pyproject.toml` | Python | Django, Flask, FastAPI, SQLAlchemy |
| `Gemfile` | Ruby | Rails, Sinatra |
| `composer.json` | PHP | Laravel, Symfony |
| `*.csproj` / `*.fsproj` | .NET | Microsoft.AspNetCore, Entity Framework |
| `go.mod` | Go | Gin, Echo, Fiber |
| `Cargo.toml` | Rust | Actix, Rocket, Axum |

**For each dependency found**:
- Record name, version (if available), and source file
- Match against the [framework catalog](references/framework-catalog.md)
- Set initial confidence: 0.8 (dependency listed but not yet confirmed by structure)

### Phase 2: Directory Structure Analysis

**Goal**: Confirm framework detection by checking for characteristic directory structures.

| Pattern | Confirms |
|---|---|
| `pages/` or `app/` directory at root | Next.js or Nuxt.js (file-based routing) |
| `src/app/` with `*.component.ts` | Angular |
| `src/components/` with `*.vue` | Vue.js |
| `src/routes/` with `+page.svelte` | SvelteKit |
| `config/routes.rb` | Rails |
| `urls.py` in multiple directories | Django |
| `prisma/schema.prisma` | Prisma ORM |
| `migrations/` directory | Database ORM present |
| `__tests__/` or `*.test.ts` / `*.spec.ts` | Test framework in use |
| `.github/workflows/` | CI/CD configured |
| `docker-compose.yml` | Containerized |

**Confidence boost**: If directory structure confirms package manifest, increase
confidence by +0.1 (to 0.9).

### Phase 3: Configuration & Import Pattern Analysis

**Goal**: Detect configuration files and import patterns for final confirmation.

**Configuration files**:
| File | Confirms |
|---|---|
| `next.config.js` / `next.config.mjs` | Next.js |
| `angular.json` | Angular |
| `nuxt.config.ts` / `nuxt.config.js` | Nuxt.js |
| `svelte.config.js` | SvelteKit |
| `vite.config.ts` | Vite bundler |
| `webpack.config.js` | Webpack bundler |
| `tailwind.config.js` | Tailwind CSS |
| `tsconfig.json` | TypeScript |
| `.eslintrc.*` / `eslint.config.*` | ESLint |
| `jest.config.*` / `vitest.config.*` | Test configuration |

**Import pattern sampling** (scan first 50 source files max):
- `import ... from 'react'` → React confirmed
- `from django.` → Django confirmed
- `@Controller`, `@Injectable` → Angular or NestJS
- `@SpringBootApplication` → Spring Boot

**Confidence boost**: Config file + imports → confidence 0.95-0.99.

### Phase 4: Synthesis & Output

**Goal**: Produce the final `stack-profile.json`.

1. **Resolve conflicts**: If multiple competing frameworks detected (e.g., React
   AND Angular), use confidence scores to pick the primary. Flag secondary as
   `alternative_detected`.

2. **Classify each framework**:
   - `frontend`: UI rendering framework
   - `frontend_meta`: Full-stack meta-framework (Next.js, Nuxt, SvelteKit)
   - `backend`: Server framework
   - `orm`: Database access layer
   - `validation`: Input validation library
   - `test`: Testing framework
   - `css`: Styling framework/library

3. **Detect monorepo**:
   - `workspaces` in package.json → npm/yarn workspaces
   - `lerna.json` → Lerna
   - `pnpm-workspace.yaml` → pnpm workspaces
   - `nx.json` → Nx
   - `turbo.json` → Turborepo
   - Multiple package manifests at different directory levels

4. **Detect API style**:
   - REST (default for Express, Django REST, Spring Boot)
   - GraphQL (`graphql`, `apollo-server`, `@nestjs/graphql` dependencies)
   - tRPC (`@trpc/server` dependency)
   - gRPC (`.proto` files, gRPC dependencies)

5. **Write** `stack-profile.json` to `output_dir`.

---

## Fallback: Unknown Frameworks

When frameworks not in the catalog are detected:

1. **Identify language**: Based on file extensions (`.py`, `.rb`, `.java`, etc.)
2. **Scan for route patterns**: Search for HTTP method annotations/functions
   (`@app.route`, `app.get`, `router.post`, etc.)
3. **Scan for validation patterns**: Search for schema/validation imports
4. **Output shallow profile**:
   ```json
   {
     "primary_language": "Python",
     "frontend_framework": "unknown",
     "backend_framework": "unknown (FastHTML suspected)",
     "detection_confidence": 0.4,
     "file_evidence": {
       "requirements.txt": ["fasthtml"],
       "file_extensions": {".py": 45, ".html": 12}
     },
     "fallback_analysis": {
       "route_patterns_found": true,
       "validation_patterns_found": false,
       "estimated_route_count": 8
     }
   }
   ```

---

## Constraints

1. **Read-only**: Never modify the codebase. Only read files.
2. **Performance**: Scan at most 200 files total. Prioritize manifests and
   config files. Use file extension counts for language detection rather than
   reading every source file.
3. **No execution**: Never execute project code, build scripts, or package
   managers. Detection is purely static file analysis.
4. **Monorepo handling**: If monorepo detected, analyze each workspace/package
   separately and merge results. Report `monorepo: true` with workspace list.
5. **Confidence threshold**: Minimum 0.3 to include a framework in the output.
   Below 0.3, mention in `fallback_analysis` only.

## Error Handling

| Error | Behavior |
|---|---|
| Codebase path not found | Fail with clear error message |
| Empty directory | Output profile with `detection_confidence: 0` and `"no_files_found": true` |
| No package manifests found | Fall back to file extension analysis, set confidence ≤ 0.4 |
| Binary-heavy project (assets, compiled) | Skip binary files, analyze only text files |
| Permission errors on files | Skip inaccessible files, log warning, continue |

## Related Skills

| Skill | Relationship |
|---|---|
| **codebase-functional-analyzer** | Downstream — consumes stack-profile.json to select framework-specific parsing |
| **functional-scenario-merger** | Downstream — merges codebase-sourced scenarios |
| **functional-test-orchestrator** | Orchestrator — invokes this skill as Phase 2 step 1 |
