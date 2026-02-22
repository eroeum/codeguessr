"""Shared helpers for integration tests."""
import re

from codeguessr import server as _srv

# Matches a line that contains only block characters and whitespace.
OBSCURED_RE: re.Pattern[str] = re.compile(r"^[\u2588\s]*$")


def target(game_id: str) -> str:
    """Return the current round's target file without spending a guess.

    Args:
        game_id: UUID of an active game session.

    Returns:
        Relative path of the file the player must identify.
    """
    return _srv._sessions[game_id].current_round.target_file


def non_target(game_id: str) -> str:
    """Return a file path that is NOT the current round's target.

    Args:
        game_id: UUID of an active game session.

    Returns:
        Relative path of any file other than the current target.
    """
    session = _srv._sessions[game_id]
    return next(f for f in session.files if f != session.current_round.target_file)
