# Tasks: Gold Tier AI Employee

**Input**: Design documents from `/specs/003-gold-tier-ai-employee/`
**Prerequisites**: plan.md, spec.md, data-model.md, research.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and Gold tier prerequisites

- [X] T001 Verify Gold tier prerequisites using scripts/verify_gold_prerequisites.py
- [X] T002 [P] Update requirements.txt with Gold tier dependencies (xero-python==2.6.0, python-facebook==2.2.0, tweepy==4.14.0, watchdog==3.0.0, schedule==1.2.0)
- [X] T003 [P] Create Gold tier Obsidian vault folders (Business/, Accounting/, Briefings/, System/)
- [X] T004 [P] Install PM2 process manager globally via npm (npm install pm2@latest -g)
- [X] T005 Update .env with Gold tier environment variables (XERO_CLIENT_ID, XERO_CLIENT_SECRET, FACEBOOK_PAGE_ACCESS_TOKEN, TWITTER_CLIENT_ID, CLAUDE_API_KEY)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Gold Tier Data Models (3 tasks)

- [x] T006 [P] Create BusinessGoal model in models/business_goal.py with metrics validation
- [x] T007 [P] Create XeroTransaction model in models/xero_transaction.py with line items support
- [x] T008 [P] Create SocialMediaPost model in models/social_media_post.py with platform-specific validation
- [x] T009 [P] Create CrossDomainWorkflow model in models/cross_domain_workflow.py with workflow steps
- [x] T010 [P] Create MCPServerStatus model in models/mcp_server_status.py with health check fields
- [x] T011 [P] Create CEOBriefing model in models/ceo_briefing.py with AI insights fields
- [x] T012 [P] Create AuditReport model in models/audit_report.py with anomaly detection
- [x] T013 [P] Create BusinessMetric model in models/business_metric.py with trend calculation
- [x] T014 [P] Create FinancialSummary model in models/financial_summary.py with profit margin calculation
- [x] T015 [P] Create SocialMediaEngagement model in models/social_media_engagement.py with engagement rate calculation

### Utility Modules (3 tasks)

- [x] T016 [P] Implement RetryManager with exponential backoff (1s, 2s, 4s) in utils/retry_manager.py
- [x] T017 [P] Implement HealthChecker for MCP server health monitoring in utils/health_checker.py
- [x] T018 [P] Implement Classifier for cross-domain rule-based classification in utils/classifier.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Autonomous Action Item Processing (Priority: P1) 🎯 MVP

**Goal**: Enable AI Processor daemon to automatically detect action items in /Needs_Action/, invoke @process-action-items skill, create plans, and generate approval requests without manual intervention

**Independent Test**: Place test action items in /Needs_Action/, verify AI Processor automatically processes them within 30 seconds, creates plans in /Plans/, and generates approval requests in /Pending_Approval/

### Implementation for User Story 1 (8 tasks)

- [ ] T019 [US1] Create ai_process_items.py daemon with watchdog file watcher monitoring /Needs_Action/ every 30 seconds
- [ ] T020 [US1] Implement priority queue processor in ai_process_items.py (urgent > high > normal > low)
- [ ] T021 [US1] Integrate Classifier (utils/classifier.py) into ai_process_items.py for cross-domain routing
- [ ] T022 [US1] Implement programmatic Agent Skill invocation (@process-action-items) in ai_process_items.py
- [ ] T023 [US1] Implement automatic detection and invocation of @execute-approved-actions skill when files appear in /Approved/
- [ ] T024 [US1] Create ecosystem.config.js for PM2 process manager with auto-restart and 10-second recovery
- [ ] T025 [US1] Update Dashboard.md to show AI Processor status (uptime, items processed, last check time)
- [ ] T026 [US1] Add error handling and logging to ai_process_items.py (log errors to /Logs/processor_errors.json)

**Checkpoint**: At this point, User Story 1 should be fully functional - AI Processor runs autonomously

---

## Phase 4: User Story 2 - Xero Accounting Integration (Priority: P2)

**Goal**: Enable automatic Xero expense tracking, invoice creation, bank transaction syncing, and financial report generation via Xero MCP Server

**Independent Test**: Connect to Xero test organization, create test expense/invoice with approval, sync bank transactions, generate financial report - verify all operations succeed and log to /Accounting/

### Implementation for User Story 2 (12 tasks)

