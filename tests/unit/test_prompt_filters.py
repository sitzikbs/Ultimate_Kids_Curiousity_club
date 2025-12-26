"""Unit tests for custom Jinja2 filters."""


from modules.prompts.filters import (
    capitalize_speaker,
    format_list,
    truncate_smart,
)


class TestFormatList:
    """Tests for format_list filter."""

    def test_format_list_basic(self):
        """Test basic list formatting."""
        result = format_list(["a", "b", "c"])
        assert result == "a, b, c"

    def test_format_list_custom_separator(self):
        """Test list formatting with custom separator."""
        result = format_list(["a", "b"], separator=" and ")
        assert result == "a and b"

    def test_format_list_empty(self):
        """Test formatting empty list."""
        result = format_list([])
        assert result == ""

    def test_format_list_none(self):
        """Test formatting None."""
        result = format_list(None)
        assert result == ""

    def test_format_list_single_item(self):
        """Test formatting single item list."""
        result = format_list(["only"])
        assert result == "only"

    def test_format_list_non_string_items(self):
        """Test formatting list with non-string items."""
        result = format_list([1, 2, 3])
        assert result == "1, 2, 3"

    def test_format_list_mixed_types(self):
        """Test formatting list with mixed types."""
        result = format_list([1, "hello", 3.14, True])
        assert result == "1, hello, 3.14, True"


class TestTruncateSmart:
    """Tests for truncate_smart filter."""

    def test_truncate_no_truncation_needed(self):
        """Test text that doesn't need truncation."""
        result = truncate_smart("Hello world", max_length=20)
        assert result == "Hello world"

    def test_truncate_at_word_boundary(self):
        """Test truncation at word boundary."""
        result = truncate_smart("This is a very long text", max_length=15)
        assert result == "This is a..."

    def test_truncate_custom_suffix(self):
        """Test truncation with custom suffix."""
        result = truncate_smart("This is a very long text", max_length=15, suffix="…")
        assert result == "This is a…"

    def test_truncate_none(self):
        """Test truncating None."""
        result = truncate_smart(None)
        assert result == ""

    def test_truncate_empty_string(self):
        """Test truncating empty string."""
        result = truncate_smart("")
        assert result == ""

    def test_truncate_exact_length(self):
        """Test text that is exactly max length."""
        result = truncate_smart("Hello", max_length=5)
        assert result == "Hello"

    def test_truncate_no_spaces(self):
        """Test truncation when no spaces found."""
        result = truncate_smart("Verylongwordwithoutspaces", max_length=10)
        assert result == "Verylon..."


class TestCapitalizeSpeaker:
    """Tests for capitalize_speaker filter."""

    def test_capitalize_basic(self):
        """Test basic speaker capitalization."""
        result = capitalize_speaker("oliver")
        assert result == "OLIVER"

    def test_capitalize_multi_word(self):
        """Test capitalizing multi-word speaker name."""
        result = capitalize_speaker("Hannah the Helper")
        assert result == "HANNAH THE HELPER"

    def test_capitalize_none(self):
        """Test capitalizing None."""
        result = capitalize_speaker(None)
        assert result == ""

    def test_capitalize_empty(self):
        """Test capitalizing empty string."""
        result = capitalize_speaker("")
        assert result == ""

    def test_capitalize_already_upper(self):
        """Test capitalizing already uppercase text."""
        result = capitalize_speaker("NARRATOR")
        assert result == "NARRATOR"
