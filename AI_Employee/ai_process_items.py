"""
AI Processor Daemon (Gold Tier)

Autonomous processor that monitors /Needs_Action/ and /Approved/ folders,
invokes Agent Skills programmatically, and processes action items automatically.
"""

import json
import logging
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from queue import PriorityQueue
from typing import Optional

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from models.action_item import ActionItem, parse_action_file
from models.cross_domain_workflow import CrossDomainWorkflow, WorkflowStep
from utils.classifier import Classifier, default_classifier
from utils.config import Config
from utils.dashboard import DashboardUpdater
from utils.health_checker import get_default_health_checker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ActionItemHandler(FileSystemEventHandler):
    """File system event handler for action items in /Needs_Action/."""
    
    def __init__(self, processor: 'AIProcessor'):
        self.processor = processor
        self.processed_files = set()
    
    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix != '.md':
            return
        
        # Avoid processing the same file multiple times
        if str(file_path) in self.processed_files:
            return
        
        self.processed_files.add(str(file_path))
        logger.info(f"New action item detected: {file_path.name}")
        
        # Add to processing queue
        self.processor.queue_action_item(file_path)


class ApprovedActionHandler(FileSystemEventHandler):
    """File system event handler for approved actions in /Approved/."""
    
    def __init__(self, processor: 'AIProcessor'):
        self.processor = processor
        self.processed_files = set()
    
    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if file_path.suffix != '.md':
            return
        
        # Avoid processing the same file multiple times
        if str(file_path) in self.processed_files:
            return
        
        self.processed_files.add(str(file_path))
        logger.info(f"New approved action detected: {file_path.name}")
        
        # Execute approved action
        self.processor.execute_approved_action(file_path)


