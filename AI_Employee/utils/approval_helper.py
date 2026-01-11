"""
Approval helper for Silver Tier Personal AI Employee.

Provides utilities for detecting external actions in plans,
assessing risk levels, and creating approval requests.
"""

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from ..models.approval_request import (
    ActionType,
    ApprovalRequest,
    RiskLevel,
    create_approval_file
)
from .audit_logger import AuditLogger
from .config import Config


# External action detection keywords
EMAIL_KEYWORDS = [
    'send email', 'reply to', 'email back', 'respond via email',
    'forward to', 'email response', 'send response', 'send reply'
]

LINKEDIN_KEYWORDS = [
    'post to linkedin', 'share on linkedin', 'linkedin update',
    'publish to linkedin', 'linkedin post', 'post on linkedin'
]

BROWSER_KEYWORDS = [
    'automate browser', 'fill form', 'click button', 'navigate to',
    'browser automation', 'web automation', 'automated form',
    'web scraping', 'submit form'
]


class ApprovalHelper:
    """
    Helper class for creating and managing approval requests.

    Handles:
    - External action detection in plans
    - Risk level assessment
    - Approval request creation
    - Auto-approval threshold checking

    Attributes:
        config: Configuration object with vault paths.
        audit_logger: AuditLogger for logging approval events.
    """

    # MCP server mapping by action type
    MCP_SERVER_MAP = {
        'email_send': ('email_mcp', 'send_email'),
        'linkedin_post': ('linkedin_mcp', 'create_post'),
        'browser_action': ('playwright_mcp', 'browser_action')
    }

    def __init__(self, config: Config):
        """
        Initialize the approval helper.

        Args:
            config: Configuration object with vault paths.
        """
        self.config = config
        self.audit_logger = AuditLogger(config.logs_path)
        self._known_contacts: set[str] = set()
        self._auto_approval_rules: dict[str, Any] = {}
        self._load_handbook_rules()

    def _load_handbook_rules(self) -> None:
        """Load known contacts and auto-approval rules from Company_Handbook.md."""
        handbook_path = self.config.handbook_path
        if not handbook_path.exists():
            return

        try:
            content = handbook_path.read_text(encoding='utf-8')

            # Extract known contacts section
            contacts_match = re.search(
                r'##\s*(?:Known|Approved)\s*Contacts?\s*\n((?:[-*]\s*.+\n)+)',
                content, re.IGNORECASE
            )
            if contacts_match:
                contacts_text = contacts_match.group(1)
                for line in contacts_text.strip().split('\n'):
                    # Extract email addresses from the line
                    emails = re.findall(r'[\w\.-]+@[\w\.-]+', line)
                    self._known_contacts.update(emails)

            # Extract auto-approval rules section
            rules_match = re.search(
                r'##\s*Auto[- ]?Approval\s*Rules?\s*\n(.*?)(?:\n##|\Z)',
                content, re.IGNORECASE | re.DOTALL
            )
            if rules_match:
                rules_text = rules_match.group(1)

                # Check for enabled flag
                if re.search(r'enabled:\s*true', rules_text, re.IGNORECASE):
                    self._auto_approval_rules['enabled'] = True

                # Check for auto-approve LinkedIn low risk
                if re.search(r'linkedin[_\s]?low[_\s]?risk:\s*true', rules_text, re.IGNORECASE):
                    self._auto_approval_rules['linkedin_low_risk'] = True

                # Check for approved email contacts auto-approve
                if re.search(r'approved[_\s]?contacts[_\s]?auto:\s*true', rules_text, re.IGNORECASE):
                    self._auto_approval_rules['approved_contacts_auto'] = True

        except OSError:
            pass

    def detect_external_action(self, content: str) -> ActionType | None:
        """
        Detect if content contains external action keywords.

        Args:
            content: Plan content or action text to scan.

        Returns:
            ActionType if external action detected, None otherwise.
        """
        content_lower = content.lower()

        # Check for email keywords
        for keyword in EMAIL_KEYWORDS:
            if keyword in content_lower:
                return 'email_send'

        # Check for LinkedIn keywords
        for keyword in LINKEDIN_KEYWORDS:
            if keyword in content_lower:
                return 'linkedin_post'

        # Check for browser automation keywords
        for keyword in BROWSER_KEYWORDS:
            if keyword in content_lower:
                return 'browser_action'

        return None

    def assess_risk_level(
        self,
        action_type: ActionType,
        target: str,
        content: str,
        parameters: dict[str, Any] | None = None
    ) -> tuple[RiskLevel, list[str]]:
        """
        Assess risk level for an action.

        Args:
            action_type: Type of action (email_send, linkedin_post, browser_action).
            target: Action target (email address, URL, etc.).
            content: Content of the action (email body, post text, etc.).
            parameters: Additional parameters (attachments, etc.).

        Returns:
            Tuple of (risk_level, list of risk factors).
        """
        parameters = parameters or {}
        risk_factors: list[str] = []
        word_count = len(content.split())

        # Browser automation is always high risk
        if action_type == 'browser_action':
            risk_factors.append('Browser automation requires human verification')
            return 'high', risk_factors

        # Email risk assessment
        if action_type == 'email_send':
            # Check if recipient is known
            if target and target.lower() not in {c.lower() for c in self._known_contacts}:
                risk_factors.append('Unknown recipient not in approved contacts list')

                # Unknown recipient with long email is high risk
                if word_count > 100:
                    return 'high', risk_factors

            # Check for attachments
            if parameters.get('attachments'):
                risk_factors.append('Attachment included')
                return 'high', risk_factors

            # Check content length
            if word_count > 100:
                risk_factors.append('Email exceeds 100 words')
                return 'medium', risk_factors

            # Known contact with short email is low risk
            if not risk_factors:
                return 'low', risk_factors

            return 'medium', risk_factors

        # LinkedIn post risk assessment
        if action_type == 'linkedin_post':
            text = parameters.get('text', content)
            char_count = len(text)

            if char_count > 500:
                risk_factors.append('Post exceeds 500 characters')
                return 'high', risk_factors

            if 'http' in text.lower() or 'https' in text.lower():
                risk_factors.append('Contains external links')

            if char_count > 200:
                risk_factors.append('Post exceeds 200 characters')
                return 'medium', risk_factors

            if risk_factors:
                return 'medium', risk_factors

            return 'low', risk_factors

        # Default to medium for unknown types
        risk_factors.append('Unknown action type, defaulting to medium risk')
        return 'medium', risk_factors

    def check_auto_approval(
        self,
        action_type: ActionType,
        risk_level: RiskLevel,
        target: str
    ) -> bool:
        """
        Check if action qualifies for auto-approval.

        Args:
            action_type: Type of action.
            risk_level: Assessed risk level.
            target: Action target.

        Returns:
            True if action can be auto-approved.
        """
        # Must have auto-approval enabled in config
        if not self.config.auto_approval_enabled:
            return False

        # Only low-risk actions can be auto-approved
        if risk_level != 'low':
            return False

        # Check handbook rules
        if not self._auto_approval_rules.get('enabled', False):
            return False

        # Email auto-approval
        if action_type == 'email_send':
            if self._auto_approval_rules.get('approved_contacts_auto'):
                if target.lower() in {c.lower() for c in self._known_contacts}:
                    return True

        # LinkedIn auto-approval
        if action_type == 'linkedin_post':
            if self._auto_approval_rules.get('linkedin_low_risk'):
                return True

        return False

    def create_approval_request(
        self,
        action_type: ActionType,
        target: str,
        content: str,
        source_action_item: str,
        parameters: dict[str, Any] | None = None,
        rationale: str = '',
        notes: str = ''
    ) -> tuple[Path | None, bool]:
        """
        Create an approval request for an external action.

        Args:
            action_type: Type of action (email_send, linkedin_post, browser_action).
            target: Action target (email, URL, etc.).
            content: Content of the action.
            source_action_item: Path to the original action item.
            parameters: Additional parameters for MCP tool.
            rationale: Why this action is recommended.
            notes: Additional notes for reviewer.

        Returns:
            Tuple of (path to approval file or None, is_auto_approved).
        """
        parameters = parameters or {}

        # Assess risk level
        risk_level, risk_factors = self.assess_risk_level(
            action_type, target, content, parameters
        )

        # Check for auto-approval
        is_auto_approved = self.check_auto_approval(
            action_type, risk_level, target
        )

        # Get MCP server and tool
        mcp_server, mcp_tool = self.MCP_SERVER_MAP.get(
            action_type, ('custom_mcp', 'custom_action')
        )

        # Create approval request
        approval_request = ApprovalRequest(
            action_type=action_type,
            target=target,
            risk_level=risk_level,
            rationale=rationale or f'Action detected in plan for {source_action_item}',
            source_action_item=source_action_item,
            mcp_server=mcp_server,
            mcp_tool=mcp_tool,
            parameters=parameters,
            risk_factors=risk_factors,
            notes=notes
        )

        # Handle auto-approval
        if is_auto_approved:
            approval_request.status = 'approved'
            approval_request.approver = 'system'
            approval_request.approval_timestamp = datetime.now()

            # Write to /Approved/ directly
            file_path = create_approval_file(
                approval_request,
                self.config.approved_path,
                dry_run=self.config.dry_run
            )

            # Log auto-approval
            if file_path:
                self.audit_logger.log_approval_workflow(
                    'approval_approved',
                    approval_request.id,
                    approver='system (auto)'
                )

            return file_path, True

        # Write to /Pending_Approval/
        file_path = create_approval_file(
            approval_request,
            self.config.pending_approval_path,
            dry_run=self.config.dry_run
        )

        # Log approval creation
        if file_path:
            self.audit_logger.log_approval_workflow(
                'approval_created',
                approval_request.id
            )

        return file_path, False

    def move_to_approved(self, approval_file: Path, approver: str = 'user') -> Path | None:
        """
        Move an approval request from /Pending_Approval/ to /Approved/.

        Args:
            approval_file: Path to the approval file in /Pending_Approval/.
            approver: Who approved (user, system, etc.).

        Returns:
            New path in /Approved/, or None if failed.
        """
        if not approval_file.exists():
            return None

        try:
            # Ensure /Approved/ exists
            self.config.approved_path.mkdir(parents=True, exist_ok=True)

            # Move file
            new_path = self.config.approved_path / approval_file.name
            shutil.move(str(approval_file), str(new_path))

            # Update approval timestamp in file content
            content = new_path.read_text(encoding='utf-8')
            now = datetime.now().isoformat()

            # Update status and timestamps in frontmatter
            content = re.sub(
                r'^status:\s*\w+',
                'status: approved',
                content,
                flags=re.MULTILINE
            )
            content = re.sub(
                r'^approval_timestamp:\s*null',
                f'approval_timestamp: {now}',
                content,
                flags=re.MULTILINE
            )
            content = re.sub(
                r'^approver:\s*null',
                f'approver: "{approver}"',
                content,
                flags=re.MULTILINE
            )

            new_path.write_text(content, encoding='utf-8')

            # Extract approval ID for logging
            id_match = re.search(r'^id:\s*"?([^"\n]+)"?', content, re.MULTILINE)
            if id_match:
                self.audit_logger.log_approval_workflow(
                    'approval_approved',
                    id_match.group(1),
                    approver=approver
                )

            return new_path

        except OSError:
            return None

    def move_to_rejected(
        self,
        approval_file: Path,
        reason: str = 'Manually rejected'
    ) -> Path | None:
        """
        Move an approval request to /Rejected/.

        Args:
            approval_file: Path to the approval file.
            reason: Rejection reason.

        Returns:
            New path in /Rejected/, or None if failed.
        """
        if not approval_file.exists():
            return None

        try:
            # Ensure /Rejected/ exists
            self.config.rejected_path.mkdir(parents=True, exist_ok=True)

            # Move file
            new_path = self.config.rejected_path / approval_file.name
            shutil.move(str(approval_file), str(new_path))

            # Update status in file content
            content = new_path.read_text(encoding='utf-8')
            content = re.sub(
                r'^status:\s*\w+',
                'status: rejected',
                content,
                flags=re.MULTILINE
            )

            # Add rejection note
            if '## Notes' in content:
                content = content.replace(
                    '## Notes\n',
                    f'## Notes\n\n**Rejection Reason**: {reason}\n'
                )

            new_path.write_text(content, encoding='utf-8')

            # Extract approval ID for logging
            id_match = re.search(r'^id:\s*"?([^"\n]+)"?', content, re.MULTILINE)
            if id_match:
                self.audit_logger.log_approval_workflow(
                    'approval_rejected',
                    id_match.group(1),
                    approver='user'
                )

            return new_path

        except OSError:
            return None
