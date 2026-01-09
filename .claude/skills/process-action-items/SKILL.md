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

**Bronze Tier Scope**: This skill focuses on **read and write operations within the vault only**. No external actions (sending emails, making payments) are performed.

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
   - Auto-approval thresholds (for future Silver/Gold tiers)

### 2.2 Analyze and Plan

For each action item, create a structured analysis:

- **Identify the action type**: Email response, file processing, information request, etc.
- **Determine priority**: Based on keywords, sender, content, and Company_Handbook rules
- **Extract key information**: Dates, deadlines, required actions, contacts
- **Check for duplicates**: Verify if this item or similar was already processed

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

**Important**: Plans should be actionable, with clear checkboxes. For Bronze tier, these are read-only recommendations (no automated execution).

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

### 2.5 Archive Processed Items

After creating the plan:

1. **Move processed file** from `/Needs_Action/` to `/Done/`
2. **Add completion metadata** to the moved file:
   - Processed timestamp
   - Plan file reference
   - Processing notes

---

## 3. File Structure Requirements

### 3.1 Vault Structure (Bronze Tier Minimum)

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

6. **Log Activity** (Optional for Bronze)
   - Basic logging to console or simple log file
   - Record what was processed and when

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

## 6. Bronze Tier Limitations

For Bronze tier, this skill:

✅ **Can Do**:
- Read from vault
- Write Plan.md files
- Update Dashboard.md
- Move files within vault
- Analyze and prioritize

❌ **Cannot Do** (Silver/Gold tiers):
- Send emails automatically
- Execute external actions
- Create approval workflows
- Interact with MCP servers for actions
- Schedule follow-ups

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

### Skill Execution:
1. Reads `/Needs_Action/EMAIL_12345.md` (from Gmail watcher)
2. Reads `Company_Handbook.md` for email response rules
3. Creates `/Plans/PLAN_email_response_2026-01-09.md` with:
   - Analysis of email request
   - Recommended response steps
   - Priority classification
4. Updates `Dashboard.md` with new pending plan count
5. Moves `EMAIL_12345.md` to `/Done/`

### Expected Output:
- One or more `Plan.md` files created
- Dashboard.md reflects new activity
- Action items archived to `/Done/`
- Clear summary of what was processed

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
