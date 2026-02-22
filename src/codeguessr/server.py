"""FastAPI application for CodeGuessr.

Exposes two API endpoints:
  - ``POST /api/game/new``: create a new game session.
  - ``POST /api/game/{game_id}/guess``: submit a file-path guess.

All other routes are handled by a catch-all that serves the Angular SPA.
"""

import os
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from codeguessr.game import (
    MAX_GUESSES_PER_ROUND,
    MIN_LINES,
    NUM_ROUNDS,
    GameSession,
    scan_directory,
)

STATIC_DIR = Path(__file__).parent / "static" / "browser"

_sessions: dict[str, GameSession] = {}
_files: list[str] = []
_root_dir: str = ""


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Scan the code directory on startup and expose the file list globally."""
    global _files, _root_dir
    root = os.environ.get("CODEGUESSR_DIR", "")
    if not root:
        raise RuntimeError("CODEGUESSR_DIR environment variable is not set")
    _root_dir = root
    _files = scan_directory(root)
    if not _files:
        raise RuntimeError(f"No qualifying code files found in {root!r}")
    yield


app = FastAPI(lifespan=lifespan)


# ---------------------------------------------------------------------------
# API routes (must be registered before the SPA catch-all)
# ---------------------------------------------------------------------------


class NewGameRequest(BaseModel):
    """Request body for creating a new game session."""

    num_rounds: int = NUM_ROUNDS
    max_guesses: int = MAX_GUESSES_PER_ROUND
    min_line_chars: int = 1
    min_lines: int = MIN_LINES
    include_pattern: str = ""
    ignore_pattern: str = ""


@app.post("/api/game/new")
async def new_game(body: NewGameRequest | None = None) -> dict[str, Any]:
    """Create a new game session with the given settings.

    Args:
        body: Game configuration (rounds, guesses, file filters, …).

    Returns:
        Initial round payload plus session metadata (``game_id``, ``files``,
        ``total_rounds``, ``max_guesses``).

    Raises:
        HTTPException: 422 if a regex pattern is invalid or no files match.
    """
    if body is None:
        body = NewGameRequest()
    include_pat = body.include_pattern.strip() or None
    ignore_pat = body.ignore_pattern.strip() or None

    for label, pat in (("include_pattern", include_pat), ("ignore_pattern", ignore_pat)):
        if pat:
            try:
                re.compile(pat)
            except re.error as exc:
                raise HTTPException(
                    status_code=422, detail=f"Invalid {label}: {exc}"
                ) from exc

    files = scan_directory(
        _root_dir,
        min_lines=body.min_lines,
        include_pattern=include_pat,
        ignore_pattern=ignore_pat,
    )
    if not files:
        raise HTTPException(
            status_code=422,
            detail="No qualifying files found with the current filter settings.",
        )

    session = GameSession.create(
        _root_dir,
        files,
        num_rounds=body.num_rounds,
        max_guesses=body.max_guesses,
        min_line_chars=body.min_line_chars,
    )
    _sessions[session.game_id] = session

    payload = session.current_round_payload()
    payload["game_id"] = session.game_id
    payload["files"] = session.files
    payload["total_rounds"] = len(session.rounds)
    payload["max_guesses"] = body.max_guesses
    return payload


class GuessRequest(BaseModel):
    """Request body for submitting a file-path guess."""

    file_path: str


@app.post("/api/game/{game_id}/guess")
async def submit_guess(game_id: str, body: GuessRequest) -> dict[str, Any]:
    """Submit a guess for the current round of a game session.

    Args:
        game_id: UUID of the target session.
        body: The guessed file path.

    Returns:
        Updated game state (see ``GameSession.submit_guess``).

    Raises:
        HTTPException: 404 if *game_id* does not refer to a known session.
    """
    session = _sessions.get(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found")
    return session.submit_guess(body.file_path)


# ---------------------------------------------------------------------------
# SPA catch-all (must be registered last)
# ---------------------------------------------------------------------------


@app.get("/{full_path:path}")
async def serve_spa(full_path: str) -> Response:
    """Serve a static file or fall back to index.html for client-side routing."""
    candidate = STATIC_DIR / full_path
    if candidate.is_file():
        return FileResponse(candidate)
    index = STATIC_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Frontend not built. Run `make build`.")
    return FileResponse(index)
