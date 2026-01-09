<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 → 1.1.0 (MINOR - Silver Tier additions)
Modified principles:
  - Principle II: "Read-Only Operations (BRONZE TIER)" → "External Actions and MCP Integration (BRONZE → SILVER)"
  - Principle IV: "Security and Privacy by Design" → Extended with HITL approval workflow
  - Principle V: "Simple Watcher Execution (BRONZE TIER)" → "Multi-Watcher Architecture (BRONZE → SILVER)"
  - Principle VII: "Basic Dashboard (BRONZE TIER)" → "Observability and Audit Logging (BRONZE → SILVER)"
Added sections:
  - Principle IX: Human-in-the-Loop (HITL) Approval Workflow (NEW)
  - Principle X: Scheduling and Process Management (NEW)
  - MCP Server Integration Requirements section (NEW)
  - Silver Tier Deliverables section (NEW)
  - Extended vault structure with /Pending_Approval, /Approved, /Rejected, /Logs folders
Removed sections: None (backward compatible with Bronze)
Templates requiring updates:
  - .specify/templates/plan-template.md: ⚠ Pending (Constitution Check needs Silver tier gates)
  - .specify/templates/spec-template.md: ✅ Compatible (requirements format aligns)
  - .specify/templates/tasks-template.md: ⚠ Pending (may need MCP/HITL task categories)
Follow-up TODOs:
  - Update plan-template.md Constitution Check section with Silver tier gates
  - Consider adding MCP/HITL task examples to tasks-template.md
  - Document approval thresholds in Company_Handbook.md template
-->

# Personal AI Employee Constitution (Bronze → Silver Tier)

**Scope**: This constitution defines principles for Bronze and Silver tier hackathon deliverables. Silver tier extends Bronze with external actions, human-in-the-loop workflows, and production readiness.

## Core Principles

### I. Local-First Architecture (NON-NEGOTIABLE)

All data MUST be stored locally in the Obsidian vault. The local Markdown files are the single source of truth.

- External APIs are permitted for read operations only
- Sensitive data (credentials, tokens, PII) MUST NEVER be committed to version control
- All persistent state lives in Markdown files within the vault

**Bronze Tier Vault Structure** (MINIMUM REQUIRED):
```
/Inbox              # New items awaiting triage
/Needs_Action       # Items requiring agent processing
/Done               # Completed actions archive
```

**Silver Tier Vault Structure** (EXTENDED):
```
/Inbox              # New items awaiting triage
/Needs_Action       # Items requiring agent processing
/Pending_Approval   # Actions awaiting human approval (SILVER)
/Approved           # Human-approved actions ready for execution (SILVER)
/Rejected           # Human-rejected actions archive (SILVER)
/Done               # Completed actions archive
/Logs               # Audit logs (MANDATORY for Silver) (SILVER)
/Plans              # Generated action plans
```

**Required Files**:
- `Dashboard.md` - Real-time status summary
- `Company_Handbook.md` - Configuration and rules

**Rationale**: Local-first ensures data sovereignty and eliminates external service dependencies for core data storage. Silver tier extends with approval workflow folders and mandatory audit logging.

### II. External Actions and MCP Integration (BRONZE → SILVER)

**Bronze Tier**: Read and write operations within the vault only. No external actions required.

**Silver Tier**: External actions via MCP servers with human-in-the-loop approval.

**Bronze Allowed Operations**:
- Reading files from the vault
- Writing Markdown files to the vault (plans, summaries, responses)
- Creating action files in `/Needs_Action` based on watcher input

**Silver Allowed Operations** (EXTENDS Bronze):
- Sending emails via MCP email server
- Posting to social media (LinkedIn) via MCP server
- Browser automation via MCP Playwright server
- Any external action approved through HITL workflow

**MCP Server Requirements** (Silver Tier):
- MUST implement at least ONE working MCP server for external actions
- MCP servers MUST follow standard MCP protocol (JSON-RPC over stdio)
- ALL external actions MUST route through HITL approval workflow (see Principle IX)
- MCP server capabilities MUST be documented in `Company_Handbook.md`

**Rationale**: Bronze establishes foundation (perception + reasoning). Silver adds action capability while maintaining safety through mandatory human approval.

### III. Agent Skills Implementation (REQUIRED)

