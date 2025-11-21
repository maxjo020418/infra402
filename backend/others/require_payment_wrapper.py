from x402.fastapi.middleware import require_payment
from x402.types import PaywallConfig
from fastapi import Request

from pydantic import BaseModel

from typing import Optional, Dict, Literal, Callable, Any
from dotenv import load_dotenv
import os

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

def PaywallConfig_builder(request: Request) \
    -> Optional[Dict[str, Any]]:

    path: str = request.url.path
    match path:
        case _ if path.startswith("/lease"):
            tier: str | None = request.query_params.get("tier")
            # temp setup
            return PaymentTemplate().model_dump()
        case _ if path.startswith("/premium"):  # for testing
            return PaymentTemplate(price="$0.02").model_dump()
        case _:
            return None

def dynamic_require_payment(config_builder: Callable):
    async def dyn_middleware(request: Request, call_next):
        config = PaywallConfig_builder(request)

        if not config:  # no paywall
            return await call_next(request)
        
        new_middleware = require_payment(**config)
        return await new_middleware(request, call_next)
    
    return dyn_middleware
