# Research Findings: Silver Tier Personal AI Employee

**Feature**: Silver Tier Personal AI Employee
**Date**: 2026-01-09
**Research Phase**: Phase 0 - Technology Selection and Patterns

## Executive Summary

This research document consolidates findings for key technical decisions required for Silver Tier implementation, extending the Bronze tier Personal AI Employee with external actions, MCP server integration, and production-ready process management.

**Key Decisions Made**:
1. **MCP Servers**: Python FastMCP (easier, consistent with codebase)
2. **Email MCP**: Custom SMTP MCP server (simplest, most control)
3. **LinkedIn Integration**: REST API v2 (official, stable)
4. **WhatsApp Automation**: Playwright with session persistence (proven pattern)
5. **Process Management**: PM2 (cross-platform, robust)
6. **Audit Logging**: Daily JSON files (simple, compliant)
7. **Approval Orchestrator**: File polling with watchdog (reliable, simple)

---

## 1. MCP Server Implementation

**Research Question**: Should we use Python FastMCP or Node.js @modelcontextprotocol/server for building custom MCP servers?

### Decision: Python FastMCP

**Rationale**:
- **Consistency**: Entire codebase is Python 3.13+ (watchers, skills, utilities)
- **Simplicity**: FastMCP provides higher-level API with less boilerplate
- **Team Familiarity**: Python developers don't need Node.js knowledge
- **Integration**: Direct integration with existing Python utilities (audit logger, config)
- **Deployment**: Single runtime environment (no Node.js + Python complexity)

### Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **FastMCP (Python)** ✅ | Simple API, Python-native, easy integration | Slightly less mature than Node SDK |
| **Low-level Python MCP SDK** | More control, official SDK | More boilerplate, complex setup |
| **Node.js MCP SDK** | Mature ecosystem, more examples | Requires Node.js, different language, integration complexity |

### Implementation Pattern (FastMCP)

```python
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Email MCP Server")

# Define tool with automatic JSON-RPC handling
@mcp.tool()
def send_email(to: str, subject: str, body: str, from_addr: str = None) -> dict:
    """Send an email via SMTP."""
    # Implementation with error handling
    try:
        # SMTP logic here
        return {"status": "sent", "message_id": "12345"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Run server on stdio (standard MCP transport)
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

**Key FastMCP Features**:
- Automatic JSON-RPC request/response handling
- Built-in error handling and validation
- Stdio transport (standard for MCP)
- Optional HTTP transport for debugging
- Resource and prompt support (not needed for Silver tier)

**Setup Requirements**:
- Install: `pip install mcp`
- No additional dependencies beyond standard library for basic servers
- SMTP library (`smtplib`) for email server

---

## 2. Email MCP Server

**Research Question**: Should we use existing email-mcp, custom SMTP MCP, or Gmail API MCP?

### Decision: Custom SMTP MCP Server

**Rationale**:
- **Control**: Full control over SMTP settings, error handling, retry logic
- **Simplicity**: SMTP is standard library (`smtplib`), no external dependencies
- **Flexibility**: Easy to support multiple SMTP providers (Gmail, SendGrid, custom)
- **Security**: Credentials managed via environment variables, not hardcoded
- **Testing**: Easy to test with local SMTP server or Gmail test account

### Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Custom SMTP MCP** ✅ | Full control, simple, standard library | Requires SMTP configuration |
| **Existing email-mcp** | Pre-built, tested | May not fit our auth/approval workflow |
| **Gmail API MCP** | Integrated with Gmail watcher | Complex OAuth, Gmail-specific |

### Implementation Approach

**Server Structure**:
```
AI_Employee/
└── mcp_servers/
    ├── email/
    │   ├── server.py          # FastMCP server with send_email tool
    │   ├── smtp_client.py     # SMTP client wrapper
    │   └── README.md          # Setup instructions
    ├── linkedin/
    │   ├── server.py
    │   └── linkedin_client.py
    └── playwright/
        ├── server.py
        └── browser_client.py
