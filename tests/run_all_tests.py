"""
Test Runner - Full System Test Suite

Runs all test modules:
- test_full_system.py: Original integration tests
- test_core_modules.py: Core state, potential, affective modules
- test_memory_ledger_runtime.py: Memory, ledger, runtime modules
- test_adapters.py: Adapter modules
- test_gmos_modules.py: GMOS implementation tests
"""

import subprocess
import sys
import os

def run_tests(test_path=None):
    """Run pytest on specified test path or all tests."""
    cmd = [sys.executable, "-m", "pytest"]
    
    if test_path:
        cmd.append(test_path)
    else:
        cmd.append("tests/")
    
    # Add verbose output
    cmd.extend(["-v", "--tb=short"])
    
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd, cwd="/home/user/gmi")
    return result.returncode


def main():
    """Run all test suites."""
    test_suites = [
        ("Full System Integration", "tests/test_full_system.py"),
        ("Core Modules", "tests/test_core_modules.py"),
        ("Memory, Ledger, Runtime", "tests/test_memory_ledger_runtime.py"),
        ("Adapters", "tests/test_adapters.py"),
        ("GMOS Modules", "tests/test_gmos_modules.py"),
    ]
    
    print("=" * 60)
    print("GMI FULL SYSTEM TEST SUITE")
    print("=" * 60)
    
    # Run individual test suites
    results = {}
    for name, path in test_suites:
        print(f"\n{'='*60}")
        print(f"Running: {name}")
        print(f"{'='*60}")
        
        returncode = run_tests(path)
        results[name] = returncode == 0
        
        if returncode != 0:
            print(f"✗ {name} FAILED")
        else:
            print(f"✓ {name} PASSED")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
