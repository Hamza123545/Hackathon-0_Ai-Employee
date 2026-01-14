"""
Xero MCP Server Health Check Script (Gold Tier)

Tests connection to Xero API and verifies authentication.
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
    Test Xero API connection and authentication.

    Returns:
        True if connection successful, False otherwise
    """
    # Check environment variables directly (standalone test)
    client_id = os.getenv('XERO_CLIENT_ID', '')
    client_secret = os.getenv('XERO_CLIENT_SECRET', '')
    tenant_id = os.getenv('XERO_TENANT_ID', '')

    if not client_id or not client_secret:
        print("❌ Xero credentials not configured")
        print("   Set XERO_CLIENT_ID and XERO_CLIENT_SECRET environment variables")
        return False

    print(f"✅ Xero Client ID: {client_id[:8]}..." if len(client_id) > 8 else f"✅ Xero Client ID: {client_id}")
    print(f"✅ Xero Client Secret: {'*' * 8}...")

    # Initialize auth manager
    try:
        from mcp_servers.xero_mcp_auth import XeroAuthManager

        auth_manager = XeroAuthManager(
            client_id=client_id,
            client_secret=client_secret
        )

        # Check if authenticated
        if not auth_manager.is_authenticated():
            print("❌ Not authenticated with Xero")
            print("   Run: python mcp_servers/xero_mcp_auth.py")
            return False

        print("✅ Xero authentication token found")

        # Get tenant ID
        stored_tenant_id = auth_manager.get_tenant_id()
        if tenant_id:
            print(f"✅ Xero Tenant ID: {tenant_id}")
        elif stored_tenant_id:
            print(f"✅ Xero Tenant ID (from token): {stored_tenant_id}")
        else:
            print("⚠️  Xero Tenant ID not found (may need to set XERO_TENANT_ID)")

        # Test API connection by getting organization details
        try:
            from xero_python.accounting import AccountingApi
            from xero_python.api_client import ApiClient, Configuration
            from xero_python.api_client.oauth2 import OAuth2Token

            token = auth_manager._get_token()
            if not token:
                print("❌ Failed to retrieve token from keyring")
                return False

            api_config = Configuration(
                oauth2_token=OAuth2Token(
                    client_id=client_id,
                    client_secret=client_secret
                )
            )

            api_client = ApiClient(api_config)
            api_client.set_oauth2_token(token)

            accounting_api = AccountingApi(api_client)
            test_tenant_id = tenant_id or stored_tenant_id

            if test_tenant_id:
                # Try to get accounts as a simple connection test
                accounts = accounting_api.get_accounts(xero_tenant_id=test_tenant_id, page=1)
                print("✅ Successfully connected to Xero API")
                print("   Organization accessible, accounts retrieved")
                return True
            else:
                print("⚠️  Cannot test API connection without tenant ID")
                print("   Set XERO_TENANT_ID environment variable")
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
    print("Xero MCP Server - Connection Test")
    print("=" * 60)
    print()

    success = test_connection()

    print()
    print("=" * 60)
    if success:
        print("✅ Xero connection test PASSED")
    else:
        print("❌ Xero connection test FAILED")
    print("=" * 60)

    sys.exit(0 if success else 1)
