"""
Facebook MCP Server (Gold Tier)

FastMCP server providing Facebook Pages integration - post messages,
retrieve engagement metrics, and manage social media presence.
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
mcp = FastMCP(name="facebook-mcp")

# Error codes per contract
ErrorCode = Literal[
    'AUTH_ERROR',
    'RATE_LIMIT',
    'INVALID_PARAMS',
    'PERMISSION_DENIED',
    'DUPLICATE_POST',
    'NETWORK_ERROR',
    'UNKNOWN'
]

# Rate limit tracking
_rate_limit_tracker = {
    'requests': [],
    'limit': 200,  # 200 requests per hour
    'window_seconds': 3600
}


class FacebookConfig:
    """Configuration for Facebook API loaded from environment variables."""
    
    @property
    def app_id(self) -> str:
        return os.environ.get('FACEBOOK_APP_ID', '')
    
    @property
    def app_secret(self) -> str:
        return os.environ.get('FACEBOOK_APP_SECRET', '')
    
    @property
    def page_id(self) -> str:
        return os.environ.get('FACEBOOK_PAGE_ID', '')


config = FacebookConfig()

# Initialize auth manager
_auth_manager: Optional[FacebookAuthManager] = None


def _get_auth_manager() -> FacebookAuthManager:
    """Get or create FacebookAuthManager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = FacebookAuthManager(
            app_id=config.app_id,
            app_secret=config.app_secret
        )
    return _auth_manager


def _get_graph_api(page_id: Optional[str] = None) -> GraphAPI:
    """Get GraphAPI instance with page access token."""
    auth_manager = _get_auth_manager()
    target_page_id = page_id or config.page_id
    
    if not target_page_id:
        raise ValueError("Facebook Page ID not configured")
    
    # Get page access token
    page_token = auth_manager.get_page_access_token(target_page_id)
    if not page_token:
        # Try to get from stored tokens
        page_token = auth_manager.get_access_token(page_id=target_page_id)
        if not page_token:
            raise RuntimeError(
                f"Page access token not found for page {target_page_id}. "
                "Run auth setup and exchange user token for page token."
            )
    
    return GraphAPI(
        access_token=page_token,
        version="18.0",
        sleep_on_rate_limit=True,
        sleep_on_rate_limit_mapping={
            200: 3600,  # Sleep 1 hour if 200 calls/hour exceeded
            100: 600    # Sleep 10 minutes if 100 calls/hour exceeded
        }
    )


def _check_rate_limit() -> None:
    """Check and enforce rate limit (200 requests/hour)."""
    now = time.time()
    
    # Remove requests older than 1 hour
    _rate_limit_tracker['requests'] = [
        req_time for req_time in _rate_limit_tracker['requests']
        if now - req_time < _rate_limit_tracker['window_seconds']
    ]
    
    # Check if limit exceeded
    if len(_rate_limit_tracker['requests']) >= _rate_limit_tracker['limit']:
        # Calculate wait time
        oldest_request = min(_rate_limit_tracker['requests'])
        wait_time = _rate_limit_tracker['window_seconds'] - (now - oldest_request) + 1
        if wait_time > 0:
            time.sleep(wait_time)
            _rate_limit_tracker['requests'] = []
    
    # Record this request
    _rate_limit_tracker['requests'].append(now)


def _classify_facebook_error(exception: FacebookError) -> tuple[str, ErrorCode]:
    """
    Classify Facebook API exception into error message and code.
    
    Args:
        exception: The FacebookError object.
    
    Returns:
        Tuple of (error_message, error_code).
    """
    error_code = getattr(exception, 'code', 0)
    error_msg = str(exception)
    
    if error_code in (190, 463, 467):
        return error_msg, 'AUTH_ERROR'
    elif error_code in (4, 17, 341):
        return error_msg, 'RATE_LIMIT'
    elif error_code == 10:
        return error_msg, 'PERMISSION_DENIED'
    elif error_code == 506:
        return error_msg, 'DUPLICATE_POST'
    elif error_code == 100:
        return error_msg, 'INVALID_PARAMS'
    elif error_code in (1, 2):
        return error_msg, 'NETWORK_ERROR'
    else:
        return error_msg, 'UNKNOWN'


@mcp.tool()
def post_to_page(
    page_id: str,
    message: str,
    link: Optional[str] = None,
    published: bool = True
) -> dict[str, Any]:
    """
    Post a message to a Facebook Page (requires approval via HITL workflow).
    
    Args:
        page_id: Facebook Page ID to post to
        message: Post message content (max 5000 characters)
        link: Optional URL to attach to the post
        published: Whether to publish immediately (false for draft)
    
    Returns:
        Dictionary with post_id, message, created_time, from, approval_request_id
    """
    if len(message) > 5000:
        raise ValueError("Message exceeds 5000 character limit")
    
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        graph = _get_graph_api(page_id)
        
        # Build post data
        post_data = {
            "message": message,
            "published": published
        }
        if link:
            post_data["link"] = link
        
        # Post to page
        result = graph.post_object(
            object_id=page_id,
            connection="feed",
            data=post_data,
            params={"fields": "id,message,created_time,from"}
        )
        
        return {
            'post_id': result.get('id', ''),
            'message': message,
            'created_time': result.get('created_time', datetime.now().isoformat()),
            'from': result.get('from', {}),
            'approval_request_id': 'generated_by_approval_workflow'
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (FacebookError, ConnectionError, TimeoutError))
        )
    except FacebookError as e:
        error_msg, error_code = _classify_facebook_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


