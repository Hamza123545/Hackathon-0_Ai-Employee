# Data Model: Gold Tier AI Employee

**Feature**: Gold Tier Personal AI Employee
**Version**: 1.0.0
**Date**: 2026-01-12
**Status**: Draft

## Purpose

This document defines the data model for Gold Tier AI Employee system, extending Bronze and Silver tiers with new entities for autonomous processing, cross-domain integration, business intelligence, and social media automation.

## Design Principles

1. **Backward Compatibility**: All Bronze and Silver tier entities remain unchanged
2. **Cross-Domain Integration**: Personal and Business domain entities unified via tagging
3. **Audit Trail**: Every external action logged with full context and credentials sanitized
4. **Zero Data Loss**: Request caching and retry queuing prevent data loss during failures
5. **Type Safety**: All entities use Pydantic models with validation
6. **Serialization**: All entities serializable to JSON for file storage and logging

---

## Bronze Tier Entities (Inherited)

### 1. Action Item

**File Location**: `/Needs_Action/<timestamp>-<source>.md`

**Purpose**: Represents a detected action item requiring processing

**Fields**:
- `id` (str, UUID): Unique identifier
- `timestamp` (datetime): When action was detected
- `source` (str): Origin (gmail, whatsapp, linkedin, filesystem)
- `priority` (str, enum): urgent, high, normal, low
- `category` (str): Action category from Company Handbook
- `title` (str): Brief action description
- `description` (str): Full action details
- `detected_by` (str): Watcher that detected the action
- `status` (str, enum): pending, processed, archived
- `metadata` (dict): Additional context

**Relationships**:
- Creates → Plan (1:1)
- Referenced by → Audit Log Entry (1:N)

---

### 2. Plan

**File Location**: `/Plans/<action-id>-plan.md`

**Purpose**: Structured plan for executing an action item

**Fields**:
- `id` (str, UUID): Unique identifier
- `action_item_id` (str, UUID): Reference to source action item
- `created_at` (datetime): Plan creation timestamp
- `title` (str): Plan title
- `classification` (str): personal, business, cross-domain
- `steps` (list[Step]): Ordered list of execution steps
  - `step_number` (int)
  - `description` (str)
  - `requires_approval` (bool)
  - `mcp_server` (str, optional)
  - `estimated_duration` (str)
- `requires_approval` (bool): Whether plan needs human approval
- `status` (str, enum): draft, approved, in_progress, completed, failed

**Relationships**:
- Created from → Action Item (1:1)
- Creates → Approval Request (1:1, if requires_approval=true)

---

### 3. Dashboard

**File Location**: `/Dashboard.md`

**Purpose**: Real-time system status and metrics

**Fields**:
- `last_updated` (datetime): Last update timestamp
- `system_status` (str, enum): healthy, degraded, down
- `pending_actions_count` (int): Count of unprocessed actions
- `pending_approvals_count` (int): Count of pending approvals
- `watchers_status` (dict[str, WatcherStatus]): Status per watcher
  - `watcher_name` (str)
  - `status` (str): active, stopped, error
  - `last_check` (datetime)
  - `items_detected_24h` (int)
- `recent_activity` (list[ActivityEntry]): Last 10 activities
  - `timestamp` (datetime)
  - `action_type` (str)
  - `description` (str)
  - `status` (str)

**Relationships**:
- References → Action Item (N)
- References → Approval Request (N)

---

## Silver Tier Entities (Inherited)

### 4. Approval Request

**File Location**: `/Pending_Approval/<timestamp>-<action-type>.json`

**Purpose**: Represents an external action awaiting human approval

**Fields**:
- `id` (str, UUID): Unique identifier
- `created_at` (datetime): Request creation timestamp
- `action_type` (str): send_email, send_whatsapp, post_linkedin, browser_action
- `mcp_server` (str): MCP server to execute action
- `action_parameters` (dict): Parameters for MCP tool invocation
- `reason` (str): Why this action is needed
- `risk_level` (str, enum): low, medium, high
- `estimated_cost` (str): Estimated API call cost
- `plan_reference` (str): Link to source plan
- `status` (str, enum): pending, approved, rejected, executed
- `approved_at` (datetime, optional): When approved
- `approved_by` (str, optional): Who approved (always "human")

