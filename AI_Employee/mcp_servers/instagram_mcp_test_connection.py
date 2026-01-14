"""
Instagram MCP Server Health Check Script (Gold Tier)

Tests connection to Instagram Graph API and verifies authentication.
"""

import os
import sys
from pathlib import Path

# Set stdout encoding to UTF-8 for Windows compatibility
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_connection() -> bool:
    """
    Test Instagram API connection and authentication.

    Note: Instagram Business API uses Facebook authentication.

    Returns:
        True if connection successful, False otherwise
    """
    # Check environment variables directly (standalone test)
    app_id = os.getenv('FACEBOOK_APP_ID', '')
    app_secret = os.getenv('FACEBOOK_APP_SECRET', '')
    page_id = os.getenv('FACEBOOK_PAGE_ID', '')
    instagram_account_id = os.getenv('INSTAGRAM_ACCOUNT_ID', '')

    if not app_id or not app_secret:
        print("❌ Facebook credentials not configured (required for Instagram)")
        print("   Set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET environment variables")
        return False

    print(f"✅ Facebook App ID: {app_id[:8]}..." if len(app_id) > 8 else f"✅ Facebook App ID: {app_id}")
    print(f"✅ Facebook App Secret: {'*' * 8}...")

    if not page_id:
        print("⚠️  Facebook Page ID not configured")
        print("   Set FACEBOOK_PAGE_ID environment variable")
        print("   Required to retrieve Instagram Business Account ID")
    else:
        print(f"✅ Facebook Page ID: {page_id}")

    if instagram_account_id:
        print(f"✅ Instagram Account ID: {instagram_account_id}")
    else:
        print("⚠️  Instagram Account ID not configured")
        print("   Will attempt to retrieve from Facebook Page")

    # Initialize auth manager
    try:
        from mcp_servers.facebook_mcp_auth import FacebookAuthManager

        auth_manager = FacebookAuthManager(
            app_id=app_id,
            app_secret=app_secret
        )

        # Check if page token exists
        if not page_id:
            print("❌ Cannot proceed without Facebook Page ID")
            return False

        page_token = auth_manager.get_page_access_token(page_id)
        if not page_token:
            print("❌ Page access token not found")
            print("   Run: python mcp_servers/facebook_mcp_auth.py")
            return False

        print("✅ Facebook Page access token found")

        # Test API connection by getting Instagram account details
        try:
            from facebook import GraphAPI

            graph = GraphAPI(access_token=page_token, version="18.0")

            # Get Instagram Business Account ID from Page
            if not instagram_account_id:
                page_data = graph.get_object(
                    object_id=page_id,
                    fields="instagram_business_account"
                )

                if 'instagram_business_account' in page_data:
                    instagram_account_id = page_data['instagram_business_account']['id']
                    print(f"✅ Retrieved Instagram Account ID: {instagram_account_id}")
                else:
                    print("❌ No Instagram Business Account linked to this Facebook Page")
                    print("   Link an Instagram Business Account to your Facebook Page")
                    return False

            # Get Instagram account details
            ig_account = graph.get_object(
                object_id=instagram_account_id,
                fields="id,username,name,followers_count,media_count,profile_picture_url"
            )

            print("✅ Successfully connected to Instagram Graph API")
            print(f"   Username: @{ig_account.get('username', 'N/A')}")
            print(f"   Name: {ig_account.get('name', 'N/A')}")
            print(f"   Followers: {ig_account.get('followers_count', 'N/A')}")
            print(f"   Posts: {ig_account.get('media_count', 'N/A')}")
            return True

        except Exception as e:
            print(f"❌ API connection test failed: {e}")
            return False

    except Exception as e:
        print(f"❌ Authentication check failed: {e}")
        return False


if __name__ == '__main__':
    """Run health check."""
    print("=" * 60)
    print("Instagram MCP Server - Connection Test")
    print("=" * 60)
    print()

    success = test_connection()

    print()
    print("=" * 60)
    if success:
        print("✅ Instagram connection test PASSED")
    else:
        print("❌ Instagram connection test FAILED")
    print("=" * 60)

    sys.exit(0 if success else 1)
