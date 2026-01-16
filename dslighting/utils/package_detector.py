"""
Package Detector - Detects available Python packages in the current environment.

This module provides utilities to scan the current Python environment and
detect installed packages, making this information available to the agent
for better code generation.
"""

import importlib.metadata as metadata
import logging
from typing import Dict, List, Optional
from pathlib import Path
import yaml
import json

logger = logging.getLogger(__name__)


class PackageDetector:
    """
    Detects and manages information about available Python packages.

    This class scans the current Python environment to detect installed
    packages and can save/load this information from config files.
    """

    # Common data science packages to highlight
    DATA_SCIENCE_PACKAGES = {
        'pandas', 'numpy', 'scipy', 'scikit-learn', 'sklearn',
        'matplotlib', 'seaborn', 'plotly', 'bokeh',
        'xgboost', 'lightgbm', 'catboost', 'torch', 'tensorflow',
        'keras', 'fastai', 'transformers', 'datasets',
        'statsmodels', 'nltk', 'spacy', 'gensim',
        'cv2', 'PIL', 'pillow', 'imageio',
        'requests', 'beautifulsoup4', 'bs4', 'scrapy',
        'sqlalchemy', 'pymongo', 'psycopg2',
        'polars', 'pyarrow', 'dask'
    }

    def __init__(self, include_stdlib: bool = False):
        """
        Initialize PackageDetector.

        Args:
            include_stdlib: Whether to include standard library packages
        """
        self.include_stdlib = include_stdlib
        self._packages_cache: Optional[Dict[str, str]] = None

    def detect_packages(self, force_refresh: bool = False) -> Dict[str, str]:
        """
        Detect all installed packages in the current environment.

        Args:
            force_refresh: Force re-detection even if cached

        Returns:
            Dictionary mapping package names to their versions
        """
        if self._packages_cache is not None and not force_refresh:
            return self._packages_cache

        packages = {}

        try:
            # Use importlib.metadata to get installed packages
            for dist in metadata.distributions():
                name = dist.metadata['Name'].lower()
                version = dist.version

                # Filter out standard library if not requested
                if not self.include_stdlib and self._is_stdlib(name):
                    continue

                packages[name] = version

            self._packages_cache = packages
            logger.info(f"Detected {len(packages)} packages in environment")

        except Exception as e:
            logger.error(f"Error detecting packages: {e}")
            # Fallback to basic package list
            packages = self._get_fallback_packages()

        return packages

    def _is_stdlib(self, package_name: str) -> bool:
        """
        Check if a package is part of the Python standard library.

        Args:
            package_name: Name of the package

        Returns:
            True if it's a standard library package
        """
        # List of common stdlib packages
        stdlib_packages = {
            'asyncio', 'concurrent', 'csv', 'datetime', 'decimal',
            'email', 'json', 'logging', 'math', 'os', 'pathlib',
            'random', 're', 'socket', 'sqlite3', 'sys', 'time',
            'urllib', 'uuid', 'warnings', 'collections', 'itertools',
            'functools', 'typing', 'dataclasses', 'enum', 'typing_extensions'
        }

        return package_name in stdlib_packages

    def _get_fallback_packages(self) -> Dict[str, str]:
        """
        Fallback method to get basic packages if metadata detection fails.

        Returns:
            Dictionary of package names to versions
        """
        packages = {}

        # Try to import common packages
        common_packages = [
            'pandas', 'numpy', 'scipy', 'sklearn', 'matplotlib',
            'seaborn', 'xgboost', 'lightgbm', 'torch', 'tensorflow'
        ]

        for pkg in common_packages:
            try:
                mod = __import__(pkg)
                version = getattr(mod, '__version__', 'unknown')
                packages[pkg] = version
            except ImportError:
                pass

        return packages

    def get_data_science_packages(self) -> Dict[str, str]:
        """
        Get only data science related packages.

        Returns:
            Dictionary of data science package names to versions
        """
        all_packages = self.detect_packages()
        ds_packages = {
            name: version
            for name, version in all_packages.items()
            if name in self.DATA_SCIENCE_PACKAGES
        }
        return ds_packages

    def format_as_context(self, packages: Optional[Dict[str, str]] = None) -> str:
        """
        Format package information as a context string for the agent.

        Args:
            packages: Package dictionary (uses detected if None)

        Returns:
            Formatted string describing available packages
        """
        if packages is None:
            packages = self.detect_packages()

        if not packages:
            return "No package information available."

        lines = [
            "Available Python packages in the current environment:",
            ""
        ]

        # Group by category
        ds_packages = self.get_data_science_packages()

        if ds_packages:
            lines.append("Data Science & ML Packages:")
            for name, version in sorted(ds_packages.items()):
                lines.append(f"  - {name} ({version})")
            lines.append("")

        # Other packages (limit to most common)
        other_packages = {
            name: version
            for name, version in packages.items()
            if name not in ds_packages
        }

        # Show top 20 other packages alphabetically
        if other_packages:
            lines.append("Other Available Packages (showing top 20):")
            for name, version in sorted(other_packages.items())[:20]:
                lines.append(f"  - {name} ({version})")

            if len(other_packages) > 20:
                lines.append(f"  ... and {len(other_packages) - 20} more packages")

        return "\n".join(lines)

    def save_to_config(self, config_path: Path, packages: Optional[Dict[str, str]] = None):
        """
        Save detected packages to a config file.

        Args:
            config_path: Path to config.yaml file
            packages: Package dictionary to save (detects if None)
        """
        if packages is None:
            packages = self.detect_packages()

        try:
            # Read existing config
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = {}

            # Add packages to config
            config['available_packages'] = {
                'enabled': True,
                'packages': packages,
                'last_updated': str(Path(__file__).stat().st_mtime)
            }

            # Write back
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Saved {len(packages)} packages to {config_path}")

        except Exception as e:
            logger.error(f"Error saving packages to config: {e}")

    def load_from_config(self, config_path: Path) -> Optional[Dict[str, str]]:
        """
        Load packages from a config file.

        Args:
            config_path: Path to config.yaml file

        Returns:
            Package dictionary if found, None otherwise
        """
        try:
            if not config_path.exists():
                return None

            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}

            pkg_config = config.get('available_packages', {})

            if not pkg_config.get('enabled', True):
                logger.info("Package detection is disabled in config")
                return None

            packages = pkg_config.get('packages', {})

            if packages:
                logger.info(f"Loaded {len(packages)} packages from {config_path}")
                return packages

            return None

        except Exception as e:
            logger.error(f"Error loading packages from config: {e}")
            return None


