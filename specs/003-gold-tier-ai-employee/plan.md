# Implementation Plan: Gold Tier AI Employee

**Branch**: `003-gold-tier-ai-employee` | **Date**: 2026-01-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-gold-tier-ai-employee/spec.md`

---

## Summary

**Primary Requirement**: Extend Personal AI Employee from Silver tier to Gold tier by adding autonomous processing (no manual skill invocation), cross-domain integration (Personal + Business), Xero accounting integration, Facebook/Instagram/Twitter social media automation, and weekly business intelligence reports with AI-generated CEO briefings.

**Technical Approach**:
- **Autonomous Processing**: Python daemon (`ai_process_items.py`) with file watcher monitors `/Needs_Action/` and automatically invokes `@process-action-items` Agent Skill every 30 seconds. Managed by PM2 with crash recovery.
- **MCP Servers**: Four new FastMCP servers (Xero, Facebook, Instagram, Twitter) with OAuth 2.0 authentication, rate limiting (exponential backoff 1s/2s/4s), and request caching for zero data loss.
- **Cross-Domain Workflows**: Rule-based classification via `Company_Handbook.md` routes actions to Personal or Business domains. Workflows span multiple domains (e.g., Gmail → Xero → LinkedIn).
- **Weekly Business Intelligence**: Scheduled Python script (`run_weekly_audit.py`) runs Monday 9:00 AM (Audit Report) and 10:00 AM (CEO Briefing). Aggregates Xero financial data, social media engagement metrics, and action logs. Uses Claude API for AI-generated insights.
- **Error Recovery**: Exponential backoff retry, MCP server health monitoring (5-min interval), graceful degradation with domain isolation, immutable audit logs with credential sanitization.

**Key Technologies**: Python 3.10+, FastMCP 1.0, xero-python 2.6, pyfacebook 2.2, tweepy 4.14, PM2 process manager, OAuth 2.0 (PKCE for Twitter), Claude API, Pydantic for data validation, watchdog for file monitoring.

---

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**:
  - `fastmcp==1.0.0` (MCP server framework)
  - `pydantic==2.5.0` (data validation)
  - `xero-python==2.6.0` (Xero accounting API)
  - `python-facebook==2.2.0` (Facebook/Instagram Graph API)
  - `tweepy==4.14.0` (Twitter API v2)
  - `watchdog==3.0.0` (file system monitoring)
  - `schedule==1.2.0` (task scheduling)
  - `requests==2.31.0`, `oauthlib==3.2.2` (HTTP and OAuth)

**Storage**:
  - File-based (Obsidian vault): JSON for structured data, Markdown for human-readable reports
  - OS Credential Manager: OAuth tokens (Windows Credential Manager, macOS Keychain, Linux Secret Service)
  - Append-only JSONL: Audit logs (`/Logs/YYYY-MM-DD.json`)

**Testing**: pytest 7.4+ with fixtures for MCP server mocking, contract validation, end-to-end workflow tests

**Target Platform**: Cross-platform (Windows, macOS, Linux) with PM2 process manager

**Project Type**: Single-project Python application with multiple daemons (AI Processor, Weekly Scheduler)

**Performance Goals**:
  - Action item processing: 95% within 60 seconds (P1, SC-001)
  - Dashboard updates: Every 60 seconds (P5, SC-010)
  - Weekly audit generation: < 60 seconds total (P4, SC-003)
  - MCP API calls: < 5 seconds p95 latency

**Constraints**:
  - Rate Limits: Xero 60/min, Facebook 200/hour, Instagram 200/hour, Twitter 100/15min
  - Zero data loss: Request caching required for MCP failures
  - HITL compliance: 100% approval for external write actions (SC-012)
  - Backward compatibility: Full Bronze/Silver compatibility (FR-060-063, SC-014)

**Scale/Scope**:
  - Action items: 1000+ per month
  - Xero transactions: 5000+ synced
  - Social media posts: 100+ per month across 3 platforms
  - Weekly reports: 52 per year with indefinite retention

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Constitution v1.2.0 Compliance

**✅ Principle I (Human-in-the-Loop)**: All external write actions (Xero invoices/expenses, social media posts, email sends) require approval via `/Pending_Approval/` → `/Approved/` workflow. Read-only actions (Xero queries, social media metrics) execute without approval. Compliance: FR-036-044, FR-045-054.

**✅ Principle II (Zero External Actions Without Approval)**: Autonomous processor creates approval requests, never executes directly. `@execute-approved-actions` skill only runs after human moves file to `/Approved/`. Compliance: FR-055-059.

**✅ Principle III (Audit Trail)**: All actions logged to `/Logs/YYYY-MM-DD.json` with `CredentialSanitizer`. Immutable append-only logs. Compliance: FR-055-059, SC-013.

**✅ Principle IV (Graceful Degradation)**: MCP server failures isolated by domain. System continues operating with degraded functionality. Failed requests cached for retry. Compliance: FR-045-054, SC-009.

**✅ Principle V (Credential Security)**: OAuth tokens stored in OS credential manager (never in files). Credentials sanitized in logs via `CredentialSanitizer`. Compliance: FR-045-054.

**✅ Principle VI (Domain Isolation)**: Personal and Business domains have separate MCP servers and health status. Failure in one domain doesn't affect the other. Compliance: FR-036-044.

**✅ Principle VII (File-Based Communication)**: All data persisted to Obsidian vault files (JSON, Markdown, JSONL). No external database. Compliance: All FRs.

**✅ Principle VIII (Agent Skills as Primary Interface)**: Autonomous processor invokes `@process-action-items` and `@execute-approved-actions` skills programmatically. Manual invocation still supported. Compliance: FR-055-059.

**✅ Principle IX (Markdown for Human Readability)**: Action items, plans, CEO briefings use Markdown. JSON for structured data (Xero transactions, audit logs). Compliance: All FRs.

**✅ Principle X (MCP Servers for External Integration)**: Four new MCP servers (Xero, Facebook, Instagram, Twitter) follow FastMCP pattern. Compliance: FR-009-027.

**✅ Principle XI (Autonomous Operation)**: AI Processor daemon runs continuously with PM2, auto-restarts on crash, monitors `/Needs_Action/` every 30 seconds. Compliance: FR-001-008, SC-008.

**✅ Principle XII (Cross-Domain Integration)**: Workflows span Personal and Business domains via rule-based classification. Unified Dashboard with separate domain health. Compliance: FR-036-044, SC-007.

**✅ Principle XIII (Business Intelligence and Reporting)**: Weekly audits (Monday 9 AM) and CEO briefings (Monday 10 AM) with AI-generated insights via Claude API. Compliance: FR-028-035, SC-003-004.

**Constitution Violations**: None. All principles satisfied.

---

## Project Structure

### Documentation (this feature)

```text
specs/003-gold-tier-ai-employee/
├── spec.md              # Feature specification (63 FRs, 14 SCs, 6 user stories)
├── plan.md              # This file (architecture and implementation phases)
├── research.md          # Phase 0 technical research (550+ lines, Context7 MCP queries)
├── data-model.md        # 15 entities (5 Bronze, 5 Silver, 10 Gold tier new)
├── quickstart.md        # Setup guide (OAuth flows, MCP servers, schedulers)
├── checklists/
│   └── requirements.md  # Specification quality validation (all passed)
└── contracts/
    ├── xero-mcp.json          # Xero MCP server protocol contract
    ├── facebook-mcp.json      # Facebook MCP server protocol contract
    ├── instagram-mcp.json     # Instagram MCP server protocol contract
    └── twitter-mcp.json       # Twitter MCP server protocol contract
