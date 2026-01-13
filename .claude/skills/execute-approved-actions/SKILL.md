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

**Domain-Specific Routing (Gold Tier - T079)**: Route actions to correct MCP server based on domain classification:
- **Personal Domain**: email-mcp, linkedin-mcp, playwright-mcp
- **Business Domain**: email-mcp, linkedin-mcp, facebook-mcp
- **Accounting Domain**: xero-mcp
- **Social Media Domain**: facebook-mcp, instagram-mcp, twitter-mcp

Based on the action type and domain, invoke the appropriate MCP tool:

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

**Xero Accounting Actions** (Gold Tier):
- MCP Server: `xero-mcp`
- Tool: `create_expense` - Create expense entry in Xero
  - Parameters: `amount`, `date`, `description`, `category`, `currency`, `receipt_url` (optional)
- Tool: `create_invoice` - Create invoice in Xero
  - Parameters: `contact_name`, `line_items`, `due_date`, `reference` (optional), `currency`
- Tool: `get_invoices` - Retrieve invoices (read-only, no approval needed)
- Tool: `get_financial_report` - Generate financial reports (read-only, no approval needed)
- Tool: `sync_bank_transactions` - Sync bank transactions (read-only, no approval needed)

**Facebook Actions** (Gold Tier):
- MCP Server: `facebook-mcp`
- Tool: `post_to_page` - Post message to Facebook Page (requires approval)
  - Parameters: `page_id`, `message`, `link` (optional), `published` (default: true)
- Tool: `get_page_posts` - Retrieve recent posts (read-only, no approval needed)
- Tool: `get_engagement_summary` - Get aggregated engagement metrics (read-only, no approval needed)
- Tool: `delete_post` - Delete a post from Facebook Page (requires approval)

**Instagram Actions** (Gold Tier):
- MCP Server: `instagram-mcp`
- Tool: `post_photo` - Post photo to Instagram Business account (requires approval, two-step: container + publish)
  - Parameters: `instagram_business_id`, `image_url`, `caption`, `location_id` (optional), `user_tags` (optional)
- Tool: `post_video` - Post video to Instagram Business account (requires approval, two-step: container + publish)
  - Parameters: `instagram_business_id`, `video_url`, `caption`, `location_id` (optional), `thumb_offset` (optional)
- Tool: `get_media` - Retrieve Instagram media posts (read-only, no approval needed)
- Tool: `get_insights` - Get Instagram Business account insights (read-only, no approval needed)
- Tool: `get_media_insights` - Get insights for specific media post (read-only, no approval needed)

**Twitter/X Actions** (Gold Tier):
- MCP Server: `twitter-mcp`
- Tool: `post_tweet` - Post a tweet (requires approval, 280 char limit)
  - Parameters: `text`, `reply_to_tweet_id` (optional), `quote_tweet_id` (optional), `media_ids` (optional, max 4), `poll_options` (optional), `poll_duration_minutes` (optional), `reply_settings` (default: "everyone")
- Tool: `delete_tweet` - Delete a tweet (requires approval)
  - Parameters: `tweet_id`, `reason` (optional)
- Tool: `get_user_tweets` - Retrieve recent tweets with metrics (read-only, no approval needed)
- Tool: `get_tweet_metrics` - Get detailed engagement metrics for a tweet (read-only, no approval needed)
- Tool: `get_engagement_summary` - Get aggregated engagement metrics for a period (read-only, no approval needed)

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
   - **MANDATORY: Log to audit log FIRST** (`/Logs/YYYY-MM-DD.json`) using `AuditLogger.log_execution()`
   - **CRITICAL**: If audit logging fails, DO NOT move file - treat as critical error
   - Update approval file with execution metadata
   - Update related plan file (mark checkboxes)
   - Move file to `/Done/` (success) or `/Rejected/` (failure) ONLY after successful audit logging

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

### Silver Tier MCP Servers

This skill integrates with three custom FastMCP servers implemented in Python:

| Server | Location | Tools | Purpose |
|--------|----------|-------|---------|
| `email-mcp` | `AI_Employee/mcp_servers/email_mcp.py` | `send_email`, `health_check` | Send emails via SMTP with TLS |
| `linkedin-mcp` | `AI_Employee/mcp_servers/linkedin_mcp.py` | `create_post`, `health_check` | Post to LinkedIn via API v2 |
| `playwright-mcp` | `AI_Employee/mcp_servers/playwright_mcp.py` | `browser_action`, `take_screenshot`, `health_check` | Browser automation |

