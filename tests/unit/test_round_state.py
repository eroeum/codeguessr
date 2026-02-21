"""Unit tests for RoundState."""
import re

from codeguessr.game import ATTEMPT_POINTS, MAX_GUESSES_PER_ROUND, REVEAL_STAGES, RoundState

OBSCURED_RE = re.compile(r"^[\u2588\s]*$")

# 60 lines of realistic-looking code used across reveal-stage tests.
_LINES: list[str] = [f"    result_{i} = compute(x={i}, y={i * 2})" for i in range(60)]


def _make(
    *,
    hl: int = 20,
    wrong: int = 0,
    correct: bool = False,
    max_guesses: int = MAX_GUESSES_PER_ROUND,
) -> RoundState:
    """Construct a RoundState with the given parameters for testing.

    Args:
        hl: 0-based highlight line index.
        wrong: Number of wrong guesses to pre-populate.
        correct: Whether to mark the round as already correct.
        max_guesses: Maximum wrong guesses allowed.

    Returns:
        A pre-configured RoundState instance.
    """
    rs = RoundState(target_file="target.py", highlight_line=hl, max_guesses=max_guesses)
    for i in range(wrong):
        rs.wrong_guesses.append(f"wrong_{i}.py")
    rs.correct = correct
    return rs


class TestRoundStateProperties:
    def test_num_wrong_counts_list(self) -> None:
        """Verify that num_wrong reflects the length of wrong_guesses."""
        assert _make(wrong=3).num_wrong == 3

    def test_is_over_when_correct(self) -> None:
        """Verify that is_over returns True when the round is marked correct."""
        assert _make(correct=True).is_over

    def test_is_over_when_max_guesses_reached(self) -> None:
        """Verify that is_over returns True when max guesses are exhausted."""
        assert _make(wrong=MAX_GUESSES_PER_ROUND).is_over

    def test_not_over_before_max_guesses(self) -> None:
        """Verify that is_over returns False when one guess remains."""
        assert not _make(wrong=MAX_GUESSES_PER_ROUND - 1).is_over

    def test_guesses_remaining(self) -> None:
        """Verify that guesses_remaining equals max_guesses minus wrong guess count."""
        assert _make(wrong=2).guesses_remaining == MAX_GUESSES_PER_ROUND - 2

    def test_guesses_remaining_reaches_zero(self) -> None:
        """Verify that guesses_remaining is zero when all guesses are used."""
        assert _make(wrong=MAX_GUESSES_PER_ROUND).guesses_remaining == 0

    def test_potential_score_at_zero_wrong(self) -> None:
        """Verify potential_score equals the first ATTEMPT_POINTS entry with no wrong guesses."""
        assert _make(wrong=0).potential_score == ATTEMPT_POINTS[0]

    def test_potential_score_matches_attempt_points(self) -> None:
        """Verify that potential_score matches ATTEMPT_POINTS at each wrong-guess index."""
        for i, expected in enumerate(ATTEMPT_POINTS):
            assert _make(wrong=i).potential_score == expected

    def test_potential_score_caps_at_last_entry(self) -> None:
        """Verify that potential_score does not fall below the last ATTEMPT_POINTS entry."""
        assert _make(wrong=100).potential_score == ATTEMPT_POINTS[-1]

    def test_custom_max_guesses(self) -> None:
        """Verify that a custom max_guesses value is respected by guesses_remaining and is_over."""
        rs = _make(wrong=2, max_guesses=3)
        assert rs.guesses_remaining == 1
        assert not rs.is_over


