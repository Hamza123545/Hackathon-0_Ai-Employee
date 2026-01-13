"""
Twitter MCP Server (Gold Tier)

FastMCP server providing Twitter/X integration - post tweets, retrieve engagement metrics,
and manage social media presence with OAuth 2.0 PKCE authentication.
"""

import os
import time
from datetime import datetime
from typing import Any, Literal, Optional

import tweepy
from fastmcp import FastMCP

from mcp_servers.twitter_mcp_auth import TwitterAuthManager
from utils.retry_manager import default_retry_manager

# Initialize MCP server
mcp = FastMCP(name="twitter-mcp")

# Error codes per contract
ErrorCode = Literal[
    'UNAUTHORIZED',
    'FORBIDDEN',
    'NOT_FOUND',
    'TOO_MANY_REQUESTS',
    'BAD_REQUEST',
    'CONFLICT',
    'INTERNAL_SERVER_ERROR',
    'SERVICE_UNAVAILABLE',
    'UNKNOWN'
]

# Rate limit tracking (100 requests per 15 minutes)
_rate_limit_tracker = {
    'requests': [],
    'limit': 100,
    'window_seconds': 900  # 15 minutes
}


class TwitterConfig:
    """Configuration for Twitter API loaded from environment variables."""
    
    @property
    def client_id(self) -> str:
        return os.environ.get('TWITTER_CLIENT_ID', '')
    
    @property
    def client_secret(self) -> Optional[str]:
        return os.environ.get('TWITTER_CLIENT_SECRET', '')


config = TwitterConfig()

# Initialize auth manager
_auth_manager: Optional[TwitterAuthManager] = None