class AIProcessor:
    """
    Autonomous AI Processor daemon.
    
    Monitors /Needs_Action/ and /Approved/ folders, invokes Agent Skills,
    and processes action items automatically.
    """
    
    # Priority mapping for queue ordering
    PRIORITY_ORDER = {
        'urgent': 0,
        'high': 1,
        'normal': 2,
        'low': 3,
        'unknown': 4
    }
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize AI Processor."""
        self.config = config or Config()
        self.classifier = default_classifier
        self.dashboard_updater = DashboardUpdater(self.config)
        self.health_checker = get_default_health_checker(self.config.vault_path)
        
        # Processing queue (priority queue)
        self.action_queue = PriorityQueue()
        self.processing_interval = getattr(self.config, 'processing_interval', 30)
        
        # Statistics
        self.stats = {
            'items_processed': 0,
            'items_failed': 0,
            'last_check_time': None,
            'start_time': datetime.now(),
            'last_error': None
        }
        
        # File watchers
        self.needs_action_observer: Optional[Observer] = None
        self.approved_observer: Optional[Observer] = None
        
        # Ensure vault structure
        self._ensure_vault_structure()
        
        # Error log file
        self.error_log_path = self.config.logs_path / 'processor_errors.json'
        self.error_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _ensure_vault_structure(self) -> None:
        """Ensure required vault folders exist."""
        folders = [
            self.config.needs_action_path,
            self.config.plans_path,
            self.config.done_path,
            self.config.pending_approval_path,
            self.config.approved_path,
            self.config.logs_path
        ]
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
    
    def queue_action_item(self, file_path: Path) -> None:
        """
        Add action item to processing queue with priority.
        
        Args:
            file_path: Path to action item file
        """
        try:
            # Parse action item to get priority
            action_item = parse_action_file(file_path)
            priority = action_item.priority or 'unknown'
            priority_value = self.PRIORITY_ORDER.get(priority, 4)
            
            # Add to queue: (priority, timestamp, file_path)
            self.action_queue.put((priority_value, time.time(), file_path))
            logger.info(f"Queued action item: {file_path.name} (priority: {priority})")
        except Exception as e:
            logger.error(f"Failed to queue action item {file_path}: {e}")
            self._log_error("queue_action_item", str(file_path), str(e))
    
    def process_action_item(self, file_path: Path) -> bool:
        """
        Process a single action item by invoking @process-action-items skill.
        
        Args:
            file_path: Path to action item file
        
        Returns:
            True if processing succeeded, False otherwise
        """
        try:
            logger.info(f"Processing action item: {file_path.name}")
            
            # Classify action item by domain
            action_item = parse_action_file(file_path)
            domain = self.classifier.classify(
                title=action_item.title,
                content=action_item.summary or action_item.content,
                source=action_item.source
            )
            logger.info(f"Classified action item as: {domain} domain")
            
            # Check if this action spans multiple domains (cross-domain workflow)
            cross_domain_workflow = self._detect_cross_domain_workflow(action_item, domain)
            
            if cross_domain_workflow:
                # Create cross-domain workflow
                workflow_path = self._create_cross_domain_workflow(cross_domain_workflow, action_item.id)
                logger.info(f"Created cross-domain workflow: {workflow_path.name}")
            
            # Invoke @process-action-items skill programmatically
            # Note: This is a placeholder - actual skill invocation depends on Claude Code integration
            # For now, we'll use a subprocess call or direct file manipulation
            success = self._invoke_process_action_items_skill(file_path, domain)
            
            if success:
                self.stats['items_processed'] += 1
                logger.info(f"Successfully processed: {file_path.name}")
                return True
            else:
                self.stats['items_failed'] += 1
                logger.error(f"Failed to process: {file_path.name}")
                return False
                
        except Exception as e:
            self.stats['items_failed'] += 1
            logger.error(f"Error processing action item {file_path}: {e}", exc_info=True)
            self._log_error("process_action_item", str(file_path), str(e))
            return False
    
    def _invoke_process_action_items_skill(
        self,
        file_path: Path,
        domain: str
    ) -> bool:
        """
        Invoke @process-action-items Agent Skill programmatically.
        
        This is a placeholder implementation. In a real Claude Code integration,
        this would invoke the skill through the Claude Code API or MCP protocol.
        
        Args:
            file_path: Path to action item file
            domain: Classified domain (personal, business, accounting, social_media)
        
        Returns:
            True if skill invocation succeeded
        """
        # For now, we'll create a simple plan file as a placeholder
        # In production, this would invoke Claude Code's skill system
        
        try:
            # Read action item content
            content = file_path.read_text(encoding='utf-8')
            
            # Create a basic plan file
            plan_id = file_path.stem
            plan_path = self.config.plans_path / f"{plan_id}-plan.md"
            
            plan_content = f"""---
type: action_plan
source: {file_path.name}
created: {datetime.now().isoformat()}
priority: {self._extract_priority(content)}
domain: {domain}
status: pending
---

# Action Plan: {file_path.stem}

## Source Information
- File: {file_path.name}
- Domain: {domain}
- Created: {datetime.now().isoformat()}

## Analysis
Action item detected and classified as {domain} domain.

## Recommended Actions
- [ ] Review action item details
- [ ] Determine required steps
- [ ] Create approval request if external action needed

