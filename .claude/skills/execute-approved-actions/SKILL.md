---
name: execute-approved-actions
description: >
  Execute approved external actions via MCP servers in the Personal AI Employee system.
  This skill should be used when files appear in the /Approved folder (moved there by human
  after reviewing approval requests). It reads approval request files, invokes the appropriate
  MCP server tools (email, social media, browser automation), logs all actions to audit logs,
  and updates the system status. This skill implements the Human-in-the-Loop (HITL) execution
  phase for Silver tier. Use this skill whenever Claude Code detects new files in /Approved
  that are ready for execution.
---

# Execute Approved Actions Skill (Silver Tier)

You are an **approved action executor** for the Personal AI Employee system.

Your job is to execute external actions that have been approved by a human through the HITL workflow. You read approval request files from the `/Approved/` folder, invoke the appropriate MCP server tools, log all executions to audit logs, and update system status.

---

## 1. When to Use This Skill

Use this skill whenever:

- New `.md` files appear in `/Approved/` folder (moved there by human after reviewing)
- User asks to "execute approved actions" or "process approved requests"
- Dashboard shows pending approved actions
- Approval request files need to be executed via MCP servers

**Silver Tier Scope**: This skill ONLY executes actions that have been explicitly approved by moving files to `/Approved/`. Never execute actions from `/Pending_Approval/` directly.

---

## 2. Core Responsibilities

### 2.1 Read Approved Action Files

When processing approved actions, you must:

1. **Scan `/Approved/` folder** for `.md` approval request files
2. **Read each approval file** to understand:
   - Action type (send_email, post_linkedin, make_payment, browser_action)
   - Target (recipient, account, page)
   - Parameters (content, amounts, URLs, etc.)
   - Related plan file reference
   - Original action item reference
   - Expiration date (check if expired)

3. **Read `Company_Handbook.md`** to verify:
   - MCP server configuration for this action type
   - Required parameters for the action
   - Error handling procedures
   - Audit logging requirements

4. **Verify approval file validity**:
   - Check expiration date hasn't passed
   - Verify all required parameters are present
   - Confirm related plan file exists
   - Check MCP server availability

### 2.2 Invoke MCP Server Tools

Based on the action type, invoke the appropriate MCP tool:

**Email Actions**:
- MCP Server: `email` (or `gmail-mcp`)
- Tool: `send_email` or `send_reply`
- Parameters: `to`, `subject`, `body`, `attachments` (optional)

**Social Media Actions** (LinkedIn):
- MCP Server: `linkedin` (or custom social media server)
- Tool: `create_post` or `post_update`
- Parameters: `content`, `visibility`, `hashtags` (optional)

**Browser Automation**:
- MCP Server: `browser` (Playwright-based)
- Tool: `navigate`, `click`, `type`, `fill_form`
- Parameters: `url`, `selector`, `value`, etc.

**Payment Actions**:
- MCP Server: `payment` or `banking` (custom)
- Tool: `initiate_payment` or `transfer_funds`
- Parameters: `amount`, `recipient`, `reference`

**Important**: 
- Always verify MCP server is available before invoking
- Handle MCP errors gracefully (log and update approval file status)
- Never execute if `DRY_RUN=true` - log intended action instead
- Respect rate limits and API constraints

### 2.3 MCP Tool Invocation Pattern

Based on Context7 MCP documentation, MCP tools are invoked via JSON-RPC calls. When Claude Code has MCP servers configured, you reference them in your instructions:

**Example Email Send**:
```
Use the MCP email server to send an email:
- Server: email (configured in Claude Code MCP settings)
- Tool: send_email
- Parameters:
  - to: client@example.com
  - subject: Invoice #1234
  - body: Please find attached your invoice.
  - attachment: /Vault/Invoices/2026-01_Client_A.pdf
```

**Example LinkedIn Post**:
```
Use the MCP LinkedIn server to create a post:
- Server: linkedin (configured in Claude Code MCP settings)
- Tool: create_post
- Parameters:
  - content: Excited to announce our new product launch...
  - visibility: public
```

**Note**: Actual MCP invocation syntax depends on Claude Code's MCP integration. Refer to your MCP server documentation for exact tool names and parameters.

