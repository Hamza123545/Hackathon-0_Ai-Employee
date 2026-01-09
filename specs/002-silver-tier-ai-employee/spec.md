# Feature Specification: Silver Tier Personal AI Employee

**Feature Branch**: `002-silver-tier-ai-employee`
**Created**: 2026-01-09
**Status**: Draft
**Input**: User description: "Build a Silver tier Personal AI Employee system that extends the Bronze tier with external actions, MCP server integration, and human-in-the-loop approval workflows. All Bronze tier capabilities remain (watchers, action item processing, plans, dashboard). Silver tier adds: multiple watchers (Gmail + WhatsApp + LinkedIn), external actions via MCP servers (email sending, LinkedIn posting, browser automation), mandatory approval workflow for sensitive actions (/Pending_Approval, /Approved, /Rejected folders), scheduled operations via cron/Task Scheduler, process management with PM2/watchdog, and mandatory audit logging to /Logs/ folder."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multiple Watchers Monitor Different Sources (Priority: P1)

As a user, I want multiple watcher scripts running simultaneously (Gmail + WhatsApp + LinkedIn) to detect items from different communication channels, so that I capture all business-critical information without manually checking each platform.

**Why this priority**: This is the foundational Silver tier capability - multi-channel monitoring is what distinguishes Silver from Bronze. Without multiple watchers, there's no point in the other Silver features.

**Independent Test**: Can be fully tested by running all three watchers simultaneously via process manager, triggering items on each platform (send email, WhatsApp message, LinkedIn notification), and verifying action files appear in `/Needs_Action/` from all three sources within check intervals.

**Acceptance Scenarios**:

1. **Given** Gmail, WhatsApp, and LinkedIn watchers are running via PM2, **When** a new email arrives, **Then** an action item file is created in `/Needs_Action/` with source tagged as "gmail" within 5 minutes.

2. **Given** all watchers are active, **When** a WhatsApp message is received in monitored contacts, **Then** an action item file is created with source "whatsapp" containing sender name, timestamp, and message preview.

3. **Given** LinkedIn watcher is monitoring company page, **When** a new comment or message appears, **Then** an action item file is created with source "linkedin" containing interaction type and content.

4. **Given** one watcher crashes, **When** PM2 detects the failure, **Then** the watcher is automatically restarted within 10 seconds without affecting other watchers.

5. **Given** multiple watchers detect items simultaneously, **When** creating action files, **Then** no race conditions occur (each file has unique ID, no overwrites).

---

### User Story 2 - Human-in-the-Loop Approval Workflow (Priority: P2)

As a user, I want sensitive external actions (sending emails, posting to LinkedIn, browser automation) to require my explicit approval before execution, so that I maintain control over what my AI employee does on my behalf while still benefiting from automation.

**Why this priority**: This is the safety mechanism for Silver tier. Without HITL, automatic external actions would be too risky. Must come before MCP execution.

**Independent Test**: Can be tested by triggering an action that requires approval (e.g., email draft), verifying approval request appears in `/Pending_Approval/`, manually moving to `/Approved/`, and confirming execution via audit log.

**Acceptance Scenarios**:

1. **Given** Claude Code determines an email should be sent, **When** the process-action-items skill runs, **Then** an approval request file is created in `/Pending_Approval/` (not `/Done/`) with risk assessment and proposed action details.

2. **Given** an approval request exists in `/Pending_Approval/`, **When** I review and move it to `/Approved/`, **Then** the execute-approved-actions skill detects it within 1 minute and executes the action via MCP server.

3. **Given** an approval request exists in `/Pending_Approval/`, **When** I move it to `/Rejected/`, **Then** the action is NOT executed and a rejection entry is logged to audit log.

4. **Given** an approval request sits in `/Pending_Approval/` for over 24 hours, **When** viewing Dashboard, **Then** it is flagged as "pending-overdue" for attention.

5. **Given** auto-approval thresholds are configured in `Company_Handbook.md` for low-risk actions, **When** a low-risk action is proposed, **Then** it moves directly to `/Approved/` with "auto_approved" status in audit log.

---

### User Story 3 - External Actions via MCP Servers (Priority: P3)

As a user, I want my AI employee to execute approved actions via standardized MCP servers (send emails, post to LinkedIn, automate browser tasks), so that my business communication and marketing happen automatically while I focus on strategic work.

**Why this priority**: This is the "action" capability that Bronze lacks. Depends on HITL approval workflow (P2) being in place first.

