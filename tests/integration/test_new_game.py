"""Integration tests for POST /api/game/new."""
from typing import Any

from fastapi.testclient import TestClient

from codeguessr import server as _srv
from codeguessr.game import ATTEMPT_POINTS
from tests.integration.helpers import OBSCURED_RE


class TestNewGame:
    def test_returns_200(self, api_client: TestClient) -> None:
        """Verify that a default new-game request returns HTTP 200."""
        assert api_client.post("/api/game/new").status_code == 200

    def test_response_has_all_required_fields(self, api_client: TestClient) -> None:
        """Verify that the response contains every expected top-level field."""
        data: dict[str, Any] = api_client.post("/api/game/new").json()
        for key in ("game_id", "files", "total_rounds", "max_guesses",
                    "round_num", "code_display", "highlight_line",
                    "potential_score", "guesses_remaining", "wrong_guesses",
                    "language"):
            assert key in data, f"Missing field: {key}"

    def test_game_id_is_unique_per_call(self, api_client: TestClient) -> None:
        """Verify that each new-game call produces a distinct game_id."""
        ids = {api_client.post("/api/game/new").json()["game_id"] for _ in range(5)}
        assert len(ids) == 5

    def test_round_num_starts_at_1(self, api_client: TestClient) -> None:
        """Verify that the first round is numbered 1."""
        assert api_client.post("/api/game/new").json()["round_num"] == 1

    def test_wrong_guesses_initially_empty(self, api_client: TestClient) -> None:
        """Verify that no wrong guesses are recorded at the start of a game."""
        assert api_client.post("/api/game/new").json()["wrong_guesses"] == []

    def test_initial_code_display_fully_obscured(self, api_client: TestClient) -> None:
        """Verify that every line of the initial code display is fully obscured."""
        code: str = api_client.post("/api/game/new").json()["code_display"]
        for line in code.split("\n"):
            assert OBSCURED_RE.match(line), f"Unobscured line: {line!r}"

    def test_files_list_is_non_empty(self, api_client: TestClient) -> None:
        """Verify that the returned file list contains at least one entry."""
        assert len(api_client.post("/api/game/new").json()["files"]) > 0

    def test_potential_score_starts_at_max(self, api_client: TestClient) -> None:
        """Verify that the initial potential score equals the maximum award."""
        assert api_client.post("/api/game/new").json()["potential_score"] == ATTEMPT_POINTS[0]

    def test_custom_num_rounds(self, api_client: TestClient) -> None:
        """Verify that total_rounds reflects the num_rounds request field."""
        data: dict[str, Any] = api_client.post("/api/game/new", json={"num_rounds": 2}).json()
        assert data["total_rounds"] == 2

    def test_custom_max_guesses_reflected_in_response(self, api_client: TestClient) -> None:
        """Verify that max_guesses and guesses_remaining both reflect the requested limit."""
        data: dict[str, Any] = api_client.post("/api/game/new", json={"max_guesses": 3}).json()
        assert data["max_guesses"] == 3
        assert data["guesses_remaining"] == 3

    def test_include_pattern_filters_file_list(self, api_client: TestClient) -> None:
        """Verify that include_pattern restricts the file list to matching paths."""
        data: dict[str, Any] = api_client.post(
            "/api/game/new", json={"include_pattern": r"\.py$"}
        ).json()
        assert all(f.endswith(".py") for f in data["files"])

    def test_ignore_pattern_removes_files(self, api_client: TestClient) -> None:
        """Verify that ignore_pattern excludes matching paths from the file list."""
        data: dict[str, Any] = api_client.post(
            "/api/game/new", json={"ignore_pattern": r"\.py$"}
        ).json()
        assert not any(f.endswith(".py") for f in data["files"])

    def test_invalid_include_pattern_returns_422(self, api_client: TestClient) -> None:
        """Verify that a malformed include_pattern regex returns HTTP 422."""
        res = api_client.post("/api/game/new", json={"include_pattern": "["})
        assert res.status_code == 422

    def test_invalid_ignore_pattern_returns_422(self, api_client: TestClient) -> None:
        """Verify that a malformed ignore_pattern regex returns HTTP 422."""
        res = api_client.post("/api/game/new", json={"ignore_pattern": ")"})
        assert res.status_code == 422

    def test_no_matching_files_returns_422(self, api_client: TestClient) -> None:
        """Verify that a pattern matching no files returns HTTP 422."""
        res = api_client.post("/api/game/new",
                              json={"include_pattern": "will_never_match_xyz_abc_123"})
        assert res.status_code == 422

    def test_min_lines_filter_too_strict_returns_422(self, api_client: TestClient) -> None:
        """Verify that an impossibly high min_lines requirement returns HTTP 422."""
        # All fixture files have 25 lines; requiring 100 should leave none.
        res = api_client.post("/api/game/new", json={"min_lines": 100})
        assert res.status_code == 422

    def test_session_stored_server_side(self, api_client: TestClient) -> None:
        """Verify that a new game session is persisted in the server-side store."""
        game_id: str = api_client.post("/api/game/new").json()["game_id"]
        assert game_id in _srv._sessions

    def test_language_field_is_non_empty_string(self, api_client: TestClient) -> None:
        """Verify that the language field is a non-empty string."""
        lang: str = api_client.post("/api/game/new").json()["language"]
        assert isinstance(lang, str) and lang

    def test_guesses_remaining_equals_max_guesses(self, api_client: TestClient) -> None:
        """Verify that guesses_remaining equals max_guesses at the start of a round."""
        data: dict[str, Any] = api_client.post("/api/game/new", json={"max_guesses": 4}).json()
        assert data["guesses_remaining"] == data["max_guesses"]
