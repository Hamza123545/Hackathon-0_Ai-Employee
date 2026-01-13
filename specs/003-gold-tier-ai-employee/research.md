# Gold Tier Research: Technical Investigation

**Feature**: Gold Tier AI Employee
**Branch**: 003-gold-tier-ai-employee
**Date**: 2026-01-12
**Phase**: Phase 0 - Research

## Research Summary

This document captures technical research for Gold tier extensions to the Personal AI Employee system. Research focused on Xero accounting integration, social media automation (Facebook, Instagram, Twitter), business intelligence automation, cross-domain integration, and error recovery strategies.

## 1. Xero API Integration

### Decision
Use official **xero-python SDK** (version 2.0+) wrapped in FastMCP server for standardized MCP protocol integration.

### Rationale
- Official SDK maintained by Xero with 926+ code snippets and high reputation score (Context7)
- Built-in OAuth 2.0 token management with automatic refresh via `OAuth2Token` class
- Comprehensive API coverage: Invoices, Expenses, Bank Transactions, Financial Reports
- Existing MCP server available: https://github.com/XeroAPI/xero-mcp-server (official implementation)
- Consistent with Silver tier FastMCP pattern

### Implementation Details

**Authentication**:
- OAuth 2.0 authorization code flow
- Token endpoint: `https://identity.xero.com/connect/token`
- Authorization endpoint: `https://login.xero.com/identity/connect/authorize`
- Required scopes: `accounting.transactions`, `accounting.reports.read`, `accounting.settings`
- Token refresh handled automatically by SDK
- Tokens stored securely in OS credential manager (not `.env`)

**Key API Endpoints**:
```python
from xeroapi import AccountingApi, ApiClient, Configuration
from xeroapi.models import Invoice, ExpenseClaim, BankTransaction

# Initialize API
api_client = ApiClient(configuration=config)
accounting_api = AccountingApi(api_client)

# Get invoices (filtered)
invoices = accounting_api.get_invoices(
    xero_tenant_id=tenant_id,
    statuses=["DRAFT", "SUBMITTED", "AUTHORISED", "PAID"],
    date_from="2026-01-01",
    date_to="2026-01-31"
)

# Create expense claim
expense = ExpenseClaim(
    user=user_id,
    amount=150.00,
    category="Office Supplies",
    description="Printer ink for home office"
)
accounting_api.create_expense_claims(xero_tenant_id, expense_claims=[expense])

# Get financial reports
report = accounting_api.get_report_profit_and_loss(
    xero_tenant_id=tenant_id,
    date_from="2026-01-01",
    date_to="2026-01-31"
)
```

**Rate Limits**:
- Standard Xero limits: 60 requests/minute per organization
- Burst limit: 100 requests (then throttled)
- Daily limit: 5000 requests/organization
- Implement exponential backoff: 1s, 2s, 4s (max 3 retries)

**Error Handling**:
```python
from xeroapi.exceptions import ApiException

try:
    invoices = accounting_api.get_invoices(xero_tenant_id=tenant_id)
except ApiException as e:
    if e.status == 429:  # Rate limit
        time.sleep(60)  # Wait 1 minute
        retry()
    elif e.status == 401:  # Auth error
        refresh_token()
        retry()
    else:
        log_error_and_cache_request(e)
```

### Alternatives Considered

**Alternative 1: Direct REST API**
- Pro: No SDK dependency
- Con: Complex OAuth 2.0 token management, manual refresh logic
- Con: Error handling requires extensive boilerplate
- **Rejected**: SDK provides significant value for OAuth complexity

**Alternative 2: Third-party accounting aggregators (Plaid, Finicity)**
- Pro: Multi-platform support (not just Xero)
- Con: Additional cost, unnecessary complexity for single accounting system
- Con: Less direct control over data sync
- **Rejected**: Over-engineered for Gold tier requirements

### Implementation Notes

**Gotcha 1**: Xero uses tenant IDs (organization IDs) - must retrieve after OAuth to identify which organization to operate on.

**Gotcha 2**: Expense claims vs Bank transactions - Expense claims are for reimbursement requests, Bank transactions are actual ledger entries. Most business expenses should use Bank transactions.

**Gotcha 3**: Invoice status transitions: DRAFT → SUBMITTED → AUTHORISED → PAID (cannot skip states).

