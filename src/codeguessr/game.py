"""Core game logic for CodeGuessr.

Provides directory scanning, game session management, and round-level
state tracking including code reveal and scoring.
"""

import os
import random
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Self

import pathspec

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INCLUDE_EXTENSIONS: frozenset[str] = frozenset({
    ".py", ".js", ".ts", ".go", ".rs", ".java", ".cpp", ".c",
    ".rb", ".swift", ".kt", ".cs", ".php",
})

PRUNE_DIRS: frozenset[str] = frozenset({
    "node_modules", ".git", "__pycache__", "dist", "build", "venv", ".venv",
})

MIN_LINES: int = 10
NUM_ROUNDS: int = 5
MAX_GUESSES_PER_ROUND: int = 6

# Maps file extension (without dot) to a highlight.js language name.
_EXT_LANG: dict[str, str] = {
    "ts": "typescript", "js": "javascript", "py": "python",
    "go": "go", "rs": "rust", "java": "java",
    "cpp": "cpp", "cc": "cpp", "cxx": "cpp",
    "c": "c", "h": "c", "rb": "ruby",
    "swift": "swift", "kt": "kotlin", "cs": "csharp", "php": "php",
}

# Points awarded for a correct guess with 0, 1, 2, … wrong guesses this round.
ATTEMPT_POINTS: list[int] = [1000, 800, 600, 400, 200, 100]

# Reveal radius around highlight_line, indexed by wrong-guess count.
# -1   → full file, all characters obscured.
# None → full file, all characters visible.
# int  → reveal ±N lines around the highlighted line.
REVEAL_STAGES: list[int | None] = [-1, 0, 3, 8, 15, None]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_gitignore_spec(dirpath: Path) -> pathspec.PathSpec | None:
    """Load a PathSpec from the .gitignore file in *dirpath*, if present.

    Args:
        dirpath: Directory to search for a .gitignore file.

    Returns:
        A ``PathSpec`` matching the .gitignore patterns, or ``None`` if no
        .gitignore exists or the file cannot be read.
    """
    gitignore = dirpath / ".gitignore"
    if not gitignore.is_file():
        return None
    try:
        lines = gitignore.read_text(encoding="utf-8", errors="ignore").splitlines()
        return pathspec.PathSpec.from_lines("gitwildmatch", lines)
    except OSError:
        return None


def _obscure(line: str) -> str:
    """Replace every non-whitespace character in *line* with U+2588 FULL BLOCK."""
    return re.sub(r"\S", "\u2588", line)


def _pick_highlight(lines: list[str], min_chars: int = 1) -> int:
    """Return a 0-based line index suitable for use as the highlighted hint.

    Prefers lines in the middle 80 % of the file that have at least
    *min_chars* non-whitespace characters.  Falls back progressively to any
    non-empty line, then to any line at all.

    Args:
        lines: All lines of the source file.
        min_chars: Minimum number of non-whitespace characters required.

    Returns:
        A randomly chosen 0-based line index.
    """
    count = len(lines)
    low = int(count * 0.1)
    high = int(count * 0.9)
    if low >= high:
        low, high = 0, count - 1

    candidates = [
        idx for idx in range(low, high + 1)
        if len(lines[idx].strip()) >= min_chars
    ]
    if not candidates:
        candidates = [idx for idx in range(count) if lines[idx].strip()]
    if not candidates:
        candidates = list(range(count))
    return random.choice(candidates)


# ---------------------------------------------------------------------------
# Directory scanner
# ---------------------------------------------------------------------------


