"""
Email MCP server for Silver Tier Personal AI Employee.

FastMCP server providing email sending capabilities via SMTP with TLS,
health checking, and robust error handling with exponential backoff retry.
"""

import os
import smtplib
import time
import uuid
from datetime import datetime, timezone
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path
from typing import Any, Literal

from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP(name="email-mcp")

# Error codes per contract
ErrorCode = Literal[
    'SMTP_AUTH_FAILED',
    'SMTP_CONNECTION_ERROR',
    'INVALID_RECIPIENT',
    'ATTACHMENT_TOO_LARGE',
    'UNKNOWN'
]


class EmailConfig:
    """Configuration for email server loaded from environment variables."""

    @property
    def smtp_host(self) -> str:
        return os.environ.get('SMTP_HOST', 'smtp.gmail.com')

    @property
    def smtp_port(self) -> int:
        return int(os.environ.get('SMTP_PORT', '587'))

    @property
    def smtp_username(self) -> str:
        return os.environ.get('SMTP_USERNAME', '')

    @property
    def smtp_password(self) -> str:
        return os.environ.get('SMTP_PASSWORD', '')

    @property
    def from_address(self) -> str:
        return os.environ.get('FROM_ADDRESS', '')

    @property
    def use_tls(self) -> bool:
        return os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'


config = EmailConfig()


def _retry_with_backoff(
    func,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 16.0,
    transient_exceptions: tuple = (smtplib.SMTPServerDisconnected, TimeoutError, ConnectionError)
) -> Any:
    """
    Execute function with exponential backoff retry for transient errors.

    Args:
        func: Callable to execute.
        max_attempts: Maximum retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        transient_exceptions: Exceptions that trigger retry.

    Returns:
        Result of successful function call.

    Raises:
        Last exception if all retries fail.
    """
    last_exception = None

    for attempt in range(max_attempts):
        try:
            return func()
        except transient_exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                delay = min(base_delay * (2 ** attempt), max_delay)
                time.sleep(delay)

    raise last_exception


def _classify_smtp_error(e: Exception) -> tuple[str, ErrorCode]:
    """
    Classify SMTP exception into error message and code.

    Args:
        e: The exception to classify.

    Returns:
        Tuple of (error_message, error_code).
    """
    error_str = str(e).lower()

    if isinstance(e, smtplib.SMTPAuthenticationError):
        return str(e), 'SMTP_AUTH_FAILED'
    elif isinstance(e, (smtplib.SMTPConnectError, ConnectionRefusedError, TimeoutError)):
        return str(e), 'SMTP_CONNECTION_ERROR'
    elif isinstance(e, smtplib.SMTPRecipientsRefused):
        return str(e), 'INVALID_RECIPIENT'
    elif 'authentication' in error_str or 'auth' in error_str:
        return str(e), 'SMTP_AUTH_FAILED'
    elif 'connect' in error_str or 'connection' in error_str:
        return str(e), 'SMTP_CONNECTION_ERROR'
    elif 'recipient' in error_str:
        return str(e), 'INVALID_RECIPIENT'
    else:
        return str(e), 'UNKNOWN'


