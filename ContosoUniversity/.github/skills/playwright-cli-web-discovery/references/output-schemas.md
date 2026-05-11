# Output Schemas Reference

JSON schema definitions for all output files produced by the
playwright-cli-web-discovery skill.

## site-map.json

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SiteMap",
  "description": "Route graph with pages, titles, hierarchy, and navigation links",
  "type": "object",
  "required": ["base_url", "discovered_at", "routes", "navigation_graph"],
  "properties": {
    "base_url": {
      "type": "string",
      "description": "The base URL of the explored web application"
    },
    "discovered_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of when discovery was performed"
    },
    "exploration_depth": {
      "type": "integer",
      "description": "Maximum link traversal depth used"
    },
    "routes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["url", "title", "element_count"],
        "properties": {
          "url": {
            "type": "string",
            "description": "Full URL of the route"
          },
          "path": {
            "type": "string",
            "description": "URL path component (e.g., /products)"
          },
          "title": {
            "type": "string",
            "description": "Page title from document node"
          },
          "element_count": {
            "type": "integer",
            "description": "Total number of elements in the snapshot"
          },
          "interactive_element_count": {
            "type": "integer",
            "description": "Number of interactive elements (buttons, inputs, links)"
          },
          "depth": {
            "type": "integer",
            "description": "Navigation depth from the landing page"
          },
          "parent_url": {
            "type": ["string", "null"],
            "description": "URL of the page where the link to this route was found"
          },
          "screenshot_path": {
            "type": "string",
            "description": "Relative path to the page screenshot"
          },
          "landmarks": {
            "type": "array",
            "items": { "type": "string" },
            "description": "ARIA landmark roles found on the page (navigation, main, etc.)"
          },
          "is_protected": {
            "type": "boolean",
            "description": "Whether this route required authentication"
          },
          "redirect_target": {
            "type": ["string", "null"],
            "description": "URL this route redirected to, if any"
          }
        }
      }
    },
    "navigation_graph": {
      "type": "object",
      "description": "Adjacency list representation of the route graph",
      "additionalProperties": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "target_url": { "type": "string" },
            "link_text": { "type": "string" },
            "ref": { "type": "integer" }
          }
        }
      }
    },
    "stats": {
      "type": "object",
      "properties": {
        "total_routes": { "type": "integer" },
        "total_links": { "type": "integer" },
        "protected_routes": { "type": "integer" },
        "failed_routes": { "type": "integer" }
      }
    }
  }
}
```

## interaction-inventory.json

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "InteractionInventory",
  "description": "Per-page interactive element map with refs and classifications",
  "type": "object",
  "required": ["base_url", "discovered_at", "pages"],
  "properties": {
    "base_url": {
      "type": "string"
    },
    "discovered_at": {
      "type": "string",
      "format": "date-time"
    },
    "pages": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["url", "elements"],
        "properties": {
          "url": {
            "type": "string",
            "description": "Page URL"
          },
          "elements": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["ref", "role", "name", "type"],
              "properties": {
                "ref": {
                  "type": "integer",
                  "description": "playwright-cli element reference"
                },
                "role": {
                  "type": "string",
                  "description": "ARIA role from snapshot"
                },
                "name": {
                  "type": "string",
                  "description": "Accessible name from snapshot"
                },
                "type": {
                  "type": "string",
                  "enum": [
                    "navigation",
                    "action-submit",
                    "action-toggle",
                    "action-trigger",
                    "form-input",
                    "form-select",
                    "form-choice",
                    "tab-navigation",
                    "modal-trigger",
                    "menu-navigation"
                  ],
                  "description": "Classified interaction type"
                },
                "attributes": {
                  "type": "object",
                  "description": "Relevant element attributes",
                  "properties": {
                    "placeholder": { "type": "string" },
                    "required": { "type": "boolean" },
                    "disabled": { "type": "boolean" },
                    "checked": { "type": "boolean" },
                    "value": { "type": "string" }
                  }
                }
              }
            }
          },
          "forms": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "form_id": { "type": "string" },
                "action": { "type": "string" },
                "method": { "type": "string" },
                "fields": {
                  "type": "array",
                  "items": { "type": "integer" },
                  "description": "Element refs belonging to this form"
                },
                "submit_ref": {
                  "type": ["integer", "null"],
                  "description": "Ref of the submit button"
                },
                "required_field_count": { "type": "integer" },
                "total_field_count": { "type": "integer" }
              }
            }
          },
          "stats": {
            "type": "object",
            "properties": {
              "total_interactive": { "type": "integer" },
              "navigation_count": { "type": "integer" },
              "action_count": { "type": "integer" },
              "form_input_count": { "type": "integer" },
              "form_count": { "type": "integer" }
            }
          }
        }
      }
    }
  }
}
```