**Relationships**:
- Created from → Plan (1:1)
- Generates → Audit Log Entry (1:1)

---

### 5. Audit Log Entry

**File Location**: `/Logs/<YYYY-MM-DD>.json` (appended)

**Purpose**: Immutable record of all external actions

**Fields**:
- `id` (str, UUID): Unique identifier
- `timestamp` (datetime): Action execution timestamp
- `action_type` (str): Type of action performed
- `mcp_server` (str): MCP server used
- `tool_name` (str): MCP tool invoked
- `parameters` (dict): Sanitized action parameters (credentials removed)
- `result` (dict): Action result (success/failure)
- `approval_request_id` (str, UUID): Reference to approval request
- `user` (str): Always "human" or "system"
- `status` (str, enum): success, failure, partial
- `error_message` (str, optional): Error details if failed

**Relationships**:
- References → Approval Request (1:1)
- References → Action Item (1:1)

---

## Gold Tier New Entities

### 6. Business Goal

**File Location**: `/Business/Goals/<goal-id>.json`

**Purpose**: Represents a business objective tracked across multiple actions

**Fields**:
- `id` (str, UUID): Unique identifier
- `created_at` (datetime): Goal creation timestamp
- `title` (str): Goal title
- `description` (str): Detailed goal description
- `target_date` (date): Target completion date
- `status` (str, enum): active, completed, deferred, cancelled
- `priority` (str, enum): critical, high, normal, low
- `metrics` (list[Metric]): Success metrics
  - `metric_name` (str)
  - `target_value` (float)
  - `current_value` (float)
  - `unit` (str)
- `related_actions` (list[str]): Action item IDs contributing to goal
- `owner` (str): Goal owner (e.g., "CEO", "CFO")
- `tags` (list[str]): Categorization tags

**Relationships**:
- References → Action Item (N)
- Referenced by → CEO Briefing (N)
- Referenced by → Audit Report (N)

**Validation**:
- `target_date` must be future date
- `metrics` must have at least 1 entry
- `status` transitions: active → completed/deferred/cancelled

---

### 7. CEO Briefing

**File Location**: `/Briefings/<YYYY-MM-DD>-ceo-briefing.md`

**Purpose**: Weekly executive summary with AI-generated insights

**Fields**:
- `id` (str, UUID): Unique identifier
- `generated_at` (datetime): Briefing generation timestamp
- `period_start` (date): Reporting period start (Monday)
- `period_end` (date): Reporting period end (Sunday)
- `executive_summary` (str): AI-generated high-level summary (200-300 words)
- `key_insights` (list[str]): 3-5 AI-generated insights
- `financial_summary` (FinancialSummary): Xero financial data
- `social_media_summary` (SocialMediaEngagement): Aggregated engagement
- `action_items_summary` (dict): Processed actions breakdown
  - `total_processed` (int)
  - `by_category` (dict[str, int])
  - `by_priority` (dict[str, int])
- `goal_progress` (list[GoalProgress]): Business goal status
  - `goal_id` (str)
  - `goal_title` (str)
  - `completion_percentage` (float)
  - `status` (str)
- `risks_and_alerts` (list[str]): Identified risks or anomalies
- `recommendations` (list[str]): AI-generated recommendations
- `attachments` (list[str]): Links to detailed reports

**Relationships**:
- References → Audit Report (1:1)
- References → Financial Summary (1:1)
- References → Social Media Engagement (1:1)
- References → Business Goal (N)

**Validation**:
- `period_start` must be Monday
- `period_end` must be Sunday
- `key_insights` must have 3-5 items
- `executive_summary` must be 200-300 words

**Generation**:
- Scheduled every Monday at 10:00 AM via cron/Task Scheduler
- Uses Claude API for AI-generated insights
- Aggregates data from Audit Report, Xero, social media MCP servers

