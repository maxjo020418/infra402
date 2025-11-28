# Repository Guidelines

Contributor quick-start for infra402. Keep changes small, typed, and in line with the service boundaries below.

## Project Structure & Module Organization
- `backend-proxmox/`: FastAPI paywall server; routes live in `routers/` (`lease.py`, `management.py`), shared helpers in `others/`, bundled x402 source in `x402/`.
- `backend-llm/`: FastAPI agent service using `pydantic-ai` and x402 HTTP client; entrypoint `pydantic-test.py` exposes `/chat` and `/info`, probes in `agentkit-test.py`.
- `frontend/`: Vite + React (TypeScript) chat UI in `src/`, styles in `styles.css`; configured via `VITE_CHAT_API_BASE`.
- Root docs: `plans.md`, placeholder `README.md`; Python envs use `pyproject.toml` + `uv.lock`.
- frontend calls backend-llm and backend-proxmox calls services from backend-proxmox

## Build, Test, and Development Commands
- Paywall backend: `cd backend-proxmox && uv sync && uv run python main.py` (requires `.env` based on `.env-local`, serves on `:4021`).
- LLM agent backend: `cd backend-llm && uv sync && uv run python pydantic-test.py` for `/chat` and `/info` on `:8000`; `uv run python agentkit-test.py` exercises agent tooling.
- Frontend: `cd frontend && pnpm install && pnpm dev` for local dev; `pnpm build` then `pnpm preview` to verify prod bundle.
- when developing either backends' function, corresponding llm exposure via backend-llm and actual implementation to backend-proxmox needs to be made.

## Coding Style & Naming Conventions
- Python: 4-space indent, type hints, async FastAPI handlers. Use `pydantic` models for request/response payloads. Keep env reads at startup and pass state via dependency helpers (e.g., `Deps` in agent service). Snake_case for modules/vars.
- TypeScript/React: functional components with hooks; typed props/state (no implicit `any`). PascalCase for components. Keep CSS in `styles.css`; prefer semantic markup for chat UI.

## Testing Guidelines
- No formal suite yet; validate manually: hit `/info` and `/chat` on `:8000`; `/lease/...`, `/management/...` on `:4021` with payment headers via x402 client.
- Future tests: prefer `pytest` for backends; React Testing Library/Vitest for UI. Mirror module boundaries in test filenames.

## Commit & Pull Request Guidelines
- Commits: short, imperative (e.g., `basic functions done`, `extra basic functions`); keep one focus per commit.
- PRs: summarize scope and affected services (`backend-proxmox`, `backend-llm`, `frontend`), call out env var changes (`ADDRESS`, `NETWORK`, `PRIVATE_KEY`, `LLM_PROVIDER`, API keys), list manual test commands and expected ports, add screenshots/GIFs for UI tweaks, and link issues when relevant.

## Security & Configuration Tips
- Keep `.env` values out of VCS; base on `.env-local`. Never log secrets.
- Ports: paywall on `4021`, agent on `8000`. Frontend uses `VITE_CHAT_API_BASE` to point at agent service.
- When wiring new LLM functionality, update both paywall implementation (`backend-proxmox`) and exposure in agent service (`backend-llm`) to stay in sync.
