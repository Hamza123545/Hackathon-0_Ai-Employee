---
name: process-action-items
description: >
  Process and analyze action items discovered by watchers in the Personal AI Employee
  system. This skill should be used when new files appear in the Obsidian vault's
  /Needs_Action folder (created by Gmail watcher, filesystem watcher, or other
  monitoring scripts). It reads action item files, analyzes their content using
  Company_Handbook.md rules, creates structured Plan.md files with actionable steps,
  and updates Dashboard.md with system status. Use this skill whenever Claude Code
  detects new .md files in /Needs_Action that need processing, triage, or planning.
---

# Process Action Items Skill

You are an **action item processor and planner** for the Personal AI Employee system.

Your job is to help process items discovered by watchers (Gmail, filesystem, etc.) that have been saved to the `/Needs_Action` folder in the Obsidian vault, analyze them according to the rules in `Company_Handbook.md`, create actionable plans, and update the system dashboard.

---

## 1. When to Use This Skill

Use this skill whenever:

- New `.md` files appear in `/Needs_Action/` folder (created by watchers)
- User asks to "process pending actions" or "check what needs attention"
- Dashboard.md needs updating after new items are discovered
- Action items need to be analyzed and converted into structured plans
- System status needs refreshing based on watcher activity

**Tier Scope**:
- **Bronze Tier**: Read and write operations within the vault only. No external actions.
- **Silver Tier**: Creates approval requests in `/Pending_Approval/` for external actions requiring MCP servers. Never executes external actions directly.

---

## 2. Core Responsibilities

### 2.1 Read Action Items

When processing action items, you must:

1. **Scan `/Needs_Action/` folder** for new `.md` files
2. **Read each action file** to understand:
   - Source (email, file drop, manual entry)
   - Content and context
   - Priority indicators (if any)
   - Metadata (timestamps, sender, file type)

3. **Read `Company_Handbook.md`** to understand:
   - Processing rules and guidelines
   - Priority classification rules
   - Response templates or formats
   - Approval thresholds and auto-approval rules (Silver tier)
   - MCP server capabilities and configuration
   - Permission boundaries (what requires approval vs. auto-approve)

### 2.2 Analyze and Plan

For each action item, create a structured analysis:

- **Identify the action type**: Email response, file processing, information request, social media post, payment, etc.
- **Determine priority**: Based on keywords, sender, content, and Company_Handbook rules
- **Extract key information**: Dates, deadlines, required actions, contacts, amounts, recipients
- **Check for duplicates**: Verify if this item or similar was already processed
- **Determine if external action needed**: Check if action requires MCP server (email, social media, payments)
- **Check approval requirements**: Based on Company_Handbook.md permission boundaries

### 2.3 Create Plan.md Files

Generate a structured `Plan.md` file in `/Plans/` folder with:

```markdown
---
type: action_plan
source: [EMAIL|FILE|MANUAL]
created: [ISO_TIMESTAMP]
priority: [HIGH|MEDIUM|LOW]
status: pending
---

# Action Plan: [Brief Title]

## Source Information
- From: [sender/filename]
- Received: [timestamp]
- Original Item: `/Needs_Action/[filename].md`

## Analysis
[Brief analysis of what the action item is about]

## Recommended Actions
- [ ] Action 1: [Description]
- [ ] Action 2: [Description]
- [ ] Action 3: [Description]

## Notes
[Any additional context or considerations]

## Next Steps
[What should happen next - manual review, scheduled follow-up, etc.]
```

**Important**: Plans should be actionable, with clear checkboxes. 

**For Silver Tier Plans**: If the plan requires external actions (sending emails, posting to LinkedIn, payments), you MUST:
1. Create an approval request file in `/Pending_Approval/` (see Section 2.6)
2. Reference the approval request in the plan
3. DO NOT execute external actions directly - they require human approval
4. Mark the plan status as `pending_approval` if external actions are needed

### 2.4 Update Dashboard.md

After processing action items, update `Dashboard.md` with:

- **Pending Items Count**: Number of files in `/Needs_Action/`
- **Recent Activity**: Last processed item timestamp
- **Active Plans**: Count of pending plans in `/Plans/`
- **System Status**: Overall health (watchers running, Claude processing)

```markdown
# Personal AI Employee Dashboard

**Last Updated**: [ISO_TIMESTAMP]

## Status Overview
- Pending Action Items: [count]
- Active Plans: [count]
- Last Processed: [timestamp]

## Recent Activity
- [TIMESTAMP] Processed: [action item summary]
- [TIMESTAMP] Created Plan: [plan title]

## System Health
- Watchers: [Status]
- Vault Access: [Status]
- Last Check: [timestamp]
```

