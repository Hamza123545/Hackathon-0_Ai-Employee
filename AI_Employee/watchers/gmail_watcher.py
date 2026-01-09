"""
Gmail watcher for Bronze Tier Personal AI Employee.

Monitors a Gmail inbox for new emails and creates action items
in the Obsidian vault when emails are detected.
"""

import base64
import logging
import pickle
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..utils.config import Config
from ..models.action_item import ActionItem, create_action_file
from .base_watcher import BaseWatcher


# Gmail API scope - read-only access to email
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail inbox for new emails and creates action items.

    Uses the Gmail API to poll for new messages. Implements OAuth 2.0
    authentication with token persistence.

    Attributes:
        credentials_path: Path to the OAuth client secrets JSON file.
        token_path: Path to store the OAuth token.
        service: Gmail API service instance.
    """

    def __init__(self, config: Config):
        """
        Initialize the Gmail watcher.

        Args:
            config: Configuration object with vault paths and Gmail settings.

        Raises:
            FileNotFoundError: If credentials file is not found.
        """
        super().__init__(config)

        self.credentials_path = Path(config.gmail_credentials_path)
        self.token_path = self.credentials_path.parent / 'token.pickle'

        # Validate credentials file exists
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"Gmail credentials file not found: {self.credentials_path}\n"
                "Please download credentials.json from Google Cloud Console."
            )

        self.service = None
        self.logger.info(f"Gmail watcher initialized")
        self.logger.info(f"Credentials: {self.credentials_path}")

    def _authenticate(self) -> Credentials:
        """
        Authenticate with Gmail API using OAuth 2.0.

        Loads existing token from pickle file if available and valid.
        Otherwise, initiates OAuth flow to get new credentials.

        Returns:
            Valid Credentials object.
        """
        creds = None

        # Load existing token if available
        if self.token_path.exists():
            self.logger.debug(f"Loading token from {self.token_path}")
            try:
                with open(self.token_path, 'rb') as token_file:
                    creds = pickle.load(token_file)
            except (pickle.UnpicklingError, EOFError) as e:
                self.logger.warning(f"Invalid token file, will re-authenticate: {e}")
                creds = None

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing expired credentials...")
                try:
                    creds.refresh(Request())
                except Exception as e:
                    self.logger.warning(f"Failed to refresh credentials: {e}")
                    creds = None

            if not creds:
                self.logger.info("Starting OAuth flow...")
                self.logger.info("A browser window will open for authentication.")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path),
                    SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            self.logger.debug(f"Saving token to {self.token_path}")
            with open(self.token_path, 'wb') as token_file:
                pickle.dump(creds, token_file)

        return creds

    def _ensure_service(self) -> None:
        """Ensure Gmail API service is initialized."""
        if self.service is None:
            creds = self._authenticate()
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Gmail API service initialized")

    def check_for_updates(self) -> list[Any]:
        """
        Poll Gmail API for new messages in the inbox.

        Returns:
            List of email info dicts for new, unprocessed emails.
        """
        self._ensure_service()
        new_emails = []

        try:
            # List recent messages from inbox
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['INBOX'],
                maxResults=20  # Check last 20 messages
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                self.logger.debug("No messages in inbox")
                return []

            for msg_ref in messages:
                msg_id = msg_ref['id']

                # Check if already processed
                if self.tracker.is_processed(msg_id, 'gmail'):
                    continue

                # Fetch full message details
                try:
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg_id,
                        format='full'
                    ).execute()
                except HttpError as e:
                    self.logger.error(f"Failed to fetch message {msg_id}: {e}")
                    continue

                # Parse message headers
                headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}

                email_info = {
                    'id': msg_id,
                    'subject': headers.get('Subject', '(No Subject)'),
                    'from': headers.get('From', 'Unknown'),
                    'to': headers.get('To', ''),
                    'date': headers.get('Date', ''),
                    'snippet': message.get('snippet', ''),
                    'body': self._extract_body(message),
                    'labels': message.get('labelIds', [])
                }

                new_emails.append(email_info)
                self.logger.info(f"New email: {email_info['subject'][:50]}")

        except HttpError as e:
            self.logger.error(f"Gmail API error: {e}")
            if e.resp.status == 401:
                self.logger.error("Authentication expired. Delete token.pickle and restart.")
            raise

        return new_emails

    def create_action_file(self, item: Any) -> Path | None:
        """
        Create an action item file for an email.

        Args:
            item: Email info dict from check_for_updates().

        Returns:
            Path to the created action file, or None if skipped/failed.
        """
        email_info = item

        # Parse date if available
        original_date = ''
        if email_info['date']:
            try:
                parsed_date = parsedate_to_datetime(email_info['date'])
                original_date = parsed_date.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                original_date = email_info['date']

        # Determine priority based on subject keywords
        priority = self._determine_priority(
            email_info['subject'],
            email_info['from']
        )

        # Build content with body or snippet
        content = email_info['body'] if email_info['body'] else email_info['snippet']
        if len(content) > 2000:
            content = content[:2000] + "\n\n[Content truncated...]"

        # Create action item
        action_item = ActionItem(
            id=email_info['id'],
            source='gmail',
            title=email_info['subject'],
            created=datetime.now(),
            priority=priority,
            status='pending',
            tags=['email'],
            summary=email_info['snippet'][:200] if email_info['snippet'] else 'No preview available',
            from_address=email_info['from'],
            original_date=original_date,
            content_type='email',
            content=content,
            watcher_type='gmail'
        )

        # Write the action file
        result = create_action_file(
            action_item,
            self.config.needs_action_path,
            dry_run=self.config.dry_run
        )

        if result:
            # Mark as processed to prevent duplicates
            self.tracker.mark_processed(email_info['id'], 'gmail')
            self.logger.info(f"Created action file: {result.name}")

        return result

    def _extract_body(self, message: dict) -> str:
        """
        Extract the plain text body from an email message.

        Args:
            message: Full message object from Gmail API.

        Returns:
            Plain text body content.
        """
        payload = message.get('payload', {})

        # Handle simple messages
        if 'body' in payload and payload['body'].get('data'):
            return self._decode_base64(payload['body']['data'])

        # Handle multipart messages
        parts = payload.get('parts', [])
        for part in parts:
            mime_type = part.get('mimeType', '')

            if mime_type == 'text/plain':
                body_data = part.get('body', {}).get('data', '')
                if body_data:
                    return self._decode_base64(body_data)

            # Handle nested multipart
            if 'parts' in part:
                for subpart in part['parts']:
                    if subpart.get('mimeType') == 'text/plain':
                        body_data = subpart.get('body', {}).get('data', '')
                        if body_data:
                            return self._decode_base64(body_data)

        return ''

    @staticmethod
    def _decode_base64(data: str) -> str:
        """
        Decode base64url-encoded string.

        Args:
            data: Base64url-encoded string.

        Returns:
            Decoded string.
        """
        try:
            # Gmail uses URL-safe base64 encoding
            decoded = base64.urlsafe_b64decode(data.encode('UTF-8'))
            return decoded.decode('utf-8', errors='replace')
        except Exception:
            return ''

    @staticmethod
    def _determine_priority(subject: str, sender: str) -> str:
        """
        Determine email priority based on subject and sender.

        Args:
            subject: Email subject line.
            sender: Email sender address.

        Returns:
            Priority level: 'high', 'medium', 'low', or 'unknown'.
        """
        subject_lower = subject.lower()

        # High priority keywords
        high_keywords = ['urgent', 'asap', 'critical', 'emergency', 'immediate']
        for keyword in high_keywords:
            if keyword in subject_lower:
                return 'high'

        # Low priority indicators
        low_keywords = ['newsletter', 'unsubscribe', 'no-reply', 'noreply', 'digest']
        for keyword in low_keywords:
            if keyword in subject_lower or keyword in sender.lower():
                return 'low'

        # Default to medium
        return 'medium'
