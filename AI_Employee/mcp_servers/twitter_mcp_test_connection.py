"""
Twitter MCP Server Health Check Script (Gold Tier)

Tests connection to Twitter API v2 and verifies authentication.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Set stdout encoding to UTF-8 for Windows compatibility
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def test_connection() -> bool:
    """
    Test Twitter API connection and authentication.

    Returns:
        True if connection successful, False otherwise
    """
    # Check environment variables directly (standalone test)
    client_id = os.getenv('TWITTER_CLIENT_ID', '')
    client_secret = os.getenv('TWITTER_CLIENT_SECRET', '')
    redirect_uri = os.getenv('TWITTER_REDIRECT_URI', 'http://localhost:8000/oauth/twitter/callback')

    if not client_id:
        print("❌ Twitter credentials not configured")
        print("   Set TWITTER_CLIENT_ID environment variable")
        return False

    print(f"✅ Twitter Client ID: {client_id[:8]}..." if len(client_id) > 8 else f"✅ Twitter Client ID: {client_id}")

    if client_secret:
        print(f"✅ Twitter Client Secret: {'*' * 8}...")
    else:
        print("⚠️  Twitter Client Secret not configured (optional for public clients)")

    print(f"✅ Redirect URI: {redirect_uri}")

    # Initialize auth manager
    try:
        from mcp_servers.twitter_mcp_auth import TwitterAuthManager

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

                print("✅ Successfully connected to Twitter API v2")
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
