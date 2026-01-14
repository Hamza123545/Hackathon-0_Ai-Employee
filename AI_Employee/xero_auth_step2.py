"""
Xero OAuth Step 2: Token Exchange

Exchanges authorization code for access token using saved code_verifier.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import json

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


def exchange_code_for_token(redirect_url):
    """Exchange authorization code for access token."""
    print("=" * 60)
    print("Xero OAuth Step 2: Token Exchange")
    print("=" * 60)
    print()

    # Get credentials
    client_id = os.getenv('XERO_CLIENT_ID', '')
    client_secret = os.getenv('XERO_CLIENT_SECRET', '')
    redirect_uri = os.getenv('XERO_REDIRECT_URI', 'http://localhost:8000/oauth/xero/callback')

    # Load code_verifier from step 1
    verifier_file = Path(__file__).parent / 'xero_code_verifier.json'
    if not verifier_file.exists():
        print("❌ Code verifier not found. Please run xero_auth_step1.py first.")
        return False

    with open(verifier_file, 'r') as f:
        verifier_data = json.load(f)
        code_verifier = verifier_data['code_verifier']

    print(f"✅ Client ID: {client_id[:20]}...")
    print(f"✅ Code verifier loaded")
    print()

    try:
        # Extract authorization code from redirect URL
        if "code=" not in redirect_url:
            print("❌ Invalid redirect URL - no authorization code found")
            return False

        auth_code = redirect_url.split("code=")[1].split("&")[0]
        print(f"✅ Authorization code: {auth_code[:30]}...")
        print()

        print("Exchanging authorization code for access token...")

        # Exchange code for token
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

            # Update .env file
            print("Updating .env file with access token and tenant ID...")

            env_file = Path(__file__).parent / '.env'
            with open(env_file, 'r', encoding='utf-8') as f:
                env_content = f.read()

            # Update XERO_TENANT_ID
            if 'XERO_TENANT_ID=' in env_content:
                lines = env_content.split('\n')
                new_lines = []
                for line in lines:
                    if line.startswith('XERO_TENANT_ID='):
                        new_lines.append(f"XERO_TENANT_ID={tenant_id}")
                    else:
                        new_lines.append(line)
                env_content = '\n'.join(new_lines)

            # Add XERO_ACCESS_TOKEN
            if 'XERO_ACCESS_TOKEN=' in env_content:
                lines = env_content.split('\n')
                new_lines = []
                for line in lines:
                    if line.startswith('XERO_ACCESS_TOKEN='):
                        new_lines.append(f"XERO_ACCESS_TOKEN={token_data['access_token']}")
                    else:
                        new_lines.append(line)
                env_content = '\n'.join(new_lines)
            else:
                # Add after XERO_REDIRECT_URI
                lines = env_content.split('\n')
                new_lines = []
                for line in lines:
                    new_lines.append(line)
                    if line.startswith('XERO_REDIRECT_URI='):
                        new_lines.append(f"XERO_ACCESS_TOKEN={token_data['access_token']}")
                env_content = '\n'.join(new_lines)

            # Add XERO_REFRESH_TOKEN
            if 'XERO_REFRESH_TOKEN=' in env_content:
                lines = env_content.split('\n')
                new_lines = []
                for line in lines:
                    if line.startswith('XERO_REFRESH_TOKEN='):
                        new_lines.append(f"XERO_REFRESH_TOKEN={token_data.get('refresh_token', '')}")
                    else:
                        new_lines.append(line)
                env_content = '\n'.join(new_lines)
            else:
                # Add after XERO_ACCESS_TOKEN
                lines = env_content.split('\n')
                new_lines = []
                for line in lines:
                    new_lines.append(line)
                    if line.startswith('XERO_ACCESS_TOKEN='):
                        new_lines.append(f"XERO_REFRESH_TOKEN={token_data.get('refresh_token', '')}")
                env_content = '\n'.join(new_lines)

            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)

            print()
            print("=" * 60)
            print("✅ Xero Setup Complete!")
            print("=" * 60)
            print()
            print(f"Organization: {tenant_name}")
            print(f"Tenant ID: {tenant_id}")
            print()
            print("Xero is now fully configured and ready to use!")
            print()

            # Clean up code_verifier file
            verifier_file.unlink()
            print("✅ Cleaned up temporary files")
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
    # Extract redirect URL from command line argument
    if len(sys.argv) < 2:
        print("Usage: python xero_auth_step2.py <redirect_url>")
        print()
        print("Example:")
        print('  python xero_auth_step2.py "http://localhost:8000/oauth/xero/callback?code=...&scope=..."')
        sys.exit(1)

    redirect_url = sys.argv[1]
    success = exchange_code_for_token(redirect_url)
    sys.exit(0 if success else 1)
