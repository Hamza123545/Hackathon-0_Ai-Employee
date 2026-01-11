# Execute Approved Actions - Real Execution Examples

This document provides real-world examples of executing approved actions via the execute-approved-actions skill.

---

## Example 1: Email Send

### Input: Approval Request File

**File**: `/Pending_Approval/APPROVAL_email_client_2026-01-09.md`

```markdown
---
type: approval_request
id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
action_type: email_send
target: "client@example.com"
risk_level: low
rationale: "Client requested invoice via email"
created_timestamp: 2026-01-09T10:30:00Z
status: approved
approval_timestamp: 2026-01-09T10:35:00Z
approver: "user"
mcp_server: "email-mcp"
mcp_tool: "send_email"
---
## Action Request

**Action Type**: Send email reply
**Reason**: Client requested invoice via email
**Target**: client@example.com

## Parameters

- **To**: client@example.com
- **Subject**: Invoice #1234 - $1,500
- **Body**: Please find attached your invoice for January 2026.
- **Attachment**: /Vault/Invoices/2026-01_Client_A.pdf
```

### Execution Flow

1. **File Detected**: ApprovalOrchestrator detects file in `/Approved/` folder
2. **Parse Approval**: Read approval file, extract parameters
3. **MCP Invocation**: Call email-mcp `send_email` tool:
   ```json
   {
     "to": "client@example.com",
     "subject": "Invoice #1234 - $1,500",
     "body": "Please find attached your invoice for January 2026.",
     "attachments": ["/Vault/Invoices/2026-01_Client_A.pdf"]
   }
   ```
4. **MCP Response**:
   ```json
   {
     "status": "sent",
     "message_id": "<1704801234.567@smtp.gmail.com>",
     "timestamp": "2026-01-09T10:36:15.123456Z"
   }
   ```
5. **Audit Log Entry** (auto-created):
   ```json
   {
     "entry_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
     "timestamp": "2026-01-09T10:36:15.123456Z",
     "action_type": "email_send",
     "actor": "claude-code",
     "target": "client@example.com",
     "parameters": {
       "subject": "Invoice #1234 - $1,500",
       "body_preview": "Please find attached your invoice...",
       "attachment_count": 1
     },
     "approval_status": "approved",
     "approval_by": "user",
     "approval_timestamp": "2026-01-09T10:35:00Z",
     "mcp_server": "email-mcp",
     "result": "success",
     "error": null,
     "execution_duration_ms": 1234,
     "approval_request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
   }
   ```
6. **File Movement**: File moved from `/Approved/` to `/Done/` with execution metadata appended

### Output: Completed Approval File

**File**: `/Done/APPROVAL_email_client_2026-01-09.md`

```markdown
---
type: approval_request
id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
action_type: email_send
target: "client@example.com"
status: executed
execution_timestamp: 2026-01-09T10:36:15.123456Z
mcp_server: "email-mcp"
execution_id: "<1704801234.567@smtp.gmail.com>"
result: "success"
---
## Execution Status

- **Status**: ✅ Executed successfully
- **Executed at**: 2026-01-09T10:36:15Z
- **MCP Server**: email-mcp
- **Execution ID**: <1704801234.567@smtp.gmail.com>
- **Duration**: 1234ms
- **Audit Log Entry**: b2c3d4e5-f6a7-8901-bcde-f12345678901
```

---

## Example 2: LinkedIn Post

### Input: Approval Request File

**File**: `/Pending_Approval/APPROVAL_linkedin_announcement_2026-01-09.md`

```markdown
---
type: approval_request
id: "c3d4e5f6-a7b8-9012-cdef-123456789012"
action_type: linkedin_post
target: "LinkedIn"
risk_level: medium
rationale: "Announce new product feature"
created_timestamp: 2026-01-09T14:00:00Z
status: approved
approval_timestamp: 2026-01-09T14:05:00Z
approver: "user"
mcp_server: "linkedin-mcp"
mcp_tool: "create_post"
---
## Parameters

- **Content**: Excited to announce our new AI-powered automation feature! 🚀 This will help teams save hours every week. #AI #Automation #Innovation
- **Visibility**: PUBLIC
```

### Execution Flow

1. **File Detected**: ApprovalOrchestrator detects file in `/Approved/`
2. **LinkedIn Rules Check**: Verify posting limits and schedule (max 3/day, 9am-5pm)
3. **MCP Invocation**: Call linkedin-mcp `create_post` tool:
   ```json
   {
     "content": "Excited to announce our new AI-powered automation feature! 🚀 This will help teams save hours every week. #AI #Automation #Innovation",
     "visibility": "PUBLIC"
   }
   ```
4. **MCP Response**:
   ```json
   {
     "status": "published",
     "post_id": "urn:li:activity:1234567890",
     "post_url": "https://www.linkedin.com/feed/update/1234567890",
     "timestamp": "2026-01-09T14:06:30.789012Z"
   }
   ```
