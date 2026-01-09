# Feature Specification: Bronze Tier Personal AI Employee

**Feature Branch**: `001-bronze-ai-employee`
**Created**: 2026-01-09
**Status**: Draft
**Input**: User description: "Build a Bronze tier Personal AI Employee system that processes action items discovered by watchers and creates actionable plans using Claude Code within an Obsidian vault"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Watcher Detects New Items (Priority: P1)

As a user, I want a watcher script to automatically detect new items from an external source (Gmail emails or new files in a monitored folder) and create corresponding action item files in my Obsidian vault's `/Needs_Action/` folder, so that I don't miss anything requiring my attention.

**Why this priority**: This is the foundational capability - without detection, nothing else works. The watcher is the "eyes" of the AI employee.

**Independent Test**: Can be fully tested by running the watcher, creating a new email/file in the monitored source, and verifying a `.md` file appears in `/Needs_Action/` within the check interval.

**Acceptance Scenarios**:

1. **Given** the watcher is running and monitoring Gmail, **When** a new email arrives, **Then** an action item file is created in `/Needs_Action/` within 60 seconds containing the email subject, sender, date, and body summary.

2. **Given** the watcher is running and monitoring a folder, **When** a new file is added to the monitored folder, **Then** an action item file is created in `/Needs_Action/` containing the filename, file type, and creation timestamp.

3. **Given** the watcher has already processed an item, **When** the same item is encountered again, **Then** no duplicate action file is created.

4. **Given** the watcher encounters a temporary API error, **When** it retries after a brief delay, **Then** it continues normal operation without crashing.

---

### User Story 2 - Claude Code Processes Action Items (Priority: P2)

As a user, I want Claude Code to read action items from `/Needs_Action/`, analyze them according to my rules in `Company_Handbook.md`, and create structured plan files in `/Plans/`, so that I receive actionable guidance for each item.

**Why this priority**: This is the "reasoning" capability - the AI employee uses intelligence to turn raw items into actionable plans.

**Independent Test**: Can be tested by manually placing an action item file in `/Needs_Action/`, invoking the process-action-items skill, and verifying a plan file appears in `/Plans/` with appropriate checkboxes and next steps.

**Acceptance Scenarios**:

1. **Given** an action item file exists in `/Needs_Action/`, **When** the process-action-items skill is invoked, **Then** Claude Code reads the file, creates a structured plan in `/Plans/`, and moves the original to `/Done/`.

2. **Given** `Company_Handbook.md` contains rules about prioritization, **When** processing an action item, **Then** the generated plan reflects the applicable rules and priority level.

3. **Given** an action item requires follow-up, **When** creating the plan, **Then** the plan includes clear, actionable checkboxes that a human can complete.

4. **Given** Claude Code encounters an unreadable file, **When** processing fails, **Then** an error is logged and the file remains in `/Needs_Action/` for manual review.

---

### User Story 3 - Dashboard Shows System Status (Priority: P3)

As a user, I want to view a `Dashboard.md` file that shows the current state of the system (pending items, recent activity, watcher status), so that I can quickly understand what's happening without checking multiple folders.

**Why this priority**: Dashboard provides visibility and confidence that the system is working. Important but not blocking core functionality.

**Independent Test**: Can be tested by checking that `Dashboard.md` accurately reflects the counts in `/Needs_Action/`, recent files in `/Done/`, and last watcher activity timestamp.

**Acceptance Scenarios**:

1. **Given** items exist in `/Needs_Action/`, **When** viewing `Dashboard.md`, **Then** the count of pending items is displayed accurately.

2. **Given** the watcher has run recently, **When** viewing `Dashboard.md`, **Then** the last check timestamp is displayed.

3. **Given** plans have been created, **When** viewing `Dashboard.md`, **Then** the count of recent plans (last 24 hours) is visible.

4. **Given** the system processed items today, **When** viewing `Dashboard.md`, **Then** a list of recent actions is displayed.

---

### User Story 4 - Vault Setup and Configuration (Priority: P4)

As a user, I want the Obsidian vault to have a clear folder structure and configuration file (`Company_Handbook.md`) so that I can customize the AI employee's behavior and understand where files are stored.

**Why this priority**: This is infrastructure/setup - needed once at the beginning, then rarely touched.

**Independent Test**: Can be tested by verifying all required folders exist, `Company_Handbook.md` is readable, and `Dashboard.md` is in the expected location.

