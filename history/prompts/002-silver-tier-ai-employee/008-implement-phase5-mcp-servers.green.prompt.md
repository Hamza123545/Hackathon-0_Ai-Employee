---
id: "008"
title: "Implement Phase 5 MCP Servers External Actions"
stage: green
date: 2026-01-11
surface: agent
model: claude-opus-4-5-20251101
feature: 002-silver-tier-ai-employee
branch: main
user: user
command: /sp.implement
labels: ["phase5", "mcp-servers", "fastmcp", "email", "linkedin", "playwright"]
links:
  spec: specs/002-silver-tier-ai-employee/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - AI_Employee/mcp_servers/email_mcp.py
  - AI_Employee/mcp_servers/linkedin_mcp.py
  - AI_Employee/mcp_servers/playwright_mcp.py
  - AI_Employee/mcp_servers/__init__.py
  - .claude/skills/execute-approved-actions/SKILL.md
  - specs/002-silver-tier-ai-employee/tasks.md
tests:
  - None (MCP servers implemented, tests pending)
---

## User Prompt

Complete Silver Tier Phase 5: User Story 3 - External Actions via MCP Servers (T036-T050) from specs/002-silver-tier-ai-employee/tasks.md.

## Instructions

1. **READ FIRST**: All specs already defined:
   - `specs/002-silver-tier-ai-employee/spec.md` (US3, FR-023 to FR-025, SC-011)
   - `specs/002-silver-tier-ai-employee/contracts/email-mcp.json` (email MCP contract)
   - `specs/002-silver-tier-ai-employee/contracts/linkedin-mcp.json` (LinkedIn MCP contract)
   - `specs/002-silver-tier-ai-employee/research.md` (FastMCP pattern lines 22-78)
   - `specs/002-silver-tier-ai-employee/tasks.md` (T036-T050 in Phase 5)
   - `.claude/skills/execute-approved-actions/SKILL.md` (execution skill documentation)

2. **Review existing**:
   - `AI_Employee/utils/audit_logger.py` (from Phase 2 T009)
   - `AI_Employee/utils/sanitizer.py` (from Phase 2 T008)
   - `AI_Employee/models/approval_request.py` (from Phase 2 T010)

3. **Implement T036-T050**:
   - **T036-T039**: `AI_Employee/mcp_servers/email_mcp.py` - FastMCP server with send_email tool (smtplib.SMTP with TLS), health_check tool, error handling (SMTP_AUTH_FAILED, SMTP_CONNECTION_ERROR, INVALID_RECIPIENT, ATTACHMENT_TOO_LARGE), exponential backoff retry (max 3 attempts)
   - **T040-T043**: `AI_Employee/mcp_servers/linkedin_mcp.py` - FastMCP server with create_post tool (requests POST to LinkedIn API v2 with headers: Authorization Bearer, X-Restli-Protocol-Version: 2.0.0, LinkedIn-Version: 202601), health_check tool, rate limit handling (429 response, queue retry)
   - **T044-T045**: `AI_Employee/mcp_servers/playwright_mcp.py` - FastMCP server with browser_action tool (playwright.sync_api navigate/click/type/fill_form/screenshots saved to /Logs/screenshots/), health_check tool
   - **T046-T050**: Update `.claude/skills/execute-approved-actions/SKILL.md` - implement MCP invocation logic

4. **Use Context7 MCP** for Python library docs (fastmcp, smtplib, requests, playwright) if needed.

5. **Follow patterns**: FastMCP SDK pattern from research.md, use AuditLogger for all executions, sanitize credentials before logging

## Response Summary

### Files Created/Updated

**AI_Employee/mcp_servers/email_mcp.py** (NEW):
- FastMCP server with `send_email` and `health_check` tools
- Uses smtplib.SMTP with TLS
- Environment variables: SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, FROM_ADDRESS, SMTP_USE_TLS
- Error codes: SMTP_AUTH_FAILED, SMTP_CONNECTION_ERROR, INVALID_RECIPIENT, ATTACHMENT_TOO_LARGE
- Exponential backoff retry (max 3 attempts) for transient errors
- Attachment support with size validation (max 25MB)

**AI_Employee/mcp_servers/linkedin_mcp.py** (NEW):
- FastMCP server with `create_post` and `health_check` tools
- Uses requests to POST to LinkedIn API v2 (/rest/posts)
- Headers: Authorization Bearer, X-Restli-Protocol-Version: 2.0.0, LinkedIn-Version: 202601
- Environment variables: LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN, LINKEDIN_API_VERSION
- Error codes: AUTH_EXPIRED, RATE_LIMIT_EXCEEDED, INVALID_CONTENT, NETWORK_ERROR
- Rate limit handling with exponential backoff (max 5 retries)
- Hashtag support and link content

**AI_Employee/mcp_servers/playwright_mcp.py** (NEW):
- FastMCP server with `browser_action`, `take_screenshot`, and `health_check` tools
- Uses playwright.sync_api for browser automation
- Action types: navigate, click, type, fill_form, screenshot
- Screenshots saved to configurable directory (/Logs/screenshots/)
- Environment variables: PLAYWRIGHT_BROWSER, PLAYWRIGHT_HEADLESS, PLAYWRIGHT_SCREENSHOT_DIR, PLAYWRIGHT_TIMEOUT_MS
- Error codes: BROWSER_ERROR, SELECTOR_NOT_FOUND, TIMEOUT, NAVIGATION_ERROR

**AI_Employee/mcp_servers/__init__.py** (UPDATED):
- Exports all MCP server tools for easy import

**.claude/skills/execute-approved-actions/SKILL.md** (UPDATED):
- Added Section 6 with complete MCP Server Integration documentation
- MCP Server Invocation Pattern (3-step process)
- Error codes and handling tables for all MCP servers
- Complete execution flow code example
- Credential sanitization requirements
- Plan file update function

**specs/002-silver-tier-ai-employee/tasks.md** (UPDATED):
- Marked T036-T050 as completed [x]
- Added Phase 5 checkpoint marker

### Key Implementation Details

1. **FastMCP Pattern**: All servers use `@mcp.tool` decorator and `mcp.run(transport='stdio')`
2. **Error Handling**: Each server defines specific error codes per contracts
3. **Retry Logic**: Email uses exponential backoff (1s, 2s, 4s), LinkedIn uses rate limit detection
4. **Credential Safety**: Parameters sanitized via CredentialSanitizer before logging
5. **Audit Logging**: All executions logged via AuditLogger.log_execution()

### Tasks Completed (T036-T050)

All 15 Phase 5 tasks completed. User Story 3 (External Actions via MCP Servers) is now complete.

## Outcome

Phase 5 implementation complete. MCP servers for email, LinkedIn, and browser automation are ready for integration with the execute-approved-actions skill. The HITL workflow can now execute approved external actions via these MCP servers with full audit logging.
