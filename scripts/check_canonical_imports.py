#!/usr/bin/env python3
"""
Canonical Import Boundary Checker

This script verifies that code under gmos/src/gmos/ does not import from 
legacy root directories (core, memory, ledger, runtime, adapters).

It should fail if anything under gmos/src/gmos/ imports:
- core (unless gmos.core)
- memory (unless gmos.memory)
- ledger (unless gmos.ledger)
- runtime (unless gmos.runtime)
- adapters (unless gmos.adapters)

Usage:
    python scripts/check_canonical_imports.py
    python scripts/check_canonical_imports.py --fix  # Show fixes without applying
"""

import os
import re
import sys
from pathlib import Path

# Legacy root directories that should NOT be imported from canonical code
LEGACY_ROOTS = {
    'core',
    'memory', 
    'ledger',
    'runtime',
    'adapters',
}

# Pattern to match: "from X import" or "import X"
# Excludes gmos.X to allow canonical imports
IMPORT_PATTERN = re.compile(
    r'^(?:from\s+(\S+)\s+import|import\s+(\S+))',
    re.MULTILINE
)


def find_legacy_imports(file_path: Path) -> list[tuple[int, str]]:
    """Find all legacy imports in a Python file."""
    violations = []
    
    try:
        content = file_path.read_text()
    except (UnicodeDecodeError, IOError):
        return violations
    
    for i, line in enumerate(content.splitlines(), 1):
        # Skip comments
        if line.strip().startswith('#'):
            continue
            
        match = IMPORT_PATTERN.match(line)
        if match:
            module = match.group(1) or match.group(2)
            
            # Check if it's a legacy root (not a gmos.* import)
            for legacy in LEGACY_ROOTS:
                # Match: "from memory import" or "import memory"
                # But NOT: "from gmos.memory import" or "import gmos.memory"
                if module == legacy or module.startswith(legacy + '.'):
                    violations.append((i, line.strip()))
                    
    return violations


def check_canonical_imports(root_dir: str = "gmos/src/gmos") -> int:
    """Check all Python files in the canonical package for legacy imports."""
    root = Path(root_dir)
    
    if not root.exists():
        print(f"ERROR: Directory {root_dir} does not exist")
        return 1
    
    all_violations = []
    
    for py_file in root.rglob("*.py"):
        # Skip __pycache__ and other non-source files
        if '__pycache__' in str(py_file):
            continue
            
        violations = find_legacy_imports(py_file)
        if violations:
            rel_path = py_file.relative_to(root)
            all_violations.append((str(rel_path), violations))
    
    if all_violations:
        print("=" * 60)
        print("CANONICAL IMPORT BOUNDARY VIOLATIONS FOUND")
        print("=" * 60)
        
        for file_path, violations in all_violations:
            print(f"\n{file_path}:")
            for line_num, line_content in violations:
                print(f"  Line {line_num}: {line_content}")
        
        print("\n" + "=" * 60)
        print(f"FAILED: Found {sum(len(v) for _, v in all_violations)} violations in {len(all_violations)} files")
        print("=" * 60)
        print("\nTo fix, replace legacy imports with canonical equivalents:")
        print("  'from memory.X import Y' -> 'from gmos.memory.X import Y'")
        print("  'from core.X import Y'   -> 'from gmos.kernel.X import Y'")
        print("  etc.")
        
        return 1
    else:
        print("=" * 60)
        print("SUCCESS: No legacy imports found in canonical package")
        print("=" * 60)
        return 0


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Check canonical import boundaries")
    parser.add_argument(
        "--root", 
        default="gmos/src/gmos",
        help="Root directory to check (default: gmos/src/gmos)"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Show what would be fixed (not implemented yet)"
    )
    
    args = parser.parse_args()
    
    if args.fix:
        print("Fix mode not yet implemented. Run without --fix to check.")
        return 1
        
    return check_canonical_imports(args.root)


if __name__ == "__main__":
    sys.exit(main())