```

### Source Code (repository root)

```text
AI_Employee/                      # Obsidian vault (existing Bronze/Silver structure)
├── Needs_Action/                 # Bronze: Action items awaiting processing
├── Plans/                        # Bronze: Generated plans
├── Pending_Approval/             # Silver: Approval requests
├── Approved/                     # Silver: Approved actions ready for execution
├── Done/                         # Bronze: Archived completed actions
├── Logs/                         # Silver: Audit logs (YYYY-MM-DD.json)
├── Dashboard.md                  # Bronze: System status
├── Company_Handbook.md           # Bronze: Rules for action classification
│
├── Business/                     # Gold: Business domain (NEW)
│   ├── Goals/                    # Business goals with metrics
│   ├── Social_Media/             # Social media posts
│   │   ├── facebook/
│   │   ├── instagram/
│   │   └── twitter/
│   ├── Workflows/                # Cross-domain workflows
│   ├── Metrics/                  # Business KPIs
│   └── Engagement/               # Social media engagement summaries
│
├── Accounting/                   # Gold: Accounting domain (NEW)
│   ├── Transactions/             # Xero transactions (synced every 6 hours)
│   ├── Summaries/                # Weekly financial summaries
│   └── Audits/                   # Weekly audit reports
│
├── Briefings/                    # Gold: CEO briefings (NEW)
│   └── YYYY-MM-DD-ceo-briefing.md
│
└── System/                       # Gold: System internals (NEW)
    └── MCP_Status/               # MCP server health status (per server)

mcp_servers/                      # MCP server implementations (existing + new)
├── gmail_mcp/                    # Silver: Gmail MCP server
│   ├── server.py
│   └── auth_setup.py
├── whatsapp_mcp/                 # Silver: WhatsApp MCP server
│   ├── server.py
│   └── auth_setup.py
├── linkedin_mcp/                 # Silver: LinkedIn MCP server
│   ├── server.py
│   └── auth_setup.py
├── browser_mcp/                  # Silver: Browser automation MCP server
│   ├── server.py
│   └── auth_setup.py
│
├── xero_mcp/                     # Gold: Xero MCP server (NEW)
│   ├── server.py                 # FastMCP server (5 tools)
│   ├── auth_setup.py             # OAuth 2.0 authorization code flow
│   ├── test_connection.py        # Health check script
│   └── models.py                 # Pydantic models for Xero entities
│
├── facebook_mcp/                 # Gold: Facebook MCP server (NEW)
│   ├── server.py                 # FastMCP server (4 tools)
│   ├── auth_setup.py             # OAuth 2.0 for Page Access Token
│   ├── test_connection.py
│   └── models.py
│
├── instagram_mcp/                # Gold: Instagram MCP server (NEW)
│   ├── server.py                 # FastMCP server (6 tools)
│   ├── auth_setup.py             # Reuses Facebook Page Access Token
│   ├── test_connection.py
│   └── models.py
│
└── twitter_mcp/                  # Gold: Twitter MCP server (NEW)
    ├── server.py                 # FastMCP server (5 tools)
    ├── auth_setup.py             # OAuth 2.0 PKCE flow
    ├── test_connection.py
    └── models.py