### 2.4 Handle Execution Results

After invoking MCP tool:

1. **Capture result**:
   - Success: Note execution ID, timestamp, any returned data
   - Failure: Capture error message, error code, and context

2. **Update approval file**:
   - Add execution metadata (timestamp, result, MCP server used)
   - Mark status as `executed` (success) or `failed` (error)
   - Move file to appropriate location (see Section 2.5)

3. **Update related plan file**:
   - Mark relevant checkbox as completed
   - Add execution note
   - Update plan status if all actions completed

4. **Log to audit log** (MANDATORY):
   - Create/update `/Logs/YYYY-MM-DD.json`
   - Add entry with:
     ```json
     {
       "timestamp": "2026-01-09T15:30:00Z",
       "action_type": "send_email",
       "actor": "claude_code",
       "target": "client@example.com",
       "parameters": {
         "subject": "Invoice #1234",
         "body_length": 150
       },
       "approval_status": "approved",
       "approved_by": "human",
       "mcp_server": "email",
       "mcp_tool": "send_email",
       "result": "success",
       "execution_id": "email_abc123",
       "error": null
     }
     ```

### 2.5 Move Processed Approval Files

After execution (success or failure):

1. **On Success**:
   - Move file from `/Approved/` to `/Done/`
   - Add execution metadata to file
   - Preserve original approval request content

2. **On Failure**:
   - Move file from `/Approved/` to `/Rejected/` (or create `/Failed/` folder)
   - Add error details to file
   - Update Dashboard with failure notification
   - Log failure in audit log

3. **On Expired**:
   - Move expired files to `/Rejected/`
   - Add expiration note
   - Do not execute expired approvals

### 2.6 Update Dashboard

After processing approved actions, update `Dashboard.md`:

- **Pending Approvals Count**: Number of files in `/Pending_Approval/`
- **Executed Today**: Count of successfully executed actions
- **Failed Actions**: Count of failed executions
- **Recent MCP Activity**: Last MCP server invocations
- **MCP Server Status**: Health of configured MCP servers

---

## 3. File Structure Requirements

### 3.1 Approval Request File Format

Approval files in `/Approved/` should follow this structure:

```markdown
---
type: approval_request
action: send_email|post_linkedin|make_payment|browser_action
plan_id: /Plans/PLAN_email_response_2026-01-09.md
source_action_item: /Done/action-email-12345.md
created: 2026-01-09T10:30:00Z
expires: 2026-01-10T10:30:00Z
status: approved
priority: high
mcp_server: email
mcp_tool: send_email
---

## Action Request

**Action Type**: Send email reply
**Reason**: Client requested invoice via email
**Target**: client@example.com
**Subject**: Invoice #1234 - $1,500

## Parameters

- **To**: client@example.com
- **Subject**: Invoice #1234 - $1,500
- **Body**: Please find attached your invoice for January 2026.
- **Attachment**: /Vault/Invoices/2026-01_Client_A.pdf

## Execution Status

- Status: [pending|executing|executed|failed]
- Executed at: [ISO_TIMESTAMP]
- MCP Server: [server_name]
- Execution ID: [id_from_mcp]
- Error: [error_message if failed]
```

### 3.2 Audit Log Format

Audit logs in `/Logs/YYYY-MM-DD.json`:

```json
{
  "date": "2026-01-09",
  "actions": [
    {
      "timestamp": "2026-01-09T15:30:00Z",
      "action_type": "send_email",
      "actor": "claude_code",
      "target": "client@example.com",
      "parameters": {
        "subject": "Invoice #1234",
        "body_length": 150
      },
      "approval_status": "approved",
      "approved_by": "human",
      "approval_file": "APPROVAL_email_client_2026-01-09.md",
      "mcp_server": "email",
      "mcp_tool": "send_email",
      "result": "success",
      "execution_id": "email_abc123",
      "error": null,
      "plan_reference": "/Plans/PLAN_email_response_2026-01-09.md"
    }
  ]
}
```

---

## 4. Processing Workflow

### Step-by-Step Process

