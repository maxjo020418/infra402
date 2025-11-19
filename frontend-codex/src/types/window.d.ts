type Eip1193RequestParams = {
  method: string;
  params?: unknown[] | Record<string, unknown>;
};

interface EthereumProvider {
  isCoinbaseWallet?: boolean;
  isMetaMask?: boolean;
  request: (args: Eip1193RequestParams) => Promise<unknown>;
}

declare global {
  interface Window {
    ethereum?: EthereumProvider;
  }
}

export {};
