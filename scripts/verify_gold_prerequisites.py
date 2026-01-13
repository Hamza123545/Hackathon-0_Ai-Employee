#!/usr/bin/env python3
"""
Gold Tier Prerequisites Verification Script

Verifies that all Gold tier prerequisites are met before starting implementation.
Checks:
- Python version (3.10+)
- Required directories exist
- Bronze/Silver tier infrastructure in place
- Node.js/npm installed (for PM2)
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import List, Tuple

# Set stdout encoding to UTF-8 for Windows compatibility
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class PrerequisiteChecker:
    """Checks Gold tier prerequisites"""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed: List[str] = []

    def check_python_version(self) -> bool:
        """Check Python version is 3.10+"""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 10:
            self.passed.append(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            self.errors.append(f"✗ Python version {version.major}.{version.minor} < 3.10 (required)")
            return False

    def check_directory_structure(self) -> bool:
        """Check Bronze/Silver tier directories exist"""
        required_dirs = [
            "AI_Employee/Needs_Action",
            "AI_Employee/Plans",
            "AI_Employee/Pending_Approval",
            "AI_Employee/Approved",
            "AI_Employee/Done",
            "AI_Employee/Logs",
        ]

        all_exist = True
        for dir_path in required_dirs:
            if Path(dir_path).exists():
                self.passed.append(f"✓ Directory exists: {dir_path}")
            else:
                self.warnings.append(f"⚠ Directory missing: {dir_path} (will be created)")
                all_exist = False

        return all_exist

    def check_bronze_silver_files(self) -> bool:
        """Check key Bronze/Silver tier files exist"""
        required_files = [
            "AI_Employee/Dashboard.md",
            "AI_Employee/Company_Handbook.md",
        ]

        all_exist = True
        for file_path in required_files:
            if Path(file_path).exists():
                self.passed.append(f"✓ File exists: {file_path}")
            else:
                self.warnings.append(f"⚠ File missing: {file_path} (Bronze/Silver tier file)")
                all_exist = False

        return all_exist

    def check_models_directory(self) -> bool:
        """Check models directory exists"""
        if Path("models").exists():
            self.passed.append("✓ models/ directory exists")
            return True
        else:
            self.warnings.append("⚠ models/ directory missing (will be created)")
            return False

    def check_nodejs_npm(self) -> bool:
        """Check Node.js and npm are installed (for PM2)"""
        node_found = False
        npm_found = False

        try:
            node_result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                shell=True
            )
            if node_result.returncode == 0:
                self.passed.append(f"✓ Node.js installed: {node_result.stdout.strip()}")
                node_found = True
            else:
                self.errors.append("✗ Node.js not installed (required for PM2)")
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            self.errors.append(f"✗ Node.js not found in PATH (required for PM2)")

        if node_found:
            try:
                npm_result = subprocess.run(
                    ["npm", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    shell=True
                )
                if npm_result.returncode == 0:
                    self.passed.append(f"✓ npm installed: {npm_result.stdout.strip()}")
                    npm_found = True
                else:
                    self.errors.append("✗ npm not installed (required for PM2)")
            except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                self.errors.append(f"✗ npm not found in PATH (required for PM2)")

        return node_found and npm_found

    def check_git_repository(self) -> bool:
        """Check if in a git repository"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.passed.append("✓ Git repository initialized")
                return True
            else:
                self.warnings.append("⚠ Not a git repository (recommended for version control)")
                return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.warnings.append("⚠ Git not found or timed out")
            return False

    def run_all_checks(self) -> bool:
        """Run all prerequisite checks"""
        print("=" * 70)
        print("Gold Tier Prerequisites Verification")
        print("=" * 70)
        print()

        checks = [
            ("Python Version", self.check_python_version),
            ("Directory Structure", self.check_directory_structure),
            ("Bronze/Silver Files", self.check_bronze_silver_files),
            ("Models Directory", self.check_models_directory),
            ("Node.js/npm", self.check_nodejs_npm),
            ("Git Repository", self.check_git_repository),
        ]

        for name, check_func in checks:
            print(f"Checking {name}...")
            check_func()
            print()

        return self.display_results()

    def display_results(self) -> bool:
        """Display check results and return overall status"""
        print("=" * 70)
        print("Results Summary")
        print("=" * 70)
        print()

        if self.passed:
            print(f"✓ PASSED ({len(self.passed)} checks):")
            for msg in self.passed:
                print(f"  {msg}")
            print()

        if self.warnings:
            print(f"⚠ WARNINGS ({len(self.warnings)} items):")
            for msg in self.warnings:
                print(f"  {msg}")
            print()

        if self.errors:
            print(f"✗ ERRORS ({len(self.errors)} critical issues):")
            for msg in self.errors:
                print(f"  {msg}")
            print()

        if self.errors:
            print("Status: ✗ FAILED - Critical prerequisites missing")
            print()
            print("Action Required:")
            print("  1. Install missing prerequisites")
            print("  2. Run this script again to verify")
            return False
        elif self.warnings:
            print("Status: ⚠ PASSED WITH WARNINGS - Proceed with caution")
            print()
            print("Recommendations:")
            print("  - Address warnings for best results")
            print("  - Missing directories will be created during setup")
            return True
        else:
            print("Status: ✓ ALL CHECKS PASSED - Ready for Gold Tier implementation")
            return True


def main():
    """Main entry point"""
    checker = PrerequisiteChecker()
    success = checker.run_all_checks()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
