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

    # Check if user wants all packages or only data science packages
    save_all = hasattr(args, 'all') and args.all

    if save_all:
        print(f"📦 Detecting ALL packages...")
        print(f"   Config: {config_path}")
        print(f"   Mode: Save all packages (including dependencies)")
    else:
        print(f"📦 Detecting Data Science & ML packages...")
        print(f"   Config: {config_path}")
        print(f"   Mode: Save only Data Science packages (recommended)")

    detector = PackageDetector()
    packages = detector.detect_packages()

    print(f"\n✓ Found {len(packages)} total packages in environment")

    # Show data science packages
    ds_packages = detector.get_data_science_packages()
    if ds_packages:
        print(f"\n📊 Data Science & ML Packages ({len(ds_packages)}):")
        for name, version in sorted(ds_packages.items()):
            print(f"   - {name} ({version})")

    if save_all:
        print(f"\n📦 Other Packages: {len(packages) - len(ds_packages)}")
        print(f"   (Use '--data-science-only' to save only DS packages)")

    # Save to config
    data_science_only = not save_all
    detector.save_to_config(config_path, packages, data_science_only=data_science_only)

    if save_all:
        print(f"\n✓ Saved all {len(packages)} packages to config: {config_path}")
    else:
        print(f"\n✓ Saved {len(ds_packages)} Data Science packages to config: {config_path}")

    # Show summary
    print(f"\n📝 Summary:")
    print(f"   Total packages in environment: {len(packages)}")
    print(f"   Data Science packages: {len(ds_packages)}")
    print(f"   Saved to config: {len(ds_packages) if not save_all else len(packages)}")
    print(f"   Config file: {config_path}")

    if not save_all:
        print(f"\n💡 Tip: Use 'dslighting detect-packages --all' to save all packages")
    else:
        print(f"\n💡 Tip: Use 'dslighting detect-packages --data-science-only' to save only DS packages")

    print(f"   Use 'agent = dslighting.Agent()' to automatically use this context")
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


def cmd_help(args):
    """Show DSLighting help and quick start guide."""
    print("=" * 70)
    print("DSLighting - Data Science Agent Framework")
    print("=" * 70)
    print()
    print("🚀 Quick Start:")
    print("-" * 70)
    print("""
from dotenv import load_dotenv
load_dotenv()

import dslighting

# Method 1: Use built-in dataset
data = dslighting.load_data("bike-sharing-demand")
agent = dslighting.Agent(workflow="aide")
result = agent.run(data)

# Method 2: Quick one-liner
result = dslighting.run_agent(task_id="bike-sharing-demand")
""")

    print("📋 Available Workflows:")
    print("-" * 70)
    print("""
  1. aide              - Adaptive Iteration & Debugging (Default)
  2. autokaggle        - Advanced competition solver
  3. data_interpreter  - Interactive data analysis
  4. automind          - Complex planning with knowledge base
  5. dsagent           - Long-term planning with logging
  6. deepanalyze       - Deep analysis with structured tags
""")

    print("💡 Useful Commands:")
    print("-" * 70)
    print("""
  dslighting workflows              - Show all workflows with details
  dslighting example <workflow>      - Show workflow example code
  dslighting quickstart             - Show detailed quick start guide
  dslighting detect-packages        - Detect available Python packages
  dslighting show-packages          - Show detected packages
""")

    print("📚 Documentation:")
    print("-" * 70)
    print("""
  Online:  https://luckyfan-cs.github.io/dslighting-web/
  GitHub:  https://github.com/usail-hkust/dslighting
  PyPI:    https://pypi.org/project/dslighting/
""")

    print("🔧 Python Help Functions:")
    print("-" * 70)
    print("""
  import dslighting
  dslighting.help()              - Show this help
  dslighting.list_workflows()    - List all workflows
  dslighting.show_example("aide") - Show workflow example
""")

    return 0


