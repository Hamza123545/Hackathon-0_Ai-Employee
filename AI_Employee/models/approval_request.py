"""
Approval request model for Silver Tier Personal AI Employee.

Defines the ApprovalRequest dataclass and helper functions for creating
approval request files in the Obsidian vault.
"""

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal


ActionType = Literal['email_send', 'linkedin_post', 'browser_action', 'custom']
RiskLevel = Literal['low', 'medium', 'high']
StatusType = Literal['pending', 'approved', 'rejected', 'executed']


@dataclass
class ApprovalRequest:
    """
    Represents a proposed external action awaiting human approval.

    Attributes:
        id: Unique identifier (UUID v4).
        action_type: Type of action to perform.
        target: Action target (email address, URL, etc.).
        risk_level: Risk assessment level.
        rationale: Why this action is recommended.
        created_timestamp: When approval request was created.
        status: Current status in approval workflow.
        approval_timestamp: When approved/rejected (None if pending).
        approver: Who approved (user, auto, None if pending).
        execution_timestamp: When executed (None if not yet executed).
        source_action_item: Path to original action item file.
        mcp_server: Target MCP server name.
        mcp_tool: Specific MCP tool to invoke.
        parameters: Action parameters for MCP tool.
        risk_factors: List of risk factor descriptions.
        notes: Additional context or considerations.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: ActionType = 'custom'
    target: str = ''
    risk_level: RiskLevel = 'medium'
    rationale: str = ''
    created_timestamp: datetime = field(default_factory=datetime.now)
    status: StatusType = 'pending'
    approval_timestamp: datetime | None = None
    approver: str | None = None
    execution_timestamp: datetime | None = None
    source_action_item: str = ''
    mcp_server: str = ''
    mcp_tool: str = ''
    parameters: dict[str, Any] = field(default_factory=dict)
    risk_factors: list[str] = field(default_factory=list)
    notes: str = ''

    def to_frontmatter(self) -> str:
        """
        Generate YAML frontmatter string for the approval request.

        Returns:
            YAML frontmatter including opening/closing delimiters.
        """
        approval_ts = (
            self.approval_timestamp.isoformat()
            if self.approval_timestamp else 'null'
        )
        execution_ts = (
            self.execution_timestamp.isoformat()
            if self.execution_timestamp else 'null'
        )
        approver_val = f'"{self.approver}"' if self.approver else 'null'

        return f"""---
type: approval_request
id: "{self.id}"
action_type: {self.action_type}
target: "{self._escape_yaml_string(self.target)}"
risk_level: {self.risk_level}
rationale: "{self._escape_yaml_string(self.rationale)}"
created_timestamp: {self.created_timestamp.isoformat()}
status: {self.status}
approval_timestamp: {approval_ts}
approver: {approver_val}
execution_timestamp: {execution_ts}
source_action_item: "{self.source_action_item}"
mcp_server: "{self.mcp_server}"
mcp_tool: "{self.mcp_tool}"
---"""

    def to_body(self) -> str:
        """
        Generate Markdown body content for the approval request.

        Returns:
            Markdown formatted body content.
        """
        # Format parameters for display (sanitized already)
        params_display = '\n'.join(
            f"- **{key}**: {value}"
            for key, value in self.parameters.items()
        ) if self.parameters else '- No parameters'

        # Format risk factors
        risk_factors_display = '\n'.join(
            f"- {factor}"
            for factor in self.risk_factors
        ) if self.risk_factors else '- No specific risk factors identified'

        action_description = self._get_action_description()

        return f"""## Proposed Action

{action_description}

## Action Parameters

{params_display}

## Risk Assessment

**Risk Level**: {self.risk_level.upper()}

**Risk Factors**:
{risk_factors_display}

## Approval Instructions

**To APPROVE**: Move this file to `/Approved/`
**To REJECT**: Move this file to `/Rejected/`

## Notes

{self.notes if self.notes else 'No additional notes.'}

## Metadata

