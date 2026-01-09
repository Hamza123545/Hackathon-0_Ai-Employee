# Process Action Items – Examples

These examples demonstrate how the `process-action-items` Skill processes different types of action items in the Personal AI Employee system for both Bronze and Silver tiers.

---

## Example 1: Processing Gmail Action Item

### Input: Action Item File

**File**: `/Needs_Action/EMAIL_20260109_12345.md`

```markdown
---
type: email
from: client@example.com
subject: Invoice Request - January 2026
received: 2026-01-09T10:15:00Z
priority: high
status: pending
source_id: EMAIL_20260109_12345
---

## Content
Hi,

Could you please send me the invoice for January 2026? We need it for our accounting records.

Thanks,
John Doe
Client Company

## Metadata
- Thread ID: thread_abc123
- Message ID: msg_xyz789
- Label: INBOX
```

### Skill Execution

1. **Reads** the action item file
2. **Reads** `Company_Handbook.md` for processing rules
3. **Analyzes**:
   - Type: Email request
   - Priority: High (explicitly set)
   - Action needed: Generate and send invoice
   - Client: Known contact (from Company_Handbook.md)

### Output: Generated Plan

**File**: `/Plans/PLAN_invoice_request_2026-01-09.md`

```markdown
---
type: action_plan
source: EMAIL
created: 2026-01-09T10:30:00Z
priority: HIGH
status: pending
original_file: Needs_Action/EMAIL_20260109_12345.md
---

# Action Plan: Invoice Request - Client Company (January 2026)

## Source Information
- **Type**: email
- **From**: client@example.com (John Doe, Client Company)
- **Received**: 2026-01-09T10:15:00Z
- **Original Item**: `/Needs_Action/EMAIL_20260109_12345.md`

## Analysis
Client has requested the January 2026 invoice for accounting purposes. This is a standard billing request from an established client. The request is time-sensitive (needed for accounting records) and should be processed promptly.

## Recommended Actions
- [ ] Verify client account details in Company_Handbook.md
- [ ] Calculate January 2026 invoice amount based on services rendered
- [ ] Generate invoice document (PDF format)
- [ ] Review invoice for accuracy (dates, amounts, line items)
- [ ] Prepare email response with invoice attachment
- [ ] **APPROVAL REQUIRED**: Review and send email (Bronze tier: manual send)

## Context
- Client: Client Company (Established account)
- Invoice Period: January 2026
- Purpose: Accounting records
- Response Template: Invoice delivery (from Company_Handbook.md)

## Notes
- Standard billing request - no special handling required
- Client is known contact - can use standard invoice template
- For Bronze tier: Email sending requires manual action

## Next Steps
1. Human reviews this plan
2. Generates invoice using standard template
3. Manually sends email with invoice attachment
4. Updates plan status to "completed" after sending
```

### Dashboard Update

**File**: `Dashboard.md` (updated section)

```markdown
## Recent Activity
- `2026-01-09T10:30:00Z` Processed: Invoice request from client@example.com
- `2026-01-09T10:30:00Z` Created Plan: Invoice Request - Client Company (January 2026)
- `2026-01-09T09:45:00Z` Processed: Weekly report file drop
- `2026-01-09T09:45:00Z` Created Plan: Process Weekly Sales Report
```

### Archive

**File**: `/Done/EMAIL_20260109_12345_20260109T103000Z.md`

```markdown
---
type: email
from: client@example.com
subject: Invoice Request - January 2026
received: 2026-01-09T10:15:00Z
priority: high
status: processed
source_id: EMAIL_20260109_12345
processed: 2026-01-09T10:30:00Z
plan_file: Plans/PLAN_invoice_request_2026-01-09.md
---

[Original content preserved...]
```

---

## Example 2: Processing File System Action Item

### Input: Action Item File

**File**: `/Needs_Action/FILE_expense_report_2026-01-08.csv.md`

```markdown
---
type: file_drop
from: /DropFolder/expense_report_2026-01-08.csv
subject: expense_report_2026-01-08.csv
received: 2026-01-09T08:00:00Z
priority: auto
status: pending
source_id: FILE_expense_report_20260108
---

## Content
New file dropped in watch folder: expense_report_2026-01-08.csv
File size: 45.2 KB
File type: CSV (text/csv)

## Metadata
- Original path: /DropFolder/expense_report_2026-01-08.csv
- Watched folder: /DropFolder
- File hash: sha256_abc123def456
```

### Skill Execution

