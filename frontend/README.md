# x402 Chat Frontend (Vite + React)

Simple chat UI that calls the local FastAPI agent (`frontend-python/pydantic-test.py`) and shows its LLM config.

## Setup

```bash
cd frontend-codex
cp .env.example .env
npm install
npm run dev  # http://localhost:3000
```

## Env

Create `.env` with:

```
VITE_CHAT_API_BASE=http://localhost:8000
```

## Notes

- UI calls `${VITE_CHAT_API_BASE}/chat` and fetches `${VITE_CHAT_API_BASE}/info` to display base URL, model, and masked API key.
