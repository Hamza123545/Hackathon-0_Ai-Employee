# API Credentials Setup Guide

**Personal AI Employee - Complete Credentials Configuration**

This guide explains how to obtain API credentials for all services used in Bronze, Silver, and Gold tiers.

---

## Table of Contents

1. [Gmail (Google)](#1-gmail-google)
2. [LinkedIn](#2-linkedin)
3. [Facebook](#3-facebook)
4. [Instagram](#4-instagram)
5. [Twitter/X](#5-twitterx)
6. [Xero Accounting](#6-xero-accounting)
7. [Claude AI (Anthropic)](#7-claude-ai-anthropic)
8. [Quick Reference](#8-quick-reference)

---

## 1. Gmail (Google)

**Purpose**: Read emails, detect action items, send emails via MCP

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Enter project name: `AI-Employee`
4. Click **Create**

### Step 2: Enable Gmail API

1. Go to **APIs & Services** → **Library**
2. Search for `Gmail API`
3. Click **Gmail API** → **Enable**

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** → Click **Create**
3. Fill in:
   - App name: `AI Employee`
   - User support email: Your email
   - Developer contact: Your email
4. Click **Save and Continue**
5. Add scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.modify`
6. Add your email as a test user
7. Click **Save and Continue**

### Step 4: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: `AI Employee Desktop`
5. Click **Create**
6. **Download JSON** → Save as `credentials.json`

### Step 5: Configure Environment

```env
# Gmail Configuration
GMAIL_CREDENTIALS_PATH=./credentials.json
GMAIL_TOKEN_PATH=./gmail_token.json
GMAIL_WATCHER_INTERVAL=300
```

### Step 6: First-time Authentication

```bash
cd AI_Employee
uv run python watchers/gmail_watcher.py
```
- Browser will open for Google login
- Authorize the app
- Token will be saved automatically

### Gmail OAuth 2.0 Technical Details

**Authorization URL**: `https://accounts.google.com/o/oauth2/v2/auth`
**Token URL**: `https://oauth2.googleapis.com/token`

**Required Scopes**:
- `https://www.googleapis.com/auth/gmail.readonly` - Read emails
- `https://www.googleapis.com/auth/gmail.send` - Send emails
- `https://www.googleapis.com/auth/gmail.modify` - Modify labels

**Python SDK Example**:
```python
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

# First-time authentication
flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json',
    scopes=SCOPES
)
creds = flow.run_local_server(port=0)

# Save credentials for future use
with open('gmail_token.json', 'w') as token:
    token.write(creds.to_json())

# Build Gmail service
service = build('gmail', 'v1', credentials=creds)

# List messages
results = service.users().messages().list(
    userId='me',
    maxResults=10,
    labelIds=['INBOX']
).execute()
```

**Refresh Token Handling**:
```python
from google.auth.transport.requests import Request

# Load existing credentials
if os.path.exists('gmail_token.json'):
    creds = Credentials.from_authorized_user_file('gmail_token.json', SCOPES)

# Refresh if expired
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
    # Save refreshed credentials
    with open('gmail_token.json', 'w') as token:
        token.write(creds.to_json())
```

---

## 2. LinkedIn

**Purpose**: Post updates, read messages, professional networking automation

### Step 1: Create LinkedIn App

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Click **Create App**
3. Fill in:
   - App name: `AI Employee`
   - LinkedIn Page: Select or create a company page
   - App logo: Upload any logo
   - Legal agreement: Check the box
4. Click **Create app**

### Step 2: Request API Access

1. Go to **Products** tab
2. Request access to:
   - **Share on LinkedIn** (for posting)
   - **Sign In with LinkedIn using OpenID Connect**
3. Wait for approval (usually instant for basic access)

### Step 3: Get Credentials

1. Go to **Auth** tab
2. Copy:
   - **Client ID**
   - **Client Secret** (click eye icon to reveal)
3. Add Redirect URL: `http://localhost:8080/linkedin/callback`

### Step 4: Configure Environment

```env
# LinkedIn Configuration
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:8080/linkedin/callback
```

### Alternative: Email/Password Method

For linkedin-api library (simpler but less official):

```bash
# Store credentials in system keyring
keyring set linkedin-mcp email your_linkedin_email@example.com
keyring set linkedin-mcp password your_linkedin_password
```

> **Note**: Use an app-specific password if you have 2FA enabled

### LinkedIn OAuth 2.0 Technical Details

**Authorization URL**: `https://www.linkedin.com/oauth/v2/authorization`
**Token URL**: `https://www.linkedin.com/oauth/v2/accessToken`

**Required Scopes**:
- `openid` - OpenID Connect
- `profile` - Basic profile info
- `email` - Email address
- `w_member_social` - Post on behalf of user

**IMPORTANT**: Redirect URLs must use HTTPS (localhost exceptions for development)

**Python OAuth Flow Example**:
```python
import requests
from urllib.parse import urlencode

# Step 1: Build authorization URL
auth_params = {
    "response_type": "code",
    "client_id": os.environ.get("LINKEDIN_CLIENT_ID"),
    "redirect_uri": "http://localhost:8080/linkedin/callback",
    "scope": "openid profile email w_member_social"
}
auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(auth_params)}"

# Step 2: Exchange code for token (after user authorizes)
token_response = requests.post(
    "https://www.linkedin.com/oauth/v2/accessToken",
    data={
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": "http://localhost:8080/linkedin/callback",
        "client_id": os.environ.get("LINKEDIN_CLIENT_ID"),
        "client_secret": os.environ.get("LINKEDIN_CLIENT_SECRET")
    }
)
access_token = token_response.json()["access_token"]
```

**Using linkedin-api Library** (unofficial but simpler):
```python
from linkedin_api import Linkedin

# Authenticate with email/password
api = Linkedin(
    email=os.environ.get("LINKEDIN_EMAIL"),
    password=os.environ.get("LINKEDIN_PASSWORD")
)

# Get profile
profile = api.get_profile()
print(f"Name: {profile['firstName']} {profile['lastName']}")

# Post update
api.post(text="Hello from AI Employee!")
```

---

## 3. Facebook

**Purpose**: Post to Facebook Pages, read engagement, manage business presence

### Step 1: Create Meta Developer Account

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click **Get Started**
3. Log in with your Facebook account
4. Complete developer registration

### Step 2: Create App

1. Go to [My Apps](https://developers.facebook.com/apps/)
2. Click **Create App**
3. Select **Business** type → Click **Next**
4. Fill in:
   - App name: `AI Employee`
   - Contact email: Your email
5. Click **Create App**

### Step 3: Add Facebook Login Product

1. In your app dashboard, find **Add Products**
2. Click **Set Up** on **Facebook Login**
3. Select **Web**
4. Enter Site URL: `http://localhost:8000`
5. Click **Save**

### Step 4: Configure Permissions

1. Go to **App Review** → **Permissions and Features**
2. Request these permissions:
   - `pages_show_list` - List pages you manage
   - `pages_read_engagement` - Read page engagement
   - `pages_manage_posts` - Create and delete posts
   - `pages_read_user_content` - Read user comments
3. For testing, add yourself as a **Tester** in **Roles**

### Step 5: Get Credentials

1. Go to **Settings** → **Basic**
2. Copy:
   - **App ID**
   - **App Secret** (click Show)

### Step 6: Get Page Access Token

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app
3. Click **Generate Access Token**
4. Select permissions: `pages_show_list`, `pages_manage_posts`
5. Click **Generate Access Token**
6. Copy the token

### Step 7: Get Page ID

1. Go to your Facebook Page
2. Click **About**
3. Scroll down to find **Page ID**
4. Or use Graph API: `GET /me/accounts`

### Step 8: Configure Environment

```env
# Facebook Configuration
FACEBOOK_APP_ID=your_app_id_here
FACEBOOK_APP_SECRET=your_app_secret_here
FACEBOOK_PAGE_ID=your_page_id_here
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_token_here
```

### Step 9: Store Token Securely

```bash
# Run authentication script to store token in keyring
cd AI_Employee
uv run python mcp_servers/facebook_mcp_auth.py
```

### Facebook Graph API Technical Details

**Graph API Base URL**: `https://graph.facebook.com/v18.0`
**Authorization URL**: `https://www.facebook.com/v18.0/dialog/oauth`
**Token URL**: `https://graph.facebook.com/v18.0/oauth/access_token`

**Required Permissions**:
- `pages_show_list` - List pages you manage
- `pages_read_engagement` - Read page engagement metrics
- `pages_manage_posts` - Create and delete page posts
- `pages_read_user_content` - Read user comments on posts

**Python SDK Example**:
```python
from facebook import GraphAPI

# Initialize with access token
graph = GraphAPI(
    access_token=os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN"),
    version="3.1"
)

# Get page info
page = graph.get_object(id=os.environ.get("FACEBOOK_PAGE_ID"))

# Post to page
graph.put_object(
    parent_object=os.environ.get("FACEBOOK_PAGE_ID"),
    connection_name="feed",
    message="Hello from AI Employee!"
)

# Get page posts with engagement
posts = graph.get_connections(
    id=os.environ.get("FACEBOOK_PAGE_ID"),
    connection_name="posts",
    fields="message,created_time,shares,reactions.summary(true)"
)
```

**Long-Lived Token Exchange**:
```python
# Exchange short-lived token for long-lived token (60 days)
import requests

response = requests.get(
    "https://graph.facebook.com/v18.0/oauth/access_token",
    params={
        "grant_type": "fb_exchange_token",
        "client_id": os.environ.get("FACEBOOK_APP_ID"),
        "client_secret": os.environ.get("FACEBOOK_APP_SECRET"),
        "fb_exchange_token": short_lived_token
    }
)
long_lived_token = response.json()["access_token"]
```

---

## 4. Instagram

**Purpose**: Post photos/videos, read insights, manage business Instagram

### Prerequisites

- Instagram account must be a **Business** or **Creator** account
- Instagram must be **linked to a Facebook Page**

### Step 1: Convert to Business Account

1. Open Instagram app
2. Go to **Settings** → **Account**
3. Click **Switch to Professional Account**
4. Select **Business**
5. Connect to your Facebook Page

### Step 2: Link to Facebook Page

1. On Facebook, go to your Page
2. Click **Settings** → **Instagram**
3. Click **Connect Account**
4. Log in to Instagram and authorize

### Step 3: Get Instagram Business Account ID

Using Graph API Explorer:

```
GET /{page-id}?fields=instagram_business_account
```

Or the system will auto-retrieve it from your Facebook Page.

### Step 4: Configure Environment

```env
# Instagram Configuration (uses Facebook credentials)
FACEBOOK_APP_ID=your_app_id_here
FACEBOOK_APP_SECRET=your_app_secret_here
FACEBOOK_PAGE_ID=your_page_id_here
INSTAGRAM_ACCOUNT_ID=your_instagram_business_id_here  # Optional, auto-detected
```

> **Note**: Instagram API uses Facebook authentication. The same Facebook App credentials work for both.

### Instagram Graph API Technical Details

**API Base URL**: `https://graph.facebook.com/v18.0`

**Required Permissions**:
- `instagram_basic` - Basic Instagram access
- `instagram_content_publish` - Publish content to Instagram
- `instagram_manage_insights` - Read Instagram insights

**Get Instagram Business Account ID**:
```python
from facebook import GraphAPI

graph = GraphAPI(access_token=page_access_token)

# Get Instagram account linked to Facebook Page
page_data = graph.get_object(
    id=os.environ.get("FACEBOOK_PAGE_ID"),
    fields="instagram_business_account"
)
instagram_account_id = page_data["instagram_business_account"]["id"]
```

**Post to Instagram (Media Container Workflow)**:
```python
import requests

# Step 1: Create media container
container_response = requests.post(
    f"https://graph.facebook.com/v18.0/{instagram_account_id}/media",
    params={
        "image_url": "https://example.com/image.jpg",  # Must be public URL
        "caption": "Hello from AI Employee!",
        "access_token": access_token
    }
)
creation_id = container_response.json()["id"]

# Step 2: Publish the container
publish_response = requests.post(
    f"https://graph.facebook.com/v18.0/{instagram_account_id}/media_publish",
    params={
        "creation_id": creation_id,
        "access_token": access_token
    }
)
```

**Get Instagram Insights**:
```python
# Get account insights
insights = graph.get_connections(
    id=instagram_account_id,
    connection_name="insights",
    fields="impressions,reach,follower_count",
    period="day"
)
```

---

## 5. Twitter/X

**Purpose**: Post tweets, read timeline, engagement analytics

### Step 1: Apply for Developer Account

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Click **Sign up for Free Account** or **Apply**
3. Fill in:
   - Use case: "Building a personal productivity tool"
   - Description: "Automated posting and engagement tracking"
4. Accept terms and submit

### Step 2: Create Project and App

1. Go to [Developer Portal Dashboard](https://developer.twitter.com/en/portal/dashboard)
2. Click **+ Create Project**
3. Project name: `AI Employee`
4. Use case: Select appropriate option
5. Project description: Brief description
6. Click **Next** → Create App
7. App name: `AI-Employee-App`

### Step 3: Set Up OAuth 2.0

1. In your app, go to **Settings**
2. Click **Set up** under **User authentication settings**
3. Configure:
   - App permissions: **Read and write**
   - Type of App: **Web App, Automated App or Bot**
   - Callback URI: `http://localhost:8000/oauth/twitter/callback`
   - Website URL: `http://localhost:8000`
4. Click **Save**

### Step 4: Get Credentials

1. Go to **Keys and tokens** tab
2. Under **OAuth 2.0 Client ID and Client Secret**:
   - Copy **Client ID**
   - Generate and copy **Client Secret**

### Step 5: Configure Environment

```env
# Twitter Configuration
TWITTER_CLIENT_ID=your_client_id_here
TWITTER_CLIENT_SECRET=your_client_secret_here
TWITTER_REDIRECT_URI=http://localhost:8000/oauth/twitter/callback
TWITTER_BEARER_TOKEN=your_bearer_token_here  # Optional, for read-only access
```

### Step 6: Authenticate

```bash
cd AI_Employee
uv run python mcp_servers/twitter_mcp_auth.py
```
- Browser will open for Twitter authorization
- Approve the app
- Token stored in system keyring

### Twitter OAuth 2.0 PKCE Technical Details

**Authorization URL**: `https://twitter.com/i/oauth2/authorize`
**Token URL**: `https://api.twitter.com/2/oauth2/token`

**Required Scopes**:
- `tweet.read` - Read tweets
- `tweet.write` - Post tweets
- `users.read` - Read user profiles
- `offline.access` - Refresh tokens

**Python Tweepy Example**:
```python
import tweepy

# OAuth 2.0 User Context (with PKCE)
oauth2_user_handler = tweepy.OAuth2UserHandler(
    client_id=os.environ.get("TWITTER_CLIENT_ID"),
    redirect_uri="http://localhost:8000/oauth/twitter/callback",
    scope=["tweet.read", "tweet.write", "users.read", "offline.access"],
    client_secret=os.environ.get("TWITTER_CLIENT_SECRET")
)

# Get authorization URL
auth_url = oauth2_user_handler.get_authorization_url()

# After user authorizes, exchange code for token
access_token = oauth2_user_handler.fetch_token(response_url)

# Create client with user context
client = tweepy.Client(
    consumer_key=os.environ.get("TWITTER_API_KEY"),
    consumer_secret=os.environ.get("TWITTER_API_SECRET"),
    access_token=access_token["access_token"]
)

# Post a tweet
response = client.create_tweet(text="Hello from AI Employee!")
```

**Alternative: Bearer Token (Read-Only)**:
```python
import tweepy

# App-only authentication (read-only)
client = tweepy.Client(bearer_token=os.environ.get("TWITTER_BEARER_TOKEN"))

# Read tweets
tweets = client.get_users_tweets(id=user_id)
```

---

## 6. Xero Accounting

**Purpose**: Create invoices, track expenses, financial reporting

### Step 1: Create Xero Developer Account

1. Go to [Xero Developer Portal](https://developer.xero.com/)
2. Click **Get started** or **Sign up**
3. Create account or log in with existing Xero account

### Step 2: Create App

1. Go to [My Apps](https://developer.xero.com/app/manage)
2. Click **New app**
3. Fill in:
   - App name: `AI Employee`
   - Integration type: **Web app**
   - Company or application URL: `http://localhost:8000`
   - Redirect URI: `http://localhost:8000/oauth/xero/callback`
4. Click **Create app**

### Step 3: Get Credentials

1. In your app, go to **Configuration**
2. Copy:
   - **Client ID**
3. Generate and copy **Client Secret**

### Step 4: Get Tenant ID

After first authentication, you'll need your organization's Tenant ID:

1. Run authentication script (Step 6)
2. Tenant ID will be displayed and stored
3. Or find it in Xero: **Settings** → **General Settings** → Organization details

### Step 5: Configure Environment

```env
# Xero Configuration
XERO_CLIENT_ID=your_client_id_here
XERO_CLIENT_SECRET=your_client_secret_here
XERO_TENANT_ID=your_tenant_id_here
XERO_REDIRECT_URI=http://localhost:8000/oauth/xero/callback
```

### Step 6: Authenticate

```bash
cd AI_Employee
uv run python mcp_servers/xero_mcp_auth.py
```
- Browser opens for Xero login
- Select organization to connect
- Authorize the app
- Tokens stored in system keyring

### Xero OAuth 2.0 Technical Details

**Authorization URL**: `https://login.xero.com/identity/connect/authorize`
**Token URL**: `https://identity.xero.com/connect/token`

**Required Scopes** (space-separated):
```
offline_access openid profile email accounting.transactions accounting.reports.read accounting.settings
```

**Python SDK Example**:
```python
from xero_python.api_client import ApiClient
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token

# Configure API client
api_client = ApiClient(
    Configuration(
        oauth2_token=OAuth2Token(
            client_id=os.environ.get("XERO_CLIENT_ID"),
            client_secret=os.environ.get("XERO_CLIENT_SECRET")
        )
    )
)

# Build authorization URL
authorization_url = api_client.get_authorization_url(
    redirect_uri="http://localhost:8000/oauth/xero/callback",
    scope="offline_access openid profile email accounting.transactions"
)

# Exchange code for token
token = api_client.get_token_set_from_authorization_code(
    code=authorization_code,
    redirect_uri="http://localhost:8000/oauth/xero/callback"
)
```

---

## 7. Claude AI (Anthropic)

**Purpose**: AI-generated insights for CEO briefings and audit reports

### Step 1: Create Anthropic Account

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Click **Sign Up**
3. Verify your email
4. Complete account setup

### Step 2: Get API Key

1. Go to [API Keys](https://console.anthropic.com/settings/keys)
2. Click **Create Key**
3. Name: `AI Employee`
4. Copy the API key (shown only once!)

### Step 3: Add Credits

1. Go to [Billing](https://console.anthropic.com/settings/billing)
2. Add payment method
3. Purchase credits (minimum $5)

### Step 4: Configure Environment

```env
# Claude AI Configuration
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
CLAUDE_MODEL=claude-sonnet-4-20250514
```

### Claude SDK Technical Details

**API Base URL**: `https://api.anthropic.com`

**Available Models** (as of 2025):
- `claude-sonnet-4-20250514` - Best balance of speed and capability
- `claude-opus-4-20250514` - Most capable for complex tasks
- `claude-3-5-haiku-20241022` - Fastest and most cost-effective

**Python SDK Example**:
```python
import os
from anthropic import Anthropic

# Initialize client (uses ANTHROPIC_API_KEY from environment)
client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

# Create a message
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Analyze this week's business metrics..."}
    ]
)

print(message.content[0].text)
```

**Streaming Example**:
```python
# Stream response for real-time output
with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Generate CEO briefing..."}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

**System Prompts for Business Context**:
```python
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2048,
    system="You are a business analyst AI assistant. Analyze data and provide actionable insights.",
    messages=[
        {"role": "user", "content": "Here are this week's metrics: ..."}
    ]
)
```

### Pricing Reference (2025)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Claude 3.5 Haiku | $0.80 | $4.00 |
| Claude Sonnet 4 | $3.00 | $15.00 |
| Claude Opus 4 | $15.00 | $75.00 |

> **Tip**: Use Haiku for cost-effective daily operations, Sonnet for CEO briefings

---

## 8. Quick Reference

### All Environment Variables

Create a `.env` file with all credentials:

```env
# =============================================================================
# BRONZE TIER - Personal Automation
# =============================================================================

# Gmail
GMAIL_CREDENTIALS_PATH=./credentials.json
GMAIL_TOKEN_PATH=./gmail_token.json
GMAIL_WATCHER_INTERVAL=300

# =============================================================================
# SILVER TIER - External Actions
# =============================================================================

# LinkedIn
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8080/linkedin/callback

# =============================================================================
# GOLD TIER - Business Integration
# =============================================================================

# Facebook
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
FACEBOOK_PAGE_ID=your_facebook_page_id

# Instagram (uses Facebook credentials)
INSTAGRAM_ACCOUNT_ID=your_instagram_business_id

# Twitter
TWITTER_CLIENT_ID=your_twitter_client_id
TWITTER_CLIENT_SECRET=your_twitter_client_secret
TWITTER_REDIRECT_URI=http://localhost:8000/oauth/twitter/callback

# Xero
XERO_CLIENT_ID=your_xero_client_id
XERO_CLIENT_SECRET=your_xero_client_secret
XERO_TENANT_ID=your_xero_tenant_id
XERO_REDIRECT_URI=http://localhost:8000/oauth/xero/callback

# Claude AI
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# =============================================================================
# SYSTEM CONFIGURATION
# =============================================================================

# Autonomous Processing
AI_PROCESSOR_ENABLED=true
PROCESSING_INTERVAL=30

# Weekly Audit Schedule
WEEKLY_AUDIT_DAY=1
WEEKLY_AUDIT_HOUR=9
CEO_BRIEFING_HOUR=10
```

### Credential Sources Summary

| Service | Portal URL | Time to Setup |
|---------|-----------|---------------|
| Gmail | [console.cloud.google.com](https://console.cloud.google.com/) | 10-15 min |
| LinkedIn | [linkedin.com/developers](https://www.linkedin.com/developers/) | 5-10 min |
| Facebook | [developers.facebook.com](https://developers.facebook.com/) | 15-20 min |
| Instagram | Uses Facebook | 5 min (after Facebook) |
| Twitter | [developer.twitter.com](https://developer.twitter.com/) | 10-15 min |
| Xero | [developer.xero.com](https://developer.xero.com/) | 10-15 min |
| Claude | [console.anthropic.com](https://console.anthropic.com/) | 5 min |

### Test All Connections

After configuring credentials, test each connection:

```bash
# Test all MCP connections
uv run python AI_Employee/mcp_servers/facebook_mcp_test_connection.py
uv run python AI_Employee/mcp_servers/instagram_mcp_test_connection.py
uv run python AI_Employee/mcp_servers/twitter_mcp_test_connection.py
uv run python AI_Employee/mcp_servers/xero_mcp_test_connection.py
uv run python AI_Employee/mcp_servers/linkedin_mcp_test_connection.py
```

---

## Troubleshooting

### Common Issues

**"Invalid Client ID"**
- Double-check you copied the full Client ID
- Ensure no extra spaces or newlines

**"Redirect URI Mismatch"**
- The redirect URI in your app settings must exactly match `.env`
- Include `http://` or `https://` prefix
- No trailing slash

**"Token Expired"**
- Re-run the authentication script
- Tokens auto-refresh but may need manual re-auth after 90 days

**"Insufficient Permissions"**
- Check app permissions in developer portal
- Some APIs require app review for production

**"Rate Limited"**
- Wait for rate limit window to reset
- Check API documentation for limits

### Security Best Practices

1. **Never commit `.env` to git** - Already in `.gitignore`
2. **Use environment variables** - Don't hardcode secrets
3. **Rotate secrets periodically** - Every 90 days recommended
4. **Use least privilege** - Only request needed permissions
5. **Monitor API usage** - Check dashboards for unusual activity

---

## Next Steps

After setting up all credentials:

1. Copy `.env.example` to `.env`
2. Fill in all credential values
3. Run test connection scripts
4. Start PM2 daemons:
   ```bash
   pm2 start ecosystem.config.js
   pm2 logs
   ```

---

**Document Version**: 1.0.0
**Last Updated**: 2026-01-13
