# Phase 2A: Subagent Mode (Context Isolation)

> ✅ **Use this mode when `runSubagent` tool is available.**

Subagents provide **context isolation** — each feature is processed in a fresh context window, preventing memory accumulation and timeout issues.

---

## When to Use

- Agent has access to `runSubagent` tool
- Application has many features (5+)
- Features are complex with many test scenarios
- Risk of context timeout in single session

## Workflow Overview

```
MAIN AGENT (orchestrator):
  FOR EACH FEATURE in FEATURE_MAP:
    1. Prepare subagent task with feature details + app URL
    2. Invoke runSubagent with task description
    3. Subagent:
       - Opens the feature URL in Playwright
       - Explores all interactive elements via snapshots
       - Interacts like a Senior UAT Tester (tries everything)
       - Generates FUNCTIONAL test cases with Playwright commands
       - Captures screenshots as evidence
       - Writes to JSONL file
       - Returns completion summary
    4. Main agent receives result, proceeds to next feature
```

---

## Subagent Task Template

For each feature, invoke `runSubagent` with this structured task:

```markdown
Act as a Senior UAT Tester. Generate comprehensive functional UAT test cases for feature: <FEATURE_NAME>

APPLICATION URL: <APP_URL>
FEATURE URL: <FEATURE_URL>

FEATURE DETAILS:
- Name: <feature_name>
- Type: <feature_type>
- Description: <what users do in this feature>
- Discovered Elements: <element_list_from_phase1>
- Test ID Prefix: TC-<PREFIX>
- Starting ID: <next_available_id>
- JSONL Output: uat_<project>.jsonl

INSTRUCTIONS:
1. Open the feature URL using playwright-cli
2. Take a snapshot to identify ALL interactive elements
3. Explore EVERY element like a Senior UAT Tester would:
   - Click every button, link, and icon
   - Fill every form field with valid AND invalid data
   - Try submitting empty forms
   - Try special characters, very long text, boundary values
   - Check what happens with no data vs lots of data
   - Look for loading states, error messages, success messages
   - Check disabled states and conditional visibility

4. Generate test cases that describe:
   - What the TESTER does (actions in plain language)
   - What the TESTER sees (expected visible results)
   - The playwright-cli command that verifies it
   - Business conditions and scenarios

5. Test Case Categories (MUST cover ALL):
   - Positive: Happy path workflows (user completes task successfully)
   - Negative: Error handling (user makes mistakes, system responds gracefully)
   - Boundary: Edge cases (empty data, maximum values, special characters)
   - Validation: Form and input validation (required fields, formats)
   - Usability: Loading states, feedback, disabled states
   - Cross-Feature: Interactions with other features

6. Write to JSONL file IMMEDIATELY after generating

TEST CASE LANGUAGE RULES:
- Use "Click", "Enter", "Select", "Navigate", "Verify" — action verbs
- Describe what USER SEES, not what code does
- Include specific values tester should enter (use test data placeholders)
- Expected results = visible outcomes (messages, screen changes, data displays)
- Include playwright-cli command for each step

TEST CASE SCHEMA:
{
  "test_case_id": "TC-<PREFIX>-NNN",
  "title": "User-focused action description",
  "feature_area": "<FEATURE_NAME>",
  "priority": "Critical|High|Medium|Low",
  "preconditions": "Setup tester needs before starting",
  "test_steps": "1. Navigate to...\n2. Click...\n3. Enter...\n4. Verify...",
  "test_data": "Specific values tester should use",
  "expected_result": "What tester should see when successful",
  "validation_points": "Specific things to check",
  "playwright_commands": "playwright-cli commands that verify this test",
  "screenshots": "Screenshot filenames captured as evidence",
  "status": "Not Started",
  "comments": ""
}

WRITE TO JSONL AFTER COMPLETION — DO NOT RETURN TEST CASES IN RESPONSE!
```

---

## Progress Tracking

After each subagent completes, the main agent displays:

```
═══════════════════════════════════════════════════════════════
[N/Total] SUBAGENT COMPLETE: <Feature Name>
   Test cases generated: <count> (TC-XXX-001 to TC-XXX-NNN)
   Screenshots captured: <count>
   Written to: uat_<project>.jsonl
   Status: ✓ Success
═══════════════════════════════════════════════════════════════
```

---

## Error Handling

If subagent fails:
1. Log the error and feature that failed
2. Mark feature as incomplete in progress tracker
3. Continue with next feature (don't block entire workflow)
4. At end, report which features need manual attention

```
⚠️ SUBAGENT FAILED: <Feature Name>
   Error: <error message>
   Action: Skipping to next feature. Manual test generation required.
```

---

## Benefits of Subagent Mode

| Benefit | Description |
|---------|-------------|
| Context Isolation | Each feature starts fresh — no memory accumulation |
| Parallel Potential | Future: multiple subagents could run in parallel |
| Error Containment | One feature failure doesn't crash entire workflow |
| Cleaner Orchestration | Main agent only tracks progress, not test case details |

---

## Fallback

If `runSubagent` is not available, use [Streaming Mode](phase2b-streaming-mode.md) instead.
