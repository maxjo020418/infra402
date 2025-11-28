import os
from dotenv import load_dotenv

from coinbase_agentkit import (
    AgentKit,
    AgentKitConfig,
    CdpEvmWalletProvider,
    CdpEvmWalletProviderConfig,
    wallet_action_provider,
    cdp_api_action_provider,
    pyth_action_provider,
)
from coinbase_agentkit.action_providers.x402 import x402_action_provider


def initialize_agentkit() -> tuple[AgentKit, CdpEvmWalletProvider]:
    """Initialize AgentKit and the underlying CDP EVM wallet provider."""
    load_dotenv()

    network_id = os.getenv("NETWORK_ID", "base-sepolia")

    config = CdpEvmWalletProviderConfig(
        api_key_id=os.getenv("CDP_API_KEY_ID"),
        api_key_secret=os.getenv("CDP_API_KEY_SECRET"),
        wallet_secret=os.getenv("CDP_WALLET_SECRET"),
        network_id=network_id,
        address="0xC1f817bC6d0C5213B7Fa45Eac87a9E5a2fCfcB40"
        # address and idempotency_key are optional – let AgentKit handle idempotent creation
    ) # type: ignore

    wallet_provider = CdpEvmWalletProvider(config)  # type: ignore[arg-type]

    agentkit = AgentKit(
        AgentKitConfig(
            wallet_provider=wallet_provider,
            action_providers=[
                wallet_action_provider(),
                cdp_api_action_provider(),
                pyth_action_provider(),
                x402_action_provider(),
            ],
        )
    )

    return agentkit, wallet_provider


if __name__ == "__main__":
    try:
        agentkit, wallet_provider = initialize_agentkit()
        print("AgentKit initialized.")
        print(f"Wallet address: {wallet_provider.get_address()}")
        print(f"Network: {wallet_provider.get_network().network_id}")
    except Exception as e:
        # Let you see the full underlying CDP error/traceback.
        import traceback

        print("Failed to initialize AgentKit / CDP wallet:")
        traceback.print_exc()
