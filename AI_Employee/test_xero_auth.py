"""
Xero OAuth 2.0 Authentication Script

Authenticates with Xero using OAuth 2.0 and retrieves Tenant ID.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import webbrowser
from urllib.parse import urlencode

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


def test_xero_auth():
    """Test Xero OAuth 2.0 authentication."""
    print("=" * 60)
    print("Xero OAuth 2.0 Authentication")
    print("=" * 60)
    print()

    # Get credentials
    client_id = os.getenv('XERO_CLIENT_ID', '')
    client_secret = os.getenv('XERO_CLIENT_SECRET', '')
    redirect_uri = os.getenv('XERO_REDIRECT_URI', 'http://localhost:8000/oauth/xero/callback')

    if not client_id or not client_secret:
        print("❌ Xero credentials not configured")
        return False

    print(f"✅ Client ID: {client_id[:20]}...")
    print(f"✅ Client Secret: {'*' * 10}...")
    print(f"✅ Redirect URI: {redirect_uri}")
    print()

    try:
        from xero_python.api_client import ApiClient, Configuration
        from xero_python.api_client.oauth2 import OAuth2Token
        from xero_python.identity import IdentityApi

        # Configure API client
        api_client = ApiClient(
            Configuration(
                oauth2_token=OAuth2Token(
                    client_id=client_id,
                    client_secret=client_secret
                )
            ),
            pool_threads=1
        )

        # Required scopes
        scopes = [
            "offline_access",
            "openid",
            "profile",
            "email",
            "accounting.transactions",
            "accounting.reports.read",
            "accounting.settings"
        ]

        # Build authorization URL
        authorization_url = api_client.get_authorization_url(
            redirect_uri=redirect_uri,
            scope=" ".join(scopes)
        )

        print()
        print("=" * 60)
        print("Xero Authorization Required")
        print("=" * 60)
        print()
        print("Opening browser for Xero authorization...")
        print()
        print("If browser doesn't open, manually visit this URL:")
        print(authorization_url)
        print()

        # Open browser
        webbrowser.open(authorization_url)

        print("After authorizing:")
        print("1. You'll be redirected to a URL like:")
        print("   http://localhost:8000/oauth/xero/callback?code=...&scope=...")
        print()
        print("2. Copy the ENTIRE redirect URL from your browser")
        print()

        # Get the redirect response from user
        redirect_response = input("Paste the redirect URL here: ").strip()

        if not redirect_response:
            print("❌ No redirect URL provided")
            return False

        print()
        print("Exchanging authorization code for access token...")

        # Exchange code for token
        token = api_client.get_token_set_from_authorization_code(
            code=redirect_response.split("code=")[1].split("&")[0],
            redirect_uri=redirect_uri
        )

        print()
        print("=" * 60)
        print("✅ Authentication Successful!")
        print("=" * 60)
        print()
        print(f"Access Token: {token.access_token[:30]}...")
        print(f"Refresh Token: {token.refresh_token[:30]}...")
        print(f"Expires In: {token.expires_in} seconds")
        print()

        # Get tenant connections
        print("Fetching Xero organizations (tenants)...")
        identity_api = IdentityApi(api_client)
        connections = identity_api.get_connections()

        if connections:
            print()
            print("=" * 60)
            print(f"✅ Found {len(connections)} Xero Organization(s)")
            print("=" * 60)
            print()

            for i, connection in enumerate(connections, 1):
                print(f"Organization {i}:")
                print(f"  Name: {connection.tenant_name}")
                print(f"  Tenant ID: {connection.tenant_id}")
                print(f"  Type: {connection.tenant_type}")
                print()

            # Use the first tenant
            tenant_id = connections[0].tenant_id
            tenant_name = connections[0].tenant_name

            print()
            print("=" * 60)
            print("✅ Xero Connection Complete!")
            print("=" * 60)
            print()
            print(f"Organization: {tenant_name}")
            print(f"Tenant ID: {tenant_id}")
            print()
            print("💾 Add this to your .env file:")
            print(f"XERO_TENANT_ID={tenant_id}")
            print()
            print("Note: Tokens are stored in system keyring for security")
            print()

            return True
        else:
            print("❌ No Xero organizations found")
            return False

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_xero_auth()
    sys.exit(0 if success else 1)
