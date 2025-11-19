# infra402 frontend stub

Chat-first dashboard for leasing infrastructure through Coinbase x402. The UI is intentionally lightweight: a chat surface that can plan container / VM work, and an action sidebar that calls the backend API so it can respond with `402 Payment Required` whenever a lease must be purchased.

## Quick start

```bash
pnpm install
pnpm dev
```

Then open http://localhost:3000. The UI uses a white background with an orange accent to match the base design brief.

## Configuration

Set the following environment variables (create `.env.local` in this folder):

| Variable | Default | Description |
| --- | --- | --- |
| `NEXT_PUBLIC_INFRA_API_BASE` | `http://localhost:4021` | Base URL for the FastAPI/x402 backend. Paths `/chat`, `/leases/container`, `/leases/vm`, and `/leases/gpu` are appended to this value. |
| `NEXT_PUBLIC_EVM_NETWORK` | `base-sepolia` | Target network for the wallet client (`base` or `base-sepolia`). Used when creating the Viem wallet for `x402-fetch`. |

When the backend returns HTTP 402, `x402-fetch` intercepts the response, prompts the connected wallet, and automatically retries the request with the x402 payment header.

## What’s in the UI?

- **Wallet connect stub** – minimal EIP-1193 connect button that builds a Viem wallet client and feeds it into `wrapFetchWithPayment`.
- **Chatbot shell** – posts to `${NEXT_PUBLIC_INFRA_API_BASE}/chat`. If the request fails (e.g., the backend is not running) it falls back to stubbed replies so the UI remains interactive.
- **Lease buttons** – each button hits a different `/leases/*` endpoint. They are intended to raise HTTP 402 from the FastAPI server; the message panel displays whether the lease was acknowledged, paid, or rejected.
- **Theme** – enforced white primary background with orange accent tokens.

## Testing payments

1. Run the FastAPI server from the repository root (`uv run python main.py`). Make sure its endpoints match the paths listed above.
2. Start the Next.js app (`pnpm dev`) and connect a wallet in your browser (Coinbase Wallet, MetaMask, etc.).
3. Click one of the lease buttons or issue a chat command that triggers a lease. When the backend responds with HTTP 402 the wallet will open; approving the transaction retries the same request with the `X-Payment` header populated by `x402-fetch`.

Because the backend URL is configurable you can point the UI at staging, production, or a mock API without changing the code.
