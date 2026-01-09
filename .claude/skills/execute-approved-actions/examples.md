# Execute Approved Actions – Examples

These examples demonstrate how the `execute-approved-actions` Skill processes approved external actions via MCP servers in the Personal AI Employee system (Silver tier).

---

## Example 1: Executing Approved Email Send

### Input: Approved Action File

**File**: `/Approved/APPROVAL_email_proposal_newclient_2026-01-09.md`

```markdown
---
type: approval_request
action: send_email
plan_id: /Plans/PLAN_proposal_request_2026-01-09.md
source_action_item: /Done/EMAIL_20260109_67890.md
created: 2026-01-09T14:35:00Z
expires: 2026-01-10T14:35:00Z
status: approved
priority: high
mcp_server: email
mcp_tool: send_email
---

## Action Request

**Action Type**: Send email reply with proposal attachment
**Target**: newclient@startup.com
**Subject**: Proposal for New Startup Inc. - Services

## Parameters

- To: newclient@startup.com
- Subject: Proposal for New Startup Inc. - Services
- Body: [Email body content]
- Attachment: /Vault/Proposals/2026-01_NewStartupInc.pdf
```

### Skill Execution

1. **Reads** approval file from `/Approved/`
2. **Verifies** approval status and expiration (not expired)
3. **Reads** `Company_Handbook.md` for MCP email server configuration
4. **Verifies** MCP email server is available
5. **Invokes** MCP tool: `email.send_email` with parameters
6. **Captures** execution result (success with email ID)
7. **Updates** approval file with execution metadata
8. **Logs** to `/Logs/2026-01-09.json`
9. **Updates** related plan file
10. **Moves** approval file to `/Done/`
11. **Updates** Dashboard.md

### Output: Updated Approval File (in /Done/)

```markdown
---
type: approval_request
action: send_email
status: executed
executed_at: 2026-01-09T15:30:00Z
mcp_server: email
mcp_tool: send_email
execution_id: email_smtp_abc123
result: success
---

[... original approval content ...]

## Execution Status

- Status: executed
- Executed at: 2026-01-09T15:30:00Z
- MCP Server: email
- Execution ID: email_smtp_abc123
- Error: null
```

### Audit Log Entry

**File**: `/Logs/2026-01-09.json`

```json
{
  "date": "2026-01-09",
  "actions": [
    {
      "timestamp": "2026-01-09T15:30:00Z",
      "action_type": "send_email",
      "actor": "claude_code",
      "target": "newclient@startup.com",
      "parameters": {
        "subject": "Proposal for New Startup Inc. - Services",
        "body_length": 450,
        "has_attachment": true
      },
      "approval_status": "approved",
      "approved_by": "human",
      "approval_file": "APPROVAL_email_proposal_newclient_2026-01-09.md",
      "mcp_server": "email",
      "mcp_tool": "send_email",
      "result": "success",
      "execution_id": "email_smtp_abc123",
      "error": null,
      "plan_reference": "/Plans/PLAN_proposal_request_2026-01-09.md"
    }
  ]
}
```

### Updated Plan File

```markdown
## Recommended Actions

- [x] Identify client: New Startup Inc.
- [x] Generate proposal document
- [x] **APPROVED & EXECUTED**: Send email with proposal attachment
  - Executed: 2026-01-09T15:30:00Z
  - Email ID: email_smtp_abc123
  - Status: Success
- [ ] Follow up if no response by Thursday
```

---

## Example 2: Executing LinkedIn Post via MCP

### Input: Approved LinkedIn Post

**File**: `/Approved/APPROVAL_linkedin_weekly_post_2026-01-09.md`

```markdown
---
type: approval_request
action: post_linkedin
status: approved
mcp_server: linkedin
mcp_tool: create_post
---

## Parameters

- Content: "🚀 Excited to share our latest client success..."
- Visibility: public
- Hashtags: #BusinessGrowth #TechInnovation
```

### Skill Execution

1. **Reads** approval file
2. **Invokes** MCP LinkedIn server tool: `linkedin.create_post`
3. **Result**: Success with post ID `linkedin_post_xyz789`
4. **Updates** approval file
5. **Logs** execution
6. **Moves** to `/Done/`

### Audit Log Entry

```json
{
  "timestamp": "2026-01-09T16:00:00Z",
  "action_type": "post_linkedin",
  "actor": "claude_code",
  "target": "linkedin_company_page",
  "parameters": {
    "content_length": 280,
    "visibility": "public",
    "hashtags": ["BusinessGrowth", "TechInnovation"]
  },
  "approval_status": "approved",
  "mcp_server": "linkedin",
  "mcp_tool": "create_post",
  "result": "success",
  "execution_id": "linkedin_post_xyz789",
  "error": null
}
```

