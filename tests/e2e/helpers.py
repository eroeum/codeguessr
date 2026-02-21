"""Shared helpers for e2e Playwright tests."""
from typing import Any


def start_game(page: Any, include_pattern: str = "") -> None:
    """Navigate to the settings page and start a new game.

    Args:
        page: A Playwright Page object pointed at the live server.
        include_pattern: Optional regex to filter files shown in the game.
            If non-empty, it is typed into the include-pattern input before
            clicking Start Game.
    """
    page.goto("/")
    page.wait_for_selector("text=SETTINGS", timeout=10_000)
    if include_pattern:
        inc = page.locator("input[placeholder*='src']").first
        inc.fill(include_pattern)
        page.wait_for_timeout(150)  # let validation settle
    page.click("button:has-text('Start Game')")
    page.wait_for_url("**/game", timeout=10_000)
    page.wait_for_selector(".code-line", timeout=10_000)
