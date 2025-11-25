# Repository Guidelines

## Project Structure & Module Organization
- `backend/`: FastAPI paywalled API (`main.py`), routers under `routers/`, shared helpers in `others/`, static assets in `static/`, and a sample SQLite DB in `data/leases.db`. Vendored `x402/` is referenced as an editable dependency via `pyproject.toml`.
- `frontend-codex/`: Vite + React chat UI calling a local OpenAI-compatible `/chat` endpoint; entry points in `src/App.tsx` and `src/main.tsx`, styles in `src/styles.css`.
- `frontend-python/`: Small Python scripts to exercise AgentKit/CDP/x402 (`agentkit-test.py`, `x402-test.py`, `pydantic-test.py`).

## Build, Test, and Development Commands
- Backend: `cd backend && uv sync` to install, then `uv run python main.py` to start on `:4021`. Uses `.env` (copy from `.example.env`) for `ADDRESS`, `NETWORK`, `CDP_CLIENT_KEY`, etc.
- Frontend (codex): `cd frontend-codex && pnpm install && pnpm dev` for local dev (Vite); `pnpm build` for a production bundle. `VITE_CHAT_API_BASE` points to your chat API (defaults to `http://localhost:8000`).
- Python scripts: `cd frontend-python && uv sync` then `uv run python pydantic-test.py` to run the payment/chat script for frontend
- You need `backend/main.py`, `frontend-python/pydantic-test.py`, `frontend-code` (pnpm) to run the suite.
- when editing `backend.py`, you should also edit `pydantic-test.py` to match the schema

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indentation, type hints where possible, small functions. Keep FastAPI router modules focused and mount under clear prefixes (`/premium`, `/lease`, `/management`).
- TypeScript/React: Functional components with hooks, keep state local, and avoid global mutable data. Name components in `PascalCase` and files in `camelCase` or `PascalCase`. Environment variables must use the `VITE_` prefix to be exposed to the UI.
- General: Prefer `uv` for Python dependency management and `pnpm` for Node. Keep imports sorted and remove unused code before committing.

## Testing Guidelines
- Add tests near the code under test (`backend/tests/` mirroring package layout). Name test files `test_*.py`; for React, prefer `*.test.tsx` colocated with components once a runner is configured.
- Cover at least the public API of new routers and any paywall logic; include happy path + failure cases (missing payment, invalid lease, etc.).
- For manual checks, hit `GET /premium/content` and lease endpoints while the server is running; confirm the React UI can fetch `/info` and `/chat` from your configured backend.

## Commit & Pull Request Guidelines
- Commits: Keep a concise, present-tense subject (~50 chars). Existing history uses short imperative summaries (`basic functions done`, `python FE env changes`); follow that style and avoid bundling unrelated changes.
- PRs: Describe the problem, the approach, and user-facing impact. Link issues/tickets, add screenshots for UI changes, and list validation steps (commands run, endpoints exercised). Mention any new env vars or migrations. Ensure CI/test commands noted above are executed or explain why not.
