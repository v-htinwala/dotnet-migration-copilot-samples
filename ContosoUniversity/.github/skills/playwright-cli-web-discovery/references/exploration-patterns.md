# Exploration Patterns Reference

## playwright-cli Full Command Reference

Based on [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli)
(`@playwright/cli` on npm). Install via `npm install -g @playwright/cli@latest`.

### Core Commands

```bash
playwright-cli open [url]               # open browser, optionally navigate to url
playwright-cli goto <url>               # navigate to a url
playwright-cli close                    # close the page
playwright-cli type <text>              # type text into editable element
playwright-cli click <ref> [button]     # click element by ref
playwright-cli dblclick <ref> [button]  # double click element
playwright-cli fill <ref> <text>        # fill text into editable element
playwright-cli drag <startRef> <endRef> # drag and drop between two elements
playwright-cli hover <ref>              # hover over element
playwright-cli select <ref> <val>       # select an option in a dropdown
playwright-cli upload <file>            # upload file(s)
playwright-cli check <ref>              # check a checkbox or radio button
playwright-cli uncheck <ref>            # uncheck a checkbox or radio button
playwright-cli snapshot                 # capture page snapshot (accessibility tree)
playwright-cli snapshot --filename=f    # save snapshot to specific file
playwright-cli eval <func> [ref]        # evaluate javascript expression
playwright-cli dialog-accept [prompt]   # accept a dialog
playwright-cli dialog-dismiss           # dismiss a dialog
playwright-cli resize <w> <h>           # resize the browser window
```

### Navigation

```bash
playwright-cli go-back                  # go back to the previous page
playwright-cli go-forward               # go forward to the next page
playwright-cli reload                   # reload the current page
```

### Keyboard

```bash
playwright-cli press <key>              # press a key: `a`, `arrowleft`, `Enter`
playwright-cli keydown <key>            # press a key down
playwright-cli keyup <key>              # press a key up
```

### Mouse

```bash
playwright-cli mousemove <x> <y>        # move mouse to position
playwright-cli mousedown [button]       # press mouse down
playwright-cli mouseup [button]         # press mouse up
playwright-cli mousewheel <dx> <dy>     # scroll mouse wheel
```

### Save As

```bash
playwright-cli screenshot [ref]         # screenshot of page or element
playwright-cli screenshot --filename=f  # save screenshot with specific filename
playwright-cli pdf                      # save page as pdf
playwright-cli pdf --filename=page.pdf  # save pdf with specific filename
```

### Tabs

```bash
playwright-cli tab-list                 # list all tabs
playwright-cli tab-new [url]            # create a new tab
playwright-cli tab-close [index]        # close a browser tab
playwright-cli tab-select <index>       # select a browser tab
```

### Storage (State)

```bash
playwright-cli state-save [filename]    # save storage state
playwright-cli state-load <filename>    # load storage state
```

### Cookies

```bash
playwright-cli cookie-list [--domain]   # list cookies
playwright-cli cookie-get <name>        # get a cookie
playwright-cli cookie-set <name> <val>  # set a cookie
playwright-cli cookie-delete <name>     # delete a cookie
playwright-cli cookie-clear             # clear all cookies
```

### LocalStorage

```bash
playwright-cli localstorage-list        # list localStorage entries
playwright-cli localstorage-get <key>   # get localStorage value
playwright-cli localstorage-set <k> <v> # set localStorage value
playwright-cli localstorage-delete <k>  # delete localStorage entry
playwright-cli localstorage-clear       # clear all localStorage
```

### SessionStorage

```bash
playwright-cli sessionstorage-list      # list sessionStorage entries
playwright-cli sessionstorage-get <k>   # get sessionStorage value
playwright-cli sessionstorage-set <k> <v> # set sessionStorage value
playwright-cli sessionstorage-delete <k>  # delete sessionStorage entry
playwright-cli sessionstorage-clear     # clear all sessionStorage
```

### Network

```bash
playwright-cli route <pattern> [opts]   # mock network requests
playwright-cli route-list               # list active routes
playwright-cli unroute [pattern]        # remove route(s)
playwright-cli network                  # list all network requests since page load
```

### DevTools

```bash
playwright-cli console [min-level]      # list console messages
playwright-cli run-code <code>          # run playwright code snippet
playwright-cli tracing-start            # start trace recording
playwright-cli tracing-stop             # stop trace recording
playwright-cli video-start              # start video recording
playwright-cli video-stop [filename]    # stop video recording
```

### Sessions

```bash
playwright-cli -s=name <cmd>            # run command in named session
playwright-cli -s=name close            # stop a named browser
playwright-cli -s=name delete-data      # delete user data for named browser
playwright-cli list                     # list all sessions
playwright-cli close-all                # close all browsers
playwright-cli kill-all                 # forcefully kill all browser processes
playwright-cli show                     # open visual dashboard for all sessions
```

### Open Parameters

```bash
playwright-cli open --browser=chrome    # use specific browser
playwright-cli open --persistent        # use persistent profile
playwright-cli open --headed            # show the browser window (headless by default)
playwright-cli open --config=file.json  # use config file
playwright-cli delete-data              # delete user data for default session
```

---

## playwright-cli Command Patterns for Discovery

### Session Management

```bash
# Start a named session
playwright-cli -s=my-session open https://example.com

# All subsequent commands use the same session
playwright-cli -s=my-session snapshot
playwright-cli -s=my-session screenshot --filename=./screenshot.png
playwright-cli -s=my-session click 42
playwright-cli -s=my-session goto https://example.com/other-page

# Close the session when done
playwright-cli -s=my-session close
```