All AI functionality MUST be implemented as Claude Agent Skills, not hardcoded prompts.

- Each skill MUST be documented in a `SKILL.md` file
- Skill documentation MUST include: purpose, inputs, outputs, approval requirements
- Skills MUST be composable and independently testable
- No inline prompt strings in application code

**Skill File Format**:
```markdown
# Skill: [Name]
## Purpose
[What this skill accomplishes]
## Inputs
[Expected input format and sources]
## Outputs
[Output format and destinations]
## Approval Required
[Yes/No and conditions]
## MCP Servers Used (Silver Tier)
[List of MCP servers this skill integrates with]
```

**Silver Tier Skill Requirements** (EXTENDS Bronze):
- Skills that invoke MCP servers MUST document which servers they use
- Skills performing external actions MUST specify approval thresholds
- Skills MUST handle approval rejection gracefully
- Skills MUST log all MCP server invocations to audit log

**Rationale**: Modular skills enable maintainability, testing, and clear documentation of AI capabilities. Silver tier adds MCP integration and approval requirements.

### IV. Security and Privacy by Design

Security MUST be built into every component from the start, not added later.

**Credential Management**:
- Credentials MUST be stored in environment variables or OS credential managers
- Credentials MUST NEVER appear in vault files or source code
- API keys stored in `.env` file which MUST be gitignored

**Audit Logging**:
- **Bronze Tier**: Basic logging to console or simple log file (OPTIONAL)
- **Silver Tier**: Structured audit logging to `/Logs/` folder (MANDATORY)

**Silver Tier Audit Log Requirements** (MANDATORY):
- ALL actions MUST be logged to `/Logs/YYYY-MM-DD.json`
- Log format: `{"timestamp", "action_type", "actor", "target", "parameters", "approval_status", "result"}`
- Logs MUST be retained for minimum 90 days
- Log files MUST NOT contain sensitive credentials
- MCP server invocations MUST be logged with request/response (sanitized)

**Human-in-the-Loop Approval** (Silver Tier):
- ALL external actions MUST require human approval (see Principle IX)
- Approval requests MUST be created in `/Pending_Approval/` folder
- Auto-approval thresholds MAY be configured in `Company_Handbook.md` for low-risk actions
- Approval/rejection decisions MUST be logged to audit log

**Development Mode**:
- `DRY_RUN=true` environment variable MUST be respected during development
- Dry-run mode logs intended actions without executing them

**Rationale**: Security-first design prevents data breaches and maintains user trust. Silver tier adds mandatory audit logging and approval workflow for external actions.

### V. Multi-Watcher Architecture (BRONZE → SILVER)

**Bronze Tier**: At least ONE working watcher (Gmail OR filesystem).

**Silver Tier**: TWO OR MORE working watchers (e.g., Gmail + WhatsApp + LinkedIn + Finance).

Watcher scripts MUST be executable and capable of monitoring external sources.

**Bronze Tier Requirements**:
- Watcher script can be run manually or via simple scheduling (cron/Task Scheduler)
- Watcher MUST check for new items and create files in `/Needs_Action`
- Basic error handling: Log errors and continue operation
- Process management (PM2/watchdog) is OPTIONAL for Bronze tier

**Silver Tier Requirements** (EXTENDS Bronze):
- MUST have at least TWO distinct watchers monitoring different sources
- Process management (PM2/supervisord/watchdog) is REQUIRED for production
- Watchers MUST support graceful shutdown and restart
- Watchers MUST log health metrics to audit log
- Each watcher MUST have independent error handling and retry logic

**Configuration**:
- Check interval configurable via environment variable (default: 60 seconds)
- Watcher settings documented in `Company_Handbook.md`

**Example Silver Tier Watcher Combinations**:
- Gmail + WhatsApp (via Playwright)
- Gmail + LinkedIn + Finance tracker
- Filesystem + Gmail + Custom webhook receiver

**Rationale**: Bronze focuses on functional watcher implementation. Silver requires multiple watchers and production-grade process management for reliability.

### VI. Testing for Core Functionality (BRONZE → SILVER)

**Bronze Tier**: Manual verification of core functionality.

**Silver Tier**: Automated testing for critical paths including MCP integration.

**Bronze Tier Testing Focus**:
- Watcher successfully creates files in `/Needs_Action`
- Claude Code can read from and write to vault
- Files are properly formatted Markdown
- Manual verification is acceptable

