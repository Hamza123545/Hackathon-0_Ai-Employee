# Research: Bronze Tier Personal AI Employee

**Feature Branch**: `001-bronze-ai-employee`
**Date**: 2026-01-09
**Status**: Complete

## Research Questions

### RQ-001: Watcher Implementation Pattern

**Question**: What is the best pattern for implementing watchers in Python 3.13+?

**Decision**: Use the `watchdog` library for filesystem watching and `google-api-python-client` for Gmail watching, with a common `BaseWatcher` abstract class.

**Rationale**:
- `watchdog` is the standard Python library for filesystem monitoring (High reputation, 74 code snippets)
- Provides `FileSystemEventHandler` with `on_created`, `on_modified`, `on_deleted` hooks
- Works cross-platform (Windows, macOS, Linux)
- Gmail API requires polling approach (no real push for OAuth apps without Cloud Pub/Sub)

**Alternatives Considered**:
- `inotify` (Linux-only)
- Manual polling with `os.listdir()` (less efficient, misses events)
- `aionotify` (async-first, adds complexity)

### RQ-002: Gmail API Authentication

**Question**: How to authenticate with Gmail API for email monitoring?

**Decision**: Use OAuth 2.0 with desktop application flow, storing credentials in `.env` and token in a gitignored JSON file.

**Rationale**:
- Gmail API requires OAuth 2.0 for user data access
- Service accounts only work for Google Workspace domains with domain-wide delegation
- Desktop application flow is simplest for single-user hackathon use case
- Token refresh handled automatically by `google-auth-oauthlib`

**Implementation Pattern**:
```python
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Load or create credentials
creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('gmail', 'v1', credentials=creds)
```

**Alternatives Considered**:
- Service Account (requires Google Workspace admin access)
- API Key only (not supported for Gmail user data)
- App passwords (deprecated, not recommended)

### RQ-003: Filesystem Watcher Implementation

**Question**: How to detect new files in a monitored directory?

**Decision**: Use `watchdog.observers.Observer` with custom `FileSystemEventHandler`.

**Rationale**:
- Native cross-platform support
- Event-driven (not polling)
- Supports recursive monitoring
- Well-documented API

**Implementation Pattern**:
```python
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

class FileWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            # Create action file in vault
            self.create_action_file(event.src_path)

observer = Observer()
observer.schedule(handler, path_to_watch, recursive=True)
observer.start()
```

### RQ-004: Environment Configuration

**Question**: How to manage configuration and secrets?

**Decision**: Use `python-dotenv` to load `.env` file into `os.environ`.

**Rationale**:
- Standard 12-factor app approach
- Simple API: `load_dotenv()` then `os.getenv()`
- High reputation (87.4 benchmark score)
- Supports `.env.example` pattern for documentation

**Implementation Pattern**:
```python
from dotenv import load_dotenv
import os

load_dotenv()

VAULT_PATH = os.getenv('VAULT_PATH', './vault')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '60'))
GMAIL_CREDENTIALS_PATH = os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
```

**Required Environment Variables**:
| Variable | Purpose | Default |
|----------|---------|---------|
| `VAULT_PATH` | Path to Obsidian vault | `./vault` |
| `CHECK_INTERVAL` | Seconds between watcher checks | `60` |
| `WATCHER_TYPE` | `gmail` or `filesystem` | `filesystem` |
| `WATCH_PATH` | Path to monitor (filesystem) | None |
| `GMAIL_CREDENTIALS_PATH` | OAuth credentials file | `credentials.json` |
| `DRY_RUN` | Log without creating files | `false` |

### RQ-005: Duplicate Prevention

**Question**: How to prevent processing the same item twice?

**Decision**: Track processed item IDs in a local JSON file within the vault.

**Rationale**:
- Simple file-based persistence (no database needed)
- Survives watcher restarts
- Can be manually edited if needed
- JSON is human-readable

**Implementation Pattern**:
```python
import json
from pathlib import Path

class ProcessedTracker:
    def __init__(self, tracker_path: Path):
        self.tracker_path = tracker_path
        self.processed_ids = self._load()

    def _load(self) -> set:
        if self.tracker_path.exists():
            with open(self.tracker_path) as f:
                return set(json.load(f))
        return set()

    def _save(self):
        with open(self.tracker_path, 'w') as f:
            json.dump(list(self.processed_ids), f, indent=2)

    def is_processed(self, item_id: str) -> bool:
        return item_id in self.processed_ids

    def mark_processed(self, item_id: str):
        self.processed_ids.add(item_id)
        self._save()
```

### RQ-006: Claude Code Agent Skill Structure

**Question**: What is the required structure for a Claude Code Agent Skill?

**Decision**: Create skill at `.claude/skills/process-action-items/` with `SKILL.md` and `prompt.md`.

**Rationale**:
- Constitution mandates Agent Skills pattern
- Keeps prompts separate from application code
- Enables skill composition and testing

**Skill Directory Structure**:
```
.claude/skills/process-action-items/
├── SKILL.md              # Skill documentation (purpose, inputs, outputs)
└── prompt.md             # The actual prompt template
```

**SKILL.md Format**:
```markdown
# Skill: Process Action Items

## Purpose
Read action items from /Needs_Action, analyze using Company_Handbook.md rules,
create structured plans in /Plans, and archive processed items to /Done.

## Inputs
- Files in `/Needs_Action/*.md`
- Rules from `/Company_Handbook.md`

## Outputs
- Plan files in `/Plans/plan-{item-slug}-{timestamp}.md`
- Moved originals to `/Done/`
- Updated `/Dashboard.md`

## Approval Required
No - Bronze tier is read-only vault operations
```

## Technology Decisions Summary

| Component | Library/Tool | Version | Notes |
|-----------|--------------|---------|-------|
| Filesystem Watcher | `watchdog` | Latest | Cross-platform, event-driven |
| Gmail API | `google-api-python-client` | Latest | OAuth 2.0 authentication |
| OAuth Flow | `google-auth-oauthlib` | Latest | Desktop app flow |
| Environment Config | `python-dotenv` | v1.2.1+ | .env file loading |
| Python | Python | 3.13+ | Per constitution |

## Dependencies (requirements.txt)

```
watchdog>=4.0.0
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.1.0
python-dotenv>=1.0.0
```

## Open Items

None - all research questions resolved for Bronze tier.
