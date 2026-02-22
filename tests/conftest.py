"""Root pytest fixtures shared across unit and integration tests."""
from pathlib import Path

import pytest

from tests.helpers import make_file  # re-export so fixtures below can use it


@pytest.fixture()
def code_dir(tmp_path: Path) -> Path:
    """Return a temporary directory populated with a realistic spread of code files."""
    (tmp_path / "src").mkdir()
    (tmp_path / "lib").mkdir()
    make_file(tmp_path / "main.py")
    make_file(tmp_path / "utils.py")
    make_file(tmp_path / "src" / "server.ts")
    make_file(tmp_path / "src" / "client.ts")
    make_file(tmp_path / "lib" / "helpers.go")
    return tmp_path
