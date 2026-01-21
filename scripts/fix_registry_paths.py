"""
Fix registry config files - convert to relative paths (but keep preparer unchanged)
"""
import yaml
from pathlib import Path

def fix_config_file(config_path: Path):
    """Fix a single config file"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        modified = False

        # Fix description path
        if 'description' in config:
            old_desc = config['description']
            if old_desc and '/' in old_desc:
                # Extract just the filename
                config['description'] = 'description.md'
                modified = True
                print(f"  description: {old_desc} -> description.md")

        # Fix grader.grade_fn
        if 'grader' in config and 'grade_fn' in config['grader']:
            old_grade_fn = config['grader']['grade_fn']
            if old_grade_fn and ':' in old_grade_fn and old_grade_fn.startswith('mlebench.'):
                # Only fix if it starts with mlebench.
                # e.g., "mlebench.competitions.task.grade:grade" -> "grade:grade"
                module_name = old_grade_fn.split(':')[-1]
                config['grader']['grade_fn'] = f"{module_name}:{module_name}"
                modified = True
                print(f"  grade_fn: {old_grade_fn} -> {module_name}:{module_name}")

        # DO NOT modify preparer - keep original paths

        if modified:
            # Write back
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            return True

        return False

    except Exception as e:
        print(f"Error processing {config_path}: {e}")
        return False

def main():
    """Fix all registry config files"""
    registry_dir = Path("/Users/liufan/projects/share/dslighting/dslighting/registry")

    print(f"Scanning {registry_dir} for config.yaml files...")

    config_files = list(registry_dir.glob("*/config.yaml"))
    print(f"Found {len(config_files)} config files\n")

    fixed_count = 0
    for config_file in sorted(config_files):
        task_name = config_file.parent.name
        print(f"Processing: {task_name}")
        if fix_config_file(config_file):
            fixed_count += 1

    print(f"\n\n{'='*80}")
    print(f"Fixed {fixed_count}/{len(config_files)} config files")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