def scan_directory(
    root: str | os.PathLike[str],
    min_lines: int = MIN_LINES,
    include_pattern: str | None = None,
    ignore_pattern: str | None = None,
) -> list[str]:
    """Return a sorted list of relative paths to qualifying code files under *root*.

    Eligible files must:
    - Have a supported extension (see ``INCLUDE_EXTENSIONS``).
    - Not be a minified JS bundle (``*.min.js``).
    - Match *include_pattern* if one is given.
    - Not match *ignore_pattern* if one is given.
    - Have at least *min_lines* non-empty lines.
    - Not be located inside a pruned or gitignored directory.

    Args:
        root: Root directory to scan recursively.
        min_lines: Minimum number of lines required in each file.
        include_pattern: Optional compiled-safe regex; only matching paths
            are included.  The pattern is matched against the forward-slash
            relative path.
        ignore_pattern: Optional compiled-safe regex; matching paths are
            excluded.

    Returns:
        Sorted list of forward-slash relative file paths.
    """
    root_path = Path(root)

    # gitignore spec cache: absolute directory path → PathSpec | None.
    _gi_cache: dict[Path, pathspec.PathSpec | None] = {}

    def _get_spec(dirpath: Path) -> pathspec.PathSpec | None:
        if dirpath not in _gi_cache:
            _gi_cache[dirpath] = _load_gitignore_spec(dirpath)
        return _gi_cache[dirpath]

    def _is_gitignored(rel: str, is_dir: bool = False) -> bool:
        """Return True if *rel* is matched by any ancestor .gitignore."""
        parts = rel.split("/")
        cur = root_path
        for idx, part in enumerate(parts):
            spec = _get_spec(cur)
            if spec is not None:
                sub = "/".join(parts[idx:])
                if spec.match_file(sub + "/" if is_dir else sub):
                    return True
            if idx < len(parts) - 1:
                cur = cur / part
        return False

    result: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        cur = Path(dirpath)

        # Prune hard-coded directories and hidden directories.
        dirnames[:] = [
            name for name in dirnames
            if name not in PRUNE_DIRS and not name.startswith(".")
        ]
        # Prune gitignored directories so we never descend into them.
        dirnames[:] = [
            name for name in dirnames
            if not _is_gitignored(
                str((cur / name).relative_to(root_path)).replace("\\", "/"),
                is_dir=True,
            )
        ]

        for filename in filenames:
            filepath = cur / filename
            rel = str(filepath.relative_to(root_path)).replace("\\", "/")

            if _is_gitignored(rel):
                continue
            if filepath.suffix.lower() not in INCLUDE_EXTENSIONS:
                continue
            if re.search(r"\.min\.js$", filename, re.IGNORECASE):
                continue
            if include_pattern and not re.search(include_pattern, rel):
                continue
            if ignore_pattern and re.search(ignore_pattern, rel):
                continue

            try:
                lines = filepath.read_text(
                    encoding="utf-8", errors="ignore"
                ).splitlines()
            except OSError:
                continue

            if len(lines) < min_lines:
                continue

            result.append(rel)

    return sorted(result)


# ---------------------------------------------------------------------------
# Game data classes
# ---------------------------------------------------------------------------


@dataclass
class RoundState:
    """Mutable state for a single guess-the-file round.

    Attributes:
        target_file: Relative path of the file the player must identify.
        highlight_line: 0-based index of the line used for the reveal hint.
        max_guesses: Maximum wrong guesses allowed before the round ends.
        wrong_guesses: Ordered list of incorrect file paths guessed so far.
        correct: Whether the player correctly identified the file.
        points_earned: Points awarded when the round was won (0 if not yet won).
    """

    target_file: str
    highlight_line: int
    max_guesses: int = MAX_GUESSES_PER_ROUND
    wrong_guesses: list[str] = field(default_factory=list)
    correct: bool = False
    points_earned: int = 0

    @property
    def num_wrong(self) -> int:
        """Number of incorrect guesses made so far."""
        return len(self.wrong_guesses)

    @property
    def is_over(self) -> bool:
        """True when the round has ended (correct guess or guesses exhausted)."""
        return self.correct or self.num_wrong >= self.max_guesses

    @property
    def guesses_remaining(self) -> int:
        """Number of wrong guesses still available."""
        return self.max_guesses - self.num_wrong

    @property
    def potential_score(self) -> int:
        """Points that would be awarded for a correct guess right now."""
        return ATTEMPT_POINTS[min(self.num_wrong, len(ATTEMPT_POINTS) - 1)]

    def get_code_display(self, lines: list[str]) -> str:
        """Return the (partially) obscured code display for the current reveal stage.

        The amount of revealed code grows with each wrong guess according to
        ``REVEAL_STAGES``.

        Args:
            lines: Raw source lines for the target file.

        Returns:
            Newline-joined string with non-revealed lines replaced by block
            characters (U+2588).
        """
        stage = REVEAL_STAGES[min(self.num_wrong, len(REVEAL_STAGES) - 1)]

        if stage == -1:
            return "\n".join(_obscure(line) for line in lines)

        if stage is None:
            return "\n".join(lines)

        assert isinstance(stage, int)
        revealed = set(range(
            max(0, self.highlight_line - stage),
            min(len(lines), self.highlight_line + stage + 1),
        ))
        return "\n".join(
            line if idx in revealed else _obscure(line)
            for idx, line in enumerate(lines)
        )

    def submit_guess(self, file_path: str) -> bool:
        """Record a guess and update round state in place.

        Args:
            file_path: Relative path guessed by the player.

        Returns:
            ``True`` if the guess was correct, ``False`` otherwise.
        """
        if file_path == self.target_file:
            self.correct = True
            self.points_earned = self.potential_score
            return True
        self.wrong_guesses.append(file_path)
        return False


