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

**Server Name**: `email` (or `gmail-mcp`)

**Configuration**:
- Command: `node` or `python` (depends on server implementation)
- Args: Server-specific (e.g., `["/path/to/email-mcp/index.js"]`)
- Environment Variables:
  - `SMTP_HOST`: SMTP server hostname
  - `SMTP_USER`: SMTP username (or Gmail API credentials)
  - `SMTP_PASS`: SMTP password (or Gmail OAuth token)
  - `GMAIL_API_KEY`: If using Gmail API

**Available Tools**:
- `send_email`: Send email with subject, body, attachments
- `send_reply`: Reply to existing email thread
- `draft_email`: Create draft without sending

**Usage Example**:
```json
{
  "name": "email",
  "command": "node",
  "args": ["/path/to/email-mcp/index.js"],
  "env": {
    "SMTP_HOST": "${SMTP_HOST}",
    "SMTP_USER": "${SMTP_USER}"
  }
}
```

### LinkedIn MCP Server (Social Media)

**Server Name**: `linkedin`

**Configuration**:
- Command: `python` or `node` (depends on implementation)
- Environment Variables:
  - `LINKEDIN_API_KEY`: LinkedIn API credentials
  - `LINKEDIN_ACCESS_TOKEN`: OAuth access token

**Available Tools**:
- `create_post`: Create new LinkedIn post
- `like_post`: Like an existing post
- `send_message`: Send direct message

**Approval Required**: Yes (all social media actions)

### Browser/Playwright MCP Server

**Server Name**: `browser` or `playwright-mcp`

**Configuration**:
- Command: `npx`
- Args: `["-y", "@modelcontextprotocol/server-puppeteer"]`

**Available Tools**:
- `navigate`: Navigate to URL
- `click`: Click element
- `type`: Type text
- `fill_form`: Fill form fields
- `screenshot`: Take screenshot

**Approval Required**: Yes (all browser actions)

## Approval Thresholds (Silver Tier)

### Auto-Approve Criteria

Actions meeting ALL criteria below can be auto-approved:

**Email Replies**:
- Recipient is in "Known Contacts" list
- Email body < 100 words
- No attachments
- Subject does not contain sensitive keywords
- Below $0 transaction value (not a payment)

**Social Media**:
- Auto-approve: Never (all social media posts require approval)

**Payments**:
- Auto-approve: Never (all payments require approval)

**Browser Actions**:
- Auto-approve: Never (all browser actions require approval)

### Approval Required

**Always require approval for**:
- Email to new contacts (not in Known Contacts list)
- Email with attachments
- Email longer than 100 words
- All social media posts (LinkedIn, Twitter, Facebook)
- All payments and financial transactions
- All browser automation actions
- Actions exceeding rate limits
- Actions flagged as high priority

### Permission Boundaries

| Action Category | Auto-Approve Threshold | Always Require Approval |
|----------------|----------------------|------------------------|
| Email replies | Known contact, < 100 words, no attachments | New contacts, bulk sends, attachments |
| Social media | Never | All posts, replies, DMs |
| Payments | Never | All transactions |
| Browser actions | Never | All navigations, clicks, form fills |
| File operations | Create, read (vault only) | Delete, move outside vault |

## Audit Logging (Silver Tier - Mandatory)

### Log Location

All actions logged to: `/Logs/YYYY-MM-DD.json`

### Required Log Fields

- `timestamp`: ISO 8601 timestamp
- `action_type`: Type of action (send_email, post_linkedin, etc.)
- `actor`: Who performed action (claude_code, human, watcher)
- `target`: Recipient/target of action
- `parameters`: Action parameters (sanitized - no credentials)
- `approval_status`: approved, auto_approved, rejected
- `mcp_server`: MCP server name (if applicable)
- `mcp_tool`: MCP tool name (if applicable)
- `result`: success, failed, dry_run
- `error`: Error details (if failed)

### Log Retention

- Minimum retention: 90 days
- Archive old logs: Move to `/Logs/Archive/YYYY-MM/`
- Never delete logs containing payment or financial transactions

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
