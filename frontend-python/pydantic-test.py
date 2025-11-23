import os
from dotenv import load_dotenv
from dataclasses import dataclass

from eth_account import Account
from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from x402.clients.httpx import x402HttpxClient  # async client with auto x402 payments  # type: ignore

load_dotenv()

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
        model_name="gpt-4o-mini",
        provider=OpenAIProvider(
            # base_url="http://localhost:8000/v1",
            api_key=os.getenv("LLM_KEY"),
        )
    ),
    deps_type=Deps,
    instructions=(
        "You are a chatbot that can optionally fetch premium content "
        "from an x402-protected endpoint.\n"
        "- Only call the fetch_premium_content tool when the user explicitly "
        "asks for premium or paid content.\n"
        "- Otherwise answer normally.\n"
        "- Explain briefly what you are doing when you use the tool."
    ),
)


@agent.tool
async def fetch_premium_content(ctx: RunContext[Deps]) -> str:
    """
    Fetch premium content from the x402-protected endpoint
    `http://localhost:4021/premium/content`.

    This tool will:
    - Make an HTTP request to the endpoint.
    - If the server returns HTTP 402 with x402 payment instructions,
      the x402 client will automatically construct a payment,
      sign it with the provided wallet, and retry the request.
    - Return the response body as text.
    """

    # Base URL without the path; the path is passed to .get()
    base_url = "http://localhost:4021"

    # x402HttpxClient wraps httpx.AsyncClient and handles the full x402 flow:​:contentReference[oaicite:3]{index=3}
    # 1) initial request
    # 2) detect 402 Payment Required
    # 3) parse payment requirements
    # 4) sign payment with ctx.deps.account
    # 5) retry request with payment header
    async with x402HttpxClient(
        account=ctx.deps.account,
        base_url=base_url,
    ) as client:
        resp = await client.get("/premium/content")
        # Raise for non-2xx (after payment has been handled)
        resp.raise_for_status()

        # Read the full body as bytes and decode as UTF-8 text
        body_bytes = await resp.aread()
        return body_bytes.decode("utf-8")


# ---------- FastAPI wrapper around the agent ----------

app = FastAPI()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


def build_deps() -> Deps:
    """
    Build dependencies for each request.

    - Uses PRIVATE_KEY from env.
    - You can swap this to share the same key as an AgentKit EthAccountWalletProvider
      if you want everything on one wallet.
    """
    # private_key = os.environ.get("PRIVATE_KEY")
    # if not private_key:
    #     raise RuntimeError("PRIVATE_KEY environment variable is required")

    # if not private_key.startswith("0x"):
    #     raise RuntimeError("PRIVATE_KEY must start with 0x")

    account = Account.from_key(os.environ.get("PRIVATE_KEY"))
    return Deps(account=account)


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    deps = build_deps()

    # Single-turn run; you can store and pass message history if you want a real chat.
    result = await agent.run(
        req.message,
        deps=deps,
    )

    return ChatResponse(reply=result.output)


# Test with
"""
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Please fetch the premium content."}'
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
