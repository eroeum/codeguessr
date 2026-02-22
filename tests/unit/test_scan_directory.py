"""Unit tests for scan_directory."""
from pathlib import Path

from codeguessr.game import MIN_LINES, scan_directory
from tests.helpers import make_file


class TestScanDirectory:
    def test_finds_python_file(self, tmp_path: Path) -> None:
        """Verify that a Python file placed in the scanned directory is discovered."""
        make_file(tmp_path / "main.py")
        assert "main.py" in scan_directory(tmp_path)

    def test_result_is_sorted(self, tmp_path: Path) -> None:
        """Verify that the returned file list is sorted lexicographically."""
        for name in ["z.py", "a.py", "m.py"]:
            make_file(tmp_path / name)
        result = scan_directory(tmp_path)
        assert result == sorted(result)

    def test_all_supported_extensions_included(self, tmp_path: Path) -> None:
        """Verify that all thirteen supported file extensions are returned by the scanner."""
        for ext in [".py", ".js", ".ts", ".go", ".rs", ".java", ".cpp", ".c",
                    ".rb", ".swift", ".kt", ".cs", ".php"]:
            make_file(tmp_path / f"file{ext}")
        result = scan_directory(tmp_path)
        assert len(result) == 13

    def test_unsupported_extensions_excluded(self, tmp_path: Path) -> None:
        """Verify that files with unsupported extensions are excluded from results."""
        for name in ["data.json", "config.yaml", "style.css", "readme.md"]:
            (tmp_path / name).write_text("x\n" * 30, encoding="utf-8")
        assert scan_directory(tmp_path) == []

    def test_excludes_node_modules(self, tmp_path: Path) -> None:
        """Verify that files inside node_modules are never included in results."""
        nm = tmp_path / "node_modules"
        nm.mkdir()
        make_file(nm / "lib.js")
        assert not any("node_modules" in p for p in scan_directory(tmp_path))

    def test_excludes_git_dir(self, tmp_path: Path) -> None:
        """Verify that files inside the .git directory are excluded."""
        git = tmp_path / ".git"
        git.mkdir()
        make_file(git / "hook.py")
        assert scan_directory(tmp_path) == []

    def test_excludes_pycache(self, tmp_path: Path) -> None:
        """Verify that files inside __pycache__ directories are excluded."""
        pc = tmp_path / "__pycache__"
        pc.mkdir()
        make_file(pc / "module.py")
        assert scan_directory(tmp_path) == []

    def test_excludes_dist_build_venv(self, tmp_path: Path) -> None:
        """Verify that files inside dist, build, venv, and .venv directories are excluded."""
        for d in ["dist", "build", "venv", ".venv"]:
            subdir = tmp_path / d
            subdir.mkdir()
            make_file(subdir / "output.js")
        assert scan_directory(tmp_path) == []

    def test_excludes_hidden_directories(self, tmp_path: Path) -> None:
        """Verify that files inside dot-prefixed hidden directories are excluded."""
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        make_file(hidden / "secret.py")
        assert scan_directory(tmp_path) == []

    def test_excludes_minified_js(self, tmp_path: Path) -> None:
        """Verify that .min.js files are excluded while plain .js files are retained."""
        make_file(tmp_path / "bundle.min.js")
        make_file(tmp_path / "bundle.js")
        result = scan_directory(tmp_path)
        assert "bundle.js" in result
        assert not any("min.js" in p for p in result)

    def test_min_lines_boundary_included(self, tmp_path: Path) -> None:
        """Verify that a file with exactly MIN_LINES lines is included in results."""
        make_file(tmp_path / "exact.py", num_lines=MIN_LINES)
        assert "exact.py" in scan_directory(tmp_path)

    def test_min_lines_boundary_excluded(self, tmp_path: Path) -> None:
        """Verify that a file with one fewer than MIN_LINES lines is excluded from results."""
        make_file(tmp_path / "short.py", num_lines=MIN_LINES - 1)
        assert scan_directory(tmp_path) == []

    def test_custom_min_lines(self, tmp_path: Path) -> None:
        """Verify that a custom min_lines threshold correctly filters files in and out."""
        make_file(tmp_path / "medium.py", num_lines=15)
        assert scan_directory(tmp_path, min_lines=20) == []
        assert "medium.py" in scan_directory(tmp_path, min_lines=10)

    def test_include_pattern_filters(self, tmp_path: Path) -> None:
        """Verify that include_pattern retains only files whose paths match the pattern."""
        make_file(tmp_path / "auth.py")
        make_file(tmp_path / "utils.py")
        result = scan_directory(tmp_path, include_pattern=r"auth")
        assert "auth.py" in result
        assert "utils.py" not in result

    def test_ignore_pattern_excludes(self, tmp_path: Path) -> None:
        """Verify that ignore_pattern removes matching files from the scan results."""
        make_file(tmp_path / "main.py")
        make_file(tmp_path / "main_test.py")
        result = scan_directory(tmp_path, ignore_pattern=r"_test\.py$")
        assert "main.py" in result
        assert "main_test.py" not in result

    def test_include_and_ignore_combined(self, tmp_path: Path) -> None:
        """Verify that include_pattern and ignore_pattern are applied together correctly."""
        make_file(tmp_path / "src_auth.py")
        make_file(tmp_path / "src_utils.py")
        make_file(tmp_path / "other.py")
        result = scan_directory(
            tmp_path, include_pattern=r"^src_", ignore_pattern=r"utils"
        )
        assert "src_auth.py" in result
        assert "src_utils.py" not in result
        assert "other.py" not in result

    def test_recursive_scan(self, tmp_path: Path) -> None:
        """Verify that files nested in deep subdirectories are discovered by the scanner."""
        subdir = tmp_path / "a" / "b" / "c"
        subdir.mkdir(parents=True)
        make_file(subdir / "deep.py")
        result = scan_directory(tmp_path)
        assert any("deep.py" in p for p in result)

    def test_returns_relative_forward_slash_paths(self, tmp_path: Path) -> None:
        """Verify that all returned paths are relative and use forward slashes."""
        (tmp_path / "src").mkdir()
        make_file(tmp_path / "src" / "main.py")
        result = scan_directory(tmp_path)
        for p in result:
            assert not p.startswith("/")
            assert "\\" not in p
            assert p == "src/main.py"

    def test_respects_gitignore_directory(self, tmp_path: Path) -> None:
        """Verify that a directory listed in .gitignore is excluded from scan results."""
        gen = tmp_path / "generated"
        gen.mkdir()
        make_file(gen / "gen.py")
        make_file(tmp_path / "real.py")
        (tmp_path / ".gitignore").write_text("generated/\n", encoding="utf-8")
        result = scan_directory(tmp_path)
        assert "real.py" in result
        assert not any("generated" in p for p in result)

    def test_respects_gitignore_file_pattern(self, tmp_path: Path) -> None:
        """Verify that a glob pattern in .gitignore excludes matching files."""
        make_file(tmp_path / "prod.py")
        make_file(tmp_path / "prod.test.py")
        (tmp_path / ".gitignore").write_text("*.test.py\n", encoding="utf-8")
        result = scan_directory(tmp_path)
        assert "prod.py" in result
        assert "prod.test.py" not in result

    def test_gitignore_in_subdirectory(self, tmp_path: Path) -> None:
        """Verify that a .gitignore inside a subdirectory excludes files within that subtree."""
        sub = tmp_path / "pkg"
        sub.mkdir()
        make_file(sub / "keep.py")
        make_file(sub / "skip.py")
        (sub / ".gitignore").write_text("skip.py\n", encoding="utf-8")
        result = scan_directory(tmp_path)
        assert "pkg/keep.py" in result
        assert "pkg/skip.py" not in result