**Best Practice**: Always validate date formats as ISO 8601 (YYYY-MM-DD) - Xero API rejects non-ISO dates.

---

## 2. Facebook Graph API Integration

### Decision
Use **python-facebook (pyfacebook)** library (version 1.0+) for Facebook Pages API with FastMCP wrapper.

### Rationale
- Comprehensive Graph API coverage with 192 code snippets, high reputation (Context7)
- Built-in rate limit handling with configurable sleep strategies
- Supports Facebook Pages (business posts) and Instagram Business (linked accounts)
- OAuth 2.0 token management included
- Single library for both Facebook and Instagram (reduces dependencies)

### Implementation Details

**Authentication**:
- OAuth 2.0 with long-lived Page Access Tokens (60-day expiry)
- Token exchange: Short-lived user token → Long-lived user token → Page access token
- Scope required: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`
- Instagram automatically accessible via linked Facebook Page

**Key API Endpoints**:
```python
from facebook import GraphAPI

# Initialize with page access token
graph = GraphAPI(access_token=PAGE_ACCESS_TOKEN, version="18.0")

# Create Facebook Page post
post = graph.put_object(
    parent_object=f"{page_id}",
    connection_name="feed",
    message="New product launch! Check out our latest innovation.",
    link="https://example.com/product"
)

# Get post engagement metrics
metrics = graph.get_object(
    id=f"{post_id}",
    fields="likes.summary(true),comments.summary(true),shares"
)

# Create Instagram Business post (via Facebook Page)
ig_user = graph.get_object(f"{page_id}?fields=instagram_business_account")
ig_post = graph.put_object(
    parent_object=ig_user['instagram_business_account']['id'],
    connection_name="media",
    image_url="https://example.com/image.jpg",
    caption="New product launch!"
)
```

**Rate Limits**:
- Standard limit: 200 calls/hour/user
- Business accounts: May have higher limits (check app settings)
- Implement rate limit handling:
```python
graph = GraphAPI(
    access_token=token,
    sleep_on_rate_limit=True,
    sleep_on_rate_limit_mapping={
        200: 3600,  # Sleep 1 hour if 200 calls/hour exceeded
        100: 600    # Sleep 10 minutes if 100 calls/hour exceeded
    }
)
```

**Error Handling**:
- Error code 190: Invalid/expired token → Refresh token
- Error code 100: Invalid parameter → Log and create notification
- Error code 368: Temporarily blocked → Exponential backoff

### Alternatives Considered

**Alternative 1: Direct Graph API with `requests` library**
- Pro: No external dependency
- Con: Manual OAuth token exchange (complex 3-step process)
- Con: Rate limit management requires custom implementation
- **Rejected**: pyfacebook handles OAuth complexity well

**Alternative 2: Facebook Marketing API SDK**
- Pro: Official Facebook SDK
- Con: Focused on ads, not organic posts
- Con: Overkill for simple posting use case
- **Rejected**: Not designed for organic Pages API

### Implementation Notes

**Gotcha 1**: Facebook Page vs Personal Profile - Graph API only supports posting to Pages, not personal profiles. User must create a Facebook Business Page.

**Gotcha 2**: Instagram Business Account required - Cannot post to personal Instagram accounts via API. Must convert to Business account and link to Facebook Page.

**Gotcha 3**: Long-lived tokens expire after 60 days - Must implement token refresh logic or notify user to regenerate.

**Best Practice**: Always check post success with error handling - Facebook API may return 200 OK but post can still fail due to content policy.

---

## 3. Twitter API v2 Integration

### Decision
Use **tweepy** library (version 4.14+) with OAuth 2.0 PKCE for Twitter API v2 integration.

### Rationale
- Official Twitter-recommended library with 260 code snippets (Context7)
- Native Twitter API v2 support (v1.1 deprecated)
- OAuth 2.0 PKCE flow with `OAuth2UserHandler`
- Built-in rate limit detection (manual sleep required)
- Clean Client interface for all v2 endpoints

### Implementation Details

**Authentication**:
- OAuth 2.0 PKCE (Proof Key for Code Exchange) - more secure than OAuth 1.0a
- No client secret needed (only client ID)
- Scopes: `tweet.read`, `tweet.write`, `users.read`, `offline.access`
- Tokens cached locally, refresh token rotates on each refresh

**Key API Endpoints**:
```python
import tweepy

