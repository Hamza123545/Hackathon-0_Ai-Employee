# Silver Tier Personal AI Employee

**Version**: 1.0.0  
**Status**: ✅ Production Ready  
**Requires**: Bronze Tier + Node.js v24+ + PM2

---

## Overview

Silver Tier extends the Bronze Tier Personal AI Employee with external actions, multi-watcher support, human-in-the-loop approval workflows, and comprehensive audit logging. Silver Tier enables your AI employee to execute approved actions via MCP servers (email, LinkedIn, browser automation) while maintaining full control through mandatory approval workflows.

---

## Capabilities Summary

### ✅ Multi-Watcher Monitoring
- **Gmail Watcher**: Monitors Gmail inbox for new emails
- **WhatsApp Watcher**: Monitors WhatsApp Web for messages from configured contacts
- **LinkedIn Watcher**: Monitors LinkedIn notifications and messages
- **Filesystem Watcher**: Monitors folders for new files (Bronze tier)

All watchers run simultaneously via PM2 process manager with automatic restart on crash.

### ✅ Human-in-the-Loop (HITL) Approval
- **Approval Workflow**: All external actions require explicit approval
- **Approval Requests**: Created in `/Pending_Approval/` folder
- **Manual Review**: User reviews and moves to `/Approved/` or `/Rejected/`
- **Auto-Approval**: Optional (disabled by default) for low-risk actions

### ✅ External Actions via MCP Servers
- **Email MCP**: Send emails via SMTP (Gmail, Outlook, custom SMTP)
- **LinkedIn MCP**: Create posts on LinkedIn via API v2
- **Playwright MCP**: Browser automation (WhatsApp, web scraping, form filling)

### ✅ LinkedIn Social Media Automation
- **Posting Rules**: Configurable limits (max 3/day), business hours (9am-5pm)
- **Approved Topics**: AI, Automation, Business Innovation
- **Queue Management**: Posts queued when limits/schedule violated
- **Rate Limit Handling**: Automatic retry after limit reset

### ✅ 24/7 Operation with PM2
- **Process Management**: PM2 manages all watchers and orchestrator
- **Auto-Restart**: Crashed processes restart within 10 seconds
- **OS Startup**: Automatic startup on system boot
- **Uptime**: >99.5% uptime target with automatic recovery

### ✅ Comprehensive Audit Logging
- **Daily Logs**: `/Logs/YYYY-MM-DD.json` (structured JSON)
- **Credential Sanitization**: All passwords, tokens, API keys automatically masked
- **90-Day Retention**: Automatic archiving of old logs
- **Zero Leaks**: Verified zero credential leaks across 100+ entries

### ✅ Enhanced Dashboard
- **Silver Metrics**: Pending approvals, MCP health, watcher status, audit entries
- **Data Freshness**: <5 minutes freshness indicator
- **Error Visualization**: Critical alerts for system issues
- **Quick Actions**: Direct links to common operations

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Personal AI Employee                     │
│                      (Silver Tier)                          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
   │ Gmail   │          │WhatsApp │          │LinkedIn │
   │ Watcher │          │ Watcher │          │ Watcher │
   └────┬────┘          └────┬────┘          └────┬────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  /Needs_Action/    │
                    │  (Action Items)    │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Claude Code       │
                    │  (process-action-  │
                    │   items skill)     │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  /Pending_Approval/│
                    │  (Approval Requests)│
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Human Review      │
                    │  (Manual Approval) │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  /Approved/       │
                    │  (Ready to Execute)│
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  ApprovalOrchestrator│
                    │  (execute-approved-  │
                    │   actions skill)     │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
   │ Email   │          │LinkedIn │          │Playwright│
   │  MCP    │          │   MCP   │          │   MCP   │
   └────┬────┘          └────┬────┘          └────┬────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  /Logs/            │
                    │  (Audit Logs)      │
                    └────────────────────┘
```

---

## Folder Structure

```
AI_Employee/
├── mcp_servers/              # MCP server implementations
│   ├── email_mcp.py          # Email sending via SMTP
│   ├── linkedin_mcp.py       # LinkedIn posting via API v2
│   └── playwright_mcp.py     # Browser automation
├── watchers/                  # Watcher implementations
│   ├── gmail_watcher.py      # Gmail monitoring
│   ├── whatsapp_watcher.py   # WhatsApp Web monitoring
│   ├── linkedin_watcher.py   # LinkedIn monitoring
│   └── filesystem_watcher.py # File monitoring (Bronze)
├── orchestrator.py            # ApprovalOrchestrator (monitors /Approved/)
├── models/                    # Data models
│   ├── approval_request.py   # Approval request model
│   ├── mcp_server.py         # MCP server metadata
│   └── watcher_instance.py   # Watcher runtime state
├── utils/                     # Utilities
│   ├── audit_logger.py       # Audit logging with sanitization
│   ├── sanitizer.py          # Credential sanitization
│   ├── dashboard.py          # Dashboard updates
│   └── linkedin_rules.py     # LinkedIn posting rules
├── Pending_Approval/          # Approval requests awaiting review
├── Approved/                  # Approved actions ready for execution
├── Rejected/                  # Rejected approval requests
├── Done/                      # Completed actions (Bronze + Silver)
├── Logs/                      # Audit logs (daily JSON files)
│   └── screenshots/          # Browser automation screenshots
├── Plans/                     # Action plans (Bronze)
├── Needs_Action/              # Action items (Bronze)
├── Dashboard.md               # System dashboard
├── Company_Handbook.md        # Configuration and rules
├── ecosystem.config.js        # PM2 configuration
├── run_watcher.py             # PM2 entry point for watchers
└── run_orchestrator.py        # PM2 entry point for orchestrator
```

---

## MCP Servers Documentation

### Email MCP (`email-mcp`)

**Purpose**: Send emails via SMTP with TLS encryption

**Tools**:
- `send_email(to, subject, body, attachments?)`: Send email
- `health_check()`: Check SMTP connectivity and authentication

**Configuration** (`.env`):
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
FROM_ADDRESS=your-email@gmail.com
SMTP_USE_TLS=true
```

