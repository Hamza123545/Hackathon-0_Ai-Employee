# Silver Tier Demo Script

**Purpose**: Demonstrate all 7 Silver tier user stories end-to-end  
**Target Time**: <45 minutes (per SC-020)  
**Prerequisites**: Silver tier fully set up and running

---

## Pre-Demo Checklist

- [ ] All watchers running via PM2: `pm2 status` shows all online
- [ ] ApprovalOrchestrator running: `pm2 status` shows approval-orchestrator online
- [ ] MCP servers configured: Email, LinkedIn (optional), Playwright
- [ ] Dashboard accessible: Open `Dashboard.md` in Obsidian
- [ ] Test email account ready: For sending test email
- [ ] LinkedIn account ready: For posting (if demonstrating LinkedIn)

---

## Demo Steps

### Step 1: Start Watchers (2 minutes)

**Action**: Verify all watchers are running

```bash
cd AI_Employee
pm2 status
```

**Expected Output**:
```
┌─────┬──────────────────────┬─────────┬─────────┬──────────┐
│ id  │ name                 │ status  │ restart │ uptime   │
├─────┼──────────────────────┼─────────┼─────────┼──────────┤
│ 0   │ gmail-watcher        │ online  │ 0       │ 2h 15m   │
│ 1   │ whatsapp-watcher     │ online  │ 0       │ 2h 15m   │
│ 2   │ linkedin-watcher     │ online  │ 0       │ 2h 15m   │
│ 3   │ approval-orchestrator│ online  │ 0       │ 2h 15m   │
└─────┴──────────────────────┴─────────┴─────────┴──────────┘
```

**Demonstrates**: User Story 5 (Scheduled 24/7 Operation with PM2)

**Checkpoint**: ✅ All watchers online

---

### Step 2: Trigger Test Email → Action Item Created (5 minutes)

**Action**: Send test email to monitored Gmail account

1. **Send Test Email**:
   - From: External email account
   - To: Your monitored Gmail account
   - Subject: "Demo: Action Item Test"
   - Body: "This is a test email for Silver tier demo. Please process this action item."

2. **Wait for Detection** (up to 5 minutes):
   - Gmail watcher checks every 5 minutes
   - Monitor `/Needs_Action/` folder

3. **Verify Action Item Created**:
   ```bash
   ls -la AI_Employee/Needs_Action/
   ```
   - Should see new file: `action-gmail-demo-*.md`

**Expected Action Item**:
```markdown
---
source: gmail
priority: medium
created: 2026-01-09T15:00:00Z
---
# Action Item: Demo: Action Item Test

**From**: sender@example.com
**Date**: 2026-01-09 15:00:00
**Subject**: Demo: Action Item Test

**Content**:
This is a test email for Silver tier demo. Please process this action item.
```

**Demonstrates**: User Story 1 (Multiple Watchers Monitor Different Sources)

**Checkpoint**: ✅ Action item created in `/Needs_Action/`

---

### Step 3: Process Action Item → Approval Request Generated (10 minutes)

**Action**: Use Claude Code to process action item

1. **Open Action Item**: Open the action item file in Obsidian
2. **Invoke Claude Code**: Use `@process-action-items` skill
3. **Claude Code Processing**:
   - Analyzes action item
   - Creates plan in `/Plans/`
   - Determines external action needed (email reply)
   - Creates approval request in `/Pending_Approval/`

4. **Verify Approval Request**:
   ```bash
   ls -la AI_Employee/Pending_Approval/
   ```
   - Should see: `APPROVAL_email_*.md`

**Expected Approval Request**:
```markdown
---
type: approval_request
action_type: email_send
target: sender@example.com
risk_level: low
mcp_server: email-mcp
mcp_tool: send_email
---
## Action Request

**Action Type**: Send email reply
**Target**: sender@example.com
**Subject**: Re: Demo: Action Item Test
**Body**: Thank you for your message. I have received and processed your request.
```

**Demonstrates**: User Story 2 (Human-in-the-Loop Approval Workflow)

**Checkpoint**: ✅ Approval request created in `/Pending_Approval/`

---

### Step 4: Approve Request → Move to /Approved/ (2 minutes)

**Action**: Manual approval (human review)

1. **Review Approval Request**: Open approval file in Obsidian
2. **Review Details**: Check action type, target, parameters, risk level
3. **Approve**: Move file from `/Pending_Approval/` to `/Approved/`
   ```bash
   mv AI_Employee/Pending_Approval/APPROVAL_email_*.md AI_Employee/Approved/
   ```

4. **Verify Moved**:
   ```bash
   ls -la AI_Employee/Approved/
   ```

**Demonstrates**: User Story 2 (Human-in-the-Loop Approval Workflow)

**Checkpoint**: ✅ Approval file moved to `/Approved/`

---

### Step 5: Execute via MCP → Email Sent, Audit Logged (5 minutes)

**Action**: ApprovalOrchestrator detects and executes approved action

1. **Wait for Execution** (up to 1 minute):
   - ApprovalOrchestrator checks `/Approved/` every 60 seconds
   - Detects new file
   - Executes via email-mcp