def detect_and_save_packages(config_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Convenience function to detect packages and save to config.

    Args:
        config_path: Path to config.yaml (uses default if None)

    Returns:
        Dictionary of detected packages
    """
    detector = PackageDetector()

    if config_path is None:
        # Try to find config.yaml in current directory or parent
        current_path = Path.cwd()
        while current_path != current_path.parent:
            potential_config = current_path / 'config.yaml'
            if potential_config.exists():
                config_path = potential_config
                break
            current_path = current_path.parent

        if config_path is None:
            config_path = Path.cwd() / 'config.yaml'

    packages = detector.detect_packages()
    detector.save_to_config(config_path, packages)

    return packages


if __name__ == "__main__":
    # Test the detector
    logging.basicConfig(level=logging.INFO)

    detector = PackageDetector()
    packages = detector.detect_packages()

    print("\n" + "="*70)
    print("Detected Packages")
    print("="*70)
    print(detector.format_as_context(packages))

    print("\n" + "="*70)
    print("Data Science Packages")
    print("="*70)
    ds_packages = detector.get_data_science_packages()
    for name, version in sorted(ds_packages.items()):
        print(f"  {name}: {version}")

    # Save to config
    config_path = Path("config.yaml")
    detector.save_to_config(config_path, packages)
    print(f"\n✓ Saved to {config_path}")