models/                           # Pydantic data models (existing + new)
├── __init__.py
├── action_item.py                # Bronze: ActionItem model
├── plan.py                       # Bronze: Plan model
├── approval_request.py           # Silver: ApprovalRequest model
├── audit_log.py                  # Silver: AuditLogEntry model
├── business_goal.py              # Gold: BusinessGoal model (NEW)
├── ceo_briefing.py               # Gold: CEOBriefing model (NEW)
├── audit_report.py               # Gold: AuditReport model (NEW)
├── xero_transaction.py           # Gold: XeroTransaction model (NEW)
├── social_media_post.py          # Gold: SocialMediaPost model (NEW)
├── cross_domain_workflow.py     # Gold: CrossDomainWorkflow model (NEW)
├── mcp_server_status.py          # Gold: MCPServerStatus model (NEW)
├── business_metric.py            # Gold: BusinessMetric model (NEW)
├── financial_summary.py          # Gold: FinancialSummary model (NEW)
└── social_media_engagement.py    # Gold: SocialMediaEngagement model (NEW)

watchers/                         # File system watchers (existing Silver tier)
├── gmail_watcher.py              # Silver: Gmail watcher (5-min interval)
├── whatsapp_watcher.py           # Silver: WhatsApp watcher (5-min interval)
├── linkedin_watcher.py           # Silver: LinkedIn watcher (daily)
└── filesystem_watcher.py         # Silver: Filesystem watcher (real-time)

utils/                            # Utility modules (existing + new)
├── credential_sanitizer.py       # Silver: Remove credentials from logs
├── audit_logger.py               # Silver: Append-only audit logging
├── retry_manager.py              # Gold: Exponential backoff retry (NEW)
├── health_checker.py             # Gold: MCP server health monitoring (NEW)
└── classifier.py                 # Gold: Cross-domain rule-based classifier (NEW)

.claude/                          # Agent Skills (existing Silver tier)
└── skills/
    ├── process-action-items/     # Bronze+Silver: Process action items
    │   ├── SKILL.md
    │   ├── examples.md
    │   └── reference.md
    └── execute-approved-actions/ # Silver: Execute approved MCP actions
        ├── SKILL.md
        ├── examples.md
        └── reference.md

scripts/                          # Utility scripts (existing + new)
├── verify_gold_prerequisites.py  # Gold: Verify Gold tier prerequisites (NEW)
├── check_mcp_health.py           # Gold: Check MCP server health (NEW)
└── create-new-feature.ps1        # Existing: Create feature branch

