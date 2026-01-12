"""
Instagram MCP Server (Gold Tier)

FastMCP server providing Instagram Business integration - post photos/videos,
retrieve engagement metrics, and manage Instagram business presence.
Uses Facebook Page Access Token (Instagram Business accounts are linked to Facebook Pages).
"""

import os
import time
from datetime import datetime
from typing import Any, Literal, Optional

from fastmcp import FastMCP
from facebook import GraphAPI, GraphAPIError as FacebookError

from mcp_servers.facebook_mcp_auth import FacebookAuthManager
from utils.retry_manager import default_retry_manager

# Initialize MCP server
mcp = FastMCP(name="instagram-mcp")

# Error codes per contract
ErrorCode = Literal[
    'AUTH_ERROR',
    'RATE_LIMIT',
    'INVALID_PARAMS',
    'PERMISSION_DENIED',
    'MEDIA_UPLOAD_FAILED',
    'NETWORK_ERROR',
    'UNKNOWN'
]

# Rate limit tracking (same as Facebook - 200 req/hour)
_rate_limit_tracker = {
    'requests': [],
    'limit': 200,
    'window_seconds': 3600
}


class InstagramConfig:
    """Configuration for Instagram API loaded from environment variables."""
    
    @property
    def app_id(self) -> str:
        return os.environ.get('FACEBOOK_APP_ID', '')  # Same as Facebook
    
    @property
    def app_secret(self) -> str:
        return os.environ.get('FACEBOOK_APP_SECRET', '')  # Same as Facebook
    
    @property
    def instagram_business_id(self) -> str:
        return os.environ.get('INSTAGRAM_BUSINESS_ID', '')


config = InstagramConfig()

# Initialize auth manager (reuses Facebook auth)
_auth_manager: Optional[FacebookAuthManager] = None


