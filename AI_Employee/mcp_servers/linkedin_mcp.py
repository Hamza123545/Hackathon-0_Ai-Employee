"""
LinkedIn MCP server for Silver Tier Personal AI Employee.

FastMCP server providing LinkedIn posting capabilities via REST API v2,
health checking, and rate limit handling with retry queue.
"""

import os
import time
from datetime import datetime, timezone
from typing import Any, Literal

import requests
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP(name="linkedin-mcp")

# Error codes per contract
ErrorCode = Literal[
    'AUTH_EXPIRED',
    'RATE_LIMIT_EXCEEDED',
    'INVALID_CONTENT',
    'NETWORK_ERROR',
    'UNKNOWN'
]


class LinkedInConfig:
    """Configuration for LinkedIn API loaded from environment variables."""

    @property
    def access_token(self) -> str:
        return os.environ.get('LINKEDIN_ACCESS_TOKEN', '')

    @property
    def person_urn(self) -> str:
        return os.environ.get('LINKEDIN_PERSON_URN', '')

    @property
    def api_base_url(self) -> str:
        return os.environ.get('LINKEDIN_API_BASE_URL', 'https://api.linkedin.com/rest')

    @property
    def api_version(self) -> str:
        # Format: YYYYMM (e.g., 202601 for January 2026)
        return os.environ.get('LINKEDIN_API_VERSION', '202601')

    def get_headers(self) -> dict[str, str]:
        """Get headers required for LinkedIn API v2 requests."""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'X-Restli-Protocol-Version': '2.0.0',
            'LinkedIn-Version': self.api_version,
            'Content-Type': 'application/json'
        }


config = LinkedInConfig()

# Rate limit tracking
_last_post_time: float = 0
_post_delay_seconds: float = 5.0  # Configurable delay between posts


class RateLimitHandler:
    """Handles rate limiting with exponential backoff retry."""

    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 16.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retry_after: float | None = None

    def should_retry(self, response: requests.Response, attempt: int) -> bool:
        """Check if request should be retried based on response."""
        if attempt >= self.max_retries:
            return False

        if response.status_code == 429:
            # Get retry-after header if present
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                self.retry_after = float(retry_after)
            else:
                self.retry_after = min(
                    self.base_delay * (2 ** attempt),
                    self.max_delay
                )
            return True

        return False

    def wait_for_retry(self, attempt: int) -> None:
        """Wait before retrying request."""
        delay = self.retry_after or min(
            self.base_delay * (2 ** attempt),
            self.max_delay
        )
        time.sleep(delay)
        self.retry_after = None


def _classify_linkedin_error(response: requests.Response) -> tuple[str, ErrorCode]:
    """
    Classify LinkedIn API error response into error message and code.

    Args:
        response: The requests Response object.

    Returns:
        Tuple of (error_message, error_code).
    """
    status_code = response.status_code

    try:
        error_data = response.json()
        error_msg = error_data.get('message', error_data.get('error', str(response.text)))
    except Exception:
        error_msg = response.text[:500] if response.text else f'HTTP {status_code}'

    if status_code == 401:
        return error_msg, 'AUTH_EXPIRED'
    elif status_code == 403:
        return error_msg, 'AUTH_EXPIRED'
    elif status_code == 429:
        return error_msg, 'RATE_LIMIT_EXCEEDED'
    elif status_code in (400, 422):
        return error_msg, 'INVALID_CONTENT'
    elif status_code in (502, 503, 504):
        return error_msg, 'NETWORK_ERROR'
    else:
        return error_msg, 'UNKNOWN'


def _enforce_rate_limit() -> None:
    """Enforce minimum delay between posts."""
    global _last_post_time

    if _last_post_time > 0:
        elapsed = time.time() - _last_post_time
        if elapsed < _post_delay_seconds:
            time.sleep(_post_delay_seconds - elapsed)


