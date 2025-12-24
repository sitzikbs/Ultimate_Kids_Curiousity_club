#!/usr/bin/env python3
"""
Project management script for Ultimate Kids Curiosity Club.
Manages GitHub issues for all Work Packages (WP0, WP1a-WP1e, WP2a-WP2b, etc.).
"""

import json
import re
import subprocess
import sys
from pathlib import Path

# Configuration
WORKSPACE_ROOT = Path("/workspaces/Ultimate_Kids_Curiousity_club")
DOCS_DIR = WORKSPACE_ROOT / "docs/work_packages"

# Dependency and parallelization mapping
DEPENDENCY_MAP = {
    "WP0": {"depends_on": ["WP1a", "WP1b"], "phase": 2},
    "WP1a": {"depends_on": [], "phase": 1},
    "WP1b": {"depends_on": [], "phase": 1},
    "WP1c": {"depends_on": ["WP1a", "WP1b"], "phase": 2},
    "WP1d": {"depends_on": ["WP1a", "WP1b"], "phase": 2},
    "WP1e": {"depends_on": ["WP1a", "WP1b", "WP1c", "WP1d"], "phase": 3},
    "WP2a": {"depends_on": ["WP0", "WP1a", "WP1b"], "phase": 3},
    "WP2b": {"depends_on": ["WP2a"], "phase": 4},
    "WP3": {"depends_on": ["WP1a", "WP1b"], "phase": 2},
    "WP4": {"depends_on": ["WP3"], "phase": 4},
    "WP5": {"depends_on": ["WP1a", "WP1b"], "phase": 2},
    "WP6a": {"depends_on": ["WP0", "WP1c", "WP2a", "WP2b"], "phase": 5},
    "WP6b": {"depends_on": ["WP6a", "WP3", "WP4", "WP5"], "phase": 6},
    "WP7a": {"depends_on": ["WP1c"], "phase": 3},
    "WP7b": {"depends_on": ["WP6a", "WP6b", "WP7a"], "phase": 7},
    "WP8": {"depends_on": [], "phase": 1},  # Ongoing, can start anytime
    "WP9a": {"depends_on": ["WP1c"], "phase": 3},
    "WP9b": {"depends_on": ["WP9a", "WP5"], "phase": 4},
    "WP9c": {"depends_on": ["WP9a", "WP9b", "WP6a", "WP6b"], "phase": 7},
    "WP10a": {"depends_on": [], "phase": 2},  # Can start anytime (static site)
    "WP10b": {"depends_on": ["WP6b", "WP7b"], "phase": 8},
}

def run_command(command):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=WORKSPACE_ROOT
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e.stderr}")
        return None

def get_wp_id(file_path):
    """Extract WP ID (e.g., WP1a) from filename."""
    match = re.search(r'(WP\d+[a-z]?)', file_path.name)
    return match.group(1) if match else None

def parse_wp_file(file_path):
    """Parse a WP markdown file to extract title and content for issue."""
    content = file_path.read_text()
    lines = content.split('\n')
    
    title = None
    # Extract title from first line
    if lines and lines[0].startswith('# '):
        title = lines[0][2:].strip()
    
    if not title:
        title = file_path.stem.replace('_', ' ')
    
    wp_id = get_wp_id(file_path)
    
    # Get dependency info with safe defaults
    if wp_id and wp_id in DEPENDENCY_MAP:
        dep_info = DEPENDENCY_MAP[wp_id]
    else:
        dep_info = {"depends_on": [], "phase": 0}
    
    # Create issue body
    # We want to link to the file and list the tasks
    relative_path = file_path.relative_to(WORKSPACE_ROOT)
    
    body = f"**Work Package Document**: [{relative_path}]({relative_path})\n\n"
    
    # Add parallelization info
    if dep_info["depends_on"]:
        deps_str = ", ".join(dep_info["depends_on"])
        body += f"**⚠️ Dependencies**: {deps_str}\n\n"
    else:
        body += "**✅ No Dependencies** - Can start immediately!\n\n"
    
    body += f"**🔢 Phase**: {dep_info['phase']}\n\n"
    
    # Determine what can be done in parallel
    parallel_wps = [wp for wp, info in DEPENDENCY_MAP.items() 
                    if info["phase"] == dep_info["phase"] and wp != wp_id]
    if parallel_wps:
        body += f"**🔀 Can be done in parallel with**: {', '.join(parallel_wps)}\n\n"
    
    body += "---\n\n"
    
    # Extract Overview
    body += "## Overview\n"
    in_overview = False
    for line in lines:
        if line.startswith("## 📋 Overview"):
            in_overview = True
            continue
        if line.startswith("## 🎯 High-Level Tasks"):
            in_overview = False
            break
        if in_overview and line.strip():
            body += line + "\n"
            
    body += "\n## Tasks\n"
    
    # Extract Tasks and Subtasks
    # We'll just grab the High-Level Tasks section down to the next H2 or end
    in_tasks = False
    for line in lines:
        if line.startswith("## 🎯 High-Level Tasks"):
            in_tasks = True
            continue
        if line.startswith("## ") and in_tasks: # Next section
            in_tasks = False
            break
        if in_tasks:
            body += line + "\n"

    # Add Feedback Checkpoints if not present in the text
    if "Feedback Checkpoints" not in content and "Checkpoint" not in content:
        body += "\n\n## 🔄 Feedback Checkpoints\n"
        body += "### Midway Checkpoint\n"
        body += "**Please request feedback when 50% of tasks are complete.**\n\n"
        body += "### Final Checkpoint\n"
        body += "**Please request feedback when all tasks are complete.**\n"

    return title, body