**Independent Test**: Can be tested by creating an approved action in `/Approved/`, triggering the execute-approved-actions skill, and verifying the external action occurred (email sent, LinkedIn post visible) with matching audit log entry.

**Acceptance Scenarios**:

1. **Given** an approved email send request exists in `/Approved/`, **When** the execute-approved-actions skill runs, **Then** the email is sent via MCP email server and confirmed in audit log with timestamp and recipient.

2. **Given** an approved LinkedIn post request exists in `/Approved/`, **When** execution occurs, **Then** the post appears on my LinkedIn profile and audit log shows "linkedin_post" action with post URL.

3. **Given** an approved browser automation task exists, **When** execution occurs via MCP Playwright server, **Then** the browser actions are performed (e.g., form submission) and screenshots are saved to `/Logs/screenshots/`.

4. **Given** MCP server is unavailable during execution, **When** the skill attempts the action, **Then** execution fails gracefully, creates error notification in `/Needs_Action/`, and logs failure to audit log.

5. **Given** an action is successfully executed, **When** complete, **Then** the approval file is moved from `/Approved/` to `/Done/` with execution timestamp appended.

---

### User Story 4 - LinkedIn Social Media Automation (Priority: P4)

As a user, I want my AI employee to automatically draft and post LinkedIn content about my business (with approval), so that I maintain consistent social media presence without manual posting.

**Why this priority**: This is a specific high-value use case for Silver tier. Builds on P2 (approval) and P3 (MCP execution) but is a complete end-to-end workflow.

**Independent Test**: Can be tested end-to-end by configuring LinkedIn posting rules in `Company_Handbook.md`, triggering content generation, approving the draft, and verifying the post appears on LinkedIn.

**Acceptance Scenarios**:

1. **Given** LinkedIn posting is configured in `Company_Handbook.md` with topic keywords, **When** relevant content is detected or scheduled time arrives, **Then** Claude Code creates a draft LinkedIn post in `/Pending_Approval/`.

2. **Given** a LinkedIn post draft exists in `/Pending_Approval/`, **When** I review and approve it, **Then** the post is published to my LinkedIn profile within 5 minutes.

3. **Given** a LinkedIn post is successfully published, **When** viewing the Dashboard, **Then** it shows "Posts this week: 3" and links to recent posts.

4. **Given** LinkedIn API rate limits are reached, **When** attempting to post, **Then** the system queues the post and retries after appropriate delay without losing content.

---

### User Story 5 - Scheduled 24/7 Operation with Process Management (Priority: P5)

As a user, I want my watchers to run continuously 24/7 via process manager (PM2/supervisord), so that my AI employee is always monitoring and responding without manual intervention.

**Why this priority**: Production readiness - necessary for true automation. Can work independently but less valuable without multi-watcher and MCP capabilities.

**Independent Test**: Can be tested by starting watchers via PM2, monitoring for 24+ hours, simulating crash scenarios, and verifying automatic restart.

**Acceptance Scenarios**:

1. **Given** watchers are configured in PM2 ecosystem file, **When** I run `pm2 start ecosystem.config.js`, **Then** all watchers start and show "online" status in `pm2 status`.

2. **Given** a watcher crashes due to unhandled exception, **When** PM2 detects the crash, **Then** the watcher is restarted within 10 seconds with crash logged to PM2 logs.

3. **Given** watchers have been running for 24 hours, **When** checking `Dashboard.md`, **Then** uptime is displayed as "24h+" and no unexpected restarts are shown.

4. **Given** system reboots, **When** OS starts up, **Then** PM2 automatically restarts all watchers (via OS startup integration) within 2 minutes.

---

### User Story 6 - Comprehensive Audit Logging (Priority: P6)

As a user, I want all external actions logged to structured JSON files in `/Logs/` with timestamps, actors, parameters, and results, so that I can audit what my AI employee has done and troubleshoot issues.

**Why this priority**: Compliance and debugging - critical for trust but not blocking functionality. Lower priority because it's passive observation.

**Independent Test**: Can be tested by executing approved actions, checking `/Logs/YYYY-MM-DD.json`, and verifying all required fields are present with accurate data.

**Acceptance Scenarios**:

1. **Given** an email is sent via MCP server, **When** the action completes, **Then** an audit log entry exists in `/Logs/2026-01-09.json` with fields: timestamp, action_type: "email_send", actor: "claude-code", target, approval_status, result.

