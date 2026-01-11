---
id: 006
title: Implement Phase 3 Multiple Watchers
stage: green
date: 2026-01-11
surface: agent
model: claude-opus-4-5-20251101
feature: 002-silver-tier-ai-employee
branch: main
user: Muhammad Hamza
command: /sp.implement
labels: ["whatsapp-watcher", "linkedin-watcher", "playwright", "pm2", "duplicate-prevention", "watcher-instance"]
links:
  spec: specs/002-silver-tier-ai-employee/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - AI_Employee/watchers/whatsapp_watcher.py
  - AI_Employee/watchers/linkedin_watcher.py
  - AI_Employee/watchers/__init__.py
  - AI_Employee/models/processed_tracker.py
  - AI_Employee/models/action_item.py
  - AI_Employee/watchers/base_watcher.py
  - AI_Employee/ecosystem.config.js
  - specs/002-silver-tier-ai-employee/tasks.md
tests:
  - none
---

## Prompt

/sp.implement Phase 3 (T015-T026) for Silver Tier Personal AI Employee - User Story 1: Multiple Watchers Monitor Different Sources

Implementation of WhatsApp and LinkedIn watchers with PM2 configuration, cross-source duplicate prevention, and WatcherInstance tracking.

## Response snapshot

Implemented all 12 Phase 3 tasks (T015-T026) for User Story 1 - Multiple Watchers:

1. **WhatsAppWatcher** (T015-T019): Playwright-based WhatsApp Web automation with session persistence via `context.storage_state()`, QR code authentication, session expiration detection, and action file creation with source: whatsapp.

2. **LinkedInWatcher** (T020-T023): REST API v2 client using requests library with OAuth2 bearer token authentication, exponential backoff rate limiting (1s→16s, max 5 retries), and action file creation with source: linkedin.

3. **PM2 Configuration** (T024): Updated ecosystem.config.js with all three watchers (gmail, whatsapp, linkedin) with autorestart, memory limits (500M/800M/300M), and 12-hour cron restart.

4. **Cross-source Duplicate Prevention** (T025): Extended ProcessedTracker with SHA-256 content hashing, `is_duplicate_content()`, and `register_content_hash()` methods.

5. **WatcherInstance Tracking** (T026): Integrated WatcherInstance with BaseWatcher for runtime metrics, saving state to `.watcher_state/{type}_state.json`.

## Outcome

- ✅ Impact: Phase 3 complete - Multi-channel watcher infrastructure ready (Gmail + WhatsApp + LinkedIn)
- 🧪 Tests: None run (implementation phase)
- 📁 Files: 8 files created/modified
- 🔁 Next prompts: Implement Phase 4 (T027-T035) - HITL Approval Workflow
- 🧠 Reflection: Playwright session persistence pattern works well for WhatsApp; LinkedIn API requires proper OAuth2 token refresh handling for production use

## Evaluation notes (flywheel)

- Failure modes observed: Context compaction required mid-implementation; resumed successfully from summary
- Graders run and results (PASS/FAIL): N/A - implementation task
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add integration tests for WhatsApp session detection and LinkedIn rate limiting
