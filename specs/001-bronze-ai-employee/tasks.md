# Tasks: Bronze Tier Personal AI Employee

**Input**: Design documents from `/specs/001-bronze-ai-employee/`
**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Tests**: Manual verification acceptable for Bronze tier. Automated tests optional.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `vault/` at repository root
- Agent skills at `.claude/skills/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and vault structure

- [x] T001 Create Python project structure with AI_Employee/watchers/, AI_Employee/models/, AI_Employee/utils/ directories
- [x] T002 Create AI_Employee/requirements.txt with watchdog>=4.0.0, google-api-python-client>=2.100.0, google-auth-oauthlib>=1.0.0, python-dotenv>=1.0.0, pyyaml>=6.0.0
- [x] T003 [P] Create AI_Employee/.env.example with VAULT_PATH, WATCHER_TYPE, CHECK_INTERVAL, WATCH_PATH, GMAIL_CREDENTIALS_PATH, DRY_RUN variables
- [x] T004 [P] Create AI_Employee/.gitignore with .env, credentials.json, token.pickle, __pycache__/, .processed_ids.json entries
- [x] T005 [P] Create AI_Employee/watchers/__init__.py, AI_Employee/models/__init__.py, AI_Employee/utils/__init__.py

**Checkpoint**: Project structure ready for foundational code

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create AI_Employee/utils/config.py with Config class using python-dotenv to load VAULT_PATH, WATCHER_TYPE, CHECK_INTERVAL, DRY_RUN from environment
- [x] T007 Create AI_Employee/models/processed_tracker.py with ProcessedTracker class for JSON-based duplicate prevention at {vault}/.processed_ids.json
- [x] T008 Create AI_Employee/watchers/base_watcher.py with abstract BaseWatcher class defining __init__(vault_path, check_interval), run(), check_for_updates(), create_action_file(item), update_dashboard() methods
- [x] T009 [P] Create AI_Employee/models/action_item.py with ActionItem dataclass and create_action_file() function using frontmatter schema from data-model.md
- [x] T010 [P] Create AI_Employee/utils/dashboard.py with DashboardUpdater class to read/write AI_Employee/Dashboard.md with pending counts and watcher status

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Watcher Detects New Items (Priority: P1)

**Goal**: Watcher script automatically detects new items from external source and creates action item files in `/Needs_Action/`

**Independent Test**: Run watcher, add file to WATCH_PATH, verify `.md` file appears in vault/Needs_Action/ within 60 seconds

### Implementation for User Story 1

- [x] T011 [US1] Create AI_Employee/watchers/filesystem_watcher.py with FilesystemWatcher class extending BaseWatcher, using watchdog Observer and FileSystemEventHandler
- [x] T012 [US1] Implement FilesystemWatcher.check_for_updates() to detect new files using watchdog on_created events
- [x] T013 [US1] Implement FilesystemWatcher.create_action_file() to write action-file-{slug}-{timestamp}.md to AI_Employee/Needs_Action/ with proper frontmatter
- [x] T014 [US1] Add duplicate prevention in FilesystemWatcher using ProcessedTracker to track file hashes
- [x] T015 [US1] Add error handling in FilesystemWatcher for inaccessible paths, permission errors with logging to console
- [x] T016 [P] [US1] Create AI_Employee/watchers/gmail_watcher.py with GmailWatcher class extending BaseWatcher (alternative to filesystem)
- [x] T017 [P] [US1] Implement GmailWatcher OAuth 2.0 authentication flow using google-auth-oauthlib with token.pickle storage
- [x] T018 [US1] Implement GmailWatcher.check_for_updates() to poll Gmail API messages.list() with INBOX label
- [x] T019 [US1] Implement GmailWatcher.create_action_file() to write action-gmail-{slug}-{timestamp}.md with email subject, sender, date, body snippet
- [x] T020 [US1] Add duplicate prevention in GmailWatcher using ProcessedTracker to track Gmail message IDs
- [x] T021 [US1] Create AI_Employee/main.py entry point that loads config, instantiates correct watcher based on WATCHER_TYPE, and calls run()

**Checkpoint**: Watcher creates action files in AI_Employee/Needs_Action/ - User Story 1 complete

---

## Phase 4: User Story 2 - Claude Code Processes Action Items (Priority: P2)

**Goal**: Claude Code reads action items from `/Needs_Action/`, creates structured plans in `/Plans/`, moves originals to `/Done/`

**Independent Test**: Place action item file in vault/Needs_Action/, invoke process-action-items skill, verify plan appears in vault/Plans/ with checkboxes

### Implementation for User Story 2

- [x] T022 [US2] Create .claude/skills/process-action-items/ directory structure
- [x] T023 [US2] Create .claude/skills/process-action-items/SKILL.md with purpose, inputs, outputs, approval requirements per constitution
- [x] T024 [US2] Create .claude/skills/process-action-items/reference.md with instructions to read from /Needs_Action/, apply Company_Handbook.md rules, create plans
- [x] T025 [US2] Define plan output format in templates/PlanTemplate.md with Context, Analysis, Action Plan (checkboxes), Notes sections per data-model.md
- [x] T026 [US2] Add instruction in SKILL.md to move processed action items from /Needs_Action/ to /Done/ after plan creation
- [x] T027 [US2] Add instruction in SKILL.md to update Dashboard.md with processing activity

**Checkpoint**: Claude Code creates plans with checkboxes - User Story 2 complete

---

## Phase 5: User Story 3 - Dashboard Shows System Status (Priority: P3)

**Goal**: Dashboard.md displays pending item count, recent activity, watcher status

**Independent Test**: Check vault/Dashboard.md accurately shows counts in /Needs_Action/, last watcher check time, recent plans created

### Implementation for User Story 3

- [x] T028 [US3] Implement DashboardUpdater.update_watcher_status() in AI_Employee/utils/dashboard.py to set watcher_status and last_watcher_check in frontmatter
- [x] T029 [US3] Implement DashboardUpdater.count_pending_items() to count .md files in AI_Employee/Needs_Action/
- [x] T030 [US3] Implement DashboardUpdater.list_recent_activity() to show items processed in last 24 hours from AI_Employee/Done/ and AI_Employee/Plans/
- [x] T031 [US3] Implement DashboardUpdater.render() to generate full Dashboard.md content with tables and stats
- [x] T032 [US3] Integrate dashboard update into BaseWatcher.run() to call update_dashboard() after each check cycle
- [x] T033 [US3] Add quick stats section showing plans_today, processed_today, active_plans counts via get_quick_stats()

**Checkpoint**: Dashboard.md reflects live system state - User Story 3 complete

---

## Phase 6: User Story 4 - Vault Setup and Configuration (Priority: P4)

**Goal**: Obsidian vault has clear folder structure and Company_Handbook.md for configuration

**Independent Test**: Verify vault/Inbox/, vault/Needs_Action/, vault/Done/, vault/Plans/ exist; Company_Handbook.md is readable and editable

### Implementation for User Story 4

- [x] T034 [US4] Create AI_Employee/ directory with Inbox/, Needs_Action/, Done/, Plans/ subdirectories
- [x] T035 [US4] Create AI_Employee/Company_Handbook.md with Watcher Configuration, Priority Rules, Processing Rules, Plan Generation Rules sections per data-model.md
- [x] T036 [US4] Create AI_Employee/Dashboard.md with initial template showing system status structure per data-model.md
- [x] T037 [US4] Add vault initialization logic to AI_Employee/main.py via Config.ensure_vault_structure() to create folders if they don't exist on first run
- [x] T038 [US4] Create AI_Employee/README.md with setup instructions, environment variable documentation, quickstart guide reference

**Checkpoint**: Vault structure complete with configuration files - User Story 4 complete

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, documentation, and final verification

- [x] T039 Add graceful shutdown handling to BaseWatcher.run() with KeyboardInterrupt catch
- [x] T040 [P] Add retry logic with exponential backoff (max 3 attempts) for transient errors in watchers
- [x] T041 [P] Add DRY_RUN mode support to create_action_file() - log instead of write when enabled
- [x] T042 Update README.md with troubleshooting section for common errors (vault inaccessible, Gmail auth expired, rate limits)
- [x] T043 Verify all .gitignore entries are correct and no sensitive files are tracked
- [x] T044 Run manual end-to-end test: start watcher, add test file, verify action item created, invoke skill, verify plan created
- [x] T045 Update specs/001-bronze-ai-employee/quickstart.md with any changes discovered during implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (Watcher) → can start after Phase 2
  - US2 (Claude Code) → can start after Phase 2 (parallel with US1)
  - US3 (Dashboard) → depends on US1 (needs watcher to update dashboard)
  - US4 (Vault Setup) → can start after Phase 2 (parallel with US1/US2)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 2 (Foundational)
        │
        ▼
   ┌────┴────┐
   │         │
   ▼         ▼
 US1       US2 ◄──── US4 (can run in parallel)
(Watcher) (Skill)    (Vault)
   │         │
   └────┬────┘
        │
        ▼
      US3
   (Dashboard)
        │
        ▼
    Phase 7
    (Polish)
```

