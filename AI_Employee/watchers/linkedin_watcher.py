"""
LinkedIn watcher for Silver Tier Personal AI Employee.

Monitors LinkedIn for new messages and interactions using the
LinkedIn REST API v2 with OAuth2 authentication.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from ..utils.config import Config
from ..models.action_item import ActionItem, create_action_file
from .base_watcher import BaseWatcher


class LinkedInRateLimitError(Exception):
    """Raised when LinkedIn API rate limit is exceeded."""
    pass


class LinkedInAuthError(Exception):
    """Raised when LinkedIn API authentication fails."""
    pass


class LinkedInWatcher(BaseWatcher):
    """
    Watches LinkedIn for new messages and interactions.

    Uses the LinkedIn REST API v2 with OAuth2 bearer token authentication.
    Implements exponential backoff for rate limit handling.

    Attributes:
        access_token: LinkedIn OAuth2 access token.
        person_urn: LinkedIn person URN for the authenticated user.
        api_version: LinkedIn API version string (YYYYMM format).
        base_url: LinkedIn API base URL.
        last_check_ids: Set of activity IDs from last check (duplicate prevention).
    """

    BASE_URL = 'https://api.linkedin.com'
    API_VERSION = '202601'  # YYYYMM format

    # Rate limit settings
    MAX_RETRIES = 5
    INITIAL_BACKOFF = 1.0  # seconds
    MAX_BACKOFF = 16.0  # seconds

    def __init__(self, config: Config):
        """
        Initialize the LinkedIn watcher.

        Args:
            config: Configuration object with vault paths and LinkedIn settings.

        Raises:
            ValueError: If LINKEDIN_ACCESS_TOKEN is not configured.
        """
        super().__init__(config)

        self.access_token = config.linkedin_access_token
        self.person_urn = config.linkedin_person_urn

        if not self.access_token:
            raise ValueError(
                "LINKEDIN_ACCESS_TOKEN environment variable is required.\n"
                "Please configure your LinkedIn OAuth2 access token."
            )

        self.last_check_ids: set[str] = set()
        self._session = requests.Session()
        self._setup_session()

        self.logger.info("LinkedIn watcher initialized")
        self.logger.info(f"Person URN: {self.person_urn or 'Will fetch from API'}")

    def _setup_session(self) -> None:
        """Configure the requests session with authentication headers."""
        self._session.headers.update({
            'Authorization': f'Bearer {self.access_token}',
            'X-Restli-Protocol-Version': '2.0.0',
            'LinkedIn-Version': self.API_VERSION,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> requests.Response:
        """
        Make an API request with rate limit handling.

        Implements exponential backoff: 1s, 2s, 4s, 8s, 16s (max 5 retries).

        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint (relative to base URL).
            **kwargs: Additional arguments for requests.

        Returns:
            Response object.

        Raises:
            LinkedInRateLimitError: If rate limit persists after all retries.
            LinkedInAuthError: If authentication fails.
            requests.RequestException: For other request errors.
        """
        url = f"{self.BASE_URL}{endpoint}"
        backoff = self.INITIAL_BACKOFF

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = self._session.request(method, url, **kwargs)

                # Check for rate limit
                if response.status_code == 429:
                    if attempt == self.MAX_RETRIES:
                        self.logger.error(
                            f"Rate limit exceeded after {self.MAX_RETRIES} retries"
                        )
                        raise LinkedInRateLimitError(
                            "LinkedIn API rate limit exceeded. Try again later."
                        )

                    # Get retry-after header if available
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            wait_time = int(retry_after)
                        except ValueError:
                            wait_time = backoff
                    else:
                        wait_time = backoff

                    self.logger.warning(
                        f"Rate limited. Attempt {attempt}/{self.MAX_RETRIES}. "
                        f"Waiting {wait_time}s before retry..."
                    )
                    time.sleep(wait_time)
                    backoff = min(backoff * 2, self.MAX_BACKOFF)
                    continue

                # Check for auth errors
                if response.status_code == 401:
                    self.logger.error("LinkedIn authentication failed")
                    raise LinkedInAuthError(
                        "LinkedIn access token is invalid or expired. "
                        "Please refresh your OAuth2 token."
                    )

                if response.status_code == 403:
                    self.logger.error("LinkedIn permission denied")
                    raise LinkedInAuthError(
                        "LinkedIn API permission denied. "
                        "Check your app permissions and token scopes."
                    )

                # Return successful response
                return response

            except requests.RequestException as e:
                if attempt == self.MAX_RETRIES:
                    raise
                self.logger.warning(f"Request failed: {e}. Retrying...")
                time.sleep(backoff)
                backoff = min(backoff * 2, self.MAX_BACKOFF)

        # Should not reach here
        raise LinkedInRateLimitError("Request failed after all retries")

    def _get_profile(self) -> dict[str, Any]:
        """
        Fetch the authenticated user's profile.

        Returns:
            Profile data dict.
        """
        response = self._make_request('GET', '/v2/me')
        response.raise_for_status()
        return response.json()

    def _ensure_person_urn(self) -> None:
        """Ensure we have the person URN, fetching if needed."""
        if not self.person_urn:
            try:
                profile = self._get_profile()
                self.person_urn = f"urn:li:person:{profile.get('id', '')}"
                self.logger.info(f"Fetched person URN: {self.person_urn}")
            except Exception as e:
                self.logger.error(f"Failed to fetch profile: {e}")

    def check_for_updates(self) -> list[Any]:
        """
        Poll LinkedIn API for new interactions.

        Checks for:
        - New messages (if messaging API access is available)
        - Profile mentions and notifications

        Returns:
            List of interaction info dicts for new, unprocessed items.
        """
        self._ensure_person_urn()
        new_interactions = []

        # Check notifications/activities
        try:
            interactions = self._check_notifications()
            new_interactions.extend(interactions)
        except Exception as e:
            self.logger.error(f"Error checking notifications: {e}")

        # Check messages (requires specific API permissions)
        try:
            messages = self._check_messages()
            new_interactions.extend(messages)
        except LinkedInAuthError:
            # Messaging API might not be available
            self.logger.debug("Messaging API not available or not authorized")
        except Exception as e:
            self.logger.error(f"Error checking messages: {e}")

        return new_interactions

    def _check_notifications(self) -> list[dict[str, Any]]:
        """
        Check for new notifications/activities.

        Note: LinkedIn's notification API has limited access.
        This implementation provides a basic pattern that can be
        extended when proper API access is available.

        Returns:
            List of notification info dicts.
        """
        new_notifications = []

        try:
            # LinkedIn's activities endpoint (may require specific permissions)
            # For now, we'll do a basic profile check
            response = self._make_request(
                'GET',
                '/v2/me',
                params={'projection': '(id,firstName,lastName)'}
            )

            if response.status_code == 200:
                # Profile accessible - log success
                self.logger.debug("LinkedIn API accessible")

            # Note: Full notification polling requires LinkedIn Partner API
            # This is a placeholder for the pattern
            # Real implementation would use /v2/socialActions or similar

        except Exception as e:
            self.logger.debug(f"Notification check: {e}")

        return new_notifications

    def _check_messages(self) -> list[dict[str, Any]]:
        """
        Check for new LinkedIn messages.

        Note: LinkedIn messaging API requires specific partner permissions.
        This implementation provides the pattern for when access is available.

        Returns:
            List of message info dicts.
        """
        new_messages = []

        try:
            # LinkedIn messaging endpoint (requires r_messaging permission)
            response = self._make_request(
                'GET',
                '/v2/conversations',
                params={
                    'q': 'participants',
                    'recipients': self.person_urn
                }
            )

            if response.status_code == 200:
                data = response.json()
                conversations = data.get('elements', [])

                for conv in conversations:
                    conv_id = conv.get('id', '')

                    # Skip if already processed
                    if self.tracker.is_processed(conv_id, 'linkedin'):
                        continue

                    # Check for new messages in conversation
                    last_activity = conv.get('lastActivityAt', 0)

                    # Get last message preview
                    messages_response = self._make_request(
                        'GET',
                        f'/v2/conversations/{conv_id}/messages',
                        params={'count': 1}
                    )

                    if messages_response.status_code == 200:
                        msgs = messages_response.json().get('elements', [])
                        if msgs:
                            last_msg = msgs[0]

                            message_info = {
                                'id': f"linkedin-msg-{conv_id}-{last_activity}",
                                'conversation_id': conv_id,
                                'interaction_type': 'message',
                                'sender': self._get_sender_name(last_msg),
                                'content': last_msg.get('body', {}).get('text', ''),
                                'timestamp': self._format_timestamp(last_activity),
                                'detected_at': datetime.now()
                            }

                            new_messages.append(message_info)
                            self.logger.info(f"New LinkedIn message from: {message_info['sender']}")

        except LinkedInAuthError:
            # Messaging requires specific permissions
            raise
        except Exception as e:
            self.logger.debug(f"Message check: {e}")

        return new_messages

    def _get_sender_name(self, message: dict) -> str:
        """Extract sender name from message."""
        sender = message.get('from', {})
        member = sender.get('member', {})

        first_name = member.get('firstName', {}).get('localized', {})
        last_name = member.get('lastName', {}).get('localized', {})

        # Get first available locale
        first = next(iter(first_name.values()), '') if first_name else ''
        last = next(iter(last_name.values()), '') if last_name else ''

        return f"{first} {last}".strip() or 'Unknown'

    def _format_timestamp(self, epoch_ms: int) -> str:
        """Convert epoch milliseconds to formatted timestamp."""
        if not epoch_ms:
            return ''
        try:
            dt = datetime.fromtimestamp(epoch_ms / 1000)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, OSError):
            return ''

    def create_action_file(self, item: Any) -> Path | None:
        """
        Create an action item file for a LinkedIn interaction.

        Args:
            item: Interaction info dict from check_for_updates().

        Returns:
            Path to the created action file, or None if skipped/failed.
        """
        interaction = item
        interaction_type = interaction.get('interaction_type', 'notification')

        # Determine title based on type
        if interaction_type == 'message':
            title = f"LinkedIn Message: {interaction.get('sender', 'Unknown')}"
            tags = ['linkedin', 'message']
        elif interaction_type == 'comment':
            title = f"LinkedIn Comment: {interaction.get('sender', 'Unknown')}"
            tags = ['linkedin', 'comment']
        elif interaction_type == 'mention':
            title = f"LinkedIn Mention: {interaction.get('sender', 'Unknown')}"
            tags = ['linkedin', 'mention']
        else:
            title = f"LinkedIn: {interaction.get('sender', 'Notification')}"
            tags = ['linkedin', 'notification']

        # Create action item
        action_item = ActionItem(
            id=interaction['id'],
            source='linkedin',
            title=title,
            created=interaction['detected_at'],
            priority=self._determine_priority(interaction),
            status='pending',
            tags=tags,
            summary=f"New {interaction_type} from {interaction.get('sender', 'Unknown')}",
            from_address=interaction.get('sender', 'Unknown'),
            original_date=interaction.get('timestamp', ''),
            content_type=f'linkedin_{interaction_type}',
            content=self._format_content(interaction),
            watcher_type='linkedin'
        )

        # Write the action file
        result = create_action_file(
            action_item,
            self.config.needs_action_path,
            dry_run=self.config.dry_run
        )

        if result:
            # Mark as processed to prevent duplicates
            self.tracker.mark_processed(interaction['id'], 'linkedin')
            self.logger.info(f"Created action file: {result.name}")

        return result

    def _format_content(self, interaction: dict) -> str:
        """Format interaction content for display."""
        content = interaction.get('content', '')
        interaction_type = interaction.get('interaction_type', 'notification')
        sender = interaction.get('sender', 'Unknown')

        return f"""**Interaction Type**: {interaction_type.title()}
