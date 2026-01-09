# Personal AI Employee - Bronze Tier

A Python-based autonomous AI assistant that monitors external sources (filesystem, Gmail) and creates actionable plans in an Obsidian vault.

## Features

- **Filesystem Watcher**: Monitor a folder for new files and create action items
- **Gmail Watcher**: Poll Gmail inbox for new emails and create action items
- **Obsidian Integration**: Store all data as Markdown files in an Obsidian vault
- **Dashboard**: Real-time status dashboard updated automatically
- **Claude Code Skills**: Process action items and generate structured plans

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

## Bronze Tier Limitations

This is the Bronze tier implementation:
- Manual execution of all plans
- No automatic email sending
- No external API integrations
- Human-in-the-loop for all actions

## License

MIT License