def cmd_workflows(args):
    """List all available workflows with details."""
    print("=" * 70)
    print("DSLighting Workflows")
    print("=" * 70)
    print()

    workflows = [
        {
            "name": "aide",
            "full_name": "AIDE (Adaptive Iteration & Debugging Enhancement)",
            "description": "Self-improving code with iterative debugging",
            "use_cases": ["Kaggle competitions (simple)", "Data analysis", "Quick prototyping"],
            "default_model": "gpt-4o",
            "parameters": {"max_iterations": 10, "temperature": 0.7},
            "unique_params": None
        },
        {
            "name": "autokaggle",
            "full_name": "AutoKaggle",
            "description": "Advanced competition solver with dynamic phase planning",
            "use_cases": ["Kaggle competitions (complex)", "High-stakes competitions", "Multi-phase problems"],
            "default_model": "gpt-4o",
            "parameters": {"temperature": 0.5},
            "unique_params": {
                "max_attempts_per_phase": "Max retries per phase (default: 5)",
                "success_threshold": "Score threshold 1-5 (default: 3.0)"
            }
        },
        {
            "name": "data_interpreter",
            "full_name": "DataInterpreter",
            "description": "Interactive data analysis and exploration",
            "use_cases": ["Data exploration", "Visualization", "Quick analysis"],
            "default_model": "gpt-4o-mini",
            "parameters": {"max_iterations": 5, "temperature": 0.7},
            "unique_params": None
        },
        {
            "name": "automind",
            "full_name": "AutoMind",
            "description": "Complex planning with knowledge base and experience replay",
            "use_cases": ["Complex tasks", "Multi-step problems", "Need historical context"],
            "default_model": "gpt-4o",
            "parameters": {"max_iterations": 10, "temperature": 0.5},
            "unique_params": {
                "case_dir": "Experience replay directory (e.g., ./experience_replay)"
            }
        },
        {
            "name": "dsagent",
            "full_name": "DS-Agent",
            "description": "Long-term planning with Plan-Execute-Log loop",
            "use_cases": ["Long-running tasks", "Need detailed logging", "Step-by-step refinement"],
            "default_model": "gpt-4o",
            "parameters": {"max_iterations": 15, "temperature": 0.6},
            "unique_params": {
                "case_dir": "Experience replay directory (e.g., ./experience_replay)"
            }
        },
        {
            "name": "deepanalyze",
            "full_name": "DeepAnalyze",
            "description": "Deep analysis with structured thinking tags",
            "use_cases": ["Deep data analysis", "Complex reasoning", "Structured outputs"],
            "default_model": "gpt-4o",
            "parameters": {"max_iterations": 10, "temperature": 0.8},
            "unique_params": None
        }
    ]

    for idx, wf in enumerate(workflows, 1):
        print(f"{idx}. {wf['name'].upper()}")
        print(f"   Full Name: {wf['full_name']}")
        print(f"   Description: {wf['description']}")
        print(f"   Use Cases: {', '.join(wf['use_cases'])}")
        print(f"   Default Model: {wf['default_model']}")

        if wf['unique_params']:
            print(f"   Unique Parameters:")
            for param, desc in wf['unique_params'].items():
                print(f"     - {param}: {desc}")
        else:
            print(f"   Unique Parameters: None (uses common params only)")

        print()

    print("💡 Use 'dslighting example <workflow>' to see example code")
    print("💡 Use 'dslighting help' for quick start guide")

    return 0


def cmd_example(args):
    """Show workflow example code."""
    workflow_name = args.workflow.lower()

    examples = {
        "aide": """
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("bike-sharing-demand")

agent = dslighting.Agent(
    workflow="aide",
    model="gpt-4o",
    temperature=0.7,
    max_iterations=10,
)

result = agent.run(data)

print(f"Score: {result.score}")
print(f"Cost: ${result.cost:.2f}")
""",
        "autokaggle": """
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("bike-sharing-demand")

agent = dslighting.Agent(
    workflow="autokaggle",
    model="gpt-4o",
    temperature=0.5,

    autokaggle={
        "max_attempts_per_phase": 5,
        "success_threshold": 3.5
    }
)

result = agent.run(data)

print(f"Score: {result.score}")
print(f"Duration: {result.duration:.1f}s")
print(f"Cost: ${result.cost:.2f}")
""",
        "data_interpreter": """
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("sales_data.csv")

agent = dslighting.Agent(
    workflow="data_interpreter",
    model="gpt-4o-mini",
    temperature=0.7,
    max_iterations=5,
)

result = agent.run(data, description="分析销售趋势")

print(f"Output: {result.output}")
print(f"Cost: ${result.cost:.2f}")
""",
        "automind": """
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("bike-sharing-demand")

agent = dslighting.Agent(
    workflow="automind",
    model="gpt-4o",
    temperature=0.5,
    max_iterations=10,

    automind={
        "case_dir": "./experience_replay"
    }
)

result = agent.run(data)

print(f"Score: {result.score}")
print(f"Output: {result.output}")
print(f"Cost: ${result.cost:.2f}")
""",
        "dsagent": """
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("bike-sharing-demand")

agent = dslighting.Agent(
    workflow="dsagent",
    model="gpt-4o",
    temperature=0.6,
    max_iterations=15,

    dsagent={
        "case_dir": "./experience_replay"
    }
)

result = agent.run(data)

print(f"Score: {result.score}")
print(f"Output: {result.output}")
print(f"Cost: ${result.cost:.2f}")
""",
        "deepanalyze": """
from dotenv import load_dotenv
load_dotenv()

import dslighting

data = dslighting.load_data("your_data.csv")

agent = dslighting.Agent(
    workflow="deepanalyze",
    model="gpt-4o",
    temperature=0.8,
    max_iterations=10,
)

result = agent.run(data, description="深度分析数据")

print(f"Output: {result.output}")
print(f"Cost: ${result.cost:.2f}")
"""
    }

    if workflow_name not in examples:
        print(f"❌ Unknown workflow: {args.workflow}")
        print(f"\nAvailable workflows: {', '.join(examples.keys())}")
        print(f"\nUse 'dslighting workflows' to see all workflows")
        return 1

    print("=" * 70)
    print(f"Example: {workflow_name.upper()}")
    print("=" * 70)
    print(examples[workflow_name])
    print("=" * 70)
    print(f"💡 Copy this code and run it!")
    print(f"💡 Use 'dslighting workflows' for more workflow details")

    return 0