**From**: {sender}
**Received**: {interaction.get('timestamp', 'Unknown')}

## Content

{content if content else '_No content preview available_'}

---

*View on LinkedIn for full context*
"""

    @staticmethod
    def _determine_priority(interaction: dict) -> str:
        """
        Determine interaction priority.

        Args:
            interaction: Interaction info dict.

        Returns:
            Priority level: 'high', 'medium', or 'low'.
        """
        content = interaction.get('content', '').lower()
        interaction_type = interaction.get('interaction_type', '')

        # High priority keywords
        high_keywords = ['urgent', 'asap', 'important', 'opportunity', 'offer']
        for keyword in high_keywords:
            if keyword in content:
                return 'high'

        # Messages are generally higher priority than notifications
        if interaction_type == 'message':
            return 'medium'

        return 'low'


def main():
    """CLI entry point for LinkedIn watcher."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='LinkedIn Watcher for Personal AI Employee')
    parser.add_argument('--test', action='store_true', help='Test API connection')
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        config = Config()
        watcher = LinkedInWatcher(config)

        if args.test:
            print("Testing LinkedIn API connection...")
            try:
                profile = watcher._get_profile()
                print(f"Connected! Profile ID: {profile.get('id')}")
                print(f"Name: {profile.get('localizedFirstName', '')} {profile.get('localizedLastName', '')}")
            except Exception as e:
                print(f"Connection failed: {e}")
                sys.exit(1)
        else:
            watcher.run()

    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except LinkedInAuthError as e:
        print(f"\nAuthentication error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