- [x] T027 [US2] Implement OAuth 2.0 authorization code flow in mcp_servers/xero_mcp_auth.py with OS credential storage
- [x] T028 [US2] Create Xero MCP Server with FastMCP framework in mcp_servers/xero_mcp.py
- [x] T029 [P] [US2] Implement get_invoices tool in mcp_servers/xero_mcp.py (retrieve invoices with status filter)
- [x] T030 [P] [US2] Implement create_expense tool in mcp_servers/xero_mcp.py (create expense with approval workflow)
- [x] T031 [P] [US2] Implement create_invoice tool in mcp_servers/xero_mcp.py (create invoice with line items and approval workflow)
- [x] T032 [P] [US2] Implement get_financial_report tool in mcp_servers/xero_mcp.py (P&L report for weekly audit)
- [x] T033 [P] [US2] Implement sync_bank_transactions tool in mcp_servers/xero_mcp.py (sync every 6 hours)
- [x] T034 [US2] Implement rate limiting (60 req/min) and exponential backoff retry in mcp_servers/xero_mcp.py
- [x] T035 [US2] Implement request caching for zero data loss in mcp_servers/xero_mcp_cache.py
- [x] T036 [US2] Create test_connection.py health check script for mcp_servers/xero_mcp_test_connection.py
- [x] T037 [US2] Extend @execute-approved-actions skill to support Xero MCP server actions in .claude/skills/execute-approved-actions/SKILL.md
- [x] T038 [US2] Create /Accounting/ folder structure (Transactions/, Summaries/, Audits/) in Obsidian vault

**Checkpoint**: At this point, User Story 2 should be fully functional - Xero integration working end-to-end

---

## Phase 5: User Story 3 - Multi-Platform Social Media Automation (Priority: P3)

**Goal**: Enable automatic social media posting to Facebook, Instagram, and Twitter with approval workflow and engagement tracking

**Independent Test**: Create test posts for each platform (text, photo, video), approve them, verify successful posting with correct formatting, retrieve engagement metrics

### Facebook MCP Server (8 tasks)

- [x] T039 [US3] Implement OAuth 2.0 page token flow in mcp_servers/facebook_mcp_auth.py with OS credential storage
- [x] T040 [US3] Create Facebook MCP Server with FastMCP framework in mcp_servers/facebook_mcp.py
- [x] T041 [P] [US3] Implement post_to_page tool in mcp_servers/facebook_mcp.py (post with approval workflow)
- [x] T042 [P] [US3] Implement get_page_posts tool in mcp_servers/facebook_mcp.py (retrieve recent posts)
- [x] T043 [P] [US3] Implement get_engagement_summary tool in mcp_servers/facebook_mcp.py (likes, comments, shares for weekly audit)
- [x] T044 [P] [US3] Implement delete_post tool in mcp_servers/facebook_mcp.py (delete with approval workflow)
- [x] T045 [US3] Implement rate limiting (200 req/hour) and error handling in mcp_servers/facebook_mcp.py
- [x] T046 [US3] Create test_connection.py health check script for mcp_servers/facebook_mcp/

### Instagram MCP Server (9 tasks)

- [x] T047 [US3] Implement Instagram Business ID retrieval in mcp_servers/instagram_mcp.py (reuses Facebook Page Access Token)
- [x] T048 [US3] Create Instagram MCP Server with FastMCP framework in mcp_servers/instagram_mcp.py
- [x] T049 [P] [US3] Implement post_photo tool in mcp_servers/instagram_mcp.py (two-step: create container + publish with approval)
- [x] T050 [P] [US3] Implement post_video tool in mcp_servers/instagram_mcp.py (two-step: create container + publish with approval)
- [x] T051 [P] [US3] Implement get_media tool in mcp_servers/instagram_mcp.py (retrieve recent media)
- [x] T052 [P] [US3] Implement get_insights tool in mcp_servers/instagram_mcp.py (reach, impressions for weekly audit)
- [x] T053 [P] [US3] Implement get_media_insights tool in mcp_servers/instagram_mcp.py (engagement metrics per post)
- [x] T054 [US3] Implement rate limiting (200 req/hour) and error handling in mcp_servers/instagram_mcp.py
- [x] T055 [US3] Create test_connection.py health check script for mcp_servers/instagram_mcp/

### Twitter MCP Server (9 tasks)

