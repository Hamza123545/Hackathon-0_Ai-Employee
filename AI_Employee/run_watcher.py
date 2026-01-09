#!/usr/bin/env python3
"""
Runner script for the Personal AI Employee watcher.

This script adds the parent directory to the Python path so the
AI_Employee module can be imported correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path for module resolution
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Now import and run the main function
from AI_Employee.main import main

if __name__ == '__main__':
    sys.exit(main())
