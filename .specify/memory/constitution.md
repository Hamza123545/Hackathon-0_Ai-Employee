<!--
SYNC IMPACT REPORT
==================
Version change: 1.1.0 → 1.2.0 (MINOR - Gold Tier additions)
Modified principles:
  - Principle III: "Agent Skills Implementation" → Extended with autonomous processing requirements
  - Principle IV: "Security and Privacy by Design" → Extended with cross-domain security
  - Principle VII: "Observability and Audit Logging" → Extended with business intelligence reporting
Added sections:
  - Principle XI: Autonomous Operation (GOLD TIER - NEW)
  - Principle XII: Cross-Domain Integration (GOLD TIER - NEW)
  - Principle XIII: Business Intelligence and Reporting (GOLD TIER - NEW)
  - Gold Tier MCP Servers: Xero, Facebook, Instagram, Twitter/X
  - Gold Tier Deliverables section (NEW)
  - Extended vault structure with /Business, /Accounting, /Briefings folders
  - Weekly Business and Accounting Audit requirements
Removed sections: None (backward compatible with Bronze and Silver)
Templates requiring updates:
  - .specify/templates/plan-template.md: ⚠ Pending (Constitution Check needs Gold tier gates)
  - .specify/templates/spec-template.md: ✅ Compatible (requirements format aligns)
  - .specify/templates/tasks-template.md: ⚠ Pending (may need autonomous processing task categories)
Follow-up TODOs:
  - Update plan-template.md Constitution Check section with Gold tier gates
  - Document Xero integration in Company_Handbook.md
  - Create CEO Briefing template in /Briefings folder
  - Document autonomous processing configuration
-->

# Personal AI Employee Constitution (Bronze → Silver → Gold Tier)

**Scope**: This constitution defines principles for Bronze, Silver, and Gold tier hackathon deliverables. Bronze establishes the foundation (detection + reasoning), Silver adds external actions with human-in-the-loop workflows, and Gold achieves autonomous cross-domain operation with business intelligence.

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

**Gold Tier Vault Structure** (EXTENDED):
```
/Inbox              # New items awaiting triage
/Needs_Action       # Items requiring agent processing (Personal + Business)
/Pending_Approval   # Actions awaiting human approval
/Approved           # Human-approved actions ready for execution
/Rejected           # Human-rejected actions archive
/Done               # Completed actions archive
/Logs               # Audit logs (MANDATORY)
/Plans              # Generated action plans
/Business           # Business-related action items and tasks (GOLD)
/Accounting         # Financial data and transactions from Xero (GOLD)
/Briefings          # CEO briefings and audit reports (GOLD)
```

**Required Files**:
- `Dashboard.md` - Real-time status summary
- `Company_Handbook.md` - Configuration and rules

**Rationale**: Local-first ensures data sovereignty and eliminates external service dependencies for core data storage. Silver tier extends with approval workflow folders and mandatory audit logging. Gold tier adds cross-domain folders (Business, Accounting, Briefings) for unified personal and business intelligence.

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

**Gold Tier Autonomous Processing** (EXTENDS Bronze and Silver):
- AI Processor MUST run automatically without manual skill invocation
- Skills MUST be invocable by the autonomous AI Processor
- Skills MUST support background processing and self-scheduling
- Skills MUST handle cross-domain operations (Personal + Business)

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

### XI. Autonomous Operation (GOLD TIER - NEW)

Gold tier achieves autonomous operation where the AI Employee processes action items automatically without manual skill invocation.

**Autonomous AI Processor Requirements** (MANDATORY for Gold):
- AI Processor script MUST run continuously in the background
- Processor MUST automatically detect new files in `/Needs_Action/`
- Processor MUST invoke appropriate Agent Skills based on action item type
- Processor MUST handle both Personal and Business domain action items
- Processor MUST coordinate multi-step workflows autonomously

**Background Processing**:
- AI Processor runs as a daemon/service (PM2/systemd/Windows Service)
- File system watcher monitors `/Needs_Action/` for new files
- Auto-processing triggered on file creation (no manual invocation)
- Skills execute in sequence with dependency handling
- Results logged to `/Logs/` with autonomous execution flag

**Self-Scheduling**:
- Processor MUST schedule periodic tasks (weekly audits, briefings)
- Configurable processing intervals in `Company_Handbook.md`
- Priority queue for urgent vs routine action items
- Rate limiting to prevent overwhelming external APIs

