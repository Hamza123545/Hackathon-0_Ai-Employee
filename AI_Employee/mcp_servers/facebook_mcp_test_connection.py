"""
Facebook MCP Server Health Check Script (Gold Tier)

Tests connection to Facebook Graph API and verifies authentication.
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
    Test Facebook API connection and authentication.

    Returns:
        True if connection successful, False otherwise
    """
    # Check environment variables directly (standalone test)
    app_id = os.getenv('FACEBOOK_APP_ID', '')
    app_secret = os.getenv('FACEBOOK_APP_SECRET', '')
    page_id = os.getenv('FACEBOOK_PAGE_ID', '')

    if not app_id or not app_secret:
        print("❌ Facebook credentials not configured")
        print("   Set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET environment variables")
        return False

    print(f"✅ Facebook App ID: {app_id[:8]}..." if len(app_id) > 8 else f"✅ Facebook App ID: {app_id}")
    print(f"✅ Facebook App Secret: {'*' * 8}...")

    if not page_id:
        print("⚠️  Facebook Page ID not configured")
        print("   Set FACEBOOK_PAGE_ID environment variable")
        print("   This is optional for testing but required for posting")
    else:
        print(f"✅ Facebook Page ID: {page_id}")

    # Initialize auth manager
    try:
        from mcp_servers.facebook_mcp_auth import FacebookAuthManager

        auth_manager = FacebookAuthManager(
            app_id=app_id,
            app_secret=app_secret
        )

        # Check if page token exists
        if page_id:
            page_token = auth_manager.get_page_access_token(page_id)
            if not page_token:
                print("❌ Page access token not found")
                print("   Run: python mcp_servers/facebook_mcp_auth.py")
                return False

            print("✅ Facebook Page access token found")

            # Test API connection by getting page details
            try:
                from facebook import GraphAPI

                graph = GraphAPI(access_token=page_token, version="18.0")

                # Get page details as a simple connection test
                page_info = graph.get_object(object_id=page_id, fields="id,name,username,fan_count")

                print("✅ Successfully connected to Facebook Graph API")
                print(f"   Page Name: {page_info.get('name', 'N/A')}")
                print(f"   Username: {page_info.get('username', 'N/A')}")
                print(f"   Followers: {page_info.get('fan_count', 'N/A')}")
                return True

            except Exception as e:
                print(f"❌ API connection test failed: {e}")
                return False
        else:
            print("⚠️  Cannot test full API connection without Page ID")
            print("   Basic authentication check passed")
            return True

    except Exception as e:
        print(f"❌ Authentication check failed: {e}")
        return False


if __name__ == '__main__':
    """Run health check."""
    print("=" * 60)
    print("Facebook MCP Server - Connection Test")
    print("=" * 60)
    print()

    success = test_connection()

    print()
    print("=" * 60)
    if success:
        print("✅ Facebook connection test PASSED")
    else:
        print("❌ Facebook connection test FAILED")
    print("=" * 60)

    sys.exit(0 if success else 1)