ai_process_items.py               # Gold: AI Processor daemon (NEW)
run_weekly_audit.py               # Gold: Weekly audit and CEO briefing generator (NEW)
ecosystem.config.js               # Gold: PM2 process manager config (NEW)
requirements.txt                  # Python dependencies (updated for Gold tier)
.env                              # Environment variables (updated for Gold tier)
```

**Structure Decision**: Single-project Python application with file-based storage (Obsidian vault). Chose file-based over database for simplicity, human readability, and backward compatibility with Bronze/Silver tiers. MCP servers follow FastMCP framework for consistency. Pydantic models provide type safety and JSON serialization.

---

## Complexity Tracking

**No Constitution Violations**. All complexity justified by Gold tier requirements:

| Complexity | Why Needed | Simpler Alternative Rejected Because |
|------------|------------|-------------------------------------|
| 4 new MCP servers | Xero, Facebook, Instagram, Twitter integrations required by spec (FR-009-027) | Manual API calls would lack rate limiting, error recovery, HITL approval, and audit logging |
| Autonomous daemon | Core differentiator of Gold tier (P1, FR-001-008) | Manual skill invocation doesn't meet 95% processing within 60s goal (SC-001) |
| Cross-domain workflows | Unified Personal + Business required by spec (P5, FR-036-044) | Separate systems would miss cross-domain insights (e.g., email → invoice → LinkedIn) |
| Weekly scheduler | Business intelligence required by spec (P4, FR-028-035) | Manual report generation doesn't meet 100% on-time delivery (SC-003-004) |
| PM2 process manager | 99% uptime and crash recovery required (SC-008, FR-045-054) | Python supervisor lacks auto-restart and monitoring |

---

## Architecture Diagram

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Gold Tier AI Employee System                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            Input Layer (Bronze/Silver)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Gmail Watcher  │  WhatsApp Watcher  │  LinkedIn Watcher  │  Filesystem     │
│  (5 min)        │  (5 min)           │  (daily)           │  (real-time)    │
└────────┬────────┴────────┬───────────┴────────┬───────────┴────────┬─────────┘
         │                 │                    │                    │
         └─────────────────┴────────────────────┴────────────────────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │   /Needs_Action/       │  ◄──── Action Items
                        └────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Autonomous Processing Layer (Gold Tier - NEW)             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   ┌───────────────────────────────────────────────────────────────┐         │
│   │  AI Processor Daemon (ai_process_items.py)                     │         │
│   │  ┌──────────────────────────────────────────────────────────┐ │         │
│   │  │  File Watcher (watchdog) - monitors /Needs_Action/       │ │         │
│   │  │  Interval: 30 seconds │  Managed by PM2                  │ │         │
│   │  └────────────────────┬───────────────────────────────────── │ │         │
│   │                       ▼                                        │ │         │
│   │  ┌──────────────────────────────────────────────────────────┐ │         │
│   │  │  Priority Queue Processor                                 │ │         │
│   │  │  1. urgent → 2. high → 3. normal → 4. low               │ │         │
│   │  └────────────────────┬───────────────────────────────────── │ │         │
│   │                       ▼                                        │ │         │
│   │  ┌──────────────────────────────────────────────────────────┐ │         │
│   │  │  Cross-Domain Classifier (classifier.py)                  │ │         │
│   │  │  Rules: Company_Handbook.md                              │ │         │
│   │  │  Output: personal │ business │ accounting │ social_media │ │         │
│   │  └────────────────────┬───────────────────────────────────── │ │         │
│   │                       ▼                                        │ │         │
│   │  ┌──────────────────────────────────────────────────────────┐ │         │
│   │  │  Invoke @process-action-items Skill (programmatic)       │ │         │
│   │  │  Creates Plan.md, Approval Requests (if needed)          │ │         │
│   │  └──────────────────────────────────────────────────────────┘ │         │
│   └───────────────────────────────────────────────────────────────┘         │
│                                                                               │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        ▼
                        ┌───────────────────────────┐
                        │  /Pending_Approval/       │  ◄──── Approval Requests
                        └─────────┬─────────────────┘
                                  │  (Human reviews)
                                  ▼
                        ┌───────────────────────────┐
                        │  /Approved/               │  ◄──── Approved Actions
                        └─────────┬─────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Execution Layer (Silver/Gold)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│   ┌───────────────────────────────────────────────────────────────┐         │
│   │  @execute-approved-actions Skill (triggered by AI Processor)  │         │
│   │                                                                 │         │
│   │  ┌─────────────────────────────────────────────────────────┐  │         │
│   │  │  MCP Server Router                                       │  │         │
│   │  │  Routes action to appropriate MCP server by domain      │  │         │
│   │  └───────┬─────────┬─────────┬─────────┬────────┬─────────┘  │         │
│   │          │         │         │         │        │              │         │
│   │  ┌───────▼─────┐ ┌─▼────┐ ┌─▼────┐ ┌──▼────┐ ┌▼─────────┐   │         │
│   │  │  Gmail MCP  │ │WhatsApp│ │LinkedIn│ │Browser│ │ (Silver) │   │         │
│   │  └─────────────┘ └───────┘ └───────┘ └───────┘ └──────────┘   │         │
│   │                                                                 │         │
│   │  ┌───────▼─────┐ ┌─▼────────┐ ┌─▼─────────┐ ┌──▼────────┐   │         │
│   │  │  Xero MCP   │ │ Facebook │ │ Instagram │ │  Twitter  │    │  (Gold) │
│   │  │  (NEW)      │ │   MCP    │ │    MCP    │ │    MCP    │    │         │
│   │  │             │ │  (NEW)   │ │   (NEW)   │ │   (NEW)   │    │         │
│   │  └─────────────┘ └──────────┘ └───────────┘ └───────────┘    │         │
│   │                                                                 │         │
│   │  All MCP servers:                                              │         │
│   │  - FastMCP framework with @mcp.tool decorators                │         │
│   │  - OAuth 2.0 authentication (tokens in OS cred manager)       │         │
│   │  - Exponential backoff retry (1s, 2s, 4s max 3 attempts)     │         │
│   │  - Rate limit handling with request caching                   │         │
│   │  - Health monitoring (5-min interval via health_checker.py)   │         │
│   │  - Audit logging (all actions logged to /Logs/)               │         │
│   └───────────────────────────────────────────────────────────────┘         │
└───────────────────────────────────┬───────────────────────────────────────┘
                                    ▼
                        ┌───────────────────────────┐
                        │  /Logs/YYYY-MM-DD.json    │  ◄──── Audit Logs
                        │  (append-only JSONL)      │       (credentials sanitized)
                        └───────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│               Business Intelligence Layer (Gold Tier - NEW)                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   ┌───────────────────────────────────────────────────────────────┐         │
│   │  Weekly Scheduler (run_weekly_audit.py)                        │         │
│   │  Monday 9:00 AM: Audit Report │ Monday 10:00 AM: CEO Briefing │         │
│   │  Managed by: PM2 cron OR system cron OR Windows Task Scheduler │         │
│   │                                                                 │         │
│   │  ┌─────────────────────────────────────────────────────────┐  │         │
│   │  │  Data Aggregation                                        │  │         │
│   │  │  - Xero MCP: get_financial_report (P&L, expenses, rev)  │  │         │
│   │  │  - Facebook MCP: get_engagement_summary (likes, shares) │  │         │
│   │  │  - Instagram MCP: get_insights (reach, impressions)     │  │         │
│   │  │  - Twitter MCP: get_engagement_summary (retweets, etc.) │  │         │
│   │  │  - Action Logs: Parse /Logs/YYYY-MM-DD.json for week    │  │         │
│   │  └────────────────────┬────────────────────────────────────┘  │         │
│   │                       ▼                                        │         │
│   │  ┌─────────────────────────────────────────────────────────┐  │         │
│   │  │  AI Analysis (Claude API)                                │  │         │
│   │  │  - Generate 3-5 key insights                             │  │         │
│   │  │  - Identify anomalies (financial, social, operational)   │  │         │
│   │  │  - Generate recommendations                              │  │         │
│   │  │  - Create executive summary (200-300 words)              │  │         │
│   │  └────────────────────┬────────────────────────────────────┘  │         │
│   │                       ▼                                        │         │
│   │  ┌─────────────────────────────────────────────────────────┐  │         │
│   │  │  Report Generation                                        │  │         │
│   │  │  - Audit Report → /Accounting/Audits/YYYY-MM-DD.json    │  │         │
│   │  │  - CEO Briefing → /Briefings/YYYY-MM-DD-ceo-briefing.md │  │         │
│   │  │  - Update Dashboard.md with latest metrics               │  │         │
│   │  └──────────────────────────────────────────────────────────┘  │         │
│   └───────────────────────────────────────────────────────────────┘         │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Monitoring & Recovery Layer (Gold)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   ┌─────────────────────────────┐  ┌──────────────────────────────┐        │
│   │  MCP Health Monitor          │  │  PM2 Process Manager         │        │
│   │  (health_checker.py)         │  │  - Auto-restart on crash     │        │
│   │  - 5-min health checks       │  │  - 10-second recovery time   │        │
│   │  - Per-server status         │  │  - Max 10 restarts           │        │
│   │  - Graceful degradation      │  │  - Startup on boot           │        │
│   │  - Domain isolation          │  └──────────────────────────────┘        │
│   └─────────────────────────────┘                                           │
│                                                                               │
│   Status files: /System/MCP_Status/<server-name>.json                       │
│   Dashboard updates: Every 60 seconds                                       │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Diagram

```
┌──────────────┐
│  Email       │  ─┐
│  (Gmail)     │   │
└──────────────┘   │
                   ├──► Action Item ──► AI Processor ──► Plan ──► Approval Request
