#!/usr/bin/env python3
"""Quality gate script for Ultimate Kids Curiosity Club.

This script runs all quality checks: linting, formatting, type checking,
and tests. It's used in CI and can be run locally before committing.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return True if successful.
    
    Args:
        cmd: Command to run as list of strings
        description: Description of what the command does
        
    Returns:
        True if command succeeded, False otherwise
    """
    print(f"\n{'=' * 60}")
    print(f"🔍 {description}")
    print(f"{'=' * 60}")
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print(f"✅ {description} passed")
        return True
    else:
        print(f"❌ {description} failed")
        return False


def main() -> int:
    """Run all quality checks.
    
    Returns:
        0 if all checks pass, 1 if any check fails
    """
    project_root = Path(__file__).parent.parent
    
    print("=" * 60)
    print("🚀 Running Quality Gate Checks")
    print("=" * 60)
    
    checks = [
        (
            ["ruff", "check", "src/", "tests/"],
            "Linting with ruff",
        ),
        (
            ["ruff", "format", "--check", "src/", "tests/"],
            "Format checking with ruff",
        ),
        (
            ["mypy", "-p", "models", "-p", "utils", "-p", "modules"],
            "Type checking with mypy",
        ),
        (
            ["pytest", "-m", "not real_api"],
            "Running tests",
        ),
    ]
    
    results = []
    for cmd, description in checks:
        success = run_command(cmd, description)
        results.append((description, success))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 QUALITY GATE SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {description}")
        if not success:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 All quality checks passed!")
        return 0
    else:
        print("⚠️  Some quality checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
