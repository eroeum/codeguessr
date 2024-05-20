"""Utilities to help with file searching."""
import os
from typing import Final, Iterable, List, NamedTuple

import git
import git.exc


GIT_PATITION_SIZE: Final[int] = 100
"""Git commands fail if the file list is too long."""


def get_files(path: str) -> List[str]:
    """Gets files in the provided path.
    
    Args:
        path: Path to fetch files for.

    Returns:
        Determined files.
    """
    if is_git_repo(path):
        return _get_files_git(path)
    return _get_files(path)


def is_git_repo(path: str) -> bool:
    """Detects if the provided path is a git repository.
    
    Args:
        path: Path to check.

    Returns:
        True if the provided path is a git repository and false otherwise.
    """
    try:
        with git.Repo(path, search_parent_directories=True) as repo:
            _ = repo.git_dir
        return True
    except git.exc.InvalidGitRepositoryError:
        return False


def _get_files_git(path: str) -> List[str]:
    """Provides files for git repos."""
    files = _get_files(path)
    with git.Repo(path, search_parent_directories=True) as repo:
        ignored: List[str] = []
        for file in _partition(files, GIT_PATITION_SIZE):
            ignored.extend(repo.ignored(file))

    return [file for file in files if file not in ignored]

def _get_files(path: str) -> List[str]:
    """Provides all files."""
    files = []
    for root, _, filenames in os.walk(path):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files


def _partition(lst: list, size: int) -> Iterable:
    for item in range(0, len(lst) // size):
        yield lst[item :: size]
