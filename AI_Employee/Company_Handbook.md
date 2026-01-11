---
version: "1.0.0"
last_updated: 2026-01-09T00:00:00Z
---

# Company Handbook

This document defines the rules and configuration for the Personal AI Employee system.

## Watcher Configuration

### Check Interval
- Default: 60 seconds
- Environment variable: `CHECK_INTERVAL`

### Watcher Type
- Options: `gmail` or `filesystem`
- Environment variable: `WATCHER_TYPE`

### Watch Paths
- Filesystem watcher: Set `WATCH_PATH` to the folder to monitor
- Gmail watcher: Uses INBOX label by default

## Priority Rules

### High Priority
Items marked as high priority include:
- Subject contains: "URGENT", "ASAP", "Critical", "Emergency", "Immediate"
- Time-sensitive requests with explicit deadlines
- From VIP contacts (customize below)

### Medium Priority
Default priority for:
- Standard business emails from known contacts
- Documents in monitored folders
- Regular work requests

### Low Priority
- Newsletters and marketing emails
- Automated notifications (no-reply senders)
- Digest emails
- Non-actionable informational updates

## Processing Rules

### Email Processing
1. Extract subject, sender, date, and body snippet
2. Determine priority based on rules above
3. Create action file in /Needs_Action
4. Include full email content in action file

### File Processing
1. Extract filename, type, creation date
2. Assign medium priority by default
3. Create action file in /Needs_Action
4. Include file path and content preview

## Plan Generation Rules

### Required Sections
Every generated plan must include:
- **Context**: Always include source reference with Obsidian link
- **Analysis**: Apply priority rules and categorization from this handbook
- **Action Plan**: Minimum 3 actionable checkboxes with clear, specific tasks

### Action Item Format
- Use imperative mood ("Review document", not "Document should be reviewed")
- Include deadline if determinable from source
- Group by timeline (Immediate Actions, Follow-up Actions)
- Each action should be specific and measurable

### Checkbox Guidelines
- [ ] Good: "Send reply email to client@example.com by end of day"
- [ ] Bad: "Handle email"

## Approved Contacts

VIP contacts that receive automatic high priority:
- (Add email addresses here)

Known contacts (medium priority):
- (Add email addresses here)

## Error Handling

### Common Errors
| Error | Resolution |
|-------|------------|
| Gmail auth expired | Delete token.pickle and restart watcher |
| Vault inaccessible | Check VAULT_PATH environment variable |
| Rate limited | Wait 5 minutes and retry |
| File permission denied | Check folder permissions |

### Recovery Procedures
1. If watcher crashes, restart with `cd AI_Employee && uv run python run_watcher.py`
2. If duplicate items appear, check .processed_ids.json for corruption (should be valid JSON)
3. If Dashboard not updating, verify watcher is running and check CHECK_INTERVAL setting
4. To reset duplicate tracking, delete .processed_ids.json and restart watcher

## MCP Server Configuration (Silver Tier)

### Email MCP Server

**Status**: ✅ Enabled by default

**Server Name**: `email-mcp`

**Configuration**:
- Implementation: Python FastMCP server (`AI_Employee/mcp_servers/email_mcp.py`)
- Environment Variables (required in `.env`):
  - `SMTP_HOST`: SMTP server hostname (e.g., `smtp.gmail.com`)
  - `SMTP_PORT`: SMTP port (e.g., `587` for TLS)
  - `SMTP_USERNAME`: SMTP username (your email address)
  - `SMTP_PASSWORD`: SMTP password or app-specific password
  - `FROM_ADDRESS`: Sender email address
  - `SMTP_USE_TLS`: `true` or `false` (default: `true`)

**Available Tools**:
- `send_email`: Send email with subject, body, optional attachments
- `health_check`: Check SMTP server connectivity and authentication

**Error Codes**:
- `SMTP_AUTH_FAILED`: Invalid credentials → use app-specific password
- `SMTP_CONNECTION_ERROR`: Cannot connect to SMTP server
- `INVALID_RECIPIENT`: Bad email address format
- `ATTACHMENT_TOO_LARGE`: Attachment exceeds 25MB limit

### LinkedIn MCP Server

**Status**: ✅ Enabled (requires OAuth token)

**Server Name**: `linkedin-mcp`

**Configuration**:
- Implementation: Python FastMCP server (`AI_Employee/mcp_servers/linkedin_mcp.py`)
- Environment Variables (required in `.env`):
  - `LINKEDIN_ACCESS_TOKEN`: OAuth 2.0 access token (get from LinkedIn Developer Portal)
  - `LINKEDIN_PERSON_URN`: Your LinkedIn person URN (e.g., `urn:li:person:12345`)
  - `LINKEDIN_API_VERSION`: API version (default: `202601`)

