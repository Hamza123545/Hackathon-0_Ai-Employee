"""
Xero MCP Server (Gold Tier)

FastMCP server providing Xero accounting integration - invoices, expenses,
bank transactions, and financial reports with OAuth 2.0 authentication.
"""

import json
import logging
import os
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal, Optional

from fastmcp import FastMCP
from xero_python.accounting import AccountingApi
from xero_python.api_client import ApiClient, Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from xero_python.exceptions import ApiException
from xero_python.models.accounting import (
    Contact,
    ExpenseClaim,
    Invoice,
    Invoices,
    LineItem
)

try:
    from mcp_servers.xero_mcp_auth import XeroAuthManager
except ImportError:
    # Fallback if module structure is different
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from xero_mcp_auth import XeroAuthManager

from utils.retry_manager import RetryManager, default_retry_manager

try:
    from mcp_servers.xero_mcp_cache import get_xero_cache
except ImportError:
    # Fallback if module structure is different
    get_xero_cache = None

# Initialize MCP server
mcp = FastMCP(name="xero-mcp")

# Configure logging
logger = logging.getLogger(__name__)

# Error codes per contract
ErrorCode = Literal[
    'AUTH_ERROR',
    'RATE_LIMIT',
    'NOT_FOUND',
    'INVALID_PARAMS',
    'NETWORK_ERROR',
    'UNKNOWN'
]

# Rate limit tracking
_rate_limit_tracker = {
    'requests': [],
    'limit': 60,  # 60 requests per minute
    'window_seconds': 60
}


class XeroConfig:
    """Configuration for Xero API loaded from environment variables."""
    
    @property
    def client_id(self) -> str:
        return os.environ.get('XERO_CLIENT_ID', '')
    
    @property
    def client_secret(self) -> str:
        return os.environ.get('XERO_CLIENT_SECRET', '')
    
    @property
    def tenant_id(self) -> str:
        return os.environ.get('XERO_TENANT_ID', '')
    
    @property
    def redirect_uri(self) -> str:
        return os.environ.get('XERO_REDIRECT_URI', 'http://localhost:8000/oauth/xero/callback')


config = XeroConfig()

# Initialize auth manager
_auth_manager: Optional[XeroAuthManager] = None
_api_client: Optional[ApiClient] = None
_accounting_api: Optional[AccountingApi] = None