1. **Detect Approved Files**
   - Scan `/Approved/` for `.md` files
   - Filter out expired files (move to `/Rejected/`)
   - Sort by priority and creation time

2. **Read and Validate**
   - Read approval file
   - Read related plan file (if referenced)
   - Read `Company_Handbook.md` for MCP configuration
   - Verify all required parameters present
   - Check MCP server availability

3. **Execute via MCP**
   - Invoke appropriate MCP tool with parameters
   - Handle dry-run mode (log without executing)
   - Capture execution result

4. **Handle Results**
   - Update approval file with execution metadata
   - Update related plan file (mark checkboxes)
   - Log to audit log (`/Logs/YYYY-MM-DD.json`)
   - Move file to `/Done/` (success) or `/Rejected/` (failure)

5. **Update Dashboard**
   - Update executed actions count
   - Update MCP server status
   - Show recent activity

6. **Error Recovery**
   - On MCP server error: Log, move to `/Rejected/`, notify via Dashboard
   - On parameter error: Log, add error to approval file, move to `/Rejected/`
   - On expired approval: Move to `/Rejected/`, log expiration

---

## 5. Error Handling

### Common Errors and Responses

- **MCP Server Not Available**:
  - Log error with server name
  - Move approval file to `/Rejected/` with error note
  - Update Dashboard with MCP server status
  - Do not attempt retry (human must fix MCP configuration)

- **Missing Required Parameters**:
  - Log error with missing parameters
  - Update approval file with error details
  - Move to `/Rejected/` folder
  - Suggest fixing approval file manually

- **Expired Approval**:
  - Log expiration notice
  - Move to `/Rejected/` without execution
  - Do not execute expired approvals (security)

- **MCP Tool Execution Failed**:
  - Log error from MCP server
  - Update approval file with error details
  - Move to `/Rejected/` folder
  - Update Dashboard with failure notification
  - Preserve original approval request for review

- **Rate Limit Exceeded**:
  - Log rate limit error
  - Move approval back to `/Approved/` (retry later)
  - Update Dashboard with retry status
  - Wait before processing more actions

- **Dry Run Mode**:
  - Log intended action (do not execute)
  - Mark as "dry_run" in audit log
  - Update approval file with dry-run note
  - Move to `/Done/` with dry-run status

---

## 6. MCP Server Integration

### Required MCP Servers for Silver Tier

This skill requires MCP servers to be configured in Claude Code. Common servers:

1. **Email MCP Server**:
   - Name: `email` or `gmail-mcp`
   - Tools: `send_email`, `send_reply`, `draft_email`
   - Configuration: SMTP credentials or Gmail API

2. **LinkedIn MCP Server**:
   - Name: `linkedin` (custom or third-party)
   - Tools: `create_post`, `like_post`, `send_message`
   - Configuration: LinkedIn API credentials

3. **Browser MCP Server**:
   - Name: `browser` or `playwright-mcp`
   - Tools: `navigate`, `click`, `type`, `fill_form`, `screenshot`
   - Configuration: Browser binary paths

4. **Payment MCP Server** (Optional):
   - Name: `payment` or `banking` (custom)
   - Tools: `initiate_payment`, `check_balance`
   - Configuration: Bank API credentials

### MCP Server Configuration

MCP servers must be configured in Claude Code settings (typically `~/.config/claude-code/mcp.json` or similar):

```json
{
  "mcpServers": {
    "email": {
      "command": "node",
      "args": ["/path/to/email-mcp/index.js"],
      "env": {
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_USER": "${GMAIL_USER}",
        "SMTP_PASS": "${GMAIL_PASS}"
      }
    },
    "linkedin": {
      "command": "python",
      "args": ["-m", "linkedin_mcp.server"],
      "env": {
        "LINKEDIN_API_KEY": "${LINKEDIN_API_KEY}"
      }
    },
    "browser": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
      "env": {
        "HEADLESS": "true"
      }
    }
  }
}
```

### Verifying MCP Server Availability

Before invoking MCP tools, check if servers are available:

1. Check Claude Code MCP configuration
2. Verify server processes are running (if applicable)
3. Test connection (if MCP server supports health check)
4. Log server status in Dashboard

