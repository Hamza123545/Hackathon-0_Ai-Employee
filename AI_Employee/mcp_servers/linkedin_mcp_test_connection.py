"""
LinkedIn MCP Server Health Check Script (Silver Tier)

Tests connection to LinkedIn API and verifies authentication.
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
    Test LinkedIn API connection and authentication.

    Returns:
        True if connection successful, False otherwise
    """
    # Check environment variables directly (standalone test)
    client_id = os.getenv('LINKEDIN_CLIENT_ID', '')
    client_secret = os.getenv('LINKEDIN_CLIENT_SECRET', '')
    redirect_uri = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:8080/linkedin/callback')

    if not client_id or not client_secret:
        print("❌ LinkedIn credentials not configured")
        print("   Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET environment variables")
        return False

    print(f"✅ LinkedIn Client ID: {client_id[:8]}..." if len(client_id) > 8 else f"✅ LinkedIn Client ID: {client_id}")
    print(f"✅ LinkedIn Client Secret: {'*' * 8}...")
    print(f"✅ Redirect URI: {redirect_uri}")

    # Try to import linkedin_api
    try:
        from linkedin_api import Linkedin
        print("✅ linkedin-api package installed")
    except ImportError:
        print("❌ linkedin-api package not installed")
        print("   Run: pip install linkedin-api")
        return False

    # Check for stored credentials
    try:
        import keyring

        # Check if we have stored LinkedIn credentials
        stored_email = keyring.get_password("linkedin-mcp", "email")
        stored_password = keyring.get_password("linkedin-mcp", "password")

        if stored_email and stored_password:
            print(f"✅ LinkedIn credentials found in keyring")
            print(f"   Email: {stored_email[:3]}...@...")

            # Try to authenticate
            try:
                api = Linkedin(stored_email, stored_password)

                # Get profile as connection test
                profile = api.get_profile()
                if profile:
                    name = f"{profile.get('firstName', '')} {profile.get('lastName', '')}"
                    headline = profile.get('headline', 'N/A')
                    print("✅ Successfully connected to LinkedIn API")
                    print(f"   Name: {name}")
                    print(f"   Headline: {headline[:50]}..." if len(headline) > 50 else f"   Headline: {headline}")
                    return True
                else:
                    print("❌ Failed to retrieve profile from LinkedIn")
                    return False

            except Exception as e:
                print(f"❌ LinkedIn authentication failed: {e}")
                print("   Credentials may be invalid or expired")
                return False
        else:
            print("⚠️  LinkedIn credentials not found in keyring")
            print("   Store credentials using keyring:")
            print("   keyring set linkedin-mcp email your_email@example.com")
            print("   keyring set linkedin-mcp password your_password")
            return False

    except Exception as e:
        print(f"❌ Keyring access failed: {e}")
        return False


if __name__ == '__main__':
    """Run health check."""
    print("=" * 60)
    print("LinkedIn MCP Server - Connection Test")
    print("=" * 60)
    print()

    success = test_connection()

    print()
    print("=" * 60)
    if success:
        print("✅ LinkedIn connection test PASSED")
    else:
        print("❌ LinkedIn connection test FAILED")
    print("=" * 60)

    sys.exit(0 if success else 1)