def _get_auth_manager() -> FacebookAuthManager:
    """Get or create FacebookAuthManager instance (shared with Facebook)."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = FacebookAuthManager(
            app_id=config.app_id,
            app_secret=config.app_secret
        )
    return _auth_manager


def _get_graph_api(page_id: Optional[str] = None) -> GraphAPI:
    """Get GraphAPI instance with page access token (for Instagram)."""
    auth_manager = _get_auth_manager()
    
    # Get page ID from config or parameter
    target_page_id = page_id or os.environ.get('FACEBOOK_PAGE_ID', '')
    if not target_page_id:
        raise ValueError("Facebook Page ID not configured (required for Instagram)")
    
    # Get page access token (same as Facebook)
    page_token = auth_manager.get_page_access_token(target_page_id)
    if not page_token:
        page_token = auth_manager.get_access_token(page_id=target_page_id)
        if not page_token:
            raise RuntimeError(
                f"Page access token not found for page {target_page_id}. "
                "Run Facebook auth setup first."
            )
    
    return GraphAPI(
        access_token=page_token,
        version="18.0",
        sleep_on_rate_limit=True,
        sleep_on_rate_limit_mapping={
            200: 3600,
            100: 600
        }
    )


def _get_instagram_business_id(page_id: Optional[str] = None) -> str:
    """Get Instagram Business Account ID from Facebook Page."""
    graph = _get_graph_api(page_id)
    target_page_id = page_id or os.environ.get('FACEBOOK_PAGE_ID', '')
    
    # Get Instagram Business Account linked to Facebook Page
    page_info = graph.get_object(
        object_id=target_page_id,
        fields="instagram_business_account"
    )
    
    ig_business_id = page_info.get('instagram_business_account', {}).get('id')
    if not ig_business_id:
        raise ValueError(
            f"No Instagram Business Account linked to Facebook Page {target_page_id}. "
            "Link Instagram Business Account to Facebook Page first."
        )
    
    return ig_business_id


def _check_rate_limit() -> None:
    """Check and enforce rate limit (200 requests/hour)."""
    now = time.time()
    _rate_limit_tracker['requests'] = [
        req_time for req_time in _rate_limit_tracker['requests']
        if now - req_time < _rate_limit_tracker['window_seconds']
    ]
    
    if len(_rate_limit_tracker['requests']) >= _rate_limit_tracker['limit']:
        oldest_request = min(_rate_limit_tracker['requests'])
        wait_time = _rate_limit_tracker['window_seconds'] - (now - oldest_request) + 1
        if wait_time > 0:
            time.sleep(wait_time)
            _rate_limit_tracker['requests'] = []
    
    _rate_limit_tracker['requests'].append(now)


def _classify_instagram_error(exception: FacebookError) -> tuple[str, ErrorCode]:
    """Classify Instagram API exception (uses Facebook error codes)."""
    error_code = getattr(exception, 'code', 0)
    error_msg = str(exception)
    
    if error_code in (190, 463, 467):
        return error_msg, 'AUTH_ERROR'
    elif error_code in (4, 17, 341):
        return error_msg, 'RATE_LIMIT'
    elif error_code == 10:
        return error_msg, 'PERMISSION_DENIED'
    elif error_code == 100:
        return error_msg, 'INVALID_PARAMS'
    elif error_code == 9004:
        return error_msg, 'MEDIA_UPLOAD_FAILED'
    elif error_code in (1, 2):
        return error_msg, 'NETWORK_ERROR'
    else:
        return error_msg, 'UNKNOWN'


@mcp.tool()
def post_photo(
    instagram_business_id: str,
    image_url: str,
    caption: str,
    location_id: Optional[str] = None,
    user_tags: Optional[str] = None
) -> dict[str, Any]:
    """
    Post a photo to Instagram Business account (requires approval via HITL workflow).
    Two-step process: create container, then publish.
    
    Args:
        instagram_business_id: Instagram Business Account ID
        image_url: Publicly accessible URL of the image to post
        caption: Caption for the post (max 2200 characters)
        location_id: Optional Instagram location ID to tag
        user_tags: Optional JSON string with user tags
    
    Returns:
        Dictionary with media_id, container_id, status, created_at, approval_request_id
    """
    if len(caption) > 2200:
        raise ValueError("Caption exceeds 2200 character limit")
    
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        graph = _get_graph_api()
        
        # Step 1: Create media container
        container_data = {
            "image_url": image_url,
            "caption": caption
        }
        if location_id:
            container_data["location_id"] = location_id
        if user_tags:
            container_data["user_tags"] = user_tags
        
        container = graph.post_object(
            object_id=instagram_business_id,
            connection="media",
            data=container_data
        )
        
        container_id = container.get('id', '')
        
        # Step 2: Publish container (requires approval in real workflow)
        # For now, return container_id - actual publishing happens after approval
        return {
            'media_id': container_id,  # Will be media_id after publishing
            'container_id': container_id,
            'status': 'pending_publish',  # Requires approval before publish
            'created_at': datetime.now().isoformat(),
            'approval_request_id': 'generated_by_approval_workflow'
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (FacebookError, ConnectionError, TimeoutError))
        )
    except FacebookError as e:
        error_msg, error_code = _classify_instagram_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


@mcp.tool()
def post_video(
    instagram_business_id: str,
    video_url: str,
    caption: str,
    location_id: Optional[str] = None,
    thumb_offset: Optional[int] = None
) -> dict[str, Any]:
    """
    Post a video to Instagram Business account (requires approval via HITL workflow).
    Two-step process: create container, then publish.
    
    Args:
        instagram_business_id: Instagram Business Account ID
        video_url: Publicly accessible URL of the video to post (MP4 format)
        caption: Caption for the video (max 2200 characters)
        location_id: Optional Instagram location ID to tag
        thumb_offset: Offset in seconds for video thumbnail frame
    
    Returns:
        Dictionary with media_id, container_id, status, created_at, approval_request_id
    """
    if len(caption) > 2200:
        raise ValueError("Caption exceeds 2200 character limit")
    
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        graph = _get_graph_api()
        
        # Step 1: Create media container
        container_data = {
            "media_type": "REELS",  # or "VIDEO"
            "video_url": video_url,
            "caption": caption
        }
        if location_id:
            container_data["location_id"] = location_id
        if thumb_offset is not None:
            container_data["thumb_offset"] = thumb_offset
        
        container = graph.post_object(
            object_id=instagram_business_id,
            connection="media",
            data=container_data
        )
        
        container_id = container.get('id', '')
        
        return {
            'media_id': container_id,
            'container_id': container_id,
            'status': 'pending_publish',
            'created_at': datetime.now().isoformat(),
            'approval_request_id': 'generated_by_approval_workflow'
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (FacebookError, ConnectionError, TimeoutError))
        )
    except FacebookError as e:
        error_msg, error_code = _classify_instagram_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


@mcp.tool()
def get_media(
    instagram_business_id: str,
    limit: int = 25,
    fields: str = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count"
) -> dict[str, Any]:
    """
    Retrieve Instagram media posts from business account with basic metadata.
    
    Args:
        instagram_business_id: Instagram Business Account ID
        limit: Number of media items to retrieve (max 100)
        fields: Comma-separated list of fields to retrieve
    
    Returns:
        Dictionary with media list, total_count, next_page
    """
    if limit > 100:
        limit = 100
    
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        graph = _get_graph_api()
        
        # Get media
        response = graph.get_connection(
            object_id=instagram_business_id,
            connection="media",
            fields=fields,
            limit=limit
        )
        
        # Format media
        media_list = []
        if 'data' in response:
            for item in response['data']:
                media_list.append({
                    'media_id': item.get('id', ''),
                    'caption': item.get('caption', ''),
                    'media_type': item.get('media_type', ''),
                    'permalink': item.get('permalink', ''),
                    'timestamp': item.get('timestamp', ''),
                    'like_count': item.get('like_count', 0),
                    'comments_count': item.get('comments_count', 0)
                })
        
        return {
            'media': media_list,
            'total_count': len(media_list),
            'next_page': response.get('paging', {}).get('next', '')
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (FacebookError, ConnectionError, TimeoutError))
        )
    except FacebookError as e:
        error_msg, error_code = _classify_instagram_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


@mcp.tool()
def get_insights(
    instagram_business_id: str,
    metric: str,
    period: str,
    since: Optional[str] = None,
    until: Optional[str] = None
) -> dict[str, Any]:
    """
    Get Instagram Business account insights for specified metrics and period.
    
    Args:
        instagram_business_id: Instagram Business Account ID
        metric: Comma-separated metrics (impressions, reach, profile_views, etc.)
        period: Time period (day, week, days_28, lifetime)
        since: Start date for insights (Unix timestamp or ISO 8601)
        until: End date for insights (Unix timestamp or ISO 8601)
    
    Returns:
        Dictionary with insights array and generated_at
    """
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        graph = _get_graph_api()
        
        # Get insights
        params = {
            "metric": metric,
            "period": period
        }
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        
        insights = graph.get_insights(
            object_id=instagram_business_id,
            **params
        )
        
        return {
            'insights': insights.get('data', []),
            'generated_at': datetime.now().isoformat()
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (FacebookError, ConnectionError, TimeoutError))
        )
    except FacebookError as e:
        error_msg, error_code = _classify_instagram_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


@mcp.tool()
def get_media_insights(
    media_id: str,
    metric: str
) -> dict[str, Any]:
    """
    Get insights for a specific Instagram media post.
    
    Args:
        media_id: Instagram media ID
        metric: Comma-separated metrics (engagement, impressions, reach, saved, video_views)
    
    Returns:
        Dictionary with media_id and insights array
    """
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        graph = _get_graph_api()
        
        # Get media insights
        insights = graph.get_insights(
            object_id=media_id,
            metric=metric
        )
        
        return {
            'media_id': media_id,
            'insights': insights.get('data', [])
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (FacebookError, ConnectionError, TimeoutError))
        )
    except FacebookError as e:
        error_msg, error_code = _classify_instagram_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


if __name__ == '__main__':
    """Run MCP server."""
    mcp.run()

