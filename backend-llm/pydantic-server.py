import os
from dataclasses import dataclass
from typing import Any, Literal

from dotenv import load_dotenv
from eth_account import Account
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from x402.clients.httpx import x402HttpxClient  # async client with auto x402 payments  # type: ignore

# env importer
load_dotenv()
LLM_PROVIDER = os.getenv("LLM_PROVIDER")
match LLM_PROVIDER:
    case "flockio":
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
        "- Before any paid action, calculate and show the estimated USD price using this formula and ask the user to confirm. Only submit lease_container or renew_lease after the user explicitly approves and set confirmPurchase=True on that call.\n"
        "  price = 0.005 + 0.00005*runtimeMinutes + 0.0005*cores + 0.0005*(memoryMB/1024) + 0.0002*diskGB (rounded to 4 decimals, prefixed with $)\n"
        "- For new leases, collect a default container password from the user and include confirmPurchase=True only after they confirm the cost.\n"
        "- Call lease_container to spin up or lease a container (required: sku, runtimeMinutes, password; use defaults otherwise).\n"
        "- Call renew_lease to extend an existing lease (ctid + runtimeMinutes) and restart it if needed; confirm price first and set confirmPurchase=True when proceeding.\n"
        "- Call exec_container_command (management route) or exec_lease_command (lease route) to run commands on an existing container.\n"
        "- Call open_container_console to request console access via the management route (ctid; consoleType optional, default vnc). open_lease_console is a backward-compatible alias.\n"
        "- Call list_managed_containers to see existing leases and their VM status.\n"
        "- Explain briefly when you submit a lease or run management actions."
    ),
)


def backend_base_url() -> str:
    return os.getenv("BACKEND_BASE_URL", "http://localhost:4021").rstrip("/")


class LeaseRequest(BaseModel):
    sku: str
    runtimeMinutes: int
    hostname: str | None = None
    cores: int = 1
    memoryMB: int = 512
    diskGB: int = 8
    password: str = Field(min_length=6, description="Default root password for the container")
    requester: str | None = None
    payload: dict[str, Any] | None = None


class LeaseResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    leaseId: str
    status: str
    ctid: str | None = None
    expiresAt: str | None = None
    message: str | None = None
    ownerWallet: str | None = None


class RenewLeaseRequest(BaseModel):
    runtimeMinutes: int = Field(gt=0)


class ExecRequest(BaseModel):
    command: str
    extraArgs: list[str] | None = None


class ExecResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    ctid: str
    upid: str
    output: str


class ConsoleRequest(BaseModel):
    consoleType: str | None = "vnc"


class ConsoleResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    ctid: str
    host: str
    port: int
    ticket: str
    user: str
    cert: str | None = None
    websocket: int | None = None
    proxy: str | None = None
    consoleUrl: str | None = None
    authCookie: str | None = None


class ManagedContainer(BaseModel):
    leaseId: str
    ctid: str
    status: str
    expiresAt: str | None = None
    network: str
    createdAt: str
    vmStatus: dict[str, Any] | None = None


def _client(account: Account) -> x402HttpxClient:
    return x402HttpxClient(
        account=account,
        base_url=backend_base_url(),
    )


def _estimate_price(
    runtime_minutes: int,
    cores: int | None = None,
    memory_mb: int | None = None,
    disk_gb: int | None = None,
) -> str:
    """Estimate price using the same linear formula as the backend paywall."""
    runtime = Decimal(str(runtime_minutes))
    c = Decimal(str(cores if cores is not None else 1))
    mem = Decimal(str(memory_mb if memory_mb is not None else 512))
    disk = Decimal(str(disk_gb if disk_gb is not None else 8))

    base = Decimal("0.005")
    per_minute = Decimal("0.00005") * runtime
    per_core = Decimal("0.0005") * c
    per_gb_ram = Decimal("0.0005") * (mem / Decimal("1024"))
    per_gb_disk = Decimal("0.0002") * disk

    total = base + per_minute + per_core + per_gb_ram + per_gb_disk
    return f"${total.quantize(Decimal('0.0001'))}"


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
    password: str | None = None,
    confirmPurchase: bool = False,
) -> LeaseResponse:
    """
    Create a paid LXC lease via the x402-protected backend at `/lease/container`.

    Required:
    - sku: product/plan id (e.g., "basic-lxc")
    - runtimeMinutes: how long the lease should last
    - password: default root password to set inside the container

    Optional:
    - cores, memoryMB, diskGB, hostname, requester
    - confirmPurchase: must be True to proceed with the paid action
    - Pricing formula: 0.005 + 0.00005*runtimeMinutes + 0.0005*cores + 0.0005*(memoryMB/1024) + 0.0002*diskGB (round to 4 decimals, prefix with $)

    Returns the backend LeaseResponse JSON, including `leaseId` and `ctid`.
    """
    if not confirmPurchase:
        estimate = _estimate_price(runtimeMinutes, cores=cores, memory_mb=memoryMB, disk_gb=diskGB)
        raise ValueError(
            f"Please confirm the purchase ({estimate}) and re-run with confirmPurchase=True."
        )
    if not password:
        raise ValueError("Please provide a container password (min 6 chars) before leasing a container.")

    payload = LeaseRequest(
        sku=sku,
        runtimeMinutes=runtimeMinutes,
        hostname=hostname,
        cores=cores,
        memoryMB=memoryMB,
        diskGB=diskGB,
        password=password,
        requester=requester,
    )

    async with _client(ctx.deps.account) as client:
        resp = await client.post("/lease/container", json=payload.model_dump(exclude_none=True))
        resp.raise_for_status()
        return LeaseResponse.model_validate(resp.json())