### Within Each User Story

- Models/utilities before main implementation
- Core functionality before error handling
- Integration with other components last

### Parallel Opportunities

**Phase 1 (Setup)**:
```
T003 (.env.example) ─┐
T004 (.gitignore)   ─┼── All parallel
T005 (__init__.py)  ─┘
```

**Phase 2 (Foundational)**:
```
T009 (action_item.py) ─┬── Parallel
T010 (dashboard.py)   ─┘
```

**User Stories**:
```
US1 (Watcher) ──┬── Can run in parallel
US2 (Skill)   ──┤
US4 (Vault)   ──┘
```

**Within US1**:
```
T016 (gmail_watcher.py) ─┬── Parallel (alternative implementations)
T011 (filesystem_watcher.py) ─┘
```

---

## Implementation Strategy

### MVP First (Bronze Tier Minimum)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (one watcher - filesystem recommended for simplicity)
4. Complete Phase 4: User Story 2 (Claude Code skill)
5. **STOP and VALIDATE**: Test watcher → action item → plan flow
6. Demo if ready

### Full Bronze Tier

1. Complete Setup + Foundational
2. Add User Story 1 (Watcher) → Test independently
3. Add User Story 2 (Skill) → Test independently
4. Add User Story 3 (Dashboard) → Test independently
5. Add User Story 4 (Vault Config) → Test independently
6. Complete Polish phase
7. Run end-to-end demo

### Bronze Tier Deliverables Checklist

- [x] Vault structure: /Inbox, /Needs_Action, /Done, /Plans
- [x] Dashboard.md with status updates
- [x] Company_Handbook.md with configuration
- [x] One working watcher (filesystem OR Gmail) - Both implemented!
- [x] Claude Code vault I/O working
- [x] At least one Agent Skill (process-action-items)
- [x] README.md with setup instructions
- [x] .env.example with required variables

---

## Task Summary

| Phase | Tasks | Parallel | Description |
|-------|-------|----------|-------------|
| Setup | 5 | 3 | Project structure and dependencies |
| Foundational | 5 | 2 | Core infrastructure |
| US1 (Watcher) | 11 | 2 | File/Gmail monitoring |
| US2 (Skill) | 6 | 0 | Claude Code integration |
| US3 (Dashboard) | 6 | 0 | Status visibility |
| US4 (Vault) | 5 | 0 | Configuration |
| Polish | 7 | 2 | Error handling and docs |
| **Total** | **45** | **9** | |

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story
- Choose ONE watcher type for Bronze tier (filesystem is simpler)
- Manual testing is acceptable per constitution
- Each checkpoint is a valid demo point
- Commit after each task or logical group