### MCP Server Configuration

MCP servers are configured via environment variables and run as stdio-based servers:

**Email MCP Configuration** (`.env`):
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=user@gmail.com
SMTP_PASSWORD=app_password
FROM_ADDRESS=user@gmail.com
SMTP_USE_TLS=true
```

**LinkedIn MCP Configuration** (`.env`):
```env
LINKEDIN_ACCESS_TOKEN=AQV...
LINKEDIN_PERSON_URN=urn:li:person:ABCDEF123
LINKEDIN_API_VERSION=202601
```

**Playwright MCP Configuration** (`.env`):
```env
PLAYWRIGHT_BROWSER=chromium
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_SCREENSHOT_DIR=D:/AI_Employee/Logs/screenshots
PLAYWRIGHT_TIMEOUT_MS=30000
```

### MCP Server Invocation Pattern

**Step 1: Health Check Before Execution**

Before invoking any MCP tool, ALWAYS run health_check to verify server availability:

```python
# For email-mcp
from AI_Employee.mcp_servers.email_mcp import health_check as email_health
result = email_health()
if result['status'] != 'available':
    # Handle MCP_SERVER_UNAVAILABLE error

# For linkedin-mcp
from AI_Employee.mcp_servers.linkedin_mcp import health_check as linkedin_health
result = linkedin_health()
if result['status'] != 'available':
    # Handle AUTH_EXPIRED or NETWORK_ERROR

# For playwright-mcp
from AI_Employee.mcp_servers.playwright_mcp import health_check as playwright_health
result = playwright_health()
if result['status'] != 'available':
    # Handle BROWSER_ERROR
```

**Step 2: Invoke MCP Tool Based on Action Type**

```python
import time
from datetime import datetime, timezone
from pathlib import Path

from AI_Employee.mcp_servers.email_mcp import send_email
from AI_Employee.mcp_servers.linkedin_mcp import create_post
from AI_Employee.mcp_servers.playwright_mcp import browser_action
from AI_Employee.utils.audit_logger import AuditLogger
from AI_Employee.utils.sanitizer import CredentialSanitizer
from AI_Employee.models.approval_request import parse_approval_file

# Parse approval file
approval = parse_approval_file(Path('/Approved/APPROVAL_email_20260109.md'))
start_time = time.time()

# Route to correct MCP server based on action_type
if approval.action_type == 'email_send':
    result = send_email(
        to=approval.parameters.get('to'),
        subject=approval.parameters.get('subject'),
        body=approval.parameters.get('body'),
        is_html=approval.parameters.get('is_html', False),
        attachments=approval.parameters.get('attachments')
    )

elif approval.action_type == 'linkedin_post':
    result = create_post(
        text=approval.parameters.get('text'),
        visibility=approval.parameters.get('visibility', 'PUBLIC'),
        hashtags=approval.parameters.get('hashtags')
    )

elif approval.action_type == 'browser_action':
    result = browser_action(
        url=approval.parameters.get('url'),
        action_type=approval.parameters.get('action_type', 'navigate'),
        selector=approval.parameters.get('selector'),
        value=approval.parameters.get('value'),
        screenshot=True,
        form_fields=approval.parameters.get('form_fields')
    )

execution_duration_ms = int((time.time() - start_time) * 1000)
```

**Step 3: Log Execution with AuditLogger (MANDATORY - MUST succeed before moving file)**

**CRITICAL REQUIREMENT**: Audit logging is MANDATORY and must succeed before moving approval files. If logging fails, treat as critical error - DO NOT move file, DO NOT update plan, log error to console.

```python
from AI_Employee.utils.audit_logger import AuditLogger
from AI_Employee.utils.sanitizer import CredentialSanitizer

# Initialize logger
sanitizer = CredentialSanitizer()
logger = AuditLogger(logs_path=Path('AI_Employee/Logs'), sanitizer=sanitizer)