@mcp.tool()
def get_page_posts(
    page_id: str,
    limit: int = 25,
    fields: str = "id,message,created_time,likes.summary(true),comments.summary(true),shares",
    since: Optional[str] = None,
    until: Optional[str] = None
) -> dict[str, Any]:
    """
    Retrieve recent posts from a Facebook Page with engagement data.
    
    Args:
        page_id: Facebook Page ID
        limit: Number of posts to retrieve (max 100)
        fields: Comma-separated list of fields to retrieve
        since: Retrieve posts since this timestamp (ISO 8601)
        until: Retrieve posts until this timestamp (ISO 8601)
    
    Returns:
        Dictionary with posts list, total_count, next_page
    """
    if limit > 100:
        limit = 100
    
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        graph = _get_graph_api(page_id)
        
        # Build parameters
        params = {
            "fields": fields,
            "limit": limit
        }
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        
        # Get page posts
        response = graph.get_connection(
            object_id=page_id,
            connection="posts",
            **params
        )
        
        # Format posts
        posts = []
        if 'data' in response:
            for post in response['data']:
                posts.append({
                    'post_id': post.get('id', ''),
                    'message': post.get('message', ''),
                    'created_time': post.get('created_time', ''),
                    'likes': post.get('likes', {}).get('summary', {}).get('total_count', 0) if isinstance(post.get('likes'), dict) else 0,
                    'comments': post.get('comments', {}).get('summary', {}).get('total_count', 0) if isinstance(post.get('comments'), dict) else 0,
                    'shares': post.get('shares', {}).get('count', 0) if isinstance(post.get('shares'), dict) else 0
                })
        
        return {
            'posts': posts,
            'total_count': len(posts),
            'next_page': response.get('paging', {}).get('next', '')
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (FacebookError, ConnectionError, TimeoutError))
        )
    except FacebookError as e:
        error_msg, error_code = _classify_facebook_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


@mcp.tool()
def get_engagement_summary(
    page_id: str,
    since: str,
    until: str,
    metrics: Optional[list[str]] = None
) -> dict[str, Any]:
    """
    Get aggregated engagement metrics for a Facebook Page over a specified period.
    
    Args:
        page_id: Facebook Page ID
        since: Start date for metrics (ISO 8601)
        until: End date for metrics (ISO 8601)
        metrics: List of metric types to retrieve (default: page_impressions, page_engaged_users, page_post_engagements)
    
    Returns:
        Dictionary with page_id, period, total_likes, total_comments, total_shares, total_reach, engagement_rate, generated_at
    """
    if metrics is None:
        metrics = ["page_impressions", "page_engaged_users", "page_post_engagements"]
    
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        graph = _get_graph_api(page_id)
        
        # Get page insights
        insights = graph.get_insights(
            object_id=page_id,
            metric=','.join(metrics),
            period="day",
            since=since,
            until=until
        )
        
        # Get posts for engagement calculation
        posts_response = get_page_posts(page_id, limit=100, since=since, until=until)
        
        # Calculate totals
        total_likes = sum(post.get('likes', 0) for post in posts_response.get('posts', []))
        total_comments = sum(post.get('comments', 0) for post in posts_response.get('posts', []))
        total_shares = sum(post.get('shares', 0) for post in posts_response.get('posts', []))
        
        # Calculate reach from insights
        total_reach = 0
        for insight in insights.get('data', []):
            if insight.get('name') == 'page_impressions':
                values = insight.get('values', [])
                if values:
                    total_reach = sum(v.get('value', 0) for v in values)
        
        # Calculate engagement rate
        total_engagement = total_likes + total_comments + total_shares
        engagement_rate = (total_engagement / total_reach * 100) if total_reach > 0 else 0.0
        
        return {
            'page_id': page_id,
            'period': f"{since} to {until}",
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_shares': total_shares,
            'total_reach': total_reach,
            'engagement_rate': round(engagement_rate, 2),
            'generated_at': datetime.now().isoformat()
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (FacebookError, ConnectionError, TimeoutError))
        )
    except FacebookError as e:
        error_msg, error_code = _classify_facebook_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


@mcp.tool()
def delete_post(
    post_id: str,
    reason: Optional[str] = None
) -> dict[str, Any]:
    """
    Delete a post from Facebook Page (requires approval via HITL workflow).
    
    Args:
        post_id: Facebook post ID to delete
        reason: Reason for deletion (for audit trail)
    
    Returns:
        Dictionary with success, post_id, deleted_at, approval_request_id
    """
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        graph = _get_graph_api()
        
        # Delete post
        result = graph.delete_object(object_id=post_id)
        
        return {
            'success': result.get('success', False),
            'post_id': post_id,
            'deleted_at': datetime.now().isoformat(),
            'approval_request_id': 'generated_by_approval_workflow'
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (FacebookError, ConnectionError, TimeoutError))
        )
    except FacebookError as e:
        error_msg, error_code = _classify_facebook_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


if __name__ == '__main__':
    """Run MCP server."""
    mcp.run()

