"""
Configuration loader for Bronze Tier Personal AI Employee.

Loads environment variables from .env file using python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """
    Configuration class that loads settings from environment variables.

    Attributes:
        vault_path: Path to the Obsidian vault
        watcher_type: Type of watcher ('filesystem' or 'gmail')
        check_interval: Seconds between watcher checks
        watch_path: Path to monitor (for filesystem watcher)
        gmail_credentials_path: Path to Gmail OAuth credentials
        dry_run: If True, log actions without writing files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """

    def __init__(self, env_path: str | Path | None = None):
        """
        Initialize configuration from environment variables.

        Args:
            env_path: Optional path to .env file. If None, searches in current
                     directory and parent directories.
        """
        # Load .env file
        if env_path:
            load_dotenv(dotenv_path=env_path)
        else:
            load_dotenv()

        # Vault configuration
        self.vault_path = Path(os.getenv('VAULT_PATH', '.')).resolve()

        # Watcher configuration
        self.watcher_type = os.getenv('WATCHER_TYPE', 'filesystem').lower()
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '60'))

        # Filesystem watcher settings
        watch_path = os.getenv('WATCH_PATH', './watch_folder')
        self.watch_path = Path(watch_path).resolve() if watch_path else None

        # Gmail watcher settings
        self.gmail_credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')

        # Development settings
        self.dry_run = os.getenv('DRY_RUN', 'false').lower() in ('true', '1', 'yes')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

    @property
    def needs_action_path(self) -> Path:
        """Path to the Needs_Action folder in the vault."""
        return self.vault_path / 'Needs_Action'

    @property
    def done_path(self) -> Path:
        """Path to the Done folder in the vault."""
        return self.vault_path / 'Done'

    @property
    def plans_path(self) -> Path:
        """Path to the Plans folder in the vault."""
        return self.vault_path / 'Plans'

    @property
    def inbox_path(self) -> Path:
        """Path to the Inbox folder in the vault."""
        return self.vault_path / 'Inbox'

    @property
    def dashboard_path(self) -> Path:
        """Path to Dashboard.md in the vault."""
        return self.vault_path / 'Dashboard.md'

    @property
    def handbook_path(self) -> Path:
        """Path to Company_Handbook.md in the vault."""
        return self.vault_path / 'Company_Handbook.md'

    @property
    def processed_ids_path(self) -> Path:
        """Path to the processed IDs tracker file."""
        return self.vault_path / '.processed_ids.json'

    @property
    def pending_approval_path(self) -> Path:
        """Path to the Pending_Approval folder (Silver tier)."""
        return self.vault_path / 'Pending_Approval'

    @property
    def approved_path(self) -> Path:
        """Path to the Approved folder (Silver tier)."""
        return self.vault_path / 'Approved'

    @property
    def rejected_path(self) -> Path:
        """Path to the Rejected folder (Silver tier)."""
        return self.vault_path / 'Rejected'

    @property
    def logs_path(self) -> Path:
        """Path to the Logs folder (Silver tier)."""
        return self.vault_path / 'Logs'

    def validate(self) -> list[str]:
        """
        Validate the configuration.

        Returns:
            List of error messages. Empty list if configuration is valid.
        """
        errors = []

        # Check vault path exists
        if not self.vault_path.exists():
            errors.append(f"Vault path does not exist: {self.vault_path}")

        # Check watcher type
        if self.watcher_type not in ('filesystem', 'gmail'):
            errors.append(f"Invalid watcher type: {self.watcher_type}. Must be 'filesystem' or 'gmail'")

        # Check watch path for filesystem watcher
        if self.watcher_type == 'filesystem':
            if not self.watch_path:
                errors.append("WATCH_PATH is required for filesystem watcher")
            elif not self.watch_path.exists():
                errors.append(f"Watch path does not exist: {self.watch_path}")

        # Check Gmail credentials for Gmail watcher
        if self.watcher_type == 'gmail':
            creds_path = Path(self.gmail_credentials_path)
            if not creds_path.exists():
                errors.append(f"Gmail credentials file not found: {self.gmail_credentials_path}")

        # Check interval is positive
        if self.check_interval <= 0:
            errors.append(f"Check interval must be positive: {self.check_interval}")

        return errors

    def ensure_vault_structure(self) -> None:
        """
        Create vault folder structure if it doesn't exist.

        Bronze tier: Creates Inbox/, Needs_Action/, Done/, Plans/
        Silver tier: Also creates Pending_Approval/, Approved/, Rejected/, Logs/
        """
        # Bronze tier folders
        bronze_folders = [self.inbox_path, self.needs_action_path,
                         self.done_path, self.plans_path]
        
        # Silver tier folders (optional - created if needed)
        silver_folders = [
            self.vault_path / 'Pending_Approval',
            self.vault_path / 'Approved',
            self.vault_path / 'Rejected',
            self.vault_path / 'Logs'
        ]
        
        # Create all folders
        for folder in bronze_folders + silver_folders:
            folder.mkdir(parents=True, exist_ok=True)

    def __repr__(self) -> str:
        return (
            f"Config(\n"
            f"  vault_path={self.vault_path},\n"
            f"  watcher_type={self.watcher_type},\n"
            f"  check_interval={self.check_interval},\n"
            f"  watch_path={self.watch_path},\n"
            f"  dry_run={self.dry_run}\n"
            f")"
        )
