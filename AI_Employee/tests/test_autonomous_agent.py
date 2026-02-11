import sys
import os
# Add parent dir to path to find autonomous_agent.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import shutil
import tempfile
from pathlib import Path
from autonomous_agent import AutonomousAgent

class TestAutonomousAgent(unittest.TestCase):
    def setUp(self):
        # Create temp vault
        self.test_dir = tempfile.mkdtemp()
        self.agent = AutonomousAgent()
        
        # Override paths
        self.agent.NEEDS_ACTION = Path(self.test_dir) / 'Needs_Action'
        self.agent.PLANS = Path(self.test_dir) / 'Plans'
        self.agent.DONE = Path(self.test_dir) / 'Done'
        self.agent.LOGS = Path(self.test_dir) / 'Logs'
        
        # global overrides (since script uses globals)
        # Note: Ideally refactor script to use instance vars for paths
        import autonomous_agent
        autonomous_agent.NEEDS_ACTION = self.agent.NEEDS_ACTION
        autonomous_agent.PLANS = self.agent.PLANS
        autonomous_agent.DONE = self.agent.DONE
        autonomous_agent.LOGS = self.agent.LOGS
        
        self.agent.ensure_directories()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_handle_task(self):
        # Create a task file
        task_file = self.agent.NEEDS_ACTION / "task_invoice.txt"
        task_file.write_text("Please create an invoice for Client A", encoding='utf-8')
        
        # Process it
        self.agent.handle_task(task_file)
        
        # Check if moved to Done
        self.assertTrue((self.agent.DONE / "task_invoice.txt").exists())
        self.assertFalse(task_file.exists())
        
        # Check if Plan created (and then moved to Done)
        plan_file = self.agent.DONE / "PLAN_task_invoice.txt"
        self.assertTrue(plan_file.exists())
        self.assertIn("Client A", task_file.read_text())

if __name__ == '__main__':
    unittest.main()