# Initialize OAuth 2.0 handler
oauth2_handler = tweepy.OAuth2UserHandler(
    client_id=CLIENT_ID,
    redirect_uri="http://localhost:8000/oauth/twitter/callback",
    scope=["tweet.read", "tweet.write", "offline.access"]
)

# Create client
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# Create tweet
response = client.create_tweet(text="New product launch! 🚀 #innovation")
tweet_id = response.data['id']

# Delete tweet
client.delete_tweet(id=tweet_id)

# Get recent tweets (search)
tweets = client.search_recent_tweets(
    query="from:username",
    max_results=10,
    tweet_fields=["created_at", "public_metrics"]
)

# Get tweet analytics
tweet = client.get_tweet(
    id=tweet_id,
    tweet_fields=["public_metrics"]
)
likes = tweet.data['public_metrics']['like_count']
retweets = tweet.data['public_metrics']['retweet_count']
```

**Rate Limits**:
- Tweet creation: 200 tweets/15-min window per user
- Tweet deletion: 50 deletes/15-min window
- Search (recent): 180 requests/15-min window (app auth)
- **Critical**: `search_all_tweets` requires manual 1-second delay between requests

**Error Handling**:
```python
try:
    response = client.create_tweet(text=tweet_text)
except tweepy.TweepyException as e:
    if "429" in str(e):  # Rate limit
        time.sleep(900)  # Wait 15 minutes
        retry()
    elif "401" in str(e):  # Auth error
        refresh_token()
        retry()
    else:
        log_error_and_cache(e)
```

### Alternatives Considered

**Alternative 1: Python-twitter library**
- Pro: Simpler API
- Con: Primarily supports v1.1 API (deprecated)
- Con: Limited v2 support
- **Rejected**: v2 API is required for future compatibility

**Alternative 2: Direct REST API with `requests`**
- Pro: No dependency
- Con: OAuth 2.0 PKCE flow is complex to implement correctly
- Con: Manual rate limit tracking
- **Rejected**: tweepy provides significant value

### Implementation Notes

**Gotcha 1**: Character limit is 280 characters including URLs (URLs count as 23 characters regardless of actual length).

**Gotcha 2**: `search_all_tweets` (archive search) requires Academic Research access or Premium API - use `search_recent_tweets` (last 7 days) for standard accounts.

**Gotcha 3**: Bearer token vs OAuth 2.0 user context - Bearer token is app-only (read-only), user context required for posting tweets.

**Best Practice**: Implement rate limit tracking locally to avoid hitting limits - Twitter returns rate limit info in response headers.

---

## 4. Business Audit Automation

### Decision
Implement **scheduled Python script** (`schedulers/weekly_audit.py`) triggered by cron/Task Scheduler, using AI analysis for insights generation.

### Rationale
- Simplest reliable scheduling (cron is battle-tested)
- Decoupled from AI Processor daemon (separate concerns)
- Template-based report generation ensures consistency
- AI analysis adds value through insights and recommendations
- Aligns with CEO Briefing template from Hackathon_0.md (lines 505-555)

### Implementation Details

**Scheduling**:
```bash
# Linux/Mac cron (runs every Monday 9:00 AM)
0 9 * * 1 cd /path/to/AI_Employee && /usr/bin/python schedulers/weekly_audit.py

# Windows Task Scheduler
- Trigger: Weekly, Monday, 9:00 AM
- Action: python.exe D:\AI_Employee\schedulers\weekly_audit.py
- Settings: Run whether user logged in or not
```

**Data Sources**:
1. **Xero Financial Data**: Revenue, expenses, outstanding invoices (via xero_mcp)
2. **Social Media Metrics**: Posts, engagement, follower growth (via facebook/instagram/twitter_mcp)
3. **Action Item Logs**: Processed items, approvals, response times (from `/Logs/`)
4. **Business Goals**: Progress tracking (from `Business_Goals.md`)
5. **Done Folder**: Completed tasks for the week (from `/Done/`)

**Audit Report Template**:
```markdown
---
type: business_audit
period: 2026-W02
generated: 2026-01-12T09:00:00Z
---

# Weekly Business & Accounting Audit

