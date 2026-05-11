# Output Paths

Stack → directory. Mirror source path under features root.

## Root Per Stack

| Stack | Features root |
|---|---|
| Java (Maven/Gradle) | `src/test/resources/features/` |
| .NET | `tests/features/` |
| Next.js / React / Node | `tests/features/` |
| Python | `tests/features/` |
| Go | `tests/features/` |
| Multi-module | per-module root above |

## Mirror Rule

Source `src/main/java/com/acme/account/AccountController.java`
→ `src/test/resources/features/account/account-create.feature` (one per endpoint).

Source `app/api/users/route.ts`
→ `tests/features/api/users/users-list.feature`, `users-create.feature`.

Source `app/components/LoginForm.tsx`
→ `tests/features/components/login-form-submit.feature`.

## File Name

`<resource>-<action>.feature` kebab-case. One file per endpoint/use case/job/component interaction.

## Existing Files

File exists → don't overwrite. Append new scenarios under existing `Feature:` if same use case. Different use case → new file with `-v2` suffix only if user confirms. Otherwise prompt.

## Confirm Before Bulk Write

>10 files in single run → list paths, confirm, then write.