class TestRoundStateSubmitGuess:
    def test_correct_guess_returns_true(self) -> None:
        """Verify that submit_guess returns True for the correct file."""
        assert _make().submit_guess("target.py") is True

    def test_correct_guess_sets_correct_and_points(self) -> None:
        """Verify that a correct guess sets correct to True and awards points."""
        rs = _make()
        rs.submit_guess("target.py")
        assert rs.correct is True
        assert rs.points_earned == ATTEMPT_POINTS[0]

    def test_correct_guess_after_wrongs_earns_fewer_points(self) -> None:
        """Verify that points earned decrease when prior wrong guesses were made."""
        rs = _make(wrong=2)
        rs.submit_guess("target.py")
        assert rs.points_earned == ATTEMPT_POINTS[2]

    def test_wrong_guess_returns_false(self) -> None:
        """Verify that submit_guess returns False for an incorrect file."""
        assert _make().submit_guess("other.py") is False

    def test_wrong_guess_appends_to_list(self) -> None:
        """Verify that a wrong guess is appended to wrong_guesses and increments num_wrong."""
        rs = _make()
        rs.submit_guess("other.py")
        assert "other.py" in rs.wrong_guesses
        assert rs.num_wrong == 1

    def test_zero_points_for_wrong_guess(self) -> None:
        """Verify that a wrong guess does not award any points."""
        rs = _make()
        rs.submit_guess("other.py")
        assert rs.points_earned == 0


class TestRoundStateCodeDisplay:
    def test_stage_minus1_all_lines_obscured(self) -> None:
        """Verify that stage -1 replaces all non-whitespace characters with block characters."""
        rs = _make(wrong=0)  # REVEAL_STAGES[0] = -1
        display = rs.get_code_display(_LINES)
        for line in display.split("\n"):
            assert OBSCURED_RE.match(line), f"Not obscured: {line!r}"

    def test_stage_minus1_preserves_line_count(self) -> None:
        """Verify that stage -1 keeps the same number of lines as the source."""
        rs = _make(wrong=0)
        assert len(rs.get_code_display(_LINES).split("\n")) == len(_LINES)

    def test_stage_0_only_highlight_line_visible(self) -> None:
        """Verify that stage 0 reveals only the highlight line, obscuring its neighbours."""
        hl = 20
        rs = _make(hl=hl, wrong=1)  # REVEAL_STAGES[1] = 0 -> radius 0
        lines = rs.get_code_display(_LINES).split("\n")
        assert lines[hl] == _LINES[hl]
        assert OBSCURED_RE.match(lines[hl - 1])
        assert OBSCURED_RE.match(lines[hl + 1])

    def test_stage_3_reveals_correct_radius(self) -> None:
        """Verify that stage 3 reveals exactly ±3 lines around the highlight line."""
        hl = 20
        rs = _make(hl=hl, wrong=2)  # REVEAL_STAGES[2] = 3
        lines = rs.get_code_display(_LINES).split("\n")
        for i in range(hl - 3, hl + 4):
            assert lines[i] == _LINES[i], f"Line {i} should be visible"
        assert OBSCURED_RE.match(lines[hl - 4])
        assert OBSCURED_RE.match(lines[hl + 4])

    def test_stage_8_reveals_correct_radius(self) -> None:
        """Verify that stage 8 reveals exactly ±8 lines around the highlight line."""
        hl = 30
        rs = _make(hl=hl, wrong=3)  # REVEAL_STAGES[3] = 8
        lines = rs.get_code_display(_LINES).split("\n")
        for i in range(hl - 8, hl + 9):
            assert lines[i] == _LINES[i]
        assert OBSCURED_RE.match(lines[hl - 9])

    def test_stage_none_full_file_visible(self) -> None:
        """Verify that the None stage returns the complete file unchanged."""
        rs = _make(wrong=len(REVEAL_STAGES) - 1)  # REVEAL_STAGES[-1] = None
        assert rs.get_code_display(_LINES) == "\n".join(_LINES)

    def test_reveal_clamps_at_file_start(self) -> None:
        """Verify that a reveal window at the file start is clamped to line 0."""
        rs = _make(hl=0, wrong=2)  # radius 3, clamped to start
        lines = rs.get_code_display(_LINES).split("\n")
        for i in range(4):  # lines 0-3 should be visible
            assert lines[i] == _LINES[i]

    def test_reveal_clamps_at_file_end(self) -> None:
        """Verify that a reveal window at the file end is clamped to the last line."""
        n = len(_LINES)
        rs = _make(hl=n - 1, wrong=2)  # radius 3, clamped to end
        lines = rs.get_code_display(_LINES).split("\n")
        for i in range(n - 4, n):
            assert lines[i] == _LINES[i]