## Financial Summary (from Xero)
- Revenue: $3,450 (up 12% from last week)
- Expenses: $1,200 (down 5% from last week)
- Net Profit: $2,250
- Outstanding Invoices: 3 ($5,600 total, avg 12 days overdue)
- Cash Flow Status: ✅ Healthy

## Social Media Performance
### Facebook
- Posts: 4 (target: 5)
- Engagement: 234 (likes + comments + shares)
- Reach: 1,850
- Follower Growth: +15

### Instagram
- Posts: 5 (target: 5)
- Engagement: 412
- Reach: 2,100
- Follower Growth: +23

### Twitter
- Tweets: 8 (target: 10)
- Engagement: 156
- Impressions: 3,200
- Follower Growth: +8

## Action Item Summary
- Total Processed: 42
- Approvals Granted: 18
- Approvals Rejected: 2
- Average Response Time: 45 minutes
- Automation Rate: 73%

## Alerts & Recommendations

### ⚠️ Alerts
1. Invoice #INV-1023 overdue by 28 days ($1,200) - follow up with customer
2. Facebook post engagement down 15% this week - review content strategy
3. Xero subscription renewal due in 7 days ($39/month)

### 💡 AI-Generated Recommendations
1. **Cost Optimization**: Office supplies expense increased 40% - consider bulk ordering for better rates
2. **Revenue Growth**: Twitter engagement is strong - consider cross-promoting products there
3. **Operational Efficiency**: 73% automation rate is below Gold tier target (80%) - review manual interventions

## Business Goals Progress
- Goal: Reach $10k MRR - Current: $7.5k (75% progress, on track for Q1)
- Goal: 1,000 Twitter followers - Current: 856 (86% progress, ahead of schedule)
```

**CEO Briefing Template** (generated at 10:00 AM after audit):
```markdown
---
type: ceo_briefing
period: 2026-W02
generated: 2026-01-12T10:00:00Z
---

# CEO Briefing: Week of January 6-12, 2026

## Executive Summary

Strong week with 12% revenue growth driven by 3 new client projects. Social media engagement remains healthy with Instagram leading at +23 followers. One critical alert: Invoice #INV-1023 overdue 28 days requires immediate attention. Overall system performance is solid with 73% automation rate, though below our 80% Gold tier target.

## Financial Highlights
- **Revenue**: $3,450 (+12% WoW)
- **Net Profit**: $2,250 (healthy 65% margin)
- **Cash Flow**: Healthy, but watch overdue invoices
- **Critical**: $1,200 invoice overdue 28 days

## Business Development
- **Social Media Growth**: +46 followers across platforms
- **Instagram Leading**: Strongest engagement (412 interactions)
- **Twitter Opportunity**: High engagement suggests expansion potential

## Operational Efficiency
- **Automation**: 73% (target: 80%)
- **Response Time**: 45 min average (excellent)
- **Action Items**: 42 processed, 95% approval rate

## Action Items for CEO

1. **URGENT**: Follow up on Invoice #INV-1023 (28 days overdue, $1,200)
2. **This Week**: Review Facebook content strategy (engagement down 15%)
3. **This Week**: Renew Xero subscription (due in 7 days)
4. **Strategic**: Investigate Twitter product promotion (high engagement)

## Upcoming Priorities
- Improve automation rate to 80% (identify manual intervention bottlenecks)
- Cross-promote products on Twitter (capitalize on engagement)
- Bulk ordering strategy for office supplies (cost optimization)
```

**AI Analysis Integration**:
```python
import anthropic

# Generate insights from aggregated data
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

prompt = f"""
Analyze this business week data and generate:
1. Top 3 alerts/concerns
2. Top 3 recommendations for improvement
3. Executive summary (2 paragraphs)

Data:
- Revenue: {revenue} (prior week: {prior_revenue})
- Expenses: {expenses} (prior week: {prior_expenses})
- Social media: {social_media_data}
- Action items: {action_summary}
- Goals progress: {goals_data}
"""

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1000,
    messages=[{"role": "user", "content": prompt}]
)

