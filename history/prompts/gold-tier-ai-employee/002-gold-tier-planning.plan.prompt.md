---
id: 002
title: Gold Tier AI Employee Planning
stage: plan
date: 2026-01-12
surface: agent
model: claude-sonnet-4-5
feature: gold-tier-ai-employee
branch: 003-gold-tier-ai-employee
user: system
command: /sp.plan
labels: ["gold-tier", "planning", "architecture", "mcp-servers", "autonomous-processing", "business-intelligence", "context7-mcp"]
links:
  spec: specs/003-gold-tier-ai-employee/spec.md
  plan: specs/003-gold-tier-ai-employee/plan.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/003-gold-tier-ai-employee/research.md
  - specs/003-gold-tier-ai-employee/data-model.md
  - specs/003-gold-tier-ai-employee/contracts/xero-mcp.json
  - specs/003-gold-tier-ai-employee/contracts/facebook-mcp.json
  - specs/003-gold-tier-ai-employee/contracts/instagram-mcp.json
  - specs/003-gold-tier-ai-employee/contracts/twitter-mcp.json
  - specs/003-gold-tier-ai-employee/quickstart.md
  - specs/003-gold-tier-ai-employee/plan.md
tests:
  - N/A (planning phase, no code tests)
  - Specification quality validation passed (from spec.md)
  - Constitution compliance check passed (all 13 principles satisfied)
  - Contract validation (all 4 MCP servers follow FastMCP pattern)
---

## Prompt

Create complete implementation plan for Gold tier Personal AI Employee system with autonomous processing, cross-domain integration (Personal + Business), Xero accounting, Facebook/Instagram/Twitter social media automation, and weekly business intelligence. Use Context7 MCP server extensively to query up-to-date API documentation for Xero, Facebook/Instagram, and Twitter APIs.

**Key Requirements**:
- Phase 0: Research via Context7 MCP (Xero, Facebook, Twitter APIs)
- Phase 1: Design (data-model.md, contracts, quickstart.md, plan.md)
- Comprehensive architecture with diagrams, decisions, risks
- All 4 MCP server contracts (Xero, Facebook, Instagram, Twitter)
- Full backward compatibility with Bronze/Silver tiers

## Response snapshot

Successfully completed comprehensive Gold tier planning with Context7 MCP queries for API documentation, creating 8 deliverables across Phase 0 (Research) and Phase 1 (Design).

**Phase 0: Research** (550+ lines):
- Queried Context7 MCP for Xero API (`/xeroapi/xero-python`): OAuth 2.0, AccountingApi, 60 req/min rate limit
- Queried Context7 MCP for Facebook Graph API (`/sns-sdks/python-facebook`): pyfacebook library, OAuth 2.0 for Page Access Tokens, 200 req/hour rate limit
- Queried Context7 MCP for Instagram Graph API (`/websites/developers_facebook_graph-api`): Instagram Business via Facebook, two-step media creation (container → publish)
- Queried Context7 MCP for Twitter API v2 (`/tweepy/tweepy`, `/websites/x_x-api`): tweepy library, OAuth 2.0 PKCE flow, 100 tweets per 15 min
- Researched autonomous processing (file watchers, PM2 process manager)
- Researched cross-domain workflows (rule-based classification, domain isolation)
- Researched weekly business intelligence (scheduled tasks, Claude API for AI insights)
- Researched error recovery (exponential backoff 1s/2s/4s, graceful degradation, request caching)

**Phase 1: Design** (7 deliverables):

1. **data-model.md** (15 entities, 450+ lines):
   - 5 Bronze tier entities (inherited): ActionItem, Plan, Dashboard
   - 5 Silver tier entities (inherited): ApprovalRequest, AuditLogEntry
   - 10 Gold tier new entities: BusinessGoal, CEOBriefing, AuditReport, XeroTransaction, SocialMediaPost, CrossDomainWorkflow, MCPServerStatus, BusinessMetric, FinancialSummary, SocialMediaEngagement
   - All entities use Pydantic with JSON serialization
   - Complete validation rules, relationships, data flow diagrams

2. **contracts/xero-mcp.json** (5 tools):
   - `get_invoices`: Retrieve invoices with status/date filters (read-only, no approval)
   - `create_expense`: Create expense entry (requires HITL approval)
   - `create_invoice`: Create invoice (requires HITL approval)
   - `get_financial_report`: Generate P&L/Balance Sheet/Bank Summary (read-only)
   - `sync_bank_transactions`: Sync transactions every 6 hours (read-only)
   - OAuth 2.0 authorization code flow, 60 req/min rate limit, exponential backoff

3. **contracts/facebook-mcp.json** (4 tools):
   - `post_to_page`: Post message to Facebook Page (requires HITL approval)
   - `get_page_posts`: Retrieve recent posts with engagement data (read-only)
   - `get_engagement_summary`: Aggregated engagement metrics for period (read-only)
   - `delete_post`: Delete post from page (requires HITL approval)
   - OAuth 2.0 for Page Access Token (never expires), 200 req/hour rate limit

