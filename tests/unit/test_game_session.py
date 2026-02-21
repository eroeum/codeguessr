"""Unit tests for GameSession (creation, properties, payload, submit_guess)."""
import itertools
from pathlib import Path

from codeguessr.game import (
    _EXT_LANG,
    ATTEMPT_POINTS,
    MAX_GUESSES_PER_ROUND,
    GameSession,
    RoundState,
    scan_directory,
)
from tests.helpers import make_file


def _make_session(
    tmp_path: Path,
    num_rounds: int = 2,
    max_guesses: int = MAX_GUESSES_PER_ROUND,
    num_files: int = 5,
) -> GameSession:
    """Create a GameSession backed by temporary Python files.

    Args:
        tmp_path: Temporary directory in which to create source files.
        num_rounds: Number of rounds the session should contain.
        max_guesses: Maximum wrong guesses allowed per round.
        num_files: Number of dummy source files to create.

    Returns:
        A fully initialised GameSession ready for testing.
    """
    for i in range(num_files):
        make_file(tmp_path / f"f{i}.py")
    files = scan_directory(tmp_path)
    return GameSession.create(str(tmp_path), files, num_rounds=num_rounds, max_guesses=max_guesses)


def _wrong_file(session: GameSession) -> str:
    """Return a file from the session that is not the current round's target.

    Args:
        session: An active GameSession whose current round has a target file.

    Returns:
        A relative file path that differs from the current target file.
    """
    return next(f for f in session.files if f != session.current_round.target_file)


class TestGameSessionCreate:
    def test_unique_game_ids(self, tmp_path: Path) -> None:
        """Verify that each GameSession.create call produces a distinct game_id."""
        make_file(tmp_path / "a.py")
        files = scan_directory(tmp_path)
        ids = {GameSession.create(str(tmp_path), files, num_rounds=1).game_id for _ in range(5)}
        assert len(ids) == 5

    def test_num_rounds_controls_round_count(self, tmp_path: Path) -> None:
        """Verify that the num_rounds argument determines the number of rounds created."""
        for i in range(5):
            make_file(tmp_path / f"f{i}.py")
        files = scan_directory(tmp_path)
        session = GameSession.create(str(tmp_path), files, num_rounds=3)
        assert len(session.rounds) == 3

    def test_max_guesses_propagated_to_rounds(self, tmp_path: Path) -> None:
        """Verify that max_guesses is forwarded to each RoundState."""
        make_file(tmp_path / "a.py")
        files = scan_directory(tmp_path)
        session = GameSession.create(str(tmp_path), files, num_rounds=1, max_guesses=2)
        assert session.current_round.max_guesses == 2

    def test_highlight_line_within_file_bounds(self, tmp_path: Path) -> None:
        """Verify that highlight_line is always a valid line index for the target file."""
        make_file(tmp_path / "a.py", num_lines=50)
        files = scan_directory(tmp_path)
        for _ in range(10):
            session = GameSession.create(str(tmp_path), files, num_rounds=1)
            target = session.current_round.target_file
            n = len((Path(tmp_path) / target).read_text().splitlines())
            assert 0 <= session.current_round.highlight_line < n

    def test_target_file_is_from_files_list(self, tmp_path: Path) -> None:
        """Verify that the target file for each round comes from the scanned files list."""
        for i in range(4):
            make_file(tmp_path / f"f{i}.py")
        files = scan_directory(tmp_path)
        session = GameSession.create(str(tmp_path), files, num_rounds=1)
        assert session.current_round.target_file in files

    def test_fewer_files_than_rounds_allowed(self, tmp_path: Path) -> None:
        """Verify that sessions with more rounds than files can still be created."""
        make_file(tmp_path / "only.py")
        files = scan_directory(tmp_path)
        session = GameSession.create(str(tmp_path), files, num_rounds=5)
        assert len(session.rounds) == 5