**Example Autonomous Flow**:
```
1. Watcher creates file in /Needs_Action/email_inquiry.md
2. AI Processor detects new file automatically
3. Processor invokes @process-action-items skill
4. Skill analyzes email and creates plan in /Plans/
5. If external action needed, creates approval request in /Pending_Approval/
6. Human approves → moves to /Approved/
7. Processor detects approved file automatically
8. Processor invokes @execute-approved-actions skill
9. Action executed via MCP server, logged, archived to /Done/
```

**Configuration**:
- `AI_PROCESSOR_ENABLED=true` - Enable autonomous processing
- `PROCESSING_INTERVAL=30` - Check for new files every 30 seconds
- `AUTO_PROCESS_PERSONAL=true` - Auto-process personal domain items
- `AUTO_PROCESS_BUSINESS=true` - Auto-process business domain items

**Rationale**: Autonomous operation eliminates manual intervention for routine tasks, enabling the AI Employee to operate continuously without human oversight for detection and planning phases. Human approval still required for external actions (HITL workflow).

### XII. Cross-Domain Integration (GOLD TIER - NEW)

Gold tier unifies Personal and Business domains into a single integrated AI Employee system.

**Domain Architecture** (MANDATORY for Gold):
- **Personal Domain**: Gmail, WhatsApp, LinkedIn (personal), filesystem monitoring
- **Business Domain**: Xero accounting, Facebook, Instagram, Twitter/X (business)
- Unified vault structure with domain-specific folders
- Cross-domain action coordination (e.g., expense from Gmail → Xero)

**Personal Domain Requirements**:
- All Silver tier personal watchers continue to operate
- Personal action items routed to standard folders
- Personal external actions (email, personal LinkedIn) via existing MCP servers

**Business Domain Requirements** (NEW for Gold):
- Xero MCP Server for accounting integration (invoices, expenses, reports)
- Facebook MCP Server for business page posting and engagement
- Instagram MCP Server for business account posting and analytics
- Twitter/X MCP Server for business profile posting and monitoring

**Cross-Domain Workflows**:
- Expense emails detected by Gmail watcher → Xero accounting entry
- Business inquiry from LinkedIn → Facebook/Twitter response coordination
- Weekly financial report from Xero → CEO briefing in `/Briefings/`
- Social media mentions → Unified response across Facebook/Instagram/Twitter

**Unified Dashboard**:
- Single `Dashboard.md` shows status for ALL domains
- Personal metrics: emails, messages, personal tasks
- Business metrics: accounting transactions, social media engagement, business tasks
- Cross-domain KPIs: response times, automation rate, approval workflow metrics

**Domain-Specific Folders**:
- `/Business/` - Business action items (social media, partnerships, sales)
- `/Accounting/` - Financial data from Xero (invoices, expenses, reports)
- Standard folders (`/Needs_Action/`, `/Logs/`, etc.) handle both domains

**Rationale**: Cross-domain integration enables the AI Employee to handle both personal and business responsibilities from a single system, with unified observability and audit trail. This reflects real-world scenarios where personal and business tasks often overlap.

### XIII. Business Intelligence and Reporting (GOLD TIER - NEW)

Gold tier adds automated business intelligence with weekly audits and CEO briefings.

**Weekly Business and Accounting Audit** (MANDATORY for Gold):
- Automated weekly audit of business and accounting activity
- Audit generated every Monday at 9:00 AM (configurable)
- Audit aggregates data from Xero, social media, and business action items
- Audit saved to `/Briefings/audit_YYYY-MM-DD.md`

**Audit Report Structure**:
```markdown
---
type: business_audit
period: YYYY-WW (ISO week)
generated: ISO_TIMESTAMP
---

# Weekly Business & Accounting Audit

## Financial Summary (from Xero)
- Revenue: $X
- Expenses: $Y
- Net: $Z
- Outstanding Invoices: N
- Overdue Payments: M

## Social Media Performance
- Facebook: X posts, Y engagement
- Instagram: X posts, Y engagement
- Twitter/X: X posts, Y engagement

## Action Item Summary
- Business actions processed: N
- Approvals granted: M
- Approvals rejected: K
- Average response time: Xh

## Alerts & Recommendations
[AI-generated insights and recommendations]
```

**CEO Briefing Generation** (MANDATORY for Gold):
- AI-generated executive summary from weekly audit
- Key insights, trends, and actionable recommendations
- Briefing saved to `/Briefings/ceo_briefing_YYYY-MM-DD.md`
- Briefing includes cross-domain metrics (personal + business)

