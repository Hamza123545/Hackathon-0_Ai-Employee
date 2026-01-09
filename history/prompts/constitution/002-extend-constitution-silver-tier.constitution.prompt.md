---
id: 002
title: Extend Constitution for Silver Tier
stage: constitution
date: 2026-01-09
surface: agent
model: claude-sonnet-4-5
feature: none
branch: main
user: system
command: /sp.constitution
labels: ["silver-tier", "mcp-integration", "hitl-workflow", "constitution", "governance"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - Manual validation of template compatibility
  - Version increment verification (1.0.0 → 1.1.0)
---

## Prompt

Read the hackathon document requirements for Silver Tier (provided below) and .specify/memory/constitution.md. Extend the constitution to support Silver Tier requirements while preserving all Bronze tier principles.

Silver Tier Requirements from Hackathon:
- All Bronze requirements plus:
- Two or more Watcher scripts (e.g., Gmail + WhatsApp + LinkedIn)
- Automatically Post on LinkedIn about business to generate sales
- Claude reasoning loop that creates Plan.md files (already in Bronze)
- One working MCP server for external action (e.g., sending emails)
- Human-in-the-loop approval workflow for sensitive actions
- Basic scheduling via cron or Task Scheduler
- All AI functionality should be implemented as Agent Skills (already required)

Key Silver Tier Additions:
1. MCP Servers for external actions (email sending, social media posting, browser automation)
2. Human-in-the-Loop (HITL) approval workflow with /Pending_Approval, /Approved, /Rejected folders
3. Additional watchers (WhatsApp via Playwright, LinkedIn, Finance watchers)
4. Social media automation (LinkedIn posting)
5. Scheduling (cron/Task Scheduler for scheduled operations)
6. Process management (PM2/supervisord/watchdog) becomes required for production
7. Audit logging becomes mandatory (not optional)

Update the constitution to:
1. Add new principles for Silver tier capabilities (MCP integration, HITL, scheduling)
2. Extend existing principles to cover Silver tier scope
3. Update "Bronze Tier Deliverables" section to include Silver tier deliverables
4. Add security requirements for external actions (approval thresholds, auto-approve limits)
5. Add section on MCP server integration requirements
6. Update vault structure to include /Pending_Approval, /Approved, /Rejected, /Logs folders
7. Add process management requirements (PM2/watchdog)
8. Make audit logging mandatory (not optional)
9. Update version number appropriately
10. Maintain backward compatibility with Bronze tier

Reference the hackathon document sections:
- Section 2.C (Action Layer with MCP servers)
- Section 6 (Security & Privacy Architecture - audit logging)
- Section 7 (Error States & Recovery - process management)
- Human-in-the-Loop pattern from hackathon doc

Ensure all new sections follow the same format as existing constitution principles with rationale, requirements, and examples where appropriate.

## Response snapshot

Successfully extended the constitution from version 1.0.0 (Bronze Tier) to version 1.1.0 (Bronze → Silver Tier) with the following major additions:

**Modified Principles**:
- Principle II: "Read-Only Operations" → "External Actions and MCP Integration" (Bronze → Silver)
- Principle IV: Extended "Security and Privacy by Design" with HITL approval workflow and mandatory audit logging
- Principle V: "Simple Watcher Execution" → "Multi-Watcher Architecture" (Bronze → Silver)
- Principle VII: "Basic Dashboard" → "Observability and Audit Logging" (Bronze → Silver)

**New Principles Added**:
- Principle IX: Human-in-the-Loop (HITL) Approval Workflow (SILVER TIER - NEW)
  - Mandatory approval workflow for all external actions
  - /Pending_Approval, /Approved, /Rejected folders
  - Approval file format with risk assessment
  - Optional auto-approval thresholds
- Principle X: Scheduling and Process Management (SILVER TIER - NEW)
  - Mandatory cron/Task Scheduler for watchers
  - Required process management (PM2/supervisord/watchdog)
  - Graceful shutdown requirements
  - Example configurations provided

**New Sections**:
- MCP Server Integration Requirements (comprehensive guide)
- Silver Tier Deliverables (7 deliverable categories)
- Silver Tier Security (extends Bronze with enhanced credential management, approval thresholds, audit compliance)
- Silver Tier Error Handling (MCP errors, approval workflow errors, process management errors)

**Extended Vault Structure**:
```
/Pending_Approval   # Actions awaiting human approval (SILVER)
/Approved           # Human-approved actions ready for execution (SILVER)
/Rejected           # Human-rejected actions archive (SILVER)
/Logs               # Audit logs (MANDATORY for Silver) (SILVER)
```

**Key Requirements**:
- Minimum TWO watchers (vs one for Bronze)
- At least ONE working MCP server
- Mandatory audit logging to /Logs/ with structured JSON format
- HITL approval required for ALL external actions
- Process management required (vs optional for Bronze)
- Node.js now required (for MCP servers)

**Backward Compatibility Maintained**:
- All Bronze tier principles preserved
- Bronze requirements clearly marked as minimum
- Silver features are additive extensions
- Tier compatibility governance policy added

The constitution now provides a complete governance framework for both Bronze and Silver tiers while maintaining clarity about which requirements apply to each tier.

## Outcome

- ✅ Impact: Constitution successfully extended to v1.1.0 with comprehensive Silver Tier support. All 10 core principles now cover Bronze → Silver transition with clear tier-specific requirements.
- 🧪 Tests: Manual validation confirmed template compatibility (plan-template.md, spec-template.md, tasks-template.md all compatible with tiered structure)
- 📁 Files: Updated .specify/memory/constitution.md with 663 lines covering Bronze and Silver tiers
- 🔁 Next prompts: Update plan-template.md Constitution Check section with Silver tier gates; document approval thresholds in Company_Handbook.md template
- 🧠 Reflection: MINOR version bump (1.0.0 → 1.1.0) was appropriate as Silver tier is an additive expansion, not a breaking change. The tiered structure (Bronze → Silver → Gold) enables incremental adoption while maintaining compatibility.

## Evaluation notes (flywheel)

- Failure modes observed: None. Constitution update was straightforward with clear requirements.
- Graders run and results (PASS/FAIL): PASS - Version increment follows semantic versioning (MINOR for new principles/sections). PASS - Backward compatibility maintained (all Bronze requirements still valid). PASS - No unresolved placeholders in constitution.
- Prompt variant (if applicable): N/A - Initial prompt was comprehensive with specific requirements
- Next experiment (smallest change to try): Consider adding Gold Tier principles in future iteration when Gold tier requirements are defined (e.g., advanced scheduling, multi-user support, autonomous decision-making)
