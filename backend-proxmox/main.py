import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import routers
from others.require_payment_wrapper import (
    PaywallConfig_builder, 
    dynamic_require_payment
)
from others.lease_worker import start_lease_worker, stop_lease_worker

# Load environment variables
load_dotenv()

# Get configuration from environment
NETWORK = os.getenv("NETWORK", "base-sepolia")
ADDRESS = os.getenv("ADDRESS")
CDP_CLIENT_KEY = os.getenv("CDP_CLIENT_KEY")

if not ADDRESS:
    raise ValueError("Missing required environment variables")

app = FastAPI()

# Allow local frontend to call this API directly
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Apply payment middleware
app.middleware("http")(dynamic_require_payment(PaywallConfig_builder))

app.include_router(routers.lease.router)
app.include_router(routers.management.router)


@app.on_event("startup")
async def _startup() -> None:
    # Start background lease status refresher
    start_lease_worker(app)


@app.on_event("shutdown")
async def _shutdown() -> None:
    await stop_lease_worker(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4021)
