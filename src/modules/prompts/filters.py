"""Custom Jinja2 filters for prompt templates."""

from typing import Any


def format_list(items: list[Any] | None, separator: str = ", ") -> str:
    """Format a list as a comma-separated string.

    Args:
        items: List of items to format (will be converted to strings)
        separator: Separator to use between items

    Returns:
        Formatted string with items separated by the separator

    Examples:
        >>> format_list(["a", "b", "c"])
        'a, b, c'
        >>> format_list(["a", "b"], separator=" and ")
        'a and b'
        >>> format_list(None)
        ''
        >>> format_list([])
        ''
    """
    if not items:
        return ""
    # Convert all items to strings for robustness
    return separator.join(str(item) for item in items)


def truncate_smart(text: str | None, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text at word boundaries.

    Args:
        text: Text to truncate
        max_length: Maximum length of the output
        suffix: Suffix to add when text is truncated

    Returns:
        Truncated text with suffix if needed

    Examples:
        >>> truncate_smart("Hello world", max_length=20)
        'Hello world'
        >>> truncate_smart("This is a very long text", max_length=15)
        'This is a...'
        >>> truncate_smart(None)
        ''
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    # Truncate at word boundary
    truncated = text[: max_length - len(suffix)]
    last_space = truncated.rfind(" ")

    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated + suffix


def capitalize_speaker(speaker: str | None) -> str:
    """Capitalize speaker name for script formatting.

    Args:
        speaker: Speaker name to capitalize

    Returns:
        Uppercased speaker name

    Examples:
        >>> capitalize_speaker("oliver")
        'OLIVER'
        >>> capitalize_speaker("Hannah the Helper")
        'HANNAH THE HELPER'
        >>> capitalize_speaker(None)
        ''
    """
    if not speaker:
        return ""
    return speaker.upper()


# Dictionary of all custom filters for easy registration
CUSTOM_FILTERS = {
    "format_list": format_list,
    "truncate_smart": truncate_smart,
    "capitalize_speaker": capitalize_speaker,
}
