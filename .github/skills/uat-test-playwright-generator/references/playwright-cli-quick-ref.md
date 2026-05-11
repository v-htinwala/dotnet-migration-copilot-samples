# Playwright CLI Quick Reference

Essential Playwright CLI commands for UAT test generation.

> For full documentation, run `playwright-cli --help` or visit [Playwright CLI GitHub](https://github.com/microsoft/playwright-cli)

---

## Installation

```bash
# Global installation (recommended for skills)
npm install -g @playwright/cli

# Install browser
playwright-cli install-browser

# Install skills (optional)
playwright-cli install --skills
```

### Environment Configuration

Set `PLAYWRIGHT_CLI_CMD` to customize the command prefix:

```bash
# Default
PLAYWRIGHT_CLI_CMD=playwright-cli

# Using npx
PLAYWRIGHT_CLI_CMD="npx @playwright/cli"
```

---

## Core Commands

### Browser & Navigation

```bash
playwright-cli open [url]               # Open browser, optionally navigate to URL
playwright-cli open <url> --headed      # Open with visible browser window
playwright-cli goto <url>               # Navigate to URL in current page
playwright-cli close                    # Close current page
playwright-cli reload                   # Reload current page
playwright-cli go-back                  # Navigate back
playwright-cli go-forward               # Navigate forward
```

### Page Inspection

```bash
playwright-cli snapshot                 # Capture page structure (element refs)
playwright-cli snapshot --filename=f    # Save snapshot to specific file
playwright-cli screenshot               # Capture screenshot of current page
playwright-cli screenshot --filename=f  # Save screenshot to specific file
playwright-cli screenshot <ref>         # Screenshot specific element
```

### Element Interaction

```bash
playwright-cli click <ref>              # Click an element
playwright-cli click <ref> right        # Right-click
playwright-cli dblclick <ref>           # Double-click
playwright-cli fill <ref> <text>        # Fill text into input field
playwright-cli type <text>              # Type text into focused element
playwright-cli select <ref> <value>     # Select dropdown option
playwright-cli check <ref>              # Check checkbox/radio
playwright-cli uncheck <ref>            # Uncheck checkbox
playwright-cli hover <ref>              # Hover over element
playwright-cli drag <start> <end>       # Drag and drop
playwright-cli upload <file>            # Upload file
```

### Keyboard

```bash
playwright-cli press <key>              # Press key (Enter, Tab, Escape, etc.)
playwright-cli keydown <key>            # Hold key down
playwright-cli keyup <key>              # Release key
```

### Dialogs

```bash
playwright-cli dialog-accept [prompt]   # Accept dialog (with optional prompt text)
playwright-cli dialog-dismiss           # Dismiss/cancel dialog
```

### Viewport

```bash
playwright-cli resize <width> <height>  # Resize browser window

# Common viewport sizes:
playwright-cli resize 375 812           # Mobile (iPhone X)
playwright-cli resize 768 1024          # Tablet (iPad)
playwright-cli resize 1920 1080         # Desktop (Full HD)
playwright-cli resize 1366 768          # Laptop
```

---

## Multi-Tab Support

```bash
playwright-cli tab-list                 # List all open tabs
playwright-cli tab-new [url]            # Open new tab
playwright-cli tab-select <index>       # Switch to tab by index
playwright-cli tab-close [index]        # Close tab (default: current)
```

---

## Session Management

```bash
playwright-cli list                     # List all browser sessions
playwright-cli -s=<name> <cmd>          # Run command in named session
playwright-cli close-all                # Close all browser sessions
playwright-cli kill-all                 # Force kill all browser processes
playwright-cli delete-data              # Delete user data for default session
```

### Environment Variable

```bash
# Set session name via environment
PLAYWRIGHT_CLI_SESSION=my-session playwright-cli open https://example.com
```

---

## Storage State

```bash
# Cookies
playwright-cli cookie-list              # List all cookies
playwright-cli cookie-get <name>        # Get specific cookie
playwright-cli cookie-set <name> <val>  # Set cookie
playwright-cli cookie-delete <name>     # Delete cookie
playwright-cli cookie-clear             # Clear all cookies

# LocalStorage
playwright-cli localstorage-list        # List localStorage entries
playwright-cli localstorage-get <key>   # Get localStorage value
playwright-cli localstorage-set <k> <v> # Set localStorage value
playwright-cli localstorage-delete <k>  # Delete localStorage entry
playwright-cli localstorage-clear       # Clear all localStorage

# Session Storage
playwright-cli sessionstorage-list      # List sessionStorage entries
playwright-cli sessionstorage-get <k>   # Get sessionStorage value
playwright-cli sessionstorage-set <k> <v> # Set sessionStorage value
playwright-cli sessionstorage-clear     # Clear all sessionStorage

# Persistent State
playwright-cli state-save [filename]    # Save storage state to file
playwright-cli state-load <filename>    # Load storage state from file
```

---

## Advanced Features

### Network Mocking

```bash
playwright-cli route <pattern> [opts]   # Mock network requests
playwright-cli route-list               # List active routes
playwright-cli unroute [pattern]        # Remove route(s)
```

### DevTools

```bash
playwright-cli console [min-level]      # List console messages
playwright-cli network                  # List network requests since page load
playwright-cli run-code <code>          # Run Playwright code snippet
```

### Tracing & Recording

```bash
playwright-cli tracing-start            # Start trace recording
playwright-cli tracing-stop             # Stop and save trace
playwright-cli video-start              # Start video recording
playwright-cli video-stop [filename]    # Stop video recording
```

### PDF Export

```bash
playwright-cli pdf                      # Save page as PDF
playwright-cli pdf --filename=page.pdf  # Save with specific filename
```

---

## Element References

When you run `playwright-cli snapshot`, each interactive element gets a reference like `e5`, `e15`, `e27`.

Use these refs in subsequent commands:

```bash
# 1. Get element refs
playwright-cli snapshot
# Output shows: e5 = email input, e7 = password input, e9 = submit button

# 2. Use refs to interact
playwright-cli fill e5 "user@example.com"
playwright-cli fill e7 "password123"
playwright-cli click e9
```

---

## Common Patterns

### Login Flow

```bash
playwright-cli open https://app.example.com/login --headed
playwright-cli snapshot
playwright-cli fill e5 "testuser@example.com"
playwright-cli fill e7 "ValidPass123!"
playwright-cli click e9
playwright-cli snapshot --filename=snapshots/after-login.yaml
playwright-cli screenshot --filename=screenshots/dashboard.png
```

### Form Testing (Negative)

```bash
# Try empty submit
playwright-cli open https://app.example.com/form
playwright-cli click e20  # Submit button
playwright-cli snapshot
playwright-cli screenshot --filename=screenshots/validation-errors.png

# Try invalid data
playwright-cli fill e5 "not-an-email"
playwright-cli click e20
playwright-cli snapshot
```

### Responsive Testing

```bash
playwright-cli open https://app.example.com --headed
playwright-cli resize 375 812  # Mobile
playwright-cli screenshot --filename=screenshots/mobile-view.png
playwright-cli resize 768 1024  # Tablet
playwright-cli screenshot --filename=screenshots/tablet-view.png
playwright-cli resize 1920 1080  # Desktop
playwright-cli screenshot --filename=screenshots/desktop-view.png
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Element not found | Run `playwright-cli snapshot` to refresh element refs |
| Session timeout | Use `playwright-cli list` to check active sessions |
| Screenshot fails | Ensure directory exists; use `--filename` with full path |
| Dialog blocking | Use `playwright-cli dialog-accept` or `dialog-dismiss` |
| Page not loading | Verify URL is accessible; check network connectivity |
| Dynamic content | Wait for content to load; re-snapshot after interactions |
| Stale refs | Always re-snapshot after page changes |