**Silver Tier Testing Focus** (EXTENDS Bronze):
- Automated tests for MCP server integration (mock servers acceptable)
- HITL approval workflow tests (create, approve, reject, execute)
- Multi-watcher coordination tests
- Audit log validation tests
- End-to-end tests for at least one complete workflow (detection → approval → execution)

**Testing Approach**:
- Bronze: Manual verification acceptable
- Silver: Automated tests RECOMMENDED, manual E2E test REQUIRED

**Rationale**: Bronze prioritizes working functionality. Silver adds testing for safety-critical workflows (approval, MCP execution, audit logging).

### VII. Observability and Audit Logging (BRONZE → SILVER)

**Bronze Tier**: Basic dashboard with system status.

**Silver Tier**: Comprehensive observability with mandatory audit logging.

The `Dashboard.md` file MUST provide visibility into system state.

**Bronze Tier Dashboard Requirements**:
- Count of items in `/Needs_Action`
- Recent watcher activity (last check time)
- Status of Claude Code integration (last read/write operation)
- Basic system health (watcher running, vault accessible)

**Silver Tier Dashboard Requirements** (EXTENDS Bronze):
- Count of items in `/Pending_Approval`, `/Approved`, `/Rejected`
- MCP server health status (last successful invocation, error count)
- Approval workflow metrics (pending approvals, average approval time)
- Recent audit log entries (last 10 actions with approval status)
- Watcher health for ALL configured watchers

**Logging Requirements**:
- **Bronze**: Basic logging to console or simple log file (optional)
- **Silver**: JSON structured logging to `/Logs/` folder (MANDATORY)

**Silver Tier Audit Log Structure**:
```json
{
  "timestamp": "2026-01-09T17:30:00Z",
  "action_type": "email_send",
  "actor": "claude-code",
  "target": "user@example.com",
  "parameters": {"subject": "...", "body_preview": "..."},
  "approval_status": "approved",
  "approval_by": "user",
  "approval_timestamp": "2026-01-09T17:25:00Z",
  "mcp_server": "email-server",
  "result": "success",
  "error": null
}
```

**Rationale**: Bronze dashboard demonstrates functionality. Silver adds comprehensive observability and mandatory audit trail for compliance and debugging.

### VIII. Modular Watcher Architecture (BRONZE → SILVER)

Watchers SHOULD follow a common pattern for consistency.

**BaseWatcher Pattern** (Recommended):
```python
class BaseWatcher:
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval

    def check_for_updates(self):
        """Poll external source for new items - implement in subclass"""
        raise NotImplementedError

    def create_action_file(self, item):
        """Create .md file in Needs_Action folder - implement in subclass"""
        raise NotImplementedError

    def run(self):
        """Main loop - poll and create files"""
        while True:
            items = self.check_for_updates()
            for item in items:
                self.create_action_file(item)
            time.sleep(self.check_interval)
```

**Bronze Tier Requirements**:
- At least ONE working watcher (Gmail OR filesystem)
- Watcher creates Markdown files in `/Needs_Action`
- Basic duplicate prevention (track processed IDs)
- Configuration via environment variables or config file

**Silver Tier Requirements** (EXTENDS Bronze):
- At least TWO working watchers with shared base class
- Each watcher MUST implement health check method
- Watchers MUST support graceful shutdown via signal handling
- Watcher registry/coordinator for multi-watcher management
- Standardized error handling and retry logic across all watchers

**Rationale**: Modular pattern enables future expansion. Silver requires consistent architecture across multiple watchers for maintainability.

### IX. Human-in-the-Loop (HITL) Approval Workflow (SILVER TIER - NEW)

ALL external actions in Silver tier MUST require explicit human approval before execution.

**Approval Workflow** (MANDATORY for Silver):

1. **Action Proposal**: Claude Code creates proposal in `/Pending_Approval/` folder
2. **Human Review**: User reviews proposal and moves to `/Approved/` or `/Rejected/`
3. **Execution**: Approved actions are executed via MCP servers
4. **Archival**: Completed actions moved to `/Done/`, rejected to `/Rejected/`

