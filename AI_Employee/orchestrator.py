"""
Approval Orchestrator for Silver Tier Personal AI Employee.

Monitors the /Approved/ folder for approved action requests and
coordinates their execution via MCP servers. Implements the
Human-in-the-Loop (HITL) workflow execution phase.

Features:
- Polls /Approved/ folder every 60 seconds
- Validates approval request files
- Checks for expiration (24-hour timeout)
- Handles malformed files gracefully
- Logs all actions to audit log
- Monitors /Rejected/ for rejection logging
"""

import logging
import re
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .models.approval_request import ApprovalRequest, parse_approval_file
from .utils.audit_logger import AuditLogger
from .utils.config import Config


class ApprovalOrchestrator:
    """
    Orchestrates the approval workflow for external actions.

    Monitors the /Approved/ folder for approved requests and
    validates them before execution. Also monitors /Rejected/
    for rejection logging.

    Attributes:
        config: Configuration object with vault paths.
        audit_logger: AuditLogger for logging all actions.
        logger: Python logger for operational logging.
        running: Flag to control the main loop.
        check_interval: Seconds between folder checks.
        expiration_hours: Hours before approval expires (default 24).
    """

    # Required fields for valid approval request
    REQUIRED_FIELDS = [
        'action_type', 'target', 'mcp_server', 'created_timestamp'
    ]

    # Valid action types
    VALID_ACTION_TYPES = ['email_send', 'linkedin_post', 'browser_action', 'custom']

    def __init__(
        self,
        config: Config,
        check_interval: int | None = None,
        expiration_hours: int = 24
    ):
        """
        Initialize the approval orchestrator.

        Args:
            config: Configuration object with vault paths.
            check_interval: Seconds between checks (default from config).
            expiration_hours: Hours before approval expires (default 24).
        """
        self.config = config
        self.check_interval = check_interval or config.approval_check_interval
        self.expiration_hours = expiration_hours
        self.running = False

        self.audit_logger = AuditLogger(config.logs_path)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Track processed files to avoid re-processing
        self._processed_files: set[str] = set()
        self._rejected_files: set[str] = set()

        # Ensure folders exist
        config.ensure_vault_structure(include_silver=True)

        self.logger.info("ApprovalOrchestrator initialized")
        self.logger.info(f"Check interval: {self.check_interval}s")
        self.logger.info(f"Expiration: {self.expiration_hours} hours")

    def run(self) -> None:
        """
        Main loop: poll /Approved/ and /Rejected/ folders.

        Runs indefinitely until stopped. Each cycle:
        1. Scans /Approved/ for new files
        2. Validates and processes approved requests
        3. Checks /Pending_Approval/ for expired requests
        4. Scans /Rejected/ for rejection logging
        5. Sleeps for check_interval seconds
        """
        self.running = True
        self.logger.info("Starting ApprovalOrchestrator...")

        try:
            while self.running:
                try:
                    # Process approved files
                    self._process_approved_folder()

                    # Check for expired pending approvals
                    self._check_expired_approvals()

                    # Log any new rejections
                    self._process_rejected_folder()

                except Exception as e:
                    self.logger.error(f"Error in orchestrator cycle: {e}")

                # Sleep until next check
                self.logger.debug(f"Sleeping for {self.check_interval}s...")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the orchestrator gracefully."""
        self.running = False
        self.logger.info("ApprovalOrchestrator stopped")

    def _process_approved_folder(self) -> None:
        """Scan and process files in /Approved/ folder."""
        approved_path = self.config.approved_path
        if not approved_path.exists():
            return

        for file_path in approved_path.glob('*.md'):
            # Skip already processed files
            if file_path.name in self._processed_files:
                continue

            self.logger.info(f"Processing approved file: {file_path.name}")

            try:
                result = self.process_approved_file(file_path)
                if result:
                    self._processed_files.add(file_path.name)
            except Exception as e:
                self.logger.error(f"Error processing {file_path.name}: {e}")

    def process_approved_file(self, file_path: Path) -> bool:
        """
        Process a single approved request file.

        Validates the file, checks expiration, and prepares for execution.
        Does NOT execute the action - that's done by execute-approved-actions skill.

        Args:
            file_path: Path to the approval file in /Approved/.

        Returns:
            True if file is valid and ready for execution, False otherwise.
        """
        # Validate file structure
        validation_errors = self._validate_approval_file(file_path)
        if validation_errors:
            self.logger.warning(
                f"Malformed approval file: {file_path.name} - {validation_errors}"
            )
            self._move_to_rejected(
                file_path,
                reason=f"Validation errors: {'; '.join(validation_errors)}"
            )
            return False

        # Parse the approval request
        approval = parse_approval_file(file_path)
        if not approval:
            self.logger.error(f"Failed to parse approval file: {file_path.name}")
            self._move_to_rejected(file_path, reason="Failed to parse file")
            return False

        # Check expiration
        if self._is_expired(approval):
            self.logger.warning(f"Approval expired: {file_path.name}")
            self._move_to_rejected(
                file_path,
                reason=f"Expired (created {approval.created_timestamp.isoformat()})"
            )
            return False

        self.logger.info(
            f"Approved request ready: {approval.action_type} -> {approval.target}"
        )
        return True

    def _validate_approval_file(self, file_path: Path) -> list[str]:
        """
        Validate an approval request file structure.

        Checks:
        - File can be read
        - Has valid YAML frontmatter
        - Contains all required fields
        - Action type is valid

        Args:
            file_path: Path to the approval file.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: list[str] = []

        try:
            content = file_path.read_text(encoding='utf-8')
        except OSError as e:
            return [f"Cannot read file: {e}"]

        # Check for YAML frontmatter
        frontmatter_match = re.match(
            r'^---\s*\n(.*?)\n---',
            content,
            re.DOTALL
        )
        if not frontmatter_match:
            return ["Missing or invalid YAML frontmatter"]

        frontmatter = frontmatter_match.group(1)

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            pattern = rf'^{field}:\s*\S+'
            if not re.search(pattern, frontmatter, re.MULTILINE):
                errors.append(f"Missing required field: {field}")

        # Check action type is valid
        action_match = re.search(r'^action_type:\s*(\w+)', frontmatter, re.MULTILINE)
        if action_match:
            action_type = action_match.group(1)
            if action_type not in self.VALID_ACTION_TYPES:
                errors.append(f"Invalid action_type: {action_type}")

        # Check type field is approval_request
        type_match = re.search(r'^type:\s*(\w+)', frontmatter, re.MULTILINE)
        if type_match:
            if type_match.group(1) != 'approval_request':
                errors.append("File type is not 'approval_request'")
        else:
            errors.append("Missing type field")

        return errors

    def _is_expired(self, approval: ApprovalRequest) -> bool:
        """
        Check if an approval request has expired.

        Args:
            approval: Parsed ApprovalRequest object.

        Returns:
            True if expired (older than expiration_hours).
        """
        expiration_time = approval.created_timestamp + timedelta(
            hours=self.expiration_hours
        )
        return datetime.now() > expiration_time

    def _check_expired_approvals(self) -> None:
        """Check /Pending_Approval/ for expired requests and move them."""
        pending_path = self.config.pending_approval_path
        if not pending_path.exists():
            return

        now = datetime.now()
        expiration_delta = timedelta(hours=self.expiration_hours)

        for file_path in pending_path.glob('*.md'):
            try:
                approval = parse_approval_file(file_path)
                if approval and self._is_expired(approval):
                    self.logger.warning(
                        f"Pending approval expired: {file_path.name}"
                    )
                    self._move_to_rejected(
                        file_path,
                        reason=f"Expired after {self.expiration_hours} hours without approval"
                    )
            except Exception as e:
                self.logger.debug(f"Error checking expiration for {file_path.name}: {e}")

    def _process_rejected_folder(self) -> None:
        """
        Scan /Rejected/ folder for new rejections and log them.

        This handles cases where a user manually moves a file to /Rejected/.
        """
        rejected_path = self.config.rejected_path
        if not rejected_path.exists():
            return

        for file_path in rejected_path.glob('*.md'):
            # Skip already logged rejections
            if file_path.name in self._rejected_files:
                continue

            # Log the rejection
            try:
                approval = parse_approval_file(file_path)
                if approval:
                    self.audit_logger.log_approval_workflow(
                        'approval_rejected',
                        approval.id,
                        approver='user'
                    )
                    self.logger.info(f"Logged rejection: {file_path.name}")

                self._rejected_files.add(file_path.name)

            except Exception as e:
                self.logger.debug(f"Error logging rejection {file_path.name}: {e}")
                self._rejected_files.add(file_path.name)

    def _move_to_rejected(self, file_path: Path, reason: str) -> Path | None:
        """
        Move a file to /Rejected/ folder with rejection note.

        Args:
            file_path: Path to the file to reject.
            reason: Rejection reason to add to notes.

        Returns:
            New path in /Rejected/, or None if failed.
        """
        try:
            # Ensure /Rejected/ exists
            self.config.rejected_path.mkdir(parents=True, exist_ok=True)

            # Read and update content
            content = file_path.read_text(encoding='utf-8')

            # Update status to rejected
            content = re.sub(
                r'^status:\s*\w+',
                'status: rejected',
                content,
                flags=re.MULTILINE
            )

            # Add rejection note
            rejection_note = (
                f"\n\n**Rejection Reason**: {reason}\n"
                f"**Rejected At**: {datetime.now().isoformat()}\n"
            )

            if '## Notes' in content:
                content = content.replace('## Notes\n', f'## Notes{rejection_note}')
            else:
                content += f"\n## Notes{rejection_note}"

            # Move file
            new_path = self.config.rejected_path / file_path.name
            file_path.unlink()  # Remove original
            new_path.write_text(content, encoding='utf-8')

            # Log rejection
            id_match = re.search(r'^id:\s*"?([^"\n]+)"?', content, re.MULTILINE)
            if id_match:
                self.audit_logger.log_approval_workflow(
                    'approval_rejected',
                    id_match.group(1),
                    approver='system'
                )

            self._rejected_files.add(new_path.name)
            self.logger.info(f"Moved to rejected: {new_path.name}")

            return new_path

        except OSError as e:
            self.logger.error(f"Failed to move to rejected: {e}")
            return None

    def get_pending_approval_stats(self) -> dict[str, Any]:
        """
        Get statistics about pending approvals.

        Returns:
            Dict with count, oldest_age_hours, is_overdue.
        """
        pending_path = self.config.pending_approval_path
        if not pending_path.exists():
            return {
                'count': 0,
                'oldest_age_hours': 0,
                'is_overdue': False
            }

        files = list(pending_path.glob('*.md'))
        count = len(files)

        if count == 0:
            return {
                'count': 0,
                'oldest_age_hours': 0,
                'is_overdue': False
            }

        # Find oldest file
        oldest_mtime = min(f.stat().st_mtime for f in files)
        oldest_dt = datetime.fromtimestamp(oldest_mtime)
        age_hours = (datetime.now() - oldest_dt).total_seconds() / 3600

        return {
            'count': count,
            'oldest_age_hours': age_hours,
            'is_overdue': age_hours >= self.expiration_hours
        }


def main():
    """CLI entry point for ApprovalOrchestrator."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Approval Orchestrator for Personal AI Employee'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )
    parser.add_argument(
        '--expiration',
        type=int,
        default=24,
        help='Expiration time in hours (default: 24)'
    )
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        config = Config()
        orchestrator = ApprovalOrchestrator(
            config,
            check_interval=args.interval,
            expiration_hours=args.expiration
        )
        orchestrator.run()

    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == '__main__':
    main()
