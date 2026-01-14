"""
Gmail Authentication Test Script

Tests Google OAuth 2.0 authentication for the Gmail API.
On first run, opens browser for user authorization.
"""

import os
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

def main():
    """Test Gmail authentication."""
    print("=" * 60)
    print("Gmail Authentication Test")
    print("=" * 60)
    print()

    # Paths
    script_dir = Path(__file__).parent
    credentials_path = script_dir / 'credentials.json'
    token_path = script_dir / 'gmail_token.json'

    print(f"Credentials file: {credentials_path}")
    print(f"Token file: {token_path}")
    print()

    # Check credentials file exists
    if not credentials_path.exists():
        print("ERROR: credentials.json not found!")
        print("Please download OAuth credentials from Google Cloud Console")
        return False

    print("credentials.json found")

    creds = None

    # Load existing token if available
    if token_path.exists():
        print("Loading existing token...")
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expired, refreshing...")
            creds.refresh(Request())
        else:
            print()
            print("Opening browser for Google authentication...")
            print("Please authorize the app in your browser.")
            print()

            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for future use
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print(f"Token saved to: {token_path}")

    # Test connection
    print()
    print("Testing Gmail API connection...")

    try:
        service = build('gmail', 'v1', credentials=creds)

        # Get user profile
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress', 'Unknown')

        print()
        print("=" * 60)
        print("SUCCESS! Gmail authentication working.")
        print(f"Connected as: {email}")
        print("=" * 60)

        # List recent messages
        print()
        print("Fetching recent emails...")
        results = service.users().messages().list(
            userId='me',
            maxResults=5,
            labelIds=['INBOX']
        ).execute()

        messages = results.get('messages', [])
        print(f"Found {len(messages)} recent messages in inbox")

        return True

    except Exception as e:
        print(f"ERROR: Failed to connect to Gmail API: {e}")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
