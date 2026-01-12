"""
Twitter MCP Server Health Check Script (Gold Tier)

Tests connection to Twitter API v2 and verifies authentication.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_servers.twitter_mcp_auth import TwitterAuthManager
from utils.config import Config


def test_connection() -> bool:
    """
    Test Twitter API connection and authentication.

    Returns:
        True if connection successful, False otherwise
    """
    config = Config()

    # Check environment variables
    client_id = config.twitter_client_id or os.getenv('TWITTER_CLIENT_ID', '')
    client_secret = config.twitter_client_secret or os.getenv('TWITTER_CLIENT_SECRET', '')
    redirect_uri = os.getenv('TWITTER_REDIRECT_URI', 'http://localhost:8000/oauth/twitter/callback')

    if not client_id:
        print("❌ Twitter credentials not configured")
        print("   Set TWITTER_CLIENT_ID environment variable")
        return False

    print(f"✅ Twitter Client ID: {client_id[:8]}...")

    if client_secret:
        print(f"✅ Twitter Client Secret: {'*' * 8}...")
    else:
        print("⚠️  Twitter Client Secret not configured (optional for public clients)")

    print(f"✅ Redirect URI: {redirect_uri}")

    # Initialize auth manager
    try:
        auth_manager = TwitterAuthManager(
            client_id=client_id,
            client_secret=client_secret if client_secret else None,
            redirect_uri=redirect_uri
        )

        # Check if authenticated
        access_token = auth_manager.get_access_token()
        if not access_token:
            print("❌ Not authenticated with Twitter")
            print("   Run: python mcp_servers/twitter_mcp_auth.py")
            return False

        print("✅ Twitter access token found")

        # Test API connection by getting authenticated user
        try:
            import tweepy

            client = tweepy.Client(bearer_token=access_token)

            # Get authenticated user as a simple connection test
            me = client.get_me(user_fields=["id", "name", "username", "public_metrics"])

            if me.data:
                user = me.data
                metrics = user.public_metrics if hasattr(user, 'public_metrics') else {}

                print(f"✅ Successfully connected to Twitter API v2")
                print(f"   Username: @{user.username}")
                print(f"   Name: {user.name}")
                print(f"   User ID: {user.id}")

                if metrics:
                    print(f"   Followers: {metrics.get('followers_count', 'N/A')}")
                    print(f"   Following: {metrics.get('following_count', 'N/A')}")
                    print(f"   Tweets: {metrics.get('tweet_count', 'N/A')}")

                return True
            else:
                print("❌ Failed to retrieve user data from Twitter API")
                return False

        except tweepy.errors.Unauthorized as e:
            print(f"❌ Authentication failed: Token may be expired or invalid")
            print(f"   Error: {e}")
            print("   Run: python mcp_servers/twitter_mcp_auth.py")
            return False

        except Exception as e:
            print(f"❌ API connection test failed: {e}")
            return False

    except Exception as e:
        print(f"❌ Authentication check failed: {e}")
        return False


if __name__ == '__main__':
    """Run health check."""
    print("=" * 60)
    print("Twitter MCP Server - Connection Test")
    print("=" * 60)
    print()

    success = test_connection()

    print()
    print("=" * 60)
    if success:
        print("✅ Twitter connection test PASSED")
    else:
        print("❌ Twitter connection test FAILED")
    print("=" * 60)

    sys.exit(0 if success else 1)