**Error Codes**:
- `SMTP_AUTH_FAILED`: Invalid credentials → use app-specific password
- `SMTP_CONNECTION_ERROR`: Cannot connect to SMTP server
- `INVALID_RECIPIENT`: Bad email address format
- `ATTACHMENT_TOO_LARGE`: Attachment exceeds 25MB

---

### LinkedIn MCP (`linkedin-mcp`)

**Purpose**: Create LinkedIn posts via API v2

**Tools**:
- `create_post(content, visibility)`: Create LinkedIn post
- `health_check()`: Check API connectivity and token validity

**Configuration** (`.env`):
```env
LINKEDIN_ACCESS_TOKEN=your-oauth-token
LINKEDIN_PERSON_URN=urn:li:person:12345
LINKEDIN_API_VERSION=202601
```

**Error Codes**:
- `AUTH_EXPIRED`: OAuth token expired → refresh token
- `RATE_LIMIT_EXCEEDED`: Too many requests → reduce posting frequency
- `INVALID_CONTENT`: Post content violates LinkedIn policies

---

### Playwright MCP (`playwright-mcp`)

**Purpose**: Browser automation for WhatsApp and web tasks

**Tools**:
- `browser_action(action, url, selector?, value?)`: Navigate, click, type, fill forms
- `take_screenshot(url, selector?)`: Capture browser screenshot
- `health_check()`: Verify Playwright and Chromium installation

**Configuration** (`.env`):
```env
SCREENSHOT_DIR=Logs/screenshots
PLAYWRIGHT_TIMEOUT_MS=30000
```

**Error Codes**:
- `BROWSER_ERROR`: Chromium not installed → run `playwright install chromium`
- `SELECTOR_NOT_FOUND`: Element not found on page
- `TIMEOUT`: Page load timeout exceeded
- `NAVIGATION_ERROR`: Page navigation failed

---

## PM2 Commands Reference

### Starting Processes

```bash
# Start all watchers and orchestrator
pm2 start ecosystem.config.js

# Start specific watcher only
pm2 start ecosystem.config.js --only gmail-watcher

# Start orchestrator only
pm2 start ecosystem.config.js --only approval-orchestrator
```

### Monitoring

```bash
# View status of all processes
pm2 status

# Real-time monitoring dashboard
pm2 monit

# View all logs
pm2 logs

# View logs for specific watcher
pm2 logs gmail-watcher

# View last 100 lines
pm2 logs --lines 100

# View only error logs
pm2 logs --err
```

### Control

```bash
# Restart all processes gracefully
pm2 restart all

# Restart specific watcher
pm2 restart gmail-watcher

# Stop all processes (keeps in PM2 list)
pm2 stop all

# Remove from PM2 list
pm2 delete gmail-watcher

# Reload configuration
pm2 reload ecosystem.config.js
```

### Persistence

```bash
# Save current process list
pm2 save

# Generate startup script for OS
pm2 startup

# Restore saved process list
pm2 resurrect
```

### Information

```bash
# Detailed info about process
pm2 info gmail-watcher

# JSON output (for scripts)
pm2 jlist

# Formatted list with details
pm2 prettylist
```

---

## Troubleshooting Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| `SMTP_AUTH_FAILED` | Use Gmail app-specific password (enable 2FA first) |
| `AUTH_EXPIRED` (LinkedIn) | Refresh OAuth token at LinkedIn Developer Portal |
| `RATE_LIMIT_EXCEEDED` | Reduce posting frequency (max 3/day) |
| `SESSION_EXPIRED` (WhatsApp) | Delete `whatsapp_session.json`, re-scan QR code |
| Watcher "errored" | Check logs: `pm2 logs watcher-name`, fix error, restart |
| PM2 not starting on boot | Run `pm2 startup` and `pm2 save` |
| Crash loop | Check logs, fix root cause, verify dependencies |

**Full troubleshooting guide**: See `specs/002-silver-tier-ai-employee/quickstart.md` → Troubleshooting section

---

## Quick Start

1. **Prerequisites**: Bronze Tier installed, Node.js v24+, Python 3.9+
2. **Follow Setup Guide**: `specs/002-silver-tier-ai-employee/quickstart.md`
3. **Estimated Time**: 90-120 minutes
4. **Verify**: Run verification tests in quickstart guide

---

## Reference Documents

- **Specification**: `specs/002-silver-tier-ai-employee/spec.md`
- **Architecture Plan**: `specs/002-silver-tier-ai-employee/plan.md`
- **Data Model**: `specs/002-silver-tier-ai-employee/data-model.md`
- **Quick Start Guide**: `specs/002-silver-tier-ai-employee/quickstart.md`
- **MCP Contracts**: `specs/002-silver-tier-ai-employee/contracts/`
- **Bronze Tier Docs**: `specs/001-bronze-ai-employee/`

---

## Support

For issues:
1. Check PM2 logs: `pm2 logs`
2. Review troubleshooting section in quickstart guide
3. Verify vault structure matches expected layout
4. Check Dashboard.md for system health status

---

**Silver Tier v1.0** - Ready for production use ✅

