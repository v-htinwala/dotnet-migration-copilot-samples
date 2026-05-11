# Test Data Patterns — functional-test-generator

Auto-generation patterns for test data across all data types.

---

## Standard Patterns by Data Type

### String Fields

| Scenario | Test Value | Category |
|---|---|---|
| Valid basic | `"Test Value"` | Positive |
| Valid with spaces | `"Test Value With Spaces"` | Positive |
| Empty string | `""` | Negative (if required) / Boundary |
| Whitespace only | `"   "` | Negative |
| Single character | `"A"` | Boundary (min) |
| At max length | `"A" × max_length` | Boundary (max) |
| Over max length | `"A" × (max_length + 1)` | Boundary (max+1) |
| Unicode characters | `"Tëst Vàlüé 日本語"` | Boundary |
| XSS injection | `"<script>alert('XSS')</script>"` | Security |
| SQL injection | `"' OR 1=1 --"` | Security |
| HTML entities | `"&lt;div&gt;test&lt;/div&gt;"` | Security |
| Very long string | `"A" × 10000` | Boundary |
| Special characters | `"!@#$%^&*()"` | Negative / Boundary |
| Leading/trailing spaces | `" test "` | Negative |
| Null character | `"test\0value"` | Security |

### Email Fields

| Scenario | Test Value | Category |
|---|---|---|
| Valid standard | `"test@example.com"` | Positive |
| Valid with subdomain | `"test@mail.example.com"` | Positive |
| Valid with plus | `"test+tag@example.com"` | Positive |
| Missing @ | `"testexample.com"` | Negative |
| Missing domain | `"test@"` | Negative |
| Missing local part | `"@example.com"` | Negative |
| Double @ | `"test@@example.com"` | Negative |
| Spaces in email | `"test @example.com"` | Negative |
| No TLD | `"test@example"` | Negative |
| Max length (254 chars) | `"a" × 243 + "@example.com"` | Boundary |
| Over max length | `"a" × 244 + "@example.com"` | Boundary |
| Empty | `""` | Negative (if required) |

### Phone Number Fields

| Scenario | Test Value | Category |
|---|---|---|
| Valid international | `"+1-555-123-4567"` | Positive |
| Valid local | `"555-123-4567"` | Positive |
| Valid with parens | `"(555) 123-4567"` | Positive |
| Letters | `"abc-def-ghij"` | Negative |
| Too short | `"12345"` | Negative |
| Too long | `"1234567890123456"` | Negative / Boundary |
| Empty | `""` | Negative (if required) |
| Special chars | `"+1 (555) 123-4567 ext. 1234"` | Boundary |

### Number Fields

| Scenario | Test Value | Category |
|---|---|---|
| Valid positive | `42` | Positive |
| Zero | `0` | Boundary |
| Negative (if allowed) | `-1` | Boundary |
| Negative (if unsigned) | `-1` | Negative |
| Min value | `min_value` | Boundary |
| Max value | `max_value` | Boundary |
| Below min | `min_value - 1` | Boundary |
| Above max | `max_value + 1` | Boundary |
| Decimal (if integer field) | `3.14` | Negative |
| String instead of number | `"abc"` | Negative |
| Very large number | `999999999999` | Boundary |
| Empty/null | `null` | Negative (if required) |

### Date Fields

| Scenario | Test Value | Category |
|---|---|---|
| Valid date | `"2026-02-25"` | Positive |
| Valid past date | `"2020-01-01"` | Positive / Boundary |
| Valid future date | `"2030-12-31"` | Positive / Boundary |
| Invalid month | `"2026-13-01"` | Negative |
| Invalid day | `"2026-02-30"` | Negative |
| Feb 29 leap year | `"2028-02-29"` | Boundary |
| Feb 29 non-leap year | `"2027-02-29"` | Negative |
| Wrong format | `"25/02/2026"` | Negative |
| String | `"not-a-date"` | Negative |
| Epoch zero | `"1970-01-01"` | Boundary |
| Empty | `""` | Negative (if required) |

### Password Fields

| Scenario | Test Value | Category |
|---|---|---|
| Valid strong | `"ValidP@ss123!"` | Positive |
| Valid exact min length | `"Pass1!"` (if min=6) | Boundary |
| Too short | `"Ps1!"` | Negative |
| No uppercase | `"validp@ss123!"` | Negative |
| No lowercase | `"VALIDP@SS123!"` | Negative |
| No digit | `"ValidP@ss!!!"` | Negative |
| No special char | `"ValidPass123"` | Negative |
| At max length | `"A" × max + "1!a"` | Boundary |
| Over max length | `"A" × (max+1) + "1!a"` | Boundary |
| Common password | `"password123"` | Security |
| SQL injection | `"' OR 1=1 --"` | Security |
| Empty | `""` | Negative |

### URL Fields

| Scenario | Test Value | Category |
|---|---|---|
| Valid HTTPS | `"https://example.com"` | Positive |
| Valid with path | `"https://example.com/path"` | Positive |
| HTTP (not HTTPS) | `"http://example.com"` | Boundary |
| No protocol | `"example.com"` | Negative |
| Invalid protocol | `"ftp://example.com"` | Negative |
| JavaScript URI | `"javascript:alert(1)"` | Security |
| Data URI | `"data:text/html,<h1>test</h1>"` | Security |
| Empty | `""` | Negative (if required) |
| Very long URL | `"https://example.com/" + "a" × 2000` | Boundary |

### Select/Dropdown Fields (Enum)

| Scenario | Test Value | Category |
|---|---|---|
| Valid option | first enum value | Positive |
| Each valid option | each enum value individually | Positive |
| Non-existent option | `"InvalidOption"` | Negative |
| Empty/unselected | `""` | Negative (if required) |
| Numeric instead of string | `0` | Negative |

---

## Security Test Data

### XSS Payloads

```
<script>alert('XSS')</script>
<img src=x onerror=alert('XSS')>
<svg onload=alert('XSS')>
javascript:alert('XSS')
"><script>alert('XSS')</script>
'><script>alert('XSS')</script>
<body onload=alert('XSS')>
<iframe src="javascript:alert('XSS')">
```

### SQL Injection Payloads

```
' OR 1=1 --
" OR 1=1 --
'; DROP TABLE users; --
' UNION SELECT null, null --
1' OR '1'='1
admin'--
' AND 1=0 UNION SELECT 'a',1,'a',1 --
```

### Path Traversal Payloads

```
../../../etc/passwd
..\..\..\..\windows\system32
%2e%2e%2f%2e%2e%2f
....//....//
```

---

## User Override Format

`test-data-overrides.json` structure:

```json
{
  "Vehicle.plate_number": {
    "valid": ["AB1234", "XY9876"],
    "invalid": ["A1", "TOOLONG123456"],
    "pattern": "^[A-Z]{2}[0-9]{4}$",
    "note": "Country-specific plate format"
  },
  "Booking.date_range": {
    "valid": ["2026-03-01 to 2026-03-15"],
    "invalid": ["2020-01-01 to 2019-12-31"],
    "note": "End date must be after start date"
  },
  "Vehicle.vin": {
    "valid": ["1HGBH41JXMN109186"],
    "invalid": ["INVALIDVIN", "12345"],
    "pattern": "^[A-HJ-NPR-Z0-9]{17}$",
    "note": "Vehicle Identification Number: 17 chars, no I/O/Q"
  }
}
```

**Override key format**: `{Feature}.{field_name}` (case-sensitive to match
field names from merged scenarios).

**Override precedence**:
1. User override values (highest)
2. Inferred from validation rules in merged scenario
3. Standard auto-generated patterns (lowest)