**CEO Briefing Structure**:
```markdown
---
type: ceo_briefing
period: YYYY-WW
generated: ISO_TIMESTAMP
---

# CEO Briefing: Week of [Date]

## Executive Summary
[1-2 paragraph overview of the week]

## Financial Highlights
- Key financial metrics
- Notable transactions
- Cash flow status

## Business Development
- Social media growth
- Customer engagement
- Lead generation

## Operational Efficiency
- Automation rate
- Response times
- System health

## Action Items for CEO
1. [Prioritized action requiring CEO attention]
2. [Prioritized action requiring CEO attention]

## Upcoming Priorities
[Next week's focus areas]
```

**Xero Integration Requirements**:
- MCP Server MUST connect to Xero API
- Read access: invoices, expenses, bank transactions, reports
- Write access: expense entries (with approval), invoice creation (with approval)
- Sync frequency: Every 6 hours or on-demand
- All Xero actions MUST be logged to `/Logs/` and require approval

**Scheduled Reports**:
- Weekly audit: Every Monday 9:00 AM
- CEO briefing: Every Monday 10:00 AM (after audit)
- Monthly financial summary: First Monday of each month
- Configurable in `Company_Handbook.md`

**Rationale**: Business intelligence and automated reporting provide executives with actionable insights without manual data aggregation. Weekly audits ensure consistent oversight of business and financial operations.

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

**Gold Tier - Required Components** (EXTENDS Silver):
| Component | Minimum Version | Purpose | Required? |
|-----------|----------------|---------|-----------|
| All Silver Components | - | Foundation | ✅ Yes |
| Xero MCP Server | Latest | Accounting integration | ✅ Yes (Gold) |
| Facebook MCP Server | Latest | Business social media | ✅ Yes (Gold) |
| Instagram MCP Server | Latest | Business social media | ✅ Yes (Gold) |
| Twitter/X MCP Server | Latest | Business social media | ✅ Yes (Gold) |
| AI Processor Daemon | - | Autonomous processing | ✅ Yes (Gold) |
| Scheduler (cron/systemd) | - | Weekly audits & briefings | ✅ Yes (Gold) |

**Additional Tools** (Gold Tier):
- Xero API Credentials: Required for accounting integration
- Facebook Business Account: Required for business page automation
- Instagram Business Account: Required for business profile automation
- Twitter/X Developer Account: Required for business profile automation
- All social media MCP servers MUST support OAuth authentication

## MCP Server Integration Requirements (SILVER → GOLD TIER)

**Silver Tier Minimum**: At least ONE working MCP server for external actions.

**Gold Tier Minimum**: At least FOUR working MCP servers (personal + business domains).

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

**Gold Tier MCP Servers** (REQUIRED):

5. **Xero Accounting Server** (MANDATORY for Gold):
   - Actions: get_invoices, create_invoice, log_expense, get_financial_report
   - Environment: Xero API credentials (OAuth 2.0)
   - Approval: Required for all write actions (create_invoice, log_expense)
   - Read-only actions (reports) may be auto-approved for weekly audits

6. **Facebook Business Server** (MANDATORY for Gold):
   - Actions: create_post, get_insights, schedule_post, reply_to_comment
   - Environment: Facebook Business API credentials
   - Approval: Required for all posts and replies

7. **Instagram Business Server** (MANDATORY for Gold):
   - Actions: create_post, create_story, get_analytics, reply_to_dm
   - Environment: Instagram Business API credentials
   - Approval: Required for all posts and replies

8. **Twitter/X Business Server** (MANDATORY for Gold):
   - Actions: create_tweet, reply_to_tweet, get_mentions, schedule_tweet
   - Environment: Twitter/X API credentials (OAuth 1.0a or 2.0)
   - Approval: Required for all tweets and replies

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

## Gold Tier Deliverables (Hackathon Requirements - EXTENDS Silver)

**Estimated Time**: 24-36 hours (includes Bronze + Silver)

**Minimum Viable Deliverables**:

1. **Autonomous AI Processor** ✅
   - [ ] AI Processor daemon/service running continuously
   - [ ] Automatic detection and processing of `/Needs_Action/` files
   - [ ] Background processing without manual skill invocation
   - [ ] Process management (PM2/systemd/Windows Service)

