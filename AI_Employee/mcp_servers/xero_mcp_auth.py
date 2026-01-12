"""
Xero OAuth 2.0 Authentication Setup (Gold Tier)

Handles OAuth 2.0 authorization code flow for Xero API integration.
Stores tokens securely in OS credential manager using keyring.
"""

import json
import os
import webbrowser
from typing import Optional
from urllib.parse import parse_qs, urlparse

import keyring
import requests
from requests_oauthlib import OAuth2Session

# Xero OAuth 2.0 endpoints
AUTHORIZATION_BASE_URL = "https://login.xero.com/identity/connect/authorize"
TOKEN_URL = "https://identity.xero.com/connect/token"
SCOPES = [
    "accounting.transactions",
    "accounting.reports.read",
    "accounting.contacts",
    "accounting.settings"
]

# Keyring service name
KEYRING_SERVICE = "xero-mcp"


class XeroAuthManager:
    """Manages Xero OAuth 2.0 authentication and token storage."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:8000/oauth/xero/callback"
    ):
        """
        Initialize Xero Auth Manager.
        
        Args:
            client_id: Xero application client ID
            client_secret: Xero application client secret
            redirect_uri: OAuth redirect URI (must match Xero app settings)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.oauth_session = OAuth2Session(
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=SCOPES
        )
    
    def get_authorization_url(self, state: Optional[str] = None) -> tuple[str, str]:
        """
        Get authorization URL for OAuth flow.
        
        Args:
            state: Optional state parameter for CSRF protection
        
        Returns:
            Tuple of (authorization_url, state)
        """
        authorization_url, state = self.oauth_session.authorization_url(
            AUTHORIZATION_BASE_URL,
            state=state
        )
        return authorization_url, state
    
    def fetch_token(self, authorization_response: str) -> dict:
        """
        Exchange authorization code for access token.
        
        Args:
            authorization_response: Full redirect URL with authorization code
        
        Returns:
            Token dictionary with access_token, refresh_token, expires_in, etc.
        """
        token = self.oauth_session.fetch_token(
            TOKEN_URL,
            authorization_response=authorization_response,
            client_secret=self.client_secret
        )
        
        # Store token in keyring
        self._store_token(token)
        
        return token
    
    def refresh_token(self) -> dict:
        """
        Refresh access token using refresh token.
        
        Returns:
            New token dictionary
        """
        refresh_token = self._get_refresh_token()
        if not refresh_token:
            raise ValueError("No refresh token available. Re-authentication required.")
        
        token = self.oauth_session.refresh_token(
            TOKEN_URL,
            refresh_token=refresh_token,
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        
        # Store updated token
        self._store_token(token)
        
        return token
    
    def get_access_token(self) -> Optional[str]:
        """
        Get current access token from keyring.
        
        Returns:
            Access token string or None if not found
        """
        token_data = self._get_token()
        if token_data:
            return token_data.get('access_token')
        return None
    
    def get_tenant_id(self) -> Optional[str]:
        """
        Get Xero tenant ID from stored token.
        
        Returns:
            Tenant ID string or None if not found
        """
        token_data = self._get_token()
        if token_data and 'tenant_id' in token_data:
            return token_data['tenant_id']
        return None
    
    def _store_token(self, token: dict) -> None:
        """
        Store token in OS credential manager.
        
        Args:
            token: Token dictionary from OAuth flow
        """
        try:
            token_json = json.dumps(token)
            keyring.set_password(KEYRING_SERVICE, "oauth_token", token_json)
        except Exception as e:
            raise RuntimeError(f"Failed to store token in keyring: {e}")
    
    def _get_token(self) -> Optional[dict]:
        """
        Retrieve token from OS credential manager.
        
        Returns:
            Token dictionary or None if not found
        """
        try:
            token_json = keyring.get_password(KEYRING_SERVICE, "oauth_token")
            if token_json:
                return json.loads(token_json)
        except Exception as e:
            print(f"Warning: Failed to retrieve token from keyring: {e}")
        return None
    
    def _get_refresh_token(self) -> Optional[str]:
        """Get refresh token from stored token."""
        token_data = self._get_token()
        if token_data:
            return token_data.get('refresh_token')
        return None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated (has valid token)."""
        return self.get_access_token() is not None
    
    def revoke_token(self) -> None:
        """Revoke and delete stored token."""
        try:
            keyring.delete_password(KEYRING_SERVICE, "oauth_token")
        except keyring.errors.PasswordDeleteError:
            pass  # Token already deleted or doesn't exist


def setup_xero_oauth(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    redirect_uri: str = "http://localhost:8000/oauth/xero/callback"
) -> XeroAuthManager:
    """
    Interactive OAuth setup for Xero.
    
    Args:
        client_id: Xero client ID (from env or user input)
        client_secret: Xero client secret (from env or user input)
        redirect_uri: OAuth redirect URI
    
    Returns:
        XeroAuthManager instance with authenticated token
    """
    # Get credentials from environment or prompt
    if not client_id:
        client_id = os.getenv('XERO_CLIENT_ID', '')
        if not client_id:
            client_id = input("Enter Xero Client ID: ").strip()
    
    if not client_secret:
        client_secret = os.getenv('XERO_CLIENT_SECRET', '')
        if not client_secret:
            client_secret = input("Enter Xero Client Secret: ").strip()
    
    auth_manager = XeroAuthManager(client_id, client_secret, redirect_uri)
    
    # Check if already authenticated
    if auth_manager.is_authenticated():
        print("✅ Already authenticated with Xero")
        return auth_manager
    
    # Start OAuth flow
    print("Starting Xero OAuth 2.0 flow...")
    authorization_url, state = auth_manager.get_authorization_url()
    
    print(f"\nPlease visit this URL to authorize:\n{authorization_url}\n")
    print("Opening browser...")
    webbrowser.open(authorization_url)
    
    # Get callback URL from user
    callback_url = input(
        "\nAfter authorizing, paste the full callback URL here: "
    ).strip()
    
    # Exchange code for token
    token = auth_manager.fetch_token(callback_url)
    
    print("✅ Successfully authenticated with Xero!")
    print(f"Token expires in: {token.get('expires_in', 'unknown')} seconds")
    
    return auth_manager


if __name__ == '__main__':
    """Run OAuth setup interactively."""
    setup_xero_oauth()

