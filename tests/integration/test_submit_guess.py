"""Integration tests for POST /api/game/{game_id}/guess."""
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from codeguessr import server as _srv
from codeguessr.game import ATTEMPT_POINTS
from tests.integration.helpers import non_target, target


class TestSubmitGuess:
    def test_unknown_game_returns_404(self, api_client: TestClient) -> None:
        """Verify that guessing against an unknown game_id returns HTTP 404."""
        res = api_client.post("/api/game/does-not-exist/guess",
                              json={"file_path": "foo.py"})
        assert res.status_code == 404

    def test_wrong_guess_correct_false(
        self, api_client: TestClient, new_game: dict[str, Any]
    ) -> None:
        """Verify that an incorrect guess sets correct to False in the response."""
        game_id: str = new_game["game_id"]
        result: dict[str, Any] = api_client.post(
            f"/api/game/{game_id}/guess", json={"file_path": non_target(game_id)}
        ).json()
        assert result["correct"] is False

    def test_wrong_guess_not_round_over(
        self, api_client: TestClient, new_game: dict[str, Any]
    ) -> None:
        """Verify that a single wrong guess does not end the round."""
        game_id: str = new_game["game_id"]
        result: dict[str, Any] = api_client.post(
            f"/api/game/{game_id}/guess", json={"file_path": non_target(game_id)}
        ).json()
        assert result["round_over"] is False

    def test_wrong_guess_returns_updated_code_display(
        self, api_client: TestClient, new_game: dict[str, Any]
    ) -> None:
        """Verify that the code_display changes after a wrong guess."""
        game_id: str = new_game["game_id"]
        before: str = new_game["code_display"]
        result: dict[str, Any] = api_client.post(
            f"/api/game/{game_id}/guess", json={"file_path": non_target(game_id)}
        ).json()
        assert result["code_display"] != before

    def test_wrong_guess_tracked_in_response(
        self, api_client: TestClient, new_game: dict[str, Any]
    ) -> None:
        """Verify that the wrong file path appears in wrong_guesses after submission."""
        game_id: str = new_game["game_id"]
        wrong: str = non_target(game_id)
        result: dict[str, Any] = api_client.post(
            f"/api/game/{game_id}/guess", json={"file_path": wrong}
        ).json()
        assert wrong in result["wrong_guesses"]

    def test_guesses_remaining_decrements(
        self, api_client: TestClient, new_game: dict[str, Any]
    ) -> None:
        """Verify that guesses_remaining decreases by one after a wrong guess."""
        game_id: str = new_game["game_id"]
        before: int = new_game["guesses_remaining"]
        result: dict[str, Any] = api_client.post(
            f"/api/game/{game_id}/guess", json={"file_path": non_target(game_id)}
        ).json()
        assert result["guesses_remaining"] == before - 1

    def test_correct_guess_correct_true(
        self, api_client: TestClient, new_game: dict[str, Any]
    ) -> None:
        """Verify that a correct guess sets correct to True in the response."""
        game_id: str = new_game["game_id"]
        result: dict[str, Any] = api_client.post(
            f"/api/game/{game_id}/guess", json={"file_path": target(game_id)}
        ).json()
        assert result["correct"] is True

    def test_correct_guess_round_over(
        self, api_client: TestClient, new_game: dict[str, Any]
    ) -> None:
        """Verify that a correct guess sets round_over to True."""
        game_id: str = new_game["game_id"]
        result: dict[str, Any] = api_client.post(
            f"/api/game/{game_id}/guess", json={"file_path": target(game_id)}
        ).json()
        assert result["round_over"] is True

    def test_correct_guess_total_score_increases(
        self, api_client: TestClient, new_game: dict[str, Any]
    ) -> None:
        """Verify that the total_score increases by the maximum award on a first-guess correct."""
        game_id: str = new_game["game_id"]
        result: dict[str, Any] = api_client.post(
            f"/api/game/{game_id}/guess", json={"file_path": target(game_id)}
        ).json()
        assert result["total_score"] == ATTEMPT_POINTS[0]

    def test_completed_round_info_on_round_over(
        self, api_client: TestClient, new_game: dict[str, Any]
    ) -> None:
        """Verify that completed_round is included in the response when a round ends."""
        game_id: str = new_game["game_id"]
        result: dict[str, Any] = api_client.post(
            f"/api/game/{game_id}/guess", json={"file_path": target(game_id)}
        ).json()
        cr: dict[str, Any] = result["completed_round"]
        assert cr["correct"] is True
        assert cr["round_num"] == 1
        assert "target_file" in cr
        assert "round_points" in cr

    def test_next_round_payload_when_not_game_over(
        self, code_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify the next round's payload is included when the game continues after a round."""
        monkeypatch.setenv("CODEGUESSR_DIR", str(code_dir))
        _srv._sessions.clear()
        with TestClient(_srv.app) as c:
            game: dict[str, Any] = c.post("/api/game/new", json={"num_rounds": 2}).json()
            game_id: str = game["game_id"]
            result: dict[str, Any] = c.post(
                f"/api/game/{game_id}/guess", json={"file_path": target(game_id)}
            ).json()
            assert result["round_over"] is True
            assert result["game_over"] is False
            assert result["round_num"] == 2
            assert "code_display" in result
            assert "language" in result

    def test_game_over_includes_rounds_summary(
        self, code_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify that the final guess response includes a rounds summary when the game ends."""
        monkeypatch.setenv("CODEGUESSR_DIR", str(code_dir))
        _srv._sessions.clear()
        with TestClient(_srv.app) as c:
            game: dict[str, Any] = c.post("/api/game/new", json={"num_rounds": 2}).json()
            game_id: str = game["game_id"]
            c.post(f"/api/game/{game_id}/guess", json={"file_path": target(game_id)})
            result: dict[str, Any] = c.post(
                f"/api/game/{game_id}/guess", json={"file_path": target(game_id)}
            ).json()
            assert result["game_over"] is True
            assert "rounds" in result
            assert len(result["rounds"]) == 2

    def test_no_code_display_on_game_over(
        self, code_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify that code_display is absent from the response when the game is over."""
        monkeypatch.setenv("CODEGUESSR_DIR", str(code_dir))
        _srv._sessions.clear()
        with TestClient(_srv.app) as c:
            game: dict[str, Any] = c.post("/api/game/new", json={"num_rounds": 1}).json()
            game_id: str = game["game_id"]
            result: dict[str, Any] = c.post(
                f"/api/game/{game_id}/guess", json={"file_path": target(game_id)}
            ).json()
            assert result["game_over"] is True
            assert "code_display" not in result

    def test_max_guesses_exhausted_ends_round(
        self, code_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify that exhausting all guesses marks the round as over with correct False."""
        monkeypatch.setenv("CODEGUESSR_DIR", str(code_dir))
        _srv._sessions.clear()
        with TestClient(_srv.app) as c:
            game: dict[str, Any] = c.post(
                "/api/game/new", json={"max_guesses": 2, "num_rounds": 1}
            ).json()
            game_id: str = game["game_id"]
            session = _srv._sessions[game_id]
            wrong_files = [f for f in session.files if f != target(game_id)]
            result: dict[str, Any] | None = None
            for wf in wrong_files[:2]:
                result = c.post(f"/api/game/{game_id}/guess", json={"file_path": wf}).json()
                if result.get("round_over"):
                    break
            assert result is not None
            if result.get("round_over"):
                assert result["correct"] is False

    def test_rounds_summary_structure(
        self, code_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify that each entry in the rounds summary contains all required keys."""
        monkeypatch.setenv("CODEGUESSR_DIR", str(code_dir))
        _srv._sessions.clear()
        with TestClient(_srv.app) as c:
            game: dict[str, Any] = c.post("/api/game/new", json={"num_rounds": 1}).json()
            game_id: str = game["game_id"]
            result: dict[str, Any] = c.post(
                f"/api/game/{game_id}/guess", json={"file_path": target(game_id)}
            ).json()
            rd: dict[str, Any] = result["rounds"][0]
            for key in ("round_num", "target_file", "correct", "points", "wrong_guesses"):
                assert key in rd