```

**Configuration**:
```env
# .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=user@gmail.com
SMTP_PASSWORD=app_password
SMTP_FROM_ADDRESS=user@gmail.com
SMTP_USE_TLS=true
```

**Error Handling**:
- SMTP connection errors → retry with exponential backoff (max 3 attempts)
- Authentication failures → fail fast, log error, notify via `/Needs_Action/`
- Rate limits → queue email, log, retry after delay
- Invalid recipients → validate before sending, return error in MCP response

---

## 3. LinkedIn API v2 Integration

**Research Question**: How should we integrate LinkedIn for posting and monitoring?

### Decision: LinkedIn REST API v2 (Official)

**Rationale**:
- **Official**: LinkedIn's supported API, stable and documented
- **OAuth2**: Standard authentication flow
- **Rate Limits**: Clear limits (documented in API responses)
- **Posting**: `/rest/posts` endpoint supports text, hashtags, media
- **Monitoring**: Can poll for notifications/messages (watcher use case)

### API Patterns

**Authentication**:
```python
# OAuth2 flow (one-time setup)
# 1. User authorizes app via browser
# 2. App receives access token
# 3. Token stored in .env (LINKEDIN_ACCESS_TOKEN)
# 4. Token refreshed before expiration (if refresh token available)

headers = {
    "Authorization": f"Bearer {access_token}",
    "X-Restli-Protocol-Version": "2.0.0",
    "Linkedin-Version": "202601",  # YYYYMM format
    "Content-Type": "application/json"
}
```

**Creating a Post**:
```python
payload = {
    "author": f"urn:li:person:{person_id}",
    "commentary": "Your post text here #hashtag",
    "visibility": "PUBLIC",
    "distribution": {
        "feedDistribution": "MAIN_FEED"
    },
    "lifecycleState": "PUBLISHED",
    "isReshareDisabledByAuthor": False
}

response = requests.post(
    "https://api.linkedin.com/rest/posts",
    headers=headers,
    json=payload
)

# Success: 201 status, post ID in x-restli-id header
post_id = response.headers.get("x-restli-id")
```

**Rate Limiting**:
- Response includes rate limit headers
- 429 status code indicates rate limit exceeded
- Implement exponential backoff: 1s, 2s, 4s, 8s, 16s (max 5 retries)
- Daily post limit: 1-3 posts/day recommended (avoid spam perception)

### LinkedIn Watcher Design

**Pattern**: API polling (not web scraping)
- Poll `/v2/me` for profile updates (1 request/5 min = ~300 requests/day, well under limits)
- Poll `/communications` for messages (if permissions granted)
- Track activity IDs to detect new interactions (duplicate prevention)
- Create action items in `/Needs_Action/` for new messages/comments

**Limitations**:
- LinkedIn API access requires app approval (may take time)
- Limited to organization pages or personal profiles (not both without separate auth)
- No real-time webhooks for free tier (polling only)

---

## 4. Playwright WhatsApp Web Automation

**Research Question**: How to use Playwright for WhatsApp Web with session persistence?

### Decision: Playwright Python with Browser Context Persistence

**Rationale**:
- **Session Persistence**: `storage_state()` saves cookies/local storage for WhatsApp login
- **No QR Code Repeat**: One-time QR scan, then reuse session
- **Reliable**: Playwright is battle-tested for web automation
- **Cross-Platform**: Works on Linux, Mac, Windows
- **Headless Mode**: Can run without visible browser (production)

### Implementation Pattern

**Initial Setup (QR Code Scan)**:
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Visible for QR scan
    context = browser.new_context()
    page = context.new_page()

    page.goto('https://web.whatsapp.com')
    print("Scan QR code in browser window...")
    page.wait_for_selector('div[data-testid="chat-list"]', timeout=60000)  # Wait for login

    # Save session
    context.storage_state(path='whatsapp_session.json')
    print("Session saved! QR scan not needed again.")

    context.close()
    browser.close()
```