2. **Given** multiple actions occur on the same day, **When** viewing the audit log file, **Then** entries are in chronological order with unique IDs and no duplicates.

3. **Given** audit log contains sensitive information, **When** logged, **Then** credentials are sanitized (masked/removed) but other parameters are intact.

4. **Given** Dashboard is viewed, **When** recent actions occurred, **Then** the last 10 audit entries are displayed inline with action type and status.

5. **Given** audit logs are 90+ days old, **When** cleanup routine runs, **Then** old logs are archived (compressed) or deleted per retention policy in `Company_Handbook.md`.

---

### User Story 7 - Enhanced Dashboard for Silver Tier (Priority: P7)

As a user, I want the Dashboard to show Silver tier metrics (MCP server status, pending approvals, watcher health, recent audit entries), so that I understand my AI employee's operational state at a glance.

**Why this priority**: Visibility and monitoring - enhances user experience but all underlying functionality can work without enhanced dashboard.

**Independent Test**: Can be tested by running the system with multiple watchers and actions, then verifying Dashboard displays all Silver tier sections accurately.

**Acceptance Scenarios**:

1. **Given** multiple watchers are running, **When** viewing Dashboard, **Then** each watcher shows status (online/stopped), last check time, and items detected today.

2. **Given** approval requests exist in `/Pending_Approval/`, **When** viewing Dashboard, **Then** pending approval count is displayed with oldest request age (e.g., "3 pending, oldest: 2h").

3. **Given** MCP servers are configured, **When** viewing Dashboard, **Then** each MCP server shows health status (available/error), last successful action, and error count.

4. **Given** external actions have been executed, **When** viewing Dashboard, **Then** recent audit entries (last 10) are displayed with timestamp, action type, and result.

---

### Edge Cases

**Bronze tier edge cases still apply** (see `specs/001-bronze-ai-employee/spec.md`), plus the following Silver tier edge cases:

- **What happens when multiple watchers detect the same item (e.g., email + LinkedIn notification about same event)?**: Duplicate detection algorithm uses content hash to identify duplicates across sources. Second detection creates a note in existing action item instead of new file.

- **What happens when user never approves/rejects items in `/Pending_Approval/`?**: Items remain pending indefinitely (no auto-expiration). Dashboard flags items older than 24 hours as "overdue" for user attention.

- **What happens when MCP server returns malformed response?**: Execution fails gracefully, error logged to audit log with sanitized error details, notification created in `/Needs_Action/` for manual review.

- **What happens when PM2 process manager is not installed?**: System detects missing PM2 during setup, warns user, falls back to manual watcher execution with documentation on installing PM2 for production use.

- **What happens when audit log JSON file is corrupted?**: Audit logger detects corruption on write, creates new dated log file with "-recovery" suffix, logs corruption event to new file, continues operation.

- **What happens when user moves file to `/Approved/` but file is malformed?**: Execute-approved-actions skill validates file format, logs validation error, moves malformed file to `/Rejected/` with error note appended.

- **What happens when LinkedIn API credentials expire during posting?**: Post execution fails with auth error, notification created in `/Needs_Action/` with instructions to refresh credentials, post remains in `/Approved/` for retry after credential refresh.

- **What happens when two approved actions target the same external resource simultaneously (e.g., two LinkedIn posts)?**: Execution queue ensures sequential processing with 5-second delay between actions to the same resource type (configurable in `Company_Handbook.md`).

## Requirements *(mandatory)*

### Functional Requirements

**All Bronze tier requirements (FR-001 through FR-014 from Bronze spec) remain mandatory.**

Additional Silver tier requirements:

