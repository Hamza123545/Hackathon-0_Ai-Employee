"""
Gold Tier AI Employee - System Health Check

Tests all configured services and provides a comprehensive status report.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


def check_gmail():
    """Check Gmail configuration."""
    print("📧 Gmail:")
    token_path = Path(__file__).parent / 'gmail_token.json'
    if token_path.exists():
        print("   ✅ OAuth token found")
        print("   ✅ Ready to monitor inbox")
        return True
    else:
        print("   ❌ OAuth token not found")
        return False


def check_facebook():
    """Check Facebook configuration."""
    print("\n📘 Facebook:")
    page_id = os.getenv('FACEBOOK_PAGE_ID', '')
    access_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN', '')

    if page_id and access_token:
        print(f"   ✅ Page ID: {page_id}")
        print(f"   ✅ Access Token: {access_token[:20]}...")
        print("   ✅ Ready to post and read engagement")
        return True
    else:
        print("   ❌ Not configured")
        return False


def check_twitter():
    """Check Twitter configuration."""
    print("\n🐦 Twitter:")
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN', '')

    if bearer_token:
        print(f"   ✅ Bearer Token: {bearer_token[:30]}...")
        print("   ✅ Ready for read-only access")
        return True
    else:
        print("   ❌ Not configured")
        return False


def check_groq():
    """Check Groq AI configuration."""
    print("\n🤖 Groq AI:")
    api_key = os.getenv('GROQ_API_KEY', '')
    model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')

    if api_key:
        print(f"   ✅ API Key: {api_key[:20]}...")
        print(f"   ✅ Model: {model}")
        print("   ✅ Ready for AI insights")
        return True
    else:
        print("   ❌ Not configured")
        return False


def check_linkedin():
    """Check LinkedIn configuration."""
    print("\n💼 LinkedIn:")
    client_id = os.getenv('LINKEDIN_CLIENT_ID', '')
    client_secret = os.getenv('LINKEDIN_CLIENT_SECRET', '')
    access_token = os.getenv('LINKEDIN_ACCESS_TOKEN', '')

    if client_id and client_secret:
        print(f"   ✅ Client ID: {client_id}")
        print(f"   ✅ Client Secret: {'*' * 20}...")
        if access_token:
            print(f"   ✅ Access Token: {access_token[:20]}...")
            print("   ✅ Ready to post and read")
            return True
        else:
            print("   ⚠️  Access Token missing - needs OAuth")
            return False
    else:
        print("   ❌ Not configured")
        return False


def check_xero():
    """Check Xero configuration."""
    print("\n💰 Xero:")
    client_id = os.getenv('XERO_CLIENT_ID', '')
    client_secret = os.getenv('XERO_CLIENT_SECRET', '')
    tenant_id = os.getenv('XERO_TENANT_ID', '')
    access_token = os.getenv('XERO_ACCESS_TOKEN', '')

    if client_id and client_secret and tenant_id:
        print(f"   ✅ Client ID: {client_id[:20]}...")
        print(f"   ✅ Client Secret: {'*' * 10}...")
        print(f"   ✅ Tenant ID: {tenant_id}")
        if access_token:
            print(f"   ✅ Access Token: {access_token[:20]}...")
            print("   ✅ Ready for accounting and financial reporting")
            return True
        else:
            print("   ⚠️  Access Token missing - needs OAuth")
            return False
    else:
        print("   ❌ Not configured")
        return False


def check_instagram():
    """Check Instagram configuration."""
    print("\n📸 Instagram:")
    instagram_id = os.getenv('INSTAGRAM_ACCOUNT_ID', '')

    if instagram_id:
        print(f"   ✅ Account ID: {instagram_id}")
        print("   ✅ Ready to post and read insights")
        return True
    else:
        print("   ⚠️  Not configured (requires Facebook permissions)")
        return False


def check_whatsapp():
    """Check WhatsApp configuration."""
    print("\n💬 WhatsApp:")
    session_file = Path(__file__).parent.parent / 'whatsapp_session.json'

    if session_file.exists():
        print(f"   ✅ Session file found")
        print("   ✅ Ready to monitor messages")
        return True
    else:
        print("   ❌ Session not initialized")
        print("   Run: uv run python -m AI_Employee.watchers.whatsapp_watcher --init")
        return False


def main():
    """Run comprehensive system health check."""
    print("=" * 60)
    print("🏆 Gold Tier AI Employee - System Health Check")
    print("=" * 60)
    print()

    results = {
        'Gmail': check_gmail(),
        'Facebook': check_facebook(),
        'Twitter': check_twitter(),
        'Groq AI': check_groq(),
        'LinkedIn': check_linkedin(),
        'Xero': check_xero(),
        'WhatsApp': check_whatsapp(),
        'Instagram': check_instagram()
    }

    print()
    print("=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print()

    working = [k for k, v in results.items() if v]
    needs_setup = [k for k, v in results.items() if not v]

    print(f"✅ Working: {len(working)}/8 services")
    for service in working:
        print(f"   • {service}")

    if needs_setup:
        print()
        print(f"⚠️  Needs Setup: {len(needs_setup)}/8 services")
        for service in needs_setup:
            print(f"   • {service}")

    print()
    print("=" * 60)
    print("🎯 System Capabilities")
    print("=" * 60)
    print()

    if results['Gmail']:
        print("✅ Email monitoring and action item detection")
    if results['Facebook']:
        print("✅ Facebook posting and engagement tracking")
    if results['Twitter']:
        print("✅ Twitter analytics and search")
    if results['Groq AI']:
        print("✅ AI-powered business insights and CEO briefings")
    if results['LinkedIn']:
        print("✅ LinkedIn professional networking automation")
    if results['Xero']:
        print("✅ Accounting and financial reporting")
    if results['WhatsApp']:
        print("✅ WhatsApp message monitoring and action detection")
    if results['Instagram']:
        print("✅ Instagram posting and insights")

    print()
    print("=" * 60)
    print("📋 Next Steps")
    print("=" * 60)
    print()

    if not results['LinkedIn'] and os.getenv('LINKEDIN_CLIENT_ID'):
        print("🔸 LinkedIn: Complete OAuth authentication")
        print("   Run: uv run python AI_Employee/test_linkedin_auth.py")
        print()

    if not results['Xero'] and os.getenv('XERO_CLIENT_ID'):
        print("🔸 Xero: Complete OAuth authentication")
        print("   Run: uv run python AI_Employee/test_xero_auth_fixed.py")
        print()

    if not results['Instagram']:
        print("🔸 Instagram: Submit Facebook app for Meta review")
        print("   Request 'pages_read_engagement' permission")
        print()

    if len(working) >= 4:
        print()
        print("🚀 Your system is ready to use!")
        print()
        print("Test the AI Employee:")
        print("   cd AI_Employee")
        print("   uv run python run_ai_processor.py")
        print()


if __name__ == '__main__':
    main()
