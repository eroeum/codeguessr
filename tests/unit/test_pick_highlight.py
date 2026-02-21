"""Unit tests for the _pick_highlight helper."""
from codeguessr.game import _pick_highlight


class TestPickHighlight:
    def test_returns_valid_index(self) -> None:
        """Verify that the returned index falls within the valid range of the line list."""
        lines = [f"line {i}" for i in range(50)]
        idx = _pick_highlight(lines)
        assert 0 <= idx < len(lines)

    def test_stays_within_middle_80_percent(self) -> None:
        """Verify that the chosen index stays within the middle 80 percent of the file."""
        lines = [f"def f_{i}(): pass" for i in range(100)]
        for _ in range(20):
            idx = _pick_highlight(lines)
            assert 10 <= idx <= 90

    def test_prefers_lines_with_content(self) -> None:
        """Verify that the only non-empty line is selected when all others are blank."""
        lines = ["" for _ in range(50)]
        lines[25] = "def real_function(): return True"
        assert _pick_highlight(lines) == 25

    def test_respects_min_chars(self) -> None:
        """Verify that only lines meeting the min_chars threshold are chosen."""
        # Only line 30 has >= 10 non-whitespace chars.
        lines = ["x" for _ in range(50)]
        lines[30] = "a longer line here!"
        idx = _pick_highlight(lines, min_chars=10)
        assert idx == 30

    def test_falls_back_to_any_nonempty_line(self) -> None:
        """Verify fallback to any non-empty line when no candidate meets min_chars."""
        lines = ["" for _ in range(30)]
        lines[15] = "a"
        # min_chars=5 means no candidates in middle-80%; falls back to any non-empty line.
        idx = _pick_highlight(lines, min_chars=5)
        assert idx == 15

    def test_handles_short_file(self) -> None:
        """Verify that a file with fewer than five lines returns a valid index."""
        lines = ["code"] * 3
        idx = _pick_highlight(lines)
        assert 0 <= idx < 3

    def test_handles_single_line(self) -> None:
        """Verify that a single-line file always returns index zero."""
        lines = ["only line"]
        idx = _pick_highlight(lines)
        assert idx == 0