---

### 8. Audit Report

**File Location**: `/Accounting/Audits/<YYYY-MM-DD>-audit-report.json`

**Purpose**: Weekly business and accounting audit with cross-domain analysis

**Fields**:
- `id` (str, UUID): Unique identifier
- `generated_at` (datetime): Audit generation timestamp
- `period_start` (date): Audit period start
- `period_end` (date): Audit period end
- `financial_data` (FinancialSummary): Xero financial summary
- `social_media_data` (SocialMediaEngagement): Social media metrics
- `action_logs_summary` (dict): Summary of action logs
  - `total_actions` (int)
  - `actions_by_domain` (dict[str, int]): personal vs business
  - `actions_by_type` (dict[str, int])
  - `success_rate` (float): Percentage of successful actions
- `cross_domain_workflows` (list[CrossDomainWorkflow]): Cross-domain actions
- `anomalies` (list[Anomaly]): Detected anomalies
  - `severity` (str): low, medium, high, critical
  - `type` (str): financial, social, operational
  - `description` (str)
  - `detected_at` (datetime)
- `mcp_server_health` (dict[str, MCPServerStatus]): Health per MCP server
- `recommendations` (list[str]): AI-generated recommendations
- `status` (str, enum): complete, partial, failed

**Relationships**:
- References → Financial Summary (1:1)
- References → Social Media Engagement (1:1)
- References → Cross-Domain Workflow (N)
- References → MCP Server Status (N)
- Creates → CEO Briefing (1:1)

**Validation**:
- `period_end` must be after `period_start`
- `success_rate` must be 0.0-100.0
- `anomalies` severity must be valid enum

**Generation**:
- Scheduled every Monday at 9:00 AM via cron/Task Scheduler
- Aggregates Xero data, social media metrics, action logs
- Runs AI analysis for anomaly detection

---

### 9. Xero Transaction

**File Location**: `/Accounting/Transactions/<transaction-id>.json`

**Purpose**: Represents a financial transaction synced from Xero

**Fields**:
- `id` (str, UUID): Unique identifier (Xero transaction ID)
- `synced_at` (datetime): When transaction was synced
- `transaction_type` (str, enum): invoice, expense, bank_transaction, payment
- `date` (date): Transaction date
- `amount` (float): Transaction amount
- `currency` (str): Currency code (ISO 4217)
- `status` (str): Xero transaction status
- `contact_name` (str): Customer/vendor name
- `description` (str): Transaction description
- `category` (str): Expense category or account code
- `line_items` (list[LineItem], optional): Invoice/expense line items
  - `description` (str)
  - `quantity` (float)
  - `unit_amount` (float)
  - `account_code` (str)
- `metadata` (dict): Additional Xero metadata
- `approval_request_id` (str, UUID, optional): If created via HITL

**Relationships**:
- Referenced by → Financial Summary (N)
- Referenced by → Audit Report (N)
- May reference → Approval Request (1:1)

**Validation**:
- `amount` must be positive for expenses/invoices
- `currency` must be valid ISO 4217 code
- `transaction_type` must be valid enum

**Sync**:
- Synced every 6 hours via scheduled task
- Uses Xero MCP Server `sync_bank_transactions` tool
- Cached locally for offline access

---

### 10. Social Media Post

**File Location**: `/Business/Social_Media/<platform>/<post-id>.json`

**Purpose**: Represents a social media post created via MCP servers

**Fields**:
- `id` (str, UUID): Unique identifier (platform post ID)
- `posted_at` (datetime): Post publication timestamp
- `platform` (str, enum): facebook, instagram, twitter
- `platform_post_id` (str): Platform-specific post ID
- `content` (str): Post text content
- `media_urls` (list[str], optional): Attached media URLs
- `post_type` (str, enum): text, photo, video, link
- `status` (str, enum): published, draft, deleted
- `engagement_metrics` (EngagementMetrics): Post engagement data
  - `likes` (int)
  - `comments` (int)
  - `shares` (int)
  - `impressions` (int)
  - `reach` (int)
  - `engagement_rate` (float)