insights = response.content[0].text
```

### Alternatives Considered

**Alternative 1: Continuous monitoring with alerts**
- Pro: Real-time issue detection
- Con: Requires additional daemon process, more complex
- Con: Alert fatigue risk
- **Rejected**: Weekly cadence sufficient for CEO-level oversight

**Alternative 2: Manual data aggregation**
- Pro: No automation complexity
- Con: Defeats purpose of AI Employee
- Con: Time-consuming for CEO
- **Rejected**: Automation is core Gold tier value

### Implementation Notes

**Gotcha 1**: Cron environment variables differ from user session - must use absolute paths or set PATH/PYTHONPATH in crontab.

**Gotcha 2**: Windows Task Scheduler requires "Run whether user logged in or not" to work reliably - without this, task won't run if user logged out.

**Gotcha 3**: ISO week numbers (YYYY-WW format) can be confusing at year boundaries - use `datetime.date.isocalendar()` for accurate week calculation.

**Best Practice**: Generate partial report if data sources unavailable - mark missing sections with `[DATA UNAVAILABLE: source_name]` and include in CEO alerts.

---

## 5. Cross-Domain Data Integration

### Decision
Implement **domain classification via rule-based tagging** with rules defined in `Company_Handbook.md`, using unified data models with domain field.

### Rationale
- Explicit rule definition provides transparency and user control
- Simpler than ML-based classification (no training data needed)
- Rules can be tested and validated before deployment
- Aligns with existing `Company_Handbook.md` configuration pattern
- Achieves 90%+ accuracy with well-defined rules

### Implementation Details

**Domain Classification Rules** (in `Company_Handbook.md`):
```markdown
## Cross-Domain Classification Rules

### Personal Domain Indicators
- Source: personal Gmail, personal WhatsApp, personal LinkedIn
- Keywords: "personal", "family", "home", "private"
- Accounts: personal bank accounts, personal credit cards

### Business Domain Indicators
- Source: business Gmail, business LinkedIn, Xero
- Keywords: "invoice", "client", "customer", "revenue", "expense", "business", "company"
- Accounts: business bank accounts, Xero transactions
- Platforms: Facebook Business Page, Instagram Business, Twitter Business account

### Cross-Domain Workflows
- Personal expense classified as business: "home office", "business expense"
- Business inquiry via personal channel: LinkedIn message about business services
```

**Classification Logic**:
```python
class CrossDomainRouter:
    def __init__(self, handbook_path: Path):
        self.rules = self.load_rules(handbook_path)

    def classify_action_item(self, action_item: ActionItem) -> str:
        """Classify action item as personal, business, or cross-domain."""

        # Check source
        if action_item.source in self.rules['personal_sources']:
            domain = 'personal'
        elif action_item.source in self.rules['business_sources']:
            domain = 'business'
        else:
            domain = 'unknown'

        # Check keywords
        content_lower = action_item.content.lower()
        business_keywords = sum(1 for kw in self.rules['business_keywords'] if kw in content_lower)
        personal_keywords = sum(1 for kw in self.rules['personal_keywords'] if kw in content_lower)

        if business_keywords > personal_keywords and domain != 'personal':
            domain = 'business'
        elif personal_keywords > business_keywords and domain != 'business':
            domain = 'personal'

        # Check for cross-domain indicators
        has_personal_source = action_item.source in self.rules['personal_sources']
        has_business_keywords = business_keywords > 0
        if has_personal_source and has_business_keywords:
            domain = 'cross-domain'

        return domain

    def route_action_item(self, action_item: ActionItem, domain: str):
        """Route action item to appropriate folder based on domain."""
        if domain == 'business':
            target_folder = self.vault_path / 'Business'
        else:
            target_folder = self.vault_path / 'Needs_Action'

        # Update action item metadata
        action_item.domain = domain
        action_item.save()
```

**Unified Dashboard Structure**:
```markdown
# AI Employee Dashboard

**Last Updated**: 2026-01-12 14:30:00
**System Status**: ✅ Operational

---

## Personal Domain

### Personal Activity (Last 7 Days)
- Emails Processed: 24
- WhatsApp Messages: 15
- LinkedIn Messages: 3
- Tasks Completed: 12

### Personal MCP Server Health
- Email Server: ✅ Healthy (last call: 2 min ago)
- LinkedIn Server: ✅ Healthy (last call: 15 min ago)

---

## Business Domain

### Business Activity (Last 7 Days)
- Xero Transactions: 8 (5 expenses, 3 invoices)
- Social Media Posts: 12 (4 FB, 5 IG, 3 Twitter)
- Business Tasks: 7

