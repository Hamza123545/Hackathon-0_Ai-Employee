# Prompt for Silver Tier Specification

**Use this prompt with `/sp.specify` to create the Silver tier feature specification:**

---

## Prompt for /sp.specify

```
Build a Silver tier Personal AI Employee system that extends the Bronze tier with external actions, MCP server integration, and human-in-the-loop approval workflows. All Bronze tier capabilities remain (watchers, action item processing, plans, dashboard). Silver tier adds: multiple watchers (Gmail + WhatsApp + LinkedIn), external actions via MCP servers (email sending, LinkedIn posting, browser automation), mandatory approval workflow for sensitive actions (/Pending_Approval, /Approved, /Rejected folders), scheduled operations via cron/Task Scheduler, process management with PM2/watchdog, and mandatory audit logging to /Logs/ folder.

**Core Silver Tier Additions**:
1. Additional watchers: WhatsApp watcher (Playwright-based) and LinkedIn watcher for social media monitoring
2. MCP server integration: At least one working MCP server for external actions (email recommended)
3. Human-in-the-Loop (HITL) approval workflow: All sensitive actions create approval requests in /Pending_Approval, human reviews and moves to /Approved, then @execute-approved-actions skill executes via MCP
4. Social media automation: Automatically post on LinkedIn about business (with approval)
5. Scheduling: Basic scheduling via cron (Mac/Linux) or Task Scheduler (Windows) for continuous watcher operation
6. Process management: PM2/supervisord/watchdog for keeping watchers running 24/7
7. Audit logging: Mandatory structured JSON logging in /Logs/YYYY-MM-DD.json for all external actions

**Reference Documents**:
- Existing Bronze tier spec: specs/001-bronze-ai-employee/spec.md (all Bronze requirements still apply)
- Hackathon document: Hackathon_0.md (Silver tier requirements section)
- Constitution: .specify/memory/constitution.md (Silver tier principles)
- Existing skills: .claude/skills/process-action-items/ and .claude/skills/execute-approved-actions/

**Silver Tier Constraints**:
- Must maintain backward compatibility with Bronze tier (Bronze features still work)
- External actions MUST go through approval workflow (no auto-execution of sensitive actions)
- At least ONE working MCP server required (email recommended as simplest)
- Audit logging is MANDATORY (not optional)
- Process management required for production operation (watchers must stay alive)
- All AI functionality must be Agent Skills (already implemented)

**Success Criteria**:
- System processes action items from multiple watchers (Gmail + WhatsApp + at least one more)
- Approval workflow functions end-to-end (Needs_Action → Plan → Pending_Approval → Approved → Execute → Done)
- At least one external action successfully executed via MCP server
- LinkedIn post successfully created and posted (with approval)
- Watchers run continuously via process manager for 24+ hours
- All external actions logged to audit logs
- Dashboard shows MCP server status and pending approvals
```

---

## Alternative Shorter Version

```
Extend Bronze tier to Silver tier: Add WhatsApp/LinkedIn watchers, MCP server for external actions (email/LinkedIn posting), HITL approval workflow (/Pending_Approval → /Approved → execute), scheduling, process management (PM2), mandatory audit logging (/Logs/). Maintain Bronze compatibility. Reference specs/001-bronze-ai-employee/spec.md and Hackathon_0.md Silver tier section. All external actions require approval except auto-approved thresholds in Company_Handbook.md.
```

---

**Usage**: Run `/sp.specify` followed by the prompt above in Claude Code.