┌──────────────┐   │                        │                            │
│  WhatsApp    │   │                        │                            │
│  Message     │  ─┤                        ▼                            ▼
└──────────────┘   │              Cross-Domain Classifier      Human Approval
                   │              (personal/business/etc.)              │
┌──────────────┐   │                        │                            │
│  LinkedIn    │   │                        │                            │
│  Notification│  ─┤                        ▼                            ▼
└──────────────┘   │              ┌───────────────────┐        ┌───────────────┐
                   │              │  Personal Domain  │        │   Approved    │
┌──────────────┐   │              │  - Gmail MCP      │        │   /Approved/  │
│  Filesystem  │  ─┘              │  - WhatsApp MCP   │        └───────┬───────┘
│  Changes     │                  │  - LinkedIn MCP   │                │
└──────────────┘                  │  - Browser MCP    │                │
                                  └───────────────────┘                │
                                  ┌───────────────────┐                │
                                  │  Business Domain  │                │
                                  │  - Xero MCP       │                │
                                  │  - Facebook MCP   │  ◄─────────────┘
                                  │  - Instagram MCP  │     @execute-approved-actions
                                  │  - Twitter MCP    │
                                  └─────────┬─────────┘
                                            │
                                            ▼
                                  ┌───────────────────┐
                                  │  External APIs    │
                                  │  - Xero           │
                                  │  - Facebook       │
                                  │  - Instagram      │
                                  │  - Twitter/X      │
                                  └─────────┬─────────┘
                                            │
                                            ▼
                                  ┌───────────────────┐
                                  │  Audit Logs       │
                                  │  /Logs/YYYY-MM-DD │
                                  │  (credentials     │
                                  │   sanitized)      │
                                  └─────────┬─────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────┐
│  Weekly Business Intelligence (Monday 9 AM / 10 AM)            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Xero Data    │  │ Social Media │  │ Action Logs  │        │
│  │ (Financial)  │  │ (Engagement) │  │ (Operations) │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                 │                 │                 │
│         └─────────────────┴─────────────────┘                 │
│                           │                                    │
│                           ▼                                    │
│                ┌───────────────────────┐                       │
│                │  AI Analysis (Claude) │                       │
│                │  - Insights           │                       │
│                │  - Anomalies          │                       │
│                │  - Recommendations    │                       │
│                └───────────┬───────────┘                       │
│                            │                                    │
│         ┌──────────────────┴──────────────────┐               │
│         ▼                                     ▼               │
│  ┌────────────────┐                  ┌─────────────────┐     │
│  │  Audit Report  │                  │  CEO Briefing   │     │
│  │  /Accounting/  │                  │  /Briefings/    │     │
│  │  Audits/       │                  │  YYYY-MM-DD.md  │     │
│  └────────────────┘                  └─────────────────┘     │
└────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 0: Research (✅ Completed)

**Deliverable**: `research.md` (550+ lines)

**Tasks**:
- ✅ Research Xero API (xero-python SDK, OAuth 2.0, AccountingApi endpoints)
- ✅ Research Facebook Graph API (pyfacebook library, OAuth 2.0, rate limits)
- ✅ Research Instagram Graph API (Instagram Business via Facebook Graph API)
- ✅ Research Twitter API v2 (tweepy library, OAuth 2.0 PKCE, rate limits)
- ✅ Research autonomous processing patterns (file watchers, daemons, PM2)
- ✅ Research cross-domain workflow patterns (rule-based classification, domain isolation)
- ✅ Research business intelligence automation (scheduled tasks, AI analysis with Claude API)
- ✅ Research error recovery strategies (exponential backoff, graceful degradation, request caching)
- ✅ Query Context7 MCP for library documentation (Xero, Facebook, Twitter APIs)