### Business MCP Server Health
- Xero Server: ✅ Healthy (last call: 5 min ago, rate limit: 45/60)
- Facebook Server: ⚠️ Degraded (last error: 1 hour ago, retry pending)
- Instagram Server: ✅ Healthy (last call: 30 min ago)
- Twitter Server: ✅ Healthy (last call: 45 min ago, rate limit: 150/200)

---

## Cross-Domain KPIs

- **Total Automation Rate**: 73% (target: 80%)
- **Unified Response Time**: 45 min average
- **Cross-Domain Workflows Executed**: 5 this week
- **AI Processor Uptime**: 99.2% (last restart: 3 days ago)

---

## System Health

- **AI Processor**: ✅ Running (PID: 12345, uptime: 72h)
- **Watchers**: ✅ All running (Gmail, WhatsApp, LinkedIn)
- **Scheduler**: ✅ Active (next audit: Monday 9:00 AM)
- **Vault Status**: ✅ Healthy (last backup: 12 hours ago)
```

### Alternatives Considered

**Alternative 1: Machine learning classification**
- Pro: Can learn from user corrections
- Con: Requires training data, model maintenance
- Con: Less transparent (black box)
- **Rejected**: Over-engineered for 90% accuracy requirement

**Alternative 2: Separate systems for personal/business**
- Pro: Complete isolation, simpler per-domain logic
- Con: Defeats Gold tier cross-domain integration goal
- Con: No unified observability
- **Rejected**: Core Gold tier value is unification

### Implementation Notes

**Gotcha 1**: Keyword-based classification can misfire on similar terms - "home office expense" could be personal or business. Require multiple keyword matches or explicit user correction.

**Gotcha 2**: Source-based routing assumes sources are correctly configured - if user uses business Gmail for personal emails, classification fails. Document source setup clearly in quickstart.

**Gotcha 3**: Cross-domain workflows require explicit approval - don't automatically execute cross-domain actions without user review.

**Best Practice**: Log all classification decisions to `/Logs/domain_classification.json` for debugging and rule refinement.

---

## 6. Error Recovery Strategies

### Decision
Implement **exponential backoff with request caching** for API failures, **process manager auto-restart** for crashes, and **graceful degradation** with domain isolation.

### Rationale
- Exponential backoff is industry standard for API retry (prevents thundering herd)
- Request caching ensures zero data loss during outages
- Process manager (PM2) provides reliable crash recovery
- Domain isolation allows partial operation (personal continues if business fails)
- Aligns with Silver tier error handling patterns (extend, don't replace)

### Implementation Details

**Exponential Backoff Implementation**:
```python
import time
from typing import Callable, Any