**Subsequent Runs (Reuse Session)**:
```python
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)  # Headless for production
    context = browser.new_context(storage_state='whatsapp_session.json')
    page = context.new_page()

    page.goto('https://web.whatsapp.com')
    page.wait_for_selector('div[data-testid="chat-list"]')  # Should load instantly

    # Monitor for new messages
    # ... (detection logic)

    context.close()
    browser.close()
```

### Message Detection Strategy

**Approach**: Poll for new messages by checking chat list
```python
# Get all chats
chats = page.locator('div[data-testid="chat-list"] div[role="listitem"]').all()

for chat in chats:
    # Check for unread badge
    unread = chat.locator('div[data-testid="unread-count"]').count()
    if unread > 0:
        chat.click()  # Open chat

        # Get latest messages
        messages = page.locator('div[data-testid="msg-container"]').all()
        last_message = messages[-1]

        sender = last_message.locator('span[aria-label*="You:"]').count() == 0  # Not from us
        if sender:
            text = last_message.locator('span.copyable-text').text_content()
            timestamp = last_message.locator('span[data-testid="msg-meta"]').text_content()

            # Create action item in /Needs_Action/
            # ...
```

**Duplicate Prevention**:
- Track last processed message timestamp per contact
- Store in `.processed_whatsapp.json` (similar to email watcher)
- Compare message timestamps to detect new messages only

**Session Expiration**:
- WhatsApp Web sessions expire after ~2 weeks of inactivity
- Detect expiration: QR code reappears (check for `canvas[aria-label="Scan me!"]`)
- On expiration: Log error, create notification in `/Needs_Action/`, stop watcher
- User must re-scan QR code and restart watcher

---

## 5. PM2 Process Management

**Research Question**: How to use PM2 for managing multiple Python watchers?

### Decision: PM2 with Python Interpreter Configuration

**Rationale**:
- **Cross-Platform**: Works on Windows, Mac, Linux
- **Auto-Restart**: Configurable crash recovery
- **Multi-Process**: Manages multiple watchers independently
- **Logging**: Built-in log rotation and management
- **Monitoring**: `pm2 status`, `pm2 logs`, `pm2 monit` commands

### Ecosystem Configuration

**File**: `AI_Employee/ecosystem.config.js`
```javascript
module.exports = {
  apps: [
    {
      name: 'gmail-watcher',
      script: 'run_watcher.py',
      args: 'gmail',
      interpreter: 'python3',  // or full path: /usr/bin/python3
      exec_mode: 'fork',       // NOT cluster (Python doesn't support cluster)
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',       // Must stay up 10s to count as successful start
      restart_delay: 4000,     // Wait 4s before restart

      // Environment variables
      env: {
        PYTHONUNBUFFERED: '1',  // Disable Python output buffering
        LOG_LEVEL: 'INFO',
        VAULT_PATH: 'D:/specs/AI_Employee'
      },

      // Logging
      error_file: './logs/gmail-watcher-err.log',
      out_file: './logs/gmail-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,

      // Memory management
      max_memory_restart: '500M'
    },
    {
      name: 'whatsapp-watcher',
      script: 'run_watcher.py',
      args: 'whatsapp',
      interpreter: 'python3',
      exec_mode: 'fork',
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',

      env: {
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO',
        VAULT_PATH: 'D:/specs/AI_Employee'
      },

      error_file: './logs/whatsapp-watcher-err.log',
      out_file: './logs/whatsapp-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,
      max_memory_restart: '800M'  // Playwright needs more memory
    },
    {
      name: 'linkedin-watcher',
      script: 'run_watcher.py',
      args: 'linkedin',
      interpreter: 'python3',
      exec_mode: 'fork',
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',

      env: {
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO',
        VAULT_PATH: 'D:/specs/AI_Employee'
      },

      error_file: './logs/linkedin-watcher-err.log',
      out_file: './logs/linkedin-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,
      max_memory_restart: '300M'
    },
    {
      name: 'approval-orchestrator',
      script: 'run_orchestrator.py',
      interpreter: 'python3',
      exec_mode: 'fork',
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      cron_restart: '0 */12 * * *',  // Restart every 12 hours for cleanup

      env: {
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO',
        VAULT_PATH: 'D:/specs/AI_Employee',
        APPROVAL_CHECK_INTERVAL: '60'  // Check /Approved every 60 seconds
      },

      error_file: './logs/orchestrator-err.log',
      out_file: './logs/orchestrator-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,
      max_memory_restart: '300M'
    }
  ]
};
```