- **Source Action Item**: [[{self.source_action_item}]]
- **MCP Server**: {self.mcp_server}
- **MCP Tool**: {self.mcp_tool}
- **Created**: {self.created_timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""

    def _get_action_description(self) -> str:
        """
        Generate human-readable action description.

        Returns:
            Description of what the action will do.
        """
        if self.action_type == 'email_send':
            subject = self.parameters.get('subject', 'No subject')
            to = self.parameters.get('to', self.target)
            return f"Send an email to **{to}** with subject: *{subject}*"

        elif self.action_type == 'linkedin_post':
            text_preview = self.parameters.get('text', '')[:100]
            return f"Post to LinkedIn: *{text_preview}...*"

        elif self.action_type == 'browser_action':
            url = self.parameters.get('url', self.target)
            action = self.parameters.get('action_type', 'navigate')
            return f"Perform browser action **{action}** on: {url}"

        else:
            return f"Execute custom action: {self.rationale}"

    def to_markdown(self) -> str:
        """
        Generate complete Markdown file content.

        Returns:
            Complete Markdown with frontmatter and body.
        """
        return f"{self.to_frontmatter()}\n\n{self.to_body()}"

    def generate_filename(self) -> str:
        """
        Generate the filename for this approval request.

        Format: APPROVAL_{action_type}_{timestamp}.md

        Returns:
            The generated filename.
        """
        timestamp = self.created_timestamp.strftime('%Y%m%d-%H%M%S')
        return f"APPROVAL_{self.action_type}_{timestamp}.md"

    @staticmethod
    def _escape_yaml_string(text: str) -> str:
        """
        Escape special characters for YAML string values.

        Args:
            text: The text to escape.

        Returns:
            Escaped text safe for YAML.
        """
        return text.replace('\\', '\\\\').replace('"', '\\"')

    @staticmethod
    def _slugify(text: str, max_length: int = 30) -> str:
        """
        Convert text to a URL-friendly slug.

        Args:
            text: The text to slugify.
            max_length: Maximum length of the slug.

        Returns:
            A lowercase, hyphenated slug.
        """
        slug = text.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        if len(slug) > max_length:
            slug = slug[:max_length].rsplit('-', 1)[0]
        return slug or 'untitled'


def create_approval_file(
    approval_request: ApprovalRequest,
    pending_approval_path: Path,
    dry_run: bool = False
) -> Path | None:
    """
    Create an approval request file in the Pending_Approval folder.

    Args:
        approval_request: The ApprovalRequest to write.
        pending_approval_path: Path to the Pending_Approval folder.
        dry_run: If True, log instead of writing.

    Returns:
        Path to the created file, or None if dry_run or failed.
    """
    filename = approval_request.generate_filename()
    file_path = pending_approval_path / filename

    if dry_run:
        print(f"[DRY RUN] Would create: {file_path}")
        return None

    try:
        # Ensure directory exists
        pending_approval_path.mkdir(parents=True, exist_ok=True)

        # Write the file
        content = approval_request.to_markdown()
        file_path.write_text(content, encoding='utf-8')
        return file_path

    except OSError as e:
        print(f"Error creating approval file: {e}")
        return None


def create_linkedin_post_approval(
    post_text: str,
    hashtags: list[str] | None = None,
    visibility: str = 'PUBLIC',
    source_action_item: str = '',
    pending_approval_path: Path | None = None,
    auto_approval_enabled: bool = False,
    max_auto_approve_length: int = 200,
    dry_run: bool = False
) -> tuple[ApprovalRequest, Path | None]:
    """
    Create a LinkedIn post approval request with proper risk assessment.

    This function implements T053 requirements:
    - Creates APPROVAL_linkedin_post_{timestamp}.md in /Pending_Approval/
    - Includes commentary text, hashtags, visibility (PUBLIC)
    - Determines risk_level: low (if meets auto-approval threshold) or medium

    Args:
        post_text: The LinkedIn post content (max 280 chars recommended).
        hashtags: List of hashtags (without # symbol).
        visibility: Post visibility - 'PUBLIC' or 'CONNECTIONS'.
        source_action_item: Path to the original action item file.
        pending_approval_path: Path to Pending_Approval folder.
        auto_approval_enabled: Whether auto-approval is enabled.
        max_auto_approve_length: Max chars for auto-approval eligibility.
        dry_run: If True, don't write file.

    Returns:
        Tuple of (ApprovalRequest, created_file_path or None).
    """
    # Default hashtags from Company_Handbook.md
    if hashtags is None:
        hashtags = ['AI', 'Automation', 'Innovation']

    # Check if link is present
    has_link = 'http://' in post_text or 'https://' in post_text

    # Determine risk level based on Company_Handbook.md rules
    # Low: <200 chars, no links, matches approved topics
    # Medium: >=200 chars OR contains links
    text_length = len(post_text)
    is_low_risk = text_length < max_auto_approve_length and not has_link

    risk_level: RiskLevel = 'low' if is_low_risk else 'medium'

    # Build risk factors list
    risk_factors = []
    if text_length >= max_auto_approve_length:
        risk_factors.append(f"Content length ({text_length} chars) exceeds auto-approval threshold ({max_auto_approve_length})")
    if has_link:
        risk_factors.append("Contains external link - requires review")
    if not risk_factors:
        risk_factors.append("Meets all auto-approval criteria (short content, no links)")

    # Determine if auto-approvable
    auto_approvable = is_low_risk and auto_approval_enabled

    # Build full text with hashtags for MCP parameter
    hashtag_text = ' '.join(f'#{tag}' for tag in hashtags)
    full_post_text = f"{post_text}\n\n{hashtag_text}" if hashtag_text else post_text

    # Create the approval request
    approval = ApprovalRequest(
        action_type='linkedin_post',
        target='LinkedIn Profile',
        risk_level=risk_level,
        rationale=f"LinkedIn post ({text_length} chars) with {len(hashtags)} hashtags",
        source_action_item=source_action_item,
        mcp_server='linkedin-mcp',
        mcp_tool='create_post',
        parameters={
            'text': full_post_text,
            'visibility': visibility,
            'hashtags': hashtags,
            'content_preview': post_text[:100] + '...' if len(post_text) > 100 else post_text,
            'character_count': text_length,
            'has_link': has_link,
            'auto_approval_eligible': auto_approvable
        },
        risk_factors=risk_factors,
        notes=f"Character count: {text_length}/280\nAuto-approval eligible: {'Yes' if auto_approvable else 'No'}"
    )

    # Create file if path provided
    file_path = None
    if pending_approval_path:
        file_path = create_approval_file(
            approval,
            pending_approval_path,
            dry_run=dry_run
        )

    return approval, file_path


def parse_approval_file(file_path: Path) -> ApprovalRequest | None:
    """
    Parse an approval request file and return an ApprovalRequest object.

    Args:
        file_path: Path to the approval request Markdown file.

    Returns:
        ApprovalRequest object if successfully parsed, None otherwise.
    """
    try:
        content = file_path.read_text(encoding='utf-8')

        # Extract frontmatter
        frontmatter_match = re.match(
            r'^---\s*\n(.*?)\n---',
            content,
            re.DOTALL
        )
        if not frontmatter_match:
            return None

        frontmatter = frontmatter_match.group(1)

        # Parse YAML-like frontmatter manually (simple parsing)
        def extract_field(name: str, default: str = '') -> str:
            match = re.search(
                rf'^{name}:\s*["\']?([^"\'\n]*)["\']?',
                frontmatter,
                re.MULTILINE
            )
            return match.group(1).strip() if match else default

        # Parse timestamps
        created_ts_str = extract_field('created_timestamp')
        created_ts = (
            datetime.fromisoformat(created_ts_str)
            if created_ts_str and created_ts_str != 'null'
            else datetime.now()
        )

        approval_ts_str = extract_field('approval_timestamp')
        approval_ts = (
            datetime.fromisoformat(approval_ts_str)
            if approval_ts_str and approval_ts_str != 'null'
            else None
        )

        execution_ts_str = extract_field('execution_timestamp')
        execution_ts = (
            datetime.fromisoformat(execution_ts_str)
            if execution_ts_str and execution_ts_str != 'null'
            else None
        )

        approver = extract_field('approver')
        approver = approver if approver and approver != 'null' else None

        return ApprovalRequest(
            id=extract_field('id'),
            action_type=extract_field('action_type', 'custom'),  # type: ignore
            target=extract_field('target'),
            risk_level=extract_field('risk_level', 'medium'),  # type: ignore
            rationale=extract_field('rationale'),
            created_timestamp=created_ts,
            status=extract_field('status', 'pending'),  # type: ignore
            approval_timestamp=approval_ts,
            approver=approver,
            execution_timestamp=execution_ts,
            source_action_item=extract_field('source_action_item'),
            mcp_server=extract_field('mcp_server'),
            mcp_tool=extract_field('mcp_tool')
        )

    except (OSError, ValueError) as e:
        print(f"Error parsing approval file: {e}")
        return None