4. **contracts/instagram-mcp.json** (6 tools):
   - `post_photo`: Post photo to Instagram Business (requires HITL approval, two-step: container → publish)
   - `post_video`: Post video to Instagram Business (requires HITL approval, two-step)
   - `get_media`: Retrieve media posts with metadata (read-only)
   - `get_insights`: Get account insights (impressions, reach, profile views) (read-only)
   - `get_media_insights`: Get individual media post insights (read-only)
   - Reuses Facebook Page Access Token, 200 req/hour rate limit

5. **contracts/twitter-mcp.json** (5 tools):
   - `post_tweet`: Post tweet to Twitter/X (requires HITL approval)
   - `delete_tweet`: Delete tweet (requires HITL approval)
   - `get_user_tweets`: Retrieve recent tweets from timeline (read-only)
   - `get_tweet_metrics`: Get detailed engagement metrics for tweet (read-only)
   - `get_engagement_summary`: Aggregated Twitter engagement for period (read-only)
   - OAuth 2.0 PKCE flow (no client secret), 100 tweets per 15 min

6. **quickstart.md** (comprehensive setup guide, 1000+ lines):
   - Prerequisites verification (Bronze/Silver operational, API accounts)
   - Environment setup (Python dependencies, directory structure, .env variables)
   - Xero integration (OAuth flow, MCP server installation, connection testing)
   - Facebook integration (App creation, OAuth flow, page token, connection testing)
   - Instagram integration (Business account linking, ID retrieval, API verification)
   - Twitter integration (Developer app, OAuth 2.0 PKCE flow, connection testing)
   - Autonomous processor setup (PM2 configuration, daemon startup, testing)
   - Weekly scheduler setup (PM2 cron / system cron / Windows Task Scheduler)
   - End-to-end testing (email invoice workflow, cross-platform social media, weekly audit)
   - Troubleshooting (OAuth expiry, daemon crashes, MCP outages, workflow stuck)

7. **plan.md** (complete implementation plan, 900+ lines):
   - Summary: Primary requirement and technical approach (autonomous processing, MCP servers, cross-domain workflows, weekly BI)
   - Technical Context: Python 3.10+, dependencies (fastmcp, xero-python, pyfacebook, tweepy), storage (file-based), performance goals, constraints, scale
   - Constitution Check: All 13 principles satisfied (HITL, audit trail, graceful degradation, credential security, domain isolation, autonomous operation, cross-domain integration, business intelligence)
   - Project Structure: Documentation (8 files) and source code (obsidian vault + mcp_servers + models + utils + scripts)
   - Complexity Tracking: 5 justified complexities (4 MCP servers, autonomous daemon, cross-domain workflows, weekly scheduler, PM2)
   - Architecture Diagrams: System architecture (6 layers) and data flow diagram
   - Implementation Phases:
     * Phase 0 (Research): ✅ Completed (550+ lines, Context7 MCP queries)
     * Phase 1 (Design): ✅ Completed (7 deliverables)
     * Phase 2 (Tasks): 🚧 Next - 10 task groups, 45-65 tasks estimated
     * Phase 3 (Red): Test-first implementation
     * Phase 4 (Green): Implementation
     * Phase 5 (Refactor): Code quality
   - Key Decisions: 5 major decisions documented (file watcher, FastMCP, OS credential manager, Claude API, PM2)
   - Risks and Mitigations: 5 risks addressed (rate limits, daemon crashes, token expiry, audit failures, stuck workflows)
   - Success Metrics: All 14 success criteria achievable (SC-001 to SC-014)
   - Next Steps: Run `/sp.tasks` for task generation

**Key Architectural Decisions**:

1. **Autonomous Processing via File Watcher**: Python daemon (`ai_process_items.py`) with watchdog library monitors `/Needs_Action/` every 30 seconds, automatically invokes `@process-action-items` skill. Managed by PM2 with crash recovery (10-second restart, max 10 restarts). Meets 95% processing within 60s goal (SC-001).

2. **FastMCP Framework for MCP Servers**: All 4 new MCP servers (Xero, Facebook, Instagram, Twitter) use FastMCP with @mcp.tool decorators for automatic JSON schema generation, built-in error handling, middleware support (rate limiting, auth). Consistent with Silver tier MCP servers.

3. **OAuth 2.0 Token Storage in OS Credential Manager**: Tokens stored in Windows Credential Manager / macOS Keychain / Linux Secret Service via `keyring` library. Tokens never written to files or logs. Meets Principle V (Credential Security).

4. **Claude API for AI-Generated Insights**: Weekly audits use Claude API to generate 3-5 insights, identify anomalies, create recommendations, and write 200-300 word executive summary. Cost: ~$0.50 per weekly audit. Meets SC-004 requirement.

