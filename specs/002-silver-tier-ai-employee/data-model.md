# Data Model: Silver Tier Personal AI Employee

**Feature**: Silver Tier Personal AI Employee
**Created**: 2026-01-09
**Status**: Draft

## Overview

This document defines all data entities for the Silver Tier Personal AI Employee system. Silver tier extends Bronze tier entities with approval workflow, MCP server integration, and audit logging capabilities.

---

## Inheritance from Bronze Tier

The following Bronze tier entities remain unchanged and are inherited:

- **Action Item**: Items discovered by watchers (see Bronze spec: `specs/001-bronze-ai-employee/spec.md`)
- **Plan**: Actionable plans created from action items (see Bronze spec)
- **Dashboard**: System status overview (see Bronze spec, extended in Silver with additional metrics)
- **Company Handbook**: Business rules and processing guidelines (see Bronze spec, extended with Silver configuration)

---

## Silver Tier Entities

### 1. Approval Request

**Purpose**: A proposed external action awaiting human approval before execution via MCP servers.

**File Location**: `/Pending_Approval/APPROVAL_<uuid>_<timestamp>.md`

**Schema**:

```yaml
---
type: approval_request
id: <uuid>                          # Unique identifier (UUID v4)
action_type: <string>               # One of: email_send, linkedin_post, browser_action, custom
target: <string>                    # Action target (email address, LinkedIn profile, URL, etc.)
risk_level: <enum>                  # One of: low, medium, high
rationale: <string>                 # Why this action is recommended
created_timestamp: <ISO8601>        # When approval request was created
status: <enum>                      # One of: pending, approved, rejected, executed
approval_timestamp: <ISO8601|null>  # When approved/rejected (null if pending)
approver: <string|null>             # Who approved (user, auto, null if pending)
execution_timestamp: <ISO8601|null> # When executed (null if not yet executed)
source_action_item: <string>        # Path to original action item file
mcp_server: <string>                # Target MCP server name (e.g., "email-mcp")
---

## Proposed Action

[Human-readable description of what will happen]

## Action Parameters

[Structured parameters for MCP tool invocation - redacted if sensitive]

## Risk Assessment

**Risk Level**: [LOW|MEDIUM|HIGH]

**Risk Factors**:
- Factor 1: Description
- Factor 2: Description

## Approval Instructions

**To APPROVE**: Move this file to `/Approved/`
**To REJECT**: Move this file to `/Rejected/`

## Notes

[Additional context or considerations]
```

**Validation Rules** (from FR-022):
- MUST include: action_type, target, parameters, risk_level, rationale, approval instructions
- `action_type` MUST be one of: email_send, linkedin_post, browser_action, custom
- `risk_level` MUST be one of: low, medium, high
- `status` MUST be one of: pending, approved, rejected, executed
- `created_timestamp` MUST be valid ISO 8601 format
- `parameters` MUST NOT contain unsanitized credentials (validated on creation)

**State Transitions**:
1. Created: `status: pending` in `/Pending_Approval/`
2. Approved: `status: approved` when moved to `/Approved/`
3. Rejected: `status: rejected` when moved to `/Rejected/`
4. Executed: `status: executed` after MCP execution, moved to `/Done/`

**Relationships**:
- References original `Action Item` via `source_action_item` path
- References `MCP Server` via `mcp_server` name
- Creates `Audit Log Entry` when executed

---

### 2. MCP Server

**Purpose**: An external action execution backend that implements Model Context Protocol.

**File Location**: Configuration in `AI_Employee/utils/config.py` or `AI_Employee/mcp_servers.json`

**Schema**:

```json
{
  "server_name": "string",              // Unique identifier (e.g., "email-mcp", "linkedin-mcp")
  "server_type": "enum",                // One of: email, linkedin, playwright, custom
  "status": "enum",                     // One of: available, error, offline, unknown
  "command": "string",                  // Startup command (e.g., "node email-mcp/index.js")
  "transport": "string",                // MCP transport protocol (usually "stdio")
  "capabilities": ["string"],           // List of supported tools (e.g., ["send_email", "list_inbox"])
  "last_successful_action": "ISO8601",  // Timestamp of last successful tool invocation (null if never)
  "last_health_check": "ISO8601",       // Timestamp of last health check
  "error_count": "number",              // Count of consecutive failures (reset on success)
  "environment": {                      // Environment variables for MCP server process
    "KEY": "value"
  },
  "config": {                           // Server-specific configuration
    // Email MCP example:
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "from_address": "user@example.com"
  }
}
```

