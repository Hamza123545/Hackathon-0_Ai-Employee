# Silver Tier Quick Start Guide

**Feature**: Silver Tier Personal AI Employee
**Created**: 2026-01-09
**Estimated Setup Time**: 90-120 minutes

This guide walks you through setting up the Silver Tier Personal AI Employee system from scratch, including MCP servers, multi-watcher configuration, and approval workflow.

---

## Prerequisites

Before starting, ensure you have:

- ✅ **Bronze Tier Installed**: Silver tier extends Bronze. If not installed, complete Bronze setup first.
- ✅ **Python 3.9+**: `python --version` should show 3.9 or higher
- ✅ **Node.js v24+**: `node --version` (required for MCP servers and PM2)
- ✅ **Git**: For version control (optional but recommended)
- ✅ **Obsidian Vault**: Running with Bronze tier vault structure at `AI_Employee/`
- ✅ **Network Access**: For Gmail, LinkedIn, WhatsApp Web, and API calls

---

## Phase 1: MCP Server Setup (30 minutes)

### 1.1 Install MCP Dependencies

```bash
# Install Python MCP SDK (FastMCP)
pip install fastmcp httpx

# Install Node.js dependencies for MCP servers
npm install -g @modelcontextprotocol/sdk
```

### 1.2 Create Email MCP Server

**Location**: `AI_Employee/mcp_servers/email-mcp/`

```bash
# Create directory structure
mkdir -p AI_Employee/mcp_servers/email-mcp
cd AI_Employee/mcp_servers/email-mcp
```

**Create `email_mcp.py`** (implementation based on `contracts/email-mcp.json`):

```python
from mcp.server.fastmcp import FastMCP
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

mcp = FastMCP("Email MCP Server")

# Configuration from environment
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_ADDRESS = os.getenv("FROM_ADDRESS")
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))

@mcp.tool()
def send_email(to: str, subject: str, body: str, from_addr: str = None) -> dict:
    """Send an email via SMTP."""
    try:
        msg = MIMEMultipart()
        msg['From'] = from_addr or FROM_ADDRESS
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        return {
            "status": "sent",
            "message_id": f"<{datetime.now().timestamp()}@{SMTP_HOST}>",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_code": "SMTP_CONNECTION_ERROR" if "connect" in str(e).lower() else "UNKNOWN"
        }

@mcp.tool()
def health_check() -> dict:
    """Check if email server is reachable."""
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)

        return {
            "status": "available",
            "smtp_reachable": True,
            "auth_valid": True,
            "checked_at": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        return {
            "status": "error",
            "smtp_reachable": False,
            "auth_valid": False,
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat() + "Z"
        }

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

**Create `.env` file** for Email MCP:

```bash
# AI_Employee/mcp_servers/email-mcp/.env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
FROM_ADDRESS=your-email@gmail.com
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
```

**⚠️ Gmail Setup**:
1. Enable 2-factor authentication on your Google account
2. Generate an App-Specific Password: https://myaccount.google.com/apppasswords
3. Use the app-specific password (not your regular password) in `.env`

### 1.3 Test Email MCP Server

```bash
cd AI_Employee/mcp_servers/email-mcp
python email_mcp.py
```

Expected output: Server starts and listens on stdio (no errors)

Press `Ctrl+C` to stop.

---

## Phase 2: LinkedIn MCP Setup (20 minutes)

### 2.1 LinkedIn OAuth Setup

1. **Create LinkedIn App**:
   - Go to https://www.linkedin.com/developers/apps
   - Click "Create app"
   - Fill in app details (name, company, logo, privacy policy URL)
   - Submit for approval

2. **Configure OAuth**:
   - Add redirect URL: `http://localhost:8000/callback`
   - Request scopes: `openid`, `profile`, `w_member_social`, `r_basicprofile`

3. **Get Credentials**:
   - Copy Client ID and Client Secret
   - Store in `.env` file

### 2.2 Create LinkedIn MCP Server

**Location**: `AI_Employee/mcp_servers/linkedin-mcp/`

```bash
mkdir -p AI_Employee/mcp_servers/linkedin-mcp
cd AI_Employee/mcp_servers/linkedin-mcp
```

**Create `linkedin_mcp.py`** (simplified version):