@mcp.tool
def create_post(
    text: str,
    visibility: str = 'PUBLIC',
    hashtags: list[str] | None = None,
    link_url: str | None = None,
    link_title: str | None = None,
    link_description: str | None = None
) -> dict[str, Any]:
    """
    Create a new LinkedIn post on user's profile.

    Args:
        text: Post content/commentary (1-3000 chars).
        visibility: Post visibility level - 'PUBLIC' or 'CONNECTIONS'.
        hashtags: Optional list of hashtags (without # symbol, max 10).
        link_url: Optional URL to share.
        link_title: Title for shared link.
        link_description: Description for shared link.

    Returns:
        Dict with status, post_id, post_url, timestamp, or error details.
    """
    global _last_post_time

    # Validate inputs
    if not text:
        return {
            'status': 'error',
            'error': 'Post text is required',
            'error_code': 'INVALID_CONTENT'
        }

    if len(text) > 3000:
        return {
            'status': 'error',
            'error': f'Post text exceeds 3000 character limit ({len(text)} chars)',
            'error_code': 'INVALID_CONTENT'
        }

    if not config.access_token:
        return {
            'status': 'error',
            'error': 'LinkedIn access token not configured',
            'error_code': 'AUTH_EXPIRED'
        }

    if not config.person_urn:
        return {
            'status': 'error',
            'error': 'LinkedIn person URN not configured',
            'error_code': 'AUTH_EXPIRED'
        }

    # Enforce rate limit between posts
    _enforce_rate_limit()

    # Build post commentary with hashtags
    commentary = text
    if hashtags:
        hashtag_text = ' '.join(f'#{tag}' for tag in hashtags[:10])
        if hashtag_text not in commentary:
            commentary = f'{commentary}\n\n{hashtag_text}'

    # Build request payload per LinkedIn API v2
    payload: dict[str, Any] = {
        'author': config.person_urn,
        'commentary': commentary,
        'visibility': visibility,
        'distribution': {
            'feedDistribution': 'MAIN_FEED',
            'targetEntities': [],
            'thirdPartyDistributionChannels': []
        },
        'lifecycleState': 'PUBLISHED',
        'isReshareDisabledByAuthor': False
    }

    # Add link content if provided
    if link_url:
        payload['content'] = {
            'article': {
                'source': link_url,
                'title': link_title or '',
                'description': link_description or ''
            }
        }

    # Make request with retry handling
    rate_limiter = RateLimitHandler()
    url = f'{config.api_base_url}/posts'

    for attempt in range(rate_limiter.max_retries):
        try:
            response = requests.post(
                url,
                headers=config.get_headers(),
                json=payload,
                timeout=30
            )

            if response.status_code == 201:
                # Success - get post ID from header
                post_id = response.headers.get('x-restli-id', '')
                post_url = f'https://www.linkedin.com/feed/update/{post_id}'

                _last_post_time = time.time()

                return {
                    'status': 'published',
                    'post_id': post_id,
                    'post_url': post_url,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

            elif rate_limiter.should_retry(response, attempt):
                rate_limiter.wait_for_retry(attempt)
                continue

            else:
                error_msg, error_code = _classify_linkedin_error(response)
                return {
                    'status': 'error',
                    'error': error_msg,
                    'error_code': error_code
                }

        except requests.exceptions.Timeout:
            if attempt < rate_limiter.max_retries - 1:
                rate_limiter.wait_for_retry(attempt)
                continue
            return {
                'status': 'error',
                'error': 'Request timed out',
                'error_code': 'NETWORK_ERROR'
            }

        except requests.exceptions.ConnectionError as e:
            if attempt < rate_limiter.max_retries - 1:
                rate_limiter.wait_for_retry(attempt)
                continue
            return {
                'status': 'error',
                'error': str(e),
                'error_code': 'NETWORK_ERROR'
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'error_code': 'UNKNOWN'
            }

    return {
        'status': 'error',
        'error': 'Max retries exceeded',
        'error_code': 'RATE_LIMIT_EXCEEDED'
    }


@mcp.tool
def health_check() -> dict[str, Any]:
    """
    Check if LinkedIn API is reachable and access token is valid.

    Returns:
        Dict with status, api_reachable, token_valid, scopes, and checked_at timestamp.
    """
    result = {
        'status': 'error',
        'api_reachable': False,
        'token_valid': False,
        'checked_at': datetime.now(timezone.utc).isoformat()
    }

    if not config.access_token:
        result['error'] = 'LinkedIn access token not configured'
        return result

    try:
        # Use userinfo endpoint to verify token
        response = requests.get(
            'https://api.linkedin.com/v2/userinfo',
            headers=config.get_headers(),
            timeout=10
        )

        result['api_reachable'] = True

        if response.status_code == 200:
            result['token_valid'] = True
            result['status'] = 'available'

            # Extract scopes if available in response
            data = response.json()
            if 'sub' in data:
                result['person_urn'] = f"urn:li:person:{data['sub']}"

        elif response.status_code == 401:
            result['error'] = 'Access token expired or invalid'

        else:
            error_msg, _ = _classify_linkedin_error(response)
            result['error'] = error_msg

    except requests.exceptions.Timeout:
        result['error'] = 'Request timed out'

    except requests.exceptions.ConnectionError as e:
        result['error'] = f'Cannot connect to LinkedIn API: {e}'

    except Exception as e:
        result['error'] = str(e)

    return result


if __name__ == '__main__':
    mcp.run(transport='stdio')
