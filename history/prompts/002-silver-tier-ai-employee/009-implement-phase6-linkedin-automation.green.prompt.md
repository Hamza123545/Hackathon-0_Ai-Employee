---
id: 009
title: Implement Phase 6 LinkedIn Social Media Automation
stage: green
date: 2026-01-11
surface: agent
model: claude-opus-4-5-20251101
feature: 002-silver-tier-ai-employee
branch: main
user: system
command: /sp.implement
labels: ["linkedin", "social-media", "automation", "phase-6", "US4"]
links:
  spec: specs/002-silver-tier-ai-employee/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - AI_Employee/Company_Handbook.md
  - .claude/skills/process-action-items/SKILL.md
  - .claude/skills/execute-approved-actions/SKILL.md
  - AI_Employee/models/approval_request.py
  - AI_Employee/utils/linkedin_rules.py
  - AI_Employee/utils/dashboard.py
  - specs/002-silver-tier-ai-employee/tasks.md
tests:
  - Manual verification of LinkedIn posting rules in Company_Handbook.md
  - Manual verification of skill documentation updates
---

## Prompt

Complete Silver Tier Phase 6: User Story 4 - LinkedIn Social Media Automation (T051-T057) from specs/002-silver-tier-ai-employee/tasks.md.

Tasks implemented:
- T051: Update Company_Handbook.md with LinkedIn Posting Rules section
- T052: Extend process-action-items skill for LinkedIn detection
- T053: Implement LinkedIn post draft approval request generation
- T054: Add LinkedIn daily post limit enforcement
- T055: Add LinkedIn posting schedule enforcement
- T056: Update dashboard.py with LinkedIn metrics
- T057: Add LinkedIn API credential expiration handling

## Response snapshot

Successfully implemented all Phase 6 tasks (T051-T057) for User Story 4 - LinkedIn Social Media Automation:

1. **T051 - Company_Handbook.md**: Added comprehensive LinkedIn Posting Rules section with:
   - max_posts_per_day: 3
   - posting_schedule: 9am-5pm business hours
   - Approved topics: AI, Automation, Business Innovation
   - Standard hashtags: #AI #Automation #Innovation #TechTrends #DigitalTransformation
   - content_length_max: 280 chars
   - auto_approval_threshold rules

2. **T052 - process-action-items skill**: Extended with LinkedIn post detection:
   - Keyword detection (announce, share, post about, publish, broadcast)
   - Topic validation against Company_Handbook.md
   - Post draft generation workflow
   - Approval request template for LinkedIn posts

3. **T053 - LinkedIn approval request generation**: Added `create_linkedin_post_approval()` function:
   - Creates APPROVAL_linkedin_post_{timestamp}.md files
   - Includes risk level assessment (low/medium based on length and links)
   - Auto-approval eligibility checking

4. **T054/T055 - Posting rules enforcement**: Created `AI_Employee/utils/linkedin_rules.py`:
   - LinkedInPostingRules class for daily limit enforcement
   - Posting schedule enforcement (business hours)
   - Queue management for blocked posts
   - Audit log integration for rate limit logging

5. **T056 - Dashboard LinkedIn metrics**: Updated DashboardUpdater:
   - posts_this_week from audit logs
   - last_post_timestamp
   - queued_posts_count
   - Recent posts with URLs

6. **T057 - AUTH_EXPIRED handling**: Added credential expiration handling:
   - `handle_linkedin_auth_expired()` creates /Needs_Action/ notification
   - Clear instructions for OAuth token refresh
   - Posts remain in /Approved/ for retry

## Outcome

- ✅ Impact: Phase 6 complete - User Story 4 (LinkedIn Automation) fully implemented
- 🧪 Tests: Manual verification of all implemented features
- 📁 Files: 7 files created/modified
- 🔁 Next prompts: Phase 7 (PM2 Management) or integration testing
- 🧠 Reflection: Clean implementation following existing patterns

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - All T051-T057 tasks completed
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Run acceptance scenarios AS4-1 through AS4-4