```python
from mcp.server.fastmcp import FastMCP
import requests
import os
from datetime import datetime

mcp = FastMCP("LinkedIn MCP Server")

ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
PERSON_URN = os.getenv("LINKEDIN_PERSON_URN")
API_BASE_URL = "https://api.linkedin.com/rest"

@mcp.tool()
def create_post(text: str, visibility: str = "PUBLIC") -> dict:
    """Create a LinkedIn post."""
    try:
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202401"
        }

        payload = {
            "author": PERSON_URN,
            "commentary": text,
            "visibility": visibility,
            "distribution": {"feedDistribution": "MAIN_FEED"},
            "lifecycleState": "PUBLISHED"
        }

        response = requests.post(
            f"{API_BASE_URL}/posts",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 201:
            post_data = response.json()
            post_id = post_data.get("id", "unknown")
            return {
                "status": "published",
                "post_id": post_id,
                "post_url": f"https://www.linkedin.com/feed/update/{post_id}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            return {
                "status": "error",
                "error": response.text,
                "error_code": "INVALID_CONTENT"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_code": "NETWORK_ERROR"
        }

@mcp.tool()
def health_check() -> dict:
    """Check LinkedIn API access."""
    try:
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "LinkedIn-Version": "202401"
        }
        response = requests.get(
            f"{API_BASE_URL}/userinfo",
            headers=headers,
            timeout=10
        )
        return {
            "status": "available" if response.status_code == 200 else "error",
            "api_reachable": True,
            "token_valid": response.status_code == 200,
            "checked_at": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        return {
            "status": "error",
            "api_reachable": False,
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat() + "Z"
        }

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

**Create `.env` file** for LinkedIn MCP:

```bash
# AI_Employee/mcp_servers/linkedin-mcp/.env
LINKEDIN_ACCESS_TOKEN=YOUR_ACCESS_TOKEN_HERE
LINKEDIN_PERSON_URN=urn:li:person:YOUR_PERSON_ID_HERE
LINKEDIN_API_BASE_URL=https://api.linkedin.com/rest
```

**Get Access Token**:
1. Use LinkedIn OAuth flow to authenticate (see OAuth setup guide)
2. Store access token in `.env`
3. Token expires after 60 days - monitor and refresh

---

## Phase 3: WhatsApp Watcher Setup (25 minutes)

### 3.1 Install Playwright

```bash
pip install playwright
playwright install chromium
```

### 3.2 Create WhatsApp Watcher

**Location**: `AI_Employee/watchers/whatsapp_watcher.py`

```python
from playwright.sync_api import sync_playwright
import time
import json
import os
from datetime import datetime
from pathlib import Path

VAULT_PATH = os.getenv("VAULT_PATH", "D:/specs/AI_Employee")
SESSION_PATH = os.path.join(VAULT_PATH, "whatsapp_session.json")
MONITORED_CONTACTS = ["John Doe", "Client Company"]  # Configure in Company_Handbook.md

def initialize_whatsapp_session():
    """Initialize WhatsApp session with QR scan."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Must be visible for QR scan
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://web.whatsapp.com")
        print("Please scan the QR code in the browser window...")

        # Wait for successful login (check for chat list)
        page.wait_for_selector('div[data-testid="chat-list"]', timeout=120000)
        print("✅ WhatsApp authenticated!")

        # Save session
        context.storage_state(path=SESSION_PATH)
        browser.close()
        print(f"Session saved to {SESSION_PATH}")

def check_whatsapp_messages():
    """Check for new WhatsApp messages from monitored contacts."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Reuse saved session
        context = browser.new_context(storage_state=SESSION_PATH)
        page = context.new_page()

        page.goto("https://web.whatsapp.com")
        page.wait_for_selector('div[data-testid="chat-list"]', timeout=30000)

        messages = []
        for contact in MONITORED_CONTACTS:
            try:
                # Search for contact
                search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
                search_box.click()
                search_box.fill(contact)
                time.sleep(1)

                # Click first result
                page.click(f'span[title="{contact}"]')
                time.sleep(1)

                # Get unread messages (messages with green background)
                unread = page.locator('div[data-testid="msg-container"]').all()
                for msg in unread[:10]:  # Last 10 messages
                    text = msg.inner_text()
                    messages.append({
                        "from_contact": contact,
                        "message_text": text,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    })
            except Exception as e:
                print(f"Error checking {contact}: {e}")

        browser.close()
        return messages

if __name__ == "__main__":
    # First run: Initialize session
    if not os.path.exists(SESSION_PATH):
        print("No session found. Initializing WhatsApp session...")
        initialize_whatsapp_session()

    # Regular check
    print("Checking WhatsApp messages...")
    messages = check_whatsapp_messages()
    print(f"Found {len(messages)} messages")
    for msg in messages:
        print(f"- {msg['from_contact']}: {msg['message_text'][:50]}...")
