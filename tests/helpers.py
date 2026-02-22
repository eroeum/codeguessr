"""Shared test helper utilities."""
from pathlib import Path


def make_file(path: Path, num_lines: int = 25) -> Path:
    """Write a Python source file with exactly *num_lines* lines of code.

    Args:
        path: Destination file path (parent directories are created).
        num_lines: Number of function-definition lines to write.

    Returns:
        The path that was written.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            f"def func_{i}(x, y): return x + y + {i}"
            for i in range(num_lines)
        ),
        encoding="utf-8",
    )
    return path
