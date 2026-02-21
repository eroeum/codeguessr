"""Integration tests for full multi-round game flows."""
import itertools
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from codeguessr import server as _srv
from codeguessr.game import ATTEMPT_POINTS
from tests.integration.helpers import non_target, target


class TestFullGameFlow:
    def test_single_round_correct_first_guess(
        self, code_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify a single-round game where the player guesses correctly on the first try."""
        monkeypatch.setenv("CODEGUESSR_DIR", str(code_dir))
        _srv._sessions.clear()
        with TestClient(_srv.app) as c:
            game: dict[str, Any] = c.post("/api/game/new", json={"num_rounds": 1}).json()
            game_id: str = game["game_id"]
            result: dict[str, Any] = c.post(
                f"/api/game/{game_id}/guess", json={"file_path": target(game_id)}
            ).json()
            assert result["correct"] is True
            assert result["game_over"] is True
            assert result["total_score"] == ATTEMPT_POINTS[0]
            assert len(result["rounds"]) == 1

    def test_multi_round_game_all_correct(
        self, code_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify a three-round game where every round is solved correctly on the first guess."""
        monkeypatch.setenv("CODEGUESSR_DIR", str(code_dir))
        _srv._sessions.clear()
        with TestClient(_srv.app) as c:
            num_rounds = 3
            game: dict[str, Any] = c.post("/api/game/new", json={"num_rounds": num_rounds}).json()
            game_id: str = game["game_id"]
            completed = 0
            result: dict[str, Any] | None = None
            while not _srv._sessions[game_id].is_game_over:
                result = c.post(
                    f"/api/game/{game_id}/guess", json={"file_path": target(game_id)}
                ).json()
                if result["round_over"]:
                    completed += 1
            assert completed == num_rounds
            assert result is not None
            assert result["game_over"] is True
            assert len(result["rounds"]) == num_rounds

    def test_wrong_then_correct_scores_less_than_immediate_correct(
        self, code_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify that a wrong guess yields a lower score than an immediate correct guess."""
        monkeypatch.setenv("CODEGUESSR_DIR", str(code_dir))
        _srv._sessions.clear()
        with TestClient(_srv.app) as c:
            # Game A: correct immediately.
            g_a: dict[str, Any] = c.post("/api/game/new", json={"num_rounds": 1}).json()
            r_a: dict[str, Any] = c.post(
                f"/api/game/{g_a['game_id']}/guess",
                json={"file_path": target(g_a["game_id"])},
            ).json()

            # Game B: one wrong guess first.
            g_b: dict[str, Any] = c.post("/api/game/new", json={"num_rounds": 1}).json()
            c.post(
                f"/api/game/{g_b['game_id']}/guess",
                json={"file_path": non_target(g_b["game_id"])},
            )
            r_b: dict[str, Any] = c.post(
                f"/api/game/{g_b['game_id']}/guess",
                json={"file_path": target(g_b["game_id"])},
            ).json()

            assert r_a["total_score"] > r_b["total_score"]

    def test_code_display_reveals_progressively(
        self, code_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify that the code display becomes less obscured with each successive wrong guess."""
        monkeypatch.setenv("CODEGUESSR_DIR", str(code_dir))
        _srv._sessions.clear()
        with TestClient(_srv.app) as c:
            game: dict[str, Any] = c.post("/api/game/new", json={"num_rounds": 1}).json()
            game_id: str = game["game_id"]
            displays: list[str] = [game["code_display"]]
            for _ in range(3):
                if _srv._sessions[game_id].current_round.is_over:
                    break
                result: dict[str, Any] = c.post(
                    f"/api/game/{game_id}/guess", json={"file_path": non_target(game_id)}
                ).json()
                if result.get("round_over"):
                    break
                displays.append(result["code_display"])
            assert len(displays) >= 2
            for a, b in itertools.pairwise(displays):
                assert a != b, "Code display must change after each wrong guess"
