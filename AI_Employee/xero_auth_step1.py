"""
Xero OAuth Step 1: Generate Authorization URL

Generates authorization URL and saves code_verifier for step 2.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlencode
import secrets
import base64
import hashlib
import json

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


def generate_auth_url():
    """Generate Xero authorization URL."""
    print("=" * 60)
    print("Xero OAuth Step 1: Authorization URL")
    print("=" * 60)
    print()

    # Get credentials
    client_id = os.getenv('XERO_CLIENT_ID', '')
    redirect_uri = os.getenv('XERO_REDIRECT_URI', 'http://localhost:8000/oauth/xero/callback')

    if not client_id:
        print("❌ XERO_CLIENT_ID not configured")
        return False

    print(f"✅ Client ID: {client_id[:20]}...")
    print(f"✅ Redirect URI: {redirect_uri}")
    print()

    try:
        # Generate PKCE pair
        code_verifier, code_challenge = generate_pkce_pair()

        # Save code_verifier for step 2
        verifier_file = Path(__file__).parent / 'xero_code_verifier.json'
        with open(verifier_file, 'w') as f:
            json.dump({'code_verifier': code_verifier}, f)

        print(f"✅ Code verifier saved to: {verifier_file}")
        print()

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
        print("📋 Authorization URL Generated")
        print("=" * 60)
        print()
        print("Copy and paste this URL into your browser:")
        print()
        print(authorization_url)
        print()
        print("=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print()
        print("1. Open the URL above in your browser")
        print("2. Authorize the application")
        print("3. Copy the ENTIRE redirect URL from your browser")
        print("4. Run: uv run python AI_Employee/xero_auth_step2.py <redirect_url>")
        print()

        return True

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = generate_auth_url()
    sys.exit(0 if success else 1)