---

## Example 3: Execution Failure Handling

### Scenario

MCP email server is unavailable (not running, connection error).

### Skill Execution

1. **Reads** approval file from `/Approved/`
2. **Attempts** to verify MCP email server
3. **Detects** server unavailable (connection error)
4. **Handles error**:
   - Logs error to audit log
   - Updates approval file with error details
   - Moves approval file to `/Rejected/` (not `/Done/`)
   - Updates Dashboard with MCP server status
   - Does NOT retry automatically

### Output: Rejected Approval File (in /Rejected/)

```markdown
---
type: approval_request
action: send_email
status: failed
error: mcp_server_unavailable
mcp_server: email
---

[... original content ...]

## Execution Status

- Status: failed
- Error: MCP server 'email' unavailable
- Error Details: Connection refused - server not running
- Recommendation: Check MCP server configuration and restart server
```

### Audit Log Entry

```json
{
  "timestamp": "2026-01-09T17:00:00Z",
  "action_type": "send_email",
  "target": "client@example.com",
  "approval_status": "approved",
  "mcp_server": "email",
  "mcp_tool": "send_email",
  "result": "failed",
  "error": "MCP server 'email' unavailable: Connection refused",
  "error_type": "mcp_server_unavailable"
}
```

---

## Example 4: Expired Approval Handling

### Scenario

Approval file has expired (expires date in past).

### Skill Execution

1. **Reads** approval file
2. **Checks** expiration date: `expires: 2026-01-08T14:35:00Z`
3. **Current time**: `2026-01-09T15:00:00Z` (expired)
4. **Handles expired**:
   - Logs expiration notice
   - Moves file to `/Rejected/` (not `/Done/`)
   - Does NOT execute (security requirement)
   - Updates Dashboard with expiration notice

### Output: Rejected Expired File

```markdown
---
type: approval_request
action: send_email
status: expired
expired_at: 2026-01-09T15:00:00Z
original_expires: 2026-01-08T14:35:00Z
---

## Execution Status

- Status: expired
- Original expiration: 2026-01-08T14:35:00Z
- Detected expired: 2026-01-09T15:00:00Z
- Action: NOT EXECUTED (expired approvals are not executed for security)
- Recommendation: Review original action item and create new approval if needed
```

---

## Example 5: Dry Run Mode

### Scenario

System is in `DRY_RUN=true` mode.

### Skill Execution

1. **Reads** approval file
2. **Checks** environment: `DRY_RUN=true`
3. **Handles dry-run**:
   - Logs intended action (does not execute)
   - Updates approval file with dry-run note
   - Marks as "dry_run" in audit log
   - Moves to `/Done/` with dry-run status

### Audit Log Entry (Dry Run)

```json
{
  "timestamp": "2026-01-09T18:00:00Z",
  "action_type": "send_email",
  "target": "test@example.com",
  "approval_status": "approved",
  "mcp_server": "email",
  "result": "dry_run",
  "dry_run_note": "DRY_RUN=true - action logged but not executed"
}
```

---

## Example 6: Multiple Approved Actions

### Scenario

Multiple approval files in `/Approved/` folder.

### Skill Execution

1. **Scans** `/Approved/` folder
2. **Finds** 3 approval files:
   - `APPROVAL_email_1.md` (high priority, not expired)
   - `APPROVAL_linkedin_1.md` (medium priority, not expired)
   - `APPROVAL_email_2.md` (low priority, not expired)
3. **Sorts** by priority (high → medium → low)
4. **Processes** each in priority order:
   - Execute high priority email
   - Execute medium priority LinkedIn post
   - Execute low priority email
5. **Updates** Dashboard with all 3 executions
6. **Logs** all 3 to audit log

### Output: Dashboard Update

```markdown
## Recent MCP Activity

- [2026-01-09 18:00] Executed: Email to client@example.com (high priority)
- [2026-01-09 18:01] Executed: LinkedIn post (medium priority)
- [2026-01-09 18:02] Executed: Email to vendor@example.com (low priority)

## MCP Server Status

- Email server: ✅ Available (3 executions today)
- LinkedIn server: ✅ Available (1 execution today)
```

---

These examples demonstrate:
- Successful execution via MCP servers
- Error handling (server unavailable, expired approvals)
- Dry-run mode support
- Multiple action processing
- Complete audit trail for all executions
- Proper file management (Done vs Rejected)

