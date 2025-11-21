from fastapi import HTTPException, Header


def check_x_payment_header(x_payment: str | None = Header(None)) -> None:
    """
    Temporary stub: treat any request that includes an X-Payment header
    as 'paid' and return the premium HTML asset.

    NOTE: This is NOT real payment verification; it's just a placeholder
    while wiring up the x402 client.
    """
    if not x_payment:
        # Normally the x402 middleware will have already responded with 402
        # before the request reaches this handler. This extra check is just
        # a temporary guard while experimenting.
        raise HTTPException(status_code=402, detail="Payment required (temporary stub).")