@dataclass
class GameSession:
    """A multi-round CodeGuessr game session.

    Attributes:
        game_id: UUID string uniquely identifying this session.
        root_dir: Absolute path to the scanned code directory.
        files: Sorted list of all eligible relative file paths in the session.
        rounds: Ordered list of round states for this game.
        current_round_idx: Index into *rounds* for the round currently in play.
    """

    game_id: str
    root_dir: str
    files: list[str]
    rounds: list[RoundState]
    current_round_idx: int = 0

    @classmethod
    def create(
        cls,
        root_dir: str,
        files: list[str],
        num_rounds: int = NUM_ROUNDS,
        max_guesses: int = MAX_GUESSES_PER_ROUND,
        min_line_chars: int = 1,
    ) -> Self:
        """Create a new session by sampling target files and selecting highlight lines.

        Args:
            root_dir: Absolute path to the directory that was scanned.
            files: All eligible relative file paths (from ``scan_directory``).
            num_rounds: Number of rounds in this game.
            max_guesses: Maximum wrong guesses allowed per round.
            min_line_chars: Minimum non-whitespace characters required in the
                highlighted line.

        Returns:
            A freshly initialised ``GameSession``.
        """
        if len(files) >= num_rounds:
            targets = random.sample(files, num_rounds)
        else:
            targets = random.choices(files, k=num_rounds)

        rounds: list[RoundState] = []
        for target in targets:
            lines = (
                (Path(root_dir) / target)
                .read_text(encoding="utf-8", errors="ignore")
                .splitlines()
            )
            rounds.append(RoundState(
                target_file=target,
                highlight_line=_pick_highlight(lines, min_chars=min_line_chars),
                max_guesses=max_guesses,
            ))

        return cls(
            game_id=str(uuid.uuid4()),
            root_dir=root_dir,
            files=files,
            rounds=rounds,
        )

    @property
    def current_round(self) -> RoundState:
        """The round currently in play."""
        return self.rounds[self.current_round_idx]

    @property
    def is_game_over(self) -> bool:
        """True when all rounds have been completed."""
        return self.current_round_idx >= len(self.rounds)

    @property
    def total_score(self) -> int:
        """Sum of points earned across all completed rounds."""
        return sum(rnd.points_earned for rnd in self.rounds)

    def _read_lines(self, target: str) -> list[str]:
        return (
            (Path(self.root_dir) / target)
            .read_text(encoding="utf-8", errors="ignore")
            .splitlines()
        )

    def current_round_payload(self) -> dict[str, Any]:
        """Build the API payload describing the current round's display state.

        Returns:
            Dictionary containing round number, code display, highlight line,
            scoring info, wrong guesses, and language identifier.
        """
        rnd = self.current_round
        ext = Path(rnd.target_file).suffix.lstrip(".")
        language = _EXT_LANG.get(ext, "plaintext")
        return {
            "round_num": self.current_round_idx + 1,
            "code_display": rnd.get_code_display(self._read_lines(rnd.target_file)),
            "highlight_line": rnd.highlight_line,
            "potential_score": rnd.potential_score,
            "guesses_remaining": rnd.guesses_remaining,
            "wrong_guesses": list(rnd.wrong_guesses),
            "language": language,
        }

    def submit_guess(self, file_path: str) -> dict[str, Any]:
        """Process a player guess and return the updated game state.

        Args:
            file_path: Relative path the player guessed.

        Returns:
            Dictionary with at minimum ``correct``, ``round_over``,
            ``game_over``, and ``total_score`` keys, plus additional round
            or game-over data as applicable.
        """
        if self.is_game_over:
            return {
                "game_over": True,
                "round_over": True,
                "correct": False,
                "total_score": self.total_score,
            }

        round_ = self.current_round
        completed_idx = self.current_round_idx
        correct = round_.submit_guess(file_path)
        round_over = round_.is_over

        game_over = False
        if round_over:
            self.current_round_idx += 1
            game_over = self.current_round_idx >= len(self.rounds)

        response: dict[str, Any] = {
            "correct": correct,
            "round_over": round_over,
            "game_over": game_over,
            "total_score": self.total_score,
        }

        if round_over:
            response["completed_round"] = {
                "round_num": completed_idx + 1,
                "target_file": round_.target_file,
                "round_points": round_.points_earned,
                "wrong_guesses": list(round_.wrong_guesses),
                "correct": round_.correct,
            }

        if round_over and game_over:
            response["rounds"] = [
                {
                    "round_num": idx + 1,
                    "target_file": rnd.target_file,
                    "correct": rnd.correct,
                    "points": rnd.points_earned,
                    "wrong_guesses": list(rnd.wrong_guesses),
                }
                for idx, rnd in enumerate(self.rounds)
            ]
        else:
            # Either the same round continues with an updated reveal, or the
            # next round's initial payload is included.
            response.update(self.current_round_payload())

        return response
