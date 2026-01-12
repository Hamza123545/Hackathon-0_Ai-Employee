"""
Create Accounting Folder Structure (Gold Tier)

Creates the /Accounting/ folder structure required for Gold Tier.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import Config


def create_accounting_folders() -> None:
    """Create Accounting folder structure."""
    config = Config()
    
    folders = [
        config.accounting_path / 'Transactions',
        config.accounting_path / 'Summaries',
        config.accounting_path / 'Audits'
    ]
    
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {folder}")
    
    print(f"\n✅ Accounting folder structure created at: {config.accounting_path}")


if __name__ == '__main__':
    create_accounting_folders()

