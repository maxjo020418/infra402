import os
from dotenv import load_dotenv
from dataclasses import dataclass

from eth_account import Account
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from x402.clients.httpx import x402HttpxClient  # async client with auto x402 payments  # type: ignore

# env importer
load_dotenv()
LLM_BASE_URL = os.getenv("LLM_PROVIDER")
match LLM_BASE_URL:
    case "flock.io":
        base_url = "https://api.flock.io/v1"
        model_name = "qwen3-235b-a22b-instruct-2507"
        api_key = os.getenv("FLOCKIO_API_KEY")
    case "openai":
        base_url = None  # defaults to openai
        model_name = "gpt-4o-mini"
        api_key = os.getenv("OPENAI_API_KEY")
    case _:
        raise ValueError("LLM_BASE_URL should be defined")

assert api_key

print(f"""
base_url: {base_url if base_url is not None else "(default) openai"}
model_name: {model_name}
api_key: {api_key[:4]}...{api_key[-4:]}
""")

# ---------- Dependencies for the agent ----------

@dataclass
class Deps:
    """
    Dependencies injected into tools.

    Right now this just holds the EVM account that will be used
    to sign x402 payment headers.
    """
    account: Account


# ---------- Define the agent ----------

agent = Agent(
    model=OpenAIChatModel(
        model_name=model_name,
        provider=OpenAIProvider(
            base_url=base_url,
            api_key=api_key,
        )
    ),
    deps_type=Deps,
    instructions=(
        "You are a chatbot that can create paid LXC leases via x402.\n"
        "- Call the lease_container tool when the user asks to spin up or lease a container.\n"
        "- Required fields: sku, runtimeMinutes. Ask for them if missing.\n"
        "- Use defaults for cores/memoryMB/diskGB if not provided.\n"
        "- Explain briefly when you submit a lease."
    ),
)


@agent.tool
async def lease_container(
    ctx: RunContext[Deps],
    sku: str,
    runtimeMinutes: int,
    cores: int = 1,
    memoryMB: int = 512,
    diskGB: int = 8,
    hostname: str | None = None,
    requester: str | None = None,
) -> dict:
    """
    Create a paid LXC lease via the x402-protected backend at `/lease/container`.

    Required:
    - sku: product/plan id (e.g., "basic-lxc")
    - runtimeMinutes: how long the lease should last

    Optional:
    - cores, memoryMB, diskGB, hostname, requester

    Returns the backend LeaseResponse JSON, including `leaseId` and `ctid`.
    """

    backend_url = os.getenv("BACKEND_BASE_URL", "http://localhost:4021").rstrip("/")

    payload = {
        "sku": sku,
        "runtimeMinutes": runtimeMinutes,
        "hostname": hostname,
        "cores": cores,
        "memoryMB": memoryMB,
        "diskGB": diskGB,
        "requester": requester,
    }

    # x402HttpxClient wraps httpx.AsyncClient and handles the 402 flow:
    # 1) initial request, 2) detect 402, 3) parse payment instructions,
    # 4) sign with ctx.deps.account, 5) retry with payment header.
    async with x402HttpxClient(
        account=ctx.deps.account,
        base_url=backend_url,
    ) as client:
        resp = await client.post("/lease/container", json=payload)
        resp.raise_for_status()
        return resp.json()


# ---------- FastAPI wrapper around the agent ----------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str


class InfoResponse(BaseModel):
    base_url: str
    model_name: str
    api_key: str


def build_deps() -> Deps:
    """
    Build dependencies for each request.

    - Uses PRIVATE_KEY from env.
    - You can swap this to share the same key as an AgentKit EthAccountWalletProvider
      if you want everything on one wallet.
    """
    account = Account.from_key(os.environ.get("PRIVATE_KEY"))
    return Deps(account=account)


def build_prompt(message: str, history: list[ChatMessage]) -> str:
    """
    Convert chat history + new user message into a single prompt string
    for the agent. We avoid relying on Agent history APIs to keep this
    compatible with the current library version.
    """
    lines = [f"{m.role.upper()}: {m.content}" for m in history]
    lines.append(f"USER: {message}")
    return "\n".join(lines)


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    deps = build_deps()

    prompt = build_prompt(req.message, req.history)

    result = await agent.run(
        prompt,
        deps=deps,
    )

    return ChatResponse(reply=result.output)


@app.get("/info", response_model=InfoResponse)
async def info() -> InfoResponse:
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
    base_label = base_url if base_url is not None else "(default) openai"
    return InfoResponse(
        base_url=base_label,
        model_name=model_name,
        api_key=masked_key,
    )


# Test with
"""
BACKEND_BASE_URL=http://localhost:4021 \
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Lease a basic-lxc for 30 minutes with 2 cores and 2048 MB RAM."}'
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