class RetryHandler:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with exponential backoff retry."""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    # Final attempt failed - cache request and raise
                    self.cache_failed_request(func, args, kwargs, e)
                    raise

                # Calculate delay: 1s, 2s, 4s
                delay = self.base_delay * (2 ** attempt)
                self.log_retry(func.__name__, attempt + 1, delay, e)
                time.sleep(delay)

    def cache_failed_request(self, func: Callable, args, kwargs, error: Exception):
        """Cache failed request for retry when service restored."""
        cache_entry = {
            "function": func.__name__,
            "args": args,
            "kwargs": kwargs,
            "error": str(error),
            "timestamp": datetime.now().isoformat(),
            "retry_count": self.max_retries
        }

        cache_file = Path("/Logs/failed_requests.json")
        cache_data = json.loads(cache_file.read_text()) if cache_file.exists() else []
        cache_data.append(cache_entry)
        cache_file.write_text(json.dumps(cache_data, indent=2))
```

**Request Cache Processing**:
```python
class FailedRequestProcessor:
    def __init__(self, cache_file: Path):
        self.cache_file = cache_file

    def process_failed_requests(self):
        """Retry all cached failed requests."""
        if not self.cache_file.exists():
            return

        cache_data = json.loads(self.cache_file.read_text())
        successful = []

        for entry in cache_data:
            try:
                # Reconstruct and retry request
                func = self.get_function(entry['function'])
                result = func(*entry['args'], **entry['kwargs'])
                self.log_success(entry, result)
                successful.append(entry)
            except Exception as e:
                self.log_retry_failure(entry, e)

        # Remove successful retries from cache
        remaining = [e for e in cache_data if e not in successful]
        self.cache_file.write_text(json.dumps(remaining, indent=2))
```

**Process Manager Configuration (PM2)**:
```javascript
// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: "ai-processor",
      script: "run_ai_processor.py",
      interpreter: "python",
      autorestart: true,
      max_restarts: 5,
      min_uptime: "10s",
      restart_delay: 4000,
      error_file: "./Logs/pm2-error.log",
      out_file: "./Logs/pm2-out.log",
      env: {
        AI_PROCESSOR_ENABLED: "true",
        PROCESSING_INTERVAL: "30"
      }
    },
    {
      name: "gmail-watcher",
      script: "watchers/gmail_watcher.py",
      interpreter: "python",
      autorestart: true,
      max_restarts: 10,
      min_uptime: "10s"
    },
    {
      name: "whatsapp-watcher",
      script: "watchers/whatsapp_watcher.py",
      interpreter: "python",
      autorestart: true,
      max_restarts: 10,
      min_uptime: "10s"
    }
  ]
};
```

**Graceful Degradation Logic**:
```python
class DomainHealthManager:
    def __init__(self):
        self.domain_health = {
            'personal': 'healthy',
            'business': 'healthy'
        }
        self.mcp_server_health = {}

    def check_domain_health(self, domain: str) -> str:
        """Check overall health of a domain."""
        if domain == 'personal':
            servers = ['email', 'linkedin']
        else:  # business
            servers = ['xero', 'facebook', 'instagram', 'twitter']

        failed_count = sum(
            1 for s in servers
            if self.mcp_server_health.get(s, 'healthy') == 'failed'
        )

        if failed_count == 0:
            return 'healthy'
        elif failed_count < len(servers):
            return 'degraded'
        else:
            return 'failed'

    def can_process_action(self, action_item: ActionItem) -> bool:
        """Determine if action can be processed based on domain health."""
        domain_health = self.check_domain_health(action_item.domain)

        if domain_health == 'failed':
            # Queue action for later
            self.queue_for_retry(action_item)
            return False
        elif domain_health == 'degraded':
            # Process if MCP server for this specific action is healthy
            required_server = action_item.get_required_mcp_server()
            return self.mcp_server_health.get(required_server) == 'healthy'
        else:
            return True
```

**Crash Threshold Detection**:
```python
class CrashMonitor:
    def __init__(self, threshold: int = 5, window: int = 3600):
        self.threshold = threshold  # 5 crashes
        self.window = window  # in 1 hour
        self.crashes = []

    def record_crash(self):
        """Record a crash event."""
        now = time.time()
        self.crashes.append(now)

        # Remove crashes outside window
        self.crashes = [t for t in self.crashes if now - t < self.window]

        if len(self.crashes) >= self.threshold:
            self.disable_auto_restart()
            self.notify_admin()
            return True
        return False

    def disable_auto_restart(self):
        """Disable PM2 auto-restart after threshold exceeded."""
        subprocess.run(["pm2", "stop", "ai-processor", "--no-autorestart"])
        self.create_notification(
            title="AI Processor Crash Threshold Exceeded",
            message=f"System crashed {len(self.crashes)} times in 1 hour. "
                   f"Auto-restart disabled. Manual intervention required.",
            priority="critical"
        )
```

### Alternatives Considered

**Alternative 1: Circuit breaker pattern**
- Pro: Prevents cascading failures
- Con: More complex than needed for single-user system
- Con: Requires threshold tuning
- **Rejected**: Exponential backoff simpler and sufficient

**Alternative 2: No caching, just fail**
- Pro: Simplest implementation
- Con: Data loss during outages
- Con: Poor user experience
- **Rejected**: Zero data loss is core requirement

### Implementation Notes

**Gotcha 1**: Exponential backoff with jitter - Add randomization to prevent synchronized retries across multiple requests (not needed for single-user system but good practice).

**Gotcha 2**: PM2 max_restarts vs crash threshold - PM2 built-in max_restarts is per-process lifetime, our crash threshold is per-hour. Implement custom monitoring.

**Gotcha 3**: Failed request cache can grow indefinitely - Implement cache cleanup for requests older than 7 days.

**Best Practice**: Always log crash reason before restart - Helps identify root causes (memory leak, API changes, network issues).

---

## 7. FastMCP Framework

### Decision
Use **FastMCP** (version 1.0+) for all Gold tier MCP servers with decorator-based tool definitions and built-in middleware.

### Rationale
- Consistent with Silver tier MCP pattern (email, LinkedIn)
- 1749-12289 code snippets, high reputation score 78-79.6 (Context7)
- Decorator-based tools (`@mcp.tool`) with automatic JSON schema generation
- Built-in middleware: ErrorHandling, RateLimiting, Timing, Logging
- OAuth authentication support (required for Xero, social media)
- Production-ready HTTP server mode

### Implementation Details

**Basic FastMCP Server Structure**:
```python
from fastmcp import FastMCP
from fastmcp.middleware import ErrorHandlingMiddleware, LoggingMiddleware

mcp = FastMCP("xero-mcp", version="1.0.0")

# Add middleware
mcp.add_middleware(ErrorHandlingMiddleware())
mcp.add_middleware(LoggingMiddleware(log_file="/Logs/xero_mcp.log"))

@mcp.tool()
def get_invoices(
    status: str = "AUTHORISED",
    from_date: str = None,
    to_date: str = None
) -> list[dict]:
    """
    Retrieve invoices from Xero with optional filtering.

    Args:
        status: Filter by invoice status (DRAFT, SUBMITTED, AUTHORISED, PAID)
        from_date: Retrieve invoices from this date (YYYY-MM-DD)
        to_date: Retrieve invoices up to this date (YYYY-MM-DD)

    Returns:
        List of invoice dictionaries
    """
    # Implementation
    pass

@mcp.tool(requires_approval=True)
def create_expense(
    amount: float,
    date: str,
    description: str,
    category: str,
    receipt_url: str = None
) -> dict:
    """
    Create an expense entry in Xero (requires approval).

    Args:
        amount: Expense amount (must be positive)
        date: Expense date (YYYY-MM-DD)
        description: Expense description (max 500 chars)
        category: Expense category/account code
        receipt_url: Optional receipt attachment URL

    Returns:
        Created expense details with ID
    """
    # Implementation - will trigger approval workflow
    pass

# Run server
if __name__ == "__main__":
    mcp.run(host="127.0.0.1", port=8001)
```

**OAuth Integration**:
```python
from fastmcp.auth import OAuth2Handler

oauth_handler = OAuth2Handler(
    client_id=os.getenv("XERO_CLIENT_ID"),
    client_secret=os.getenv("XERO_CLIENT_SECRET"),
    authorization_url="https://login.xero.com/identity/connect/authorize",
    token_url="https://identity.xero.com/connect/token",
    scopes=["accounting.transactions", "accounting.reports.read"]
)

mcp.add_auth_handler(oauth_handler)
```

### Implementation Notes

**Best Practice**: Use type hints for automatic JSON schema generation - FastMCP introspects function signatures to create MCP tool schemas.

**Best Practice**: Implement health check endpoint - FastMCP supports custom endpoints for monitoring.

---

## Summary of Key Decisions

| Area | Decision | Library/Tool | Rationale |
|------|----------|--------------|-----------|
| Xero Integration | Official xero-python SDK + MCP wrapper | xero-python 2.0+ | OAuth 2.0 complexity handled, official support |
| Facebook/Instagram | pyfacebook library | python-facebook 1.0+ | Single library for both, rate limit handling |
| Twitter | tweepy with OAuth 2.0 PKCE | tweepy 4.14+ | Official recommended, v2 API support |
| Business Audits | Scheduled Python script + AI analysis | cron + Claude API | Simple, reliable, AI-generated insights |
| Cross-Domain | Rule-based classification | Custom router + Company_Handbook.md | Transparent, testable, user-controllable |
| Error Recovery | Exponential backoff + request caching | Custom RetryHandler + PM2 | Zero data loss, automatic recovery |
| MCP Framework | FastMCP with decorators | fastmcp 1.0+ | Consistent with Silver, production-ready |

## Next Phase

With technical research complete, proceed to Phase 1 design artifacts:
- **data-model.md**: Entity definitions for Gold tier
- **contracts/**: MCP server contracts (JSON schemas)
- **quickstart.md**: Setup guide for Gold tier
- **plan.md**: Complete architecture plan
