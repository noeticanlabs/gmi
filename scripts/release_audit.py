#!/usr/bin/env python3
"""
Release Audit Script

Pre-release audit checks for GM-OS package quality.
Run this before releasing to ensure code quality.

Usage:
    python scripts/release_audit.py
"""

import os
import sys
import subprocess
from pathlib import Path


def check_imports():
    """Check that all canonical imports work."""
    print("Checking imports...")
    try:
        import gmos
        import gmos.kernel
        import gmos.agents.gmi
        import gmos.memory
        import gmos.action
        print("  ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def check_no_pycache():
    """Check for stale pycache files."""
    print("Checking for __pycache__...")
    pycache_count = 0
    for root, dirs, files in os.walk('gmos'):
        if '__pycache__' in root:
            pycache_count += 1
    
    if pycache_count > 0:
        print(f"  ✗ Found {pycache_count} __pycache__ directories")
        return False
    else:
        print("  ✓ No __pycache__ found")
        return True


def check_no_todo_in_canonical():
    """Check for TODO in canonical paths."""
    print("Checking for TODO in canonical paths...")
    issues = []
    canonical_paths = [
        'gmos/src/gmos/kernel',
        'gmos/src/gmos/agents/gmi',
        'gmos/src/gmos/memory',
    ]
    
    for path in canonical_paths:
        for root, dirs, files in os.walk(path):
            for f in files:
                if f.endswith('.py'):
                    filepath = os.path.join(root, f)
                    with open(filepath, 'r') as fp:
                        for i, line in enumerate(fp):
                            if 'TODO' in line or 'FIXME' in line:
                                issues.append(f"{filepath}:{i+1}")
    
    if issues:
        print(f"  ✗ Found {len(issues)} TODO/FIXME in canonical paths")
        for issue in issues[:5]:
            print(f"    {issue}")
        return False
    else:
        print("  ✓ No TODO/FIXME in canonical paths")
        return True


def check_legacy_dirs():
    """Check that legacy directories have LEGACY.md."""
    print("Checking legacy directories...")
    legacy_dirs = ['core', 'memory', 'ledger', 'runtime', 'adapters', 'experiments']
    missing = []
    
    for d in legacy_dirs:
        if not os.path.exists(f"{d}/LEGACY.md"):
            missing.append(d)
    
    if missing:
        print(f"  ✗ Missing LEGACY.md in: {missing}")
        return False
    else:
        print("  ✓ All legacy directories have LEGACY.md")
        return True


def check_canonical_readme():
    """Check that CANONICAL.md exists."""
    print("Checking CANONICAL.md...")
    if os.path.exists('CANONICAL.md'):
        print("  ✓ CANONICAL.md exists")
        return True
    else:
        print("  ✗ CANONICAL.md missing")
        return False


def main():
    """Run all audit checks."""
    print("=" * 50)
    print("GM-OS Release Audit")
    print("=" * 50)
    
    os.chdir(Path(__file__).parent.parent)
    
    checks = [
        check_imports,
        check_no_pycache,
        check_no_todo_in_canonical,
        check_legacy_dirs,
        check_canonical_readme,
    ]
    
    results = []
    for check in checks:
        results.append(check())
        print()
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} checks passed")
    
    if all(results):
        print("✓ Release audit PASSED")
        return 0
    else:
        print("✗ Release audit FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