2. **Cross-Domain Integration** ✅
   - [ ] Unified vault with `/Business/`, `/Accounting/`, `/Briefings/` folders
   - [ ] Personal domain watchers (Gmail, WhatsApp, LinkedIn) operational
   - [ ] Business domain watchers operational
   - [ ] Cross-domain workflows implemented (e.g., expense email → Xero)

3. **Xero Accounting Integration** ✅
   - [ ] Xero MCP Server implemented and documented
   - [ ] Read access to invoices, expenses, reports
   - [ ] Write access with approval workflow (create invoice, log expense)
   - [ ] Sync every 6 hours or on-demand

4. **Multi-Platform Social Media Automation** ✅
   - [ ] Facebook MCP Server for business page posting
   - [ ] Instagram MCP Server for business account posting
   - [ ] Twitter/X MCP Server for business profile posting
   - [ ] Unified social media posting workflow with approval
   - [ ] Cross-platform response coordination

5. **Weekly Business and Accounting Audit** ✅
   - [ ] Automated weekly audit scheduled (Monday 9:00 AM)
   - [ ] Aggregates data from Xero, Facebook, Instagram, Twitter/X
   - [ ] Audit report saved to `/Briefings/audit_YYYY-MM-DD.md`
   - [ ] Financial summary, social media metrics, action item summary

6. **CEO Briefing Generation** ✅
   - [ ] Automated CEO briefing generated weekly (Monday 10:00 AM)
   - [ ] AI-generated executive summary with insights
   - [ ] Briefing saved to `/Briefings/ceo_briefing_YYYY-MM-DD.md`
   - [ ] Includes financial highlights, business development, action items

7. **Enhanced Error Recovery** ✅
   - [ ] Graceful degradation when MCP servers unavailable
   - [ ] Retry logic with exponential backoff
   - [ ] Comprehensive audit logging for all domains
   - [ ] Dashboard shows health status for all MCP servers

8. **Comprehensive Documentation** ✅
   - [ ] README includes Gold tier setup (autonomous processing, Xero, social media)
   - [ ] Architecture documentation with cross-domain workflows
   - [ ] Lessons learned document
   - [ ] `.env.example` includes all Gold tier MCP server variables

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

### Gold Tier Error Handling (EXTENDS Silver)

**Autonomous Processor Errors**:
- If AI Processor crashes, PM2/systemd MUST restart automatically
- Log all processing errors to `/Logs/processor_errors.json`
- If repeated crashes (>5 in 1 hour), disable auto-restart and notify CEO
- Dashboard MUST show processor uptime and error count

**Cross-Domain Errors**:
- If Xero API unavailable, cache requests and retry when service restored
- If social media API rate limited, queue posts with exponential backoff
- Log cross-domain errors with source domain flag
- Dashboard MUST show health status for each domain (Personal, Business)

**Business Intelligence Errors**:
- If weekly audit fails, retry 3 times with 1-hour delay
- If audit still fails, generate partial report with available data
- Log missing data sources in audit report
- Send notification to CEO if audit incomplete

**MCP Server Redundancy** (RECOMMENDED for Gold):
- Configure fallback MCP servers for critical services
- If primary Xero server fails, fallback to secondary or manual mode
- If social media posting fails, create notification in `/Needs_Action/`

**Graceful Degradation**:
- Personal domain continues operating if Business domain fails
- Business domain continues operating if Personal domain fails
- Core functionality (detection, reasoning, planning) never blocked by MCP errors
- Weekly audits generate with partial data if some sources unavailable

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
- Gold tier MUST remain backward compatible with Bronze and Silver tiers
- All Bronze deliverables MUST work without Silver or Gold features
- All Silver deliverables MUST work without Gold features
- Higher tier features MUST be additive, not replacements
- Autonomous processing (Gold) can be disabled to operate in Silver mode

**Version**: 1.2.0 | **Ratified**: 2026-01-09 | **Last Amended**: 2026-01-12

**Note**: This constitution supports Bronze, Silver, and Gold tiers. Bronze tier focuses on detection (watchers) and reasoning (Claude Code). Silver tier adds action capability (MCP servers), safety (HITL approval workflow), and production readiness (scheduling, process management, mandatory audit logging). Gold tier achieves autonomous operation (AI Processor), cross-domain integration (Personal + Business), business intelligence (weekly audits, CEO briefings), and comprehensive external integration (Xero accounting, Facebook, Instagram, Twitter/X).