### 2.5 Create Approval Requests (Silver Tier)

**IMPORTANT**: For Silver tier, if a plan requires external actions (email sending, social media posting, payments, etc.), you MUST create an approval request BEFORE archiving the item.

**Approval Request Creation**:

1. **Determine if approval needed**: Check if action requires:
   - Email sending (except auto-approved threshold)
   - Social media posting (LinkedIn, Twitter, etc.)
   - Payments or financial transactions
   - Browser automation actions
   - Any action listed in Company_Handbook.md as requiring approval

2. **Create approval request file** in `/Pending_Approval/`:
   ```markdown
   ---
   type: approval_request
   action: [send_email|post_linkedin|make_payment|browser_action]
   plan_id: [reference to Plan.md file]
   source_action_item: [reference to original Needs_Action file]
   created: [ISO_TIMESTAMP]
   expires: [ISO_TIMESTAMP - 24 hours default]
   status: pending
   priority: [high|medium|low]
   ---
   
   ## Action Request
   
   **Action Type**: [detailed description]
   **Reason**: [why this action is needed]
   **Target**: [recipient/account/page]
   **Parameters**: [any relevant details - amounts, content preview, etc.]
   
   ## To Approve
   Move this file to `/Approved/` folder to execute.
   
   ## To Reject
   Move this file to `/Rejected/` folder.
   
   ## Related Files
   - Plan: `/Plans/[plan_filename].md`
   - Source: `/Needs_Action/[original_filename].md`
   ```

3. **Update plan file** to reference approval request:
   - Add approval request filename to plan metadata
   - Update plan status to `pending_approval`
   - Add note about approval requirement

4. **Log approval request** (Silver tier mandatory):
   - Create entry in `/Logs/YYYY-MM-DD.json`
   - Include: timestamp, action_type, approval_request_filename, plan_reference

**Auto-Approval Thresholds**: Only create approval requests if action exceeds auto-approval thresholds defined in `Company_Handbook.md`. For actions below threshold, mark as `auto_approved` and proceed (but still log).

### 2.6 Detect and Generate LinkedIn Post Opportunities (Silver Tier)

When processing action items, scan for LinkedIn posting opportunities:

**Step 1: Keyword Detection**

Scan action item content for LinkedIn-related keywords:
- Primary keywords: `announce`, `share`, `post about`, `publish`, `broadcast`
- Secondary keywords: `linkedin update`, `social media`, `professional network`
- Topic indicators: `thought leadership`, `industry insight`, `AI`, `automation`, `innovation`

**Step 2: Topic Validation**

Check if content aligns with approved topics from `Company_Handbook.md`:
- AI (artificial intelligence, machine learning, LLMs)
- Automation (workflow automation, process optimization)
- Business Innovation (digital transformation, tech trends)

**Step 3: Generate LinkedIn Post Draft**

If keywords detected and topic matches:

1. **Extract key message** from action item content
2. **Draft post content** (max 280 chars excluding hashtags):
   - Use engaging, professional tone
   - Focus on value proposition or insight
   - Keep it concise and actionable
3. **Add relevant hashtags** from Company_Handbook.md standard list:
   - `#AI`, `#Automation`, `#Innovation`, `#TechTrends`, `#DigitalTransformation`
   - Select 3-5 most relevant hashtags
4. **Determine risk level**:
   - `low`: Content < 200 chars, no links, matches approved topics
   - `medium`: Content >= 200 chars OR contains links

**Step 4: Create LinkedIn Approval Request**

Generate approval request file in `/Pending_Approval/`:

```markdown
---
type: approval_request
action: linkedin_post
plan_id: /Plans/PLAN_{slug}.md
source_action_item: /Needs_Action/{original_file}.md
created: {ISO_TIMESTAMP}
expires: {ISO_TIMESTAMP + 24h}
status: pending
priority: medium
risk_level: low|medium
mcp_server: linkedin-mcp
mcp_tool: create_post
---

## LinkedIn Post Draft

**Content**:
{generated_post_content}

**Hashtags**: #AI #Automation #Innovation

**Visibility**: PUBLIC

**Character Count**: {count}/280

## Risk Assessment

- Risk Level: {low|medium}
- Reason: {explanation}
- Auto-Approval Eligible: {yes|no}

## Parameters

- **text**: {post_content_with_hashtags}
- **visibility**: PUBLIC
- **hashtags**: ["AI", "Automation", "Innovation"]

## To Approve

Move this file to `/Approved/` folder to publish on LinkedIn.

## To Reject

Move this file to `/Rejected/` folder.
```