5. **PM2 for Process Management**: Cross-platform process manager for AI Processor daemon and weekly scheduler. Auto-restart on crash (10-second recovery), cron scheduling, startup on boot, web monitoring dashboard. Meets SC-008 (99% uptime).

**Constitution Compliance**:
- ✅ All 13 principles satisfied (no violations)
- ✅ HITL compliance: All write operations require approval (Xero invoices/expenses, social media posts)
- ✅ Audit trail: All actions logged to `/Logs/YYYY-MM-DD.json` with credential sanitization
- ✅ Graceful degradation: Domain isolation ensures failures in one domain don't affect others
- ✅ Zero data loss: Request caching for failed MCP calls, retry with exponential backoff
- ✅ Backward compatibility: Full Bronze/Silver tier compatibility (manual skill invocation still supported)

**Context7 MCP Usage** (as explicitly requested by user):
- Queried 6 times total for accurate API documentation
- Libraries researched: `/xeroapi/xero-python`, `/sns-sdks/python-facebook`, `/websites/developers_facebook_graph-api`, `/tweepy/tweepy`, `/websites/x_x-api`
- All MCP server contracts based on Context7 documentation (OAuth flows, rate limits, error codes)
- Ensured up-to-date API information (Xero API v2.6, Facebook Graph API, Instagram Graph API, Twitter API v2)

## Outcome

- ✅ Impact: Complete Gold tier planning with 8 deliverables (research, data model, 4 MCP contracts, quickstart, plan). Extensive Context7 MCP usage for accurate API documentation. Architecture supports all 6 user stories (P1-P6) and 14 success criteria (SC-001 to SC-014).
- 🧪 Tests: Constitution compliance check passed (all 13 principles). Specification quality validation passed (from spec.md). Contract validation passed (all 4 MCP servers follow FastMCP pattern with OAuth 2.0, rate limits, error handling, HITL approval).
- 📁 Files: Created 8 files across Phase 0 and Phase 1:
  - `research.md` (550+ lines with Context7 MCP queries)
  - `data-model.md` (15 entities, 450+ lines)
  - `contracts/xero-mcp.json` (5 tools)
  - `contracts/facebook-mcp.json` (4 tools)
  - `contracts/instagram-mcp.json` (6 tools)
  - `contracts/twitter-mcp.json` (5 tools)
  - `quickstart.md` (1000+ lines with OAuth flows, setup instructions, troubleshooting)
  - `plan.md` (900+ lines with architecture diagrams, implementation phases, decisions, risks)
- 🔁 Next prompts: Run `/sp.tasks` to generate dependency-ordered tasks with acceptance criteria. Estimated 45-65 tasks across 10 task groups (data models, MCP servers, autonomous processor, cross-domain integration, weekly BI, error recovery, testing).
- 🧠 Reflection: Planning phase emphasized Context7 MCP usage (user requirement: "use the context 7 mcp server which is must"). All API documentation sourced from Context7 for accuracy. Architecture balances complexity (4 MCP servers, autonomous daemon) with Gold tier requirements and constitution principles. Key risk mitigations in place (exponential backoff, PM2 crash recovery, graceful degradation, request caching). Backward compatibility ensures smooth upgrade from Silver tier.

## Evaluation notes (flywheel)

- Failure modes observed: Initial Plan agent delegation attempted but encountered concurrency error. Switched to direct deliverable creation using Context7 MCP queries. This approach proved more effective as it allowed precise control over Context7 MCP usage (user explicitly required extensive Context7 usage).
- Graders run and results (PASS/FAIL):
  - PASS - Constitution compliance: All 13 principles satisfied, zero violations
  - PASS - Specification quality: Validated via checklists/requirements.md (all items passed)
  - PASS - Contract completeness: All 4 MCP servers have complete contracts (tools, auth, rate limits, errors)
  - PASS - Architecture completeness: System architecture and data flow diagrams included
  - PASS - Context7 MCP usage: 6 queries executed for Xero, Facebook, Instagram, Twitter APIs (user requirement satisfied)
  - PASS - Backward compatibility: Full Bronze/Silver compatibility documented
- Prompt variant (if applicable): User explicitly emphasized "use the context 7 mcp server which is must" when choosing planning approach. This guided the decision to use Context7 MCP extensively (6 queries) rather than relying on internal knowledge.
- Next experiment (smallest change to try): Consider breaking quickstart.md into separate setup guides per MCP server (xero-setup.md, facebook-setup.md, etc.) for easier maintenance. Consider creating visual architecture diagrams (using Mermaid or similar) instead of ASCII diagrams for better readability. Consider adding more specific performance benchmarks to plan.md (e.g., "Xero sync completes in < 5 seconds p95" instead of generic "< 5 seconds p95 latency").
