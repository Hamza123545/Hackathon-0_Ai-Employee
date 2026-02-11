"""
Test Odoo Connection
"""
import os
import sys
import xmlrpc.client
from dotenv import load_dotenv

# Load env
load_dotenv()

ODOO_URL = os.environ.get("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.environ.get("ODOO_DB", "odoo")
ODOO_USERNAME = os.environ.get("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.environ.get("ODOO_PASSWORD", "admin")

def test_connection():
    print(f"Testing connection to {ODOO_URL}...")
    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if uid:
            print(f"✅ SUCCESS: Authenticated as UID {uid}")
            
            # Additional check: Get server version
            version = common.version()
            print(f"ℹ️ Server Version: {version.get('server_version')}")
            return True
        else:
            print("❌ FAILURE: Authentication returned no UID. Check credentials.")
            return False
            
    except ConnectionRefusedError:
        print(f"❌ FAILURE: Connection refused to {ODOO_URL}. Is Odoo running?")
        return False
    except Exception as e:
        print(f"❌ FAILURE: Error: {e}")
        return False

if __name__ == "__main__":
    test_connection()
