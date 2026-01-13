"""
MCP Health Monitoring Daemon (Gold Tier - Phase 8)

Monitors health of all MCP servers every 5 minutes and updates status files.
"""

import logging
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import Config
from utils.health_checker import HealthChecker, get_default_health_checker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_xero_health() -> tuple[bool, float, str | None]:
    """Check Xero MCP server health."""
    try:
        from mcp_servers.xero_mcp import get_invoices
        
        start_time = time.time()
        # Try a simple read-only operation
        result = get_invoices(page=1)
        response_time_ms = (time.time() - start_time) * 1000.0
        
        if result and 'invoices' in result:
            return True, response_time_ms, None
        else:
            return False, response_time_ms, "Unexpected response format"
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000.0 if 'start_time' in locals() else 0.0
        return False, response_time_ms, str(e)


def check_facebook_health() -> tuple[bool, float, str | None]:
    """Check Facebook MCP server health."""
    try:
        from mcp_servers.facebook_mcp import get_page_posts
        
        start_time = time.time()
        # Try a simple read-only operation
        result = get_page_posts(limit=1)
        response_time_ms = (time.time() - start_time) * 1000.0
        
        if result and 'status' in result:
            return True, response_time_ms, None
        else:
            return False, response_time_ms, "Unexpected response format"
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000.0 if 'start_time' in locals() else 0.0
        return False, response_time_ms, str(e)


def check_instagram_health() -> tuple[bool, float, str | None]:
    """Check Instagram MCP server health."""
    try:
        from mcp_servers.instagram_mcp import get_media
        
        start_time = time.time()
        # Try a simple read-only operation
        result = get_media(limit=1)
        response_time_ms = (time.time() - start_time) * 1000.0
        
        if result and 'status' in result:
            return True, response_time_ms, None
        else:
            return False, response_time_ms, "Unexpected response format"
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000.0 if 'start_time' in locals() else 0.0
        return False, response_time_ms, str(e)


def check_twitter_health() -> tuple[bool, float, str | None]:
    """Check Twitter MCP server health."""
    try:
        from mcp_servers.twitter_mcp import get_user_tweets
        
        start_time = time.time()
        # Try a simple read-only operation
        result = get_user_tweets(max_results=1)
        response_time_ms = (time.time() - start_time) * 1000.0
        
        if result and 'status' in result:
            return True, response_time_ms, None
        else:
            return False, response_time_ms, "Unexpected response format"
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000.0 if 'start_time' in locals() else 0.0
        return False, response_time_ms, str(e)


def check_email_health() -> tuple[bool, float, str | None]:
    """Check Email MCP server health."""
    try:
        from mcp_servers.email_mcp import health_check
        
        start_time = time.time()
        result = health_check()
        response_time_ms = (time.time() - start_time) * 1000.0
        
        if result and result.get('status') == 'available':
            return True, response_time_ms, None
        else:
            return False, response_time_ms, result.get('error', 'Unknown error')
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000.0 if 'start_time' in locals() else 0.0
        return False, response_time_ms, str(e)


def check_linkedin_health() -> tuple[bool, float, str | None]:
    """Check LinkedIn MCP server health."""
    try:
        from mcp_servers.linkedin_mcp import health_check
        
        start_time = time.time()
        result = health_check()
        response_time_ms = (time.time() - start_time) * 1000.0
        
        if result and result.get('status') == 'available':
            return True, response_time_ms, None
        else:
            return False, response_time_ms, result.get('error', 'Unknown error')
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000.0 if 'start_time' in locals() else 0.0
        return False, response_time_ms, str(e)


def main():
    """Main health check daemon loop."""
    logger.info("Starting MCP Health Monitoring Daemon...")
    
    config = Config()
    health_checker = get_default_health_checker(config.vault_path)
    
    # MCP servers to monitor
    servers = {
        'xero-mcp': check_xero_health,
        'facebook-mcp': check_facebook_health,
        'instagram-mcp': check_instagram_health,
        'twitter-mcp': check_twitter_health,
        'email-mcp': check_email_health,
        'linkedin-mcp': check_linkedin_health,
    }
    
    check_interval = 300  # 5 minutes
    
    logger.info(f"Monitoring {len(servers)} MCP servers every {check_interval} seconds")
    
    try:
        while True:
            for server_name, health_func in servers.items():
                try:
                    # Check if server should be checked (respects interval)
                    if health_checker.should_check_server(server_name):
                        logger.info(f"Checking health of {server_name}...")
                        status = health_checker.check_server_health(
                            server_name=server_name,
                            health_check_func=health_func
                        )
                        logger.info(
                            f"{server_name}: {status.status} "
                            f"(success_rate: {status.calculate_success_rate():.1f}%, "
                            f"avg_response: {status.average_response_time_ms:.1f}ms)"
                        )
                    else:
                        logger.debug(f"Skipping {server_name} - checked recently")
                except Exception as e:
                    logger.error(f"Error checking {server_name}: {e}", exc_info=True)
            
            # Sleep until next check cycle
            logger.debug(f"Sleeping for {check_interval} seconds...")
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error in health check daemon: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