# Log execution (parameters are auto-sanitized)
# MUST catch exceptions - if this fails, do not proceed with file movement
try:
    entry_id = logger.log_execution(
    action_type=approval.action_type,  # 'email_send', 'linkedin_post', 'browser_action'
    actor='claude-code',
    target=approval.target,
    parameters=approval.parameters,  # Will be sanitized automatically
    approval_status='approved',
    approval_by='user',
    approval_timestamp=approval.approval_timestamp,
    mcp_server=approval.mcp_server,
    result='success' if result.get('status') in ['sent', 'published', 'success'] else 'failure',
    error=result.get('error'),
    error_code=result.get('error_code'),
    execution_duration_ms=execution_duration_ms,
    approval_request_id=approval.id,
    extra_fields={
        'message_id': result.get('message_id'),
        'post_id': result.get('post_id'),
        'post_url': result.get('post_url'),
        'screenshot_path': result.get('screenshot_path')
    }
    )
    # Logging succeeded - proceed with file movement
except Exception as log_error:
    # CRITICAL: If audit logging fails, do NOT move file
    print(f"CRITICAL ERROR: Audit logging failed: {log_error}")
    print(f"Approval file NOT moved - manual intervention required: {approval_file_path}")
    raise  # Re-raise to prevent file movement
)
```

### LinkedIn Posting Rules Enforcement (T054/T055)

Before executing LinkedIn posts, ALWAYS check posting rules:

```python
from AI_Employee.utils.linkedin_rules import LinkedInPostingRules, get_linkedin_metrics

# Initialize rules enforcer
rules = LinkedInPostingRules(
    logs_path=Path('AI_Employee/Logs'),
    max_posts_per_day=3,          # From Company_Handbook.md
    posting_schedule_start=9,      # 9 AM
    posting_schedule_end=17        # 5 PM
)

# Check if posting is allowed
can_post, block_reason = rules.can_post_now()

if not can_post:
    if 'rate_limit_daily_exceeded' in block_reason:
        # T054: Daily limit reached - queue for next day
        # Log rate_limit_daily_exceeded to audit
        logger.log_execution(
            action_type='linkedin_post',
            actor='system',
            target='LinkedIn',
            result='failure',
            error=block_reason,
            error_code='RATE_LIMIT_DAILY_EXCEEDED'
        )
        # Keep approval file in /Approved/ with queued status
        # Add queue_until timestamp to file

    elif 'outside_posting_schedule' in block_reason:
        # T055: Outside business hours - queue for next window
        next_window = rules.get_next_posting_window()
        # Keep approval file with estimated post time
        # Update approval file with queue status
```

**Daily Post Limit Check (T054)**:
```python
posts_today = rules.count_linkedin_posts_today()
max_posts = rules.max_posts_per_day  # 3 by default

if posts_today >= max_posts:
    # Queue post for tomorrow
    # Log: rate_limit_daily_exceeded
    # DO NOT execute
    # Keep in /Approved/ with status: queued
```

**Posting Schedule Check (T055)**:
```python
if not rules.is_within_posting_schedule():
    # Current time outside 9am-5pm
    next_window = rules.get_next_posting_window()
    # Queue post for next business hour
    # Keep in /Approved/ with estimated_post_time
```

**Queue Behavior**:
- Posts that violate rules are NOT rejected
- Posts remain in `/Approved/` with `status: queued`
- Add `queue_until: {ISO_TIMESTAMP}` to approval file
- Orchestrator re-checks queued posts on each cycle
- Execute when rules permit (next day or next business hour)

### Error Codes and Handling

Each MCP server returns specific error codes:

**Email MCP Error Codes**:
| Error Code | Description | Recovery |
|------------|-------------|----------|
| `SMTP_AUTH_FAILED` | Invalid credentials | Check SMTP_USERNAME/PASSWORD |
| `SMTP_CONNECTION_ERROR` | Cannot connect to SMTP | Check SMTP_HOST/PORT |
| `INVALID_RECIPIENT` | Bad email address | Verify recipient |
| `ATTACHMENT_TOO_LARGE` | >25MB attachments | Reduce attachment size |

**LinkedIn MCP Error Codes**:
| Error Code | Description | Recovery |
|------------|-------------|----------|
| `AUTH_EXPIRED` | Token expired (60 days) | Re-authenticate OAuth, create /Needs_Action/ notification |
| `RATE_LIMIT_EXCEEDED` | Too many posts | Wait and retry |
| `RATE_LIMIT_DAILY_EXCEEDED` | Daily limit (3) reached | Queue for next day |
| `OUTSIDE_POSTING_SCHEDULE` | Outside business hours | Queue for next window |
| `INVALID_CONTENT` | Policy violation | Review post content |
| `NETWORK_ERROR` | API unreachable | Check connectivity |

### LinkedIn AUTH_EXPIRED Handling (T057)

When LinkedIn MCP returns `AUTH_EXPIRED` error:

```python
from AI_Employee.utils.linkedin_rules import (
    handle_linkedin_auth_expired,
    check_linkedin_auth_error
)

