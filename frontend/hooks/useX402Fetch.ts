"use client";

import { wrapFetchWithPayment } from "x402-fetch";
import { useAccount } from "wagmi";
import { createWalletClient, custom } from "viem";
import { baseSepolia } from "@reown/appkit/networks";
import { useMemo } from "react";

export function useX402Fetch() {
  const { address, isConnected } = useAccount();

  const fetchWithPayment = useMemo(() => {
    if (!isConnected || !address || !window.ethereum) {
      return fetch;
    }

    const walletClient = createWalletClient({
      account: address,
      chain: baseSepolia,
      transport: custom(window.ethereum),
    });

    return wrapFetchWithPayment(fetch, walletClient);
  }, [address, isConnected]);

  return fetchWithPayment;
}
