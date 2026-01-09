<!--
SYNC IMPACT REPORT
==================
Version change: 0.0.0 → 1.0.0 (MAJOR - initial constitution)
Modified principles: N/A (new file)
Added sections:
  - 8 Core Principles (Local-First, HITL, Agent Skills, Security, Autonomous Ops, Test-First, Observability, Modular Watchers)
  - Technology Stack section
  - Security Requirements section
  - Bronze Tier Deliverables section
  - Error Handling section
  - Governance section
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ Compatible (Constitution Check section aligns)
  - .specify/templates/spec-template.md: ✅ Compatible (requirements format aligns)
  - .specify/templates/tasks-template.md: ✅ Compatible (phase structure aligns)
Follow-up TODOs: None
-->

# Personal AI Employee Constitution (Bronze Tier)

**Scope**: This constitution defines the minimum viable principles for achieving Bronze tier hackathon deliverables.

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

**Required Files**:
- `Dashboard.md` - Real-time status summary
- `Company_Handbook.md` - Configuration and rules

**Rationale**: Local-first ensures data sovereignty and eliminates external service dependencies for core data storage.

### II. Read-Only Operations (BRONZE TIER)

For Bronze tier, Claude Code MUST only perform read and write operations within the vault. No external actions (sending emails, payments, social media) are required.

**Allowed Operations**:
- Reading files from the vault
- Writing Markdown files to the vault (plans, summaries, responses)
- Creating action files in `/Needs_Action` based on watcher input

**Bronze Tier Limitation**: External actions (email sending, payments, etc.) are out of scope. Focus is on detection (watchers) and reasoning (Claude Code) only.

**Rationale**: Bronze tier establishes the foundation - perception (watchers) and reasoning (Claude) - without requiring action capabilities.

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
```

**Rationale**: Modular skills enable maintainability, testing, and clear documentation of AI capabilities.

### IV. Security and Privacy by Design

Security MUST be built into every component from the start, not added later.

**Credential Management**:
- Credentials MUST be stored in environment variables or OS credential managers
- Credentials MUST NEVER appear in vault files or source code
- API keys stored in `.env` file which MUST be gitignored

**Audit Logging**:
- ALL actions MUST be logged to `/Vault/Logs/YYYY-MM-DD.json`
- Log format: `{"timestamp", "action_type", "actor", "target", "parameters", "approval_status", "result"}`
- Logs MUST be retained for minimum 90 days
- Log files MUST NOT contain sensitive credentials

**Development Mode**:
- `DRY_RUN=true` environment variable MUST be respected during development
- Dry-run mode logs intended actions without executing them

**Rationale**: Security-first design prevents data breaches and maintains user trust.

### V. Simple Watcher Execution (BRONZE TIER)

Watcher scripts MUST be executable and capable of monitoring external sources.

**Bronze Tier Requirements**:
- Watcher script can be run manually or via simple scheduling (cron/Task Scheduler)
- Watcher MUST check for new items and create files in `/Needs_Action`
- Basic error handling: Log errors and continue operation
- Process management (PM2/watchdog) is OPTIONAL for Bronze tier

**Configuration**:
- Check interval configurable via environment variable (default: 60 seconds)
- Watcher settings documented in `Company_Handbook.md`

**Rationale**: Bronze tier focuses on functional watcher implementation, not production-grade process management.

### VI. Basic Testing for Core Functionality (BRONZE TIER)

Core functionality SHOULD be tested to verify it works.

**Bronze Tier Testing Focus**:
- Watcher successfully creates files in `/Needs_Action`
- Claude Code can read from and write to vault
- Files are properly formatted Markdown

**Testing Approach**: Manual verification is acceptable for Bronze tier. Automated tests are recommended but not required.

**Rationale**: Bronze tier prioritizes working functionality over comprehensive test coverage.

### VII. Basic Dashboard (BRONZE TIER)

The `Dashboard.md` file MUST provide visibility into system state.

**Bronze Tier Dashboard Requirements**:
- Count of items in `/Needs_Action`
- Recent watcher activity (last check time)
- Status of Claude Code integration (last read/write operation)
- Basic system health (watcher running, vault accessible)

**Logging**:
- Basic logging to console or simple log file
- JSON structured logging is OPTIONAL for Bronze tier
- Log watcher errors and Claude Code operations

**Rationale**: Bronze tier dashboard demonstrates the system is functioning, without requiring advanced observability.

### VIII. Modular Watcher Architecture (BRONZE TIER)

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

**Rationale**: Modular pattern enables future expansion while keeping Bronze tier simple and focused.

## Technology Stack (Bronze Tier)

**Required Components**:
| Component | Minimum Version | Purpose | Required? |
|-----------|----------------|---------|-----------|
| Obsidian | v1.10.6+ | Vault management and UI | ✅ Yes |
| Claude Code | claude-3-5-sonnet or Router | AI processing | ✅ Yes |
| Python | 3.13+ | Watcher scripts | ✅ Yes |
| Node.js | v24+ | Optional (for MCP servers) | ❌ No |
| PM2 | Latest | Optional (process management) | ❌ No |

**Additional Tools** (Optional for Bronze):
- MCP Servers: Not required for Bronze tier
- Playwright: Only if implementing WhatsApp watcher (not required)
- GitHub Desktop: For version control (recommended)

## Security Requirements (Bronze Tier)

### Credential Management

**MANDATORY**:
- API keys and tokens MUST be stored in `.env` file (gitignored)
- Credentials MUST NEVER appear in vault files or source code
- `.env` file MUST be added to `.gitignore`

**Optional for Bronze**:
- OS Credential Manager for sensitive passwords (recommended but not required)
- Environment variable validation

### Basic Security Practices

- Never commit `.env` files
- Document required environment variables in `README.md`
- Use test/sandbox accounts during development if available

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

## Error Handling (Bronze Tier)

### Basic Error Handling

**Watcher Errors**:
- Log errors to console or simple log file
- Continue operation (don't crash on single failure)
- Log timestamp and error message
- Document common errors in `Company_Handbook.md`

### API Errors

**For Gmail/External APIs**:
- Handle common errors (rate limits, timeouts)
- Log error and retry once after short delay (optional)
- If repeated failures, log and continue to next check cycle
- Do not expose credentials in error messages

### Claude Code Errors

- If vault I/O fails, log error
- Ensure vault permissions are correct
- Document troubleshooting steps in README

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
- MINOR: New principles or material expansions
- PATCH: Clarifications and non-semantic refinements

**Compliance Review**:
- All PRs MUST verify compliance with constitution
- Code reviews MUST check adherence to principles
- Violations MUST be documented and remediated

**Version**: 1.0.0 | **Ratified**: 2026-01-09 | **Last Amended**: 2026-01-09

**Note**: This constitution is scoped specifically for Bronze tier hackathon deliverables. Silver and Gold tiers will extend these principles with additional capabilities (MCP servers, HITL workflows, scheduled operations, etc.) as defined in their respective feature specifications.
