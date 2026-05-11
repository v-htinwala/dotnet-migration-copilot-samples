# Framework Catalog — tech-stack-detector

Complete detection signals for all supported frameworks. The tech-stack-detector
uses these patterns to identify frameworks, their route definitions, validation
approaches, and ORM/data-access patterns.

---

## Frontend Frameworks

### React

| Aspect | Detection Signals |
|--------|------------------|
| **Package** | `react` in package.json dependencies |
| **Files** | `.jsx`, `.tsx` file extensions |
| **Imports** | `import React from 'react'`, `import { useState }` |
| **Config** | None specific (often paired with meta-framework) |
| **Route Pattern** | React Router: `<Route path="..." element={...} />`, `createBrowserRouter()` |
| **Validation** | PropTypes, Yup (`yup`), Zod (`zod`), React Hook Form (`react-hook-form`) |
| **State** | Redux (`redux`, `@reduxjs/toolkit`), Zustand, Recoil, Jotai |

### Next.js

| Aspect | Detection Signals |
|--------|------------------|
| **Package** | `next` in package.json dependencies |
| **Files** | `pages/` directory OR `app/` directory (App Router) |
| **Imports** | `import { useRouter } from 'next/router'`, `'next/navigation'` |
| **Config** | `next.config.js`, `next.config.mjs`, `next.config.ts` |
| **Route Pattern** | File-based: `pages/api/vehicles.ts` → `/api/vehicles`, `app/dashboard/page.tsx` → `/dashboard` |
| **Validation** | Same as React + server actions with Zod |
| **API Routes** | `pages/api/*.ts` (Pages Router) or `app/*/route.ts` (App Router) |

### Angular

| Aspect | Detection Signals |
|--------|------------------|
| **Package** | `@angular/core` in package.json |
| **Files** | `*.component.ts`, `*.module.ts`, `*.service.ts` |
| **Imports** | `import { Component } from '@angular/core'` |
| **Config** | `angular.json`, `tsconfig.app.json` |
| **Route Pattern** | `RouterModule.forRoot([{ path: '...', component: ... }])` |
| **Validation** | Template-driven forms (`FormsModule`), Reactive forms (`ReactiveFormsModule`) |
| **Structure** | `src/app/` with component folders |

### Vue.js

| Aspect | Detection Signals |
|--------|------------------|
| **Package** | `vue` in package.json dependencies |
| **Files** | `*.vue` single-file components |
| **Imports** | `import { createApp } from 'vue'` |
| **Config** | `vue.config.js`, `vite.config.ts` with Vue plugin |
| **Route Pattern** | Vue Router: `{ path: '/...', component: ... }` in router config |
| **Validation** | Vuelidate (`@vuelidate/core`), VeeValidate (`vee-validate`) |

### Nuxt.js

| Aspect | Detection Signals |
|--------|------------------|
| **Package** | `nuxt` in package.json dependencies |
| **Files** | `pages/` directory, `*.vue` files |
| **Config** | `nuxt.config.ts`, `nuxt.config.js` |
| **Route Pattern** | File-based: `pages/users/[id].vue` → `/users/:id` |
| **Validation** | Same as Vue |
| **API Routes** | `server/api/*.ts` |

### Svelte / SvelteKit

| Aspect | Detection Signals |
|--------|------------------|
| **Package** | `svelte` or `@sveltejs/kit` in package.json |
| **Files** | `*.svelte` files |
| **Config** | `svelte.config.js` |
| **Route Pattern** | File-based: `src/routes/+page.svelte`, `src/routes/api/+server.ts` |
| **Validation** | Superforms (`sveltekit-superforms`), Zod |

---

## Backend Frameworks

### Express / Node.js

