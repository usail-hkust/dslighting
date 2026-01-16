#!/usr/bin/env python3
"""
DSLighting CLI - Command-line interface for DSLighting management.

Provides commands for package detection, configuration, and maintenance.
"""

import argparse
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def cmd_detect_packages(args):
    """Detect and save available packages to config."""
    from dslighting.utils.package_detector import PackageDetector

    config_path = Path(args.config) if args.config else None

    if config_path is None:
        # Find config.yaml
        for path in [Path.cwd(), Path.cwd().parent, Path.home() / ".dslighting"]:
            potential = path / "config.yaml"
            if potential.exists():
                config_path = potential
                break

    if config_path is None:
        config_path = Path.cwd() / "config.yaml"

    print(f"📦 Detecting packages...")
    print(f"   Config: {config_path}")

    detector = PackageDetector()
    packages = detector.detect_packages()

    print(f"\n✓ Found {len(packages)} packages")

    # Show data science packages
    ds_packages = detector.get_data_science_packages()
    if ds_packages:
        print(f"\n📊 Data Science Packages ({len(ds_packages)}):")
        for name, version in sorted(ds_packages.items()):
            print(f"   - {name}: {version}")

    # Save to config
    detector.save_to_config(config_path, packages)
    print(f"\n✓ Saved to config: {config_path}")

    # Show summary
    print(f"\n📝 Summary:")
    print(f"   Total packages: {len(packages)}")
    print(f"   Data Science packages: {len(ds_packages)}")
    print(f"   Config file: {config_path}")
    print(f"\n💡 Tip: Use 'agent = dslighting.Agent()' to automatically use this context")
    print(f"   Use 'agent = dslighting.Agent(include_package_context=False)' to disable")


def cmd_show_packages(args):
    """Show detected packages from config."""
    from dslighting.utils.package_detector import PackageDetector

    config_path = Path(args.config) if args.config else None

    if config_path is None:
        # Find config.yaml
        for path in [Path.cwd(), Path.cwd().parent, Path.home() / ".dslighting"]:
            potential = path / "config.yaml"
            if potential.exists():
                config_path = potential
                break

    if config_path is None or not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print(f"   Run 'dslighting detect-packages' first")
        return 1

    print(f"📋 Loading packages from: {config_path}")

    detector = PackageDetector()
    packages = detector.load_from_config(config_path)

    if packages is None:
        print(f"❌ No packages found in config")
        print(f"   Run 'dslighting detect-packages' to detect packages")
        return 1

    print(f"\n✓ Found {len(packages)} packages in config")

    # Show formatted context
    print(f"\n{detector.format_as_context(packages)}")

    return 0


def cmd_validate_config(args):
    """Validate DSLighting configuration."""
    import yaml

    config_path = Path(args.config) if args.config else Path.cwd() / "config.yaml"

    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return 1

    print(f"🔍 Validating: {config_path}")

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Check available_packages section
        if 'available_packages' in config:
            pkg_config = config['available_packages']

            print(f"\n✓ Package detection configured:")
            print(f"   Enabled: {pkg_config.get('enabled', True)}")
            print(f"   Packages: {len(pkg_config.get('packages', {}))}")

            if pkg_config.get('enabled', True):
                print(f"\n💡 Package context is ENABLED")
                print(f"   Agent will automatically know about available packages")
            else:
                print(f"\n⚠️  Package context is DISABLED")
                print(f"   Agent will not be aware of available packages")
                print(f"   Enable with: available_packages.enabled = true")
        else:
            print(f"\n⚠️  No package detection configured")
            print(f"   Run 'dslighting detect-packages' to set up")

        print(f"\n✓ Configuration is valid")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='dslighting',
        description='DSLighting - Data Science Agent CLI'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # detect-packages command
    detect_parser = subparsers.add_parser(
        'detect-packages',
        help='Detect and save available Python packages to config'
    )
    detect_parser.add_argument(
        '-c', '--config',
        help='Path to config.yaml file',
        default=None
    )
    detect_parser.set_defaults(func=cmd_detect_packages)

    # show-packages command
    show_parser = subparsers.add_parser(
        'show-packages',
        help='Show detected packages from config'
    )
    show_parser.add_argument(
        '-c', '--config',
        help='Path to config.yaml file',
        default=None
    )
    show_parser.set_defaults(func=cmd_show_packages)

    # validate-config command
    validate_parser = subparsers.add_parser(
        'validate-config',
        help='Validate DSLighting configuration'
    )
    validate_parser.add_argument(
        '-c', '--config',
        help='Path to config.yaml file',
        default=None
    )
    validate_parser.set_defaults(func=cmd_validate_config)

    # Parse arguments
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    # Execute command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Interrupted")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
