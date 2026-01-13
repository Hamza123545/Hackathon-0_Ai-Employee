"""
Xero MCP Request Cache (Gold Tier)

Implements request caching for zero data loss when Xero API is unavailable.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from utils.config import Config


class XeroRequestCache:
    """
    Caches failed Xero API requests for retry when API is available.
    
    Implements zero data loss by storing all failed requests locally.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize request cache.
        
        Args:
            cache_dir: Directory to store cached requests. If None, uses System/Failed_Requests/
        """
        if cache_dir is None:
            config = Config()
            cache_dir = config.system_path / 'Failed_Requests'
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def cache_request(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        error: str,
        error_code: str
    ) -> str:
        """
        Cache a failed request for later retry.
        
        Args:
            tool_name: Name of the MCP tool that failed
            parameters: Tool parameters
            error: Error message
            error_code: Error code
        
        Returns:
            Cache entry ID
        """
        cache_id = str(uuid4())
        cache_entry = {
            'id': cache_id,
            'tool_name': tool_name,
            'parameters': parameters,
            'error': error,
            'error_code': error_code,
            'cached_at': datetime.now().isoformat(),
            'retry_count': 0,
            'status': 'pending'
        }
        
        cache_file = self.cache_dir / f"{cache_id}.json"
        cache_file.write_text(
            json.dumps(cache_entry, indent=2),
            encoding='utf-8'
        )
        
        return cache_id
    
    def get_pending_requests(self) -> list[dict[str, Any]]:
        """
        Get all pending cached requests.
        
        Returns:
            List of cache entry dictionaries
        """
        pending = []
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                entry = json.loads(cache_file.read_text(encoding='utf-8'))
                if entry.get('status') == 'pending':
                    pending.append(entry)
            except Exception:
                continue
        
        return pending
    
    def mark_retried(self, cache_id: str) -> None:
        """
        Mark a cached request as retried.
        
        Args:
            cache_id: Cache entry ID
        """
        cache_file = self.cache_dir / f"{cache_id}.json"
        if cache_file.exists():
            try:
                entry = json.loads(cache_file.read_text(encoding='utf-8'))
                entry['retry_count'] = entry.get('retry_count', 0) + 1
                entry['last_retry_at'] = datetime.now().isoformat()
                cache_file.write_text(
                    json.dumps(entry, indent=2),
                    encoding='utf-8'
                )
            except Exception:
                pass
    
    def mark_completed(self, cache_id: str) -> None:
        """
        Mark a cached request as completed (successfully executed).
        
        Args:
            cache_id: Cache entry ID
        """
        cache_file = self.cache_dir / f"{cache_id}.json"
        if cache_file.exists():
            try:
                entry = json.loads(cache_file.read_text(encoding='utf-8'))
                entry['status'] = 'completed'
                entry['completed_at'] = datetime.now().isoformat()
                cache_file.write_text(
                    json.dumps(entry, indent=2),
                    encoding='utf-8'
                )
            except Exception:
                pass
    
    def mark_failed(self, cache_id: str, error: str) -> None:
        """
        Mark a cached request as permanently failed.
        
        Args:
            cache_id: Cache entry ID
            error: Final error message
        """
        cache_file = self.cache_dir / f"{cache_id}.json"
        if cache_file.exists():
            try:
                entry = json.loads(cache_file.read_text(encoding='utf-8'))
                entry['status'] = 'failed'
                entry['final_error'] = error
                entry['failed_at'] = datetime.now().isoformat()
                cache_file.write_text(
                    json.dumps(entry, indent=2),
                    encoding='utf-8'
                )
            except Exception:
                pass
    
    def delete_entry(self, cache_id: str) -> None:
        """Delete a cache entry."""
        cache_file = self.cache_dir / f"{cache_id}.json"
        if cache_file.exists():
            cache_file.unlink()


# Default cache instance
_default_cache: Optional[XeroRequestCache] = None


def get_xero_cache() -> XeroRequestCache:
    """Get default Xero request cache instance."""
    global _default_cache
    if _default_cache is None:
        _default_cache = XeroRequestCache()
    return _default_cache