| Aspect | Detection Signals |
|--------|------------------|
| **Package** | `express` in package.json |
| **Files** | `routes/*.js`, `controllers/*.js`, `middleware/*.js` |
| **Imports** | `const express = require('express')`, `import express from 'express'` |
| **Route Pattern** | `app.get('/path', handler)`, `router.post('/path', handler)`, `app.use('/api', router)` |
| **Middleware** | `app.use(cors())`, `app.use(express.json())` |
| **Validation** | express-validator, Joi (`joi`), celebrate |
| **ORM** | Sequelize, TypeORM, Prisma, Mongoose (MongoDB) |

### Django (Python)

| Aspect | Detection Signals |
|--------|------------------|
| **Package** | `django` or `Django` in requirements.txt / Pipfile |
| **Files** | `urls.py`, `views.py`, `models.py`, `admin.py`, `manage.py` |
| **Imports** | `from django.` pattern |
| **Config** | `settings.py` with `INSTALLED_APPS` |
| **Route Pattern** | `urlpatterns = [path('api/vehicles/', views.VehicleList.as_view())]` |
| **Validation** | Django Forms, DRF serializers (`rest_framework`) |
| **ORM** | Django ORM (built-in): `models.Model` subclasses |
| **REST** | Django REST Framework (`djangorestframework` in requirements) |

### Flask (Python)

| Aspect | Detection Signals |
|--------|------------------|
| **Package** | `flask` or `Flask` in requirements.txt |
| **Files** | `app.py` or `__init__.py` with Flask app factory |
| **Imports** | `from flask import Flask` |
| **Route Pattern** | `@app.route('/path', methods=['GET', 'POST'])` |
| **Validation** | Flask-WTF, Marshmallow, Pydantic |
| **ORM** | SQLAlchemy (`flask-sqlalchemy`), Peewee |

### Spring Boot (Java)

| Aspect | Detection Signals |
|--------|------------------|
| **Package** | `spring-boot-starter-web` in pom.xml or build.gradle |
| **Files** | `*Controller.java`, `*Service.java`, `*Repository.java` |
| **Imports** | `import org.springframework.` |
| **Config** | `application.properties`, `application.yml` |
| **Route Pattern** | `@RequestMapping("/api")`, `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping` |
| **Validation** | Bean Validation (`@Valid`, `@NotNull`, `@Size`), `javax.validation` / `jakarta.validation` |
| **ORM** | Spring Data JPA, Hibernate |
| **Security** | Spring Security (`spring-boot-starter-security`) |

### FastAPI (Python)

| Aspect | Detection Signals |
|--------|------------------|
| **Package** | `fastapi` in requirements.txt |
| **Files** | `main.py` with FastAPI app, `routers/*.py` |
| **Imports** | `from fastapi import FastAPI` |
| **Route Pattern** | `@app.get('/path')`, `@app.post('/path')`, `@router.get()` |
| **Validation** | Pydantic models (built-in): `class Item(BaseModel):` |
| **ORM** | SQLAlchemy, Tortoise ORM, SQLModel |
| **Docs** | Auto-generated OpenAPI at `/docs` and `/redoc` |

### Laravel (PHP)

| Aspect | Detection Signals |
|--------|------------------|
| **Package** | `laravel/framework` in composer.json |
| **Files** | `artisan`, `routes/web.php`, `routes/api.php` |
| **Config** | `config/*.php`, `.env` |
| **Route Pattern** | `Route::get('/path', [Controller::class, 'method'])` in routes files |
| **Validation** | Form Request classes (`app/Http/Requests/`), `$request->validate([...])` |
| **ORM** | Eloquent (built-in): `extends Model` |

### Rails (Ruby)

| Aspect | Detection Signals |
|--------|------------------|
| **Package** | `rails` in Gemfile |
| **Files** | `config/routes.rb`, `app/controllers/`, `app/models/` |
| **Config** | `config/application.rb`, `config/database.yml` |
| **Route Pattern** | `resources :vehicles`, `get '/path', to: 'controller#action'` |
| **Validation** | ActiveModel validations: `validates :name, presence: true, length: { maximum: 50 }` |
| **ORM** | ActiveRecord (built-in) |

### ASP.NET (C#)