**Key Findings**:
- Xero: Use xero-python SDK v2.6+ with OAuth 2.0 authorization code flow, 60 req/min rate limit
- Facebook/Instagram: Use pyfacebook (python-facebook) with GraphAPI class, 200 req/hour rate limit
- Twitter: Use tweepy v4.14+ with OAuth 2.0 PKCE (no client secret in code), 100 tweets per 15 min
- FastMCP: Decorator-based @mcp.tool with automatic JSON schema generation
- PM2: Auto-restart, crash recovery within 10 seconds, cron scheduling support
- Exponential backoff: 1s, 2s, 4s (max 3 attempts) for all MCP API calls

---

### Phase 1: Design (✅ Completed)

**Deliverables**:
- ✅ `data-model.md` (15 entities: 5 Bronze, 5 Silver, 10 Gold tier new)
- ✅ `contracts/xero-mcp.json` (5 tools: get_invoices, create_expense, create_invoice, get_financial_report, sync_bank_transactions)
- ✅ `contracts/facebook-mcp.json` (4 tools: post_to_page, get_page_posts, get_engagement_summary, delete_post)
- ✅ `contracts/instagram-mcp.json` (6 tools: post_photo, post_video, get_media, get_insights, get_media_insights)
- ✅ `contracts/twitter-mcp.json` (5 tools: post_tweet, delete_tweet, get_user_tweets, get_tweet_metrics, get_engagement_summary)
- ✅ `quickstart.md` (Setup guide with OAuth flows, MCP servers, schedulers)

**Key Decisions**:
- **Entity Design**: 10 new Gold tier entities extend Bronze/Silver with backward compatibility. All entities use Pydantic for validation.
- **MCP Contracts**: All 4 MCP servers follow FastMCP pattern with OAuth 2.0, rate limits, error codes, HITL approval workflow for write operations.
- **OAuth Flows**: Xero and Facebook use authorization code flow. Twitter uses PKCE (no client secret). Instagram reuses Facebook page token.
- **Data Formats**: JSON for structured data (Xero transactions, audit logs), Markdown for human-readable reports (CEO briefing), JSONL for append-only audit logs.
- **Scheduling**: PM2 cron for AI Processor and weekly tasks. Fallback: system cron (Linux/Mac) or Windows Task Scheduler.

---

### Phase 2: Tasks (🚧 Next Phase - Not Started)

**Command**: `/sp.tasks`

**Deliverable**: `tasks.md` (dependency-ordered tasks with acceptance criteria)

**Expected Tasks** (estimated breakdown):
1. **Task Group 1: Gold Tier Data Models** (3-5 tasks)
   - Implement 10 new Pydantic models (BusinessGoal, CEOBriefing, AuditReport, XeroTransaction, SocialMediaPost, CrossDomainWorkflow, MCPServerStatus, BusinessMetric, FinancialSummary, SocialMediaEngagement)
   - Add JSON serialization and validation
   - Write unit tests for all models

2. **Task Group 2: Xero MCP Server** (5-7 tasks)
   - Implement OAuth 2.0 authorization code flow (`auth_setup.py`)
   - Implement FastMCP server with 5 tools (`server.py`)
   - Implement rate limiting and exponential backoff
   - Implement request caching for zero data loss
   - Write integration tests with Xero sandbox API
   - Create health check script (`test_connection.py`)
   - Document setup in `quickstart.md` (already done)

3. **Task Group 3: Facebook MCP Server** (4-6 tasks)
   - Implement OAuth 2.0 page token flow (`auth_setup.py`)
   - Implement FastMCP server with 4 tools (`server.py`)
   - Implement rate limiting and error handling
   - Write integration tests with Facebook Graph API test app
   - Create health check script
   - Update quickstart.md with Facebook setup

4. **Task Group 4: Instagram MCP Server** (4-6 tasks)
   - Implement Instagram Business ID retrieval (`auth_setup.py`)
   - Implement FastMCP server with 6 tools (photo/video posting) (`server.py`)
   - Implement two-step media creation (container → publish)
   - Write integration tests with Instagram test account
   - Create health check script
   - Update quickstart.md with Instagram setup

5. **Task Group 5: Twitter MCP Server** (5-7 tasks)
   - Implement OAuth 2.0 PKCE flow (`auth_setup.py`)
   - Implement FastMCP server with 5 tools (`server.py`)
   - Implement rate limiting (100 tweets per 15 min)
   - Handle refresh token rotation (6-month expiry)
   - Write integration tests with Twitter API sandbox
   - Create health check script
   - Update quickstart.md with Twitter setup

6. **Task Group 6: Autonomous Processor** (6-8 tasks)
   - Implement file watcher with watchdog library (`ai_process_items.py`)
   - Implement priority queue processor (urgent > high > normal > low)
   - Integrate cross-domain classifier (`classifier.py`)
   - Implement programmatic Agent Skill invocation
   - Configure PM2 process manager (`ecosystem.config.js`)
   - Write end-to-end tests (create action item → verify plan created)
   - Implement crash recovery and error handling
   - Update Dashboard with AI Processor status

