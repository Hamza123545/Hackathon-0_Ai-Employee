# Quickstart: Bronze Tier Personal AI Employee

**Feature Branch**: `001-bronze-ai-employee`
**Estimated Setup Time**: 30 minutes

## Prerequisites

- Python 3.13+ installed
- Obsidian v1.10.6+ installed
- Git (optional, for version control)
- Gmail account (if using Gmail watcher)

## Step 1: Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd <repository-root>

# Create virtual environment (this project uses uv)
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies using uv
# Note: This project uses uv package manager
pip install uv
uv sync
```

**Important**: This project uses the `uv` package manager. All Python commands should be run with `uv run` prefix when using the watcher.

## Step 2: Create Obsidian Vault Structure

```bash
# The vault is located at AI_Employee/ in the repository root
# Folder structure is already created:
# - AI_Employee/Inbox/
# - AI_Employee/Needs_Action/
# - AI_Employee/Done/
# - AI_Employee/Plans/
# - AI_Employee/watch_folder/ (for filesystem watcher)

# Verify structure exists
ls -la AI_Employee/
```

## Step 3: Configure Environment Variables

```bash
# Copy example environment file
cd AI_Employee
cp .env.example .env

# Edit .env with your settings
```

**Required Variables** (`AI_Employee/.env`):
```
# Vault Configuration - MUST use absolute paths
VAULT_PATH=D:/your/path/to/AI_Employee

# Watcher Configuration
WATCHER_TYPE=filesystem    # or 'gmail'
CHECK_INTERVAL=5           # seconds (5-60 recommended)

# For Filesystem Watcher - MUST use absolute path
WATCH_PATH=D:/your/path/to/AI_Employee/watch_folder

# For Gmail Watcher (if using gmail)
GMAIL_CREDENTIALS_PATH=credentials.json

# Development
DRY_RUN=false
LOG_LEVEL=INFO
```

**CRITICAL**: Paths in `.env` MUST be absolute paths. Relative paths like `./AI_Employee` will cause "path does not exist" errors.

## Step 4: Initialize Vault Files

The watcher will create `Dashboard.md` and `Company_Handbook.md` on first run, or you can create them manually:

**Dashboard.md**:
```markdown
---
last_updated: 2026-01-09T00:00:00Z
watcher_status: stopped
last_watcher_check: null
---

# Personal AI Employee Dashboard

**Last Updated**: Not yet initialized

## System Status

| Component | Status | Last Activity |
|-----------|--------|---------------|
| Watcher | Stopped | - |
| Vault Access | Checking... | - |

## Pending Items

**Items in /Needs_Action**: 0

## Recent Activity (Last 24h)

No activity recorded yet.

## Quick Stats

- **Plans created today**: 0
- **Items processed today**: 0
- **Active plans**: 0
```

**Company_Handbook.md**:
```markdown
---
version: "1.0.0"
last_updated: 2026-01-09
---

# Company Handbook

## Priority Rules

### High Priority
- Subject contains: "URGENT", "ASAP", "Critical", "Important"

### Medium Priority
- Default for most items

### Low Priority
- Newsletters and automated emails

## Processing Rules

### Action Plan Requirements
- Minimum 3 actionable checkboxes per plan
- Use imperative mood
- Group by timeline (immediate, follow-up)
```

## Step 5: Setup Gmail OAuth (If Using Gmail Watcher)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the Gmail API
4. Create OAuth 2.0 credentials (Desktop application type)
5. Download `credentials.json` to project root
6. First run will prompt for browser authentication

## Step 6: Run the Watcher

```bash
# Navigate to AI_Employee directory
cd AI_Employee

# Run the watcher using uv (IMPORTANT: use uv run)
uv run python run_watcher.py

