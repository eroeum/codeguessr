build:
	cd client && npm install && npm run build -- --output-path=../src/codeguessr/static

install: build
	pip install -e ".[dev]"

# ── Tests ──────────────────────────────────────────────────────────────────

test:
	pytest tests/unit/ tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v

test-all:
	pytest tests/ -v

# ── Linting ────────────────────────────────────────────────────────────────

lint-py:
	ruff check src/ tests/
	mypy src/

lint-ts:
	cd client && npm run lint

lint: lint-py lint-ts

# ── Distribution ───────────────────────────────────────────────────────────

dist: build
	hatch build -t wheel

publish: dist
	hatch publish