**Acceptance Scenarios**:

1. **Given** a fresh installation, **When** setup is complete, **Then** folders `/Inbox`, `/Needs_Action`, `/Done`, and `/Plans` exist.

2. **Given** `Company_Handbook.md` exists, **When** the user opens it, **Then** it contains editable configuration sections for watcher settings and processing rules.

3. **Given** the vault is configured, **When** opening Obsidian, **Then** `Dashboard.md` is visible and displays system status.

---

### Edge Cases

- **What happens when the vault folder is inaccessible?**: Log error, notify user via console output, do not crash.
- **What happens when Gmail API credentials expire?**: Log authentication error, stop watcher gracefully, create notification in `/Needs_Action/` about credential refresh needed.
- **What happens when `/Needs_Action/` is empty?**: Process-action-items skill exits gracefully with "No items to process" message.
- **What happens when a plan file already exists for an action item?**: Append timestamp to filename to avoid overwrite (e.g., `plan-email-subject-2026-01-09-143022.md`).
- **What happens when the watcher check interval is too short for API rate limits?**: Log warning, automatically back off to respect rate limits.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST include a watcher script that monitors ONE external source (Gmail OR filesystem folder).
- **FR-002**: Watcher MUST create Markdown files in `/Needs_Action/` when new items are detected.
- **FR-003**: Watcher MUST track processed item IDs to prevent duplicate file creation.
- **FR-004**: Watcher MUST be configurable via environment variables (check interval, source path/account).
- **FR-005**: System MUST include a Claude Code Agent Skill named "process-action-items" that reads from `/Needs_Action/`.
- **FR-006**: The process-action-items skill MUST read rules from `Company_Handbook.md` when creating plans.
- **FR-007**: Plans created by Claude Code MUST include actionable checkboxes and clear next steps.
- **FR-008**: System MUST move processed action items from `/Needs_Action/` to `/Done/` after plan creation.
- **FR-009**: System MUST maintain a `Dashboard.md` file with current system status.
- **FR-010**: All credentials (API keys, OAuth tokens) MUST be stored in environment variables, never in vault files.
- **FR-011**: System MUST log errors to console or log file without exposing credentials.
- **FR-012**: Watcher MUST continue operation after transient errors (retry once, then continue to next cycle).
- **FR-013**: System MUST include `Company_Handbook.md` with configurable rules and settings.
- **FR-014**: All AI functionality MUST be implemented as documented Agent Skills, not inline prompts.

### Key Entities

- **Action Item**: A detected item requiring attention. Attributes: source (email/file), title/subject, content summary, timestamp, priority (if determinable), unique ID.
- **Plan**: A structured response to an action item. Attributes: linked action item, created timestamp, checkboxes for next steps, priority, due date (if applicable).
- **Dashboard**: A live status summary. Attributes: pending item count, recent actions list, watcher status, last update timestamp.
- **Company Handbook**: Configuration and rules document. Attributes: watcher settings, processing rules, priority definitions, approved contacts (for future HITL).

## Assumptions

The following assumptions were made based on common patterns and Bronze tier constraints:

1. **Single Watcher**: Only one watcher type is needed for Bronze tier (Gmail OR filesystem, user chooses during setup).
2. **Manual Triggering**: The process-action-items skill is invoked manually by the user or via a simple cron/scheduled task; real-time processing is not required.
3. **Local Obsidian**: The Obsidian vault is on the local filesystem, not synced to cloud during operation.
4. **English Language**: Action items and plans are in English.
5. **Check Interval Default**: Watcher defaults to 60-second check intervals unless configured otherwise.
6. **No Authentication UI**: OAuth/credential setup is done manually via environment variables and documentation; no GUI for auth flow.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Watcher detects and creates action files for 100% of new items within 2 check intervals (default: 2 minutes).
- **SC-002**: No duplicate action files are created for the same source item.
- **SC-003**: Claude Code successfully creates a plan file for 95% of action items (5% may fail due to malformed input).
- **SC-004**: Plans contain at least 3 actionable checkboxes on average.
- **SC-005**: Dashboard accurately reflects system state within 5 minutes of changes.
- **SC-006**: System handles common errors (network timeouts, API rate limits) without crashing for 1-hour continuous operation.
- **SC-007**: User can complete initial setup (vault structure + one watcher) in under 30 minutes using documentation.
- **SC-008**: All 4 user stories can be demonstrated end-to-end in under 15 minutes.
