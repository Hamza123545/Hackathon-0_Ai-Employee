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
