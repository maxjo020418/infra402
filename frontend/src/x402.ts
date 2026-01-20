import { type Address, type Hex, numberToHex } from 'viem';

export const X402_VERSION = 1;

export interface PaymentRequirement {
  scheme: string;
  network: string;
  maxAmountRequired: string;
  resource: string;
  description: string;
  mimeType: string;
  payTo: string;
  maxTimeoutSeconds: number;
  asset: string;
  extra?: {
    name?: string;
    version?: string;
    [key: string]: any;
  };
}

export interface PaymentRequest {
  x402Version: number;
  accepts: PaymentRequirement[];
  error: string;
}

export interface X402Header {
  x402Version: number;
  scheme: string;
  network: string;
  payload: {
    signature: Hex | null;
    authorization: {
      from: Address;
      to: Address;
      value: string;
      validAfter: string;
      validBefore: string;
      nonce: Hex;
    };
  };
}

export const EIP712_DOMAIN_TYPES = {
  TransferWithAuthorization: [
    { name: 'from', type: 'address' },
    { name: 'to', type: 'address' },
    { name: 'value', type: 'uint256' },
    { name: 'validAfter', type: 'uint256' },
    { name: 'validBefore', type: 'uint256' },
    { name: 'nonce', type: 'bytes32' },
  ],
} as const;

export function generateNonce(): Hex {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return `0x${Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')}`;
}

export function encodeX402Header(header: X402Header): string {
  const json = JSON.stringify(header);
  // Simple Base64 encoding for browser
  return btoa(json);
}

export function getChainId(network: string): number {
  if (import.meta.env.VITE_DEFAULT_CHAIN_ID) {
      return parseInt(import.meta.env.VITE_DEFAULT_CHAIN_ID, 10);
  }
  switch (network) {
    case 'base-sepolia':
      return 84532;
    case 'base':
      return 8453;
    case 'sepolia':
      return 11155111;
    case 'mainnet':
      return 1;
    default:
      throw new Error(`Unknown network: ${network}`);
  }
}
