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

## Bronze Tier Limitations

This handbook is configured for Bronze tier operation:
- All plans require manual review and execution
- No automatic email sending
- No external API calls for actions
- Human-in-the-loop for all operations