# After MCP invocation returns error
result = linkedin_mcp.create_post(text=post_text, visibility='PUBLIC')

if result.get('status') == 'error':
    error_code = result.get('error_code')
    error_message = result.get('error')

    if check_linkedin_auth_error(error_code, error_message):
        # T057: Create notification in /Needs_Action/
        notification_path = handle_linkedin_auth_expired(
            needs_action_path=Path('AI_Employee/Needs_Action'),
            approval_file_path=approval_file_path,  # Keep in /Approved/
            error_message=error_message
        )

        # Log to audit
        logger.log_execution(
            action_type='linkedin_post',
            actor='system',
            target='LinkedIn',
            result='failure',
            error=error_message,
            error_code='AUTH_EXPIRED',
            extra_fields={
                'notification_created': str(notification_path),
                'retry_after_credential_refresh': True
            }
        )

        # DO NOT move approval file to /Rejected/
        # Keep in /Approved/ for retry after credentials are refreshed
```

**AUTH_EXPIRED Flow**:
1. Detect AUTH_EXPIRED from MCP response
2. Create notification in `/Needs_Action/` with refresh instructions
3. Log failure to audit with `retry_after_credential_refresh: true`
4. **Keep approval file in `/Approved/`** - do NOT reject
5. User refreshes credentials per notification instructions
6. Next orchestrator cycle retries the post

**Notification Contents**:
- Clear instructions for refreshing LinkedIn OAuth token
- Link to LinkedIn Developer Portal
- Required OAuth scopes
- Steps to update `.env` file
- Reference to failed approval file

**Playwright MCP Error Codes**:
| Error Code | Description | Recovery |
|------------|-------------|----------|
| `BROWSER_ERROR` | Chromium not installed | Run: playwright install chromium |
| `SELECTOR_NOT_FOUND` | Element not found | Verify CSS selector |
| `TIMEOUT` | Page load timeout | Increase PLAYWRIGHT_TIMEOUT_MS |
| `NAVIGATION_ERROR` | Page navigation failed | Verify URL |

### Handling MCP Errors in Execution Flow

```python
# Error handling pattern
def execute_approved_action(approval_file_path: Path) -> dict:
    from AI_Employee.models.approval_request import parse_approval_file
    from AI_Employee.utils.audit_logger import AuditLogger

    approval = parse_approval_file(approval_file_path)
    logs_path = Path('AI_Employee/Logs')
    logger = AuditLogger(logs_path)

    # 1. Check expiration
    if approval.created_timestamp and approval.approval_timestamp:
        age_hours = (datetime.now() - approval.created_timestamp).total_seconds() / 3600
        if age_hours > 24:
            # Move to /Rejected/, log expiration
            logger.log_execution(
                action_type=approval.action_type,
                actor='system',
                target=approval.target,
                result='failure',
                error='Approval request expired (>24 hours)',
                error_code='EXPIRED'
            )
            # Move file to /Rejected/
            return {'status': 'error', 'error': 'Expired', 'error_code': 'EXPIRED'}

    # 2. Health check MCP server
    health_result = _check_mcp_health(approval.mcp_server)
    if health_result['status'] != 'available':
        logger.log_execution(
            action_type=approval.action_type,
            actor='system',
            target=approval.target,
            mcp_server=approval.mcp_server,
            result='failure',
            error=f"MCP server unavailable: {health_result.get('error', 'Unknown')}",
            error_code='MCP_SERVER_UNAVAILABLE'
        )
        # Move file to /Rejected/
        # Create notification in /Needs_Action/
        return {'status': 'error', 'error_code': 'MCP_SERVER_UNAVAILABLE'}

    # 3. Validate parameters
    validation_error = _validate_parameters(approval)
    if validation_error:
        logger.log_execution(
            action_type=approval.action_type,
            actor='system',
            target=approval.target,
            result='failure',
            error=validation_error,
            error_code='PARAMETER_VALIDATION_FAILED'
        )
        # Move file to /Rejected/
        return {'status': 'error', 'error_code': 'PARAMETER_VALIDATION_FAILED'}

    # 4. Execute via MCP
    start_time = time.time()
    try:
        result = _invoke_mcp_tool(approval)
        execution_duration_ms = int((time.time() - start_time) * 1000)

        if result.get('status') in ['sent', 'published', 'success']:
            # Success: Log, move to /Done/
            logger.log_execution(
                action_type=approval.action_type,
                actor='claude-code',
                target=approval.target,
                parameters=approval.parameters,
                approval_status='approved',
                approval_by='user',
                mcp_server=approval.mcp_server,
                result='success',
                execution_duration_ms=execution_duration_ms,
                approval_request_id=approval.id
            )
            # Move file to /Done/
            # Update related plan file
            return result
        else:
            # Failure: Log, move to /Rejected/
            logger.log_execution(
                action_type=approval.action_type,
                actor='claude-code',
                target=approval.target,
                mcp_server=approval.mcp_server,
                result='failure',
                error=result.get('error'),
                error_code=result.get('error_code', 'MCP_TOOL_FAILED'),
                execution_duration_ms=execution_duration_ms
            )
            # Move file to /Rejected/
            # Create notification in /Needs_Action/
            return result

    except Exception as e:
        logger.log_execution(
            action_type=approval.action_type,
            actor='system',
            target=approval.target,
            mcp_server=approval.mcp_server,
            result='failure',
            error=str(e),
            error_code='UNKNOWN'
        )
        return {'status': 'error', 'error': str(e), 'error_code': 'UNKNOWN'}
