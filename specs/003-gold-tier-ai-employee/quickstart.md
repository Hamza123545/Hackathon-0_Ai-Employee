# Quickstart Guide: Gold Tier AI Employee

**Feature**: Gold Tier Personal AI Employee
**Version**: 1.0.0
**Date**: 2026-01-12
**Estimated Setup Time**: 3-4 hours

---

## Overview

This guide walks you through setting up the Gold Tier AI Employee system from scratch. Gold tier extends Silver tier with:
- Autonomous AI processing (no manual skill invocation)
- Xero accounting integration
- Facebook, Instagram, and Twitter automation
- Weekly business audits with CEO briefings
- Cross-domain workflow integration

**Prerequisites**: Bronze and Silver tiers must be fully operational before starting Gold tier setup.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Xero Integration](#xero-integration)
4. [Facebook Integration](#facebook-integration)
5. [Instagram Integration](#instagram-integration)
6. [Twitter Integration](#twitter-integration)
7. [Autonomous Processor Setup](#autonomous-processor-setup)
8. [Weekly Scheduler Setup](#weekly-scheduler-setup)
9. [Testing the System](#testing-the-system)
10. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

### Required Systems (Bronze + Silver Tier)
- ✅ Obsidian vault at `~/AI_Employee/` with Bronze tier structure
- ✅ Silver tier watchers operational (Gmail, WhatsApp, LinkedIn, filesystem)
- ✅ Silver tier MCP servers installed (Gmail, WhatsApp, LinkedIn, browser)
- ✅ Silver tier Agent Skills functional (`@process-action-items`, `@execute-approved-actions`)
- ✅ Python 3.10+ with virtual environment
- ✅ Claude API key configured in `.env`

### New Requirements (Gold Tier)
- Xero account with API access enabled
- Facebook Page with admin access
- Instagram Business Account linked to Facebook Page
- Twitter/X Developer Account with API access

### API Access Verification

Run this verification script:
```bash
python scripts/verify_gold_prerequisites.py
```

Expected output:
```
✅ Bronze tier operational
✅ Silver tier operational
✅ Claude API key valid
⚠️  Xero API not configured (expected)
⚠️  Facebook API not configured (expected)
⚠️  Instagram API not configured (expected)
⚠️  Twitter API not configured (expected)
```

---

## 2. Environment Setup

### Step 2.1: Update Dependencies

Add Gold tier dependencies to `requirements.txt`:
```bash
# Existing Bronze/Silver dependencies
fastmcp==1.0.0
pydantic==2.5.0
watchdog==3.0.0
requests==2.31.0
playwright==1.40.0

# Gold Tier: Xero integration
xero-python==2.6.0
oauthlib==3.2.2
requests-oauthlib==1.3.1

# Gold Tier: Facebook/Instagram integration
python-facebook==2.2.0  # pyfacebook

# Gold Tier: Twitter integration
tweepy==4.14.0

# Gold Tier: Scheduling
schedule==1.2.0
```

Install dependencies:
```bash
cd ~/AI_Employee
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2.2: Create Gold Tier Directory Structure

```bash
# Create new Gold tier directories
mkdir -p ~/AI_Employee/Business
mkdir -p ~/AI_Employee/Business/Goals
mkdir -p ~/AI_Employee/Business/Social_Media/facebook
mkdir -p ~/AI_Employee/Business/Social_Media/instagram
mkdir -p ~/AI_Employee/Business/Social_Media/twitter
mkdir -p ~/AI_Employee/Business/Workflows
mkdir -p ~/AI_Employee/Business/Metrics
mkdir -p ~/AI_Employee/Business/Engagement
mkdir -p ~/AI_Employee/Accounting
mkdir -p ~/AI_Employee/Accounting/Transactions
mkdir -p ~/AI_Employee/Accounting/Summaries
mkdir -p ~/AI_Employee/Accounting/Audits
mkdir -p ~/AI_Employee/Briefings
mkdir -p ~/AI_Employee/System/MCP_Status
```

Verify structure:
```bash
tree ~/AI_Employee -L 2
```

Expected output:
```
AI_Employee/
├── Business/
│   ├── Goals/
│   ├── Social_Media/
│   ├── Workflows/
│   ├── Metrics/
│   └── Engagement/
├── Accounting/
│   ├── Transactions/
│   ├── Summaries/
│   └── Audits/
├── Briefings/
├── System/
│   └── MCP_Status/
├── (Bronze tier directories...)
└── (Silver tier directories...)
```

### Step 2.3: Update Environment Variables

Add Gold tier credentials to `.env`:
```bash
# Existing Bronze/Silver variables
CLAUDE_API_KEY=sk-ant-...
GMAIL_CLIENT_ID=...
WHATSAPP_API_KEY=...
LINKEDIN_CLIENT_ID=...

# Gold Tier: Xero
XERO_CLIENT_ID=your-xero-client-id
XERO_CLIENT_SECRET=your-xero-client-secret
XERO_REDIRECT_URI=http://localhost:8080/callback
XERO_TENANT_ID=  # Leave empty, will be populated after OAuth

# Gold Tier: Facebook/Instagram
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret
FACEBOOK_REDIRECT_URI=http://localhost:8080/facebook/callback
FACEBOOK_PAGE_ID=  # Leave empty, will be populated after OAuth
INSTAGRAM_BUSINESS_ID=  # Leave empty, will be populated after OAuth

# Gold Tier: Twitter
TWITTER_CLIENT_ID=your-twitter-client-id
TWITTER_CLIENT_SECRET=your-twitter-client-secret
TWITTER_REDIRECT_URI=http://localhost:8080/twitter/callback

# Gold Tier: Scheduling
AI_PROCESSOR_ENABLED=true
AI_PROCESSOR_INTERVAL_SECONDS=30
WEEKLY_AUDIT_ENABLED=true
WEEKLY_AUDIT_DAY=Monday
WEEKLY_AUDIT_TIME=09:00
CEO_BRIEFING_TIME=10:00
```

---

## 3. Xero Integration

### Step 3.1: Create Xero App

1. Go to [Xero Developer Portal](https://developer.xero.com/app/manage)
2. Click "New app"
3. Configure:
   - **App name**: "AI Employee Gold Tier"
   - **Company or application URL**: `http://localhost:8080`
   - **OAuth 2.0 redirect URI**: `http://localhost:8080/callback`
   - **Scopes**: Select all accounting scopes:
     - `accounting.transactions`
     - `accounting.reports.read`
     - `accounting.contacts`
     - `accounting.settings`
4. Save and copy:
   - Client ID → `XERO_CLIENT_ID` in `.env`
   - Client Secret → `XERO_CLIENT_SECRET` in `.env`

### Step 3.2: Run Xero OAuth Flow

```bash
python mcp_servers/xero_mcp/auth_setup.py
```

This script will:
1. Start local server on port 8080
2. Open browser for Xero authorization
3. Handle OAuth callback
4. Exchange code for access token
5. Retrieve tenant ID
6. Save tokens to OS credential manager
7. Update `.env` with `XERO_TENANT_ID`

Expected output:
```
🔐 Starting Xero OAuth 2.0 authorization...
🌐 Opening browser to: https://login.xero.com/identity/connect/authorize?...
⏳ Waiting for authorization callback...
✅ Authorization code received
🔄 Exchanging code for access token...
✅ Access token obtained (expires in 1800s)
✅ Refresh token obtained (expires in 60 days)
🏢 Retrieving tenant ID...
✅ Tenant ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
💾 Saving credentials to OS credential manager...
✅ Xero integration complete!
```

### Step 3.3: Install Xero MCP Server

```bash
cd mcp_servers/
fastmcp install xero_mcp/server.py --name xero-mcp
```

Verify installation:
```bash
fastmcp list
```

Expected output:
```
Installed MCP Servers:
- xero-mcp (stdio, xero_mcp/server.py)
- gmail-mcp (stdio, gmail_mcp/server.py)
- whatsapp-mcp (stdio, whatsapp_mcp/server.py)
- linkedin-mcp (stdio, linkedin_mcp/server.py)
- browser-mcp (stdio, browser_mcp/server.py)
```

### Step 3.4: Test Xero Connection

```bash
python mcp_servers/xero_mcp/test_connection.py
```

This script tests:
- ✅ OAuth token validation
- ✅ Tenant connection
- ✅ Retrieve invoices (last 10)
- ✅ Retrieve bank transactions (last 10)
- ✅ Generate P&L report (last 30 days)

Expected output:
```
🧪 Testing Xero MCP Server...
✅ OAuth token valid
✅ Connected to tenant: Your Company Name
✅ Retrieved 10 invoices (2 PAID, 8 AUTHORISED)
✅ Retrieved 10 bank transactions
✅ Generated Profit & Loss report:
   Revenue: $12,450.00
   Expenses: $8,920.00
   Net Profit: $3,530.00
✅ All Xero tests passed!
```

---

## 4. Facebook Integration

### Step 4.1: Create Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/apps)
2. Click "Create App"
3. Select "Business" app type
4. Configure:
   - **App name**: "AI Employee Gold Tier"
   - **Contact email**: your-email@example.com
5. Add Products:
   - Add "Facebook Login"
   - Configure settings:
     - **Valid OAuth Redirect URIs**: `http://localhost:8080/facebook/callback`
     - **Client OAuth Login**: ON
     - **Web OAuth Login**: ON
6. Add permissions:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
   - `pages_read_user_content`
7. Save and copy:
   - App ID → `FACEBOOK_APP_ID` in `.env`
   - App Secret → `FACEBOOK_APP_SECRET` in `.env`

### Step 4.2: Run Facebook OAuth Flow

```bash
python mcp_servers/facebook_mcp/auth_setup.py
```

This script will:
1. Start local server on port 8080
2. Open browser for Facebook authorization
3. Prompt to select Facebook Page
4. Exchange code for access token
5. Exchange user token for long-lived page token
6. Save tokens to OS credential manager
7. Update `.env` with `FACEBOOK_PAGE_ID`

Expected output:
```
🔐 Starting Facebook OAuth 2.0 authorization...
🌐 Opening browser to: https://www.facebook.com/dialog/oauth?...
⏳ Waiting for authorization callback...
✅ Authorization code received
🔄 Exchanging code for user access token...
✅ User access token obtained (expires in 5400s)
📄 Retrieving Facebook Pages...
   1. My Business Page (ID: 1234567890)
   2. Personal Page (ID: 0987654321)
Select a page (1-2): 1
🔄 Exchanging user token for page access token...
✅ Page access token obtained (never expires)
💾 Saving credentials to OS credential manager...
✅ Facebook integration complete!
```

### Step 4.3: Install Facebook MCP Server

```bash
cd mcp_servers/
fastmcp install facebook_mcp/server.py --name facebook-mcp
```

### Step 4.4: Test Facebook Connection

```bash
python mcp_servers/facebook_mcp/test_connection.py
```

Expected output:
```
🧪 Testing Facebook MCP Server...
✅ Page access token valid
✅ Connected to page: My Business Page
✅ Retrieved 25 recent posts
✅ Retrieved engagement metrics:
   Total likes: 1,250
   Total comments: 180
   Total shares: 95
   Engagement rate: 4.2%
✅ All Facebook tests passed!
```

---

## 5. Instagram Integration

### Step 5.1: Link Instagram Business Account

**Prerequisites**:
- Instagram account must be a Business or Creator account
- Instagram account must be linked to the same Facebook Page

Steps:
1. Go to Instagram app
2. Settings → Account → Switch to Professional Account
3. Select "Business" account type
4. Link to Facebook Page (select the same page from Step 4)
5. Verify link: Settings → Account → Linked Accounts → Facebook

### Step 5.2: Run Instagram OAuth Flow

```bash
python mcp_servers/instagram_mcp/auth_setup.py
```

This script will:
1. Reuse Facebook page access token (from Step 4)
2. Retrieve Instagram Business Account ID
3. Verify Instagram API access
4. Save credentials to OS credential manager
5. Update `.env` with `INSTAGRAM_BUSINESS_ID`

Expected output:
```
🔐 Setting up Instagram Business API...
✅ Using Facebook page access token from OS credential manager
🔄 Retrieving Instagram Business Account ID...
✅ Instagram Business Account ID: 98765432101234
📸 Verifying Instagram API access...
✅ Retrieved Instagram account info:
   Username: @mybusinessaccount
   Followers: 1,250
✅ Instagram integration complete!
```

### Step 5.3: Install Instagram MCP Server

```bash
cd mcp_servers/
fastmcp install instagram_mcp/server.py --name instagram-mcp
```

### Step 5.4: Test Instagram Connection

```bash
python mcp_servers/instagram_mcp/test_connection.py
```

Expected output:
```
🧪 Testing Instagram MCP Server...
✅ Instagram API access verified
✅ Connected to account: @mybusinessaccount
✅ Retrieved 25 recent media posts
✅ Retrieved insights:
   Impressions (7 days): 5,420
   Reach (7 days): 3,210
   Profile views (7 days): 890
   Engagement rate: 5.8%
✅ All Instagram tests passed!
```

---

## 6. Twitter Integration

### Step 6.1: Create Twitter Developer App

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a Project:
   - **Project name**: "AI Employee Gold Tier"
   - **Use case**: "Making a bot" or "Building tools for personal use"
3. Create an App within the project:
   - **App name**: "AI Employee Bot"
   - **Environment**: Development
4. Configure App Settings:
   - Navigate to "Settings" tab
   - Set **Type of App**: Web App
   - Add **Callback URI**: `http://localhost:8080/twitter/callback`
   - Enable **OAuth 2.0**: ON
   - Set **OAuth 2.0 scopes**:
     - `tweet.read`
     - `tweet.write`
     - `users.read`
     - `offline.access` (for refresh tokens)
5. Save and copy:
   - Client ID → `TWITTER_CLIENT_ID` in `.env`
   - Client Secret → `TWITTER_CLIENT_SECRET` in `.env`

### Step 6.2: Run Twitter OAuth Flow

```bash
python mcp_servers/twitter_mcp/auth_setup.py
```

This script will:
1. Start local server on port 8080
2. Generate PKCE code challenge
3. Open browser for Twitter authorization
4. Handle OAuth callback with PKCE code verifier
5. Exchange code for access token
6. Retrieve user info
7. Save tokens to OS credential manager

Expected output:
```
🔐 Starting Twitter OAuth 2.0 authorization (PKCE)...
🔑 Generated PKCE code challenge
🌐 Opening browser to: https://twitter.com/i/oauth2/authorize?...
⏳ Waiting for authorization callback...
✅ Authorization code received
🔄 Exchanging code for access token (with PKCE)...
✅ Access token obtained (expires in 7200s)
✅ Refresh token obtained (expires in 6 months)
👤 Retrieving user info...
✅ Connected to user: @yourtwitterhandle
💾 Saving credentials to OS credential manager...
✅ Twitter integration complete!
```

### Step 6.3: Install Twitter MCP Server

```bash
cd mcp_servers/
fastmcp install twitter_mcp/server.py --name twitter-mcp
```

### Step 6.4: Test Twitter Connection

```bash
python mcp_servers/twitter_mcp/test_connection.py
```

Expected output:
```
🧪 Testing Twitter MCP Server...
✅ Access token valid
✅ Connected to user: @yourtwitterhandle
✅ Retrieved 25 recent tweets
✅ Retrieved engagement metrics:
   Total retweets: 45
   Total likes: 320
   Total replies: 28
   Total impressions: 8,540
   Engagement rate: 4.6%
✅ All Twitter tests passed!
```

---

## 7. Autonomous Processor Setup

### Step 7.1: Review AI Processor Script

The AI Processor daemon automatically detects and processes action items without manual skill invocation.

**Location**: `~/AI_Employee/ai_process_items.py`

**Key Features**:
- File watcher monitors `/Needs_Action/` for new files
- Automatic invocation of `@process-action-items` Agent Skill
- Priority queue (urgent → high → normal → low)
- Configurable processing interval (default: 30 seconds)
- Crash recovery with PM2 process manager

### Step 7.2: Install PM2 Process Manager

```bash
# Install Node.js (if not already installed)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 globally
npm install -g pm2
```

Verify installation:
```bash
pm2 --version
```

### Step 7.3: Configure AI Processor

Edit `~/AI_Employee/ecosystem.config.js`:
```javascript
module.exports = {
  apps: [
    {
      name: 'ai-processor',
      script: './venv/bin/python',
      args: 'ai_process_items.py',
      cwd: '/home/user/AI_Employee',
      interpreter: 'none',
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,
      env: {
        AI_PROCESSOR_ENABLED: 'true',
        AI_PROCESSOR_INTERVAL_SECONDS: '30',
        CLAUDE_API_KEY: process.env.CLAUDE_API_KEY
      },
      error_file: './Logs/ai-processor-error.log',
      out_file: './Logs/ai-processor-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true
    }
  ]
};
```

### Step 7.4: Start AI Processor Daemon

```bash
cd ~/AI_Employee
pm2 start ecosystem.config.js
```

Verify startup:
```bash
pm2 list
```

Expected output:
```
┌─────┬──────────────┬─────────┬─────────┬─────────┬──────────┐
│ id  │ name         │ mode    │ status  │ ↺       │ cpu      │
├─────┼──────────────┼─────────┼─────────┼─────────┼──────────┤
│ 0   │ ai-processor │ fork    │ online  │ 0       │ 2%       │
└─────┴──────────────┴─────────┴─────────┴─────────┴──────────┘
```

View logs:
```bash
pm2 logs ai-processor --lines 50
```

Expected logs:
```
[2026-01-12 10:30:00] AI Processor daemon starting...
[2026-01-12 10:30:00] Watching /Needs_Action/ for new files
[2026-01-12 10:30:00] Processing interval: 30 seconds
[2026-01-12 10:30:00] AI Processor daemon ready
```

### Step 7.5: Test Autonomous Processing

Create a test action item:
```bash
cat > ~/AI_Employee/Needs_Action/test-autonomous-processing.md <<EOF
---
id: test-001
timestamp: 2026-01-12T10:30:00Z
source: manual
priority: high
category: testing
---

# Test Autonomous Processing

**Action Required**: Test that AI Processor automatically detects and processes this action item.

**Expected Behavior**:
1. AI Processor detects file within 30 seconds
2. Invokes @process-action-items skill
3. Creates Plan.md in /Plans/ folder
4. Updates Dashboard.md
5. Archives this file to /Done/
EOF
```

Wait 30 seconds and check logs:
```bash
pm2 logs ai-processor --lines 20
```

Expected logs:
```
[2026-01-12 10:30:30] New action item detected: test-autonomous-processing.md
[2026-01-12 10:30:30] Priority: high
[2026-01-12 10:30:30] Invoking @process-action-items skill...
[2026-01-12 10:30:35] Plan created: /Plans/test-001-plan.md
[2026-01-12 10:30:35] Dashboard updated
[2026-01-12 10:30:35] Action item archived to /Done/
[2026-01-12 10:30:35] Processing completed in 5.2s
```

Verify Plan.md was created:
```bash
cat ~/AI_Employee/Plans/test-001-plan.md
```

### Step 7.6: Configure Startup on Boot

```bash
pm2 startup
```

Follow the printed instructions (paste the generated command).

Save current process list:
```bash
pm2 save
```

---

## 8. Weekly Scheduler Setup

### Step 8.1: Review Scheduler Script

**Location**: `~/AI_Employee/run_weekly_audit.py`

**Key Features**:
- Scheduled execution every Monday at 9:00 AM (Audit Report)
- Scheduled execution every Monday at 10:00 AM (CEO Briefing)
- Aggregates Xero data, social media metrics, action logs
- AI-generated insights using Claude API
- Generates markdown reports in `/Briefings/` and `/Accounting/Audits/`

### Step 8.2: Test Weekly Audit (Manual)

```bash
cd ~/AI_Employee
python run_weekly_audit.py --mode audit --manual
```

Expected output:
```
📊 Generating Weekly Audit Report...
🔄 Retrieving Xero financial data (last 7 days)...
   Revenue: $2,450.00
   Expenses: $1,320.00
   Net Profit: $1,130.00
🔄 Retrieving Facebook engagement metrics...
   Posts: 5
   Total engagement: 320 (likes: 180, comments: 95, shares: 45)
🔄 Retrieving Instagram engagement metrics...
   Posts: 8
   Total engagement: 580 (likes: 420, comments: 120, saved: 40)
🔄 Retrieving Twitter engagement metrics...
   Tweets: 12
   Total engagement: 450 (likes: 280, retweets: 85, replies: 85)
🔄 Analyzing action logs...
   Total actions: 23 (personal: 15, business: 8)
   Success rate: 95.7%
🤖 Generating AI insights using Claude API...
   Insight 1: Social media engagement up 15% week-over-week
   Insight 2: Operating expenses decreased 8% due to vendor renegotiation
   Insight 3: Instagram posts outperforming Facebook by 2.3x engagement rate
✅ Audit Report saved to: /Accounting/Audits/2026-01-12-audit-report.json
⏱️  Generated in 12.5s
```

### Step 8.3: Test CEO Briefing (Manual)

```bash
python run_weekly_audit.py --mode briefing --manual
```

Expected output:
```
📋 Generating CEO Briefing...
📊 Loading Audit Report: /Accounting/Audits/2026-01-12-audit-report.json
🤖 Generating executive summary using Claude API...
🤖 Generating recommendations using Claude API...
✅ CEO Briefing saved to: /Briefings/2026-01-12-ceo-briefing.md
⏱️  Generated in 8.3s
```

View briefing:
```bash
cat ~/AI_Employee/Briefings/2026-01-12-ceo-briefing.md
```

### Step 8.4: Configure Weekly Scheduler

**Option A: PM2 Cron (Recommended)**

Add to `ecosystem.config.js`:
```javascript
{
  name: 'weekly-audit',
  script: './venv/bin/python',
  args: 'run_weekly_audit.py --mode audit',
  cwd: '/home/user/AI_Employee',
  interpreter: 'none',
  autorestart: false,
  cron_restart: '0 9 * * 1',  // Every Monday at 9:00 AM
  env: {
    CLAUDE_API_KEY: process.env.CLAUDE_API_KEY,
    XERO_CLIENT_ID: process.env.XERO_CLIENT_ID,
    // ... (other env vars)
  }
},
{
  name: 'ceo-briefing',
  script: './venv/bin/python',
  args: 'run_weekly_audit.py --mode briefing',
  cwd: '/home/user/AI_Employee',
  interpreter: 'none',
  autorestart: false,
  cron_restart: '0 10 * * 1',  // Every Monday at 10:00 AM
  env: {
    CLAUDE_API_KEY: process.env.CLAUDE_API_KEY
  }
}
```

Start schedulers:
```bash
pm2 restart ecosystem.config.js
pm2 save
```

**Option B: System Cron (Linux/Mac)**

```bash
crontab -e
```

Add:
```cron
# Weekly Audit Report (Monday 9:00 AM)
0 9 * * 1 cd /home/user/AI_Employee && ./venv/bin/python run_weekly_audit.py --mode audit >> Logs/cron-audit.log 2>&1

# CEO Briefing (Monday 10:00 AM)
0 10 * * 1 cd /home/user/AI_Employee && ./venv/bin/python run_weekly_audit.py --mode briefing >> Logs/cron-briefing.log 2>&1
```

**Option C: Windows Task Scheduler**

1. Open Task Scheduler
2. Create Task: "Weekly Audit"
   - Trigger: Weekly, Monday, 9:00 AM
   - Action: Start program
     - Program: `C:\Users\YourName\AI_Employee\venv\Scripts\python.exe`
     - Arguments: `run_weekly_audit.py --mode audit`
     - Start in: `C:\Users\YourName\AI_Employee`
3. Create Task: "CEO Briefing"
   - Trigger: Weekly, Monday, 10:00 AM
   - Action: Start program (same as above, but `--mode briefing`)

---

## 9. Testing the System

### Step 9.1: End-to-End Test: Email Invoice Workflow

This test verifies cross-domain integration (Personal → Business).

**Scenario**: Receive email request to create invoice, process autonomously, create Xero invoice.

1. **Send test email** to your Gmail:
   - Subject: "Please create invoice for John Doe"
   - Body: "Create invoice for John Doe for consulting services. Amount: $1,500. Due date: 2026-01-30."

2. **Wait for Gmail watcher** to detect email (within 5 minutes)

3. **Verify autonomous processing**:
   ```bash
   pm2 logs ai-processor --lines 50
   ```

   Expected logs:
   ```
   [10:35:00] New action item detected: gmail-invoice-request.md
   [10:35:00] Invoking @process-action-items skill...
   [10:35:05] Plan created: invoice-john-doe-plan.md
   [10:35:05] Cross-domain workflow detected: personal + accounting
   [10:35:05] Creating approval request...
   [10:35:05] Approval request created: pending_approval/xero-create-invoice.json
   ```

4. **Approve the invoice**:
   ```bash
   mv ~/AI_Employee/Pending_Approval/xero-create-invoice.json ~/AI_Employee/Approved/
   ```

5. **Verify execution**:
   ```bash
   pm2 logs ai-processor --lines 50
   ```

   Expected logs:
   ```
   [10:36:00] Approved action detected: xero-create-invoice.json
   [10:36:00] Invoking @execute-approved-actions skill...
   [10:36:05] Executing Xero MCP: create_invoice
   [10:36:08] Xero invoice created: INV-2026-001
   [10:36:08] Audit log entry created
   [10:36:08] Cross-domain workflow completed
   ```

6. **Verify in Xero**:
   - Log in to Xero
   - Navigate to "Business" → "Invoices"
   - Find invoice for "John Doe" with amount $1,500

7. **Verify audit log**:
   ```bash
   tail -50 ~/AI_Employee/Logs/$(date +%Y-%m-%d).json | jq .
   ```

### Step 9.2: End-to-End Test: Social Media Post Workflow

This test verifies multi-platform social media posting.

**Scenario**: Create cross-platform social media post for business announcement.

1. **Create action item**:
   ```bash
   cat > ~/AI_Employee/Needs_Action/social-media-announcement.md <<EOF
   ---
   id: social-001
   timestamp: $(date -Iseconds)
   source: manual
   priority: high
   category: marketing
   ---

   # Social Media Announcement

   **Action Required**: Post business announcement across all social media platforms.

   **Message**: "Excited to announce our new product launch! 🚀 Available now at example.com/product"

   **Platforms**: Facebook, Instagram, Twitter
   EOF
   ```

2. **Wait for autonomous processing** (30 seconds)

3. **Verify approval requests created**:
   ```bash
   ls -l ~/AI_Employee/Pending_Approval/
   ```

   Expected output:
   ```
   facebook-post-announcement.json
   instagram-post-announcement.json
   twitter-post-announcement.json
   ```

4. **Approve all posts**:
   ```bash
   mv ~/AI_Employee/Pending_Approval/*.json ~/AI_Employee/Approved/
   ```

5. **Verify execution** (check logs for each platform)

6. **Verify posts on platforms**:
   - Facebook: Check your Facebook Page
   - Instagram: Check your Instagram Business Account
   - Twitter: Check your Twitter profile

7. **Verify audit log**:
   ```bash
   grep "social-001" ~/AI_Employee/Logs/$(date +%Y-%m-%d).json
   ```

### Step 9.3: Test Weekly Audit Generation

1. **Manually trigger weekly audit**:
   ```bash
   python run_weekly_audit.py --mode audit --manual
   ```

2. **Verify Audit Report created**:
   ```bash
   cat ~/AI_Employee/Accounting/Audits/$(date +%Y-%m-%d)-audit-report.json | jq .
   ```

3. **Verify Financial Summary**:
   ```bash
   jq '.financial_data' ~/AI_Employee/Accounting/Audits/$(date +%Y-%m-%d)-audit-report.json
   ```

4. **Verify Social Media Engagement**:
   ```bash
   jq '.social_media_data' ~/AI_Employee/Accounting/Audits/$(date +%Y-%m-%d)-audit-report.json
   ```

5. **Generate CEO Briefing**:
   ```bash
   python run_weekly_audit.py --mode briefing --manual
   ```

6. **View CEO Briefing**:
   ```bash
   cat ~/AI_Employee/Briefings/$(date +%Y-%m-%d)-ceo-briefing.md
   ```

---

## 10. Troubleshooting

### Issue: Xero OAuth Token Expired

**Symptoms**:
```
Error: Xero API returned 401 Unauthorized
```

**Solution**:
```bash
python mcp_servers/xero_mcp/auth_setup.py --refresh
```

This will use the refresh token to obtain a new access token.

---

### Issue: Facebook Page Access Token Invalid

**Symptoms**:
```
Error: Facebook API returned 190 OAuthException
```

**Solution**:
```bash
python mcp_servers/facebook_mcp/auth_setup.py --reauth
```

This will re-run the OAuth flow to obtain a new page access token.

---

### Issue: AI Processor Crashed

**Symptoms**:
```bash
pm2 list
# ai-processor status: stopped or errored
```

**Solution**:
```bash
# View error logs
pm2 logs ai-processor --err --lines 50

# Restart AI Processor
pm2 restart ai-processor

# If persistent crashes:
pm2 delete ai-processor
pm2 start ecosystem.config.js
```

---

### Issue: Weekly Audit Failed

**Symptoms**:
```
Error: Failed to retrieve Xero financial data
```

**Solutions**:

1. **Check Xero token**:
   ```bash
   python mcp_servers/xero_mcp/test_connection.py
   ```

2. **Check network connectivity**:
   ```bash
   curl -I https://api.xero.com
   ```

3. **Run audit in debug mode**:
   ```bash
   python run_weekly_audit.py --mode audit --manual --debug
   ```

4. **Check rate limits**:
   ```bash
   cat ~/AI_Employee/System/MCP_Status/xero-mcp.json | jq '.rate_limit_status'
   ```

---

### Issue: MCP Server Not Responding

**Symptoms**:
```
Error: MCP server timeout after 30s
```

**Solution**:

1. **Check MCP server health**:
   ```bash
   python scripts/check_mcp_health.py --server xero-mcp
   ```

2. **Restart MCP server**:
   ```bash
   fastmcp restart xero-mcp
   ```

3. **Check system resources**:
   ```bash
   top
   # Ensure CPU < 80%, Memory < 80%
   ```

4. **Enable graceful degradation**:
   - System will continue operating without failed MCP server
   - Check `/System/MCP_Status/<server-name>.json` for status
   - Failed actions queued for retry when server recovers

---

### Issue: Cross-Domain Workflow Stuck

**Symptoms**:
```
Workflow status: active, completion_percentage: 50%
```

**Solution**:

1. **Check workflow status**:
   ```bash
   cat ~/AI_Employee/Business/Workflows/<workflow-id>.json | jq '.steps'
   ```

2. **Identify stuck step**:
   ```bash
   jq '.steps[] | select(.status == "pending")' ~/AI_Employee/Business/Workflows/<workflow-id>.json
   ```

3. **Check approval requests**:
   ```bash
   ls -l ~/AI_Employee/Pending_Approval/
   ```

4. **Manually approve or cancel**:
   ```bash
   # Approve:
   mv ~/AI_Employee/Pending_Approval/<request>.json ~/AI_Employee/Approved/

   # Cancel:
   mv ~/AI_Employee/Pending_Approval/<request>.json ~/AI_Employee/Done/
   ```

---

## Appendix A: Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `CLAUDE_API_KEY` | ✅ | Claude API key for AI processing | `sk-ant-...` |
| `XERO_CLIENT_ID` | ✅ | Xero OAuth client ID | `ABC123...` |
| `XERO_CLIENT_SECRET` | ✅ | Xero OAuth client secret | `XYZ789...` |
| `XERO_REDIRECT_URI` | ✅ | Xero OAuth redirect URI | `http://localhost:8080/callback` |
| `XERO_TENANT_ID` | Auto | Xero tenant ID (populated by auth) | `a1b2c3d4-...` |
| `FACEBOOK_APP_ID` | ✅ | Facebook app ID | `1234567890` |
| `FACEBOOK_APP_SECRET` | ✅ | Facebook app secret | `abc123...` |
| `FACEBOOK_REDIRECT_URI` | ✅ | Facebook OAuth redirect URI | `http://localhost:8080/facebook/callback` |
| `FACEBOOK_PAGE_ID` | Auto | Facebook page ID (populated by auth) | `987654321` |
| `INSTAGRAM_BUSINESS_ID` | Auto | Instagram business ID (populated by auth) | `1234567890` |
| `TWITTER_CLIENT_ID` | ✅ | Twitter OAuth client ID | `XYZ123...` |
| `TWITTER_CLIENT_SECRET` | ✅ | Twitter OAuth client secret | `ABC789...` |
| `TWITTER_REDIRECT_URI` | ✅ | Twitter OAuth redirect URI | `http://localhost:8080/twitter/callback` |
| `AI_PROCESSOR_ENABLED` | ⚙️ | Enable AI Processor daemon | `true` |
| `AI_PROCESSOR_INTERVAL_SECONDS` | ⚙️ | Processing interval in seconds | `30` |
| `WEEKLY_AUDIT_ENABLED` | ⚙️ | Enable weekly audit generation | `true` |
| `WEEKLY_AUDIT_DAY` | ⚙️ | Day for weekly audit | `Monday` |
| `WEEKLY_AUDIT_TIME` | ⚙️ | Time for weekly audit (HH:MM) | `09:00` |
| `CEO_BRIEFING_TIME` | ⚙️ | Time for CEO briefing (HH:MM) | `10:00` |

---

## Appendix B: PM2 Commands Reference

| Command | Description |
|---------|-------------|
| `pm2 start ecosystem.config.js` | Start all processes from config |
| `pm2 stop <name>` | Stop a specific process |
| `pm2 restart <name>` | Restart a specific process |
| `pm2 delete <name>` | Delete a process from PM2 |
| `pm2 list` | List all processes |
| `pm2 logs <name>` | View logs for a process |
| `pm2 logs <name> --err` | View error logs only |
| `pm2 logs <name> --lines 50` | View last 50 log lines |
| `pm2 flush` | Flush all logs |
| `pm2 monit` | Monitor CPU/memory in real-time |
| `pm2 save` | Save current process list |
| `pm2 startup` | Configure PM2 startup on boot |
| `pm2 unstartup` | Remove PM2 startup configuration |
| `pm2 describe <name>` | View detailed process info |

---

## Next Steps

✅ **Gold Tier Setup Complete!**

You now have:
- Autonomous AI processing running 24/7
- Xero accounting integration with 6-hour sync
- Facebook, Instagram, Twitter automation
- Weekly business audits and CEO briefings
- Cross-domain workflow integration
- Comprehensive error recovery and logging

**Recommended Actions**:
1. Monitor AI Processor logs for first 24 hours: `pm2 logs ai-processor`
2. Review first weekly audit on next Monday
3. Verify all MCP server health status: `cat ~/AI_Employee/System/MCP_Status/*.json`
4. Create business goals in `/Business/Goals/` for tracking
5. Review Dashboard daily: `cat ~/AI_Employee/Dashboard.md`

**Further Enhancements** (Out of scope for Gold tier):
- Multi-user support
- Mobile app integration
- Advanced analytics dashboard
- Custom watcher plugins
- External API for third-party integrations

---

**Setup Status**: ✅ Complete
**Gold Tier Operational**: 🚀 Ready
**Support**: See troubleshooting section or check system logs

