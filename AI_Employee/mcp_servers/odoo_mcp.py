"""
Odoo MCP Server (Gold Tier)

FastMCP server providing Odoo Community/Enterprise integration via XML-RPC.
Supports authentication, invoice creation, and financial reporting.
"""

import os
import time
import xmlrpc.client
from datetime import datetime
from typing import Any, Literal, Optional, Dict, List

from fastmcp import FastMCP
from utils.retry_manager import default_retry_manager

# Initialize MCP server
mcp = FastMCP(name="odoo-mcp")

# Configuration
ODOO_URL = os.environ.get("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.environ.get("ODOO_DB", "odoo")
ODOO_USERNAME = os.environ.get("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.environ.get("ODOO_PASSWORD", "admin")

class OdooClient:
    def __init__(self):
        self.url = ODOO_URL
        self.db = ODOO_DB
        self.username = ODOO_USERNAME
        self.password = ODOO_PASSWORD
        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        self.uid = None

    def authenticate(self):
        """Authenticate and get User ID (uid)."""
        if not self.uid:
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            if not self.uid:
                raise PermissionError("Odoo authentication failed. Check credentials.")
        return self.uid

    def execute(self, model: str, method: str, *args, **kwargs):
        """Execute a method on an Odoo model."""
        uid = self.authenticate()
        return self.models.execute_kw(self.db, uid, self.password, model, method, args, kwargs)

client = OdooClient()

@mcp.tool()
def check_connection() -> str:
    """Verify connection to Odoo server."""
    try:
        uid = client.authenticate()
        version = client.common.version()
        return f"Connected to Odoo (UID: {uid}). Server Version: {version.get('server_version')}"
    except Exception as e:
        return f"Connection failed: {str(e)}"

@mcp.tool()
def create_customer(name: str, email: str, phone: Optional[str] = None) -> Dict[str, Any]:
    """
    Create or find a customer (res.partner).
    
    Args:
        name: Name of the customer
        email: Email address
        phone: Optional phone number
    """
    def _execute():
        # Check if exists
        existing_ids = client.execute('res.partner', 'search', 
            [['email', '=', email]])
        
        if existing_ids:
            return {'id': existing_ids[0], 'status': 'existing', 'name': name}
            
        # Create new
        vals = {'name': name, 'email': email, 'customer_rank': 1}
        if phone:
            vals['phone'] = phone
            
        new_id = client.execute('res.partner', 'create', [vals])
        return {'id': new_id, 'status': 'created', 'name': name}

    try:
        return default_retry_manager.retry(_execute)
    except Exception as e:
        raise RuntimeError(f"Failed to manage customer: {str(e)}")

@mcp.tool()
def create_invoice(
    customer_name: str, 
    line_items: List[Dict[str, Any]], 
    date_invoice: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a Customer Invoice (account.move).
    
    Args:
        customer_name: Name of the customer (must exist or email provided in separate call)
        line_items: List of dicts with {'description': str, 'quantity': float, 'price_unit': float}
        date_invoice: YYYY-MM-DD (defaults to today)
    """
    def _execute():
        # 1. Find Customer
        partner_ids = client.execute('res.partner', 'search', [['name', 'ilike', customer_name]])
        if not partner_ids:
            raise ValueError(f"Customer '{customer_name}' not found. Create them first.")
        partner_id = partner_ids[0]

        # 2. Prepare Line Items
        # Odoo One2many format: (0, 0, {values})
        invoice_lines = []
        for item in line_items:
            line_vals = {
                'name': item.get('description', 'Service'),
                'quantity': float(item.get('quantity', 1.0)),
                'price_unit': float(item.get('price_unit', 0.0)),
            }
            invoice_lines.append((0, 0, line_vals))

        # 3. Create Invoice (account.move)
        move_vals = {
            'move_type': 'out_invoice', # Customer Invoice
            'partner_id': partner_id,
            'invoice_date': date_invoice or datetime.now().strftime('%Y-%m-%d'),
            'invoice_line_ids': invoice_lines,
        }
        
        invoice_id = client.execute('account.move', 'create', [move_vals])
        
        # 4. Get Name (Number)
        # Note: Name is usually 'Draft' until posted
        invoice_data = client.execute('account.move', 'read', [invoice_id], ['name', 'state', 'amount_total'])
        
        return {
            'invoice_id': invoice_id,
            'data': invoice_data[0],
            'approval_request_id': 'generated_by_approval_workflow' # Consistent with Xero MCP
        }

    try:
        return default_retry_manager.retry(_execute)
    except Exception as e:
        raise RuntimeError(f"Failed to create invoice: {str(e)}")

@mcp.tool()
def get_financial_stats(period_start: str, period_end: str) -> Dict[str, Any]:
    """
    Get revenue stats for CEO Briefing.
    Queries posted invoices in the date range.
    """
    def _execute():
        domain = [
            ['move_type', '=', 'out_invoice'],
            ['state', '=', 'posted'],
            ['invoice_date', '>=', period_start],
            ['invoice_date', '<=', period_end]
        ]
        
        # Search
        invoice_ids = client.execute('account.move', 'search', domain)
        
        # Read and Sum
        if not invoice_ids:
            return {'revenue': 0.0, 'invoice_count': 0}
            
        invoices = client.execute('account.move', 'read', invoice_ids, ['amount_untaxed'])
        total_revenue = sum(inv['amount_untaxed'] for inv in invoices)
        
        return {
            'period': f"{period_start} to {period_end}",
            'revenue': total_revenue,
            'invoice_count': len(invoices)
        }

    try:
        return default_retry_manager.retry(_execute)
    except Exception as e:
        raise RuntimeError(f"Failed to get stats: {str(e)}")

if __name__ == '__main__':
    mcp.run()