class TestGameSessionProperties:
    def test_current_round_is_round_state(self, tmp_path: Path) -> None:
        """Verify that current_round returns a RoundState instance."""
        session = _make_session(tmp_path)
        assert isinstance(session.current_round, RoundState)

    def test_not_game_over_at_start(self, tmp_path: Path) -> None:
        """Verify that is_game_over is False at the start of a new session."""
        assert not _make_session(tmp_path).is_game_over

    def test_total_score_zero_at_start(self, tmp_path: Path) -> None:
        """Verify that total_score is zero before any guesses are submitted."""
        assert _make_session(tmp_path).total_score == 0

    def test_total_score_accumulates_across_rounds(self, tmp_path: Path) -> None:
        """Verify that total_score sums points from all completed rounds."""
        session = _make_session(tmp_path, num_rounds=2)
        session.submit_guess(session.current_round.target_file)
        session.submit_guess(session.current_round.target_file)
        assert session.total_score == ATTEMPT_POINTS[0] * 2


class TestRoundPayload:
    def test_payload_has_all_required_keys(self, tmp_path: Path) -> None:
        """Verify that current_round_payload contains every required key."""
        payload = _make_session(tmp_path, num_rounds=1).current_round_payload()
        for key in ("round_num", "code_display", "highlight_line",
                    "potential_score", "guesses_remaining", "wrong_guesses", "language"):
            assert key in payload, f"Missing key: {key}"

    def test_round_num_starts_at_1(self, tmp_path: Path) -> None:
        """Verify that the first round is numbered 1 in the payload."""
        assert _make_session(tmp_path, num_rounds=1).current_round_payload()["round_num"] == 1

    def test_wrong_guesses_initially_empty(self, tmp_path: Path) -> None:
        """Verify that wrong_guesses is an empty list at the start of a round."""
        assert _make_session(tmp_path, num_rounds=1).current_round_payload()["wrong_guesses"] == []

    def test_language_mapping_python(self, tmp_path: Path) -> None:
        """Verify that .py files are mapped to the 'python' language label."""
        make_file(tmp_path / "script.py")
        files = scan_directory(tmp_path)
        session = GameSession.create(str(tmp_path), files, num_rounds=1)
        if session.current_round.target_file.endswith(".py"):
            assert session.current_round_payload()["language"] == "python"

    def test_language_is_a_string(self, tmp_path: Path) -> None:
        """Verify that the language value in the payload is a non-empty string."""
        lang = _make_session(tmp_path, num_rounds=1).current_round_payload()["language"]
        assert isinstance(lang, str) and lang

    def test_ext_lang_map_covers_all_supported_extensions(self) -> None:
        """Verify that _EXT_LANG contains all expected file extensions."""
        expected = {"ts", "js", "py", "go", "rs", "java", "cpp", "cc", "cxx",
                    "c", "h", "rb", "swift", "kt", "cs", "php"}
        assert expected.issubset(_EXT_LANG.keys())


