#!/usr/bin/env python3
"""Simple HTML validation script for website pages."""

import sys
from html.parser import HTMLParser
from pathlib import Path


class HTMLValidator(HTMLParser):
    """Simple HTML validator to check for basic issues."""

    def __init__(self) -> None:
        super().__init__()
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.tags_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Track opening tags."""
        # Only track tags that need closing
        if tag not in [
            "br",
            "img",
            "hr",
            "input",
            "meta",
            "link",
            "area",
            "base",
            "col",
            "embed",
            "param",
            "source",
            "track",
            "wbr",
        ]:
            self.tags_stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        """Check closing tags match."""
        if self.tags_stack and self.tags_stack[-1] == tag:
            self.tags_stack.pop()
        elif tag not in [
            "br",
            "img",
            "hr",
            "input",
            "meta",
            "link",
        ]:  # Ignore self-closing
            self.errors.append(f"Unexpected closing tag: {tag}")

    def error(self, message: str) -> None:
        """Handle parser errors."""
        self.errors.append(message)


def validate_html_file(file_path: Path) -> tuple[bool, list[str], list[str]]:
    """
    Validate an HTML file.

    Args:
        file_path: Path to HTML file

    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    validator = HTMLValidator()

    try:
        content = file_path.read_text(encoding="utf-8")
        validator.feed(content)

        # Check for unclosed tags
        if validator.tags_stack:
            validator.warnings.append(
                f"Potentially unclosed tags: {', '.join(validator.tags_stack)}"
            )

        # Basic checks
        if "<html" not in content.lower():
            validator.errors.append("Missing <html> tag")
        if "<head" not in content.lower():
            validator.errors.append("Missing <head> tag")
        if "<body" not in content.lower():
            validator.errors.append("Missing <body> tag")
        if "<title>" not in content.lower():
            validator.errors.append("Missing <title> tag")

        return len(validator.errors) == 0, validator.errors, validator.warnings

    except Exception as e:
        return False, [f"Failed to parse file: {e}"], []


def main() -> int:
    """Main validation function."""
    website_dir = Path(__file__).parent.parent / "website"

    # Find all HTML files
    html_files = [
        website_dir / "index.html",
        website_dir / "pages" / "about.html",
        website_dir / "pages" / "shows.html",
        website_dir / "pages" / "subscribe.html",
        website_dir / "pages" / "contact.html",
        website_dir / "pages" / "privacy.html",
        website_dir / "pages" / "shows" / "hannah-the-historian.html",
        website_dir / "pages" / "shows" / "oliver-the-inventor.html",
    ]

    all_valid = True
    total_errors = 0
    total_warnings = 0

    print("🔍 Validating HTML files...\n")

    for html_file in html_files:
        if not html_file.exists():
            print(f"⚠️  {html_file.relative_to(website_dir)}: File not found")
            all_valid = False
            continue

        is_valid, errors, warnings = validate_html_file(html_file)

        if is_valid and not warnings:
            print(f"✅ {html_file.relative_to(website_dir)}: Valid")
        elif is_valid:
            print(f"⚠️  {html_file.relative_to(website_dir)}: Valid with warnings")
            for warning in warnings:
                print(f"   - {warning}")
            total_warnings += len(warnings)
        else:
            print(f"❌ {html_file.relative_to(website_dir)}: Invalid")
            for error in errors:
                print(f"   - {error}")
            total_errors += len(errors)
            all_valid = False

    print("\n📊 Summary:")
    print(f"   Files checked: {len(html_files)}")
    print(f"   Errors: {total_errors}")
    print(f"   Warnings: {total_warnings}")

    if all_valid:
        print("\n✅ All HTML files are valid!")
        return 0
    else:
        print("\n❌ Some HTML files have errors.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