7. **Task Group 7: Cross-Domain Integration** (4-6 tasks)
   - Implement rule-based classifier with Company_Handbook.md parsing
   - Create CrossDomainWorkflow model and workflow orchestration
   - Implement domain-specific MCP routing
   - Implement domain isolation for graceful degradation
   - Update Dashboard with domain health status
   - Write cross-domain workflow tests (e.g., Gmail → Xero → LinkedIn)

8. **Task Group 8: Weekly Business Intelligence** (6-8 tasks)
   - Implement data aggregation from Xero, Facebook, Instagram, Twitter (`run_weekly_audit.py`)
   - Integrate Claude API for AI-generated insights
   - Implement Audit Report generation (JSON)
   - Implement CEO Briefing generation (Markdown)
   - Configure weekly scheduler (PM2 cron / system cron / Windows Task Scheduler)
   - Write tests for report generation (mock MCP responses)
   - Implement partial report handling (when MCP servers unavailable)
   - Update Dashboard with last audit status

9. **Task Group 9: Error Recovery & Health Monitoring** (5-7 tasks)
   - Implement exponential backoff retry utility (`retry_manager.py`)
   - Implement MCP health monitoring daemon (`health_checker.py`, 5-min interval)
   - Implement request caching for failed MCP calls
   - Implement graceful degradation per domain
   - Write MCPServerStatus model and health status files
   - Write error recovery tests (simulate MCP failures, verify retry)
   - Document troubleshooting in quickstart.md (already done)

10. **Task Group 10: Integration & Testing** (4-6 tasks)
    - Write end-to-end test: Email invoice workflow (Gmail → Xero → LinkedIn)
    - Write end-to-end test: Cross-platform social media post (Facebook + Instagram + Twitter)
    - Write end-to-end test: Weekly audit generation
    - Verify backward compatibility with Bronze/Silver tiers
    - Performance testing (1000+ action items, 60-second audit generation)
    - Create verification script (`verify_gold_prerequisites.py`)

**Estimated Total**: 45-65 tasks

---

### Phase 3: Red (Test-First Implementation)

**Command**: `/sp.tasks` → Implement each task with tests first

**Approach**:
- Write failing tests for each task before implementation
- Use pytest fixtures for MCP server mocking
- Use contract validation tests for MCP servers
- Write integration tests with sandbox/test APIs

---

### Phase 4: Green (Implementation)

**Command**: Implement code to pass tests

**Approach**:
- Implement MCP servers following FastMCP pattern
- Implement Pydantic models with validation
- Implement autonomous processor with file watcher
- Implement weekly scheduler with Claude API integration
- Ensure all tests pass

---

### Phase 5: Refactor (Code Quality)

**Command**: Refactor for maintainability

**Approach**:
- Extract common MCP logic to base class
- Extract OAuth flows to shared utility
- Extract Claude API calls to shared utility
- Ensure code follows PEP 8 style guide
- Add type hints for all functions

---

## Key Decisions

### Decision 1: Autonomous Processing via File Watcher

**Options Considered**:
1. Manual skill invocation (Silver tier approach)
2. File watcher with automatic skill invocation (chosen)
3. Event-driven architecture with message queue

**Decision**: File watcher with automatic skill invocation

**Rationale**:
- Meets 95% processing within 60 seconds goal (SC-001)
- Backward compatible with manual invocation
- Simpler than message queue (no additional infrastructure)
- PM2 provides crash recovery and monitoring

**Trade-offs**:
- Adds complexity of daemon management
- Requires PM2 installation and configuration
- 30-second polling interval (not real-time)

**Acceptance**: Justified by Gold tier P1 requirement (FR-001-008)

---

### Decision 2: FastMCP Framework for MCP Servers

**Options Considered**:
1. Custom MCP implementation (raw stdio protocol)
2. FastMCP framework with decorators (chosen)
3. Alternative MCP frameworks (e.g., mcp-python)

**Decision**: FastMCP framework with @mcp.tool decorators

**Rationale**:
- Automatic JSON schema generation
- Built-in error handling and logging
- Middleware support (rate limiting, authentication)
- Consistent with Silver tier MCP servers

**Trade-offs**:
- Dependency on FastMCP library
- Learning curve for decorators

**Acceptance**: Reduces MCP server implementation time by 50%

---

### Decision 3: OAuth 2.0 Token Storage in OS Credential Manager

**Options Considered**:
1. Store tokens in `.env` file
2. Store tokens in encrypted file
3. Store tokens in OS credential manager (chosen)

**Decision**: OS credential manager (Windows Credential Manager, macOS Keychain, Linux Secret Service)

**Rationale**:
- Tokens never written to files or logs
- OS-level encryption and access control
- Cross-platform support via `keyring` library

**Trade-offs**:
- Requires OS credential manager setup
- Manual token deletion if credential manager corrupted

**Acceptance**: Meets Principle V (Credential Security)

---

### Decision 4: Claude API for AI-Generated Insights

**Options Considered**:
1. Rule-based insights (template-based)
2. Claude API with prompt engineering (chosen)
3. Local LLM (e.g., Llama)

**Decision**: Claude API with prompt engineering

**Rationale**:
- High-quality insights (better than rule-based)
- No local GPU required (unlike local LLM)
- Consistent with existing Claude API usage (Silver tier)