class TestGameSessionSubmitGuess:
    def test_wrong_guess_correct_false(self, tmp_path: Path) -> None:
        """Verify that a wrong guess returns correct=False in the response."""
        session = _make_session(tmp_path)
        assert session.submit_guess(_wrong_file(session))["correct"] is False

    def test_wrong_guess_not_round_over(self, tmp_path: Path) -> None:
        """Verify that a single wrong guess does not end the round."""
        session = _make_session(tmp_path)
        assert session.submit_guess(_wrong_file(session))["round_over"] is False

    def test_wrong_guess_code_display_changes(self, tmp_path: Path) -> None:
        """Verify that code_display changes after a wrong guess reveals more code."""
        session = _make_session(tmp_path)
        before = session.current_round_payload()["code_display"]
        result = session.submit_guess(_wrong_file(session))
        assert result["code_display"] != before

    def test_wrong_guess_tracked_in_response(self, tmp_path: Path) -> None:
        """Verify that the submitted wrong file appears in wrong_guesses of the response."""
        session = _make_session(tmp_path)
        wrong = _wrong_file(session)
        assert wrong in session.submit_guess(wrong)["wrong_guesses"]

    def test_correct_guess_returns_true(self, tmp_path: Path) -> None:
        """Verify that submitting the target file returns correct=True."""
        session = _make_session(tmp_path)
        assert session.submit_guess(session.current_round.target_file)["correct"] is True

    def test_correct_guess_round_over(self, tmp_path: Path) -> None:
        """Verify that a correct guess sets round_over to True in the response."""
        session = _make_session(tmp_path)
        assert session.submit_guess(session.current_round.target_file)["round_over"] is True

    def test_correct_guess_awards_full_points(self, tmp_path: Path) -> None:
        """Verify that a first-attempt correct guess awards the maximum points."""
        session = _make_session(tmp_path)
        result = session.submit_guess(session.current_round.target_file)
        assert result["total_score"] == ATTEMPT_POINTS[0]

    def test_completed_round_in_response(self, tmp_path: Path) -> None:
        """Verify that completed_round in the response contains correct summary fields."""
        session = _make_session(tmp_path)
        result = session.submit_guess(session.current_round.target_file)
        cr = result["completed_round"]
        assert cr["correct"] is True
        assert cr["round_num"] == 1
        assert cr["round_points"] == ATTEMPT_POINTS[0]
        assert "target_file" in cr

    def test_next_round_payload_after_correct(self, tmp_path: Path) -> None:
        """Verify that after a correct guess in round 1 the response advances to round 2."""
        session = _make_session(tmp_path, num_rounds=2)
        result = session.submit_guess(session.current_round.target_file)
        assert result["round_over"] is True
        assert result["game_over"] is False
        assert result["round_num"] == 2

    def test_points_decrease_with_more_wrong_guesses(self, tmp_path: Path) -> None:
        """Verify that points earned decrease as the number of prior wrong guesses increases."""
        scores = []
        for wrong_count in range(4):
            sub = tmp_path / f"run_{wrong_count}"
            sub.mkdir()
            for i in range(6):
                make_file(sub / f"f{i}.py")
            files = scan_directory(sub)
            session = GameSession.create(str(sub), files, num_rounds=1)
            wrong_files = [f for f in files if f != session.current_round.target_file]
            for wf in wrong_files[:wrong_count]:
                session.submit_guess(wf)
            result = session.submit_guess(session.current_round.target_file)
            scores.append(result["total_score"])
        for a, b in itertools.pairwise(scores):
            assert a > b

    def test_exhausting_max_guesses_ends_round(self, tmp_path: Path) -> None:
        """Verify that using all allowed guesses ends the round even without a correct guess."""
        session = _make_session(tmp_path, max_guesses=2)
        wrong_files = [f for f in session.files if f != session.current_round.target_file]
        result = None
        for wf in wrong_files[:2]:
            result = session.submit_guess(wf)
        assert result is not None
        assert result["round_over"] is True
        assert result["correct"] is False

    def test_game_over_after_last_round(self, tmp_path: Path) -> None:
        """Verify that game_over is True after the final round is completed."""
        session = _make_session(tmp_path, num_rounds=2)
        session.submit_guess(session.current_round.target_file)
        result = session.submit_guess(session.current_round.target_file)
        assert result["game_over"] is True

    def test_game_over_includes_all_rounds_summary(self, tmp_path: Path) -> None:
        """Verify that the game-over response includes a summary for every round."""
        session = _make_session(tmp_path, num_rounds=2)
        session.submit_guess(session.current_round.target_file)
        result = session.submit_guess(session.current_round.target_file)
        assert "rounds" in result
        assert len(result["rounds"]) == 2

    def test_rounds_summary_structure(self, tmp_path: Path) -> None:
        """Verify that each entry in the rounds summary contains all required keys."""
        session = _make_session(tmp_path, num_rounds=1)
        result = session.submit_guess(session.current_round.target_file)
        rd = result["rounds"][0]
        for key in ("round_num", "target_file", "correct", "points", "wrong_guesses"):
            assert key in rd, f"Missing key in round summary: {key}"

    def test_no_next_round_payload_on_game_over(self, tmp_path: Path) -> None:
        """Verify that a game-over response does not include a next-round code_display."""
        session = _make_session(tmp_path, num_rounds=1)
        result = session.submit_guess(session.current_round.target_file)
        assert result["game_over"] is True
        assert "code_display" not in result

    def test_already_game_over_returns_game_over(self, tmp_path: Path) -> None:
        """Verify that guessing after the game is over still returns game_over=True."""
        session = _make_session(tmp_path, num_rounds=1)
        session.submit_guess(session.current_round.target_file)
        result = session.submit_guess("anything.py")
        assert result["game_over"] is True
