"""Fixtures for e2e Playwright tests.

Tests are skipped automatically when either:
- ``playwright`` is not installed  (pip install playwright && playwright install chromium)
- the Angular frontend has not been built  (make build)
"""
import os
import threading
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from tests.helpers import make_file

_STATIC_INDEX: Path = (
    Path(__file__).parent.parent.parent
    / "src" / "codeguessr" / "static" / "browser" / "index.html"
)
_E2E_PORT: int = 19876


@pytest.fixture(scope="session")
def live_server_url(tmp_path_factory: pytest.TempPathFactory) -> Generator[str, None, None]:
    """Start a live uvicorn process and yield its base URL.

    Automatically skipped when playwright is not installed or the Angular
    frontend has not been built with ``make build``.

    Args:
        tmp_path_factory: pytest factory for session-scoped temporary paths.

    Yields:
        Base URL string, e.g. ``"http://127.0.0.1:19876"``.
    """
    try:
        import playwright  # noqa: F401
    except ImportError:
        pytest.skip(
            "playwright not installed — run: pip install playwright && playwright install chromium"
        )

    if not _STATIC_INDEX.exists():
        pytest.skip("Angular frontend not built — run: make build")

    import httpx
    import uvicorn

    root = tmp_path_factory.mktemp("e2e_project")
    (root / "src").mkdir()
    for i in range(4):
        make_file(root / f"module_{i}.py")
    for i in range(4, 6):
        make_file(root / "src" / f"module_{i}.py")

    previous_dir: str | None = os.environ.get("CODEGUESSR_DIR")
    os.environ["CODEGUESSR_DIR"] = str(root)

    config = uvicorn.Config(
        "codeguessr.server:app",
        host="127.0.0.1",
        port=_E2E_PORT,
        log_level="error",
    )
    server = uvicorn.Server(config)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    base_url = f"http://127.0.0.1:{_E2E_PORT}"
    for _ in range(60):
        try:
            response = httpx.post(f"{base_url}/api/game/new", timeout=0.5)
            if response.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.1)
    else:
        server.should_exit = True
        pytest.fail("Live server did not start within 6 seconds")

    yield base_url

    server.should_exit = True
    server_thread.join(timeout=5)
    if previous_dir is not None:
        os.environ["CODEGUESSR_DIR"] = previous_dir
    else:
        os.environ.pop("CODEGUESSR_DIR", None)


@pytest.fixture(scope="session")
def browser_instance(live_server_url: str) -> Generator[Any, None, None]:
    """Yield a session-scoped Playwright Chromium browser instance.

    Args:
        live_server_url: Fixture ensuring the live server is running.

    Yields:
        A Playwright ``Browser`` object.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture()
def page(browser_instance: Any, live_server_url: str) -> Generator[Any, None, None]:
    """Yield a fresh Playwright page for each test, then close it.

    Args:
        browser_instance: Session-scoped Chromium browser.
        live_server_url: Base URL for the running server.

    Yields:
        A Playwright ``Page`` object with ``base_url`` set to the live server.
    """
    ctx = browser_instance.new_context(base_url=live_server_url)
    pg = ctx.new_page()
    yield pg
    pg.close()
    ctx.close()
