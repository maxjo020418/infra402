"use client";

import { AppKitProvider, createAppKit } from "@reown/appkit/react";
import { WagmiAdapter } from "@reown/appkit-adapter-wagmi";
import { baseSepolia } from "@reown/appkit/networks";
import { ReactNode } from "react";

// 1. Get projectId from https://cloud.walletconnect.com
const projectId = process.env.NEXT_PUBLIC_PROJECT_ID;
if (!projectId) {
  throw new Error("NEXT_PUBLIC_PROJECT_ID is not set");
}

// 2. Create AppKit instance
const metadata = {
  name: 'Infra402',
  description: 'Lease infrastructure with x402 payments',
  url: 'http://localhost:3000',
  icons: ['/icon.png']
}

const wagmiAdapter = new WagmiAdapter({
  projectId,
  networks: [baseSepolia],
  ssr: true,
});

const appKit = createAppKit({
  projectId,
  metadata,
  adapters: [wagmiAdapter],
});

export function Web3ModalProvider({ children }: { children: ReactNode }) {
  return (
    <AppKitProvider appKit={appKit}>
      {children}
    </AppKitProvider>
  );
}