def cmd_quickstart(args):
    """Show detailed quick start guide."""
    print("=" * 70)
    print("DSLighting Quick Start Guide")
    print("=" * 70)
    print()

    print("📦 Installation")
    print("-" * 70)
    print("""
pip install dslighting
""")

    print("🔑 Setup API Keys")
    print("-" * 70)
    print("""
# Create .env file in your project directory:
echo 'OPENAI_API_KEY=your_key_here' > .env
echo 'ANTHROPIC_API_KEY=your_key_here' >> .env
""")

    print("🚀 Your First Agent (3 Simple Steps)")
    print("-" * 70)
    print("""
# Step 1: Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Step 2: Import DSLighting
import dslighting

# Step 3: Run your first agent
result = dslighting.run_agent(
    task_id="bike-sharing-demand",
    workflow="aide"
)

print(f"Success! Score: {result.score}")
""")

    print("📊 Using Your Own Data")
    print("-" * 70)
    print("""
import dslighting

# Load your data
data = dslighting.load_data("path/to/your/data.csv")

# Create agent
agent = dslighting.Agent(workflow="data_interpreter")

# Run with custom description
result = agent.run(data, description="分析销售数据并找出趋势")
""")

    print("🎯 Choosing the Right Workflow")
    print("-" * 70)
    print("""
  Task Type                     | Recommended Workflow
  ------------------------------|----------------------
  Quick analysis                | data_interpreter
  Simple competition            | aide
  Complex competition           | autokaggle
  Need historical knowledge     | automind
  Long-running task             | dsagent
  Deep analysis                 | deepanalyze
""")

    print("💡 Pro Tips")
    print("-" * 70)
    print("""
1. Start with 'aide' workflow for most tasks
2. Use 'gpt-4o-mini' for faster, cheaper results
3. Set max_iterations to control cost/time
4. Use keep_workspace=True to debug
5. Check results.score to evaluate performance
""")

    print("📚 Next Steps")
    print("-" * 70)
    print("""
  dslighting workflows           - See all workflows
  dslighting example aide        - See workflow examples
  dslighting help                - Show all commands

  https://luckyfan-cs.github.io/dslighting-web/  - Full documentation
""")

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='dslighting',
        description='DSLighting - Data Science Agent CLI'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # help command
    help_parser = subparsers.add_parser(
        'help',
        help='Show DSLighting help and quick start guide'
    )
    help_parser.set_defaults(func=cmd_help)

    # workflows command
    workflows_parser = subparsers.add_parser(
        'workflows',
        help='List all available workflows with details'
    )
    workflows_parser.set_defaults(func=cmd_workflows)

    # example command
    example_parser = subparsers.add_parser(
        'example',
        help='Show workflow example code'
    )
    example_parser.add_argument(
        'workflow',
        help='Workflow name (e.g., aide, autokaggle, data_interpreter, etc.)'
    )
    example_parser.set_defaults(func=cmd_example)

    # quickstart command
    quickstart_parser = subparsers.add_parser(
        'quickstart',
        help='Show detailed quick start guide'
    )
    quickstart_parser.set_defaults(func=cmd_quickstart)

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
    detect_parser.add_argument(
        '--all',
        action='store_true',
        help='Save all packages (including dependencies). Default: save only Data Science packages'
    )
    detect_parser.add_argument(
        '--data-science-only',
        action='store_true',
        help='Save only Data Science & ML packages (default behavior)'
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
        cmd_help(None)
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
