"""
Audit logger for Silver Tier Personal AI Employee.

Provides structured logging of external actions to daily JSON files
with credential sanitization and atomic writes.
"""

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from .sanitizer import CredentialSanitizer


ActionType = Literal[
    'email_send',
    'linkedin_post',
    'browser_action',
    'watcher_detection',
    'approval_created',
    'approval_approved',
    'approval_rejected',
    'approval_executed',
    'custom'
]

ActorType = Literal['claude-code', 'user', 'system']

ApprovalStatus = Literal['approved', 'auto_approved', 'rejected', 'not_required']

ResultType = Literal['success', 'failure', 'partial']


class AuditLogger:
    """
    Logs external actions to daily JSON files with credential sanitization.

    Features:
    - Daily log files (/Logs/YYYY-MM-DD.json)
    - Atomic writes (temp file + rename)
    - Automatic credential sanitization
    - UUID v4 entry IDs for uniqueness
    - ISO 8601 timestamps in UTC

    Attributes:
        logs_path: Path to the Logs folder.
        sanitizer: CredentialSanitizer instance.
    """

    def __init__(
        self,
        logs_path: Path | str,
        sanitizer: CredentialSanitizer | None = None
    ):
        """
        Initialize the audit logger.

        Args:
            logs_path: Path to the Logs folder.
            sanitizer: Optional custom CredentialSanitizer instance.
        """
        self.logs_path = Path(logs_path)
        self.sanitizer = sanitizer or CredentialSanitizer()

        # Ensure Logs directory exists
        self.logs_path.mkdir(parents=True, exist_ok=True)

    def _get_log_file_path(self, date: datetime | None = None) -> Path:
        """
        Get the log file path for a given date.

        Args:
            date: Optional date for the log file. Defaults to today (UTC).

        Returns:
            Path to the log file.
        """
        if date is None:
            date = datetime.now(timezone.utc)
        filename = date.strftime('%Y-%m-%d') + '.json'
        return self.logs_path / filename

    def _load_log_entries(self, log_path: Path) -> list[dict[str, Any]]:
        """
        Load existing log entries from a file.

        Args:
            log_path: Path to the log file.

        Returns:
            List of existing entries, or empty list if file doesn't exist.
        """
        if not log_path.exists():
            return []

        try:
            content = log_path.read_text(encoding='utf-8')
            data = json.loads(content)
            return data.get('entries', [])
        except (json.JSONDecodeError, OSError):
            # If file is corrupted, start fresh
            return []

    def _write_log_atomically(
        self,
        log_path: Path,
        entries: list[dict[str, Any]]
    ) -> None:
        """
        Write log entries atomically using temp file + rename.

        Args:
            log_path: Path to the log file.
            entries: List of log entries to write.
        """
        data = {'entries': entries}

        # Write to temp file first
        temp_fd, temp_path = tempfile.mkstemp(
            suffix='.json',
            dir=str(self.logs_path)
        )

        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path_obj = Path(temp_path)
            temp_path_obj.replace(log_path)

        except Exception:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    def _create_entry(
        self,
        action_type: ActionType,
        actor: ActorType,
        target: str,
        parameters: dict[str, Any] | None = None,
        approval_status: ApprovalStatus = 'not_required',
        approval_by: str | None = None,
        approval_timestamp: datetime | None = None,
        mcp_server: str | None = None,
        result: ResultType = 'success',
        result_details: str | None = None,
        error: str | None = None,
        error_code: str | None = None,
        execution_duration_ms: int | None = None,
        approval_request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        extra_fields: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Create a sanitized log entry.

        Args:
            action_type: Type of action performed.
            actor: Who/what initiated the action.
            target: Action target (email, URL, etc.).
            parameters: Action parameters (will be sanitized).
            approval_status: Approval workflow status.
            approval_by: Who approved the action.
            approval_timestamp: When approval was granted.
            mcp_server: Which MCP server executed the action.
            result: Execution result.
            result_details: Human-readable result description.
            error: Error message if failed.
            error_code: Machine-readable error code.
            execution_duration_ms: Execution time in milliseconds.
            approval_request_id: UUID of the approval request.
            metadata: Additional context.
            extra_fields: Additional fields to include.

        Returns:
            Sanitized log entry dict.
        """
        now = datetime.now(timezone.utc)

        # Sanitize parameters
        sanitized_params = {}
        if parameters:
            sanitized_params = self.sanitizer.sanitize(parameters)

        # Sanitize metadata
        sanitized_metadata = {}
        if metadata:
            sanitized_metadata = self.sanitizer.sanitize(metadata)

        entry: dict[str, Any] = {
            'entry_id': str(uuid.uuid4()),
            'timestamp': now.isoformat(),
            'action_type': action_type,
            'actor': actor,
            'target': target,
            'parameters': sanitized_params,
            'approval_status': approval_status,
            'approval_by': approval_by,
            'approval_timestamp': (
                approval_timestamp.isoformat()
                if approval_timestamp else None
            ),
            'result': result,
            'result_details': result_details,
            'error': error,
            'error_code': error_code,
            'mcp_server': mcp_server,
            'execution_duration_ms': execution_duration_ms,
            'approval_request_id': approval_request_id,
            'metadata': sanitized_metadata or {
                'user_agent': 'claude-code/1.0',
                'platform': 'silver-v1.0'
            }
        }

        # Add any extra fields
        if extra_fields:
            entry.update(self.sanitizer.sanitize(extra_fields))

        return entry

    def log_execution(
        self,
        action_type: ActionType,
        actor: ActorType,
        target: str,
        parameters: dict[str, Any] | None = None,
        approval_status: ApprovalStatus = 'approved',
        approval_by: str | None = None,
        approval_timestamp: datetime | None = None,
        mcp_server: str | None = None,
        result: ResultType = 'success',
        result_details: str | None = None,
        error: str | None = None,
        error_code: str | None = None,
        execution_duration_ms: int | None = None,
        approval_request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        extra_fields: dict[str, Any] | None = None
    ) -> str:
        """
        Log an external action execution.

        This is the primary method for logging MCP server executions.

        Args:
            action_type: Type of action performed.
            actor: Who/what initiated the action.
            target: Action target (email, URL, etc.).
            parameters: Action parameters (will be sanitized).
            approval_status: Approval workflow status.
            approval_by: Who approved the action.
            approval_timestamp: When approval was granted.
            mcp_server: Which MCP server executed the action.
            result: Execution result.
            result_details: Human-readable result description.
            error: Error message if failed.
            error_code: Machine-readable error code.
            execution_duration_ms: Execution time in milliseconds.
            approval_request_id: UUID of the approval request.
            metadata: Additional context.
            extra_fields: Additional fields to include.

        Returns:
            The entry_id of the logged entry.
        """
        entry = self._create_entry(
            action_type=action_type,
            actor=actor,
            target=target,
            parameters=parameters,
            approval_status=approval_status,
            approval_by=approval_by,
            approval_timestamp=approval_timestamp,
            mcp_server=mcp_server,
            result=result,
            result_details=result_details,
            error=error,
            error_code=error_code,
            execution_duration_ms=execution_duration_ms,
            approval_request_id=approval_request_id,
            metadata=metadata,
            extra_fields=extra_fields
        )

        # Validate entry before writing
        is_valid, validation_errors = self.validate_entry(entry)
        if not is_valid:
            raise ValueError(
                f"Invalid audit log entry: {', '.join(validation_errors)}"
            )

        log_path = self._get_log_file_path()
        entries = self._load_log_entries(log_path)
        entries.append(entry)
        self._write_log_atomically(log_path, entries)

        return entry['entry_id']

    def log_watcher_activity(
        self,
        watcher_type: str,
        items_detected: int,
        last_check_time: datetime | None = None,
        result: ResultType = 'success',
        error: str | None = None
    ) -> str:
        """
        Log watcher detection activity.

        Args:
            watcher_type: Type of watcher (gmail, whatsapp, linkedin).
            items_detected: Number of items detected in this cycle.
            last_check_time: When the check occurred.
            result: Execution result.
            error: Error message if failed.

        Returns:
            The entry_id of the logged entry.
        """
        return self.log_execution(
            action_type='watcher_detection',
            actor='system',
            target=watcher_type,
            parameters={
                'watcher_type': watcher_type,
                'items_detected': items_detected,
                'last_check_time': (
                    last_check_time.isoformat()
                    if last_check_time
                    else datetime.now(timezone.utc).isoformat()
                )
            },
            approval_status='not_required',
            result=result,
            error=error
        )

    def log_approval_workflow(
        self,
        action_type: Literal[
            'approval_created',
            'approval_approved',
            'approval_rejected'
        ],
        approval_request_id: str,
        approver: str | None = None
    ) -> str:
        """
        Log approval workflow state transitions.

        Args:
            action_type: Type of approval action.
            approval_request_id: UUID of the approval request.
            approver: Who approved/rejected (user, auto, system).

        Returns:
            The entry_id of the logged entry.
        """
        return self.log_execution(
            action_type=action_type,
            actor='system',
            target=approval_request_id,
            parameters={'approval_request_id': approval_request_id},
            approval_status='not_required',
            approval_by=approver,
            approval_timestamp=datetime.now(timezone.utc),
            approval_request_id=approval_request_id
        )

    def get_entries(
        self,
        date: datetime | None = None,
        limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Get log entries for a given date.

        Args:
            date: Date to get entries for. Defaults to today (UTC).
            limit: Maximum number of entries to return (most recent).

        Returns:
            List of log entries.
        """
        log_path = self._get_log_file_path(date)
        entries = self._load_log_entries(log_path)

        if limit:
            return entries[-limit:]
        return entries

    def count_entries_by_action_type(
        self,
        action_type: ActionType,
        date: datetime | None = None
    ) -> int:
        """
        Count entries of a specific action type for a given date.

        Args:
            action_type: Type of action to count.
            date: Date to count entries for. Defaults to today.

        Returns:
            Number of entries matching the action type.
        """
        entries = self.get_entries(date)
        return sum(1 for e in entries if e.get('action_type') == action_type)

    def validate_entry(self, entry: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate an audit log entry against required schema.

        Checks:
        - All required fields present (timestamp, action_type, actor, target, approval_status, result)
        - entry_id is valid UUID v4
        - timestamp is valid ISO 8601 format
        - action_type is valid enum value
        - actor is valid enum value
        - approval_status is valid enum value
        - result is valid enum value

        Args:
            entry: Log entry dict to validate.

        Returns:
            Tuple of (is_valid, list_of_errors).
        """
        errors: list[str] = []
        required_fields = [
            'timestamp', 'action_type', 'actor', 'target',
            'approval_status', 'result'
        ]

        # Check required fields
        for field in required_fields:
            if field not in entry:
                errors.append(f"Missing required field: {field}")

        # Validate entry_id is UUID v4
        entry_id = entry.get('entry_id', '')
        if entry_id:
            try:
                uuid.UUID(entry_id, version=4)
            except (ValueError, TypeError):
                errors.append(f"Invalid entry_id format (must be UUID v4): {entry_id}")

        # Validate timestamp is ISO 8601
        timestamp = entry.get('timestamp', '')
        if timestamp:
            try:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                errors.append(f"Invalid timestamp format (must be ISO 8601): {timestamp}")

        # Validate action_type enum
        valid_action_types = [
            'email_send', 'linkedin_post', 'browser_action',
            'watcher_detection', 'approval_created', 'approval_approved',
            'approval_rejected', 'approval_executed', 'custom'
        ]
        action_type = entry.get('action_type', '')
        if action_type and action_type not in valid_action_types:
            errors.append(f"Invalid action_type (must be one of {valid_action_types}): {action_type}")

        # Validate actor enum
        valid_actors = ['claude-code', 'user', 'system']
        actor = entry.get('actor', '')
        if actor and actor not in valid_actors:
            errors.append(f"Invalid actor (must be one of {valid_actors}): {actor}")

        # Validate approval_status enum
        valid_approval_statuses = ['approved', 'auto_approved', 'rejected', 'not_required']
        approval_status = entry.get('approval_status', '')
        if approval_status and approval_status not in valid_approval_statuses:
            errors.append(
                f"Invalid approval_status (must be one of {valid_approval_statuses}): {approval_status}"
            )

        # Validate result enum
        valid_results = ['success', 'failure', 'partial']
        result = entry.get('result', '')
        if result and result not in valid_results:
            errors.append(f"Invalid result (must be one of {valid_results}): {result}")

        return len(errors) == 0, errors

    def cleanup_old_logs(
        self,
        retention_days: int = 90,
        archive: bool = True
    ) -> dict[str, Any]:
        """
        Clean up audit logs older than retention period.

        Args:
            retention_days: Number of days to retain logs (default: 90).
            archive: If True, compress old logs to .gz before deleting.

        Returns:
            Dict with cleanup statistics: files_archived, files_deleted, total_size_freed.
        """
        import gzip
        import shutil
        from datetime import timedelta

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        stats = {
            'files_archived': 0,
            'files_deleted': 0,
            'total_size_freed': 0
        }

        if not self.logs_path.exists():
            return stats

        # Find all log files
        for log_file in self.logs_path.glob('*.json'):
            # Skip if already archived
            if log_file.name.endswith('.gz'):
                continue

            # Parse date from filename (YYYY-MM-DD.json)
            try:
                date_str = log_file.stem
                file_date = datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)

                # Check if file is older than retention period
                if file_date < cutoff_date:
                    file_size = log_file.stat().st_size

                    if archive:
                        # Compress to .gz
                        gz_path = log_file.with_suffix('.json.gz')
                        try:
                            with open(log_file, 'rb') as f_in:
                                with gzip.open(gz_path, 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                            log_file.unlink()  # Delete original after compression
                            stats['files_archived'] += 1
                            stats['total_size_freed'] += file_size
                        except OSError as e:
                            # If compression fails, just delete
                            log_file.unlink()
                            stats['files_deleted'] += 1
                            stats['total_size_freed'] += file_size
                    else:
                        # Delete without archiving
                        log_file.unlink()
                        stats['files_deleted'] += 1
                        stats['total_size_freed'] += file_size

            except (ValueError, OSError):
                # Skip files that don't match date pattern or can't be processed
                continue

        return stats