**Available Tools**:
- `create_post`: Create new LinkedIn post with content and visibility
- `health_check`: Check LinkedIn API connectivity and token validity

**Error Codes**:
- `AUTH_EXPIRED`: OAuth token expired → refresh token
- `RATE_LIMIT_EXCEEDED`: Too many requests → reduce posting frequency
- `INVALID_CONTENT`: Post content violates LinkedIn policies

### Playwright/Browser MCP Server

**Status**: ✅ Enabled (for WhatsApp watcher and browser automation)

**Server Name**: `playwright-mcp`

**Configuration**:
- Implementation: Python FastMCP server (`AI_Employee/mcp_servers/playwright_mcp.py`)
- Environment Variables (optional):
  - `SCREENSHOT_DIR`: Directory for screenshots (default: `Logs/screenshots/`)
  - `PLAYWRIGHT_TIMEOUT_MS`: Browser timeout in milliseconds (default: `30000`)

**Available Tools**:
- `browser_action`: Navigate, click, type, fill forms
- `take_screenshot`: Capture browser screenshot
- `health_check`: Verify Playwright and Chromium installation

**Error Codes**:
- `BROWSER_ERROR`: Chromium not installed → run `playwright install chromium`
- `SELECTOR_NOT_FOUND`: Element not found on page
- `TIMEOUT`: Page load timeout exceeded
- `NAVIGATION_ERROR`: Page navigation failed

## Approval Workflow (Silver Tier)

### Auto-Approval Configuration

**Default**: ⚠️ **Disabled** (all actions require manual approval)

**To Enable Auto-Approval**:
Set `auto_approval_enabled: true` in this handbook and configure thresholds below.

### Auto-Approve Criteria

Actions meeting ALL criteria below can be auto-approved (if enabled):

**Email Replies**:
- Recipient is in "Known Contacts" list (see Approved Contacts section)
- Email body < 100 words
- No attachments
- Subject does not contain sensitive keywords (payment, invoice, urgent, etc.)
- Risk level: `low` (as determined by Claude Code)

**Social Media**:
- Auto-approve: ❌ **Never** (all social media posts require manual approval)

**Payments**:
- Auto-approve: ❌ **Never** (all payments require manual approval)

**Browser Actions**:
- Auto-approve: ❌ **Never** (all browser actions require manual approval)

### Approval Required

**Always require manual approval for**:
- Email to new contacts (not in Known Contacts list)
- Email with attachments
- Email longer than 100 words
- All social media posts (LinkedIn, Twitter, Facebook)
- All payments and financial transactions
- All browser automation actions
- Actions exceeding rate limits
- Actions flagged as high priority or high risk
- Actions with risk_level: `high` or `medium`

### Approval Workflow Steps

1. **Detection**: Watcher detects item → action item created in `/Needs_Action/`
2. **Processing**: Claude Code processes action → creates plan and approval request
3. **Approval Request**: File created in `/Pending_Approval/` with risk assessment
4. **Human Review**: User reviews and moves file to `/Approved/` or `/Rejected/`
5. **Execution**: ApprovalOrchestrator detects approved file → executes via MCP server
6. **Audit Logging**: All executions logged to `/Logs/YYYY-MM-DD.json`
7. **Completion**: File moved to `/Done/` with execution metadata

### Permission Boundaries

| Action Category | Auto-Approve Threshold | Always Require Approval |
|----------------|----------------------|------------------------|
| Email replies | Known contact, < 100 words, no attachments, low risk | New contacts, bulk sends, attachments, high risk |
| Social media | ❌ Never | All posts, replies, DMs |
| Payments | ❌ Never | All transactions |
| Browser actions | ❌ Never | All navigations, clicks, form fills |
| File operations | Create, read (vault only) | Delete, move outside vault |

## Audit Logging (Silver Tier - Mandatory)

### Status
✅ **Enabled** - All external actions are logged

### Log Location

All actions logged to: `/Logs/YYYY-MM-DD.json` (daily JSON files)

### Required Log Fields

- `entry_id`: Unique UUID v4 identifier
- `timestamp`: ISO 8601 timestamp in UTC
- `action_type`: Type of action (`email_send`, `linkedin_post`, `browser_action`, `watcher_detection`, etc.)
- `actor`: Who performed action (`claude-code`, `user`, `system`)
- `target`: Recipient/target of action (email address, URL, etc.)
- `parameters`: Action parameters (**sanitized** - credentials removed/masked)
- `approval_status`: `approved`, `auto_approved`, `rejected`, `not_required`
- `approval_by`: Who approved (`user`, `auto`, `system`, or `null`)
- `approval_timestamp`: When approval was granted (ISO 8601)
- `mcp_server`: MCP server name (e.g., `email-mcp`, `linkedin-mcp`)
- `result`: `success`, `failure`, `partial`
- `error`: Error message (if failed)
- `error_code`: Machine-readable error code (if failed)
- `execution_duration_ms`: Execution time in milliseconds
- `approval_request_id`: UUID of original approval request (if applicable)

