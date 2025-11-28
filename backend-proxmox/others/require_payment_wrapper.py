import json
import os
from decimal import Decimal
from typing import Any, Callable, Dict, Literal, Optional

from dotenv import load_dotenv
from fastapi import Request
from pydantic import BaseModel
from x402.fastapi.middleware import require_payment
from x402.types import PaywallConfig

# Load environment variables
load_dotenv()

# Get configuration from environment
NETWORK = os.getenv("NETWORK", "base-sepolia")
ADDRESS = os.getenv("ADDRESS")
CDP_CLIENT_KEY = os.getenv("CDP_CLIENT_KEY")

ct_tiers = Literal[""]  # TBD

class PaymentTemplate(BaseModel):
    price: str = "$0.01"
    pay_to_address: str | None = ADDRESS
    path: str = "*"
    network: str = NETWORK
    paywall_config: PaywallConfig = PaywallConfig(
        cdp_client_key=CDP_CLIENT_KEY or "",
        app_name="infra402 payment",
        app_logo="/static/x402.png",
    )


def _calculate_dynamic_price(payload: dict[str, Any]) -> str:
    """Compute a small linear price based on requested resources."""
    runtime_minutes = Decimal(str(payload.get("runtimeMinutes", 0) or 0))
    cores = Decimal(str(payload.get("cores", 1) or 1))
    memory_mb = Decimal(str(payload.get("memoryMB", 512) or 512))
    disk_gb = Decimal(str(payload.get("diskGB", 8) or 8))

    base = Decimal("0.005")
    per_minute = Decimal("0.00005") * runtime_minutes
    per_core = Decimal("0.0005") * cores
    per_gb_ram = Decimal("0.0005") * (memory_mb / Decimal("1024"))
    per_gb_disk = Decimal("0.0002") * disk_gb

    total = base + per_minute + per_core + per_gb_ram + per_gb_disk
    total = total.quantize(Decimal("0.0001"))
    return f"${total}"


async def PaywallConfig_builder(request: Request) -> Optional[Dict[str, Any]]:
    path: str = request.url.path

    match path:
        case _ if path.startswith("/lease") and path.endswith("/container"):
            payload: dict[str, Any] = {}
            try:
                raw_body = await request.body()
                if raw_body:
                    payload = json.loads(raw_body)
            except Exception:
                payload = {}

            price = _calculate_dynamic_price(payload)
            return PaymentTemplate(price=price).model_dump()
        case _ if path.startswith("/lease") and path.endswith("/renew"):
            payload: dict[str, Any] = {}
            try:
                raw_body = await request.body()
                if raw_body:
                    payload = json.loads(raw_body)
            except Exception:
                payload = {}
            # Renewals priced only on runtimeMinutes; other fields ignored
            price = _calculate_dynamic_price(payload)
            return PaymentTemplate(price=price).model_dump()
        case _ if "/console" in path or "/command" in path or path.startswith("/management"):
            # Console/exec routes are protected for ownership and use a minimal fee.
            return PaymentTemplate(price="$0.001").model_dump()
        case _:
            return None

def dynamic_require_payment(config_builder: Callable):
    async def dyn_middleware(request: Request, call_next):
        config = await config_builder(request)

        if not config:  # no paywall
            return await call_next(request)
        
        new_middleware = require_payment(**config)
        return await new_middleware(request, call_next)
    
    return dyn_middleware