```

### Credential Sanitization

**CRITICAL**: Always sanitize parameters before logging:

```python
from AI_Employee.utils.sanitizer import CredentialSanitizer

sanitizer = CredentialSanitizer()

# Sensitive keys automatically detected and redacted:
# password, token, api_key, secret, credential, auth, bearer,
# smtp_password, access_token, refresh_token, private_key,
# client_secret, authorization

# Token-like strings (>30 chars alphanumeric) are masked as "first4...last4"

# Example:
params = {
    'to': 'user@example.com',
    'smtp_password': 'secret123',  # Will be redacted
    'body': 'Hello world'
}

sanitized = sanitizer.sanitize(params)
# Result: {'to': 'user@example.com', 'smtp_password': '***REDACTED***', 'body': 'Hello world'}
```

### Update Related Plan File After Execution

After successful execution, update the related plan file:

```python
import re
from pathlib import Path
from datetime import datetime, timezone

def update_plan_file(plan_path: Path, action_description: str, result: dict):
    """Mark checkbox as completed and add execution note."""
    if not plan_path.exists():
        return

    content = plan_path.read_text(encoding='utf-8')
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')

    # Find matching unchecked checkbox containing the action description
    pattern = rf'- \[ \] (.*{re.escape(action_description[:30])}.*)'

    def replace_checkbox(match):
        original_text = match.group(1)
        execution_note = f"\n  - Executed: {timestamp}"
        if result.get('message_id'):
            execution_note += f"\n  - Message ID: {result['message_id']}"
        if result.get('post_url'):
            execution_note += f"\n  - Post URL: {result['post_url']}"
        return f"- [x] {original_text}{execution_note}"

    updated_content = re.sub(pattern, replace_checkbox, content, count=1)
    plan_path.write_text(updated_content, encoding='utf-8')
```

### Verifying MCP Server Availability

Before invoking MCP tools, check if servers are available:

1. Check environment variables are configured
2. Run health_check tool for the target MCP server
3. Verify returned status is 'available'
4. Log server status in Dashboard

If MCP server unavailable:
- Log error with error code `MCP_SERVER_UNAVAILABLE`
- Move approval to `/Rejected/` with "MCP server unavailable" note
- Create notification in `/Needs_Action/` with troubleshooting steps
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