- `approval_request_id` (str, UUID): Reference to approval request
- `created_by` (str): Always "ai_employee"
- `metadata` (dict): Platform-specific metadata

**Relationships**:
- References → Approval Request (1:1)
- Referenced by → Social Media Engagement (N)
- Referenced by → Audit Report (N)

**Validation**:
- `platform` must be facebook, instagram, or twitter
- `content` must not exceed platform limits (280 chars for Twitter, 2200 for Instagram, 5000 for Facebook)
- `engagement_metrics` must have non-negative values

**Sync**:
- Posted via Facebook/Instagram/Twitter MCP Servers
- Engagement metrics synced daily at 8:00 AM
- Used in weekly audit and CEO briefing

---

### 11. Cross-Domain Workflow

**File Location**: `/Business/Workflows/<workflow-id>.json`

**Purpose**: Represents a workflow spanning Personal and Business domains

**Fields**:
- `id` (str, UUID): Unique identifier
- `created_at` (datetime): Workflow creation timestamp
- `title` (str): Workflow title
- `description` (str): Workflow description
- `domains` (list[str]): Domains involved (personal, business, accounting, social_media)
- `trigger_source` (str): What triggered the workflow (gmail, whatsapp, xero, etc.)
- `steps` (list[WorkflowStep]): Workflow steps
  - `step_number` (int)
  - `domain` (str): Domain for this step
  - `action_type` (str)
  - `mcp_server` (str)
  - `status` (str): pending, completed, failed
  - `completed_at` (datetime, optional)
- `status` (str, enum): active, completed, failed, cancelled
- `completion_percentage` (float): 0.0-100.0
- `related_action_items` (list[str]): Action item IDs
- `related_transactions` (list[str]): Xero transaction IDs, if applicable
- `related_posts` (list[str]): Social media post IDs, if applicable

**Relationships**:
- References → Action Item (N)
- References → Xero Transaction (N, optional)
- References → Social Media Post (N, optional)
- Referenced by → Audit Report (N)

**Validation**:
- `domains` must have at least 2 domains
- `completion_percentage` must be 0.0-100.0
- `steps` must be in sequential order

**Example**:
- Workflow: "Process invoice payment and notify client"
  1. Domain: accounting → Create Xero invoice (MCP: xero-mcp)
  2. Domain: personal → Send Gmail notification (MCP: gmail-mcp)
  3. Domain: business → Post LinkedIn update (MCP: linkedin-mcp)

---

### 12. MCP Server Status

**File Location**: `/System/MCP_Status/<server-name>.json`

**Purpose**: Tracks health and availability of MCP servers

**Fields**:
- `server_name` (str): MCP server name (xero-mcp, facebook-mcp, etc.)
- `last_checked` (datetime): Last health check timestamp
- `status` (str, enum): healthy, degraded, down, unknown
- `domain` (str, enum): personal, business, accounting, social_media
- `connection_status` (str, enum): connected, disconnected, timeout
- `last_successful_request` (datetime, optional): Last successful API call
- `last_error` (str, optional): Last error message
- `error_count_24h` (int): Number of errors in last 24 hours
- `success_rate_24h` (float): Success rate percentage (0.0-100.0)
- `average_response_time_ms` (float): Average response time in milliseconds
- `rate_limit_status` (dict): Rate limit info
  - `current_usage` (int)
  - `limit` (int)
  - `reset_at` (datetime)
- `enabled` (bool): Whether server is enabled in config

**Relationships**:
- Referenced by → Dashboard (N)
- Referenced by → Audit Report (N)

**Validation**:
- `status` must be valid enum
- `success_rate_24h` must be 0.0-100.0
- `error_count_24h` must be non-negative

**Health Check**:
- Checked every 5 minutes via scheduled task
- Uses MCP server `/health` endpoint
- Triggers graceful degradation if status is down

---

### 13. Business Metric