## api-surface.json

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "APISurface",
  "description": "Observed API endpoints with methods, URL patterns, and response shapes",
  "type": "object",
  "required": ["base_url", "discovered_at", "endpoints"],
  "properties": {
    "base_url": {
      "type": "string"
    },
    "discovered_at": {
      "type": "string",
      "format": "date-time"
    },
    "endpoints": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["method", "url_pattern", "classification"],
        "properties": {
          "method": {
            "type": "string",
            "enum": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
          },
          "url_pattern": {
            "type": "string",
            "description": "URL with path params abstracted (e.g., /api/users/:id)"
          },
          "url_examples": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Actual URLs observed"
          },
          "status_codes": {
            "type": "array",
            "items": { "type": "integer" },
            "description": "HTTP status codes observed"
          },
          "content_type": {
            "type": "string",
            "description": "Response content type"
          },
          "classification": {
            "type": "string",
            "enum": ["data-fetch", "mutation", "auth", "static", "other"]
          },
          "triggered_by": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "page_url": { "type": "string" },
                "action": { "type": "string" }
              }
            }
          },
          "request_body_shape": {
            "type": ["object", "null"],
            "description": "Top-level keys of request body (no values)"
          },
          "response_body_shape": {
            "type": ["object", "null"],
            "description": "Top-level keys of response body (no values)"
          },
          "observation_count": {
            "type": "integer",
            "description": "Number of times this endpoint was observed"
          }
        }
      }
    },
    "stats": {
      "type": "object",
      "properties": {
        "total_endpoints": { "type": "integer" },
        "data_fetch_count": { "type": "integer" },
        "mutation_count": { "type": "integer" },
        "auth_count": { "type": "integer" }
      }
    }
  }
}
```

## auth-flows.json

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AuthFlows",
  "description": "Detected authentication patterns and protected routes",
  "type": "object",
  "required": ["base_url", "discovered_at", "auth_detected", "auth_type"],
  "properties": {
    "base_url": {
      "type": "string"
    },
    "discovered_at": {
      "type": "string",
      "format": "date-time"
    },
    "auth_detected": {
      "type": "boolean",
      "description": "Whether any authentication mechanism was detected"
    },
    "auth_type": {
      "type": "string",
      "enum": ["form-based", "oauth", "token-based", "session-based", "none"],
      "description": "Primary authentication mechanism detected"
    },
    "login_page": {
      "type": ["object", "null"],
      "properties": {
        "url": { "type": "string" },
        "form_fields": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "ref": { "type": "integer" },
              "name": { "type": "string" },
              "type": { "type": "string" }
            }
          }
        },
        "submit_ref": { "type": "integer" }
      }
    },
    "protected_routes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "url": {
            "type": "string",
            "description": "URL of the protected route"
          },
          "redirect_to": {
            "type": "string",
            "description": "URL the user is redirected to when not authenticated"
          }
        }
      }
    },
    "storage_tokens": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "storage": {
            "type": "string",
            "enum": ["localStorage", "sessionStorage", "cookie"]
          },
          "key": { "type": "string" },
          "pattern": {
            "type": "string",
            "description": "Token pattern detected (jwt, opaque, session-id)"
          }
        }
      }
    },
    "oauth_providers": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "provider": { "type": "string" },
          "redirect_url": { "type": "string" },
          "callback_url": { "type": "string" }
        }
      }
    },
    "auth_api_endpoints": {
      "type": "array",
      "items": { "type": "string" },
      "description": "API endpoints related to authentication"
    }
  }
}
```