### Credential Sanitization

✅ **Enabled** - All credentials are automatically sanitized before logging

**Sanitized Fields**:
- `password`, `smtp_password`, `api_key`, `access_token`, `refresh_token`
- `token`, `secret`, `credential`, `auth`, `bearer`, `authorization`
- Token-like strings (>30 chars alphanumeric) are masked: `{first4}...{last4}`

**Verification**: Run `python -m pytest AI_Employee/tests/test_audit_logging.py::TestAuditLogging::test_zero_credential_leaks_sample_100_entries` to verify zero credential leaks.

### Log Retention

- **Retention Period**: 90 days (configurable via `AUDIT_LOG_RETENTION_DAYS` environment variable)
- **Archive Policy**: Logs older than retention period are compressed to `.gz` format
- **Cleanup**: Automatic cleanup runs via PM2 cron_restart or manual execution
- **Never Delete**: Logs containing payment or financial transactions are preserved indefinitely

### Log File Format

Each daily log file contains:
```json
{
  "entries": [
    {
      "entry_id": "uuid-v4",
      "timestamp": "2026-01-09T15:30:00.123456Z",
      "action_type": "email_send",
      "actor": "claude-code",
      "target": "recipient@example.com",
      "parameters": {
        "subject": "Test Email",
        "body_preview": "Test body content..."
      },
      "approval_status": "approved",
      "approval_by": "user",
      "approval_timestamp": "2026-01-09T15:25:00Z",
      "mcp_server": "email-mcp",
      "result": "success",
      "error": null,
      "execution_duration_ms": 1234,
      "approval_request_id": "uuid-of-approval"
    }
  ]
}
```

## Bronze Tier Limitations

**Bronze tier operation** (read-only):
- All plans require manual review and execution
- No automatic email sending
- No external API calls for actions
- Human-in-the-loop for all operations

## Silver Tier Capabilities

**Silver tier operation** (with external actions via approval):
- Plans can specify external actions (email, social media, payments)
- Approval requests created in `/Pending_Approval/` for sensitive actions
- MCP servers execute approved actions
- Mandatory audit logging for all external actions
- Human-in-the-loop approval required for sensitive operations

## LinkedIn Posting Rules (Silver Tier)

### Posting Limits and Schedule

| Setting | Value | Description |
|---------|-------|-------------|
| `max_posts_per_day` | 3 | Maximum LinkedIn posts allowed per calendar day |
| `posting_schedule_start` | 09:00 | Start of posting window (business hours) |
| `posting_schedule_end` | 17:00 | End of posting window (business hours) |
| `posting_timezone` | local | Timezone for schedule enforcement |
| `content_length_max` | 280 | Maximum characters for post content (excluding hashtags) |
| `rate_limit_delay_seconds` | 5 | Minimum delay between consecutive posts |

### Approved Topics

Posts should align with these approved topics:
- **AI**: Artificial intelligence, machine learning, LLMs, Claude, ChatGPT
- **Automation**: Workflow automation, process optimization, productivity tools
- **Business Innovation**: Digital transformation, tech trends, startup insights

### Standard Hashtags

Default hashtags to include (up to 5 per post):
- `#AI`
- `#Automation`
- `#Innovation`
- `#TechTrends`
- `#DigitalTransformation`

### Auto-Approval Threshold

LinkedIn posts may be auto-approved if ALL conditions are met:
- `auto_approval_enabled`: false (default - all posts require manual approval)
- Post content length < 200 characters
- No external links included
- Content matches approved topics
- Within daily post limit (< max_posts_per_day)

**Note**: Even when auto-approval is enabled, LinkedIn posts are considered `risk_level: low` only if they meet the above criteria. Posts with links or longer content are `risk_level: medium`.

### LinkedIn Post Keywords

Action items containing these keywords may trigger LinkedIn post generation:
- `announce`, `share`, `post about`, `publish`, `broadcast`
- `linkedin update`, `social media`, `professional network`
- `thought leadership`, `industry insight`

### Queue Behavior

When posting limits or schedule are violated:
- Posts are queued in `/Pending_Approval/` with status `queued`
- Queue position and estimated post time are added to approval file
- Queued posts execute automatically when limits reset (next day) or schedule resumes (next business hour)
- `rate_limit_daily_exceeded` logged to audit when daily limit reached

### Credential Expiration

LinkedIn OAuth tokens expire after 60 days. When `AUTH_EXPIRED` error detected:
1. Create notification in `/Needs_Action/` with refresh instructions
2. Post remains in `/Approved/` for retry after credential refresh
3. Dashboard shows LinkedIn MCP status as "❌ AUTH_EXPIRED"
4. All queued posts are preserved until token is refreshed