## Notes
This plan was auto-generated by AI Processor. Manual review recommended.
"""
            
            plan_path.write_text(plan_content, encoding='utf-8')
            logger.info(f"Created plan: {plan_path.name}")
            
            # Update dashboard
            self.dashboard_updater.update_ai_processor_status(
                uptime_seconds=int((datetime.now() - self.stats['start_time']).total_seconds()),
                items_processed=self.stats['items_processed'],
                items_failed=self.stats['items_failed'],
                last_check_time=datetime.now()
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to invoke process-action-items skill: {e}", exc_info=True)
            return False
    
    def _detect_cross_domain_workflow(
        self,
        action_item: ActionItem,
        primary_domain: str
    ) -> Optional[CrossDomainWorkflow]:
        """
        Detect if action item spans multiple domains (cross-domain workflow).
        
        Args:
            action_item: The action item to analyze
            primary_domain: The primary domain classification
            
        Returns:
            CrossDomainWorkflow if cross-domain detected, None otherwise
        """
        # Check if action content suggests multiple domains
        content_lower = (action_item.title + " " + (action_item.content or "")).lower()
        
        # Cross-domain indicators:
        # - Personal expense email that should be logged in business accounting
        # - Business inquiry via personal LinkedIn that should be responded via business social media
        # - Personal task that requires business resource
        
        cross_domain_indicators = {
            ('personal', 'accounting'): ['expense', 'receipt', 'invoice', 'payment', 'bought', 'purchased'],
            ('personal', 'business'): ['client', 'customer', 'partnership', 'business', 'meeting'],
            ('business', 'social_media'): ['post', 'announce', 'promote', 'share', 'social'],
            ('accounting', 'business'): ['invoice', 'expense', 'transaction', 'financial']
        }
        
        # Check if primary domain + secondary domain indicators exist
        for (source_domain, target_domain), keywords in cross_domain_indicators.items():
            if primary_domain == source_domain:
                if any(keyword in content_lower for keyword in keywords):
                    # Create cross-domain workflow
                    steps = [
                        WorkflowStep(
                            step_number=1,
                            description=f"Process {primary_domain} action: {action_item.title}",
                            domain=primary_domain,
                            action_type="process_action",
                            status="pending"
                        ),
                        WorkflowStep(
                            step_number=2,
                            description=f"Create {target_domain} entry for: {action_item.title}",
                            domain=target_domain,
                            action_type=f"{target_domain}_action",
                            status="pending"
                        )
                    ]
                    
                    return CrossDomainWorkflow(
                        title=f"Cross-Domain: {action_item.title}",
                        description=f"Workflow spanning {primary_domain} and {target_domain} domains",
                        source_domain=primary_domain,
                        target_domain=target_domain,
                        steps=steps,
                        trigger_action_id=action_item.id,
                        status="pending"
                    )
        
        return None
    
    def _create_cross_domain_workflow(
        self,
        workflow: CrossDomainWorkflow,
        action_id: str
    ) -> Path:
        """
        Create cross-domain workflow file in /Business/Workflows/.
        
        Args:
            workflow: The cross-domain workflow to create
            action_id: The triggering action item ID
            
        Returns:
            Path to created workflow file
        """
        workflows_path = self.config.business_path / 'Workflows'
        workflows_path.mkdir(parents=True, exist_ok=True)
        
        workflow_file = workflows_path / f"{workflow.id}.json"
        workflow_file.write_text(workflow.model_dump_json(), encoding='utf-8')
        
        logger.info(f"Created cross-domain workflow: {workflow_file.name}")
        return workflow_file
    
    def _extract_priority(self, content: str) -> str:
        """Extract priority from content."""
        content_lower = content.lower()
        if any(word in content_lower for word in ['urgent', 'asap', 'critical', 'emergency']):
            return 'urgent'
        elif any(word in content_lower for word in ['high', 'important', 'priority']):
            return 'high'
        elif any(word in content_lower for word in ['low', 'whenever', 'optional']):
            return 'low'
        return 'normal'
    
    def execute_approved_action(self, file_path: Path) -> bool:
        """
        Execute an approved action by invoking @execute-approved-actions skill.
        
        Args:
            file_path: Path to approved action file
        
        Returns:
            True if execution succeeded, False otherwise
        """
        try:
            logger.info(f"Executing approved action: {file_path.name}")
            
            # Invoke @execute-approved-actions skill programmatically
            success = self._invoke_execute_approved_actions_skill(file_path)
            
            if success:
                logger.info(f"Successfully executed: {file_path.name}")
                return True
            else:
                logger.error(f"Failed to execute: {file_path.name}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing approved action {file_path}: {e}", exc_info=True)
            self._log_error("execute_approved_action", str(file_path), str(e))
            return False
    
    def _invoke_execute_approved_actions_skill(self, file_path: Path) -> bool:
        """
        Invoke @execute-approved-actions Agent Skill programmatically.
        
        This is a placeholder implementation. In a real Claude Code integration,
        this would invoke the skill through the Claude Code API or MCP protocol.
        
        Implements domain-specific MCP routing (T079) and domain isolation (T080).
        
        Args:
            file_path: Path to approved action file
        
        Returns:
            True if skill invocation succeeded
        """
        # For now, we'll just log that execution would happen
        # In production, this would invoke Claude Code's skill system to execute MCP actions
        
        try:
            # Read approved action content
            content = file_path.read_text(encoding='utf-8')
            
            # Extract domain from approval file (if present)
            domain_match = re.search(r'domain:\s*(\w+)', content, re.IGNORECASE)
            domain = domain_match.group(1) if domain_match else 'personal'
            
            # Extract MCP server from approval file
            mcp_match = re.search(r'mcp_server:\s*(\w+)', content, re.IGNORECASE)
            mcp_server = mcp_match.group(1) if mcp_match else None
            
            # Route to correct MCP server by domain (T079)
            mcp_server = self._route_mcp_server_by_domain(domain, mcp_server)
            
            logger.info(f"Would execute approved action: {file_path.name} (domain: {domain}, MCP: {mcp_server})")
            
            # Domain isolation: Wrap execution in try-except to prevent domain failures from affecting others (T080)
            try:
                # In production: Parse approval request, invoke MCP server, log to audit log, move to /Done/
                # For now, just move to /Done/ as placeholder
                done_path = self.config.done_path / file_path.name
                file_path.rename(done_path)
                logger.info(f"Moved to /Done/: {file_path.name}")
                
                return True
            except Exception as domain_error:
                # Domain isolation: Log error but don't crash entire processor
                logger.error(f"Domain-specific error for {domain} domain: {domain_error}")
                self._log_error("execute_approved_action", str(file_path), f"Domain {domain} error: {domain_error}")
                # Move to rejected folder for this domain
                rejected_path = self.config.rejected_path / file_path.name
                file_path.rename(rejected_path)
                return False
            
        except Exception as e:
            logger.error(f"Failed to invoke execute-approved-actions skill: {e}", exc_info=True)
            return False
    
    def _route_mcp_server_by_domain(self, domain: str, suggested_mcp: Optional[str] = None) -> str:
        """
        Route to correct MCP server by domain (T079).
        
        Implements graceful degradation (T087): Checks server health before routing.
        
        Args:
            domain: Domain classification (personal, business, accounting, social_media)
            suggested_mcp: Suggested MCP server from approval file
            
        Returns:
            MCP server name to use
        """
        # Domain-to-MCP server mapping
        domain_mcp_mapping = {
            'personal': {
                'email': 'email-mcp',
                'linkedin': 'linkedin-mcp',
                'whatsapp': 'playwright-mcp',
                'browser': 'playwright-mcp'
            },
            'business': {
                'email': 'email-mcp',
                'linkedin': 'linkedin-mcp',
                'social_media': 'facebook-mcp'  # Default to Facebook for business
            },
            'accounting': {
                'xero': 'xero-mcp',
                'expense': 'xero-mcp',
                'invoice': 'xero-mcp'
            },
            'social_media': {
                'facebook': 'facebook-mcp',
                'instagram': 'instagram-mcp',
                'twitter': 'twitter-mcp'
            }
        }
        
        # If suggested MCP is valid, check health first (T087)
        if suggested_mcp:
            if self._is_mcp_server_available(suggested_mcp):
                return suggested_mcp
            else:
                logger.warning(f"Suggested MCP server {suggested_mcp} is unavailable, trying alternatives")
        
        # Otherwise, route by domain with health check (T087)
        domain_servers = domain_mcp_mapping.get(domain, {})
        if domain_servers:
            # Try to find a healthy server for this domain
            for server_name in domain_servers.values():
                if self._is_mcp_server_available(server_name):
                    return server_name
            # If all servers are down, return first one anyway (will be handled by graceful degradation)
            return list(domain_servers.values())[0]
        
        # Default fallback
        return 'email-mcp'
    
    def _is_mcp_server_available(self, server_name: str) -> bool:
        """
        Check if MCP server is available (T087 - graceful degradation).
        
        Args:
            server_name: Name of MCP server
            
        Returns:
            True if server is healthy or degraded (still usable), False if down
        """
        status = self.health_checker.get_server_status(server_name)
        if status is None:
            # No status yet, assume available
            return True
        
        # Server is available if healthy or degraded (but not down)
        return status.status in ['healthy', 'degraded']
    
    def _log_error(self, operation: str, file_path: str, error: str) -> None:
        """Log error to processor_errors.json."""
        try:
            error_entry = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'file_path': file_path,
                'error': error
            }
            
            # Append to error log
            errors = []
            if self.error_log_path.exists():
                try:
                    errors = json.loads(self.error_log_path.read_text(encoding='utf-8'))
                except:
                    errors = []
            
            errors.append(error_entry)
            self.error_log_path.write_text(
                json.dumps(errors, indent=2),
                encoding='utf-8'
            )
            
            self.stats['last_error'] = error_entry
            
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
    
    def start(self) -> None:
        """Start the AI Processor daemon."""
        logger.info("Starting AI Processor daemon...")
        
        # Start file watchers
        self._start_file_watchers()
        
        # Process queue
        self._process_queue()
    
    def _start_file_watchers(self) -> None:
        """Start file system watchers for /Needs_Action/ and /Approved/."""
        # Watch /Needs_Action/ folder
        needs_action_handler = ActionItemHandler(self)
        self.needs_action_observer = Observer()
        self.needs_action_observer.schedule(
            needs_action_handler,
            str(self.config.needs_action_path),
            recursive=False
        )
        self.needs_action_observer.start()
        logger.info(f"Watching /Needs_Action/ folder: {self.config.needs_action_path}")
        
        # Watch /Approved/ folder
        approved_handler = ApprovedActionHandler(self)
        self.approved_observer = Observer()
        self.approved_observer.schedule(
            approved_handler,
            str(self.config.approved_path),
            recursive=False
        )
        self.approved_observer.start()
        logger.info(f"Watching /Approved/ folder: {self.config.approved_path}")
    
    def _process_queue(self) -> None:
        """Process action items from queue."""
        logger.info("Starting queue processing loop...")
        
        try:
            while True:
                # Process items from queue
                while not self.action_queue.empty():
                    priority, timestamp, file_path = self.action_queue.get()
                    
                    # Check if file still exists
                    if not file_path.exists():
                        logger.warning(f"Action item file no longer exists: {file_path}")
                        continue
                    
                    # Process the action item
                    self.process_action_item(file_path)
                    self.stats['last_check_time'] = datetime.now()
                
                # Sleep before next check
                time.sleep(self.processing_interval)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            self.stop()
        except Exception as e:
            logger.error(f"Fatal error in queue processing: {e}", exc_info=True)
            self._log_error("_process_queue", "queue_loop", str(e))
            raise
    
    def stop(self) -> None:
        """Stop the AI Processor daemon."""
        logger.info("Stopping AI Processor daemon...")
        
        if self.needs_action_observer:
            self.needs_action_observer.stop()
            self.needs_action_observer.join()
        
        if self.approved_observer:
            self.approved_observer.stop()
            self.approved_observer.join()
        
        logger.info("AI Processor daemon stopped")


def main():
    """Main entry point for AI Processor daemon."""
    config = Config()
    processor = AIProcessor(config)
    
    try:
        processor.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