| Aspect | Detection Signals |
|--------|------------------|
| **Package** | `Microsoft.AspNetCore` in `*.csproj` |
| **Files** | `Controllers/*.cs`, `Program.cs`, `Startup.cs` |
| **Config** | `appsettings.json`, `launchSettings.json` |
| **Route Pattern** | `[Route("api/[controller]")]`, `[HttpGet]`, `[HttpPost]` |
| **Validation** | Data Annotations (`[Required]`, `[StringLength]`), FluentValidation |
| **ORM** | Entity Framework Core (`Microsoft.EntityFrameworkCore`) |

---

## Mobile Frameworks

### React Native

| Aspect | Detection Signals |
|--------|------------------|
| **Package** | `react-native` in package.json |
| **Files** | `App.tsx`, `android/`, `ios/` directories |
| **Config** | `metro.config.js`, `app.json` / `app.config.js` (Expo) |
| **Navigation** | React Navigation (`@react-navigation/native`) |

### Flutter

| Aspect | Detection Signals |
|--------|------------------|
| **Package** | `pubspec.yaml` with `flutter` SDK dependency |
| **Files** | `lib/main.dart`, `*.dart` files |
| **Config** | `pubspec.yaml`, `analysis_options.yaml` |
| **Route Pattern** | `MaterialPageRoute`, `GoRouter` |

---

## Cross-Cutting Detection

### Package Managers

| Manager | Detection Signal |
|---------|-----------------|
| npm | `package-lock.json` |
| yarn | `yarn.lock` |
| pnpm | `pnpm-lock.yaml` |
| bun | `bun.lockb` |
| pip | `requirements.txt` |
| pipenv | `Pipfile.lock` |
| poetry | `poetry.lock` |
| maven | `pom.xml` |
| gradle | `build.gradle` / `build.gradle.kts` |
| composer | `composer.lock` |
| bundler | `Gemfile.lock` |
| cargo | `Cargo.lock` |
| nuget | `packages.config` / `*.csproj` with `<PackageReference>` |

### Test Frameworks

| Framework | Detection Signal |
|-----------|-----------------|
| Jest | `jest` in package.json, `jest.config.*` |
| Vitest | `vitest` in package.json, `vitest.config.*` |
| Mocha | `mocha` in package.json |
| Cypress | `cypress` in package.json, `cypress.config.*` |
| Playwright | `@playwright/test` in package.json, `playwright.config.*` |
| pytest | `pytest` in requirements.txt, `pytest.ini` / `pyproject.toml [tool.pytest]` |
| JUnit | `junit` in pom.xml / build.gradle |
| RSpec | `rspec` in Gemfile |
| xUnit | `xunit` in *.csproj |

### Monorepo Tools

| Tool | Detection Signal |
|------|-----------------|
| npm workspaces | `"workspaces"` in root package.json |
| Lerna | `lerna.json` |
| Nx | `nx.json` |
| Turborepo | `turbo.json` |
| pnpm workspaces | `pnpm-workspace.yaml` |
| Yarn workspaces | `"workspaces"` in package.json + yarn.lock |

### API Styles

| Style | Detection Signal |
|-------|-----------------|
| REST | HTTP method decorators/functions (default for most frameworks) |
| GraphQL | `graphql`, `apollo-server`, `@nestjs/graphql`, `graphene` |
| tRPC | `@trpc/server` in package.json |
| gRPC | `.proto` files, `grpc` dependencies |
| WebSocket | `socket.io`, `ws`, `channels` (Django) |

### CSS / Styling

| Framework | Detection Signal |
|-----------|-----------------|
| Tailwind CSS | `tailwindcss` in package.json, `tailwind.config.*` |
| Bootstrap | `bootstrap` in package.json |
| Material UI | `@mui/material` in package.json |
| Styled Components | `styled-components` in package.json |
| CSS Modules | `*.module.css` / `*.module.scss` files |
| Sass/SCSS | `sass` in package.json, `*.scss` files |