```

### 3.3 Initialize WhatsApp Session

```bash
cd AI_Employee/watchers
python whatsapp_watcher.py
```

A browser window will open. Scan the QR code with your phone to authenticate. Session will be saved for future use.

---

## Phase 4: PM2 Process Management (15 minutes)

### 4.1 Install PM2

```bash
npm install -g pm2
```

### 4.2 Create PM2 Ecosystem Configuration

**Location**: `AI_Employee/ecosystem.config.js`

```javascript
module.exports = {
  apps: [
    {
      name: 'gmail-watcher',
      script: 'watchers/gmail_watcher.py',
      interpreter: 'python',
      cwd: 'D:/specs/AI_Employee',
      exec_mode: 'fork',
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,
      env: {
        PYTHONUNBUFFERED: '1',
        VAULT_PATH: 'D:/specs/AI_Employee'
      }
    },
    {
      name: 'whatsapp-watcher',
      script: 'watchers/whatsapp_watcher.py',
      interpreter: 'python',
      cwd: 'D:/specs/AI_Employee',
      exec_mode: 'fork',
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,
      env: {
        PYTHONUNBUFFERED: '1',
        VAULT_PATH: 'D:/specs/AI_Employee'
      }
    },
    {
      name: 'linkedin-watcher',
      script: 'watchers/linkedin_watcher.py',
      interpreter: 'python',
      cwd: 'D:/specs/AI_Employee',
      exec_mode: 'fork',
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,
      env: {
        PYTHONUNBUFFERED: '1',
        VAULT_PATH: 'D:/specs/AI_Employee',
        LINKEDIN_ACCESS_TOKEN: 'YOUR_TOKEN_HERE'
      }
    }
  ]
};
```

### 4.3 Start Watchers with PM2

```bash
cd AI_Employee
pm2 start ecosystem.config.js
```

**Verify watchers are running**:

```bash
pm2 status
```

Expected output:
```
┌─────┬──────────────────────┬─────────┬─────────┬──────────┐
│ id  │ name                 │ status  │ restart │ uptime   │
├─────┼──────────────────────┼─────────┼─────────┼──────────┤
│ 0   │ gmail-watcher        │ online  │ 0       │ 5m       │
│ 1   │ whatsapp-watcher     │ online  │ 0       │ 5m       │
│ 2   │ linkedin-watcher     │ online  │ 0       │ 5m       │
└─────┴──────────────────────┴─────────┴─────────┴──────────┘
```

**PM2 Commands**:
- `pm2 logs` - View all logs
- `pm2 logs gmail-watcher` - View specific watcher logs
- `pm2 restart all` - Restart all watchers
- `pm2 stop all` - Stop all watchers
- `pm2 delete all` - Remove all watchers

---

## Phase 5: Vault Structure Update (10 minutes)

### 5.1 Create Silver Tier Folders

```bash
cd AI_Employee

# Create approval workflow folders
mkdir -p Pending_Approval
mkdir -p Approved
mkdir -p Rejected

# Create audit log folders
mkdir -p Logs
mkdir -p Logs/screenshots

# Verify structure
ls -la
```

Expected structure:
```
AI_Employee/
├── Dashboard.md
├── Company_Handbook.md
├── Needs_Action/
├── Plans/
├── Done/
├── Pending_Approval/      # New (Silver)
├── Approved/              # New (Silver)
├── Rejected/              # New (Silver)
├── Logs/                  # New (Silver)
│   └── screenshots/
├── watchers/
│   ├── gmail_watcher.py
│   ├── whatsapp_watcher.py
│   └── linkedin_watcher.py
├── mcp_servers/
│   ├── email-mcp/
│   └── linkedin-mcp/
└── ecosystem.config.js
```

### 5.2 Update Company_Handbook.md

Add Silver tier configuration section:

```markdown
# Company Handbook

[... existing Bronze tier content ...]

## Silver Tier Configuration

### MCP Servers
- **Email MCP**: Enabled (SMTP: smtp.gmail.com)
- **LinkedIn MCP**: Enabled (API v2)
- **Playwright MCP**: Enabled (WhatsApp automation)

### Approval Workflow
- **Auto-Approval Threshold**: Disabled (all actions require manual approval)
- **Approval Timeout**: 24 hours (flag as overdue, do not auto-reject)

### Watcher Configuration
- **Gmail Watcher**: Check interval 5 minutes
- **WhatsApp Watcher**: Check interval 5 minutes, Monitored contacts: ["John Doe", "Client Company"]
- **LinkedIn Watcher**: Check interval 10 minutes