# Alternative: Activate venv first, then run
# .venv\Scripts\activate  (Windows)
# source .venv/bin/activate  (Linux/Mac)
# python run_watcher.py
```

The watcher will:
1. Verify vault structure on startup
2. Check for new items every `CHECK_INTERVAL` seconds
3. Create action files in `/Needs_Action/` with proper frontmatter
4. Track processed file IDs in `.processed_ids.json` (prevents duplicates)
5. Update `Dashboard.md` automatically
6. Log activity to console (stderr)

**To stop the watcher**: Press `Ctrl+C`

## Step 7: Process Action Items with Claude Code

1. Open Claude Code in your repository directory
2. Check `AI_Employee/Needs_Action/` for pending items
3. Invoke the process-action-items skill:

```
@process-action-items
```

Or use the skill command:
```
/process-action-items
```

This will:
1. Read action items from `AI_Employee/Needs_Action/`
2. Load processing rules from `Company_Handbook.md`
3. Analyze content and determine priority (HIGH/MEDIUM/LOW)
4. Create structured plan files in `AI_Employee/Plans/` with:
   - Context section with source reference
   - Analysis section with priority rationale
   - Minimum 3 actionable checkboxes
   - Notes and next steps
5. Move processed items to `AI_Employee/Done/`
6. Update `Dashboard.md` with processing activity

**Expected Output**: A plan file like `plan-[slug]-[timestamp].md` in the `/Plans/` folder with actionable checkboxes.

## Verification Checklist

- [ ] Vault folder structure exists at `AI_Employee/` (Inbox, Needs_Action, Done, Plans, watch_folder)
- [ ] `.env` file configured with ABSOLUTE paths
- [ ] Virtual environment activated or using `uv run`
- [ ] `Dashboard.md` displays in Obsidian and shows watcher status
- [ ] `Company_Handbook.md` is readable and contains priority rules
- [ ] Watcher starts without "path does not exist" errors
- [ ] Test file in `watch_folder/` creates action item in `/Needs_Action/` within CHECK_INTERVAL
- [ ] Action item has proper frontmatter (id, source, title, created, priority, status, tags)
- [ ] `.processed_ids.json` tracks file ID (duplicate prevention)
- [ ] Claude Code @process-action-items skill reads from vault
- [ ] Plan created in `/Plans/` with 3+ checkboxes
- [ ] Processed item moved to `/Done/`
- [ ] Dashboard.md shows pending count of 0 after processing

## Troubleshooting

### Watcher won't start
- **"path does not exist" error**: Use ABSOLUTE paths in `.env`, not relative paths
  - Wrong: `VAULT_PATH=./AI_Employee`
  - Right: `VAULT_PATH=D:/your/repo/AI_Employee`
- **ModuleNotFoundError**: Run with `uv run` or activate virtual environment first
- **Permission errors**: Check folder permissions, run as administrator if needed
- Verify Python 3.13+ is installed: `python --version`

### Gmail authentication fails
- Ensure `credentials.json` is in `AI_Employee/` directory
- Delete `token.pickle` and re-authenticate
- Check Gmail API is enabled in Google Cloud Console
- Verify OAuth consent screen is configured

### Claude Code can't access vault
- Verify `VAULT_PATH` uses absolute path
- Check file permissions (read/write access)
- Ensure Obsidian is not locking files
- Confirm vault structure exists (Inbox, Needs_Action, Done, Plans folders)

### No action files created
- Check watcher is running (should show "Starting FilesystemWatcher..." in console)
- Verify `WATCH_PATH` exists and uses absolute path
- Confirm files are being added to `watch_folder/` after watcher starts
- Enable `DRY_RUN=true` in `.env` to see what would be created without writing
- Check console logs for errors (output goes to stderr)
- Verify `.processed_ids.json` exists and is valid JSON

### Duplicate action items created
- Check `.processed_ids.json` for corruption (should be valid JSON)
- Delete `.processed_ids.json` and restart watcher to reset tracking
- Verify file content hasn't changed (hash is based on content)

## Next Steps

1. Customize `Company_Handbook.md` with your priority rules
2. Add more email filters or file patterns
3. Review generated plans and refine prompts
4. Consider adding automated scheduling (cron/Task Scheduler)

## File Locations Summary

| File | Location | Purpose |
|------|----------|---------|
| Environment Config | `AI_Employee/.env` | API keys, paths, settings (requires absolute paths) |
| Watcher Entry Point | `AI_Employee/run_watcher.py` | Script to start watcher with correct Python path |
| Main Watcher Logic | `AI_Employee/main.py` | Watcher initialization and configuration |
| Processed IDs Tracker | `AI_Employee/.processed_ids.json` | Prevents duplicate processing (auto-created) |
| Gmail Credentials | `AI_Employee/credentials.json` | OAuth client config (if using Gmail) |
| Gmail Token | `AI_Employee/token.pickle` | Stored OAuth token (if using Gmail) |
| Vault Root | `AI_Employee/` | Obsidian vault root directory |
| Watch Folder | `AI_Employee/watch_folder/` | Drop files here for filesystem watcher to detect |
| Watcher Modules | `AI_Employee/watchers/` | filesystem_watcher.py, gmail_watcher.py, base_watcher.py |
| Agent Skill | `.claude/skills/process-action-items/` | Claude Code skill for processing action items |
| Company Rules | `AI_Employee/Company_Handbook.md` | Priority rules and processing guidelines |
| System Dashboard | `AI_Employee/Dashboard.md` | Live status (auto-updated by watcher) |