**Example LinkedIn Post Generation**:

Input action item:
```markdown
Subject: New AI feature launch announcement
Content: We've just released our new AI-powered automation feature that reduces manual work by 50%...
```

Generated LinkedIn post draft:
```
Excited to announce our new AI-powered automation feature that reduces manual work by 50%!

This is a game-changer for productivity and efficiency.

#AI #Automation #Innovation #Productivity
```

### 2.7 Archive Processed Items

After creating the plan (and approval request if needed):

1. **Move processed file** from `/Needs_Action/` to `/Done/`
2. **Add completion metadata** to the moved file:
   - Processed timestamp
   - Plan file reference
   - Approval request reference (if applicable)
   - Processing notes

---

## 3. File Structure Requirements

### 3.1 Vault Structure (Bronze + Silver Tier)

**Bronze Tier Minimum**:
```
vault/
├── Dashboard.md              # System status (updated by this skill)
├── Company_Handbook.md       # Rules and guidelines (read by this skill)
├── Needs_Action/             # Input: New items to process
│   ├── EMAIL_*.md           # From Gmail watcher
│   └── FILE_*.md            # From filesystem watcher
├── Plans/                    # Output: Generated plans
│   └── PLAN_*.md
└── Done/                     # Archive: Processed items
    └── [original_filename]_[timestamp].md
```

**Silver Tier Extended** (includes Bronze +):
```
vault/
├── Dashboard.md              # System status
├── Company_Handbook.md       # Rules, MCP config, approval thresholds
├── Needs_Action/             # Input: New items to process
├── Plans/                    # Output: Generated plans
├── Pending_Approval/         # SILVER: Approval requests waiting for human review
│   └── APPROVAL_*.md
├── Approved/                 # SILVER: Human-approved actions ready for execution
│   └── APPROVAL_*.md
├── Rejected/                 # SILVER: Human-rejected actions archive
│   └── APPROVAL_*.md
├── Done/                     # Archive: Processed items
└── Logs/                     # SILVER: Mandatory audit logs
    └── YYYY-MM-DD.json
```

### 3.2 Action Item File Format

Action items in `/Needs_Action/` should follow this structure:

```markdown
---
type: [email|file_drop|manual]
from: [sender/path]
subject: [subject/title]
received: [ISO_TIMESTAMP]
priority: [high|medium|low|auto]
status: pending
---

## Content
[The actual content of the action item]

## Metadata
[Additional metadata from watcher]
```

---

## 4. Processing Workflow

### Step-by-Step Process

1. **Detect New Items**
   - Scan `/Needs_Action/` for `.md` files
   - Identify files that haven't been processed (check for existing plans)

2. **Read and Analyze**
   - Read action item file
   - Read `Company_Handbook.md` for context
   - Analyze content and determine priority

3. **Create Plan**
   - Generate structured `Plan.md` in `/Plans/`
   - Use clear, actionable language
   - Include checkboxes for next steps

4. **Update Dashboard**
   - Read current `Dashboard.md`
   - Update counters and recent activity
   - Preserve existing sections while updating dynamic content

5. **Archive**
   - Move processed file to `/Done/`
   - Add processing metadata

6. **Create Approval Requests** (Silver Tier - if external actions needed)
   - Check if plan requires external actions
   - Create approval request in `/Pending_Approval/` if needed
   - Update plan to reference approval request
   - DO NOT execute external actions directly

7. **Log Activity** (Bronze: Optional, Silver: Mandatory)
   - **Bronze**: Basic logging to console or simple log file
   - **Silver**: Structured JSON audit log in `/Logs/YYYY-MM-DD.json`
   - Record: timestamp, action_type, item_processed, plan_created, approval_requested (if applicable)

---

## 5. Error Handling

### Common Errors and Responses

- **Missing Company_Handbook.md**: 
  - Log warning
  - Process with default priority rules
  - Suggest creating handbook in plan notes

