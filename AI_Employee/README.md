# Personal AI Employee - Gold Tier

A Python-based autonomous AI assistant that monitors external sources (filesystem, Gmail, WhatsApp, LinkedIn), processes action items automatically, integrates with business systems (Xero, Facebook, Instagram, Twitter), and generates weekly business intelligence reports.

## Features

### Bronze Tier
- **Filesystem Watcher**: Monitor a folder for new files and create action items
- **Gmail Watcher**: Poll Gmail inbox for new emails and create action items
- **Obsidian Integration**: Store all data as Markdown files in an Obsidian vault
- **Dashboard**: Real-time status dashboard updated automatically
- **Claude Code Skills**: Process action items and generate structured plans

### Silver Tier
- **Multi-Channel Watchers**: Gmail, WhatsApp, LinkedIn, Filesystem
- **MCP Server Integration**: Email, LinkedIn, Browser automation
- **Approval Workflow**: Human-in-the-loop (HITL) for external actions
- **Audit Logging**: Complete audit trail with credential sanitization

### Gold Tier (NEW)
- **Autonomous Processing**: AI Processor automatically processes action items (no manual invocation)
- **Xero Accounting Integration**: Automatic expense tracking, invoice creation, financial reports
- **Multi-Platform Social Media**: Facebook, Instagram, Twitter automation
- **Weekly Business Intelligence**: Automated audits and CEO briefings with AI insights
- **Cross-Domain Integration**: Seamless workflows spanning personal and business domains
- **Error Recovery**: Exponential backoff retry, request caching, graceful degradation

## Quick Start

### 1. Install Dependencies