### LinkedIn Posting Rules
- **Max Posts Per Day**: 3
- **Posting Schedule**: Business hours (9am-5pm)
- **Topics**: AI, Automation, Business Innovation
- **Hashtags**: #AI #Automation #Innovation

### Audit Logging
- **Retention**: 90 days
- **Log Format**: Daily JSON files (YYYY-MM-DD.json)
- **Sanitization**: Enabled (mask credentials, PII)
```

---

## Phase 6: Verification & Testing (15 minutes)

### 6.1 Test Email MCP Server

```bash
# Test health check
cd AI_Employee/mcp_servers/email-mcp
python email_mcp.py

# In another terminal, test send_email tool (use MCP client or manual test)
```

### 6.2 Test Approval Workflow

1. **Trigger action item**:
   - Send yourself a test email
   - Gmail watcher should detect it → creates file in `Needs_Action/`

2. **Process action item**:
   - Run: `@process-action-items` skill in Claude Code
   - Should create plan in `Plans/`
   - If external action needed → creates approval request in `Pending_Approval/`

3. **Approve action**:
   - Review file in `Pending_Approval/`
   - Move file to `Approved/`

4. **Execute action**:
   - Run: `@execute-approved-actions` skill in Claude Code
   - Should execute via MCP server
   - Check `Logs/YYYY-MM-DD.json` for audit entry
   - Approved file moved to `Done/`

### 6.3 Verify Dashboard

Open `AI_Employee/Dashboard.md` and verify it shows:
- ✅ Pending approval count
- ✅ MCP server health status
- ✅ Watcher status (online/stopped) for all three watchers
- ✅ Recent audit entries (last 10)

---

## Troubleshooting

### Email MCP Issues

**Problem**: `SMTP_AUTH_FAILED` error
**Solution**: Use Gmail App-Specific Password (not regular password). Enable 2FA first.

**Problem**: `SMTP_CONNECTION_ERROR`
**Solution**: Check firewall settings. Gmail SMTP port 587 must be accessible.

### LinkedIn MCP Issues

**Problem**: `AUTH_EXPIRED` error
**Solution**: Refresh LinkedIn access token via OAuth flow (tokens expire after 60 days).

**Problem**: `RATE_LIMIT_EXCEEDED`
**Solution**: Reduce posting frequency in `Company_Handbook.md`. LinkedIn recommends max 3 posts/day.

### WhatsApp Watcher Issues

**Problem**: `SESSION_EXPIRED` error
**Solution**: Delete `whatsapp_session.json` and re-run initialization with QR scan.

**Problem**: WhatsApp Web logged out
**Solution**: Check WhatsApp on phone is connected to internet. Session expires after 14 days of inactivity.

### PM2 Issues

**Problem**: Watcher shows "errored" status
**Solution**: Check logs: `pm2 logs watcher-name`. Fix error and restart: `pm2 restart watcher-name`

**Problem**: Watchers not restarting after system reboot
**Solution**: Enable PM2 startup: `pm2 startup` (follow displayed instructions), then `pm2 save`

---

## Next Steps

1. **Test End-to-End Workflow**:
   - Send test email → detect → process → approve → execute → audit log

2. **Configure LinkedIn Posting**:
   - Update `Company_Handbook.md` with posting topics and schedule
   - Test draft generation and approval workflow

3. **Monitor for 24 Hours**:
   - Verify watchers remain online: `pm2 status`
   - Check Dashboard for system health
   - Review audit logs in `Logs/`

4. **Tune Configuration**:
   - Adjust watcher check intervals based on volume
   - Configure auto-approval thresholds (if desired)
   - Set up cron/Task Scheduler for automated cleanup (log retention)

---

## Reference Documents

- **Specification**: `specs/002-silver-tier-ai-employee/spec.md`
- **Architecture**: `specs/002-silver-tier-ai-employee/plan.md` (to be created)
- **Data Model**: `specs/002-silver-tier-ai-employee/data-model.md`
- **MCP Contracts**: `specs/002-silver-tier-ai-employee/contracts/`
- **Bronze Tier Docs**: `specs/001-bronze-ai-employee/`

---

## Support

If you encounter issues:
1. Check PM2 logs: `pm2 logs`
2. Review MCP server logs in respective directories
3. Verify vault structure matches expected layout
4. Consult troubleshooting section above

**Estimated Total Setup Time**: 90-120 minutes (depending on OAuth setup and testing)

**Silver Tier Status**: ✅ Ready for production use after successful testing
