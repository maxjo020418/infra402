import base64
import json
from typing import Optional

from fastapi import HTTPException, Request, status
from x402.types import VerifyResponse


def _wallet_from_x_payment(header_value: str) -> Optional[str]:
    try:
        decoded = base64.b64decode(header_value).decode("utf-8")
        payload = json.loads(decoded)
    except Exception:
        return None

    auth = payload.get("payload", {}).get("authorization", {})
    wallet = auth.get("from")
    if isinstance(wallet, str) and wallet:
        return wallet
    return None


def get_request_wallet(request: Request) -> str:
    """
    Extract a wallet address from the request.

    This is a lightweight auth helper for mock/free endpoints:
    - Prefer verified payer if already available on request.state.
    - Otherwise accept an X-Payment header and extract the "from" address.
    - Otherwise accept an X-Wallet header.
    """
    verify: VerifyResponse | None = getattr(request.state, "verify_response", None)
    if verify is not None and verify.payer:
        return verify.payer

    x_payment = request.headers.get("X-Payment")
    if x_payment:
        wallet = _wallet_from_x_payment(x_payment)
        if wallet:
            return wallet

    wallet = request.headers.get("X-Wallet")
    if wallet:
        return wallet

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing wallet authentication",
    )