This project uses [uv](https://docs.astral.sh/uv/) for fast dependency management.

```bash
cd AI_Employee
uv sync
```

Or if you prefer pip:

```bash
cd AI_Employee
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and edit it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Required: Path to this folder (the Obsidian vault)
VAULT_PATH=./AI_Employee

# Choose watcher type: 'filesystem' or 'gmail'
WATCHER_TYPE=filesystem

# Check interval in seconds
CHECK_INTERVAL=60

# For filesystem watcher: folder to monitor
WATCH_PATH=./watch_folder

# For Gmail watcher: path to OAuth credentials
GMAIL_CREDENTIALS_PATH=credentials.json

# Development options
DRY_RUN=false
LOG_LEVEL=INFO
```

### 3. Start the Watcher

```bash
uv run python -m AI_Employee.main
```

Or without uv:

```bash
python -m AI_Employee.main
```

## Vault Structure

```
AI_Employee/
├── Inbox/              # Manual triage area (Bronze: unused)
├── Needs_Action/       # Watcher deposits action items here
├── Done/               # Processed action items archived here
├── Plans/              # Claude Code creates plans here
├── Dashboard.md        # System status
├── Company_Handbook.md # Configuration and rules
└── .processed_ids.json # Duplicate prevention tracker (gitignored)
```

## Filesystem Watcher Setup

1. Create a watch folder:
   ```bash
   mkdir watch_folder
   ```

2. Set `WATCHER_TYPE=filesystem` and `WATCH_PATH=./watch_folder` in `.env`

3. Start the watcher:
   ```bash
   uv run python -m AI_Employee.main
   ```

4. Drop files into `watch_folder/` - action items will appear in `Needs_Action/`

## Gmail Watcher Setup

### Prerequisites

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the Gmail API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download `credentials.json` to the AI_Employee folder

### Configuration

1. Set `WATCHER_TYPE=gmail` in `.env`
2. Set `GMAIL_CREDENTIALS_PATH=credentials.json` in `.env`

### First Run

1. Start the watcher:
   ```bash
   uv run python -m AI_Employee.main
   ```

2. A browser window will open for OAuth authentication
3. Grant permission to read your Gmail
4. Token is saved to `token.pickle` for future runs

## Processing Action Items

Use Claude Code to process pending action items:

1. Open the vault in Claude Code
2. Run the `process-action-items` skill:
   ```
   Process any new action items in /Needs_Action folder. Create plans and update dashboard.
   ```

3. Review generated plans in `/Plans/`
4. Complete the checkbox items manually (Bronze tier)

## Configuration

### Company Handbook

Edit `Company_Handbook.md` to customize:
- Priority rules (which keywords trigger high/medium/low)
- VIP contacts (auto-high priority)
- Processing rules
- Plan generation guidelines

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VAULT_PATH` | Path to Obsidian vault | `.` |
| `WATCHER_TYPE` | `filesystem` or `gmail` | `filesystem` |
| `CHECK_INTERVAL` | Seconds between checks | `60` |
| `WATCH_PATH` | Folder to monitor (filesystem) | `./watch_folder` |
| `GMAIL_CREDENTIALS_PATH` | OAuth credentials file | `credentials.json` |
| `DRY_RUN` | Log without writing files | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Troubleshooting

### Vault Inaccessible
- Verify `VAULT_PATH` is set correctly in `.env`
- Check folder permissions

### Gmail Auth Expired
- Delete `token.pickle`
- Restart watcher to trigger re-authentication

### Rate Limited (Gmail)
- Reduce `CHECK_INTERVAL` to poll less frequently
- Wait a few minutes before restarting

### Duplicate Items
- Check `.processed_ids.json` for corruption
- Clear the file to reprocess all items

### Watcher Not Starting
- Check `LOG_LEVEL=DEBUG` for detailed output
- Verify all dependencies installed: `uv sync` or `pip install -r requirements.txt`

## Development

### Dry Run Mode

Test without creating files:

```bash
DRY_RUN=true uv run python -m AI_Employee.main
```

### Debug Logging

Enable verbose logging:

```bash
LOG_LEVEL=DEBUG uv run python -m AI_Employee.main
```

## Gold Tier Quick Start

### Prerequisites

1. **Bronze + Silver Tier Operational**: Ensure all Bronze and Silver tier features are working
2. **API Access**: 
   - Xero account with API access
   - Facebook Page with admin access
   - Instagram Business Account
   - Twitter Developer Account
3. **Python 3.10+** with required dependencies

### Setup Steps

1. **Install Gold Tier Dependencies**:
   ```bash
   pip install xero-python pyfacebook tweepy schedule keyring
   ```

2. **Configure Environment Variables** (add to `.env`):
   ```env
   # Xero API
   XERO_CLIENT_ID=your_client_id
   XERO_CLIENT_SECRET=your_client_secret
   XERO_TENANT_ID=your_tenant_id
   
   # Facebook/Instagram API
   FACEBOOK_APP_ID=your_app_id
   FACEBOOK_APP_SECRET=your_app_secret
   FACEBOOK_PAGE_ID=your_page_id
   
   # Twitter API
   TWITTER_CLIENT_ID=your_client_id
   TWITTER_CLIENT_SECRET=your_client_secret
   
   # Anthropic API (for AI insights)
   ANTHROPIC_API_KEY=your_api_key
   ```

3. **Run Verification Script**:
   ```bash
   python scripts/verify_gold_prerequisites.py
   ```

4. **Start AI Processor** (PM2):
   ```bash
   pm2 start ecosystem.config.js --only ai-processor
   ```

5. **Start MCP Health Checker** (PM2):
   ```bash
   pm2 start ecosystem.config.js --only mcp-health-checker
   ```

For detailed setup instructions, see `specs/003-gold-tier-ai-employee/quickstart.md`.

## Tier Comparison

| Feature | Bronze | Silver | Gold |
|---------|--------|--------|------|
| Watchers | Filesystem, Gmail | + WhatsApp, LinkedIn | All + Autonomous |
| Processing | Manual skill invocation | Manual skill invocation | **Automatic** |
| MCP Servers | None | Email, LinkedIn, Browser | + Xero, Facebook, Instagram, Twitter |
| Approval Workflow | N/A | HITL required | HITL + Auto-processing |
| Business Intelligence | N/A | N/A | **Weekly audits + CEO briefings** |
| Cross-Domain | N/A | N/A | **Personal + Business integration** |
| Error Recovery | Basic | Basic | **Exponential backoff + caching** |

## License

MIT License