def _get_auth_manager() -> TwitterAuthManager:
    """Get or create TwitterAuthManager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = TwitterAuthManager(
            client_id=config.client_id,
            client_secret=config.client_secret
        )
    return _auth_manager


def _get_client() -> tweepy.Client:
    """Get tweepy Client instance with authenticated token."""
    auth_manager = _get_auth_manager()
    return auth_manager.get_client()


def _check_rate_limit() -> None:
    """Check and enforce rate limit (100 requests per 15 minutes)."""
    now = time.time()
    
    # Remove requests older than 15 minutes
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


def _classify_twitter_error(exception: Exception) -> tuple[str, ErrorCode]:
    """
    Classify Twitter API exception into error message and code.
    
    Args:
        exception: The exception object.
    
    Returns:
        Tuple of (error_message, error_code).
    """
    error_msg = str(exception)
    
    # Check for HTTP status codes in error message
    if "401" in error_msg or "UNAUTHORIZED" in error_msg.upper():
        return error_msg, 'UNAUTHORIZED'
    elif "403" in error_msg or "FORBIDDEN" in error_msg.upper():
        return error_msg, 'FORBIDDEN'
    elif "404" in error_msg or "NOT_FOUND" in error_msg.upper():
        return error_msg, 'NOT_FOUND'
    elif "429" in error_msg or "TOO_MANY_REQUESTS" in error_msg.upper():
        return error_msg, 'TOO_MANY_REQUESTS'
    elif "400" in error_msg or "BAD_REQUEST" in error_msg.upper():
        return error_msg, 'BAD_REQUEST'
    elif "409" in error_msg or "CONFLICT" in error_msg.upper():
        return error_msg, 'CONFLICT'
    elif "500" in error_msg:
        return error_msg, 'INTERNAL_SERVER_ERROR'
    elif "503" in error_msg or "SERVICE_UNAVAILABLE" in error_msg.upper():
        return error_msg, 'SERVICE_UNAVAILABLE'
    else:
        return error_msg, 'UNKNOWN'


@mcp.tool()
def post_tweet(
    text: str,
    reply_to_tweet_id: Optional[str] = None,
    quote_tweet_id: Optional[str] = None,
    media_ids: Optional[list[str]] = None,
    poll_options: Optional[list[str]] = None,
    poll_duration_minutes: Optional[int] = None,
    reply_settings: str = "everyone"
) -> dict[str, Any]:
    """
    Post a tweet to Twitter/X (requires approval via HITL workflow).
    
    Args:
        text: Tweet text content (max 280 characters)
        reply_to_tweet_id: Optional tweet ID to reply to
        quote_tweet_id: Optional tweet ID to quote
        media_ids: Optional array of media IDs to attach (max 4 images or 1 video)
        poll_options: Optional poll options (2-4 choices)
        poll_duration_minutes: Optional poll duration in minutes (5 min to 7 days)
        reply_settings: Who can reply (everyone, mentionedUsers, following)
    
    Returns:
        Dictionary with tweet_id, text, created_at, approval_request_id
    """
    if len(text) > 280:
        raise ValueError("Tweet text exceeds 280 character limit")
    
    if media_ids and len(media_ids) > 4:
        raise ValueError("Maximum 4 media items allowed")
    
    if poll_options:
        if len(poll_options) < 2 or len(poll_options) > 4:
            raise ValueError("Poll must have 2-4 options")
        if not poll_duration_minutes or poll_duration_minutes < 5 or poll_duration_minutes > 10080:
            raise ValueError("Poll duration must be 5 minutes to 7 days (10080 minutes)")
    
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        client = _get_client()
        
        # Build tweet parameters
        tweet_params = {
            "text": text,
            "reply_settings": reply_settings
        }
        if reply_to_tweet_id:
            tweet_params["in_reply_to_tweet_id"] = reply_to_tweet_id
        if quote_tweet_id:
            tweet_params["quote_tweet_id"] = quote_tweet_id
        if media_ids:
            tweet_params["media_ids"] = media_ids
        if poll_options:
            tweet_params["poll"] = {
                "options": poll_options,
                "duration_minutes": poll_duration_minutes
            }
        
        # Create tweet
        response = client.create_tweet(**tweet_params)
        
        tweet_data = response.data
        return {
            'tweet_id': tweet_data.get('id', ''),
            'text': text,
            'created_at': datetime.now().isoformat(),
            'approval_request_id': 'generated_by_approval_workflow'
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (tweepy.TweepyException, ConnectionError, TimeoutError))
        )
    except tweepy.TweepyException as e:
        error_msg, error_code = _classify_twitter_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


@mcp.tool()
def delete_tweet(
    tweet_id: str,
    reason: Optional[str] = None
) -> dict[str, Any]:
    """
    Delete a tweet from Twitter/X (requires approval via HITL workflow).
    
    Args:
        tweet_id: Tweet ID to delete
        reason: Reason for deletion (for audit trail)
    
    Returns:
        Dictionary with success, tweet_id, deleted_at, approval_request_id
    """
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        client = _get_client()
        
        # Delete tweet
        response = client.delete_tweet(id=tweet_id)
        
        return {
            'success': response.data.get('deleted', False),
            'tweet_id': tweet_id,
            'deleted_at': datetime.now().isoformat(),
            'approval_request_id': 'generated_by_approval_workflow'
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (tweepy.TweepyException, ConnectionError, TimeoutError))
        )
    except tweepy.TweepyException as e:
        error_msg, error_code = _classify_twitter_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


@mcp.tool()
def get_user_tweets(
    user_id: Optional[str] = None,
    max_results: int = 25,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    exclude: Optional[list[str]] = None
) -> dict[str, Any]:
    """
    Retrieve recent tweets from authenticated user's timeline with public metrics.
    
    Args:
        user_id: Twitter user ID (defaults to authenticated user)
        max_results: Number of tweets to retrieve (5-100)
        start_time: Retrieve tweets since this timestamp (ISO 8601)
        end_time: Retrieve tweets until this timestamp (ISO 8601)
        exclude: Exclude retweets or replies
    
    Returns:
        Dictionary with tweets list and meta information
    """
    if max_results < 5:
        max_results = 5
    elif max_results > 100:
        max_results = 100
    
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        client = _get_client()
        
        # Get authenticated user ID if not provided
        if not user_id:
            me = client.get_me()
            user_id = me.data.id
        
        # Build parameters
        tweet_params = {
            "id": user_id,
            "max_results": max_results,
            "tweet_fields": ["created_at", "public_metrics", "author_id"]
        }
        if start_time:
            tweet_params["start_time"] = start_time
        if end_time:
            tweet_params["end_time"] = end_time
        if exclude:
            tweet_params["exclude"] = exclude
        
        # Get user tweets
        response = client.get_users_tweets(**tweet_params)
        
        # Format tweets
        tweets = []
        if response.data:
            for tweet in response.data:
                public_metrics = tweet.public_metrics or {}
                tweets.append({
                    'tweet_id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat() if tweet.created_at else '',
                    'author_id': tweet.author_id,
                    'public_metrics': {
                        'retweet_count': public_metrics.get('retweet_count', 0),
                        'reply_count': public_metrics.get('reply_count', 0),
                        'like_count': public_metrics.get('like_count', 0),
                        'quote_count': public_metrics.get('quote_count', 0),
                        'impression_count': public_metrics.get('impression_count', 0)
                    }
                })
        
        return {
            'tweets': tweets,
            'meta': {
                'result_count': len(tweets),
                'newest_id': tweets[0].get('tweet_id') if tweets else None,
                'oldest_id': tweets[-1].get('tweet_id') if tweets else None,
                'next_token': response.meta.get('next_token') if response.meta else None
            }
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (tweepy.TweepyException, ConnectionError, TimeoutError))
        )
    except tweepy.TweepyException as e:
        error_msg, error_code = _classify_twitter_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


@mcp.tool()
def get_tweet_metrics(
    tweet_id: str,
    include_private_metrics: bool = False
) -> dict[str, Any]:
    """
    Get detailed engagement metrics for a specific tweet.
    
    Args:
        tweet_id: Tweet ID to retrieve metrics for
        include_private_metrics: Include non-public metrics (requires OAuth user context)
    
    Returns:
        Dictionary with tweet_id, text, created_at, public_metrics, organic_metrics
    """
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        client = _get_client()
        
        # Build fields
        tweet_fields = ["created_at", "public_metrics"]
        if include_private_metrics:
            tweet_fields.append("non_public_metrics")
            tweet_fields.append("organic_metrics")
        
        # Get tweet
        response = client.get_tweet(
            id=tweet_id,
            tweet_fields=tweet_fields
        )
        
        tweet = response.data
        public_metrics = tweet.public_metrics or {}
        organic_metrics = tweet.organic_metrics if hasattr(tweet, 'organic_metrics') and tweet.organic_metrics else {}
        
        return {
            'tweet_id': tweet_id,
            'text': tweet.text,
            'created_at': tweet.created_at.isoformat() if tweet.created_at else '',
            'public_metrics': {
                'retweet_count': public_metrics.get('retweet_count', 0),
                'reply_count': public_metrics.get('reply_count', 0),
                'like_count': public_metrics.get('like_count', 0),
                'quote_count': public_metrics.get('quote_count', 0),
                'impression_count': public_metrics.get('impression_count', 0)
            },
            'organic_metrics': {
                'impression_count': organic_metrics.get('impression_count', 0),
                'like_count': organic_metrics.get('like_count', 0),
                'reply_count': organic_metrics.get('reply_count', 0),
                'retweet_count': organic_metrics.get('retweet_count', 0),
                'url_link_clicks': organic_metrics.get('url_link_clicks', 0),
                'user_profile_clicks': organic_metrics.get('user_profile_clicks', 0)
            } if include_private_metrics else {}
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (tweepy.TweepyException, ConnectionError, TimeoutError))
        )
    except tweepy.TweepyException as e:
        error_msg, error_code = _classify_twitter_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


@mcp.tool()
def get_engagement_summary(
    user_id: str,
    start_time: str,
    end_time: str
) -> dict[str, Any]:
    """
    Get aggregated Twitter engagement metrics for specified time period.
    
    Args:
        user_id: Twitter user ID (defaults to authenticated user)
        start_time: Start date for metrics (ISO 8601)
        end_time: End date for metrics (ISO 8601)
    
    Returns:
        Dictionary with user_id, period, total_tweets, engagement metrics, engagement_rate, generated_at
    """
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        client = _get_client()
        
        # Get user tweets for the period
        tweets_response = get_user_tweets(
            user_id=user_id,
            max_results=100,
            start_time=start_time,
            end_time=end_time
        )
        
        tweets = tweets_response.get('tweets', [])
        
        # Calculate totals
        total_tweets = len(tweets)
        total_retweets = sum(t.get('public_metrics', {}).get('retweet_count', 0) for t in tweets)
        total_likes = sum(t.get('public_metrics', {}).get('like_count', 0) for t in tweets)
        total_replies = sum(t.get('public_metrics', {}).get('reply_count', 0) for t in tweets)
        total_quotes = sum(t.get('public_metrics', {}).get('quote_count', 0) for t in tweets)
        total_impressions = sum(t.get('public_metrics', {}).get('impression_count', 0) for t in tweets)
        
        # Calculate engagement rate
        total_engagement = total_likes + total_replies + total_retweets + total_quotes
        engagement_rate = (total_engagement / total_impressions * 100) if total_impressions > 0 else 0.0
        
        return {
            'user_id': user_id,
            'period': f"{start_time} to {end_time}",
            'total_tweets': total_tweets,
            'total_retweets': total_retweets,
            'total_likes': total_likes,
            'total_replies': total_replies,
            'total_quotes': total_quotes,
            'total_impressions': total_impressions,
            'engagement_rate': round(engagement_rate, 2),
            'generated_at': datetime.now().isoformat()
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (tweepy.TweepyException, ConnectionError, TimeoutError))
        )
    except tweepy.TweepyException as e:
        error_msg, error_code = _classify_twitter_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


if __name__ == '__main__':
    """Run MCP server."""
    mcp.run()