- **FR-015**: System MUST support at least TWO distinct watcher types running simultaneously (Gmail + one of: WhatsApp, LinkedIn, filesystem).
- **FR-016**: System MUST include a WhatsApp watcher that uses Playwright to monitor WhatsApp Web for new messages from configured contacts.
- **FR-017**: System MUST include a LinkedIn watcher that monitors LinkedIn notifications and messages for the configured account.
- **FR-018**: All watchers MUST be managed by a process supervisor (PM2, supervisord, or watchdog) that automatically restarts crashed processes.
- **FR-019**: System MUST include vault folders: `/Pending_Approval/`, `/Approved/`, `/Rejected/`, `/Logs/` in addition to Bronze tier folders.
- **FR-020**: System MUST include an "execute-approved-actions" Agent Skill that reads from `/Approved/` and executes via MCP servers.
- **FR-021**: All external actions (email send, social media post, browser automation) MUST create approval requests in `/Pending_Approval/` before execution.
- **FR-022**: Approval request files MUST include: action type, target, parameters, risk assessment (low/medium/high), rationale, and approval instructions.
- **FR-023**: System MUST integrate with at least ONE working MCP server (email server recommended as minimum).
- **FR-024**: MCP servers MUST follow Model Context Protocol (JSON-RPC over stdio) standard.
- **FR-025**: All external actions MUST be logged to `/Logs/YYYY-MM-DD.json` with structured format: timestamp, action_type, actor, target, parameters (sanitized), approval_status, result.
- **FR-026**: Audit logs MUST retain entries for minimum 90 days (configurable in `Company_Handbook.md`).
- **FR-027**: Audit logs MUST NOT contain credentials or unsanitized sensitive data (API keys, passwords, tokens).
- **FR-028**: System MUST support auto-approval for low-risk actions when configured in `Company_Handbook.md` with explicit thresholds.
- **FR-029**: Dashboard MUST display Silver tier metrics: pending approval count, MCP server health, watcher status for all watchers, recent audit entries (last 10).
- **FR-030**: System MUST include scheduler configuration (cron for Linux/Mac, Task Scheduler for Windows) for continuous watcher operation.
- **FR-031**: LinkedIn posting capability MUST support approval workflow (draft → approve → post) with configurable posting rules.
- **FR-032**: All AI functionality MUST remain as documented Agent Skills (process-action-items, execute-approved-actions) per Bronze tier requirement.

### Key Entities

**All Bronze tier entities (Action Item, Plan, Dashboard, Company Handbook) remain, plus:**

- **Approval Request**: A proposed external action awaiting human approval. Attributes: action_type (email_send, linkedin_post, browser_action), target, parameters (action-specific), risk_level (low/medium/high), rationale, created_timestamp, status (pending/approved/rejected/executed), approval_timestamp, approver.

- **MCP Server**: An external action execution backend. Attributes: server_name, server_type (email/linkedin/playwright/custom), status (available/error/offline), last_successful_action, error_count, capabilities (list of supported actions).

- **Audit Log Entry**: A record of an executed external action. Attributes: entry_id, timestamp, action_type, actor (claude-code/user/system), target, parameters (sanitized), approval_status (approved/auto_approved/rejected), approval_by, result (success/failure), error (if failed), mcp_server.

- **Watcher Instance**: A running watcher process. Attributes: watcher_type (gmail/whatsapp/linkedin/filesystem), status (online/stopped/crashed), last_check_time, items_detected_today, uptime, restart_count, process_id (PM2 ID or OS PID).

## Assumptions

**All Bronze tier assumptions remain valid**, plus the following Silver tier assumptions:

1. **MCP Server Availability**: At least one MCP server (email recommended) is installed and configured before Silver tier operation. Setup documentation guides MCP server installation.

2. **Process Manager**: PM2 is the default process manager (cross-platform, widely used). Alternative: supervisord (Linux) or watchdog library (Python fallback). User chooses during setup.

3. **Approval Frequency**: External actions requiring approval occur 2-10 times per day on average. System is designed for human-in-the-loop at this frequency, not hundreds of actions per hour.

4. **LinkedIn Posting Frequency**: LinkedIn posts are limited to 1-3 per day to avoid rate limits and maintain quality. Configurable in `Company_Handbook.md`.

5. **WhatsApp Web Access**: WhatsApp watcher requires WhatsApp Web to be accessible and logged in. Playwright maintains session; user must scan QR code once during initial setup.

6. **Audit Log Size**: Daily audit logs are expected to be < 10MB per day (approximately 1000 actions/day). Compression/archival recommended after 30 days.

7. **Single User**: Silver tier is designed for single-user operation. Multi-user support (shared approvals, role-based permissions) is Gold tier scope.

8. **Network Connectivity**: System assumes reliable network connectivity for MCP servers and external API access. Offline operation not supported for external actions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

**All Bronze tier success criteria (SC-001 through SC-008) remain valid**, plus the following Silver tier criteria:

- **SC-009**: At least TWO distinct watchers (e.g., Gmail + WhatsApp) run continuously for 24+ hours without manual intervention, detecting and processing items from both sources.

- **SC-010**: Approval workflow functions end-to-end for 95% of proposed external actions: action detected → plan created → approval request in `/Pending_Approval/` → human review → approved action executes via MCP server → logged to audit log → moved to `/Done/`.