@agent.tool
async def exec_container_command(
    ctx: RunContext[Deps],
    ctid: str,
    command: str,
    extraArgs: list[str] | None = None,
) -> ExecResponse:
    """
    Execute a command on a leased container via `/management/exec/{ctid}`.

    Required:
    - ctid: container ID
    - command: command to run

    Optional:
    - extraArgs: list of extra CLI args
    """
    payload = ExecRequest(command=command, extraArgs=extraArgs)

    async with _client(ctx.deps.account) as client:
        resp = await client.post(f"/management/exec/{ctid}", json=payload.model_dump(exclude_none=True))
        resp.raise_for_status()
        return ExecResponse.model_validate(resp.json())


@agent.tool
async def exec_lease_command(
    ctx: RunContext[Deps],
    ctid: str,
    command: str,
    extraArgs: list[str] | None = None,
) -> ExecResponse:
    """
    Execute a command on a leased container via `/lease/{ctid}/command`.

    Required:
    - ctid: container ID
    - command: command to run

    Optional:
    - extraArgs: list of extra CLI args
    """
    payload = ExecRequest(command=command, extraArgs=extraArgs)

    async with _client(ctx.deps.account) as client:
        resp = await client.post(f"/lease/{ctid}/command", json=payload.model_dump(exclude_none=True))
        resp.raise_for_status()
        return ExecResponse.model_validate(resp.json())


@agent.tool
async def renew_lease(
    ctx: RunContext[Deps],
    ctid: str,
    runtimeMinutes: int,
    confirmPurchase: bool = False,
) -> LeaseResponse:
    """
    Renew an existing lease and restart the container if needed via `/lease/{ctid}/renew`.

    Args:
    - ctid: container ID
    - runtimeMinutes: additional minutes to extend the lease
    - confirmPurchase: must be True to proceed with the paid action
    - Pricing formula: 0.005 + 0.00005*runtimeMinutes (other terms use defaults from backend)
    """
    if not confirmPurchase:
        estimate = _estimate_price(runtimeMinutes)
        raise ValueError(
            f"Please confirm the renewal purchase ({estimate}) and re-run with confirmPurchase=True."
        )

    payload = RenewLeaseRequest(runtimeMinutes=runtimeMinutes)

    async with _client(ctx.deps.account) as client:
        resp = await client.post(f"/lease/{ctid}/renew", json=payload.model_dump())
        resp.raise_for_status()
        return LeaseResponse.model_validate(resp.json())


@agent.tool
async def open_container_console(
    ctx: RunContext[Deps],
    ctid: str,
    consoleType: str | None = "vnc",
) -> ConsoleResponse:
    """
    Request console access for a leased container via `/management/console/{ctid}`.

    Args:
    - ctid: container ID
    - consoleType: "vnc" (default) or "spice"
    """
    payload = ConsoleRequest(consoleType=consoleType)

    async with _client(ctx.deps.account) as client:
        resp = await client.post(f"/management/console/{ctid}", json=payload.model_dump(exclude_none=True))
        resp.raise_for_status()
        return ConsoleResponse.model_validate(resp.json())


@agent.tool
async def open_lease_console(
    ctx: RunContext[Deps],
    ctid: str,
    consoleType: str | None = "vnc",
) -> ConsoleResponse:
    """
    Request console access for a leased container via `/management/console/{ctid}`.

    Args:
    - ctid: container ID
    - consoleType: "vnc" (default) or "spice"
    """
    payload = ConsoleRequest(consoleType=consoleType)

    async with _client(ctx.deps.account) as client:
        resp = await client.post(f"/management/console/{ctid}", json=payload.model_dump(exclude_none=True))
        resp.raise_for_status()
        return ConsoleResponse.model_validate(resp.json())


@agent.tool
async def list_managed_containers(ctx: RunContext[Deps]) -> list[ManagedContainer]:
    """
    Retrieve active and past leases via `/management/list`.
    """
    async with _client(ctx.deps.account) as client:
        resp = await client.get("/management/list")
        resp.raise_for_status()
        raw_list = resp.json()
        return [ManagedContainer.model_validate(item) for item in raw_list]


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

    try:
        result = await agent.run(
            prompt,
            deps=deps,
        )
        reply = result.output
    except ValueError as exc:
        reply = str(exc)
    except Exception as exc:
        reply = f"Request failed: {exc}"

    return ChatResponse(reply=reply)


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