1. **Reads** the action item file
2. **Reads** `Company_Handbook.md` for file processing rules
3. **Analyzes**:
   - Type: CSV file drop
   - Priority: Medium (expense reports are routine)
   - Action needed: Process expense report, categorize expenses
   - File type: CSV (structured data)

### Output: Generated Plan

**File**: `/Plans/PLAN_expense_report_2026-01-09.md`

```markdown
---
type: action_plan
source: FILE
created: 2026-01-09T08:15:00Z
priority: MEDIUM
status: pending
original_file: Needs_Action/FILE_expense_report_2026-01-08.csv.md
---

# Action Plan: Process Expense Report (2026-01-08)

## Source Information
- **Type**: file_drop
- **From**: /DropFolder/expense_report_2026-01-08.csv
- **Received**: 2026-01-09T08:00:00Z
- **Original Item**: `/Needs_Action/FILE_expense_report_2026-01-08.csv.md`

## Analysis
Expense report CSV file has been dropped in the watch folder. This appears to be a routine monthly expense report that needs processing, categorization, and potentially integration into accounting records. CSV format suggests structured data that can be programmatically processed.

## Recommended Actions
- [ ] Read and parse CSV file from /DropFolder/
- [ ] Validate CSV structure (columns, data types)
- [ ] Categorize expenses according to Company_Handbook.md categories
- [ ] Flag any unusual or high-value expenses for review
- [ ] Generate summary report of expenses
- [ ] Store processed data in appropriate location (vault or accounting system)
- [ ] Archive original CSV file after processing

## Context
- File Type: CSV (structured data)
- Processing Rules: See Company_Handbook.md → Expense Processing
- Expected Columns: Date, Amount, Category, Description, Receipt
- Archive Location: /Accounting/Expenses/2026/01/

## Notes
- Standard monthly expense report - routine processing
- For Bronze tier: Manual review of categorization recommended
- High-value items (>$500) should be flagged for approval

## Next Steps
1. Human reviews this plan
2. Processes CSV file (manual or with script)
3. Reviews categorized expenses
4. Archives file after processing
5. Updates plan status to "completed"
```

---

## Example 3: Error Handling - Malformed Action Item

### Input: Malformed Action Item

**File**: `/Needs_Action/EMAIL_broken_001.md`

```markdown
---
type: email
from: unknown@example.com
subject: Test Email
received: invalid-date
status: pending
# Missing required fields, invalid timestamp
---

## Content
This is a test email with malformed frontmatter.
```

### Skill Execution