def _check_attachment_size(attachments: list[dict[str, Any]] | None, max_size_mb: int = 25) -> tuple[bool, str]:
    """
    Check if total attachment size is within limits.

    Args:
        attachments: List of attachment dicts with 'path' key.
        max_size_mb: Maximum total size in MB.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not attachments:
        return True, ''

    total_size = 0
    max_bytes = max_size_mb * 1024 * 1024

    for attachment in attachments:
        path = Path(attachment.get('path', ''))
        if path.exists():
            total_size += path.stat().st_size

    if total_size > max_bytes:
        return False, f'Total attachment size ({total_size / 1024 / 1024:.1f}MB) exceeds limit ({max_size_mb}MB)'

    return True, ''


@mcp.tool
def send_email(
    to: str,
    subject: str,
    body: str,
    from_addr: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    attachments: list[dict[str, Any]] | None = None,
    is_html: bool = False
) -> dict[str, Any]:
    """
    Send an email via SMTP with TLS.

    Args:
        to: Recipient email address.
        subject: Email subject line (max 998 chars).
        body: Email body (plain text or HTML, max 50000 chars).
        from_addr: Sender email address (optional, uses default from config).
        cc: List of CC recipients.
        bcc: List of BCC recipients.
        attachments: List of attachment dicts with keys: filename, path, content_type (optional).
        is_html: Whether body is HTML (default: False).

    Returns:
        Dict with status, message_id, timestamp, or error details.
    """
    # Validate inputs
    if not to:
        return {
            'status': 'error',
            'error': 'Recipient email address is required',
            'error_code': 'INVALID_RECIPIENT'
        }

    # Check attachment size
    size_ok, size_error = _check_attachment_size(attachments)
    if not size_ok:
        return {
            'status': 'error',
            'error': size_error,
            'error_code': 'ATTACHMENT_TOO_LARGE'
        }

    # Build message
    sender = from_addr or config.from_address
    if not sender:
        return {
            'status': 'error',
            'error': 'Sender email address not configured',
            'error_code': 'UNKNOWN'
        }

    # Create message
    if attachments:
        msg = MIMEMultipart()
        body_part = MIMEText(body, 'html' if is_html else 'plain', 'utf-8')
        msg.attach(body_part)

        # Add attachments
        for attachment in attachments:
            path = Path(attachment.get('path', ''))
            if not path.exists():
                continue

            filename = attachment.get('filename', path.name)
            content_type = attachment.get('content_type', 'application/octet-stream')
            main_type, sub_type = content_type.split('/', 1) if '/' in content_type else ('application', 'octet-stream')

            with open(path, 'rb') as f:
                part = MIMEBase(main_type, sub_type)
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                msg.attach(part)
    else:
        msg = MIMEText(body, 'html' if is_html else 'plain', 'utf-8')

    msg['Subject'] = subject[:998]  # RFC 5322 limit
    msg['From'] = sender
    msg['To'] = to
    if cc:
        msg['Cc'] = ', '.join(cc)

    # Generate message ID
    message_id = f'<{uuid.uuid4()}@{sender.split("@")[-1] if "@" in sender else "localhost"}>'
    msg['Message-ID'] = message_id

    # Build recipient list
    all_recipients = [to]
    if cc:
        all_recipients.extend(cc)
    if bcc:
        all_recipients.extend(bcc)

    def do_send():
        """Inner function for retry wrapper."""
        with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as server:
            if config.use_tls:
                server.starttls()
            server.login(config.smtp_username, config.smtp_password)
            server.sendmail(sender, all_recipients, msg.as_string())

    try:
        _retry_with_backoff(do_send, max_attempts=3)

        return {
            'status': 'sent',
            'message_id': message_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    except smtplib.SMTPAuthenticationError as e:
        error_msg, error_code = _classify_smtp_error(e)
        return {
            'status': 'error',
            'error': error_msg,
            'error_code': error_code
        }

    except smtplib.SMTPRecipientsRefused as e:
        return {
            'status': 'error',
            'error': f'Recipients refused: {e.recipients}',
            'error_code': 'INVALID_RECIPIENT'
        }

    except Exception as e:
        error_msg, error_code = _classify_smtp_error(e)
        return {
            'status': 'error',
            'error': error_msg,
            'error_code': error_code
        }


@mcp.tool
def health_check() -> dict[str, Any]:
    """
    Check if SMTP server is reachable and credentials are valid.

    Returns:
        Dict with status, smtp_reachable, auth_valid, and checked_at timestamp.
    """
    result = {
        'status': 'error',
        'smtp_reachable': False,
        'auth_valid': False,
        'checked_at': datetime.now(timezone.utc).isoformat()
    }

    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=10) as server:
            result['smtp_reachable'] = True

            if config.use_tls:
                server.starttls()

            server.login(config.smtp_username, config.smtp_password)
            result['auth_valid'] = True
            result['status'] = 'available'

    except smtplib.SMTPAuthenticationError:
        result['smtp_reachable'] = True
        result['error'] = 'SMTP authentication failed'

    except (smtplib.SMTPConnectError, ConnectionRefusedError, TimeoutError) as e:
        result['error'] = f'Cannot connect to SMTP server: {e}'

    except Exception as e:
        result['error'] = str(e)

    return result


if __name__ == '__main__':
    mcp.run(transport='stdio')