def close_all_issues():
    """Close all existing open issues."""
    output = run_command("gh issue list --limit 100 --json number,title --state open")
    if output:
        try:
            issues = json.loads(output)
            print(f"Found {len(issues)} open issues to close.")
            for issue in issues:
                num = issue['number']
                title = issue['title']
                print(f"🗑️  Closing issue #{num}: {title}")
                run_command(f'gh issue close {num} --comment "Closing to reorganize into sub-Work Packages. New issues will be created with clearer dependencies and parallelization info."')
            print(f"✅ Closed {len(issues)} issues.\n")
        except json.JSONDecodeError:
            print("Failed to parse issue list JSON")
    else:
        print("No open issues found.\n")

def get_existing_issues():
    """Get list of existing issue titles."""
    output = run_command("gh issue list --limit 100 --json title --state open")
    if output:
        try:
            issues = json.loads(output)
            return [issue['title'] for issue in issues]
        except json.JSONDecodeError:
            print("Failed to parse issue list JSON")
            return []
    return []

def create_issues():
    """Create GitHub issues for each WP."""
    existing_titles = get_existing_issues()
    print(f"Found {len(existing_titles)} existing open issues.")
    
    # Sort files by phase first, then by WP number
    def sort_key(p):
        wp_id = get_wp_id(p)
        if not wp_id:
            return (999, 0, '')
        dep_info = DEPENDENCY_MAP.get(wp_id, {"depends_on": [], "phase": 999})
        match = re.search(r'WP(\d+)([a-z]?)', p.name)
        if match:
            num = int(match.group(1))
            letter = match.group(2) or ''
            return (dep_info["phase"], num, letter)
        return (999, 0, '')
    
    wp_files = sorted(list(DOCS_DIR.glob("WP*.md")), key=sort_key)
    
    print(f"Found {len(wp_files)} Work Package documents.")
    print(f"Creating issues in phase order...\n")
    
    current_phase = None
    for wp_file in wp_files:
        wp_id = get_wp_id(wp_file)
        
        # Get dependency info with safe defaults
        if wp_id and wp_id in DEPENDENCY_MAP:
            dep_info = DEPENDENCY_MAP[wp_id]
        else:
            dep_info = {"depends_on": [], "phase": 0}
        
        # Print phase header
        if dep_info["phase"] != current_phase:
            current_phase = dep_info["phase"]
            print(f"\n{'='*60}")
            print(f"Phase {current_phase}")
            print(f"{'='*60}")
        
        title, body = parse_wp_file(wp_file)
        
        if title in existing_titles:
            print(f"⏭️  Skipping existing issue: {title}")
            continue
            
        print(f"📝 Creating issue for: {title}")
        
        # Write body to temp file to avoid shell escaping issues
        temp_body_file = WORKSPACE_ROOT / "temp_issue_body.md"
        temp_body_file.write_text(body)
        
        # Create issue without labels (labels don't exist yet in repo)
        cmd = f'gh issue create --title "{title}" --body-file "{temp_body_file}"'
        result = run_command(cmd)
        
        if result:
            print(f"✅ Created: {result}")
        else:
            print(f"❌ Failed to create issue for {title}")
        
        if temp_body_file.exists():
            temp_body_file.unlink()
    
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"{'='*60}")
    phase_summary = {}
    for wp_id, info in DEPENDENCY_MAP.items():
        phase = info["phase"]
        phase_summary[phase] = phase_summary.get(phase, 0) + 1
    
    for phase in sorted(phase_summary.keys()):
        count = phase_summary[phase]
        print(f"Phase {phase}: {count} Work Packages")
    print()

def main():
    print("=" * 60)
    print("Ultimate Kids Curiosity Club - Project Management Script")
    print("=" * 60)
    print()
    
    # Check if gh CLI is available
    if not run_command("gh --version"):
        print("❌ Error: GitHub CLI (gh) is not installed or not in PATH.")
        print("   Install it from: https://cli.github.com/")
        sys.exit(1)
    
    # Check if authenticated
    auth_check = run_command("gh auth status")
    if not auth_check or "Logged in" not in auth_check:
        print("❌ Error: Not authenticated with GitHub CLI.")
        print("   Run: gh auth login")
        sys.exit(1)
    
    print("✅ GitHub CLI is ready.\n")
    
    # Close all existing issues
    print("Step 1: Closing existing issues...")
    print("-" * 60)
    close_all_issues()
    
    # Create new issues
    print("Step 2: Creating new issues with dependency info...")
    print("-" * 60)
    create_issues()
    
    print()
    print("=" * 60)
    print("✅ Done! Check GitHub Issues for all Work Packages.")
    print()
    print("📊 Parallelization Strategy:")
    print("  • Phase 1: WP1a, WP1b, WP8 (can all run in parallel)")
    print("  • Phase 2: WP0, WP1c, WP1d, WP3, WP5, WP10a (after Phase 1)")
    print("  • Phase 3: WP1e, WP2a, WP7a, WP9a (after Phase 2)")
    print("  • Phase 4+: Continue with dependency chain")
    print("=" * 60)

if __name__ == "__main__":
    main()