1. **Attempts to read** the action item file
2. **Detects** malformed frontmatter (invalid timestamp)
3. **Handles error**:
   - Logs error: "Failed to parse frontmatter in EMAIL_broken_001.md: Invalid timestamp format"
   - Skips processing (doesn't crash)
   - Creates error entry in Dashboard

### Dashboard Update (Error Entry)

```markdown
## System Health
- **Watchers**: running
- **Vault Access**: accessible
- **Last Check**: 2026-01-09T11:00:00Z
- **Processing Errors**: 1
  - `2026-01-09T11:00:00Z` ERROR: Failed to process EMAIL_broken_001.md - Invalid frontmatter timestamp. Manual review required.
```

### Result

- File remains in `/Needs_Action/` for manual review
- Other action items continue processing normally
- Error logged but doesn't block system operation

---

## Example 4: Duplicate Detection

### Input: Duplicate Action Item

**File**: `/Needs_Action/EMAIL_20260109_12345_duplicate.md`

```markdown
---
type: email
from: client@example.com
subject: Invoice Request - January 2026
received: 2026-01-09T10:20:00Z
priority: high
status: pending
source_id: EMAIL_20260109_12345
---

## Content
[Same content as Example 1]
```

### Skill Execution

1. **Reads** the action item file
2. **Detects** duplicate by comparing `source_id` (EMAIL_20260109_12345)
3. **Checks** if plan already exists: `PLAN_invoice_request_2026-01-09.md`
4. **Handles duplicate**:
   - Logs: "Skipped duplicate action item: EMAIL_20260109_12345 (already processed)"
   - Skips processing
   - Optionally adds note to existing plan

### Existing Plan (Updated with Note)

```markdown
## Notes
- Standard billing request - no special handling required
- Client is known contact - can use standard invoice template
- For Bronze tier: Email sending requires manual action
- **Duplicate detected**: Similar request received at 2026-01-09T10:20:00Z, skipped processing
```

---

## Example 5: Missing Company_Handbook.md

### Scenario

`Company_Handbook.md` doesn't exist in the vault.

### Skill Execution

1. **Attempts to read** `Company_Handbook.md`
2. **Detects** file missing
3. **Handles gracefully**:
   - Logs warning: "Company_Handbook.md not found, using default priority rules"
   - Uses default rules:
     - HIGH: Keywords "urgent", "asap", "important", "deadline"
     - MEDIUM: Standard business requests
     - LOW: Newsletters, automated messages
4. **Creates plan** with note about missing handbook

### Generated Plan (with Note)

```markdown
## Notes
- **WARNING**: Company_Handbook.md not found in vault
- Used default priority classification rules
- Recommend creating Company_Handbook.md with custom processing rules
- Priority determined by keyword matching only
```

---

These examples demonstrate the skill's robustness in handling various scenarios while maintaining consistency and reliability in Bronze tier action item processing.

---

## Example 6: Silver Tier - Email Action with Approval Request

### Input: Action Item File

**File**: `/Needs_Action/EMAIL_20260109_67890.md`

```markdown
---
type: email
from: newclient@startup.com
subject: Urgent: Need proposal by Friday
received: 2026-01-09T14:30:00Z
priority: high
status: pending
source_id: EMAIL_20260109_67890
---

## Content

Hi there,

We're a startup and need a proposal for your services. Can you send it by Friday? We're in a rush to make a decision.

Best,
Sarah Chen
New Startup Inc.
```

### Skill Execution (Silver Tier)

1. **Reads** the action item file
2. **Reads** `Company_Handbook.md` for rules and approval thresholds
3. **Analyzes**:
   - Type: Email request requiring reply
   - Priority: High (urgent deadline)
   - Action needed: Send email reply with proposal
   - Approval required: YES (email to new contact, exceeds auto-approve threshold)
4. **Creates** plan file in `/Plans/`
5. **Creates** approval request in `/Pending_Approval/` (Silver tier)
6. **Logs** approval request to audit log
7. **Updates** Dashboard.md

### Output: Generated Plan (with Approval Reference)

**File**: `/Plans/PLAN_proposal_request_2026-01-09.md`

```markdown
---
type: action_plan
source: EMAIL
created: 2026-01-09T14:35:00Z
priority: HIGH
status: pending_approval
approval_request: APPROVAL_email_proposal_newclient_2026-01-09.md
---

# Action Plan: Send Proposal to New Startup Inc.

## Source Information
- From: newclient@startup.com (New Startup Inc.)
- Received: 2026-01-09T14:30:00Z
- Original Item: `/Needs_Action/EMAIL_20260109_67890.md`

## Analysis

High priority request from new client requiring urgent proposal. Deadline: Friday. This is a new contact, so approval required before sending email reply.

## Recommended Actions

- [x] Identify client: New Startup Inc. (newclient@startup.com)
- [x] Determine proposal scope: Review request details
- [ ] Generate proposal document
- [ ] **APPROVAL REQUIRED**: Send email with proposal attachment
- [ ] Follow up if no response by Thursday

## Approval Status

**External action requires approval**: Email send to new contact
- Approval request: `/Pending_Approval/APPROVAL_email_proposal_newclient_2026-01-09.md`
- Status: Pending human review
- Once approved, use `@execute-approved-actions` skill to send email via MCP server
```

### Output: Approval Request (Silver Tier)

**File**: `/Pending_Approval/APPROVAL_email_proposal_newclient_2026-01-09.md`

```markdown
---
type: approval_request
action: send_email
plan_id: /Plans/PLAN_proposal_request_2026-01-09.md
source_action_item: /Needs_Action/EMAIL_20260109_67890.md
created: 2026-01-09T14:35:00Z
expires: 2026-01-10T14:35:00Z
status: pending
priority: high
mcp_server: email
mcp_tool: send_email
---

# Approval Request: Send Email Reply

## Action Summary

**Type**: Send email reply with proposal attachment
**Reason**: New client requested proposal with Friday deadline (high priority)
**Target**: newclient@startup.com
**Priority**: high

## Action Details

### Parameters

- **To**: newclient@startup.com
- **Subject**: Proposal for New Startup Inc. - Services
- **Body**: [Draft email body with proposal details]
- **Attachment**: /Vault/Proposals/2026-01_NewStartupInc.pdf (to be generated)

### Content Preview

Hi Sarah,

Thank you for reaching out. I've prepared a proposal for your services...

[Full email body preview]

## Approval Instructions

### To Approve This Action

1. Review email content and proposal attachment
2. Verify recipient is correct
3. Move this file to `/Approved/` folder
4. The `@execute-approved-actions` skill will send the email via MCP server

### To Reject This Action

Move this file to `/Rejected/` folder with rejection reason.

## Execution Status

- Status: pending
- Awaiting human approval

## Audit Trail

- Created: 2026-01-09T14:35:00Z by @process-action-items
```

### Audit Log Entry

**File**: `/Logs/2026-01-09.json`

```json
{
  "date": "2026-01-09",
  "actions": [
    {
      "timestamp": "2026-01-09T14:35:00Z",
      "action_type": "approval_request_created",
      "actor": "claude_code",
      "target": "newclient@startup.com",
      "parameters": {
        "action": "send_email",
        "subject": "Proposal for New Startup Inc.",
        "priority": "high"
      },
      "approval_status": "pending",
      "approval_file": "APPROVAL_email_proposal_newclient_2026-01-09.md",
      "plan_reference": "/Plans/PLAN_proposal_request_2026-01-09.md",
      "result": "pending_approval",
      "error": null
    }
  ]
}
```

---

## Example 7: Silver Tier - LinkedIn Post with Approval

### Input: Action Item File

**File**: `/Needs_Action/LINKEDIN_weekly_post_2026-01-09.md`

```markdown
---
type: social_media
source: linkedin
subject: Weekly business update post
received: 2026-01-09T09:00:00Z
priority: medium
status: pending
trigger: scheduled
---

## Content

Scheduled LinkedIn post for weekly business update. Should include:
- Recent client success story
- Upcoming product launch
- Industry insights

## Metadata
- Post type: Business update
- Visibility: Public
- Hashtags: #BusinessGrowth #TechInnovation
```

### Skill Execution (Silver Tier)

1. **Reads** action item and `Company_Handbook.md`
2. **Determines**: LinkedIn post requires approval (all social media posts)
3. **Creates** plan with LinkedIn posting steps
4. **Creates** approval request with post content
5. **Logs** to audit log

### Output: Approval Request for LinkedIn Post

**File**: `/Pending_Approval/APPROVAL_linkedin_weekly_post_2026-01-09.md`

```markdown
---
type: approval_request
action: post_linkedin
plan_id: /Plans/PLAN_linkedin_weekly_update_2026-01-09.md
created: 2026-01-09T09:05:00Z
expires: 2026-01-10T09:05:00Z
status: pending
priority: medium
mcp_server: linkedin
mcp_tool: create_post
---

# Approval Request: LinkedIn Post

## Action Summary

**Type**: Create LinkedIn business update post
**Reason**: Scheduled weekly business update (automated)
**Target**: LinkedIn company page / personal profile
**Priority**: medium

## Action Details

### Parameters

- **Content**: [Generated post content with client success, product launch, insights]
- **Visibility**: public
- **Hashtags**: #BusinessGrowth #TechInnovation
- **Media**: [optional image attachment]

### Content Preview

🚀 Excited to share our latest client success story...

[Full post content preview]

## Approval Instructions

**Move to `/Approved/` to post, or `/Rejected/` to cancel.**
```

---

## Example 8: Silver Tier - Auto-Approval Threshold (No Approval Needed)

### Scenario

Email reply to known contact, below auto-approve threshold (e.g., < 100 words, known contact, no attachments).

### Skill Execution

1. **Reads** action item and `Company_Handbook.md` approval thresholds
2. **Determines**: Action meets auto-approval criteria
3. **Creates** plan
4. **Creates** approval request but marks as `auto_approved: true`
5. **Immediately** moves approval to `/Approved/` (or creates execution file)
6. **Logs** with `auto_approved: true` flag

### Output: Auto-Approved Action

**Audit Log Entry**:

```json
{
  "timestamp": "2026-01-09T15:00:00Z",
  "action_type": "send_email",
  "target": "knownclient@example.com",
  "approval_status": "auto_approved",
  "auto_approve_reason": "Known contact, simple reply, below word limit",
  "mcp_server": "email",
  "result": "pending_execution"
}
```

**Note**: Even auto-approved actions should still be logged and tracked.

---

These Silver tier examples demonstrate:
- Approval request creation for external actions
- Integration with MCP servers for execution
- Audit logging requirements
- Auto-approval threshold handling
- Complete HITL workflow from detection → approval → execution