5. **Audit Log Entry**:
   ```json
   {
     "entry_id": "d4e5f6a7-b8c9-0123-def4-234567890123",
     "timestamp": "2026-01-09T14:06:30.789012Z",
     "action_type": "linkedin_post",
     "actor": "claude-code",
     "target": "LinkedIn",
     "parameters": {
       "content_preview": "Excited to announce our new AI-powered...",
       "visibility": "PUBLIC",
       "hashtags": ["#AI", "#Automation", "#Innovation"]
     },
     "approval_status": "approved",
     "approval_by": "user",
     "mcp_server": "linkedin-mcp",
     "result": "success",
     "execution_duration_ms": 2345,
     "approval_request_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
     "extra_fields": {
       "post_id": "urn:li:activity:1234567890",
       "post_url": "https://www.linkedin.com/feed/update/1234567890"
     }
   }
   ```
6. **File Movement**: File moved to `/Done/` with post URL

---

## Example 3: Browser Automation

### Input: Approval Request File

**File**: `/Pending_Approval/APPROVAL_browser_form_2026-01-09.md`

```markdown
---
type: approval_request
id: "e5f6a7b8-c9d0-1234-ef56-345678901234"
action_type: browser_action
target: "https://example.com/contact"
risk_level: high
rationale: "Submit contact form with business inquiry"
mcp_server: "playwright-mcp"
mcp_tool: "browser_action"
---
## Parameters

- **Action**: fill_form
- **URL**: https://example.com/contact
- **Form Fields**:
  - name: "John Doe"
  - email: "john@example.com"
  - message: "Interested in your services"
- **Take Screenshot**: true
```

### Execution Flow

1. **File Detected**: ApprovalOrchestrator detects file
2. **MCP Invocation**: Call playwright-mcp `browser_action` tool:
   ```json
   {
     "action": "fill_form",
     "url": "https://example.com/contact",
     "form_fields": {
       "name": "John Doe",
       "email": "john@example.com",
       "message": "Interested in your services"
     },
     "take_screenshot": true
   }
   ```
3. **MCP Response**:
   ```json
   {
     "status": "success",
     "screenshot_path": "/Logs/screenshots/2026-01-09_14-30-45_contact-form.png",
     "timestamp": "2026-01-09T14:30:45.123456Z"
   }
   ```
4. **Audit Log Entry**: Logged with screenshot path
5. **File Movement**: File moved to `/Done/` with screenshot reference

---

## Example 4: Error Handling - MCP Unavailable

### Scenario: Email MCP Server Not Running

**Input**: Approval file in `/Approved/` for email send

**Execution Flow**:
1. **Health Check**: ApprovalOrchestrator checks email-mcp health
2. **Health Check Fails**: MCP server returns `status: error`
3. **Error Handling**:
   - Log error to audit log:
     ```json
     {
       "action_type": "email_send",
       "result": "failure",
       "error": "MCP server unavailable: email-mcp",
       "error_code": "MCP_SERVER_UNAVAILABLE"
     }
     ```
   - Move file to `/Rejected/` (not `/Done/`)
   - Create notification in `/Needs_Action/`:
     ```markdown
     # MCP Server Unavailable
     
     **Issue**: Email MCP server is not responding
     **Action**: Check PM2 status, restart email-mcp server
     **Approval File**: APPROVAL_email_client_2026-01-09.md (moved to /Rejected/)
     ```

---

## Example 5: Error Handling - Expired Approval

### Scenario: Approval Request Expired (>24 hours)

**Input**: Approval file in `/Approved/` created 25 hours ago

**Execution Flow**:
1. **Expiration Check**: ApprovalOrchestrator checks `created_timestamp`
2. **Expired Detected**: Age = 25 hours > 24 hour limit
3. **Error Handling**:
   - Log expiration to audit log:
     ```json
     {
       "action_type": "email_send",
       "result": "failure",
       "error": "Approval request expired (>24 hours)",
       "error_code": "EXPIRED"
     }
     ```
   - Move file to `/Rejected/` (not executed)
   - Do NOT execute expired approvals (security)

---

## Example 6: Error Handling - Malformed Approval File

### Scenario: Approval File Missing Required Fields

**Input**: Malformed approval file in `/Approved/`

```markdown
---
type: approval_request
# Missing: action_type, target, parameters, mcp_server
---
```

**Execution Flow**:
1. **Parse Attempt**: ApprovalOrchestrator tries to parse file
2. **Validation Fails**: Missing required fields
3. **Error Handling**:
   - Log validation error to audit log:
     ```json
     {
       "action_type": "unknown",
       "result": "failure",
       "error": "Missing required fields: action_type, target, mcp_server",
       "error_code": "PARAMETER_VALIDATION_FAILED"
     }
     ```
   - Move file to `/Rejected/` with error details appended
   - Create notification in `/Needs_Action/` for manual review

---

## Best Practices

1. **Always Log Before Moving**: Audit logging must succeed before moving files
2. **Handle Errors Gracefully**: Never crash orchestrator on MCP errors
3. **Preserve Approval Files**: Keep original approval content in `/Done/` or `/Rejected/`
4. **Update Related Plans**: Mark checkboxes in related plan files after execution
5. **Verify MCP Health**: Check MCP server availability before execution
6. **Respect Rate Limits**: Queue actions when rate limits exceeded
7. **Sanitize Credentials**: All parameters automatically sanitized before logging

---

**For more details**: See `.claude/skills/execute-approved-actions/SKILL.md`