### PM2 Commands

**Start all watchers**:
```bash
cd AI_Employee
pm2 start ecosystem.config.js
```

**Monitor status**:
```bash
pm2 status                    # List all processes
pm2 logs                      # View logs (all processes)
pm2 logs gmail-watcher        # View specific process logs
pm2 monit                     # Real-time monitoring UI
```

**Control processes**:
```bash
pm2 stop gmail-watcher        # Stop specific watcher
pm2 restart whatsapp-watcher  # Restart watcher
pm2 delete linkedin-watcher   # Remove from PM2
pm2 reload ecosystem.config.js  # Reload config
```

**OS Startup Integration**:
```bash
pm2 startup                   # Generate startup script
pm2 save                      # Save current process list
# Watchers will auto-start on OS boot
```

### Alternative: Supervisord (Linux Only)

**Config**: `/etc/supervisor/conf.d/ai-employee.conf`
```ini
[program:gmail-watcher]
command=/usr/bin/python3 /path/to/run_watcher.py gmail
directory=/path/to/AI_Employee
autostart=true
autorestart=true
startretries=10
redirect_stderr=true
stdout_logfile=/var/log/ai-employee/gmail-watcher.log

[program:whatsapp-watcher]
command=/usr/bin/python3 /path/to/run_watcher.py whatsapp
directory=/path/to/AI_Employee
autostart=true
autorestart=true
startretries=10
redirect_stderr=true
stdout_logfile=/var/log/ai-employee/whatsapp-watcher.log
```

**Recommendation**: PM2 preferred for cross-platform support.

---

## 6. Audit Logging Design

**Research Question**: What's the best approach for audit logging with credential sanitization?

### Decision: Daily JSON Files with Structured Schema

**Rationale**:
- **Simple**: One file per day (`/Logs/2026-01-09.json`)
- **Compliance**: 90-day retention (delete files older than 90 days)
- **Structured**: JSON array for easy parsing
- **Rotation**: Automatic (new file each day)
- **Performance**: Append-only writes (fast)

### Schema Design

```json
{
  "entries": [
    {
      "entry_id": "ae3f12b4-5678-90cd-ef12-34567890abcd",
      "timestamp": "2026-01-09T14:23:15.123456Z",
      "action_type": "email_send",
      "actor": "claude-code",
      "target": "user@example.com",
      "parameters": {
        "subject": "Meeting reminder",
        "body_preview": "Hi, just a reminder about...",
        "from": "assistant@example.com"
      },
      "approval_status": "approved",
      "approval_by": "user",
      "approval_timestamp": "2026-01-09T14:20:00Z",
      "mcp_server": "email-mcp",
      "result": "success",
      "error": null,
      "execution_duration_ms": 1234
    },
    {
      "entry_id": "bf4e23c5-6789-01de-fg23-45678901bcde",
      "timestamp": "2026-01-09T14:25:30.789012Z",
      "action_type": "linkedin_post",
      "actor": "claude-code",
      "target": "urn:li:person:12345",
      "parameters": {
        "commentary": "Excited to share our new feature!",
        "visibility": "PUBLIC"
      },
      "approval_status": "auto_approved",
      "approval_by": "system",
      "approval_timestamp": "2026-01-09T14:25:29Z",
      "mcp_server": "linkedin-mcp",
      "result": "success",
      "error": null,
      "post_url": "https://linkedin.com/feed/update/urn:li:share:6844785523593134080",
      "execution_duration_ms": 2156
    }
  ]
}
```