**File Location**: `/Business/Metrics/<YYYY-MM-DD>-<metric-name>.json`

**Purpose**: Tracks specific business KPIs over time

**Fields**:
- `id` (str, UUID): Unique identifier
- `metric_name` (str): Metric name (e.g., "monthly_revenue", "social_engagement")
- `date` (date): Metric date
- `value` (float): Metric value
- `unit` (str): Metric unit (USD, percentage, count, etc.)
- `source` (str): Data source (xero, facebook, instagram, twitter, manual)
- `category` (str, enum): financial, social, operational, growth
- `trend` (str, enum): up, down, stable
- `change_percentage` (float): Percentage change from previous period
- `target_value` (float, optional): Target value if applicable
- `metadata` (dict): Additional context

**Relationships**:
- Referenced by → CEO Briefing (N)
- Referenced by → Audit Report (N)
- May reference → Business Goal (N)

**Validation**:
- `category` must be valid enum
- `trend` calculated automatically based on historical data
- `change_percentage` calculated automatically

**Tracking**:
- Updated daily at 8:00 AM via scheduled task
- Aggregates data from Xero, social media MCP servers
- Used for trend analysis in CEO briefings

---

### 14. Financial Summary

**File Location**: `/Accounting/Summaries/<YYYY-MM-DD>-financial-summary.json`

**Purpose**: Aggregated financial data from Xero for a period

**Fields**:
- `id` (str, UUID): Unique identifier
- `generated_at` (datetime): Summary generation timestamp
- `period_start` (date): Financial period start
- `period_end` (date): Financial period end
- `report_type` (str, enum): weekly, monthly, quarterly, annual
- `revenue` (float): Total revenue for period
- `expenses` (float): Total expenses for period
- `net_profit` (float): Revenue - Expenses
- `profit_margin` (float): (Net Profit / Revenue) * 100
- `outstanding_invoices` (int): Count of unpaid invoices
- `outstanding_amount` (float): Total amount of unpaid invoices
- `top_expenses` (list[dict]): Top 5 expense categories
  - `category` (str)
  - `amount` (float)
  - `percentage_of_total` (float)
- `bank_balance` (float): Current bank balance
- `currency` (str): Currency code (ISO 4217)
- `xero_data_source` (dict): Xero report metadata
- `status` (str, enum): complete, partial, stale

**Relationships**:
- References → Xero Transaction (N)
- Referenced by → Audit Report (1:1)
- Referenced by → CEO Briefing (1:1)

**Validation**:
- `net_profit` = `revenue` - `expenses`
- `profit_margin` calculated correctly
- `period_end` must be after `period_start`
- `outstanding_amount` must be non-negative

**Generation**:
- Generated weekly (Monday 9:00 AM) via Xero MCP `get_financial_report` tool
- Cached for 24 hours to reduce API calls
- Used in Audit Report and CEO Briefing

---

### 15. Social Media Engagement

**File Location**: `/Business/Engagement/<YYYY-MM-DD>-engagement-summary.json`

**Purpose**: Aggregated social media engagement metrics across platforms

**Fields**:
- `id` (str, UUID): Unique identifier
- `generated_at` (datetime): Summary generation timestamp
- `period_start` (date): Engagement period start
- `period_end` (date): Engagement period end
- `platforms` (dict[str, PlatformEngagement]): Engagement per platform
  - `platform` (str): facebook, instagram, twitter
  - `posts_count` (int): Number of posts in period
  - `total_likes` (int): Total likes across posts
  - `total_comments` (int): Total comments across posts
  - `total_shares` (int): Total shares/retweets across posts
  - `total_impressions` (int): Total impressions
  - `total_reach` (int): Total reach
  - `engagement_rate` (float): (Likes + Comments + Shares) / Impressions * 100
  - `follower_count` (int): Current follower count
  - `follower_growth` (int): Change in followers during period
- `overall_engagement_rate` (float): Weighted average across platforms
- `top_performing_posts` (list[dict]): Top 5 posts by engagement
  - `platform` (str)
  - `post_id` (str)
  - `content` (str, truncated to 100 chars)
  - `engagement_rate` (float)
