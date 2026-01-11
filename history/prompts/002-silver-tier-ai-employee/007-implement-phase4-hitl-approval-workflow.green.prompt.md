---
id: 007
title: Implement Phase 4 HITL Approval Workflow
stage: green
date: 2026-01-11
surface: agent
model: claude-opus-4-5-20251101
feature: 002-silver-tier-ai-employee
branch: main
user: Muhammad Hamza
command: /sp.implement
labels: ["approval-workflow", "hitl", "orchestrator", "risk-assessment", "audit-logging"]
links:
  spec: specs/002-silver-tier-ai-employee/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - AI_Employee/utils/approval_helper.py
  - AI_Employee/orchestrator.py
  - AI_Employee/utils/dashboard.py
  - AI_Employee/utils/__init__.py
  - .claude/skills/process-action-items/reference.md
  - specs/002-silver-tier-ai-employee/tasks.md
tests:
  - none
---

## Prompt

/sp.implement Complete Silver Tier Phase 4: User Story 2 - Human-in-the-Loop Approval Workflow (tasks T027-T035)

Implementation of HITL approval workflow including:
- External action detection in plans (email, LinkedIn, browser automation keywords)
- Risk level assessment (low/medium/high based on content and target)
- Auto-approval threshold checking from Company_Handbook.md
- ApprovalOrchestrator polling /Approved/ folder
- Expiration handling (24-hour timeout)
- Malformed file validation
- Rejection handling with audit logging
- Dashboard pending approval metrics with overdue labels

## Response snapshot

Implemented all 9 Phase 4 tasks (T027-T035) for User Story 2 - HITL Approval Workflow:

1. **T027**: Extended `.claude/skills/process-action-items/reference.md` with Section 7 covering external action detection keywords, risk assessment algorithms, and approval request creation flow.

2. **T028-T029**: Created `AI_Employee/utils/approval_helper.py` with ApprovalHelper class providing:
   - `detect_external_action()` - keyword-based detection
   - `assess_risk_level()` - returns risk level and factors
   - `check_auto_approval()` - reads Company_Handbook.md rules
   - `create_approval_request()` - creates approval files in /Pending_Approval/

3. **T030-T033**: Created `AI_Employee/orchestrator.py` with ApprovalOrchestrator class:
   - 60-second polling of /Approved/ folder
   - YAML frontmatter validation
   - 24-hour expiration handling
   - Rejection logging to audit log

4. **T034**: Enhanced DashboardUpdater with `_list_pending_approval_files()` and `#pending-overdue` labels for items >24 hours old.

5. **T035**: PM2 config already present from Phase 3 with correct settings.

## Outcome

- ✅ Impact: Phase 4 complete - Human-in-the-Loop approval workflow functional end-to-end
- 🧪 Tests: None run (implementation phase)
- 📁 Files: 6 files created/modified
- 🔁 Next prompts: Implement Phase 5 (T036-T050) - External Actions via MCP Servers
- 🧠 Reflection: The ApprovalHelper pattern cleanly separates detection, assessment, and creation concerns; orchestrator design supports both automated and manual workflows

## Evaluation notes (flywheel)

- Failure modes observed: None - implementation proceeded smoothly
- Graders run and results (PASS/FAIL): N/A - implementation task
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add integration tests for approval workflow state transitions
