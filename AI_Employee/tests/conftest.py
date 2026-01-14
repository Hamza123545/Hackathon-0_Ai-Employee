"""
Pytest configuration for Gold Tier AI Employee tests.

Fixes import paths to allow running tests from project root.
"""

import sys
from pathlib import Path

# Add AI_Employee directory to Python path for imports
ai_employee_dir = Path(__file__).parent.parent
if str(ai_employee_dir) not in sys.path:
    sys.path.insert(0, str(ai_employee_dir))

# Also add parent directory for accessing AI_Employee as a package
project_root = ai_employee_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
