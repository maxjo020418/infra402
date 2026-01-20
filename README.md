# infra402

Infrastructure leasing demo built around `x402` payments.

This repo contains three services:
- `backend-proxmox/`: FastAPI paywalled API that provisions and manages Proxmox LXC containers (port `4021`).
- `backend-llm/`: FastAPI chat agent that calls the paywalled API. It acts as an orchestrator but delegates payment signing to the client (port `8000`).
- `frontend/`: Vite + React UI that calls the agent service and handles crypto payments via wallet connection (port `3000`).

## Requirements

- Python `3.10+`
- `uv` (Python dependency manager)
- Node.js `18+`
- `pnpm`
- Proxmox VE host + API token (to actually create/manage containers)
- An EVM address to receive payments (paywall configuration)
- A browser wallet (e.g., Coinbase Wallet) for the client-side user
- Coinbase Developer Platform API Key (for OnchainKit in the frontend)

## Configuration

### `backend-proxmox` (paywalled API)

Create `backend-proxmox/.env` (start from `backend-proxmox/.example.env`) and set at minimum:
- `ADDRESS`: EVM address to receive payments
- `NETWORK`: EVM network name (defaults to `base-sepolia`)

To enable Proxmox operations, also set:
- `PVE_HOST`, `PVE_TOKEN_ID`, `PVE_TOKEN_SECRET`, `PVE_NODE`, `PVE_STORAGE`, `PVE_OS_TEMPLATE`
- `PVE_ROOT_PASSWORD` (used for console ticket flows)
- `PVE_VERIFY_SSL` (`true`/`false`)
- Optional: `PVE_CONSOLE_HOST` (external hostname for console URLs)

See `backend-proxmox/PROXMOX_API_USAGE.md` for the expected Proxmox-side permissions and endpoints.

### `backend-llm` (agent API)

Create `backend-llm/.env` (start from `backend-llm/.example.env`) and set:
- `LLM_PROVIDER`: `openai` or `flockio`
- If `LLM_PROVIDER=openai`: `OPENAI_API_KEY`
- If `LLM_PROVIDER=flockio`: `FLOCKIO_API_KEY`
- Optional: `BACKEND_BASE_URL` (defaults to `http://localhost:4021`)

Note: `backend-llm/.example.env` may not list all currently used variables; the server reads `LLM_PROVIDER`, `OPENAI_API_KEY`, and `FLOCKIO_API_KEY`.

### `frontend` (UI)

Create `frontend/.env` with:
```
VITE_CHAT_API_BASE=http://localhost:8000
VITE_ONCHAINKIT_API_KEY=your_cdp_api_key
VITE_DEFAULT_NETWORK=base-sepolia
```

## Run (local)

### 1) Start the paywalled API
```bash
cd backend-proxmox
uv sync
uv run python main.py  # http://localhost:4021
```

### 2) Start the agent API
```bash
cd backend-llm
uv sync
uv run python pydantic-server.py  # http://localhost:8000
```

### 3) Start the UI
```bash
cd frontend
pnpm install
pnpm dev  # http://localhost:3000
```

## API surface

Agent service (no payment required):
- `GET /info`: returns the configured LLM base URL + model name (and a masked API key)
- `POST /chat`: chat endpoint; the agent can call paid tools to manage leases. Returns a `payment_request` object if 402 is encountered.

Paywalled Proxmox service (`x402` payment required):
- `POST /lease/container`
- `POST /lease/{ctid}/renew`
- `POST /management/exec/{ctid}`
- `POST /management/console/{ctid}`
- `GET /management/list`

For request/response examples and the payment flow, see `backend-proxmox/API_USAGE.md`.

## Notes

- Secrets belong in `.env` files and should not be committed.
- The **frontend** is the entity that signs the payment headers using the connected wallet. The agent backend merely facilitates the negotiation.