### Credential Sanitization

**Implementation**:
```python
import re
from typing import Any

class AuditLogger:
    SENSITIVE_KEYS = [
        'password', 'token', 'api_key', 'secret', 'credential',
        'auth', 'bearer', 'smtp_password', 'access_token'
    ]

    def sanitize_credentials(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remove or mask sensitive data recursively."""
        sanitized = {}
        for key, value in data.items():
            lower_key = key.lower()

            # Check if key contains sensitive terms
            if any(term in lower_key for term in self.SENSITIVE_KEYS):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_credentials(value)
            elif isinstance(value, str) and self._looks_like_token(value):
                sanitized[key] = self._mask_token(value)
            else:
                sanitized[key] = value

        return sanitized

    def _looks_like_token(self, value: str) -> bool:
        """Detect if string looks like a token/key."""
        # Long alphanumeric strings that look like tokens
        if len(value) > 30 and re.match(r'^[A-Za-z0-9+/=_-]+$', value):
            return True
        return False

    def _mask_token(self, token: str) -> str:
        """Mask token showing only first/last 4 chars."""
        if len(token) <= 8:
            return "***REDACTED***"
        return f"{token[:4]}...{token[-4:]}"
```

**Testing**: Unit tests verify zero credential leaks across sample data.

---

## 7. Approval Orchestrator Design

**Research Question**: How should the approval orchestrator detect and execute approved actions?

### Decision: File Polling with Watchdog Library

**Rationale**:
- **Reliable**: Watchdog is proven for file system monitoring
- **Simple**: Poll `/Approved/` folder every 60 seconds
- **Cross-Platform**: Works on Windows, Mac, Linux
- **Low Overhead**: Minimal CPU/memory usage
- **Fault-Tolerant**: Survives transient file system issues

### Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Polling with watchdog** ✅ | Simple, reliable, proven | 60s latency (acceptable per spec) |
| **Real-time file watching** | Instant detection | Complex, race conditions, OS-dependent |
| **MCP tool invocation** | Event-driven | Requires MCP client integration, more complex |

### Implementation Pattern

```python
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class ApprovalHandler(FileSystemEventHandler):
    def __init__(self, approved_path: Path):
        self.approved_path = approved_path

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix != '.md':
            return

        # Process approval
        self.execute_approved_action(file_path)

    def execute_approved_action(self, file_path: Path):
        """Read approval, execute via MCP, log to audit, move to Done."""
        # 1. Read and validate approval file
        # 2. Determine MCP server and action
        # 3. Execute via MCP client
        # 4. Log to audit log
        # 5. Move file to /Done/ with execution timestamp
        pass

# Run orchestrator
observer = Observer()
handler = ApprovalHandler(Path('/path/to/Approved'))
observer.schedule(handler, str(handler.approved_path), recursive=False)
observer.start()

try:
    while True:
        time.sleep(60)  # Keep alive
except KeyboardInterrupt:
    observer.stop()
observer.join()
```

**Check Interval**: 60 seconds (meets spec requirement: execution within 1 minute of approval)

---

## 8. Technology Stack Summary

### Core Dependencies

**Python Packages** (add to `pyproject.toml`):
```toml
[project.dependencies]
# Existing Bronze dependencies
watchdog = "^3.0.0"
google-api-python-client = "^2.108.0"
python-dotenv = "^1.0.0"

# New Silver dependencies
mcp = "^1.0.0"                    # FastMCP for MCP servers
playwright = "^1.40.0"            # WhatsApp watcher
requests = "^2.31.0"              # LinkedIn API
aiohttp = "^3.9.0"                # Async HTTP for MCP
pydantic = "^2.5.0"               # Data validation
```

**System Dependencies**:
- **Node.js v24+**: For PM2 (install via `nvm` or official installer)
- **PM2**: Install globally: `npm install -g pm2`
- **Playwright browsers**: Install via `playwright install chromium`