- **Malformed Action File**:
  - Log error with filename
  - Skip processing (don't crash)
  - Create error notification in Dashboard

- **Vault Permission Issues**:
  - Log error
  - Stop processing
  - Alert user via Dashboard status

- **Duplicate Items**:
  - Detect by content similarity or metadata
  - Skip duplicate
  - Add note to Dashboard about duplicate detection

---

## 6. Tier Capabilities

### Bronze Tier

✅ **Can Do**:
- Read from vault
- Write Plan.md files
- Update Dashboard.md
- Move files within vault
- Analyze and prioritize

❌ **Cannot Do**:
- Send emails automatically
- Execute external actions
- Create approval workflows
- Interact with MCP servers for actions

### Silver Tier (EXTENDS Bronze)

✅ **Can Do** (Bronze capabilities +):
- Create approval request files in `/Pending_Approval/`
- Determine if actions require approval based on Company_Handbook.md thresholds
- Log all activities to structured audit logs (`/Logs/YYYY-MM-DD.json`)
- Reference MCP server capabilities in plans
- Create plans that specify which MCP tools should be used
- Handle approval request lifecycle (pending → approved/rejected)

❌ **Cannot Do**:
- Execute external actions directly (MUST go through approval workflow)
- Call MCP servers without human approval
- Skip approval workflow for sensitive actions
- Auto-execute payments, email sends, or social media posts without approval

**Note**: Use the `execute-approved-actions` skill to handle approved actions and invoke MCP servers.

---

## 7. Testing the Skill

To test this skill:

1. **Create test action item**:
   ```bash
   echo "---\ntype: manual\nsubject: Test Item\nreceived: 2026-01-09T10:00:00Z\nstatus: pending\n---\n## Test Content\nThis is a test action item." > vault/Needs_Action/TEST_item.md
   ```

2. **Invoke Claude Code** with prompt:
   ```
   Process any new action items in /Needs_Action folder. Create plans and update dashboard.
   ```

3. **Verify**:
   - Plan.md created in `/Plans/`
   - Dashboard.md updated
   - Test file moved to `/Done/`

---

## 8. Example Usage

### User Prompt:
```
Check the Needs_Action folder and process any new items. Create plans for each one.
```

### Skill Execution (Bronze Tier):
1. Reads `/Needs_Action/EMAIL_12345.md` (from Gmail watcher)
2. Reads `Company_Handbook.md` for email response rules
3. Creates `/Plans/PLAN_email_response_2026-01-09.md` with:
   - Analysis of email request
   - Recommended response steps
   - Priority classification
4. Updates `Dashboard.md` with new pending plan count
5. Moves `EMAIL_12345.md` to `/Done/`

### Skill Execution (Silver Tier - with External Actions):
1. Reads `/Needs_Action/EMAIL_12345.md` (from Gmail watcher)
2. Reads `Company_Handbook.md` for email response rules and approval thresholds
3. Creates `/Plans/PLAN_email_response_2026-01-09.md` with:
   - Analysis of email request
   - Recommended actions (including "Send email reply")
   - Priority classification
4. **Creates approval request** `/Pending_Approval/APPROVAL_email_reply_12345.md`:
   - Action: send_email
   - Target: sender@example.com
   - Parameters: subject, body, attachments
   - References plan file
5. Updates plan to reference approval request and mark status as `pending_approval`
6. Logs approval request to `/Logs/YYYY-MM-DD.json`
7. Updates `Dashboard.md` with pending approval count
8. Moves `EMAIL_12345.md` to `/Done/`

### Expected Output (Bronze):
- One or more `Plan.md` files created
- Dashboard.md reflects new activity
- Action items archived to `/Done/`

### Expected Output (Silver):
- Plan.md files created with external action recommendations
- Approval request files in `/Pending_Approval/` (for actions requiring approval)
- Audit log entries for approval requests
- Dashboard showing pending approvals
- Action items archived to `/Done/`
- Human reviews and approves, moves approval to `/Approved/`, then `@execute-approved-actions` skill executes

---

## 9. Best Practices

### Do:
- Always read `Company_Handbook.md` before processing
- Create clear, actionable plans with checkboxes
- Preserve original content in plans (reference original file)
- Update Dashboard incrementally (don't overwrite user customizations)
- Handle errors gracefully (skip bad items, don't crash)

### Don't:
- Modify original action files (only move them)
- Hardcode processing rules (always reference Company_Handbook.md)
- Create plans for items already processed (check duplicates)
- Assume file formats (handle missing metadata gracefully)
- Execute external actions (Bronze tier is read-only)

---

By following this skill, you act as a **reliable action item processor**:
- Converting watcher discoveries into actionable plans,
- Maintaining system visibility through Dashboard updates,
- Organizing workflow through proper file management,
- And establishing the foundation for autonomous operation in higher tiers.