- `status` (str, enum): complete, partial, stale

**Relationships**:
- References → Social Media Post (N)
- Referenced by → Audit Report (1:1)
- Referenced by → CEO Briefing (1:1)

**Validation**:
- `engagement_rate` calculated correctly per platform
- `overall_engagement_rate` is weighted average
- `period_end` must be after `period_start`
- All counts must be non-negative

**Generation**:
- Generated weekly (Monday 9:00 AM) via Facebook/Instagram/Twitter MCP servers
- Aggregates metrics using `get_engagement_summary` tools
- Used in Audit Report and CEO Briefing

---

## Entity Relationships Diagram

```
[Action Item] --1:1--> [Plan] --1:1--> [Approval Request] --1:1--> [Audit Log Entry]
     |                    |                    |
     |                    |                    +--N:1--> [Cross-Domain Workflow]
     +--N:1--> [Business Goal]
                         |
                         +--N:1--> [CEO Briefing]
                                        |
                                        +--1:1--> [Audit Report]
                                        |              |
                                        |              +--1:1--> [Financial Summary] --N:1--> [Xero Transaction]
                                        |              |
                                        |              +--1:1--> [Social Media Engagement] --N:1--> [Social Media Post]
                                        |              |
                                        |              +--N:1--> [Cross-Domain Workflow]
                                        |              |
                                        |              +--N:1--> [MCP Server Status]
                                        |
                                        +--N:1--> [Business Metric]

[Dashboard] --references--> [Action Item], [Approval Request], [MCP Server Status]
```

---

## Data Flow

### 1. Autonomous Processing Flow
```
File Watcher → Action Item → AI Processor → Plan → Approval Request → Approved → Execute → Audit Log
```

### 2. Xero Sync Flow
```
Scheduled Task (6 hours) → Xero MCP → Xero Transaction → Financial Summary → Audit Report
```

### 3. Social Media Flow
```
Plan → Approval Request → Approved → Facebook/Instagram/Twitter MCP → Social Media Post → Engagement → Social Media Engagement
```

### 4. Weekly Audit Flow
```
Monday 9:00 AM → Aggregate (Xero + Social + Logs) → Audit Report → CEO Briefing → Dashboard
```

### 5. Cross-Domain Workflow Flow
```
Action Item (Gmail) → Plan → Step 1: Xero Invoice → Step 2: Send Email → Step 3: LinkedIn Post → Complete
```

---

## Serialization Standards

### File Formats
- **JSON**: All structured entities (Xero Transaction, Social Media Post, MCP Server Status, etc.)
- **Markdown**: Human-readable reports (Action Item, Plan, CEO Briefing, Audit Report)
- **Log Files**: JSONL (JSON Lines) for Audit Log Entries

### JSON Schema
All entities have corresponding Pydantic models with:
- Type validation
- Field constraints (min/max, regex, enums)
- Auto-generated JSON Schema for documentation
- Serialization/deserialization methods

### Timestamp Format
- ISO 8601: `YYYY-MM-DDTHH:MM:SS.sssZ`
- All timestamps in UTC
- Converted to local time for display only

### Currency Format
- ISO 4217 currency codes (USD, GBP, EUR, etc.)
- Amounts stored as float (2 decimal places for display)
- Currency symbol display handled by UI layer

---

## Validation Rules

### Required Field Validation
- All `required` fields must be present
- No null values for required fields
- Empty strings not allowed for required string fields

### Enum Validation
- All enum fields validated against defined enum values
- Case-sensitive enum matching
- Invalid enum values rejected with clear error message

### Range Validation
- Percentage fields: 0.0-100.0
- Counts: non-negative integers
- Amounts: positive floats for transactions
- Dates: `end_date` must be after `start_date`

### Cross-Field Validation
- `net_profit` = `revenue` - `expenses`
- `completion_percentage` matches completed steps / total steps
- `success_rate` calculated from success and failure counts

---

## Migration from Silver Tier