**Validation Rules** (from FR-023, FR-024):
- `server_name` MUST be unique across all configured MCP servers
- `server_type` MUST be one of: email, linkedin, playwright, custom
- `status` MUST be one of: available, error, offline, unknown
- `transport` MUST be "stdio" (MCP standard)
- `capabilities` MUST be non-empty array of strings (tool names)
- At least ONE MCP server MUST be configured and available for Silver tier operation

**State Transitions**:
1. Initialized: `status: unknown` (not yet health-checked)
2. Available: `status: available` (health check passed)
3. Error: `status: error` (health check failed or tool invocation error)
4. Offline: `status: offline` (process not running or unreachable)

**Relationships**:
- Referenced by `Approval Request` via `mcp_server` field
- Referenced by `Audit Log Entry` via `mcp_server` field
- Displayed in `Dashboard` MCP server health section

---

### 3. Audit Log Entry

**Purpose**: A structured record of an executed external action for compliance, debugging, and audit trails.

**File Location**: `/Logs/YYYY-MM-DD.json` (daily JSON file with array of entries)

**Schema**:

```json
{
  "entry_id": "uuid",                   // Unique identifier (UUID v4)
  "timestamp": "ISO8601",               // When action was executed (UTC)
  "action_type": "string",              // Type of action (email_send, linkedin_post, browser_action, etc.)
  "actor": "string",                    // Who/what initiated action (claude-code, user, system)
  "target": "string",                   // Action target (email, URL, profile, etc.) - MAY be sanitized
  "parameters": {                       // Action-specific parameters (MUST be sanitized)
    "key": "value"                     // Credentials/tokens MUST be removed or masked
  },
  "approval_status": "enum",            // One of: approved, auto_approved, rejected, not_required
  "approval_by": "string|null",         // Who approved (user, auto, null if not_required)
  "approval_timestamp": "ISO8601|null", // When approval was granted (null if not_required)
  "result": "enum",                     // One of: success, failure, partial
  "result_details": "string|null",      // Human-readable result description
  "error": "string|null",               // Error message if result: failure (null if success)
  "error_code": "string|null",          // Machine-readable error code (null if success)
  "mcp_server": "string",               // Which MCP server executed this action
  "execution_duration_ms": "number",    // How long execution took (milliseconds)
  "approval_request_id": "string|null", // UUID of original approval request (null if auto-approved)
  "metadata": {                         // Additional context
    "user_agent": "claude-code/1.0",
    "platform": "windows",
    "version": "silver-v1.0"
  }
}
```

**Validation Rules** (from FR-025, FR-027):
- `entry_id` MUST be unique UUID v4
- `timestamp` MUST be valid ISO 8601 format in UTC timezone
- `action_type` MUST match one of the supported action types
- `actor` MUST be one of: claude-code, user, system
- `approval_status` MUST be one of: approved, auto_approved, rejected, not_required
- `result` MUST be one of: success, failure, partial
- `parameters` MUST NOT contain unsanitized credentials (API keys, passwords, tokens)
- `parameters` MUST NOT contain raw email body if it contains PII (only preview/hash)
- Entry MUST be appended to daily log file `/Logs/YYYY-MM-DD.json`

**Sanitization Rules** (from FR-027):
- **Credentials**: Remove or mask: api_key, password, token, secret, auth_header, access_token, refresh_token
- **Sensitive Data**: Hash or truncate: email body (preview only), personal identifiers
- **Preserve**: Action type, target (email/URL OK), timestamps, status, result

**Retention** (from FR-026):
- MUST retain entries for minimum 90 days (configurable in `Company_Handbook.md`)
- After 90 days: archive (compress) or delete per retention policy

**Relationships**:
- References `Approval Request` via `approval_request_id`
- References `MCP Server` via `mcp_server`
- Displayed in `Dashboard` recent audit entries section (last 10)

---

### 4. Watcher Instance

**Purpose**: A running watcher process that monitors a specific source (Gmail, WhatsApp, LinkedIn, filesystem) for new action items.

**File Location**: Runtime state in PM2 process manager or in-memory; Dashboard representation in `/Dashboard.md`

**Schema**:

```json
{
  "watcher_type": "enum",               // One of: gmail, whatsapp, linkedin, filesystem
  "status": "enum",                     // One of: online, stopped, crashed, starting, unknown
  "process_id": "string",               // PM2 process ID or OS PID
  "last_check_time": "ISO8601",         // When watcher last polled source
  "items_detected_today": "number",     // Count of action items detected since midnight
  "items_detected_total": "number",     // Total count since watcher start
  "uptime_seconds": "number",           // How long watcher has been running (seconds)
  "uptime_display": "string",           // Human-readable uptime (e.g., "24h 15m")
  "restart_count": "number",            // Number of times PM2 has restarted this watcher
  "last_restart_time": "ISO8601|null",  // When last restart occurred (null if never restarted)
  "last_restart_reason": "string|null", // Why watcher restarted (crash, manual, config change)
  "config": {                           // Watcher-specific configuration
    "check_interval_seconds": 300,     // How often to poll (default: 5 minutes)
    "enabled": true,                   // Whether watcher is enabled
    "source_specific_config": {}       // Gmail: label, WhatsApp: contacts, etc.
  },
  "health": {                           // Health metrics
    "last_error": "string|null",       // Last error message (null if healthy)
    "last_error_time": "ISO8601|null", // When last error occurred
    "consecutive_errors": "number"     // Count of consecutive errors (0 if healthy)
  }
}
```

**Validation Rules** (from FR-015, FR-016, FR-017, FR-018):
- `watcher_type` MUST be one of: gmail, whatsapp, linkedin, filesystem
- `status` MUST be one of: online, stopped, crashed, starting, unknown
- At least TWO distinct watcher types MUST be configured and running for Silver tier (FR-015)
- `process_id` MUST match PM2 process ID or OS PID
- `last_check_time` MUST be updated on each polling cycle

**State Transitions**:
1. Starting: `status: starting` (PM2 launching process)
2. Online: `status: online` (process running, polling successfully)
3. Crashed: `status: crashed` (process exited unexpectedly)
4. Stopped: `status: stopped` (manually stopped by user or PM2)
5. Auto-restart: `crashed` → `starting` → `online` (PM2 recovery)

**PM2 Integration** (from FR-018):
- MUST be managed by PM2 (or supervisord) for automatic crash recovery
- MUST restart within 10 seconds of crash (FR-018)
- Restart count tracked via PM2 metadata

**Relationships**:
- Creates `Action Item` files when items detected
- Displayed in `Dashboard` watcher status section
- Configuration read from `Company_Handbook.md` and `AI_Employee/utils/config.py`

---

## Entity Relationships Diagram

```
┌─────────────────┐
│  Watcher        │
│  Instance       │──────creates──────┐
└─────────────────┘                   │
                                      ▼
                              ┌─────────────────┐
                              │  Action Item    │
                              │  (Bronze)       │
                              └─────────────────┘
                                      │
                              analyzed by @process-action-items
                                      │
                                      ▼
                              ┌─────────────────┐
                              │  Plan           │
                              │  (Bronze)       │
                              └─────────────────┘
                                      │
                              if external action needed
                                      │
                                      ▼
                              ┌─────────────────┐
                              │  Approval       │
                              │  Request        │──references──┐
                              └─────────────────┘              │
                                      │                        │
                              human moves to /Approved/        │
                                      │                        │
                                      ▼                        ▼
                       ┌──────────────────────────┐   ┌─────────────────┐
                       │  execute-approved-       │   │  MCP Server     │
                       │  actions skill           │───│                 │
                       └──────────────────────────┘   └─────────────────┘
                                      │
                                  executes via MCP
                                      │
                                      ▼
                              ┌─────────────────┐
                              │  Audit Log      │
                              │  Entry          │
                              └─────────────────┘
                                      │
                              displayed in
                                      │
                                      ▼
                              ┌─────────────────┐
                              │  Dashboard      │
                              │  (Extended)     │
                              └─────────────────┘
```

---

## File System Structure