- [x] T056 [US3] Implement OAuth 2.0 PKCE flow in mcp_servers/twitter_mcp_auth.py with OS credential storage
- [x] T057 [US3] Create Twitter MCP Server with FastMCP framework in mcp_servers/twitter_mcp.py
- [x] T058 [P] [US3] Implement post_tweet tool in mcp_servers/twitter_mcp.py (280 char limit, approval workflow)
- [x] T059 [P] [US3] Implement delete_tweet tool in mcp_servers/twitter_mcp.py (delete with approval workflow)
- [x] T060 [P] [US3] Implement get_user_tweets tool in mcp_servers/twitter_mcp.py (retrieve recent tweets with metrics)
- [x] T061 [P] [US3] Implement get_tweet_metrics tool in mcp_servers/twitter_mcp.py (public and organic metrics)
- [x] T062 [P] [US3] Implement get_engagement_summary tool in mcp_servers/twitter_mcp.py (aggregated engagement for weekly audit)
- [x] T063 [US3] Implement rate limiting (100 tweets per 15 min) and refresh token rotation in mcp_servers/twitter_mcp.py
- [x] T064 [US3] Create test_connection.py health check script for mcp_servers/twitter_mcp/

### Social Media Integration (2 tasks)

- [x] T065 [US3] Extend @execute-approved-actions skill to support Facebook, Instagram, Twitter MCP servers in .claude/skills/execute-approved-actions/SKILL.md
- [x] T066 [US3] Create /Business/Social_Media/ folder structure (facebook/, instagram/, twitter/) in Obsidian vault

**Checkpoint**: At this point, User Story 3 should be fully functional - All 3 social media platforms working

---

## Phase 6: User Story 4 - Weekly Business & Accounting Audit with CEO Briefing (Priority: P4)

**Goal**: Automatically generate comprehensive weekly audit (Monday 9 AM) and CEO briefing (Monday 10 AM) with AI-generated insights from Xero, social media, and action logs

**Independent Test**: Run weekly audit manually, verify it aggregates data from all sources (Xero, Facebook, Instagram, Twitter, action logs), generates audit report JSON and CEO briefing Markdown with 3-5 AI insights

### Implementation for User Story 4 (10 tasks)

- [x] T067 [US4] Create run_weekly_audit.py scheduler script with two phases (9 AM audit, 10 AM CEO briefing)
- [x] T068 [US4] Implement data aggregation from Xero MCP (get_financial_report) in run_weekly_audit.py
- [x] T069 [US4] Implement data aggregation from Facebook/Instagram/Twitter MCPs (get_engagement_summary) in run_weekly_audit.py
- [x] T070 [US4] Implement action logs parsing from /Logs/YYYY-MM-DD.json for weekly summary in run_weekly_audit.py
- [x] T071 [US4] Integrate Claude API for AI-generated insights (3-5 key insights, anomaly detection) in run_weekly_audit.py
- [x] T072 [US4] Implement Audit Report generation (JSON) to /Accounting/Audits/YYYY-MM-DD-audit-report.json in run_weekly_audit.py
- [x] T073 [US4] Implement CEO Briefing generation (Markdown) to /Briefings/YYYY-MM-DD-ceo-briefing.md in run_weekly_audit.py
- [x] T074 [US4] Implement partial report handling when MCP servers unavailable (mark [DATA UNAVAILABLE: source]) in run_weekly_audit.py
- [x] T075 [US4] Configure PM2 cron scheduler in ecosystem.config.js (Monday 9 AM and 10 AM) OR Windows Task Scheduler/system cron
- [x] T076 [US4] Update Dashboard.md to show last audit status and next scheduled audit time

**Checkpoint**: At this point, User Story 4 should be fully functional - Weekly reports generating automatically

---

## Phase 7: User Story 5 - Cross-Domain Integration (Priority: P5)

**Goal**: Enable seamless workflows spanning Personal and Business domains with unified Dashboard and correct domain routing

**Independent Test**: Trigger cross-domain workflow (e.g., personal expense email → business Xero entry), verify correct domain classification, routing, and tracking in Dashboard.md

### Implementation for User Story 5 (6 tasks)