**Approval File Format**:
```markdown
---
type: approval_request
action: [email_send|linkedin_post|browser_action|etc]
created: [ISO_TIMESTAMP]
status: pending
risk_level: [low|medium|high]
auto_approve_eligible: [true|false]
mcp_server: [server_name]
---

# Approval Request: [Brief Title]

## Proposed Action
[What will be done - clear, specific description]

## Target
[Email address, LinkedIn profile, URL, etc.]

## Parameters
[Detailed parameters for the action]

## Rationale
[Why this action is being proposed]

## Risk Assessment
[What could go wrong, impact if error occurs]

## Approval Instructions
- Move to `/Approved/` to execute
- Move to `/Rejected/` to cancel
```

**Auto-Approval Thresholds** (Optional):
- MAY be configured in `Company_Handbook.md` for low-risk actions
- MUST specify exact criteria (e.g., "emails < 100 words to known contacts")
- MUST still log to audit log with "auto_approved" status
- User MUST be able to disable auto-approval globally

**Approval Timeout**:
- Approval requests older than 24 hours SHOULD be flagged in Dashboard
- No automatic rejection - human must explicitly reject or approve

**Rationale**: HITL ensures human oversight for all external actions, preventing unintended consequences while enabling automation for approved workflows.

### X. Scheduling and Process Management (SILVER TIER - NEW)

Silver tier requires production-ready scheduling and process management.

**Scheduling Requirements** (MANDATORY for Silver):
- Watchers MUST be scheduled via cron (Linux/Mac) or Task Scheduler (Windows)
- At least one scheduled operation MUST be configured and documented
- Schedule configuration MUST be documented in `README.md`

**Example Cron Schedule**:
```bash
# Check Gmail every 5 minutes
*/5 * * * * cd /path/to/AI_Employee && uv run python run_watcher.py gmail

# Check WhatsApp every 10 minutes
*/10 * * * * cd /path/to/AI_Employee && uv run python run_watcher.py whatsapp
```

**Process Management** (REQUIRED for Silver):
- Watchers MUST be managed by process supervisor (PM2/supervisord/watchdog)
- Process manager MUST restart watchers on crash
- Process manager MUST log watcher lifecycle events
- Health checks MUST be implemented for each watcher

**Example PM2 Configuration**:
```json
{
  "apps": [
    {
      "name": "gmail-watcher",
      "script": "run_watcher.py",
      "args": "gmail",
      "interpreter": "uv run python",
      "autorestart": true,
      "max_restarts": 10,
      "min_uptime": "10s"
    },
    {
      "name": "whatsapp-watcher",
      "script": "run_watcher.py",
      "args": "whatsapp",
      "interpreter": "uv run python",
      "autorestart": true,
      "max_restarts": 10,
      "min_uptime": "10s"
    }
  ]
}
```

**Graceful Shutdown**:
- ALL watchers MUST handle SIGTERM/SIGINT signals
- Shutdown MUST update Dashboard to "stopped" status
- In-progress operations MUST complete or save state before exit

**Rationale**: Production readiness requires reliable scheduling and automatic recovery from failures. Bronze can run manually; Silver must run autonomously.

## Technology Stack

**Bronze Tier - Required Components**:
| Component | Minimum Version | Purpose | Required? |
|-----------|----------------|---------|-----------|
| Obsidian | v1.10.6+ | Vault management and UI | ✅ Yes |
| Claude Code | claude-3-5-sonnet or Router | AI processing | ✅ Yes |
| Python | 3.13+ | Watcher scripts | ✅ Yes |
| Node.js | v24+ | Optional (for MCP servers) | ❌ No |
| PM2 | Latest | Optional (process management) | ❌ No |

**Silver Tier - Required Components** (EXTENDS Bronze):
| Component | Minimum Version | Purpose | Required? |
|-----------|----------------|---------|-----------|
| Obsidian | v1.10.6+ | Vault management and UI | ✅ Yes |
| Claude Code | claude-3-5-sonnet or Router | AI processing | ✅ Yes |
| Python | 3.13+ | Watcher scripts | ✅ Yes |
| Node.js | v24+ | MCP servers | ✅ Yes (Silver) |
| PM2/supervisord | Latest | Process management | ✅ Yes (Silver) |
| Playwright | Latest | WhatsApp/browser automation | ⚠️ If using WhatsApp watcher |

