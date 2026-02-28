#!/usr/bin/env python3
"""Pre-deployment verification script for the website."""

import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


def check_file_exists(file_path: Path, description: str) -> bool:
    """Check if a file exists."""
    if file_path.exists():
        print(f"✅ {description}: Found")
        return True
    else:
        print(f"❌ {description}: Missing at {file_path}")
        return False


def verify_json_valid(file_path: Path) -> bool:
    """Verify JSON file is valid."""
    try:
        with file_path.open() as f:
            json.load(f)
        return True
    except json.JSONDecodeError as e:
        print(f"   ❌ Invalid JSON: {e}")
        return False


def verify_sitemap() -> bool:
    """Verify sitemap.xml is valid."""
    website_dir = Path(__file__).parent.parent / "website"
    sitemap_path = website_dir / "sitemap.xml"

    if not sitemap_path.exists():
        print("❌ Sitemap: Missing")
        return False

    try:
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = root.findall("sm:url", ns)

        if len(urls) >= 8:  # At least homepage + shows + episodes
            print(f"✅ Sitemap: Valid with {len(urls)} URLs")
            return True
        else:
            print(f"⚠️  Sitemap: Only {len(urls)} URLs (expected at least 8)")
            return False
    except ET.ParseError as e:
        print(f"❌ Sitemap: Invalid XML - {e}")
        return False


def verify_episodes() -> bool:
    """Verify episode JSON files."""
    website_dir = Path(__file__).parent.parent / "website"
    episodes_dir = website_dir / "data" / "episodes"

    all_valid = True

    for episode_file in ["hannah_the_historian.json", "oliver_the_inventor.json"]:
        file_path = episodes_dir / episode_file
        if not check_file_exists(file_path, f"Episodes: {episode_file}"):
            all_valid = False
            continue

        if not verify_json_valid(file_path):
            all_valid = False
            continue

        # Check episode count
        with file_path.open() as f:
            data = json.load(f)
            episode_count = len(data.get("episodes", []))
            if episode_count > 0:
                print(f"   ✅ {episode_count} episodes found")
            else:
                print("   ⚠️  No episodes in file")

    return all_valid


def verify_html_pages() -> bool:
    """Verify critical HTML pages exist."""
    website_dir = Path(__file__).parent.parent / "website"

    pages = [
        ("Homepage", website_dir / "index.html"),
        (
            "Hannah's Show",
            website_dir / "pages" / "shows" / "hannah-the-historian.html",
        ),
        ("Oliver's Show", website_dir / "pages" / "shows" / "oliver-the-inventor.html"),
        ("Subscribe Page", website_dir / "pages" / "subscribe.html"),
    ]

    all_exist = True
    for description, path in pages:
        if not check_file_exists(path, f"Page: {description}"):
            all_exist = False

    return all_exist


def verify_assets() -> bool:
    """Verify critical assets exist."""
    website_dir = Path(__file__).parent.parent / "website"

    assets = [
        ("JavaScript", website_dir / "js" / "bundle.min.js"),
        ("CSS", website_dir / "css" / "style.css"),
        ("Robots.txt", website_dir / "robots.txt"),
        ("Headers", website_dir / "_headers"),
    ]

    all_exist = True
    for description, path in assets:
        if not check_file_exists(path, f"Asset: {description}"):
            all_exist = False

    return all_exist


def verify_deployment_config() -> bool:
    """Verify deployment configuration exists."""
    repo_dir = Path(__file__).parent.parent

    configs = [
        ("GitHub Workflow", repo_dir / ".github" / "workflows" / "deploy-website.yml"),
        ("ADR 007", repo_dir / "docs" / "decisions" / "007-hosting-provider.md"),
        ("Deployment Guide", repo_dir / "docs" / "DEPLOYMENT.md"),
    ]

    all_exist = True
    for description, path in configs:
        if not check_file_exists(path, f"Config: {description}"):
            all_exist = False

    return all_exist


def main() -> int:
    """Run all verification checks."""
    print("🔍 Pre-Deployment Verification\n")
    print("=" * 50)

    checks = [
        ("HTML Pages", verify_html_pages),
        ("Episode Data", verify_episodes),
        ("Assets", verify_assets),
        ("Sitemap", verify_sitemap),
        ("Deployment Config", verify_deployment_config),
    ]

    results = []
    for check_name, check_func in checks:
        print(f"\n📋 Checking {check_name}...")
        print("-" * 50)
        result = check_func()
        results.append((check_name, result))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Summary")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check_name}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 All checks passed! Website is ready for deployment.")
        return 0
    else:
        failed = total - passed
        print(
            f"\n⚠️  {failed} check(s) failed. "
            "Please fix issues before deploying."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
