"""
Credential sanitizer for Silver Tier Personal AI Employee.

Provides recursive sanitization of sensitive data (passwords, tokens, API keys)
for safe audit logging and approval requests.
"""

import re
from typing import Any


class CredentialSanitizer:
    """
    Recursively sanitizes sensitive data in dictionaries and lists.

    Detects and masks:
    - Keys matching SENSITIVE_KEYS patterns (password, token, api_key, etc.)
    - Values that look like tokens (long alphanumeric strings)

    Attributes:
        SENSITIVE_KEYS: List of key name patterns to redact.
        REDACTED_PLACEHOLDER: String used to replace sensitive values.
        MIN_TOKEN_LENGTH: Minimum length for token-like string detection.
    """

    SENSITIVE_KEYS: list[str] = [
        'password',
        'token',
        'api_key',
        'secret',
        'credential',
        'auth',
        'bearer',
        'smtp_password',
        'access_token',
        'refresh_token',
        'private_key',
        'client_secret',
        'authorization',
    ]

    REDACTED_PLACEHOLDER: str = '***REDACTED***'
    MIN_TOKEN_LENGTH: int = 30

    def __init__(
        self,
        sensitive_keys: list[str] | None = None,
        redacted_placeholder: str | None = None,
        min_token_length: int | None = None
    ):
        """
        Initialize the sanitizer with optional custom settings.

        Args:
            sensitive_keys: Custom list of sensitive key patterns.
            redacted_placeholder: Custom redaction placeholder.
            min_token_length: Minimum length for token detection.
        """
        if sensitive_keys is not None:
            self.SENSITIVE_KEYS = sensitive_keys
        if redacted_placeholder is not None:
            self.REDACTED_PLACEHOLDER = redacted_placeholder
        if min_token_length is not None:
            self.MIN_TOKEN_LENGTH = min_token_length

    def sanitize(self, data: Any) -> Any:
        """
        Recursively sanitize sensitive data.

        Args:
            data: Data to sanitize (dict, list, or primitive).

        Returns:
            Sanitized copy of the data with credentials masked.
        """
        if isinstance(data, dict):
            return self._sanitize_dict(data)
        elif isinstance(data, list):
            return self._sanitize_list(data)
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data

    def _sanitize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize a dictionary recursively.

        Args:
            data: Dictionary to sanitize.

        Returns:
            New dictionary with sensitive values masked.
        """
        sanitized: dict[str, Any] = {}

        for key, value in data.items():
            lower_key = key.lower()

            # Check if key contains any sensitive pattern
            if self._is_sensitive_key(lower_key):
                sanitized[key] = self.REDACTED_PLACEHOLDER
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = self._sanitize_list(value)
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_string(value)
            else:
                sanitized[key] = value

        return sanitized

    def _sanitize_list(self, data: list[Any]) -> list[Any]:
        """
        Sanitize a list recursively.

        Args:
            data: List to sanitize.

        Returns:
            New list with sensitive values masked.
        """
        return [self.sanitize(item) for item in data]

    def _sanitize_string(self, value: str) -> str:
        """
        Sanitize a string value if it looks like a token.

        Args:
            value: String value to check.

        Returns:
            Masked string if it looks like a token, original otherwise.
        """
        if self._looks_like_token(value):
            return self._mask_token(value)
        return value

    def _is_sensitive_key(self, key: str) -> bool:
        """
        Check if a key matches any sensitive pattern.

        Args:
            key: Lowercase key name to check.

        Returns:
            True if key contains a sensitive pattern.
        """
        return any(term in key for term in self.SENSITIVE_KEYS)

    def _looks_like_token(self, value: str) -> bool:
        """
        Detect if a string looks like a token or API key.

        Criteria:
        - Length >= MIN_TOKEN_LENGTH
        - Matches alphanumeric pattern with common token characters

        Args:
            value: String to check.

        Returns:
            True if the string looks like a token.
        """
        if len(value) < self.MIN_TOKEN_LENGTH:
            return False

        # Match patterns common in tokens: alphanumeric, +, /, =, _, -
        token_pattern = r'^[A-Za-z0-9+/=_\-]+$'
        return bool(re.match(token_pattern, value))

    def _mask_token(self, token: str) -> str:
        """
        Mask a token showing only first and last 4 characters.

        Args:
            token: Token string to mask.

        Returns:
            Masked token in format "{first4}...{last4}" or REDACTED
            for short tokens.
        """
        if len(token) <= 8:
            return self.REDACTED_PLACEHOLDER
        return f"{token[:4]}...{token[-4:]}"


# Module-level convenience function
def sanitize_credentials(data: Any) -> Any:
    """
    Convenience function to sanitize data using default settings.

    Args:
        data: Data to sanitize.

    Returns:
        Sanitized copy of the data.
    """
    sanitizer = CredentialSanitizer()
    return sanitizer.sanitize(data)