### Platform Support

| Platform | Watchers | PM2 | MCP Servers | Notes |
|----------|----------|-----|-------------|-------|
| **Windows 10/11** | ✅ | ✅ | ✅ | Full support, use Windows paths |
| **macOS** | ✅ | ✅ | ✅ | Full support |
| **Linux (Ubuntu 22.04+)** | ✅ | ✅ | ✅ | Full support |

---

## 9. Performance and Scale Targets

**From Spec Success Criteria**:

| Metric | Target | Implementation Strategy |
|--------|--------|-------------------------|
| **Watcher Uptime** | > 99.5% over 24h | PM2 auto-restart (max_restarts: 10) |
| **Approval Execution** | Within 10 minutes | Orchestrator polling: 60s interval |
| **LinkedIn Post Success** | 100% (valid posts) | Retry with exponential backoff, queue on failure |
| **Audit Log Coverage** | 100% of external actions | Mandatory logging in all execution paths |
| **Credential Leaks** | Zero | Sanitization unit tests, code review |
| **Dashboard Freshness** | < 5 minutes | Update Dashboard every 60s (watcher cycle) |
| **Daily Capacity** | 50+ items/day | Tested with load simulation |

---

## 10. Security Considerations

### Credential Management

**Storage**:
- All credentials in `.env` file (gitignored)
- Never in vault files or source code
- Production: Consider OS credential manager (keyring library)

**Required Credentials**:
```env
# Email MCP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=user@gmail.com
SMTP_PASSWORD=app_password_here
SMTP_FROM_ADDRESS=user@gmail.com

# LinkedIn MCP
LINKEDIN_ACCESS_TOKEN=AQV...long_token_here
LINKEDIN_PERSON_URN=urn:li:person:12345

# WhatsApp (Playwright session)
WHATSAPP_SESSION_FILE=./whatsapp_session.json  # Path only, not credential

# Gmail Watcher (existing Bronze)
GMAIL_CREDENTIALS_PATH=./credentials.json
```

### Approval Thresholds

**Auto-Approval Criteria** (from `Company_Handbook.md`):
- Email < 100 words to known contacts (allowlist in handbook)
- LinkedIn posts < 200 chars without links
- No browser automation (always requires approval)

**Default**: Auto-approval **DISABLED** (safety-first per constitution)

---

## 11. Next Steps

**Phase 1 - Design**:
- ✅ Research complete
- 🔄 Create `data-model.md` with entity schemas
- 🔄 Create `/contracts/` with MCP server interfaces
- 🔄 Create `quickstart.md` with setup instructions

**Phase 2 - Implementation** (after planning complete):
- Implement WhatsApp watcher (extends BaseWatcher)
- Implement LinkedIn watcher (extends BaseWatcher)
- Implement Email MCP server (FastMCP)
- Implement LinkedIn MCP server (FastMCP)
- Implement Playwright MCP server (optional)
- Implement ApprovalOrchestrator
- Implement AuditLogger utility
- Extend DashboardUpdater for Silver tier metrics
- Create PM2 ecosystem config
- Update process-action-items skill (approval request generation)
- Update execute-approved-actions skill (MCP execution)

---

## 12. Open Questions and Risks

**Risks**:
1. **LinkedIn API Access**: Requires app approval (may take days/weeks) → **Mitigation**: Apply early, have fallback (manual posting)
2. **WhatsApp Session Expiration**: Sessions expire after 2 weeks → **Mitigation**: Document re-scan process, detect expiration gracefully
3. **MCP Server Complexity**: First-time MCP implementation → **Mitigation**: Start with simple email server, test thoroughly
4. **PM2 on Windows**: Less common than Linux → **Mitigation**: Test on Windows early, document quirks

**Open Questions**:
- None remaining (all technical decisions documented above)

---

**Research Phase Status**: ✅ Complete
**Next Phase**: Phase 1 - Design (data-model.md, contracts/, quickstart.md)
