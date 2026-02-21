"""E2E tests for the Settings page."""
from typing import Any

from tests.e2e.helpers import start_game


class TestSettingsPage:
    def test_settings_page_loads(self, page: Any) -> None:
        """Verify that the settings page loads and displays the SETTINGS heading."""
        page.goto("/")
        page.wait_for_selector("text=SETTINGS", timeout=10_000)

    def test_start_button_present(self, page: Any) -> None:
        """Verify that a Start Game button is visible on the settings page."""
        page.goto("/")
        page.wait_for_selector("text=SETTINGS")
        assert page.locator("button:has-text('Start Game')").count() > 0

    def test_start_game_navigates_to_game(self, page: Any) -> None:
        """Verify that clicking Start Game navigates to the /game route."""
        start_game(page)
        assert "/game" in page.url

    def test_invalid_regex_disables_start_button(self, page: Any) -> None:
        """Verify that an invalid regex in the include-pattern input disables Start Game."""
        page.goto("/")
        page.wait_for_selector("text=SETTINGS")
        page.locator("input[placeholder*='src']").first.fill("[bad regex")
        page.wait_for_timeout(200)
        btn = page.locator("button:has-text('Start Game')")
        assert btn.is_disabled()

    def test_valid_regex_enables_start_button(self, page: Any) -> None:
        """Verify that a valid regex in the include-pattern input keeps Start Game enabled."""
        page.goto("/")
        page.wait_for_selector("text=SETTINGS")
        page.locator("input[placeholder*='src']").first.fill(r"\.py$")
        page.wait_for_timeout(200)
        btn = page.locator("button:has-text('Start Game')")
        assert not btn.is_disabled()

    def test_settings_persisted_to_localstorage(self, page: Any) -> None:
        """Verify that settings entered by the user survive a page navigation via localStorage."""
        page.goto("/")
        page.wait_for_selector("text=SETTINGS")
        rounds_input = page.locator("input[type='number']").first
        rounds_input.fill("3")
        page.goto("/results")
        page.wait_for_timeout(200)
        page.goto("/")
        page.wait_for_selector("text=SETTINGS")
        page.wait_for_timeout(300)
        value = page.locator("input[type='number']").first.input_value()
        assert value == "3"

    def test_statusbar_visible(self, page: Any) -> None:
        """Verify that the status bar element is present on the settings page."""
        page.goto("/")
        page.wait_for_selector(".statusbar")

    def test_breadcrumb_shows_settings(self, page: Any) -> None:
        """Verify that the breadcrumb on the settings page contains the word Settings."""
        page.goto("/")
        page.wait_for_selector("text=Settings")
