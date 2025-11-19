import { base, baseSepolia, type Chain } from "viem/chains";

const API_BASE = process.env.NEXT_PUBLIC_INFRA_API_BASE?.trim();
const NETWORK_FROM_ENV = process.env.NEXT_PUBLIC_EVM_NETWORK?.trim();

const STRIPPED_BASE =
  API_BASE && API_BASE.endsWith("/") ? API_BASE.slice(0, -1) : API_BASE;

const DEFAULT_CHAIN =
  NETWORK_FROM_ENV && NETWORK_FROM_ENV.toLowerCase() === "base"
    ? base
    : baseSepolia;

export const API_BASE_URL = STRIPPED_BASE || "http://localhost:4021";
export const TARGET_CHAIN: Chain = DEFAULT_CHAIN;
export const TARGET_NETWORK_LABEL =
  NETWORK_FROM_ENV?.toLowerCase() === "base" ? "Base Mainnet" : "Base Sepolia";
