"""
Autonomous Agent (Gold Tier)
"The Ralph Wiggum Loop"

This script acts as the persistent "consciousness" of the AI Employee.
It implements the Watch -> Plan -> Execute -> Finish loop.
Now with Platinum Tier Zone Awareness (Cloud vs Local).

Modes:
- CLOUD: Watches /Needs_Action, Plans, and creates /Pending_Approval items. Drafts only.
- LOCAL: Watches /Approved, Executes final actions (Send, Pay), moves to /Done.
"""

import json
import logging
import os
import shutil
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Configuration
VAULT_PATH = Path(os.environ.get('VAULT_PATH', 'D:/Hackathon-0_Ai-Employee/AI_Employee'))
AGENT_MODE = os.environ.get('AGENT_MODE', 'local').lower() # 'cloud' or 'local'

NEEDS_ACTION = VAULT_PATH / 'Needs_Action'
PLANS = VAULT_PATH / 'Plans'
PENDING_APPROVAL = VAULT_PATH / 'Pending_Approval'
APPROVED = VAULT_PATH / 'Approved'
REJECTED = VAULT_PATH / 'Rejected'
DONE = VAULT_PATH / 'Done'
LOGS = VAULT_PATH / 'Logs'

# Setup Logging
def setup_logging():
    LOGS.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOGS / f"agent_{datetime.now().strftime('%Y-%m-%d')}.log")
        ],
        force=True
    )

logger = logging.getLogger(f"RalphWiggum-{AGENT_MODE.upper()}")

class AutonomousAgent:
    def __init__(self):
        self.running = True
        self.check_interval = 10  # Seconds
        self.mode = AGENT_MODE
        self.ensure_directories()
    
    def ensure_directories(self):
        for p in [NEEDS_ACTION, PLANS, PENDING_APPROVAL, APPROVED, REJECTED, DONE, LOGS]:
            p.mkdir(parents=True, exist_ok=True)

    def run(self):
        setup_logging()
        logger.info(f"Autonomous Agent Started in {self.mode.upper()} mode")
        
        if self.mode == 'cloud':
            logger.info(f"Watching {NEEDS_ACTION} -> Plans -> {PENDING_APPROVAL}")
        else:
            logger.info(f"Watching {APPROVED} -> Execute -> {DONE}")
        
        try:
            while self.running:
                self.process_loop()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Stopping agent...")

    def process_loop(self):
        """Core logic of the loop, split by zone."""
        
        if self.mode == 'cloud':
            # Cloud Strategy: Triage & Draft
            # 1. READ: Check for new work in Needs_Action
            files = list(NEEDS_ACTION.glob('*.md'))
            for file_path in files:
                logger.info(f"Cloud: Processing task {file_path.name}")
                try:
                    self.cloud_handle_task(file_path)
                except Exception as e:
                    logger.error(f"Failed to process {file_path.name}: {e}")
                    
        elif self.mode == 'local':
            # Local Strategy: Execute Approved Items
            # 1. READ: Check for approved items
            files = list(APPROVED.glob('*.md')) # Approvals might be .json or .md
            # Also check json
            files.extend(list(APPROVED.glob('*.json')))
            
            for file_path in files:
                logger.info(f"Local: Executing approved task {file_path.name}")
                try:
                    self.local_execute_task(file_path)
                except Exception as e:
                    logger.error(f"Failed to process {file_path.name}: {e}")

    # --- CLOUD LOGIC ---
    def cloud_handle_task(self, file_path: Path):
        content = file_path.read_text(encoding='utf-8')
        
        # 2. THINK/PLAN
        plan_name = f"PLAN_{file_path.name}"
        logger.info(f"Creating plan: {plan_name}")
        plan_content = self.generate_plan(file_path.name, content)
        (PLANS / plan_name).write_text(plan_content, encoding='utf-8')
        
        # 3. DRAFT (Create Approval Request)
        # Instead of executing, we move to Pending_Approval (or create a new approval file)
        # For simplicity in this demo, we'll simulate "Drafting" by creating an approval file.
        
        approval_filename = f"APPROVAL_{file_path.name}"
        approval_path = PENDING_APPROVAL / approval_filename
        
        approval_content = f"""---
type: approval_request
source_task: {file_path.name}
status: pending_approval
created: {datetime.now().isoformat()}
---

## Proposed Action
Execute task defined in {file_path.name}

## Plan
{plan_content}

## Action Required
Move this file to /Approved to execute.
"""
        approval_path.write_text(approval_content, encoding='utf-8')
        logger.info(f"Drafted approval request: {approval_filename}")
        
        # Move original task to "In Progress" or just keep it? 
        # For this logic, let's move the original task to a temporary 'Processing' state or just leave it?
        # Better: Implementation Plan said "Cloud owns...". 
        # Let's move the Needs_Action file to a 'Drafted' folder or straight to Done (as the "Drafting" task is done)
        # But we need to keep the context. 
        # Convention: Move Needs_Action item to Done because the "Drafting" is complete.
        # The "Execution" is a *new* task that starts when Approved.
        
        shutil.move(str(file_path), str(DONE / file_path.name))
        logger.info(f"Moved {file_path.name} to Done (Drafting Complete)")

    def generate_plan(self, filename: str, content: str) -> str:
        """Simulate LLM planning."""
        return f"""
        Objective: Process {filename}
        Key Steps:
        1. Analyze intent
        2. Draft response/action
        3. Request approval
        """

    # --- LOCAL LOGIC ---
    def local_execute_task(self, file_path: Path):
        """Execute the approved action."""
        logger.info(f"Executing {file_path.name}...")
        
        # Simulate Execution (e.g. sending the email, paying the bill)
        time.sleep(1) # Simulation
        
        # 4. FINISH
        logger.info(f"Execution complete. Moving {file_path.name} to Done")
        shutil.move(str(file_path), str(DONE / file_path.name))

if __name__ == "__main__":
    agent = AutonomousAgent()
    agent.run()
