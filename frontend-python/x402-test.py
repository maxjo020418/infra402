from eth_account import Account
from x402.clients.httpx import x402HttpxClient

from dotenv import load_dotenv
import os
import asyncio
import logging

load_dotenv()

# Initialize account
account = Account.from_key(os.getenv("PRIVATE_KEY"))

logging.basicConfig(
    format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)

async def main():
    # Create client and make request
    async with x402HttpxClient(
            account=account, 
            base_url="http://localhost:4021"
            ) as client:
        response = await client.get("/premium/content")
        print(await response.aread())

if __name__ == "__main__":
    asyncio.run(main())