### Backward Compatibility
- All Bronze and Silver tier entities unchanged
- New Gold tier entities additive only
- Existing files and formats preserved
- No breaking changes to APIs or data structures

### Migration Steps
1. Add new entity directories (`/Business`, `/Accounting`, `/Briefings`)
2. Initialize MCP Server Status for all servers
3. Run initial Xero sync to populate Xero Transactions
4. Generate initial Financial Summary and Social Media Engagement
5. First weekly audit scheduled for next Monday

### Data Retention
- Action Items: 90 days
- Audit Logs: 90 days
- CEO Briefings: Indefinite (archived after 1 year)
- Xero Transactions: Indefinite (synced from Xero)
- Social Media Posts: 90 days (engagement metrics retained)
- MCP Server Status: 7 days (rolling)

---

## Performance Considerations

### Caching Strategy
- Xero data cached for 6 hours (sync interval)
- Social media engagement cached for 24 hours
- MCP Server Status cached for 5 minutes
- CEO Briefings cached indefinitely (static after generation)

### Indexing
- Action Items indexed by `status` and `priority`
- Xero Transactions indexed by `date` and `transaction_type`
- Social Media Posts indexed by `platform` and `posted_at`
- Audit Logs indexed by `timestamp` and `action_type`

### Query Optimization
- Dashboard queries limited to last 24 hours
- Audit Report queries limited to 7-day period
- CEO Briefing aggregates pre-computed during generation
- Pagination for large result sets (max 100 items per page)

---

## Security and Privacy

### Credential Sanitization
- All credentials removed from Audit Logs via `CredentialSanitizer`
- OAuth tokens never logged
- API keys never logged
- Passwords never logged

### Access Control
- All external actions require HITL approval
- Approval workflow enforced by file system (`/Pending_Approval` → `/Approved`)
- No bypass mechanism for approval

### Audit Trail
- Every external action logged with full context
- Immutable audit logs (append-only)
- Audit logs include user (always "human" or "system")
- Failed actions logged with error details

---

## Error Handling

### Validation Errors
- Pydantic validation errors return clear error messages
- Invalid enum values list valid options
- Range violations specify min/max bounds
- Required field violations list missing fields

### MCP Server Errors
- Retry with exponential backoff (1s, 2s, 4s)
- Request caching for zero data loss
- Graceful degradation when server down
- Error logged to MCP Server Status

### Data Integrity
- Atomic file writes (write to temp, then rename)
- File locking for concurrent access
- Backup on every write to `/System/Backups`
- Checksum validation for critical files

---

## Testing Strategy

### Unit Tests
- Pydantic model validation tests
- Serialization/deserialization tests
- Enum validation tests
- Cross-field validation tests

### Integration Tests
- Entity relationship tests
- Data flow tests (end-to-end)
- MCP server integration tests
- File system persistence tests

### Performance Tests
- Large dataset handling (1000+ action items)
- Query performance benchmarks
- Caching effectiveness tests
- Concurrent access tests

---

## Appendix: Entity Size Estimates

| Entity | Avg Size (bytes) | Max Count | Total Storage |
|--------|------------------|-----------|---------------|
| Action Item | 2 KB | 1000 | 2 MB |
| Plan | 3 KB | 1000 | 3 MB |
| Approval Request | 1.5 KB | 500 | 750 KB |
| Audit Log Entry | 1 KB | 10,000 | 10 MB |
| Xero Transaction | 2 KB | 5,000 | 10 MB |
| Social Media Post | 1.5 KB | 1,000 | 1.5 MB |
| CEO Briefing | 15 KB | 52 (yearly) | 780 KB |
| Audit Report | 20 KB | 52 (yearly) | 1 MB |
| Financial Summary | 5 KB | 52 (yearly) | 260 KB |
| Social Media Engagement | 8 KB | 52 (yearly) | 416 KB |
| **Total** | | | **~30 MB/year** |

---

**Status**: Ready for implementation
**Next Steps**: Create `quickstart.md` and update `plan.md`
