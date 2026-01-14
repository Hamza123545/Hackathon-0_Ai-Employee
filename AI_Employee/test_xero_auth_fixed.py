"""
Xero OAuth 2.0 Authentication Script (Fixed)

Authenticates with Xero using OAuth 2.0 and retrieves Tenant ID.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import webbrowser
from urllib.parse import urlencode
import secrets
import base64
import hashlib

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


def generate_pkce_pair():
    """Generate PKCE code verifier and challenge."""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge


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
        # Generate PKCE pair
        code_verifier, code_challenge = generate_pkce_pair()

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

        # Build authorization URL manually
        auth_params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': ' '.join(scopes),
            'state': secrets.token_urlsafe(16),
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }

        authorization_url = f"https://login.xero.com/identity/connect/authorize?{urlencode(auth_params)}"

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

        # Extract authorization code
        if "code=" not in redirect_response:
            print("❌ Invalid redirect URL - no authorization code found")
            return False

        auth_code = redirect_response.split("code=")[1].split("&")[0]

        print()
        print("Exchanging authorization code for access token...")

        # Exchange code for token using requests
        import requests

        token_response = requests.post(
            "https://identity.xero.com/connect/token",
            data={
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': redirect_uri,
                'code_verifier': code_verifier,
                'client_id': client_id,
                'client_secret': client_secret
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        if token_response.status_code != 200:
            print(f"❌ Token exchange failed: {token_response.status_code}")
            print(f"Response: {token_response.text}")
            return False

        token_data = token_response.json()

        print()
        print("=" * 60)
        print("✅ Authentication Successful!")
        print("=" * 60)
        print()
        print(f"Access Token: {token_data['access_token'][:30]}...")
        print(f"Refresh Token: {token_data.get('refresh_token', 'N/A')[:30]}...")
        print(f"Expires In: {token_data.get('expires_in', 'N/A')} seconds")
        print()

        # Get tenant connections
        print("Fetching Xero organizations (tenants)...")

        connections_response = requests.get(
            "https://api.xero.com/connections",
            headers={
                'Authorization': f"Bearer {token_data['access_token']}",
                'Content-Type': 'application/json'
            }
        )

        if connections_response.status_code != 200:
            print(f"❌ Failed to get connections: {connections_response.status_code}")
            print(f"Response: {connections_response.text}")
            return False

        connections = connections_response.json()

        if connections:
            print()
            print("=" * 60)
            print(f"✅ Found {len(connections)} Xero Organization(s)")
            print("=" * 60)
            print()

            for i, connection in enumerate(connections, 1):
                print(f"Organization {i}:")
                print(f"  Name: {connection.get('tenantName', 'N/A')}")
                print(f"  Tenant ID: {connection.get('tenantId', 'N/A')}")
                print(f"  Type: {connection.get('tenantType', 'N/A')}")
                print()

            # Use the first tenant
            tenant_id = connections[0].get('tenantId', '')
            tenant_name = connections[0].get('tenantName', '')

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
