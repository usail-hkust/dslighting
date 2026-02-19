"""
Top-level CLI entry point for console scripts.

This module is referenced by pyproject/setuptools entry points:
    dslighting = dslighting_cli:main
"""

from dslighting.cli.__main__ import main


if __name__ == "__main__":
    import sys

    sys.exit(main())
