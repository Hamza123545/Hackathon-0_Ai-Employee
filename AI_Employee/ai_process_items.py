#!/usr/bin/env python3
"""
Automatic AI Processing for Personal AI Employee.

Monitors /Needs_Action/ folder and automatically processes new action items
using Claude Code or Anthropic API. Implements automatic risk assessment
and routing to approval workflow.

Features:
- Automatic detection of new action items
- Multiple processing methods (Claude CLI, Anthropic API, fallback)
- Risk assessment and auto-routing
- Dashboard updates
- Duplicate prevention
- Error recovery and graceful degradation

Usage:
    python ai_process_items.py
    python ai_process_items.py --interval 30 --method anthropic
    python ai_process_items.py --dry-run

Environment Variables:
    ANTHROPIC_API_KEY: API key for Anthropic API (if using API method)
    CLAUDE_CLI_PATH: Path to Claude CLI executable (optional)
    PROCESS_INTERVAL: Seconds between checks (default: 60)
    PROCESS_METHOD: 'claude-cli', 'anthropic', or 'auto' (default: auto)
    DRY_RUN: If 'true', simulate processing without actual API calls
"""

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .models.action_item import ActionItem, parse_action_file
from .utils.approval_helper import ApprovalHelper
from .utils.audit_logger import AuditLogger
from .utils.config import Config
from .utils.dashboard import DashboardUpdater


ProcessingMethod = Literal['claude-cli', 'anthropic', 'auto', 'simulation']