**Additional Tools** (Silver Tier):
- MCP Email Server: Required for email sending actions
- MCP Playwright Server: Required for browser/WhatsApp automation
- MCP Custom Servers: For social media, finance APIs, etc.
- GitHub Desktop: For version control (recommended)

## MCP Server Integration Requirements (SILVER TIER)

**Minimum Requirement**: At least ONE working MCP server for external actions.

**MCP Server Standards**:
- MUST follow Model Context Protocol (JSON-RPC over stdio)
- MUST be documented in `Company_Handbook.md` with:
  - Server name and purpose
  - Available actions/tools
  - Required environment variables
  - Example usage
- MUST implement error handling and return structured errors
- MUST support dry-run mode (when `DRY_RUN=true`)

**Common MCP Servers for Silver Tier**:

1. **Email Server** (Recommended):
   - Actions: send_email, send_reply
   - Environment: SMTP credentials or Gmail API
   - Approval: Required for all sends

2. **LinkedIn Server** (For social media automation):
   - Actions: create_post, like_post, send_message
   - Environment: LinkedIn API credentials
   - Approval: Required for all posts/messages

3. **Playwright Server** (For browser/WhatsApp):
   - Actions: navigate, click, type, screenshot
   - Environment: Browser binary paths
   - Approval: Required for all actions

4. **Custom Finance Server** (Example):
   - Actions: check_balance, categorize_expense
   - Environment: Bank API or CSV file path
   - Approval: Required for writes, optional for reads

**MCP Server Discovery**:
- MCP servers MUST be configured in Claude Code MCP settings
- Skills MUST verify MCP server availability before proposing actions
- Dashboard MUST show MCP server health status

**Rationale**: MCP servers provide standardized, safe interface for external actions. Separation of concerns: Claude Code reasons, MCP servers act.

## Security Requirements

### Bronze Tier Security

**Credential Management**:
- API keys and tokens MUST be stored in `.env` file (gitignored)
- Credentials MUST NEVER appear in vault files or source code
- `.env` file MUST be added to `.gitignore`

**Basic Security Practices**:
- Never commit `.env` files
- Document required environment variables in `README.md`
- Use test/sandbox accounts during development if available

### Silver Tier Security (EXTENDS Bronze)

**Credential Management** (ENHANCED):
- Production credentials MUST use OS credential manager (Keychain/Credential Manager)
- API keys rotated every 90 days (documented in `Company_Handbook.md`)
- Separate credentials for development/production environments

**Approval Thresholds**:
- Auto-approval MUST be disabled by default
- If enabled, auto-approval MUST be limited to:
  - Low-risk actions (defined in `Company_Handbook.md`)
  - Known trusted targets (allowlist)
  - Actions below specified limits (e.g., email < 100 words)

**Audit and Compliance**:
- Audit logs MUST be retained for 90 days minimum
- Audit logs MUST NOT contain credentials or sensitive PII
- Failed approval requests MUST be logged with rejection reason
- MCP server errors MUST be logged with sanitized parameters

**Rate Limiting**:
- External actions MUST respect API rate limits
- Automatic backoff on rate limit errors
- Daily/hourly limits configurable in `Company_Handbook.md`

## Bronze Tier Deliverables (Hackathon Requirements)

**Estimated Time**: 8-12 hours

**Minimum Viable Deliverables**:

1. **Obsidian Vault Structure** ✅
   - [ ] `Dashboard.md` with basic status updates
   - [ ] `Company_Handbook.md` with configuration
   - [ ] Folders: `/Inbox`, `/Needs_Action`, `/Done`

2. **One Working Watcher** ✅
   - [ ] Gmail watcher OR filesystem watcher
   - [ ] Creates `.md` files in `/Needs_Action` folder
   - [ ] Basic duplicate prevention

3. **Claude Code Integration** ✅
   - [ ] Claude Code successfully reads from vault
   - [ ] Claude Code successfully writes to vault (creates Plan.md files)
   - [ ] At least one Agent Skill implemented and documented as `SKILL.md`

4. **Basic Documentation** ✅
   - [ ] README.md with setup instructions
   - [ ] `.env.example` file showing required variables
   - [ ] Basic folder structure documented

## Silver Tier Deliverables (Hackathon Requirements - EXTENDS Bronze)

**Estimated Time**: 16-24 hours (includes Bronze)

