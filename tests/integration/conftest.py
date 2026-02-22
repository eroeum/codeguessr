"""Fixtures for integration tests."""
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from codeguessr import server as _srv


@pytest.fixture()
def api_client(
    code_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[TestClient, None, None]:
    """Return a FastAPI TestClient with CODEGUESSR_DIR pointing at code_dir.

    Args:
        code_dir: Temporary directory pre-populated with code files.
        monkeypatch: pytest monkeypatch fixture for environment variable injection.

    Yields:
        A running TestClient instance scoped to the test.
    """
    monkeypatch.setenv("CODEGUESSR_DIR", str(code_dir))
    _srv._sessions.clear()
    with TestClient(_srv.app) as client:
        yield client


@pytest.fixture()
def new_game(api_client: TestClient) -> dict[str, Any]:
    """Return the JSON response body for a freshly created game session.

    Args:
        api_client: A running TestClient pointed at a populated code directory.

    Returns:
        Parsed JSON payload from POST /api/game/new.
    """
    res = api_client.post("/api/game/new")
    assert res.status_code == 200
    return res.json()  # type: ignore[no-any-return]
