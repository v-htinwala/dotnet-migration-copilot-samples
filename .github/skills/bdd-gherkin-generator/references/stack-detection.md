# Stack Detection

Detect stack → pick output path + tags + scenario patterns.

## Heuristics

| Signal | Stack | Tag |
|---|---|---|
| `pom.xml`, `build.gradle`, `*.java` | Java | `@java` |
| `*.csproj`, `*.sln`, `Program.cs` | .NET | `@dotnet` |
| `package.json` + `next` dep | Next.js | `@nextjs` |
| `package.json` + `react` dep, no `next` | React | `@react` |
| `package.json` + `express`/`fastify`/`nest` | Node API | `@node` |
| `requirements.txt`, `pyproject.toml`, `*.py` | Python | `@python` |
| `*.go`, `go.mod` | Go | `@go` |

## Layer Detection

| Source pattern | Layer | Tag |
|---|---|---|
| `@RestController`, `@GetMapping`, `[ApiController]`, `app.get(...)`, `route.ts`, `app/api/**/route.ts` | REST | `@rest` |
| `@Service`, `*Service.cs`, `*Service.ts`, domain svc class | Service | `@service` |
| `*.tsx`, `*.jsx`, Razor `*.cshtml`, Vue/Svelte | UI | `@ui` |
| `@Scheduled`, Quartz job, Spring Batch `Job`, Hangfire `BackgroundJob`, `cron`, `node-cron` | Batch | `@batch` |
| `@Controller` + view return, MVC `Controller` returning `View()`, Rails ctrl | MVC | `@mvc` |
| `@Repository`, `DbContext`, Mongoose model, Prisma client | Persistence | `@persistence` |

## Mixed Repo

Multi-stack repo (e.g. Spring backend + Next frontend) → detect per source file. Tag accordingly. Output paths split per stack root.

## Fallback

No signal match → ask user for stack. Don't guess.