- [x] T077 [US5] Enhance Classifier (utils/classifier.py) to parse Company_Handbook.md and classify actions by domain (personal, business, accounting, social_media)
- [x] T078 [US5] Implement CrossDomainWorkflow orchestration in ai_process_items.py (track multi-step workflows across domains)
- [x] T079 [US5] Implement domain-specific MCP routing in @execute-approved-actions skill (route to correct MCP server by domain)
- [x] T080 [US5] Implement domain isolation for graceful degradation (business domain failure doesn't affect personal domain)
- [x] T081 [US5] Enhance Dashboard.md with separate Personal and Business sections (show domain-specific metrics and health status)
- [x] T082 [US5] Create /Business/Workflows/ folder for cross-domain workflow tracking in Obsidian vault

**Checkpoint**: At this point, User Story 5 should be fully functional - Cross-domain workflows working seamlessly

---

## Phase 8: User Story 6 - Error Recovery & Graceful Degradation (Priority: P6)

**Goal**: Enable robust error handling with exponential backoff retry, MCP health monitoring, request caching for zero data loss, and graceful degradation when services fail

**Independent Test**: Simulate MCP server failures (disconnect Xero API), verify system retries with backoff, caches failed requests, logs failures, continues operating with degraded functionality, and recovers when service restored

### Implementation for User Story 6 (7 tasks)

- [x] T083 [US6] Integrate RetryManager (utils/retry_manager.py) into all MCP servers (Xero, Facebook, Instagram, Twitter) for exponential backoff retry
- [x] T084 [US6] Implement request caching for failed MCP calls in all MCP servers (cache to /System/Failed_Requests/ for zero data loss)
- [x] T085 [US6] Create MCP health monitoring daemon in scripts/check_mcp_health.py (5-minute interval health checks)
- [x] T086 [US6] Implement MCPServerStatus file writing to /System/MCP_Status/<server-name>.json (per-server health tracking)
- [x] T087 [US6] Implement graceful degradation in ai_process_items.py (continue processing when MCP servers down, create notifications)
- [x] T088 [US6] Enhance Dashboard.md to show MCP server health status per server (healthy, degraded, down) with last successful request time
- [x] T089 [US6] Configure PM2 auto-restart for ai_process_items.py and run_weekly_audit.py (max 10 restarts, 10-second recovery)

**Checkpoint**: At this point, User Story 6 should be fully functional - System resilient to failures

---

## Phase 9: Integration Testing & Polish

**Purpose**: End-to-end testing, backward compatibility verification, and final polish

### Integration Tests (4 tasks)

- [x] T090 [P] Write end-to-end test: Email invoice workflow (Gmail → Xero → LinkedIn notification)
- [x] T091 [P] Write end-to-end test: Cross-platform social media post (Facebook + Instagram + Twitter)
- [x] T092 [P] Write end-to-end test: Weekly audit generation (aggregate all sources, verify AI insights)
- [x] T093 [P] Write end-to-end test: AI Processor autonomous operation (place 10 action items, verify all processed automatically)

### Backward Compatibility & Performance (4 tasks)

- [x] T094 Verify Bronze tier compatibility (manual skill invocation still works)
- [x] T095 Verify Silver tier compatibility (existing MCP servers Gmail/WhatsApp/LinkedIn/Browser still functional)
- [x] T096 Performance testing: 1000+ action items processed within expected time (95% under 60 seconds)
- [x] T097 Performance testing: Weekly audit generation completes in under 60 seconds with all data sources

### Documentation & Final Polish (4 tasks)

- [x] T098 [P] Update README.md with Gold tier quick start guide
- [x] T099 [P] Update .env.example with Gold tier environment variables
- [x] T100 [P] Create quickstart.md verification checklist for Gold tier setup
- [x] T101 [P] Run scripts/verify_gold_prerequisites.py and address any failures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3, P1)**: Depends on Foundational - Autonomous Processing (MVP)
- **User Story 2 (Phase 4, P2)**: Depends on Foundational + US1 - Xero Integration
- **User Story 3 (Phase 5, P3)**: Depends on Foundational + US1 - Social Media
- **User Story 4 (Phase 6, P4)**: Depends on US2 + US3 - Weekly Audit (needs data sources)
- **User Story 5 (Phase 7, P5)**: Depends on US1 + US2 + US3 - Cross-Domain (needs all domains)
- **User Story 6 (Phase 8, P6)**: Depends on US1 + US2 + US3 - Error Recovery (needs MCP servers)
- **Integration Testing (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Requires US1 (autonomous processor needed to trigger Xero actions)
- **User Story 3 (P3)**: Requires US1 (autonomous processor needed to trigger social media actions)
- **User Story 4 (P4)**: Requires US2 + US3 (needs data from Xero and social media for audit)
- **User Story 5 (P5)**: Requires US1 + US2 + US3 (needs all domains operational for cross-domain workflows)
- **User Story 6 (P6)**: Requires US2 + US3 (needs MCP servers to test error recovery and health monitoring)

### Parallel Opportunities

- **Foundational (Phase 2)**: All data model tasks (T006-T015) can run in parallel, all utility tasks (T016-T018) can run in parallel
- **User Story 2**: Xero MCP tools (T029-T033) can be implemented in parallel after T028
- **User Story 3**: Facebook tools (T041-T044), Instagram tools (T049-T053), Twitter tools (T058-T062) can all be implemented in parallel within their respective servers
- **Integration Tests (Phase 9)**: All test tasks (T090-T093) can run in parallel, all documentation tasks (T098-T101) can run in parallel

---

## Critical Path for Minimum Viable Gold Tier (MVP)

**Objective**: Deliver core Gold tier value with autonomous processing and one integration

### MVP Scope (User Story 1 + User Story 2)

1. **Phase 1**: Setup (T001-T005) - 5 tasks
2. **Phase 2**: Foundational (T006-T018) - 13 tasks
3. **Phase 3**: User Story 1 - Autonomous Processing (T019-T026) - 8 tasks
4. **Phase 4**: User Story 2 - Xero Integration (T027-T038) - 12 tasks
5. **Validation**: Test autonomous Xero expense workflow end-to-end

**Total MVP Tasks**: 38 tasks

**MVP Validation**:
- Place expense email in /Needs_Action/
- AI Processor automatically detects it within 30 seconds
- Creates plan in /Plans/
- Creates Xero expense approval request in /Pending_Approval/
- Human approves by moving to /Approved/
- AI Processor detects approval and executes via Xero MCP
- Expense logged in Xero, audit log created, Dashboard updated
- **Success**: End-to-end workflow with zero manual skill invocation

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T018)
3. Complete Phase 3: User Story 1 (T019-T026)
4. Complete Phase 4: User Story 2 (T027-T038)
5. **STOP and VALIDATE**: Test autonomous Xero workflow independently
6. Demo MVP to stakeholders