- **SC-011**: At least ONE external action (email send OR LinkedIn post) executes successfully via MCP server with matching audit log entry within 10 minutes of approval.

- **SC-012**: LinkedIn posts appear on user's profile within 5 minutes of approval, with 100% success rate for valid posts (failures due to API errors handled gracefully with notifications).

- **SC-013**: Process manager (PM2) automatically restarts crashed watchers within 10 seconds, with uptime > 99.5% over 24-hour test period (allowing for brief restarts).

- **SC-014**: All external actions (100%) are logged to `/Logs/YYYY-MM-DD.json` with all required fields present (timestamp, action_type, actor, target, approval_status, result).

- **SC-015**: Audit logs contain zero instances of unsanitized credentials (API keys, passwords, tokens) across 100 sampled entries.

- **SC-016**: Dashboard displays Silver tier metrics (pending approvals, MCP server health, all watcher statuses, recent audit entries) with data freshness < 5 minutes.

- **SC-017**: User can complete Silver tier setup (MCP server integration, multi-watcher configuration, PM2 setup, approval workflow test) in under 2 hours using documentation.

- **SC-018**: Auto-approval rules (if configured) correctly identify and auto-approve low-risk actions per `Company_Handbook.md` thresholds, with zero false positives (high-risk actions incorrectly auto-approved).

- **SC-019**: System handles at least 50 action items per day across multiple watchers and external actions, maintaining Dashboard accuracy and audit log completeness.

- **SC-020**: All 7 Silver tier user stories can be demonstrated end-to-end in under 45 minutes (Bronze + Silver capabilities).

## Out of Scope (Silver Tier)

The following are explicitly out of scope for Silver tier and deferred to Gold tier or future development:

- **Multi-user support**: Shared approvals, role-based permissions, team collaboration.
- **Advanced scheduling**: Complex time-based rules, recurring tasks, calendar integration.
- **Machine learning**: Autonomous decision-making, pattern recognition, predictive actions.
- **Mobile app**: Native iOS/Android app for approval workflow (Silver uses Obsidian mobile or manual file moves).
- **Real-time notifications**: Push notifications for pending approvals (user checks Dashboard manually).
- **Advanced MCP servers**: Payment processing, CRM integration, advanced analytics (Silver focuses on email, LinkedIn, browser automation).
- **Multi-platform social media**: Twitter, Facebook, Instagram automation (Silver tier: LinkedIn only).
- **Voice/chat interface**: Conversational interface for approvals (Silver: file-based workflow).
- **Advanced audit analytics**: Trend analysis, reporting dashboard, compliance reports (Silver: raw JSON logs only).
- **Webhook receivers**: Inbound webhooks for external services (Silver: pull-based watchers only).

## Dependencies

**All Bronze tier dependencies remain**, plus:

- **Node.js v24+**: Required for MCP servers (Bronze: optional, Silver: mandatory).
- **PM2 or supervisord**: Required for process management (Bronze: optional, Silver: mandatory).
- **Playwright**: Required for WhatsApp watcher (if used) and browser automation MCP server.
- **MCP Email Server**: Minimum one MCP server for external actions (email recommended).
- **LinkedIn API Access**: Required for LinkedIn watcher and posting (API credentials needed).
- **WhatsApp Web**: Required for WhatsApp watcher (must be logged in via Playwright).

## Backward Compatibility

Silver tier MUST maintain full backward compatibility with Bronze tier:

- All Bronze tier capabilities (single watcher, action processing, plans, dashboard) continue to work without Silver features enabled.
- Bronze tier vault structure is a subset of Silver tier structure (Bronze folders remain, Silver adds approval and logs folders).
- Bronze tier skills (process-action-items) continue to function; Silver adds execute-approved-actions skill.
- Users can deploy Bronze tier and later upgrade to Silver tier without data migration (only configuration updates needed).

## Constraints

- **Mandatory Approval**: All external actions MUST go through approval workflow. Auto-approval requires explicit configuration with strict thresholds (not enabled by default).
- **Audit Logging**: Audit logging is MANDATORY for Silver tier (Bronze: optional). Cannot disable audit logs.
- **Process Management**: Production deployment requires process manager (PM2/supervisord). Manual watcher execution only for development/testing.
- **Network Dependency**: External actions require network connectivity. Offline mode not supported for MCP server actions.
- **Single User**: Silver tier remains single-user system (like Bronze). Multi-user is Gold tier scope.
