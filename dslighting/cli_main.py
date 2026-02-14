"""
DSLighting CLI entry point.

This module provides backward compatibility. Use 'python -m dslighting.cli' or
'datacompy' command instead.
"""

from dslighting.cli.__main__ import main

if __name__ == '__main__':
    import sys
    sys.exit(main())
