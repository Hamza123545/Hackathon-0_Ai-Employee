# Silver Tier Personal AI Employee - Installation Guide

This guide covers the system dependencies and setup steps required for the Silver Tier Personal AI Employee. The setup time is estimated at **90-120 minutes** for first-time installation.

## Prerequisites

- **Operating System**: Windows 10/11, macOS 12+, or Linux (Ubuntu 22.04+)
- **Python**: 3.9 or higher
- **Node.js**: v18 or higher (for PM2 process manager)
- **Git**: For version control
- **Internet Connection**: Required for API access (Gmail, LinkedIn, WhatsApp Web)

## Step 1: System Dependencies

### 1.1 Install Node.js

Node.js is required for the PM2 process manager that runs watchers continuously.

**Windows:**
```powershell
# Download and install from https://nodejs.org/
# Or use Chocolatey:
choco install nodejs
```

**macOS:**
```bash
# Using Homebrew:
brew install node
```

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Verify Installation:**
```bash
node --version  # Should be v18.x or higher
npm --version   # Should be 9.x or higher
```

### 1.2 Install PM2 Process Manager

PM2 manages the continuous operation of watchers with auto-restart and monitoring.

```bash
# Install PM2 globally
npm install -g pm2

# Verify installation
pm2 --version  # Should be 5.x or higher
```

### 1.3 Install Python Dependencies

```bash
# Navigate to the AI_Employee directory
cd AI_Employee

# Install Python packages
pip install -r requirements.txt

# This installs:
# - Bronze tier: watchdog, google-api-python-client, python-dotenv, pyyaml
# - Silver tier: fastmcp, playwright, requests, aiohttp, pydantic
```

### 1.4 Install Playwright Browsers

Playwright requires browser binaries for WhatsApp Web automation.

```bash
# Install Chromium browser for Playwright
playwright install chromium

# Verify installation
playwright --version  # Should be 1.40.x or higher
```

**Note**: This downloads ~300MB of browser binaries. Ensure you have sufficient disk space.

## Step 2: Configuration

### 2.1 Create Environment File

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

### 2.2 Required Configuration

Edit the `.env` file and configure the following:

**Bronze Tier (Required):**
```bash
VAULT_PATH=./AI_Employee
WATCHER_TYPE=gmail
CHECK_INTERVAL=300
GMAIL_CREDENTIALS_PATH=credentials.json
```

**Silver Tier (Required for Silver features):**
```bash
# LinkedIn API
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token_here
LINKEDIN_PERSON_URN=urn:li:person:YOURPERSONID

# WhatsApp Watcher
WHATSAPP_SESSION_FILE=./AI_Employee/whatsapp_session.json

# Email MCP Server (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
FROM_ADDRESS=your_email@gmail.com

# Optional Settings
APPROVAL_CHECK_INTERVAL=60
AUTO_APPROVAL_ENABLED=false
AUDIT_LOG_RETENTION_DAYS=90
```

### 2.3 Obtain API Credentials

**Gmail API:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download credentials as `credentials.json`
6. Place in `AI_Employee/` directory

**LinkedIn API:**
1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Create a new app
3. Request OAuth 2.0 access token with scopes: `r_liteprofile`, `w_member_social`
4. Copy access token to `.env` as `LINKEDIN_ACCESS_TOKEN`
5. Get your Person URN from LinkedIn API and set as `LINKEDIN_PERSON_URN`

**Gmail SMTP (for Email MCP):**
1. Enable 2-Factor Authentication on your Google account
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Use the app password as `SMTP_PASSWORD` in `.env`

## Step 3: Verify Installation

### 3.1 Test Python Dependencies

```bash
# Test Python imports
python -c "import fastmcp, playwright, requests, aiohttp, pydantic; print('All imports successful')"
```

### 3.2 Test PM2

```bash
# Check PM2 status
pm2 list

# Should show empty list initially (no processes running)
```

### 3.3 Test Playwright

```bash
# Test Playwright browser launch
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); print('Browser launched successfully'); b.close(); p.stop()"
```

## Step 4: First Run

### 4.1 Authenticate Gmail Watcher (Bronze Tier)

```bash
# Run Gmail watcher once to authenticate
python watchers/gmail_watcher.py

# Follow the OAuth flow in your browser
# This creates token.json for future authentication
```

### 4.2 Authenticate WhatsApp Watcher (Silver Tier)

