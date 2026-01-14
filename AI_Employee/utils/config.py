"""
Configuration loader for Bronze/Silver Tier Personal AI Employee.

Loads environment variables from .env file using python-dotenv.
Supports both Bronze tier (watchers only) and Silver tier (MCP servers,
approval workflow, audit logging).
"""

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


class Config:
    """
    Configuration class that loads settings from environment variables.

    Bronze Tier Attributes:
        vault_path: Path to the Obsidian vault
        watcher_type: Type of watcher ('filesystem' or 'gmail')
        check_interval: Seconds between watcher checks
        watch_path: Path to monitor (for filesystem watcher)
        gmail_credentials_path: Path to Gmail OAuth credentials
        dry_run: If True, log actions without writing files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Silver Tier Attributes:
        approval_check_interval: Seconds between approval folder checks
        mcp_servers_config_path: Path to MCP servers JSON configuration
        audit_log_retention_days: Days to retain audit logs before cleanup
        auto_approval_enabled: Whether auto-approval is enabled (default: False)
        linkedin_access_token: LinkedIn API OAuth2 token
        linkedin_person_urn: LinkedIn person URN for API calls
        whatsapp_session_file: Path to WhatsApp session file
        smtp_host: SMTP server hostname for email MCP
        smtp_port: SMTP server port
        smtp_username: SMTP authentication username
        smtp_password: SMTP authentication password
        smtp_from_address: Default from address for emails
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

        # Silver tier configuration
        self._load_silver_tier_config()
        
        # Gold tier configuration
        self._load_gold_tier_config()

    def _load_silver_tier_config(self) -> None:
        """Load Silver tier specific configuration from environment."""
        # Approval workflow settings
        self.approval_check_interval = int(
            os.getenv('APPROVAL_CHECK_INTERVAL', '60')
        )
        self.auto_approval_enabled = os.getenv(
            'AUTO_APPROVAL_ENABLED', 'false'
        ).lower() in ('true', '1', 'yes')

        # MCP servers configuration
        self.mcp_servers_config_path = os.getenv(
            'MCP_SERVERS_CONFIG_PATH',
            str(self.vault_path / 'mcp_servers.json')
        )

        # Audit logging settings
        self.audit_log_retention_days = int(
            os.getenv('AUDIT_LOG_RETENTION_DAYS', '90')
        )

        # LinkedIn settings
        self.linkedin_access_token = os.getenv('LINKEDIN_ACCESS_TOKEN', '')
        self.linkedin_person_urn = os.getenv('LINKEDIN_PERSON_URN', '')

        # WhatsApp settings
        self.whatsapp_session_file = os.getenv(
            'WHATSAPP_SESSION_FILE',
            str(self.vault_path / 'whatsapp_session.json')
        )

        # Email MCP settings
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.smtp_from_address = os.getenv('FROM_ADDRESS', '')
    
    def _load_gold_tier_config(self) -> None:
        """Load Gold tier specific configuration from environment."""
        # AI Processor settings
        self.processing_interval = int(
            os.getenv('PROCESSING_INTERVAL', '30')
        )
        self.ai_processor_enabled = os.getenv(
            'AI_PROCESSOR_ENABLED', 'false'
        ).lower() in ('true', '1', 'yes')
        self.auto_process_personal = os.getenv(
            'AUTO_PROCESS_PERSONAL', 'true'
        ).lower() in ('true', '1', 'yes')
        self.auto_process_business = os.getenv(
            'AUTO_PROCESS_BUSINESS', 'true'
        ).lower() in ('true', '1', 'yes')

        # Groq API for AI-generated insights (replaces Claude/Anthropic)
        self.groq_api_key = os.getenv('GROQ_API_KEY', '')
        self.groq_model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')

        # Legacy: Keep anthropic_api_key for backward compatibility
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', '')

        # Xero settings
        self.xero_client_id = os.getenv('XERO_CLIENT_ID', '')
        self.xero_client_secret = os.getenv('XERO_CLIENT_SECRET', '')
        self.xero_tenant_id = os.getenv('XERO_TENANT_ID', '')
        self.xero_redirect_uri = os.getenv('XERO_REDIRECT_URI', 'http://localhost:8000/oauth/xero/callback')

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

    @property
    def screenshots_path(self) -> Path:
        """Path to the Logs/screenshots folder (Silver tier)."""
        return self.logs_path / 'screenshots'
    
    @property
    def accounting_path(self) -> Path:
        """Path to the Accounting folder (Gold tier)."""
        return self.vault_path / 'Accounting'
    
    @property
    def business_path(self) -> Path:
        """Path to the Business folder (Gold tier)."""
        return self.vault_path / 'Business'
    
    @property
    def briefings_path(self) -> Path:
        """Path to the Briefings folder (Gold tier)."""
        return self.vault_path / 'Briefings'
    
    @property
    def system_path(self) -> Path:
        """Path to the System folder (Gold tier)."""
        return self.vault_path / 'System'

    def get_mcp_servers_config(self) -> dict[str, Any]:
        """
        Load MCP servers configuration from JSON file.

        Returns:
            Dictionary with MCP server configurations.
        """
        config_path = Path(self.mcp_servers_config_path)
        if not config_path.exists():
            return {'servers': []}

        try:
            content = config_path.read_text(encoding='utf-8')
            return json.loads(content)
        except (json.JSONDecodeError, OSError):
            return {'servers': []}

    def save_mcp_servers_config(self, config: dict[str, Any]) -> bool:
        """
        Save MCP servers configuration to JSON file.

        Args:
            config: Dictionary with MCP server configurations.

        Returns:
            True if saved successfully, False otherwise.
        """
        config_path = Path(self.mcp_servers_config_path)
        try:
            content = json.dumps(config, indent=2)
            config_path.write_text(content, encoding='utf-8')
            return True
        except OSError:
            return False

    def is_silver_tier_enabled(self) -> bool:
        """
        Check if Silver tier features are enabled.

        Silver tier is enabled if any of the following are true:
        - At least one MCP server is configured
        - Approval workflow folders exist
        - LinkedIn or WhatsApp credentials are set

        Returns:
            True if Silver tier features are available.
        """
        # Check for MCP servers config
        mcp_config = self.get_mcp_servers_config()
        if mcp_config.get('servers'):
            return True

        # Check for Silver tier folders
        if self.pending_approval_path.exists():
            return True

        # Check for Silver tier credentials
        if self.linkedin_access_token or self.smtp_username:
            return True

        return False

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

        # Check watcher type (Silver tier adds 'whatsapp' and 'linkedin')
        valid_watchers = ('filesystem', 'gmail', 'whatsapp', 'linkedin')
        if self.watcher_type not in valid_watchers:
            errors.append(
                f"Invalid watcher type: {self.watcher_type}. "
                f"Must be one of: {', '.join(valid_watchers)}"
            )

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

        # Silver tier validations
        errors.extend(self._validate_silver_tier())

        return errors

    def _validate_silver_tier(self) -> list[str]:
        """
        Validate Silver tier specific configuration.

        Returns:
            List of error messages for Silver tier config.
        """
        errors: list[str] = []

        # Validate approval check interval
        if self.approval_check_interval <= 0:
            errors.append(
                f"Approval check interval must be positive: "
                f"{self.approval_check_interval}"
            )

        # Validate audit log retention
        if self.audit_log_retention_days <= 0:
            errors.append(
                f"Audit log retention days must be positive: "
                f"{self.audit_log_retention_days}"
            )

        # Validate SMTP port if host is set
        if self.smtp_host and self.smtp_port:
            if not (1 <= self.smtp_port <= 65535):
                errors.append(
                    f"SMTP port must be between 1 and 65535: {self.smtp_port}"
                )

        # Validate WhatsApp watcher requirements
        if self.watcher_type == 'whatsapp':
            session_path = Path(self.whatsapp_session_file)
            if not session_path.parent.exists():
                errors.append(
                    f"WhatsApp session directory does not exist: "
                    f"{session_path.parent}"
                )

        # Validate LinkedIn watcher requirements
        if self.watcher_type == 'linkedin':
            if not self.linkedin_access_token:
                errors.append(
                    "LINKEDIN_ACCESS_TOKEN is required for LinkedIn watcher"
                )

        return errors

    def ensure_vault_structure(self, include_silver: bool = True) -> None:
        """
        Create vault folder structure if it doesn't exist.

        Bronze tier: Creates Inbox/, Needs_Action/, Done/, Plans/
        Silver tier: Also creates Pending_Approval/, Approved/, Rejected/,
                     Logs/, Logs/screenshots/

        Args:
            include_silver: Whether to create Silver tier folders (default: True).
        """
        # Bronze tier folders
        bronze_folders = [
            self.inbox_path,
            self.needs_action_path,
            self.done_path,
            self.plans_path
        ]

        # Silver tier folders
        silver_folders = [
            self.pending_approval_path,
            self.approved_path,
            self.rejected_path,
            self.logs_path,
            self.screenshots_path  # Logs/screenshots for Playwright
        ]

        # Create Bronze folders
        for folder in bronze_folders:
            folder.mkdir(parents=True, exist_ok=True)

        # Create Silver folders if requested
        if include_silver:
            for folder in silver_folders:
                folder.mkdir(parents=True, exist_ok=True)
            
            # Gold tier folders (extends Silver)
            gold_folders = [
                self.accounting_path / 'Transactions',
                self.accounting_path / 'Summaries',
                self.accounting_path / 'Audits',
                self.business_path / 'Goals',
                self.business_path / 'Social_Media' / 'facebook',
                self.business_path / 'Social_Media' / 'instagram',
                self.business_path / 'Social_Media' / 'twitter',
                self.business_path / 'Workflows',
                self.business_path / 'Metrics',
                self.business_path / 'Engagement',
                self.briefings_path,
                self.system_path / 'MCP_Status',
                self.system_path / 'Failed_Requests'
            ]
            
            # Create social media folders
            for folder in gold_folders:
                folder.mkdir(parents=True, exist_ok=True)
            
            for folder in gold_folders:
                folder.mkdir(parents=True, exist_ok=True)

    def __repr__(self) -> str:
        return (
            f"Config(\n"
            f"  vault_path={self.vault_path},\n"
            f"  watcher_type={self.watcher_type},\n"
            f"  check_interval={self.check_interval},\n"
            f"  watch_path={self.watch_path},\n"
            f"  dry_run={self.dry_run},\n"
            f"  # Silver tier\n"
            f"  approval_check_interval={self.approval_check_interval},\n"
            f"  auto_approval_enabled={self.auto_approval_enabled},\n"
            f"  audit_log_retention_days={self.audit_log_retention_days},\n"
            f"  silver_tier_enabled={self.is_silver_tier_enabled()}\n"
            f")"
        )
