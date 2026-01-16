#!/usr/bin/env python3
"""
DSLighting Setup Script - Auto-configure package detection on first install.

This script is automatically run after installation to detect available
packages and save them to config.yaml.
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def setup_package_context():
    """Auto-detect packages and configure on first install."""
    print("="*70)
    print("DSLighting Package Context Setup")
    print("="*70)
    print()

    # Check if already configured
    config_paths = [
        Path.cwd() / "config.yaml",
        Path.home() / ".dslighting" / "config.yaml",
    ]

    existing_config = None
    for config_path in config_paths:
        if config_path.exists():
            try:
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}

                if 'available_packages' in config:
                    existing_config = config_path
                    break
            except Exception:
                pass

    if existing_config:
        print(f"✓ Package context already configured:")
        print(f"  {existing_config}")
        print()
        print("💡 To re-detect packages, run:")
        print(f"  dslighting detect-packages")
        return

    # Detect packages
    print("📦 Detecting available Python packages...")
    print()

    try:
        from dslighting.utils.package_detector import PackageDetector

        detector = PackageDetector()
        packages = detector.detect_packages()

        print(f"✓ Found {len(packages)} packages")

        # Show data science packages
        ds_packages = detector.get_data_science_packages()
        if ds_packages:
            print(f"\n📊 Data Science Packages ({len(ds_packages)}):")
            for name, version in sorted(ds_packages.items()):
                print(f"   - {name}: {version}")

        # Determine config path
        config_path = Path.cwd() / "config.yaml"

        # Save to config
        detector.save_to_config(config_path, packages)

        print(f"\n✓ Configuration saved to:")
        print(f"  {config_path}")

        print()
        print("="*70)
        print("Setup Complete!")
        print("="*70)
        print()
        print("💡 Package context is now ENABLED by default")
        print("   The agent will automatically know about available packages")
        print()
        print("📝 Usage:")
        print("   agent = dslighting.Agent()  # Package context enabled (default)")
        print("   agent = dslighting.Agent(include_package_context=False)  # Disable")
        print()
        print("🔧 Management:")
        print("   dslighting detect-packages     # Re-detect packages")
        print("   dslighting show-packages       # Show detected packages")
        print("   dslighting validate-config     # Validate configuration")

    except Exception as e:
        print(f"\n⚠️  Setup failed: {e}")
        print()
        print("💡 You can manually set up later by running:")
        print("   dslighting detect-packages")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(setup_package_context())
