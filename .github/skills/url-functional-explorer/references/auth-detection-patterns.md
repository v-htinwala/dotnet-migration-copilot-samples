# Auth Detection Patterns — url-functional-explorer

Heuristics for detecting authentication requirements in web applications
using playwright-cli snapshot analysis and storage inspection commands.

---

## Login Page Detection

**Detection approach**: Take a snapshot and check the current URL:
```bash
playwright-cli -s=<session-name> snapshot
playwright-cli -s=<session-name> eval "window.location.href"
```

### High-Confidence Indicators (any one is sufficient)

| Indicator | Snapshot Detection Pattern |
|---|---|
| Password input | `textbox` role node with name containing "password" |
| Sign-in button | `button` role node with name matching: "Sign In", "Log In", "Login", "Sign Up" |
| Login URL | URL (from `eval`) containing: `/login`, `/signin`, `/auth`, `/sso` |
| Login form | `form` role with both email/username `textbox` and password `textbox` children |
| OAuth buttons | `button` role with name: "Continue with Google", "Sign in with GitHub" |

### Medium-Confidence Indicators (need 2+ to confirm)

| Indicator | Pattern |
|---|---|
| Login heading | `<h1>` or `<h2>` with text: "Welcome", "Sign In", "Account" |
| Remember me | Checkbox with label: "Remember me", "Keep me signed in" |
| Forgot password | Link with text: "Forgot password?", "Reset password" |
| Registration link | Link with text: "Create account", "Register", "Sign up" |
| Auth redirect | HTTP 302/307 redirect to a `/login` URL |

### False Positive Guards

Don't trigger auth checkpoint for:
- Public marketing landing pages with a "Sign In" link in the header
- Cookie consent dialogs
- Newsletter signup forms
- Contact forms with email fields

**Disambiguation**: If a page has a password field BUT also has significant
non-auth content (blog posts, product listings, documentation), it's likely
a public page with a login section — NOT a login-required page.

---

## Post-Authentication Verification

After user reports login is complete, verify using playwright-cli:

```bash
# Check current URL
playwright-cli -s=<session-name> eval "window.location.href"
# Take fresh snapshot to inspect page content
playwright-cli -s=<session-name> snapshot
```

### Positive Signals (auth succeeded)

| Signal | playwright-cli Check |
|---|---|
| URL changed | `eval "window.location.href"` — no longer on `/login` or `/auth` path |
| Dashboard visible | Snapshot shows `heading` role with authenticated area names |
| User menu | Snapshot shows `link` or `button` with user name, "My Account", or avatar |
| Navigation loaded | Snapshot shows `navigation` role with app-specific menu items |
| No password field | No `textbox` node with password-like name in snapshot |

### Negative Signals (auth may have failed)

| Signal | playwright-cli Check |
|---|---|
| Still on login page | `eval "window.location.href"` still contains `/login` |
| Error message | Snapshot contains text matching "Invalid", "Incorrect", "Failed" |
| Password field visible | Snapshot still has password `textbox` node |

---

## Session Handling

### Cookie-Based Auth

After successful auth, the playwright-cli named session retains cookies
automatically. Inspect stored cookies with:
```bash
playwright-cli -s=<session-name> cookie-list
```

### Token-Based Auth (JWT)

Some SPAs store JWT in localStorage/sessionStorage. The named session
preserves these within the session. Inspect stored tokens with:
```bash
playwright-cli -s=<session-name> localstorage-list
playwright-cli -s=<session-name> sessionstorage-list
```

Look for common auth token keys:
```bash
playwright-cli -s=<session-name> localstorage-get token
playwright-cli -s=<session-name> localstorage-get access_token
playwright-cli -s=<session-name> cookie-get session
```

If the token expires mid-exploration (detected by 401/403 responses via
`playwright-cli -s=<session-name> network`):

1. Detect 401/403 responses during navigation
2. Notify user: "Session may have expired. Please re-authenticate."
3. Wait for user confirmation
4. Resume exploration

### Multi-Factor Auth (MFA)

The auth checkpoint naturally handles MFA because:
- User completes all auth steps manually in the headed browser (`--headed`)
- Skill only resumes after user confirms completion
- All session tokens/cookies are captured automatically in the named session

---

## Common Login Form Structures

### Standard Form

```html
<form action="/api/auth/login" method="POST">
  <input type="email" name="email" placeholder="Email">
  <input type="password" name="password" placeholder="Password">
  <button type="submit">Sign In</button>
</form>
```

### SPA Login (no form action)

```html
<div class="login-container">
  <input type="text" placeholder="Username or Email">
  <input type="password" placeholder="Password">
  <button onclick="handleLogin()">Log In</button>
</div>
```

### OAuth / SSO

```html
<div class="auth-options">
  <button class="oauth-google">Continue with Google</button>
  <button class="oauth-github">Sign in with GitHub</button>
  <hr>
  <a href="/auth/login">Sign in with email</a>
</div>
```

### Enterprise SSO Redirect

The page immediately redirects to:
- `login.microsoftonline.com` (Azure AD)
- `auth0.com` domain
- `okta.com` domain
- Custom SAML/OIDC provider

In this case, the auth checkpoint still works — the user completes SSO in the
browser and confirms when redirected back to the app.