2. **Verify Execution**:
   - **Email Sent**: Check recipient's inbox for reply email
   - **File Moved**: Check `/Done/` folder
     ```bash
     ls -la AI_Employee/Done/
     ```
   - **Audit Log Entry**: Check `/Logs/YYYY-MM-DD.json`
     ```bash
     cat AI_Employee/Logs/2026-01-09.json | jq '.entries[-1]'
     ```

**Expected Audit Log Entry**:
```json
{
  "entry_id": "uuid-v4",
  "timestamp": "2026-01-09T15:10:00Z",
  "action_type": "email_send",
  "actor": "claude-code",
  "target": "sender@example.com",
  "parameters": {
    "subject": "Re: Demo: Action Item Test",
    "body_preview": "Thank you for your message..."
  },
  "approval_status": "approved",
  "approval_by": "user",
  "mcp_server": "email-mcp",
  "result": "success",
  "execution_duration_ms": 1234
}
```

**Demonstrates**: 
- User Story 3 (External Actions via MCP Servers)
- User Story 6 (Comprehensive Audit Logging)

**Checkpoint**: ✅ Email sent, audit logged, file moved to `/Done/`

---

### Step 6: Check Dashboard → Verify All Metrics Updated (5 minutes)

**Action**: View Dashboard to see Silver tier metrics

1. **Open Dashboard**: `Dashboard.md` in Obsidian
2. **Verify Silver Tier Metrics Section**:
   - **Pending Approvals**: Should show count (may be 0 if all processed)
   - **MCP Server Health**: Should show email-mcp as ✅ available
   - **All Watchers Status**: Should show all watchers as ✅ online
   - **Recent Audit Entries**: Should show email_send entry with ✅ success
   - **Data Freshness**: Should show <5 minutes

3. **Verify Metrics**:
   - Watcher uptime: Shows hours/minutes
   - Items detected today: Shows count
   - Recent audit entries: Shows last 10 actions
   - MCP server status: Shows health and last action

**Expected Dashboard Section**:
```markdown
## Silver Tier Metrics

**Last Updated**: 2026-01-09 15:15:00 - ✅ Fresh (<5 minutes)

### Pending Approvals
**Pending**: 0 | **Oldest**: N/A

### MCP Server Health
| Server | Status | Last Success | Errors |
|--------|--------|--------------|--------|
| email-mcp | ✅ available | 2026-01-09 15:10 | 0 |

### All Watchers Status
| Watcher | Status | Last Check | Detected Today | Uptime |
|---------|--------|------------|----------------|--------|
| gmail | ✅ online | 2026-01-09 15:15 | 1 | 2h 20m |

### Recent Audit Entries (Last 10)
| Time | Action | Target | Result | Approval |
|------|--------|--------|--------|----------|
| 5m ago | email_send | sender@example.com | ✅ success | approved |
```

**Demonstrates**: User Story 7 (Enhanced Dashboard for Silver Tier)

**Checkpoint**: ✅ Dashboard shows all Silver metrics

---

## Optional: LinkedIn Post Demo (10 minutes)

**Note**: Only if LinkedIn MCP is configured

### Step 7: LinkedIn Post Workflow

1. **Trigger LinkedIn Post Request**:
   - Create action item with LinkedIn posting keywords
   - Process with Claude Code
   - Approval request created in `/Pending_Approval/`

2. **Approve LinkedIn Post**:
   - Review post content
   - Move to `/Approved/`

3. **Execute Post**:
   - ApprovalOrchestrator executes via linkedin-mcp
   - Post appears on LinkedIn profile
   - Audit log entry created with post_url

4. **Verify**:
   - Check LinkedIn profile for new post
   - Check Dashboard shows "Posts this week: 1"
   - Check audit log has post_url

**Demonstrates**: User Story 4 (LinkedIn Social Media Automation)

---

## Demo Summary

**Total Time**: ~30-45 minutes (depending on optional LinkedIn demo)

**User Stories Demonstrated**:
- ✅ US1: Multiple Watchers (Gmail, WhatsApp, LinkedIn)
- ✅ US2: HITL Approval Workflow (approval request → review → approve)
- ✅ US3: External Actions via MCP (email sent via email-mcp)
- ✅ US4: LinkedIn Automation (optional)
- ✅ US5: PM2 Process Management (watchers running 24/7)
- ✅ US6: Audit Logging (all actions logged with sanitization)
- ✅ US7: Enhanced Dashboard (all Silver metrics displayed)

**Success Criteria Met**:
- ✅ SC-020: All 7 user stories demonstrated in <45 minutes
- ✅ SC-011: External action executed within 10 minutes of approval
- ✅ SC-014: 100% audit logging with all required fields
- ✅ SC-016: Dashboard displays Silver metrics with <5min freshness

---

## Troubleshooting During Demo

**If action item not created**:
- Check Gmail watcher logs: `pm2 logs gmail-watcher`
- Verify email arrived in monitored inbox
- Wait up to 5 minutes (check interval)

**If approval not executed**:
- Check ApprovalOrchestrator logs: `pm2 logs approval-orchestrator`
- Verify file is in `/Approved/` (not `/Pending_Approval/`)
- Check email-mcp health: Verify SMTP credentials

**If Dashboard not updated**:
- Check watcher status: `pm2 status`
- Verify Dashboard.md is writable
- Check last_updated timestamp in Dashboard

---

**Demo Complete** ✅

