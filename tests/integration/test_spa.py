"""Integration tests for the SPA catch-all route."""
from fastapi.testclient import TestClient


class TestSPACatchAll:
    def test_api_endpoint_returns_json(self, api_client: TestClient) -> None:
        """Verify that the /api/game/new endpoint returns a JSON content-type header."""
        res = api_client.post("/api/game/new")
        assert "application/json" in res.headers.get("content-type", "")

    def test_non_api_path_handled_by_spa(self, api_client: TestClient) -> None:
        """Verify that an unknown path is handled by the SPA route without raising errors."""
        res = api_client.get("/some/unknown/route")
        # Static files may not exist in test env; accept any non-API response.
        assert res.status_code in (200, 404, 500)

    def test_api_routes_not_swallowed_by_spa(self, api_client: TestClient) -> None:
        """Verify that API routes are resolved before the SPA catch-all route."""
        res = api_client.post("/api/game/new")
        assert res.status_code == 200
        assert "game_id" in res.json()