### Snapshot YAML Format

The `snapshot` command returns an accessibility tree in YAML format:

```yaml
- role: document
  name: "Page Title"
  children:
    - role: navigation
      name: "Main Navigation"
      children:
        - role: link
          name: "Home"
          ref: 1
          url: "/"
        - role: link
          name: "Products"
          ref: 2
          url: "/products"
    - role: main
      children:
        - role: heading
          name: "Welcome"
          level: 1
        - role: button
          name: "Get Started"
          ref: 3
        - role: textbox
          name: "Search"
          ref: 4
```

**Key fields:**
- `role`: ARIA role of the element
- `name`: Accessible name (visible text, aria-label, etc.)
- `ref`: Integer reference used for `click`, `fill`, `hover`, etc.
- `url`: href attribute for link elements
- `children`: Nested child elements
- `level`: Heading level (1-6) for heading role
- `checked`: Boolean for checkbox/radio elements
- `disabled`: Boolean for disabled elements
- `required`: Boolean for required form fields

### Element Interaction Commands

```bash
# Click an element by ref
playwright-cli -s=my-session click 3

# Fill a text input by ref
playwright-cli -s=my-session fill 4 "search query"

# Select an option in a dropdown
playwright-cli -s=my-session select 5 "option1"

# Hover over an element (to reveal dropdowns, tooltips)
playwright-cli -s=my-session hover 6

# Press keyboard keys
playwright-cli -s=my-session press Enter
playwright-cli -s=my-session press Escape
```

### Network Monitoring

```bash
# Capture network requests during the current page load
playwright-cli -s=my-session network

# Example output:
# GET  https://example.com/api/products  200  application/json
# GET  https://example.com/api/cart       200  application/json
# POST https://example.com/api/analytics  204  text/plain
```

### JavaScript Evaluation

```bash
# Get the current URL
playwright-cli -s=my-session eval "window.location.href"

# Get localStorage keys
playwright-cli -s=my-session localstorage-list

# Get cookies
playwright-cli -s=my-session cookie-list

# Get sessionStorage keys
playwright-cli -s=my-session sessionstorage-list

# Check for specific auth tokens
playwright-cli -s=my-session localstorage-get token
```

## Strategies for SPA vs MPA Exploration

### Single-Page Applications (SPAs)

SPAs use client-side routing — the page doesn't fully reload on navigation.

**Detection signals:**
- URL changes use hash (`#/route`) or `history.pushState`
- The `<html>` element stays the same across "navigations"
- Network requests during navigation are XHR/fetch, not document requests

**Exploration strategy:**
1. After clicking a link, wait for URL change rather than page load:
   ```bash
   playwright-cli -s=my-session click 2
   # Wait briefly for SPA to render
   playwright-cli -s=my-session snapshot
   ```
2. Compare successive snapshots to detect content changes
3. Track URL changes via `eval "window.location.href"` after each click
4. Handle hash-based routing: normalize URLs by treating `#/route` as paths
5. Watch for lazy-loaded content that appears after scrolling

### Multi-Page Applications (MPAs)

MPAs perform full page reloads on navigation.

**Detection signals:**
- Clicking links triggers full page loads
- Each page has a unique HTML document
- Network shows document-type requests on navigation

**Exploration strategy:**
1. Standard navigation with `click` or `navigate` commands
2. Wait for full page load before capturing snapshot
3. Each page is independent — capture complete state per page

### Hybrid Applications

Some apps mix SPA and MPA patterns (e.g., Next.js with client + server routes).

**Strategy:**
- Treat each navigation as potentially either SPA or MPA
- Always wait for both network idle and content stability
- Use URL as the primary route identifier

## Handling Dynamic Content

### Infinite Scroll
```bash
# Scroll to bottom to trigger lazy loading
playwright-cli -s=my-session eval "window.scrollTo(0, document.body.scrollHeight)"
# Wait for new content
playwright-cli -s=my-session snapshot
```

### Lazy Loading
- After initial snapshot, scroll the page incrementally
- Re-snapshot after each scroll to detect new elements
- Stop when no new elements appear

### Dynamic Content (Modals, Dropdowns, Accordions)
- Click trigger elements to reveal hidden content
- Snapshot after each interaction to capture expanded state
- Track which elements are initially hidden vs visible

## Session & Cookie Management for Authenticated Exploration

### Pre-authenticated Exploration

If auth credentials are provided:

1. Navigate to the login page
2. Fill credentials:
   ```bash
   playwright-cli -s=my-session fill <email-ref> "user@example.com"
   playwright-cli -s=my-session fill <password-ref> "password123"
   playwright-cli -s=my-session click <submit-ref>
   ```
3. Wait for redirect to authenticated page
4. Proceed with exploration — session cookies are maintained within the named session

### Token-Based Auth

If a bearer token is provided:
```bash
playwright-cli -s=my-session localstorage-set token "<token-value>"
playwright-cli -s=my-session goto <url>  # Reload to apply token
```

## Rate Limiting and Timeout Handling

### Rate Limiting
- Add 500ms delay between navigation actions to avoid overwhelming the server
- If receiving 429 (Too Many Requests), increase delay to 2000ms
- For discovery purposes, speed is less important than completeness

### Timeout Handling
- Default page load timeout: 30000ms (30 seconds)
- If a page times out, log it and move to the next route
- Retry timed-out pages once at the end of discovery
- For slow-loading pages (heavy JS bundles), consider increasing timeout

### Error Recovery
- If a navigation fails, try refreshing the page first
- If the session becomes unresponsive, close and reopen it
- Always maintain a fallback list of undiscovered routes for retry
