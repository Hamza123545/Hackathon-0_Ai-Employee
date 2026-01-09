---
id: 001
title: Bronze AI Employee Specification Creation
stage: spec
date: 2026-01-09
surface: agent
model: claude-opus-4-5
feature: 001-bronze-ai-employee
branch: 001-bronze-ai-employee
user: user
command: /sp.specify
labels: ["spec", "bronze-tier", "ai-employee", "watcher", "obsidian", "claude-code"]
links:
  spec: specs/001-bronze-ai-employee/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-bronze-ai-employee/spec.md
  - specs/001-bronze-ai-employee/checklists/requirements.md
  - history/prompts/001-bronze-ai-employee/
tests:
  - null
---

## Prompt

Feature Description

Build a Bronze tier Personal AI Employee system that processes action items discovered by watchers (Gmail or filesystem) and creates actionable plans using Claude Code. The system operates entirely within an Obsidian vault using local Markdown files.

**Core Components**:
1. Obsidian vault with required folder structure (`/Inbox`, `/Needs_Action`, `/Done`) and essential files (`Dashboard.md`, `Company_Handbook.md`)
2. One working watcher (Gmail OR filesystem) that monitors external sources and creates `.md` action item files in `/Needs_Action/` folder when new items are detected
3. Claude Code integration that reads action items from `/Needs_Action/`, analyzes them using `Company_Handbook.md` rules, creates structured `Plan.md` files in `/Plans/` folder, and updates `Dashboard.md` with system status
4. Process-action-items Agent Skill that handles the analysis and plan creation workflow
5. Basic error handling and logging

**Bronze Tier Constraints**:
- All operations are read-only within the vault (no external actions like sending emails or payments)
- One watcher is sufficient (Gmail OR filesystem, not both required)
- Process management (PM2/watchdog) is optional
- Manual testing is acceptable (automated tests recommended but not required)
- No MCP servers required for actions (vault I/O only)

**User Goals**:
- Automatically detect new emails or files that need attention
- Get structured, actionable plans created by Claude Code
- View system status and recent activity in a dashboard
- Have processed items automatically archived

**Success Criteria**:
- Watcher successfully creates action item files in `/Needs_Action/`
- Claude Code can read from and write to the vault
- Plans are created with clear, actionable checkboxes
- Dashboard reflects current system state
- System handles common errors gracefully without crashing

## Response snapshot

Created feature specification for Bronze Tier Personal AI Employee with:

- **4 User Stories** (prioritized P1-P4):
  1. Watcher Detects New Items (P1) - foundational capability
  2. Claude Code Processes Action Items (P2) - reasoning capability
  3. Dashboard Shows System Status (P3) - visibility
  4. Vault Setup and Configuration (P4) - infrastructure

- **14 Functional Requirements** (FR-001 to FR-014) covering:
  - Watcher functionality and duplicate prevention
  - Claude Code integration and Agent Skills
  - Dashboard and logging requirements
  - Security (credentials in env vars)

- **8 Success Criteria** (SC-001 to SC-008) with measurable outcomes

- **5 Edge Cases** documented

- **6 Assumptions** for Bronze tier defaults

Quality checklist: ALL ITEMS PASS - spec ready for planning.

## Outcome

- Impact: High - Comprehensive spec for Bronze tier hackathon deliverable
- Tests: N/A (spec phase)
- Files: spec.md, checklists/requirements.md
- Next prompts: /sp.plan to create implementation plan, /sp.tasks to generate task list
- Reflection: Spec covers all Bronze tier requirements with clear acceptance criteria and reasonable defaults

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Quality checklist - all PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
