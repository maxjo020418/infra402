# infra402

Infrastructure leasing demo built around `x402` payments. This system allows users to lease and manage Proxmox LXC containers via an AI agent. The payment negotiation is handled on the client-side via wallet signatures (EIP-712).

## Architecture

The project consists of three distinct services:

1.  **Frontend (`frontend/`)**
    *   **Tech:** Vite + React (TypeScript), Wagmi, OnchainKit.
    *   **Role:** User interface for chatting with the AI agent and handling crypto payments. It connects to the user's wallet to sign payment authorizations when requested by the agent.
    *   **Port:** 3000 (default)

2.  **Agent Backend (`backend-llm/`)**
    *   **Tech:** Python, FastAPI, `pydantic-ai`.
    *   **Role:** An AI agent that interprets user requests and calls the paywalled Proxmox API. It detects `402 Payment Required` responses and propagates payment requests to the frontend instead of signing them itself.
    *   **Port:** 8000

3.  **Paywalled API (`backend-proxmox/`)**
    *   **Tech:** Python, FastAPI, `x402` middleware.
    *   **Role:** Interfaces directly with the Proxmox VE host to create/manage containers. It enforces payment via `x402` for sensitive operations.
    *   **Port:** 4021

## Getting Started

### Prerequisites
*   Python 3.10+ and `uv` (dependency manager)
*   Node.js 18+ and `pnpm`
*   Proxmox VE host + API token
*   EVM wallet (e.g., Coinbase Wallet, MetaMask)
*   Coinbase Developer Platform API Key (for OnchainKit)

### Configuration
Each service requires its own `.env` file.

*   **`backend-proxmox/.env`**:
    *   `ADDRESS`: EVM address to receive payments.
    *   `NETWORK`: EVM network name (default: `base-sepolia`).
    *   Proxmox credentials (`PVE_HOST`, `PVE_TOKEN_ID`, etc.).

*   **`backend-llm/.env`**:
    *   LLM provider config (`LLM_PROVIDER`, `OPENAI_API_KEY`, etc.).
    *   Note: `PRIVATE_KEY` is **no longer required** for the agent.

*   **`frontend/.env`**:
    *   `VITE_CHAT_API_BASE=http://localhost:8000`
    *   `VITE_ONCHAINKIT_API_KEY=your_cdp_api_key`
    *   `VITE_DEFAULT_NETWORK=base-sepolia` (Optional: 'base' or 'sepolia')

### Running the Project

Run each service in a separate terminal:

**1. Paywalled API**
```bash
cd backend-proxmox
uv sync
uv run python main.py
```

**2. Agent Backend**
```bash
cd backend-llm
uv sync
uv run python pydantic-server.py
```

**3. Frontend**
```bash
cd frontend
pnpm install
pnpm dev
```

## Development Guidelines

### Structure & Organization
*   **Boundaries:** The frontend talks *only* to the Agent (`backend-llm`). The Agent talks to the Paywall (`backend-proxmox`). The Paywall talks to Proxmox.
*   **Payment Flow:**
    1.  User requests action (e.g., "lease container").
    2.  Agent calls Paywall API.
    3.  Paywall returns `402 Payment Required`.
    4.  Agent catches 402 and returns `payment_request` JSON to Frontend.
    5.  Frontend prompts user to sign/pay via Wallet.
    6.  Frontend retries request to Agent with signed `X-Payment` header.
    7.  Agent attaches header and calls Paywall API again.
    8.  Paywall verifies signature and executes action.

### Coding Style
*   **Python:** 4-space indent, snake_case. Use type hints and Pydantic models.
*   **TypeScript:** PascalCase for components. Functional components with hooks. Strictly typed (avoid `any`).

### Testing
*   **Manual:** Verify flows via the UI. Connect wallet, trigger a paid action, and ensure the signature prompt appears and the action completes upon approval.
*   **Agent:** `backend-llm/agentkit-test.py` contains probes for testing agent tooling.