```bash
# Run WhatsApp watcher to scan QR code
python watchers/whatsapp_watcher.py

# A browser window will open with WhatsApp Web
# Scan the QR code with your phone's WhatsApp app
# Session will be saved to whatsapp_session.json
# Session expires after 14 days (re-authentication required)
```

### 4.3 Start All Watchers with PM2

```bash
# Start all processes
pm2 start ecosystem.config.js

# View process status
pm2 list

# Monitor logs in real-time
pm2 logs

# View specific watcher logs
pm2 logs gmail-watcher
pm2 logs whatsapp-watcher
pm2 logs linkedin-watcher
pm2 logs approval-orchestrator
```

### 4.4 Enable PM2 Startup on Boot (Optional)

```bash
# Generate startup script
pm2 startup

# Follow the command output to enable auto-start
# Save current process list
pm2 save
```

## Step 5: Verify Silver Tier Operation

### 5.1 Check Watcher Status

```bash
# All watchers should show status: online
pm2 list

# Check logs for errors
pm2 logs --lines 50
```

### 5.2 Verify Folder Structure

```bash
# All Silver tier folders should exist
ls -la AI_Employee/
# Should show: Pending_Approval/, Approved/, Rejected/, Logs/, Logs/screenshots/
```

### 5.3 Test Action Item Detection

1. Send yourself a test email (Gmail watcher)
2. Send a WhatsApp message to your monitored number
3. Wait 5 minutes (default check interval)
4. Check `AI_Employee/Needs_Action/` for new action items

### 5.4 Monitor Dashboard

```bash
# View the Dashboard (if Bronze tier @process-action-items is set up)
cat AI_Employee/Dashboard.md
```

## Troubleshooting

### PM2 Process Not Starting

```bash
# Check PM2 logs for errors
pm2 logs <process-name> --err

# Restart specific process
pm2 restart <process-name>

# Delete and restart
pm2 delete <process-name>
pm2 start ecosystem.config.js --only <process-name>
```

### WhatsApp Session Expired

```bash
# Stop WhatsApp watcher
pm2 stop whatsapp-watcher

# Delete old session
rm AI_Employee/whatsapp_session.json

# Re-authenticate
python watchers/whatsapp_watcher.py

# Restart watcher
pm2 restart whatsapp-watcher
```

### LinkedIn API Rate Limit

```bash
# Check LinkedIn watcher logs
pm2 logs linkedin-watcher

# Increase CHECK_INTERVAL in .env to reduce API calls
# Restart watcher
pm2 restart linkedin-watcher
```

### Playwright Browser Not Found

```bash
# Reinstall Playwright browsers
playwright install chromium --force

# Test browser launch
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); b.close(); p.stop()"
```

## Next Steps

1. **Review Documentation**: Read `quickstart.md` for workflow details
2. **Configure Company Handbook**: Edit `AI_Employee/Company_Handbook.md` with your rules
3. **Test Approval Workflow**: Create a test approval request and move through folders
4. **Monitor Audit Logs**: Check `AI_Employee/Logs/YYYY-MM-DD.json` for execution history
5. **Setup MCP Servers**: Configure email, LinkedIn, and Playwright MCP servers (Phase 2+)

## Maintenance

### Daily Tasks
- Monitor PM2 logs for errors: `pm2 logs`
- Check Dashboard for pending approvals: `cat AI_Employee/Dashboard.md`

### Weekly Tasks
- Review audit logs: `cat AI_Employee/Logs/$(date +%Y-%m-%d).json`
- Check watcher uptime: `pm2 list`

### Monthly Tasks
- Rotate audit logs (older than 90 days)
- Refresh LinkedIn access token (60-day expiry)
- Re-authenticate WhatsApp session if expired (14-day expiry)

## Uninstallation

```bash
# Stop all PM2 processes
pm2 stop all
pm2 delete all

# Remove PM2 startup script
pm2 unstartup

# Uninstall PM2
npm uninstall -g pm2

# Remove Python dependencies
pip uninstall -r requirements.txt -y

# Remove Playwright browsers
playwright uninstall
```

## Support

For issues, refer to:
- **Specification**: `specs/002-silver-tier-ai-employee/spec.md`
- **Quick Start**: `specs/002-silver-tier-ai-employee/quickstart.md`
- **Research**: `specs/002-silver-tier-ai-employee/research.md`
- **Architecture**: `specs/002-silver-tier-ai-employee/plan.md`

## Version Information

- **Feature**: Silver Tier Personal AI Employee
- **Version**: 1.0.0
- **Date**: 2026-01-09
- **Branch**: 002-silver-tier-ai-employee
