---
id: 001
title: Personal AI Employee Constitution Creation
stage: constitution
date: 2026-01-09
surface: agent
model: claude-opus-4-5
feature: none
branch: master
user: user
command: /sp.constitution
labels: ["constitution", "hackathon", "ai-employee", "obsidian", "autonomous-agent"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - null
---

## Prompt

Create a constitution for the Personal AI Employee Hackathon project. This is a Bronze tier hackathon project to build an autonomous AI agent using Claude Code, Obsidian, and Python watchers.

Core principles needed:

1. **Local-First Architecture (NON-NEGOTIABLE)**: All data stored locally in Obsidian vault. External APIs for read/actions only. Source of truth in local Markdown. Never commit sensitive data. Vault structure: /Inbox, /Needs_Action, /Done, /Plans, /Logs, /Pending_Approval, /Approved, /Rejected.

2. **Human-in-the-Loop (HITL) for Sensitive Actions (MANDATORY)**: All sensitive actions (payments > $50, emails to new contacts, social media replies, file deletions) must create approval request files in /Pending_Approval before execution. Claude Code must NEVER execute these directly. Auto-approval thresholds defined in Company_Handbook.md.

3. **Agent Skills Implementation (REQUIRED)**: All AI functionality must be implemented as Claude Agent Skills, not hardcoded prompts. Each skill documented in SKILL.md with purpose, inputs, outputs, approval requirements.

4. **Security and Privacy by Design**: Credentials in environment variables or secure credential managers (never in vault/code). API keys in .env (gitignored). Audit logging for ALL actions in /Vault/Logs/YYYY-MM-DD.json format: timestamp, action_type, actor, target, parameters, approval_status, result. Logs retained 90 days minimum. Dry-run mode (DRY_RUN=true) during development.

5. **Autonomous Operation with Process Management**: Watcher scripts run as background daemons with auto-restart. Use PM2, supervisord, or custom watchdog. Handle transient errors with exponential backoff (max 3 retries). Watchdog monitors critical processes.

6. **Test-First Development for Critical Paths**: Focus on watcher file creation, Claude Code vault I/O, approval workflow, error handling. Tests before each commit. Integration tests for end-to-end flows.

7. **Observability and Monitoring**: Dashboard.md updated real-time with bank balance, pending messages, active projects, recent actions. Structured JSON logging. Graceful degradation: queue locally if APIs fail, never auto-retry payments.

8. **Modular Watcher Architecture**: All watchers inherit from BaseWatcher with abstract methods check_for_updates() and create_action_file(item). Track processed IDs to prevent duplicates. Configuration via environment variables.

Technology stack: Obsidian v1.10.6+, Claude Code (claude-3-5-sonnet or Router), Python 3.13+, Node.js v24+, MCP Servers, Playwright, PM2.

Security requirements: Credential management (env vars, OS credential managers), sandboxing (DEV_MODE, DRY_RUN flags), rate limiting (max 10 emails/hour, max 3 payments/hour), permission boundaries table for auto-approve thresholds.

Bronze tier deliverables: Obsidian vault with Dashboard.md and Company_Handbook.md, one working Watcher script (Gmail OR file system), Claude Code vault I/O working, basic folder structure, all AI as Agent Skills.

Error handling: Transient errors (exponential backoff), authentication

## Response snapshot

Created constitution v1.0.0 for Personal AI Employee hackathon project with 8 core principles:

1. Local-First Architecture - Obsidian vault as single source of truth
2. Human-in-the-Loop (HITL) - Approval workflow for sensitive actions
3. Agent Skills Implementation - Modular, documented AI capabilities
4. Security and Privacy by Design - Credentials, logging, dry-run mode
5. Autonomous Operation - Process management with PM2/supervisord
6. Test-First Development - Critical path testing requirements
7. Observability and Monitoring - Dashboard.md and structured logging
8. Modular Watcher Architecture - BaseWatcher pattern with deduplication

Additional sections: Technology Stack, Security Requirements, Bronze Tier Deliverables, Error Handling, and Governance.

## Outcome

- Impact: High - Established foundational principles for entire hackathon project
- Tests: N/A - Constitution is documentation, not code
- Files: .specify/memory/constitution.md (created/updated)
- Next prompts: Create spec for first watcher, define Company_Handbook.md structure
- Reflection: All 8 user-specified principles captured with rationale and implementation details

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