**Minimum Viable Deliverables**:

1. **Multi-Watcher System** ✅
   - [ ] At least TWO working watchers (e.g., Gmail + WhatsApp)
   - [ ] Process manager configured (PM2/supervisord)
   - [ ] Health monitoring for each watcher

2. **MCP Server Integration** ✅
   - [ ] At least ONE working MCP server (email recommended)
   - [ ] MCP server documented in `Company_Handbook.md`
   - [ ] Skills integrated with MCP server

3. **Human-in-the-Loop Workflow** ✅
   - [ ] `/Pending_Approval`, `/Approved`, `/Rejected` folders created
   - [ ] Approval request skill implemented
   - [ ] At least one approval → execution workflow tested

4. **Social Media Automation** ✅
   - [ ] LinkedIn posting capability via MCP server
   - [ ] Approval workflow for LinkedIn posts
   - [ ] At least one successful post via approval workflow

5. **Audit Logging** ✅
   - [ ] `/Logs` folder with JSON structured logs
   - [ ] All external actions logged with approval status
   - [ ] Dashboard displays recent audit entries

6. **Scheduling** ✅
   - [ ] Cron/Task Scheduler configured for watchers
   - [ ] Scheduled operations documented in README
   - [ ] At least one scheduled watcher running continuously

7. **Enhanced Documentation** ✅
   - [ ] README includes Silver tier setup (MCP, scheduling, approvals)
   - [ ] `Company_Handbook.md` includes approval thresholds
   - [ ] `.env.example` includes MCP server variables

## Error Handling

### Bronze Tier Error Handling

**Watcher Errors**:
- Log errors to console or simple log file
- Continue operation (don't crash on single failure)
- Log timestamp and error message
- Document common errors in `Company_Handbook.md`

**API Errors**:
- Handle common errors (rate limits, timeouts)
- Log error and retry once after short delay (optional)
- If repeated failures, log and continue to next check cycle
- Do not expose credentials in error messages

**Claude Code Errors**:
- If vault I/O fails, log error
- Ensure vault permissions are correct
- Document troubleshooting steps in README

### Silver Tier Error Handling (EXTENDS Bronze)

**MCP Server Errors**:
- Log MCP errors to audit log with sanitized parameters
- Retry with exponential backoff (max 3 retries)
- If MCP server unavailable, create notification in `/Needs_Action/`
- Dashboard MUST show MCP server error count

**Approval Workflow Errors**:
- If approval file malformed, move to `/Needs_Action/` with error note
- If approval timeout exceeded, flag in Dashboard (no auto-reject)
- If execution fails after approval, log error and notify user

**Process Management Errors**:
- PM2/supervisord MUST restart crashed watchers
- Log crash count and last error to Dashboard
- If crash loop detected (>10 crashes in 1 hour), disable auto-restart and notify

**Recovery Procedures**:
- Document recovery procedures in `Company_Handbook.md`
- Include commands for manual restart, log inspection, state reset
- Provide troubleshooting flowchart for common errors

## Governance

This constitution is the authoritative source for project principles and practices. All development decisions MUST comply with these principles.

**Amendment Process**:
1. Propose amendment via pull request
2. Document rationale and impact
3. Update version number per semantic versioning
4. Update dependent templates if affected
5. Require explicit approval before merge

**Versioning Policy**:
- MAJOR: Backward incompatible principle changes or removals
- MINOR: New principles or material expansions (e.g., Bronze → Silver)
- PATCH: Clarifications and non-semantic refinements

**Compliance Review**:
- All PRs MUST verify compliance with constitution
- Code reviews MUST check adherence to principles
- Violations MUST be documented and remediated

**Tier Compatibility**:
- Silver tier MUST remain backward compatible with Bronze tier
- All Bronze deliverables MUST work without Silver features
- Silver features MUST be additive, not replacements

**Version**: 1.1.0 | **Ratified**: 2026-01-09 | **Last Amended**: 2026-01-09

**Note**: This constitution now supports both Bronze and Silver tiers. Bronze tier focuses on detection (watchers) and reasoning (Claude Code). Silver tier adds action capability (MCP servers), safety (HITL approval workflow), and production readiness (scheduling, process management, mandatory audit logging). Gold tier will further extend with advanced scheduling, multi-user support, and autonomous decision-making within approved boundaries.
