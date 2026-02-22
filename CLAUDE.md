# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Build
```bash
make build          # npm install + ng build → src/codeguessr/static/browser/
pip install -e .    # install package with entry point (requires static/ to exist — make build first)
pip install -e ".[dev]"  # install with dev dependencies (pytest, ruff, mypy, playwright, httpx)
```

### Run
```bash
codeguessr                        # scan cwd, start server at http://localhost:4200
codeguessr --dir /path/to/repo    # scan a specific directory
cd client && npm start            # Angular dev server at :4200, proxies /api → :8000
```

### Test
```bash
make test           # unit + integration (tests/unit/ + tests/integration/)
make test-e2e       # Playwright e2e (requires: make build + playwright install chromium)
make test-all       # all tests

# Run a single test
pytest tests/unit/test_scan_directory.py::TestScanDirectory::test_respects_gitignore_file_pattern -v
pytest tests/integration/test_new_game.py::TestNewGame -v   # whole class
```

### Lint
```bash
make lint           # ruff + mypy + ng lint
make lint-py        # ruff check src/ tests/ && mypy src/
make lint-ts        # cd client && npm run lint
```

## Architecture

### Data flow
1. `cli.py` (Click) sets `CODEGUESSR_DIR`, then starts uvicorn pointing at `server.py`.
2. FastAPI lifespan (`server.py`) calls `scan_directory(root)` at startup; results stored in module-level `_files` and `_root_dir`.
3. `POST /api/game/new` creates a `GameSession` (in-memory `_sessions` dict). Sessions are never evicted.
4. `POST /api/game/{id}/guess` delegates to `GameSession.submit_guess()` which mutates `RoundState` and returns the next payload.
5. All other `GET` routes are caught by `serve_spa()` which serves built Angular assets from `src/codeguessr/static/browser/`. If `index.html` doesn't exist it returns 404.

### Python backend (`src/codeguessr/`)
- **`game.py`** — all game logic; no I/O except file reads. `scan_directory()` walks the tree, respects `.gitignore` via `pathspec`, prunes `PRUNE_DIRS` and hidden dirs. `GameSession.create()` samples target files; `RoundState.get_code_display()` applies the reveal stages.
- **`server.py`** — thin FastAPI layer; holds the three module-level globals (`_sessions`, `_files`, `_root_dir`). API routes **must** be registered before the SPA catch-all route or FastAPI will swallow them.
- **`cli.py`** — Click entry point; passes `--dir` as `CODEGUESSR_DIR` env var to the server.

### Reveal stages (`REVEAL_STAGES` in `game.py`)
Index is `min(num_wrong_guesses, len(REVEAL_STAGES)-1)`:
- `-1` → full file, all characters replaced with █
- `int N` → ±N lines visible around `highlight_line`, rest obscured
- `None` → full file visible

Scoring: `ATTEMPT_POINTS = [1000, 800, 600, 400, 200, 100]` indexed by wrong-guess count.

### Angular frontend (`client/src/app/`)
Standalone components, Angular 17+ control flow (`@if`/`@for`). Routes: `''` → `SettingsComponent`, `'game'` → `GameComponent`, `'results'` → `ResultsComponent`.

- **`game.service.ts`** — all HTTP calls; defines all API response interfaces (`NewGameResponse`, `GuessResponse`, `CompletedRound`, `RoundSummary`). Keep interface definitions here.
- **`game.component.ts`** — main game UI; manages the file-tree (`TreeNode[]`), highlight.js syntax highlighting, and round/game state. Uses `inject()` pattern and `takeUntilDestroyed()` for subscriptions.
- **`results.component.ts`** — reads final score from Angular router navigation state (passed by `GameComponent` on game over).
- **`settings.component.ts`** — configures and launches a new game.

Dev proxy (`client/proxy.conf.json`) forwards `/api/*` to `http://localhost:8000` so `ng serve` works alongside a local uvicorn instance.

### Tests
```
tests/
  helpers.py               # make_file() helper (shared)
  conftest.py              # code_dir fixture (shared)
  unit/                    # tests for game.py internals
    test_obscure.py        # _obscure()
    test_pick_highlight.py # _pick_highlight()
    test_scan_directory.py # scan_directory()
    test_round_state.py    # RoundState properties, submit_guess, get_code_display
    test_game_session.py   # GameSession create/properties/payload/submit_guess
  integration/             # FastAPI TestClient tests
    conftest.py            # api_client, new_game fixtures
    helpers.py             # target(), non_target(), OBSCURED_RE
    test_new_game.py       # POST /api/game/new
    test_submit_guess.py   # POST /api/game/{id}/guess
    test_game_flow.py      # multi-round scenario flows
    test_spa.py            # SPA catch-all route
  e2e/                     # Playwright browser tests
    conftest.py            # live_server_url, browser_instance, page fixtures
    helpers.py             # start_game()
    test_settings_page.py  # settings page
    test_game_page.py      # game layout + interaction
    test_results_page.py   # results page
```
- Integration tests access `_srv._sessions` directly to get the target file without spending a guess.
- E2E tests use a session-scoped uvicorn thread on port 19876; auto-skipped when playwright or built frontend are absent.

### Build & packaging
`make build` outputs to `src/codeguessr/static/` (gitignored except `.gitkeep`). The `.gitkeep` must stay so hatchling's `force-include` doesn't fail on `pip install -e .` before a build. The wheel packages the built static files via `[tool.hatch.build.targets.wheel.force-include]`.

## CI (`.github/workflows/ci.yml`)
`lint` job gates `test` (matrix: Python 3.11/3.12/3.13) and `e2e` jobs. E2E only runs on `push`, not PRs.
