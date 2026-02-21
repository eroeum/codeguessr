"""Unit tests for the _obscure helper."""
from codeguessr.game import _obscure


class TestObscure:
    def test_replaces_non_whitespace_with_block(self) -> None:
        """Verify that every non-whitespace character is replaced with a block glyph."""
        assert _obscure("hello") == "\u2588" * 5

    def test_preserves_leading_spaces(self) -> None:
        """Verify that leading spaces are left intact and only trailing content is obscured."""
        result = _obscure("    hello")
        assert result == "    " + "\u2588" * 5

    def test_preserves_leading_tab(self) -> None:
        """Verify that a leading tab character is preserved while the rest is obscured."""
        result = _obscure("\thello")
        assert result[0] == "\t"
        assert result[1:] == "\u2588" * 5

    def test_preserves_mixed_whitespace(self) -> None:
        """Verify that a mixed-whitespace prefix is preserved and content is obscured."""
        result = _obscure("  \t  code")
        assert result[:5] == "  \t  "
        assert result[5:] == "\u2588" * 4

    def test_empty_line_unchanged(self) -> None:
        """Verify that an empty string is returned unchanged."""
        assert _obscure("") == ""

    def test_whitespace_only_unchanged(self) -> None:
        """Verify that a whitespace-only string is returned unchanged."""
        assert _obscure("   \t  ") == "   \t  "

    def test_length_preserved(self) -> None:
        """Verify that the obscured output has the same length as the input."""
        line = "def foo(x, y): return x + y"
        assert len(_obscure(line)) == len(line)

    def test_full_replacement(self) -> None:
        """Verify that a string with no whitespace is fully replaced with block glyphs."""
        assert _obscure("abc") == "\u2588\u2588\u2588"

    def test_inline_spaces_preserved(self) -> None:
        """Verify that spaces between non-whitespace characters are preserved in the output."""
        result = _obscure("a b c")
        assert result == "\u2588 \u2588 \u2588"
