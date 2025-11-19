"use client";

import { useCallback, useMemo, useState } from "react";
import { createWalletClient, custom, type Chain, type WalletClient } from "viem";
import { base, baseSepolia } from "viem/chains";

const CHAINS_BY_ID: Record<number, Chain> = {
  [base.id]: base,
  [baseSepolia.id]: baseSepolia,
};

const getChainById = (chainId?: number) => {
  if (!chainId) return undefined;
  return CHAINS_BY_ID[chainId];
};

export type BrowserWalletState = {
  address: `0x${string}` | null;
  chain: Chain | null;
  walletClient: WalletClient | null;
  isConnecting: boolean;
  error: string | null;
  connectWallet: () => Promise<void>;
  disconnectWallet: () => void;
  shortAddress: string;
};

export function useBrowserWallet(targetChain: Chain): BrowserWalletState {
  const [address, setAddress] = useState<`0x${string}` | null>(null);
  const [chain, setChain] = useState<Chain | null>(targetChain);
  const [walletClient, setWalletClient] = useState<WalletClient | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const connectWallet = useCallback(async () => {
    if (typeof window === "undefined") return;

    const provider = window.ethereum;
    if (!provider) {
      setError("No EIP-1193 wallet detected. Install Coinbase Wallet or MetaMask.");
      return;
    }

    setIsConnecting(true);
    try {
      const accounts = (await provider.request({
        method: "eth_requestAccounts",
      })) as string[];

      const [account] = accounts;
      if (!account) {
        throw new Error("Wallet did not return any accounts.");
      }

      const chainHex = (await provider.request({
        method: "eth_chainId",
      })) as string;
      const connectedChainId = chainHex ? parseInt(chainHex, 16) : undefined;
      const resolvedChain = getChainById(connectedChainId) || targetChain;

      const client = createWalletClient({
        account: account as `0x${string}`,
        chain: resolvedChain,
        transport: custom(provider),
      });

      setChain(resolvedChain);
      setAddress(account as `0x${string}`);
      setWalletClient(client);
      setError(null);
    } catch (err) {
      console.error("Failed to connect wallet", err);
      setError(
        err instanceof Error ? err.message : "Failed to connect wallet."
      );
    } finally {
      setIsConnecting(false);
    }
  }, [targetChain]);

  const disconnectWallet = useCallback(() => {
    setAddress(null);
    setChain(null);
    setWalletClient(null);
  }, []);

  const shortAddress = useMemo(() => {
    if (!address) return "";
    return `${address.slice(0, 6)}…${address.slice(-4)}`;
  }, [address]);

  return {
    address,
    chain,
    walletClient,
    isConnecting,
    error,
    connectWallet,
    disconnectWallet,
    shortAddress,
  };
}
