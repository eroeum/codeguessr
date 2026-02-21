"""E2E tests for the Game page — layout and interaction."""
import re
from typing import Any

import pytest

from tests.e2e.helpers import start_game


class TestGamePageLayout:
    def test_code_lines_rendered(self, page: Any) -> None:
        """Verify that at least one .code-line element is rendered in the editor."""
        start_game(page)
        assert page.locator(".code-line").count() > 0

    def test_code_initially_obscured(self, page: Any) -> None:
        """Verify that the initial code display contains block glyphs indicating obscured text."""
        start_game(page)
        content = page.locator(".editor-lines").inner_text()
        assert "\u2588" in content

    def test_file_explorer_rendered(self, page: Any) -> None:
        """Verify that the file explorer panel with the GUESS THE FILE heading is visible."""
        start_game(page)
        assert page.locator("text=GUESS THE FILE").count() > 0

    def test_file_buttons_present(self, page: Any) -> None:
        """Verify that at least one file-row button is present in the file explorer."""
        start_game(page)
        assert page.locator("button.file-row").count() > 0

    def test_tab_bar_shows_rounds(self, page: Any) -> None:
        """Verify that the tab bar contains at least as many tabs as the default round count."""
        start_game(page)
        # Default 5 rounds -> 5 tabs.
        assert page.locator(".tab").count() >= 5

    def test_statusbar_shows_guesses_remaining(self, page: Any) -> None:
        """Verify that the status bar displays a guesses-remaining indicator."""
        start_game(page)
        guesses_text = page.locator(".sb-guesses").inner_text()
        assert "guesses" in guesses_text.lower()

    def test_gutter_line_numbers_shown(self, page: Any) -> None:
        """Verify that line-number gutter elements are rendered alongside the code."""
        start_game(page)
        assert page.locator(".ln").count() > 0

    def test_highlighted_line_has_css_class(self, page: Any) -> None:
        """Verify that exactly one .code-line element carries the highlighted CSS class."""
        start_game(page)
        assert page.locator(".code-line.highlighted").count() == 1


class TestGameInteraction:
    def test_search_filters_file_list(self, page: Any) -> None:
        """Verify that typing in the search box hides files that do not match the query."""
        start_game(page)
        search = page.locator(".sb-search-input")
        search.fill("module_0")
        page.wait_for_timeout(200)
        file_rows = page.locator("button.file-row")
        for i in range(file_rows.count()):
            text = file_rows.nth(i).inner_text()
            assert "module_0" in text.lower()

    def test_clear_button_appears_during_search(self, page: Any) -> None:
        """Verify that a clear button appears in the search bar when a query is entered."""
        start_game(page)
        page.locator(".sb-search-input").fill("mod")
        page.wait_for_timeout(100)
        assert page.locator(".sb-search-clear").count() > 0

    def test_clear_button_clears_search(self, page: Any) -> None:
        """Verify that clicking the clear button resets the search input to empty."""
        start_game(page)
        page.locator(".sb-search-input").fill("mod")
        page.wait_for_timeout(100)
        page.locator(".sb-search-clear").click()
        page.wait_for_timeout(100)
        assert page.locator(".sb-search-input").input_value() == ""

    def test_wrong_guess_marks_file_wrong(self, page: Any) -> None:
        """Verify that a wrong guess adds the .wrong CSS class to the guessed file button."""
        start_game(page)
        file_rows = page.locator("button.file-row:not([disabled])")
        if file_rows.count() == 0:
            pytest.skip("No clickable file buttons")

        initial_wrong = page.locator("button.file-row.wrong").count()
        file_rows.first.click()
        page.wait_for_timeout(600)

        if page.locator(".round-overlay").count() > 0:
            return  # Happened to be correct — nothing to assert here.
        assert page.locator("button.file-row.wrong").count() > initial_wrong

    def test_wrong_guess_reduces_guesses_remaining(self, page: Any) -> None:
        """Verify that a wrong guess decrements the guesses-remaining counter by one."""
        start_game(page)
        before_text = page.locator(".sb-guesses").inner_text()
        before_n = int(re.search(r"\d+", before_text).group())

        file_rows = page.locator("button.file-row:not([disabled])")
        file_rows.first.click()
        page.wait_for_timeout(600)

        if page.locator(".round-overlay").count() > 0:
            pytest.skip("First click happened to be correct")

        after_text = page.locator(".sb-guesses").inner_text()
        after_n = int(re.search(r"\d+", after_text).group())
        assert after_n == before_n - 1

    def test_correct_guess_shows_overlay(self, page: Any) -> None:
        """Verify that guessing the correct file triggers the round-over overlay."""
        start_game(page, include_pattern=r"module_0\.py$")
        file_btn = page.locator("button.file-row")
        assert file_btn.count() == 1, "include_pattern should leave exactly one file"
        file_btn.click()
        page.wait_for_selector(".round-overlay", timeout=5_000)
        assert page.locator("text=Correct!").count() > 0

    def test_correct_guess_shows_points(self, page: Any) -> None:
        """Verify that the round-over overlay displays earned points after a correct guess."""
        start_game(page, include_pattern=r"module_0\.py$")
        page.locator("button.file-row").click()
        page.wait_for_selector(".round-overlay", timeout=5_000)
        pts_text = page.locator(".rp-earned").inner_text()
        assert "+" in pts_text

    def test_next_round_button_dismisses_overlay(self, page: Any) -> None:
        """Verify that clicking Next Round removes the round-over overlay from the page."""
        start_game(page, include_pattern=r"module_0\.py$")
        page.locator("button.file-row").click()
        page.wait_for_selector(".round-overlay", timeout=5_000)

        next_btn = page.locator("button:has-text('Next Round')")
        if next_btn.count() > 0:
            next_btn.click()
            page.wait_for_timeout(500)
            assert page.locator(".round-overlay").count() == 0

    def test_collapse_all_button_collapses_dirs(self, page: Any) -> None:
        """Verify that the Collapse All Folders button hides child file rows."""
        start_game(page)
        dir_rows_before = page.locator(".dir-row").count()
        if dir_rows_before == 0:
            pytest.skip("No directory rows in file tree")
        files_before = page.locator("button.file-row").count()
        page.locator("button[title='Collapse All Folders']").click()
        page.wait_for_timeout(200)
        assert page.locator("button.file-row").count() < files_before

    def test_clicking_directory_toggles_collapse(self, page: Any) -> None:
        """Verify that clicking a directory row toggles its children between visible and hidden."""
        start_game(page)
        dir_rows = page.locator(".dir-row")
        if dir_rows.count() == 0:
            pytest.skip("No directory rows in file tree")
        files_before = page.locator("button.file-row").count()
        dir_rows.first.click()
        page.wait_for_timeout(200)
        files_after = page.locator("button.file-row").count()
        assert files_before != files_after