```
AI_Employee/                       # Obsidian vault root
├── Dashboard.md                  # Extended with Silver metrics
├── Company_Handbook.md           # Extended with Silver config
├── Needs_Action/                 # Action items from watchers (Bronze)
│   ├── EMAIL_*.md
│   ├── WHATSAPP_*.md
│   └── LINKEDIN_*.md
├── Plans/                        # Generated plans (Bronze)
│   └── PLAN_*.md
├── Pending_Approval/             # Approval requests awaiting review (Silver)
│   └── APPROVAL_*.md
├── Approved/                     # Approved actions ready for execution (Silver)
│   └── APPROVAL_*.md
├── Rejected/                     # Rejected actions (Silver)
│   └── APPROVAL_*.md
├── Done/                         # Completed items (Bronze + Silver)
│   ├── EMAIL_*.md
│   ├── PLAN_*.md
│   └── APPROVAL_*.md
└── Logs/                         # Audit logs (Silver)
    ├── 2026-01-09.json          # Daily JSON audit log
    ├── 2026-01-10.json
    └── screenshots/             # Browser automation screenshots
        └── *.png
```

---

## Validation Summary

### Approval Request Validation
- ✅ Action type is one of: email_send, linkedin_post, browser_action, custom
- ✅ Risk level is one of: low, medium, high
- ✅ Status is one of: pending, approved, rejected, executed
- ✅ All required fields present (FR-022)
- ✅ No unsanitized credentials in parameters (FR-027)

### MCP Server Validation
- ✅ At least ONE MCP server configured (FR-023)
- ✅ Server follows MCP protocol (JSON-RPC over stdio) (FR-024)
- ✅ Server name is unique
- ✅ Capabilities list is non-empty

### Audit Log Entry Validation
- ✅ All entries have structured format with required fields (FR-025)
- ✅ Credentials sanitized (no API keys, passwords, tokens) (FR-027)
- ✅ Timestamp in ISO 8601 UTC format
- ✅ Entry ID is unique UUID v4
- ✅ Retention minimum 90 days (FR-026)

### Watcher Instance Validation
- ✅ At least TWO distinct watcher types running (FR-015)
- ✅ WhatsApp watcher uses Playwright (FR-016)
- ✅ LinkedIn watcher monitors notifications/messages (FR-017)
- ✅ All watchers managed by PM2/supervisord (FR-018)

---

## State Machine Summary

### Approval Request Lifecycle

```
┌─────────┐
│ pending │ (created in /Pending_Approval/)
└─────────┘
    │
    ├─── human moves to /Approved/ ───┐
    │                                  │
    │                                  ▼
    │                            ┌──────────┐
    │                            │ approved │
    │                            └──────────┘
    │                                  │
    │                           execute-approved-actions
    │                                  │
    │                                  ▼
    │                            ┌──────────┐
    │                            │ executed │ (moved to /Done/)
    │                            └──────────┘
    │
    └─── human moves to /Rejected/ ───┐
                                       │
                                       ▼
                                 ┌──────────┐
                                 │ rejected │ (stays in /Rejected/)
                                 └──────────┘
```

### Watcher Instance Lifecycle

```
┌──────────┐
│ starting │ (PM2 launching)
└──────────┘
    │
    ▼
┌──────────┐
│  online  │ (polling successfully)
└──────────┘
    │
    ├─── unhandled exception ───┐
    │                            │
    │                            ▼
    │                      ┌──────────┐
    │                      │ crashed  │
    │                      └──────────┘
    │                            │
    │                      PM2 auto-restart
    │                            │
    │                            ▼
    │                      ┌──────────┐
    │                      │ starting │
    │                      └──────────┘
    │
    └─── user stops ───┐
                       │
                       ▼
                 ┌──────────┐
                 │ stopped  │
                 └──────────┘
```

---

## Notes

- **Backward Compatibility**: All Bronze tier entities (Action Item, Plan, Dashboard, Company Handbook) remain unchanged. Silver tier extends Dashboard and Company Handbook with additional sections but maintains Bronze structure.

- **Sanitization**: All entities that store external action parameters (Approval Request, Audit Log Entry) MUST sanitize credentials. Sanitization algorithm defined in `AI_Employee/utils/sanitizer.py` (to be implemented).

- **Persistence**:
  - Approval Requests: File-based (Markdown files in vault folders)
  - MCP Servers: Configuration file (JSON or Python config)
  - Audit Log Entries: Daily JSON files (append-only)
  - Watcher Instances: Runtime state in PM2; Dashboard displays snapshot

- **Concurrency**: File-based entities (Approval Requests) use UUID v4 for collision avoidance. Audit log appends are atomic (file locking or append-only pattern).

- **Testing**: Each entity schema can be validated independently. See `specs/002-silver-tier-ai-employee/plan.md` Phase 2 for validation test cases.