### Incremental Delivery

1. **Foundation** (Setup + Foundational) → Core data models and utilities ready
2. **MVP** (US1 + US2) → Autonomous processing with Xero → Deploy/Demo
3. **Social Media** (US3) → Add Facebook/Instagram/Twitter → Deploy/Demo
4. **Business Intelligence** (US4) → Add weekly audits and CEO briefings → Deploy/Demo
5. **Advanced** (US5 + US6) → Add cross-domain integration and error recovery → Deploy/Demo
6. **Polish** (Phase 9) → Integration tests and final polish → Production Release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (critical path)
2. Once US1 (Autonomous Processing) is complete:
   - Developer A: User Story 2 (Xero)
   - Developer B: User Story 3 (Social Media - all 3 platforms)
   - Developer C: User Story 6 (Error Recovery utilities)
3. After US2 + US3 complete:
   - Developer A: User Story 4 (Weekly Audit)
   - Developer B: User Story 5 (Cross-Domain Integration)
4. After US4 + US5 complete:
   - All developers: Integration testing in parallel

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Stop at any checkpoint to validate story independently
- Commit after each task or logical group
- Total tasks: **101 tasks**
  - Setup: 5 tasks
  - Foundational: 13 tasks
  - US1 (Autonomous Processing): 8 tasks
  - US2 (Xero Integration): 12 tasks
  - US3 (Social Media Automation): 28 tasks
  - US4 (Weekly Audit/CEO Briefing): 10 tasks
  - US5 (Cross-Domain Integration): 6 tasks
  - US6 (Error Recovery): 7 tasks
  - Integration Testing & Polish: 12 tasks

**Success Criteria Mapping**:
- SC-001 (95% under 60s): US1 (T019-T026)
- SC-002 (80% end-to-end completion): US1 + US5 (T019-T026, T077-T082)
- SC-003 (Weekly audit on-time): US4 (T067-T076)
- SC-004 (CEO briefing with 3+ insights): US4 (T071, T073)
- SC-005 (Xero 99% success): US2 + US6 (T027-T038, T083-T084)
- SC-006 (Social media 95% success): US3 + US6 (T039-T066, T083-T084)
- SC-007 (Cross-domain 90% accuracy): US5 (T077-T082)
- SC-008 (AI Processor 99% uptime): US1 + US6 (T024, T089)
- SC-009 (Zero data loss): US6 (T084)
- SC-010 (Dashboard updates 60s): US1 + US5 (T025, T081, T088)
- SC-011 (70% manual reduction): US1 (T019-T026)
- SC-012 (100% HITL compliance): All MCP servers (approval workflow)
- SC-013 (100% audit logging): US2, US3, US6 (all MCP servers)
- SC-014 (Backward compatibility): Phase 9 (T094-T095)
