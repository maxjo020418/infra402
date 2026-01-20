import { OnchainKitProvider } from '@coinbase/onchainkit';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { baseSepolia, base, sepolia } from 'wagmi/chains';
import { http, createConfig, WagmiProvider } from 'wagmi';
import { coinbaseWallet } from 'wagmi/connectors';
import type { ReactNode } from 'react';

const queryClient = new QueryClient();

const networkName = import.meta.env.VITE_DEFAULT_NETWORK;
let activeChain = baseSepolia;

if (networkName === 'base') {
  activeChain = base;
} else if (networkName === 'sepolia') {
  activeChain = sepolia;
}

const wagmiConfig = createConfig({
  chains: [activeChain],
  connectors: [
    coinbaseWallet({
      appName: 'Infra402',
    }),
  ],
  transports: {
    [activeChain.id]: http(),
  },
});

export function Providers({ children }: { children: ReactNode }) {
  return (
    <WagmiProvider config={wagmiConfig}>
      <QueryClientProvider client={queryClient}>
        <OnchainKitProvider
          apiKey={import.meta.env.VITE_ONCHAINKIT_API_KEY}
          chain={activeChain}
        >
          {children}
        </OnchainKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}