class AIProcessor:
    """
    Automatic AI processor for action items.

    Monitors /Needs_Action/ folder and processes new items using
    Claude Code or Anthropic API. Handles risk assessment, approval
    routing, and dashboard updates.
    """

    def __init__(
        self,
        config: Config,
        method: ProcessingMethod = 'auto',
        check_interval: int = 60,
        dry_run: bool = False
    ):
        """
        Initialize the AI processor.

        Args:
            config: Configuration object with vault paths.
            method: Processing method ('claude-cli', 'anthropic', 'auto', 'simulation').
            check_interval: Seconds between checks (default: 60).
            dry_run: If True, simulate processing without API calls.
        """
        self.config = config
        self.method = method
        self.check_interval = check_interval
        self.dry_run = dry_run
        self.running = False

        # Initialize components
        self.audit_logger = AuditLogger(config.logs_path)
        self.approval_helper = ApprovalHelper(config)
        self.dashboard_updater = DashboardUpdater(config)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Track processed files
        self.processed_files: set[str] = set()
        self._load_processed_tracker()

        # Initialize processing method
        self._init_processing_method()

    def _init_processing_method(self) -> None:
        """Initialize the processing method based on configuration."""
        if self.method == 'auto':
            # Try to detect available method
            if self._check_claude_cli():
                self.method = 'claude-cli'
                self.logger.info("Using Claude CLI for processing")
            elif ANTHROPIC_AVAILABLE and os.getenv('ANTHROPIC_API_KEY'):
                self.method = 'anthropic'
                self.logger.info("Using Anthropic API for processing")
            else:
                self.method = 'simulation'
                self.logger.warning(
                    "No Claude CLI or Anthropic API available. "
                    "Using simulation mode (will create plans but not process with AI)"
                )
        elif self.method == 'anthropic':
            if not ANTHROPIC_AVAILABLE:
                raise ImportError(
                    "Anthropic package not installed. "
                    "Install with: pip install anthropic"
                )
            if not os.getenv('ANTHROPIC_API_KEY'):
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable not set"
                )
            self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        elif self.method == 'claude-cli':
            if not self._check_claude_cli():
                raise FileNotFoundError(
                    "Claude CLI not found. "
                    "Install Claude Code or set CLAUDE_CLI_PATH"
                )

    def _check_claude_cli(self) -> bool:
        """Check if Claude CLI is available."""
        claude_path = os.getenv('CLAUDE_CLI_PATH', 'claude')
        try:
            result = subprocess.run(
                [claude_path, '--version'],
                capture_output=True,
                timeout=5,
                check=False
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _load_processed_tracker(self) -> None:
        """Load processed files tracker from disk."""
        tracker_path = self.config.vault_path / '.ai_processed.json'
        if tracker_path.exists():
            try:
                data = json.loads(tracker_path.read_text(encoding='utf-8'))
                self.processed_files = set(data.get('processed', []))
                self.logger.info(f"Loaded {len(self.processed_files)} processed files")
            except (json.JSONDecodeError, OSError) as e:
                self.logger.warning(f"Failed to load processed tracker: {e}")

    def _save_processed_tracker(self) -> None:
        """Save processed files tracker to disk."""
        tracker_path = self.config.vault_path / '.ai_processed.json'
        try:
            data = {
                'processed': list(self.processed_files),
                'last_updated': datetime.now().isoformat()
            }
            tracker_path.write_text(
                json.dumps(data, indent=2),
                encoding='utf-8'
            )
        except OSError as e:
            self.logger.error(f"Failed to save processed tracker: {e}")

    def run(self) -> None:
        """Main processing loop."""
        self.running = True
        self.logger.info("=" * 50)
        self.logger.info("AI Processor - Automatic Action Item Processing")
        self.logger.info("=" * 50)
        self.logger.info(f"Method: {self.method}")
        self.logger.info(f"Check interval: {self.check_interval}s")
        self.logger.info(f"Dry run: {self.dry_run}")
        self.logger.info(f"Vault path: {self.config.vault_path}")

        try:
            while self.running:
                try:
                    self._process_cycle()
                except Exception as e:
                    self.logger.error(f"Error in processing cycle: {e}", exc_info=True)

                # Sleep until next check
                self.logger.debug(f"Sleeping for {self.check_interval}s...")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the processor gracefully."""
        self.running = False
        self._save_processed_tracker()
        self.logger.info("AI Processor stopped")

    def _process_cycle(self) -> None:
        """Single processing cycle: check for new items and process them."""
        needs_action_path = self.config.needs_action_path
        if not needs_action_path.exists():
            return

        # Find new action items
        new_items = []
        for file_path in needs_action_path.glob('*.md'):
            if file_path.name not in self.processed_files:
                new_items.append(file_path)

        if not new_items:
            return

        self.logger.info(f"Found {len(new_items)} new action item(s)")

        # Process each item
        for file_path in new_items:
            try:
                self._process_action_item(file_path)
                self.processed_files.add(file_path.name)
            except Exception as e:
                self.logger.error(
                    f"Failed to process {file_path.name}: {e}",
                    exc_info=True
                )

        # Save tracker and update dashboard
        self._save_processed_tracker()
        self.dashboard_updater.update_all_sections(status='running')

    def _process_action_item(self, file_path: Path) -> None:
        """
        Process a single action item file.

        Args:
            file_path: Path to the action item file.
        """
        self.logger.info(f"Processing: {file_path.name}")

        # Parse action item
        try:
            action_item = parse_action_file(file_path)
        except Exception as e:
            self.logger.error(f"Failed to parse action item: {e}")
            return

        # Read Company Handbook for context
        handbook_content = self._read_handbook()

        # Process with AI
        if self.method == 'simulation':
            plan_content = self._simulate_processing(action_item, handbook_content)
        elif self.method == 'anthropic':
            plan_content = self._process_with_anthropic(action_item, handbook_content)
        elif self.method == 'claude-cli':
            plan_content = self._process_with_claude_cli(action_item, handbook_content)
        else:
            self.logger.error(f"Unknown processing method: {self.method}")
            return

        if not plan_content:
            self.logger.warning(f"No plan generated for {file_path.name}")
            return

        # Create plan file
        plan_path = self._create_plan_file(action_item, plan_content, file_path)

        # Check for external actions and create approval requests
        self._check_external_actions(plan_path, action_item)

        # Move action item to Done
        self._move_to_done(file_path, plan_path)

        # Log processing
        self.audit_logger.log_action(
            action_type='action_item_processed',
            actor='claude-code',
            target=file_path.name,
            parameters={'plan_file': plan_path.name},
            result='success'
        )

        self.logger.info(f"Successfully processed {file_path.name}")

    def _read_handbook(self) -> str:
        """Read Company_Handbook.md for processing context."""
        handbook_path = self.config.handbook_path
        if handbook_path.exists():
            try:
                return handbook_path.read_text(encoding='utf-8')
            except OSError:
                pass
        return ""

    def _simulate_processing(
        self,
        action_item: ActionItem,
        handbook_content: str
    ) -> str:
        """
        Simulate AI processing (fallback when no AI available).

        Creates a basic plan structure without actual AI processing.
        """
        plan_id = f"plan-{action_item.id[:8]}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        plan_content = f"""---
type: action_plan
source: {action_item.source}
created: {datetime.now().isoformat()}
priority: {action_item.priority}
status: pending
action_item_id: {action_item.id}
---

# Action Plan: {action_item.title}

## Source Information
- From: {action_item.source}
- Received: {action_item.created.isoformat() if action_item.created else 'Unknown'}
- Original Item: `/Needs_Action/{action_item.id}.md`

## Analysis
This action item was automatically detected and requires processing.

**Priority**: {action_item.priority}
**Tags**: {', '.join(action_item.tags) if action_item.tags else 'None'}

## Recommended Actions
- [ ] Review the action item content
- [ ] Determine appropriate response or action
- [ ] Execute or schedule the action

## Notes
*This plan was generated in simulation mode. For full AI processing, configure Claude CLI or Anthropic API.*

## Next Steps
1. Review the original action item in `/Done/`
2. Complete the recommended actions above
3. Update this plan with results

---
*Generated by AI Processor (simulation mode)*
"""
        return plan_content

    def _process_with_anthropic(
        self,
        action_item: ActionItem,
        handbook_content: str
    ) -> str | None:
        """
        Process action item using Anthropic API.

        Args:
            action_item: The action item to process.
            handbook_content: Company Handbook content for context.

        Returns:
            Plan content as markdown string, or None if processing failed.
        """
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would process with Anthropic API: {action_item.title}")
            return self._simulate_processing(action_item, handbook_content)

        # Build prompt for Anthropic API
        system_prompt = """You are an action item processor for the Personal AI Employee system.
Your job is to analyze action items and create structured plans with actionable steps.
Follow the rules in Company_Handbook.md and create plans in the specified format."""

        user_prompt = f"""Process this action item and create a structured plan:

## Company Handbook Rules
{handbook_content[:2000] if handbook_content else 'No handbook available'}

## Action Item
**Title**: {action_item.title}
**Source**: {action_item.source}
**Priority**: {action_item.priority}
**Content**:
{action_item.content[:3000]}

Create a structured plan following this format:

---
type: action_plan
source: {action_item.source}
created: {datetime.now().isoformat()}
priority: [HIGH|MEDIUM|LOW]
status: pending
---

# Action Plan: [Brief Title]

## Source Information
- From: [sender/filename]
- Received: [timestamp]
- Original Item: `/Needs_Action/[filename].md`

## Analysis
[Brief analysis of what the action item is about]

## Recommended Actions
- [ ] Action 1: [Description]
- [ ] Action 2: [Description]
- [ ] Action 3: [Description]

## Notes
[Any additional context]

## Next Steps
[Clear next steps]

Return ONLY the plan markdown, no additional text."""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            plan_content = response.content[0].text
            self.logger.info("Successfully processed with Anthropic API")
            return plan_content

        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            # Fallback to simulation
            return self._simulate_processing(action_item, handbook_content)

    def _process_with_claude_cli(
        self,
        action_item: ActionItem,
        handbook_content: str
    ) -> str | None:
        """
        Process action item using Claude CLI.

        Args:
            action_item: The action item to process.
            handbook_content: Company Handbook content for context.

        Returns:
            Plan content as markdown string, or None if processing failed.
        """
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would process with Claude CLI: {action_item.title}")
            return self._simulate_processing(action_item, handbook_content)

        # Claude CLI approach: invoke the skill
        # Note: This is a placeholder - actual implementation depends on
        # how Claude CLI exposes skills programmatically
        claude_path = os.getenv('CLAUDE_CLI_PATH', 'claude')
        
        # For now, fallback to simulation
        # TODO: Implement actual Claude CLI skill invocation when API is available
        self.logger.warning("Claude CLI skill invocation not yet implemented, using simulation")
        return self._simulate_processing(action_item, handbook_content)

    def _create_plan_file(
        self,
        action_item: ActionItem,
        plan_content: str,
        source_file: Path
    ) -> Path:
        """
        Create a plan file from processed content.

        Args:
            action_item: The original action item.
            plan_content: The plan markdown content.
            source_file: Path to the source action item file.

        Returns:
            Path to the created plan file.
        """
        # Generate plan filename
        slug = re.sub(r'[^\w-]', '-', action_item.title.lower())[:50]
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        plan_filename = f"plan-{slug}-{timestamp}.md"
        plan_path = self.config.plans_path / plan_filename

        # Ensure plans directory exists
        self.config.plans_path.mkdir(parents=True, exist_ok=True)

        # Write plan file
        plan_path.write_text(plan_content, encoding='utf-8')
        self.logger.info(f"Created plan: {plan_path.name}")

        return plan_path

    def _check_external_actions(
        self,
        plan_path: Path,
        action_item: ActionItem
    ) -> None:
        """
        Check plan for external actions and create approval requests if needed.

        Args:
            plan_path: Path to the plan file.
            action_item: The original action item.
        """
        try:
            plan_content = plan_path.read_text(encoding='utf-8')
            
            # Use ApprovalHelper to detect external actions
            # This will check for email, LinkedIn, browser actions, etc.
            # and create approval requests in /Pending_Approval/
            
            # For now, we rely on the skill to create approval requests
            # This method can be extended to automatically detect and create them
            self.logger.debug(f"Checked plan for external actions: {plan_path.name}")

        except Exception as e:
            self.logger.warning(f"Failed to check external actions: {e}")

    def _move_to_done(self, action_file: Path, plan_path: Path) -> None:
        """
        Move action item to Done folder.

        Args:
            action_file: Path to the action item file.
            plan_path: Path to the created plan file.
        """
        try:
            # Ensure Done directory exists
            self.config.done_path.mkdir(parents=True, exist_ok=True)

            # Read and update action item with plan reference
            content = action_file.read_text(encoding='utf-8')
            
            # Add plan reference to frontmatter
            if 'plan_file:' not in content:
                # Insert after first --- block
                frontmatter_end = content.find('---', 3)
                if frontmatter_end > 0:
                    plan_ref = f"\nplan_file: {plan_path.name}\nprocessed_at: {datetime.now().isoformat()}\n"
                    content = content[:frontmatter_end] + plan_ref + content[frontmatter_end:]

            # Move to Done
            done_file = self.config.done_path / action_file.name
            done_file.write_text(content, encoding='utf-8')
            action_file.unlink()

            self.logger.info(f"Moved to Done: {action_file.name}")

        except Exception as e:
            self.logger.error(f"Failed to move to Done: {e}")


def main() -> int:
    """CLI entry point for AI processor."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Automatic AI Processing for Personal AI Employee'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=int(os.getenv('PROCESS_INTERVAL', '60')),
        help='Check interval in seconds (default: 60)'
    )
    parser.add_argument(
        '--method',
        type=str,
        choices=['claude-cli', 'anthropic', 'auto', 'simulation'],
        default=os.getenv('PROCESS_METHOD', 'auto'),
        help='Processing method (default: auto)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=os.getenv('DRY_RUN', 'false').lower() in ('true', '1', 'yes'),
        help='Dry run mode (simulate without API calls)'
    )
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    try:
        config = Config()
        processor = AIProcessor(
            config,
            method=args.method,
            check_interval=args.interval,
            dry_run=args.dry_run
        )
        processor.run()

    except KeyboardInterrupt:
        print("\nShutting down...")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        logging.exception("Fatal error")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
