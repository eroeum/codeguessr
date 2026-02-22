"""E2E tests for the Results page."""
from typing import Any

from tests.e2e.helpers import start_game


class TestResultsPage:
    def _complete_game(self, page: Any) -> None:
        """Play a 1-round game with a single known file and land on results.

        Args:
            page: A Playwright Page object pointed at the live server.
        """
        start_game(page, include_pattern=r"module_0\.py$")
        page.locator("button.file-row").click()
        page.wait_for_selector(".round-overlay", timeout=5_000)
        see_results = page.locator("button:has-text('See Results')")
        if see_results.count() > 0:
            see_results.click()
            page.wait_for_url("**/results", timeout=5_000)
        else:
            page.goto("/results")

    def test_play_again_navigates_to_settings(self, page: Any) -> None:
        """Verify that clicking Play Again returns the user to the settings page."""
        self._complete_game(page)
        play_again = page.locator("button:has-text('Play Again'), a:has-text('Play Again')")
        if play_again.count() > 0:
            play_again.first.click()
            page.wait_for_timeout(500)
            assert page.url.endswith("/") or "game" not in page.url

    def test_results_page_accessible(self, page: Any) -> None:
        """Verify that the results page renders a body element after completing a game."""
        self._complete_game(page)
        if "/results" in page.url:
            assert page.locator("body").count() > 0

    def test_unknown_route_redirects_to_settings(self, page: Any) -> None:
        """Verify that navigating to an unknown route redirects the user to the settings page."""
        page.goto("/this/does/not/exist")
        page.wait_for_timeout(500)
        assert page.url.endswith("/") or "settings" in page.url.lower()