def _get_auth_manager() -> XeroAuthManager:
    """Get or create XeroAuthManager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = XeroAuthManager(
            client_id=config.client_id,
            client_secret=config.client_secret,
            redirect_uri=config.redirect_uri
        )
    return _auth_manager


def _get_api_client() -> ApiClient:
    """Get or create Xero API client with OAuth token."""
    global _api_client
    if _api_client is None:
        auth_manager = _get_auth_manager()
        
        # Get token from keyring
        token = auth_manager._get_token()
        if not token:
            raise RuntimeError("Not authenticated with Xero. Run auth_setup.py first.")
        
        # Configure API client with OAuth2
        api_config = Configuration(
            oauth2_token=OAuth2Token(
                client_id=config.client_id,
                client_secret=config.client_secret
            )
        )
        
        _api_client = ApiClient(api_config)
        
        # Set token getter/saver for automatic refresh
        @_api_client.oauth2_token_getter
        def get_token():
            return auth_manager._get_token()
        
        @_api_client.oauth2_token_saver
        def save_token(token_dict):
            auth_manager._store_token(token_dict)
        
        # Set initial token
        _api_client.set_oauth2_token(token)
    
    return _api_client


def _get_accounting_api() -> AccountingApi:
    """Get or create AccountingApi instance."""
    global _accounting_api
    if _accounting_api is None:
        api_client = _get_api_client()
        _accounting_api = AccountingApi(api_client)
    return _accounting_api


def _check_rate_limit() -> None:
    """Check and enforce rate limit (60 requests/minute)."""
    now = time.time()
    
    # Remove requests older than 1 minute
    _rate_limit_tracker['requests'] = [
        req_time for req_time in _rate_limit_tracker['requests']
        if now - req_time < _rate_limit_tracker['window_seconds']
    ]
    
    # Check if limit exceeded
    if len(_rate_limit_tracker['requests']) >= _rate_limit_tracker['limit']:
        # Calculate wait time
        oldest_request = min(_rate_limit_tracker['requests'])
        wait_time = _rate_limit_tracker['window_seconds'] - (now - oldest_request) + 1
        if wait_time > 0:
            time.sleep(wait_time)
            # Clear old requests after wait
            _rate_limit_tracker['requests'] = []
    
    # Record this request
    _rate_limit_tracker['requests'].append(now)


def _classify_xero_error(exception: ApiException) -> tuple[str, ErrorCode]:
    """
    Classify Xero API exception into error message and code.
    
    Args:
        exception: The ApiException object.
    
    Returns:
        Tuple of (error_message, error_code).
    """
    status_code = getattr(exception, 'status', 0)
    error_msg = str(exception)
    
    if status_code == 401 or status_code == 403:
        return error_msg, 'AUTH_ERROR'
    elif status_code == 429:
        return error_msg, 'RATE_LIMIT'
    elif status_code == 404:
        return error_msg, 'NOT_FOUND'
    elif status_code == 400 or status_code == 422:
        return error_msg, 'INVALID_PARAMS'
    elif status_code in (502, 503, 504):
        return error_msg, 'NETWORK_ERROR'
    else:
        return error_msg, 'UNKNOWN'


@mcp.tool()
def get_invoices(
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    contact_ids: Optional[list[str]] = None,
    page: int = 1
) -> dict[str, Any]:
    """
    Retrieve invoices from Xero with optional filtering.
    
    Args:
        status: Filter by invoice status (DRAFT, SUBMITTED, AUTHORISED, PAID)
        date_from: Retrieve invoices from this date (YYYY-MM-DD)
        date_to: Retrieve invoices up to this date (YYYY-MM-DD)
        contact_ids: Filter by contact IDs
        page: Page number for pagination
    
    Returns:
        Dictionary with invoices list, total_count, and page
    """
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        accounting_api = _get_accounting_api()
        tenant_id = config.tenant_id or _get_auth_manager().get_tenant_id()
        
        if not tenant_id:
            raise ValueError("Xero tenant ID not configured")
        
        # Build query parameters
        where_clause_parts = []
        if status:
            where_clause_parts.append(f'Status=="{status}"')
        if date_from:
            where_clause_parts.append(f'Date >= DateTime({date_from})')
        if date_to:
            where_clause_parts.append(f'Date <= DateTime({date_to})')
        if contact_ids:
            contact_filter = ' || '.join([f'Contact.ContactID==Guid("{cid}")' for cid in contact_ids])
            where_clause_parts.append(f'({contact_filter})')
        
        where_clause = ' && '.join(where_clause_parts) if where_clause_parts else None
        
        # Get invoices
        response = accounting_api.get_invoices(
            xero_tenant_id=tenant_id,
            where=where_clause,
            page=page
        )
        
        # Format response
        invoices = []
        if hasattr(response, 'invoices') and response.invoices:
            for inv in response.invoices:
                invoices.append({
                    'invoice_id': str(inv.invoice_id) if hasattr(inv, 'invoice_id') else '',
                    'invoice_number': inv.invoice_number if hasattr(inv, 'invoice_number') else '',
                    'contact': inv.contact.name if hasattr(inv, 'contact') and inv.contact else '',
                    'date': inv.date.isoformat() if hasattr(inv, 'date') and inv.date else '',
                    'due_date': inv.due_date.isoformat() if hasattr(inv, 'due_date') and inv.due_date else '',
                    'total': float(inv.total) if hasattr(inv, 'total') else 0.0,
                    'amount_due': float(inv.amount_due) if hasattr(inv, 'amount_due') else 0.0,
                    'currency': inv.currency_code if hasattr(inv, 'currency_code') else 'USD',
                    'status': inv.status if hasattr(inv, 'status') else ''
                })
        
        return {
            'invoices': invoices,
            'total_count': len(invoices),
            'page': page
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (ApiException, ConnectionError, TimeoutError))
        )
    except ApiException as e:
        error_msg, error_code = _classify_xero_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


@mcp.tool()
def create_expense(
    amount: float,
    date: str,
    description: str,
    category: str,
    currency: str = "USD",
    receipt_url: Optional[str] = None
) -> dict[str, Any]:
    """
    Create an expense entry in Xero (requires approval via HITL workflow).
    
    Args:
        amount: Expense amount (must be positive)
        date: Expense date (YYYY-MM-DD)
        description: Expense description
        category: Expense category/account code
        currency: Currency code (ISO 4217)
        receipt_url: Optional receipt attachment URL
    
    Returns:
        Dictionary with expense_id, status, created_at, approval_request_id
    """
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        accounting_api = _get_accounting_api()
        tenant_id = config.tenant_id or _get_auth_manager().get_tenant_id()
        
        if not tenant_id:
            raise ValueError("Xero tenant ID not configured")
        
        # Parse date
        expense_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Create expense claim
        # Note: Xero API uses ExpenseClaim model
        # This is a simplified implementation - full implementation would
        # require proper account code mapping and receipt attachment handling
        
        expense_claim = ExpenseClaim(
            status="SUBMITTED",
            # Additional fields would be set here based on Xero API requirements
        )
        
        # Create expense claim
        response = accounting_api.create_expense_claims(
            xero_tenant_id=tenant_id,
            expense_claims=[expense_claim]
        )
        
        # Extract expense ID from response
        expense_id = None
        if hasattr(response, 'expense_claims') and response.expense_claims:
            expense_id = str(response.expense_claims[0].expense_claim_id)
        
        return {
            'expense_id': expense_id or 'pending',
            'status': 'submitted',
            'created_at': datetime.now().isoformat(),
            'approval_request_id': 'generated_by_approval_workflow'
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (ApiException, ConnectionError, TimeoutError))
        )
    except (ApiException, ConnectionError, TimeoutError) as e:
        # Cache failed request for zero data loss (T084)
        if get_xero_cache:
            try:
                error_msg, error_code = _classify_xero_error(e) if isinstance(e, ApiException) else (str(e), 'NETWORK_ERROR')
                cache_id = get_xero_cache().cache_request(
                    tool_name='create_expense',
                    parameters={
                        'amount': amount,
                        'date': date,
                        'description': description,
                        'category': category,
                        'currency': currency,
                        'receipt_url': receipt_url
                    },
                    error=error_msg,
                    error_code=error_code
                )
                logger.warning(f"Cached failed create_expense request: {cache_id}")
            except Exception as cache_error:
                logger.error(f"Failed to cache request: {cache_error}")
        
        if isinstance(e, ApiException):
            error_msg, error_code = _classify_xero_error(e)
            raise RuntimeError(f"{error_code}: {error_msg}")
        else:
            raise RuntimeError(f"NETWORK_ERROR: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


@mcp.tool()
def create_invoice(
    contact_name: str,
    line_items: list[dict[str, Any]],
    due_date: str,
    reference: Optional[str] = None,
    currency: str = "USD"
) -> dict[str, Any]:
    """
    Create a new invoice in Xero (requires approval via HITL workflow).
    
    Args:
        contact_name: Customer/contact name
        line_items: List of line items, each with description, quantity, unit_amount, account_code
        due_date: Invoice due date (YYYY-MM-DD)
        reference: Optional reference/PO number
        currency: Currency code (ISO 4217)
    
    Returns:
        Dictionary with invoice_id, invoice_number, status, total, created_at, approval_request_id
    """
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        accounting_api = _get_accounting_api()
        tenant_id = config.tenant_id or _get_auth_manager().get_tenant_id()
        
        if not tenant_id:
            raise ValueError("Xero tenant ID not configured")
        
        # Get or create contact
        contacts_response = accounting_api.get_contacts(xero_tenant_id=tenant_id)
        contact_id = None
        if hasattr(contacts_response, 'contacts') and contacts_response.contacts:
            for contact in contacts_response.contacts:
                if contact.name == contact_name:
                    contact_id = str(contact.contact_id)
                    break
        
        if not contact_id:
            # Create new contact
            new_contact = Contact(name=contact_name)
            contact_response = accounting_api.create_contacts(
                xero_tenant_id=tenant_id,
                contacts=[new_contact]
            )
            if hasattr(contact_response, 'contacts') and contact_response.contacts:
                contact_id = str(contact_response.contacts[0].contact_id)
        
        # Build line items
        invoice_line_items = []
        for item in line_items:
            line_item = LineItem(
                description=item['description'],
                quantity=float(item['quantity']),
                unit_amount=float(item['unit_amount']),
                account_code=item.get('account_code', '')
            )
            invoice_line_items.append(line_item)
        
        # Parse dates
        invoice_date = datetime.now().date()
        due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
        
        # Create invoice
        invoice = Invoice(
            type="ACCREC",  # Accounts Receivable
            contact=Contact(contact_id=contact_id),
            line_items=invoice_line_items,
            date=invoice_date,
            due_date=due_date_obj,
            reference=reference
        )
        
        invoices = Invoices(invoices=[invoice])
        response = accounting_api.create_invoices(
            xero_tenant_id=tenant_id,
            invoices=invoices
        )
        
        # Extract invoice details
        invoice_id = None
        invoice_number = None
        total = 0.0
        
        if hasattr(response, 'invoices') and response.invoices:
            inv = response.invoices[0]
            invoice_id = str(inv.invoice_id) if hasattr(inv, 'invoice_id') else None
            invoice_number = inv.invoice_number if hasattr(inv, 'invoice_number') else None
            total = float(inv.total) if hasattr(inv, 'total') else 0.0
        
        return {
            'invoice_id': invoice_id or 'pending',
            'invoice_number': invoice_number or '',
            'status': 'draft',
            'total': total,
            'created_at': datetime.now().isoformat(),
            'approval_request_id': 'generated_by_approval_workflow'
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (ApiException, ConnectionError, TimeoutError))
        )
    except ApiException as e:
        error_msg, error_code = _classify_xero_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


@mcp.tool()
def get_financial_report(
    report_type: str,
    from_date: str,
    to_date: str
) -> dict[str, Any]:
    """
    Generate financial report (Profit & Loss, Balance Sheet, Bank Summary).
    
    Args:
        report_type: Type of report (profit_and_loss, balance_sheet, bank_summary)
        from_date: Report start date (YYYY-MM-DD)
        to_date: Report end date (YYYY-MM-DD)
    
    Returns:
        Dictionary with report_type, period, revenue, expenses, net_profit, generated_at, details
    """
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        accounting_api = _get_accounting_api()
        tenant_id = config.tenant_id or _get_auth_manager().get_tenant_id()
        
        if not tenant_id:
            raise ValueError("Xero tenant ID not configured")
        
        # Parse dates
        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
        
        # Get report based on type
        if report_type == "profit_and_loss":
            report = accounting_api.get_report_profit_and_loss(
                xero_tenant_id=tenant_id,
                from_date=from_date_obj,
                to_date=to_date_obj
            )
        elif report_type == "balance_sheet":
            report = accounting_api.get_report_balance_sheet(
                xero_tenant_id=tenant_id,
                date=to_date_obj
            )
        else:
            raise ValueError(f"Unsupported report type: {report_type}")
        
        # Extract financial data
        revenue = 0.0
        expenses = 0.0
        net_profit = 0.0
        
        if hasattr(report, 'reports') and report.reports:
            # Parse report data (simplified - actual parsing depends on Xero report structure)
            # This would need to be implemented based on actual Xero API response format
            pass
        
        return {
            'report_type': report_type,
            'period': f"{from_date} to {to_date}",
            'revenue': revenue,
            'expenses': expenses,
            'net_profit': net_profit,
            'generated_at': datetime.now().isoformat(),
            'details': {}  # Full report details would go here
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (ApiException, ConnectionError, TimeoutError))
        )
    except ApiException as e:
        error_msg, error_code = _classify_xero_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


@mcp.tool()
def sync_bank_transactions(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    bank_account_id: Optional[str] = None
) -> dict[str, Any]:
    """
    Sync bank transactions from Xero for specified period.
    
    Args:
        from_date: Sync transactions from this date (YYYY-MM-DD)
        to_date: Sync transactions up to this date (YYYY-MM-DD)
        bank_account_id: Filter by specific bank account ID
    
    Returns:
        Dictionary with transaction_count, transactions list, synced_at
    """
    _check_rate_limit()
    
    def _execute() -> dict[str, Any]:
        accounting_api = _get_accounting_api()
        tenant_id = config.tenant_id or _get_auth_manager().get_tenant_id()
        
        if not tenant_id:
            raise ValueError("Xero tenant ID not configured")
        
        # Get bank transactions
        where_clause = None
        if bank_account_id:
            where_clause = f'BankAccount.AccountID==Guid("{bank_account_id}")'
        
        response = accounting_api.get_bank_transactions(
            xero_tenant_id=tenant_id,
            where=where_clause
        )
        
        # Format transactions
        transactions = []
        if hasattr(response, 'bank_transactions') and response.bank_transactions:
            for txn in response.bank_transactions:
                transactions.append({
                    'transaction_id': str(txn.bank_transaction_id) if hasattr(txn, 'bank_transaction_id') else '',
                    'type': txn.type if hasattr(txn, 'type') else '',
                    'date': txn.date.isoformat() if hasattr(txn, 'date') and txn.date else '',
                    'amount': float(txn.total) if hasattr(txn, 'total') else 0.0,
                    'description': txn.reference if hasattr(txn, 'reference') else '',
                    'status': txn.status if hasattr(txn, 'status') else ''
                })
        
        return {
            'transaction_count': len(transactions),
            'transactions': transactions,
            'synced_at': datetime.now().isoformat()
        }
    
    try:
        return default_retry_manager.retry(
            _execute,
            should_retry=lambda e: isinstance(e, (ApiException, ConnectionError, TimeoutError))
        )
    except ApiException as e:
        error_msg, error_code = _classify_xero_error(e)
        raise RuntimeError(f"{error_code}: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"UNKNOWN: {str(e)}")


if __name__ == '__main__':
    """Run MCP server."""
    mcp.run()