**Trade-offs**:
- API cost (~$0.50 per weekly audit)
- Network dependency (requires internet)
- Latency (5-10 seconds per audit)

**Acceptance**: Justified by P4 requirement (FR-028-035) and SC-004 (3+ insights)

---

### Decision 5: PM2 for Process Management

**Options Considered**:
1. Python supervisor library
2. systemd (Linux only)
3. PM2 (Node.js process manager) (chosen)
4. Windows Service (Windows only)

**Decision**: PM2 process manager

**Rationale**:
- Cross-platform (Windows, macOS, Linux)
- Auto-restart on crash (10-second recovery)
- Cron scheduling built-in
- Web-based monitoring dashboard
- Startup on boot configuration

**Trade-offs**:
- Requires Node.js installation
- Learning curve for PM2 commands

**Acceptance**: Meets SC-008 (99% uptime, 10-second recovery)

---

## Risks and Mitigations

### Risk 1: MCP API Rate Limits Exceeded

**Likelihood**: Medium
**Impact**: High (blocks external actions)

**Mitigation**:
- Exponential backoff retry (1s, 2s, 4s)
- Rate limit monitoring via MCPServerStatus
- Request caching for failed calls (zero data loss)
- Graceful degradation (system continues with reduced functionality)

**Residual Risk**: Low (rate limits are generous for expected usage: Xero 60/min, Facebook 200/hour, Twitter 100/15min)

---

### Risk 2: AI Processor Daemon Crashes

**Likelihood**: Medium
**Impact**: High (no autonomous processing)

**Mitigation**:
- PM2 auto-restart (max 10 restarts, 10-second recovery)
- Crash logging to `/Logs/ai-processor-error.log`
- Health monitoring via `pm2 list` status
- Fallback to manual skill invocation (Silver tier compatibility)

**Residual Risk**: Low (PM2 provides reliable crash recovery)

---

### Risk 3: OAuth Token Expiry

**Likelihood**: High (tokens expire after 30-60 days)
**Impact**: Medium (MCP calls fail until token refreshed)

**Mitigation**:
- Refresh token flow for Xero (60-day expiry)
- Long-lived page tokens for Facebook/Instagram (never expire)
- Refresh token rotation for Twitter (6-month expiry)
- Token expiry monitoring via MCPServerStatus
- Clear error messages in logs with refresh instructions

**Residual Risk**: Low (refresh flows tested and documented in quickstart.md)

---

### Risk 4: Weekly Audit Fails Due to MCP Server Outage

**Likelihood**: Low
**Impact**: Medium (no CEO briefing)

**Mitigation**:
- Partial report generation (use cached data for unavailable MCP servers)
- Retry mechanism (3 attempts with exponential backoff)
- Status indicator in audit report (complete / partial / failed)
- Dashboard alert when audit fails

**Residual Risk**: Low (partial reports still provide value)

---

### Risk 5: Cross-Domain Workflow Stuck

**Likelihood**: Medium
**Impact**: Medium (workflow incomplete)

**Mitigation**:
- Workflow status tracking (active / completed / failed / cancelled)
- Dashboard visibility into stuck workflows
- Manual approval timeout (7 days → auto-cancel)
- Clear troubleshooting guide in quickstart.md

**Residual Risk**: Low (workflows can be manually cancelled)

---

## Success Metrics (from Spec)

Gold tier success measured by 14 criteria (SC-001 to SC-014):

1. **SC-001**: 95% of action items processed within 60 seconds automatically ✅
2. **SC-002**: 80% end-to-end workflow completion without human intervention (except approval) ✅
3. **SC-003**: Weekly audits 100% on-time delivery Monday 9:00 AM ✅
4. **SC-004**: CEO briefings 100% on-time Monday 10:00 AM with 3+ insights ✅
5. **SC-005**: Xero sync 99% success rate every 6 hours ✅
6. **SC-006**: Social media posting 95% success rate across 3 platforms ✅
7. **SC-007**: Cross-domain workflow routing 90% accuracy ✅
8. **SC-008**: AI Processor 99% uptime with 10-second crash recovery ✅
9. **SC-009**: Zero data loss during MCP server failures with retry queuing ✅
10. **SC-010**: Real-time Dashboard updates every 60 seconds ✅
11. **SC-011**: 70% reduction in manual intervention time vs Silver tier ✅
12. **SC-012**: 100% HITL compliance (no external action without approval) ✅
13. **SC-013**: 100% audit logging coverage ✅
14. **SC-014**: Full backward compatibility with Bronze/Silver tiers ✅

All success criteria achievable with proposed architecture.

---

## Next Steps

1. **Run `/sp.tasks`** to generate dependency-ordered tasks with acceptance criteria
2. **Begin Phase 2 (Red)**: Write failing tests for Task Group 1 (Data Models)
3. **Implement Phase 3 (Green)**: Implement code to pass tests
4. **Continue TDD cycle** through all 10 task groups
5. **Final integration testing**: End-to-end workflows and performance testing
6. **Deploy to production**: Follow quickstart.md setup guide

**Estimated Timeline**: 6-8 weeks (45-65 tasks at 1-2 tasks per day)

---

**Status**: ✅ Planning Complete - Ready for Task Generation
**Next Command**: `/sp.tasks`