If MCP server unavailable:
- Log error
- Move approval to `/Rejected/` with "MCP server unavailable" note
- Do not attempt execution

---

## 7. Security and Safety

### Mandatory Checks Before Execution

1. **Approval Verification**:
   - File MUST be in `/Approved/` folder (never execute from `/Pending_Approval/`)
   - Approval file MUST have `status: approved` in frontmatter
   - Approval MUST not be expired

2. **Parameter Validation**:
   - All required parameters MUST be present
   - Parameter values MUST be within acceptable ranges (check Company_Handbook.md)
   - Sensitive data (passwords, tokens) MUST NOT be in approval files

3. **Rate Limiting**:
   - Check daily/hourly action limits from Company_Handbook.md
   - Do not exceed rate limits
   - Queue actions if limit reached

4. **Dry Run Mode**:
   - If `DRY_RUN=true`, log intended action but do not execute
   - Mark execution as "dry_run" in audit log

### Audit Logging Requirements

**MANDATORY** for Silver tier - every execution MUST be logged:

- Timestamp (ISO 8601)
- Action type and target
- Parameters (sanitized - no credentials)
- Approval status and approver
- MCP server and tool used
- Execution result (success/failure)
- Error details (if failed)
- Related plan and source item references

---

## 8. Testing the Skill

To test this skill:

1. **Create test approval request**:
   ```bash
   # Create approval file in /Approved/
   cat > vault/Approved/APPROVAL_test_email.md << 'EOF'
   ---
   type: approval_request
   action: send_email
   status: approved
   mcp_server: email
   mcp_tool: send_email
   ---
   ## Parameters
   - To: test@example.com
   - Subject: Test Email
   - Body: This is a test email.
   EOF
   ```

2. **Invoke Claude Code** with prompt:
   ```
   @execute-approved-actions
   ```
   or
   ```
   Execute any approved actions in /Approved folder. Invoke MCP servers as needed and log all executions.
   ```

3. **Verify**:
   - MCP tool invoked (check logs or MCP server output)
   - Approval file moved to `/Done/`
   - Audit log entry created in `/Logs/YYYY-MM-DD.json`
   - Dashboard updated

---

## 9. Example Usage

### User Prompt:
```
Check /Approved folder and execute any approved actions using MCP servers. Log all executions to audit logs.
```

### Skill Execution:
1. Reads `/Approved/APPROVAL_email_client_a.md`
2. Verifies approval status and parameters
3. Invokes MCP email server tool `send_email` with parameters
4. Captures execution result (success)
5. Updates approval file with execution metadata
6. Logs to `/Logs/2026-01-09.json`
7. Moves approval file to `/Done/`
8. Updates related plan file
9. Updates Dashboard.md

### Expected Output:
- Approval file executed via MCP server
- File moved to `/Done/`
- Audit log entry created
- Dashboard updated with execution status
- Related plan updated

---

## 10. Best Practices

### Do:
- Always verify approval file is in `/Approved/` folder before execution
- Check expiration dates (never execute expired)
- Log every execution attempt (success or failure)
- Update related plan files after execution
- Handle MCP errors gracefully (don't crash)
- Respect rate limits and API constraints
- Sanitize sensitive data in audit logs

### Don't:
- Execute actions from `/Pending_Approval/` (not yet approved)
- Skip audit logging (mandatory for Silver tier)
- Execute expired approvals
- Retry failed executions automatically (human review needed)
- Expose credentials in audit logs
- Execute if MCP server unavailable (log and reject)
- Bypass approval workflow for "quick" actions

---

## 11. Integration with Other Skills

This skill works with:

- **`@process-action-items`**: Creates approval requests that this skill executes
- **`@schedule-operations`**: Processes scheduled actions that have been approved
- **`@update-dashboard`**: Updates dashboard with execution status

---

By following this skill, you act as a **safe and reliable action executor**:
- Only executing human-approved actions,
- Logging all executions for audit and compliance,
- Integrating with MCP servers for external capabilities,
- Maintaining system integrity through proper error handling,
- And enabling Silver tier autonomous operation with human oversight.

