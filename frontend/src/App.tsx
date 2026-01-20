import {
  FormEvent,
  KeyboardEvent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { sdk } from "@farcaster/miniapp-sdk";
import {
  ConnectWallet,
  Wallet,
  WalletDropdown,
  WalletDropdownDisconnect,
} from "@coinbase/onchainkit/wallet";
import { Address, Avatar, Name, Identity, EthBalance } from "@coinbase/onchainkit/identity";
import { useAccount, useSignTypedData } from "wagmi";
import {
  encodeX402Header,
  generateNonce,
  getChainId,
  EIP712_DOMAIN_TYPES,
  type PaymentRequest,
  type PaymentRequirement,
  type X402Header,
  X402_VERSION,
} from "./x402";
import { Hex } from "viem";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type Info = {
  base_url: string;
  model_name: string;
  api_key: string;
};

const markdownComponents: Components = {
  a: ({ node, ...props }) => (
    <a {...props} target="_blank" rel="noreferrer">
      {props.children}
    </a>
  ),
};

const chatApiBase =
  (import.meta.env.VITE_CHAT_API_BASE as string | undefined)?.replace(
    /\/$/,
    "",
  ) || "http://localhost:8000";

function randomId() {
  return Math.random().toString(36).slice(2, 10);
}

function App() {
  const { address, isConnected } = useAccount();
  const { signTypedDataAsync } = useSignTypedData();

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: randomId(),
      role: "assistant",
      content: "hello! how can I help you?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<Info | null>(null);
  const [pendingPayment, setPendingPayment] = useState<PaymentRequest | null>(
    null,
  );

  // Track the message that triggered the payment to retry it
  const [pendingMessageContent, setPendingMessageContent] = useState<string | null>(null);

  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const messagesRef = useRef<HTMLElement | null>(null);

  const canSend = useMemo(
    () => Boolean(input.trim()) && !loading && !pendingPayment,
    [input, loading, pendingPayment],
  );

  // Base App MiniApp SDK - notify app is ready
  useEffect(() => {
    sdk.actions.ready();
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const resp = await fetch(`${chatApiBase}/info`);
        if (!resp.ok) return;
        const data = (await resp.json()) as Info;
        if (!cancelled) setInfo(data);
      } catch {
        // ignore
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!messagesRef.current) return;
    messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
  }, [messages, loading, pendingPayment]);

  async function sendChat(
    event?: FormEvent,
    overrideContent?: string,
    paymentHeaders?: Record<string, string>,
  ) {
    event?.preventDefault();
    setError(null);

    const content = overrideContent ?? input.trim();
    if (!content) return;
    if (loading) return;

    // If this is a new message (not a retry), add to history
    if (!overrideContent) {
      const userMessage: ChatMessage = {
        id: randomId(),
        role: "user",
        content,
      };
      setMessages((prev) => [...prev, userMessage]);
      setInput("");
    }

    setLoading(true);

    // Build history for the request
    // Note: If retrying, the last user message is already in `messages` state
    let historyPayload = messages.map(({ role, content: text }) => ({
      role,
      content: text,
    }));

    if (overrideContent) {
      // If retrying, the last message in history is likely the user message we are sending.
      // Remove it to avoid duplication since backend appends `message`.
      const lastMsg = historyPayload[historyPayload.length - 1];
      if (lastMsg && lastMsg.role === 'user' && lastMsg.content === overrideContent) {
        historyPayload.pop();
      }
    }

    try {
      const body: any = {
        message: content,
        history: historyPayload,
      };

      if (paymentHeaders) {
        body.payment_headers = paymentHeaders;
      }

      const response = await fetch(`${chatApiBase}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Request failed: ${response.status} ${text}`);
      }

      const data = await response.json();

      if (data.payment_request) {
        // 402 encountered
        setPendingPayment(data.payment_request);
        setPendingMessageContent(content);
        // Do NOT add an assistant message yet.
        return;
      }

      const reply = data?.reply ?? "No content returned.";

      const assistantMessage: ChatMessage = {
        id: randomId(),
        role: "assistant",
        content: reply,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Clear pending state on success
      setPendingPayment(null);
      setPendingMessageContent(null);

    } catch (err) {
      const reason =
        err instanceof Error ? err.message : "Unexpected error during request.";
      setError(reason);
      setMessages((prev) => [
        ...prev,
        {
          id: randomId(),
          role: "assistant",
          content: "Something went wrong while contacting the LLM.",
        },
      ]);
    } finally {
      setLoading(false);
      // Only focus if we aren't waiting for payment
      if (!pendingPayment) {
        inputRef.current?.focus();
      }
    }
  }

  async function handlePayment() {
    if (!pendingPayment || !address || !pendingMessageContent) return;
    setError(null);

    try {
      // 1. Select requirement (exact scheme, correct network)
      const targetNetwork = import.meta.env.VITE_DEFAULT_NETWORK || "base-sepolia";
      const requirement = pendingPayment.accepts.find(
        (r) => r.scheme === "exact" && r.network === targetNetwork
      );

      if (!requirement) {
        throw new Error(`No supported payment scheme found (need exact on ${targetNetwork})`);
      }

      // 2. Prepare data
      const chainId = getChainId(requirement.network);
      const nonce = generateNonce();
      const validAfter = BigInt(Math.floor(Date.now() / 1000) - 60);
      const validBefore = BigInt(
        Math.floor(Date.now() / 1000) + requirement.maxTimeoutSeconds
      );
      const value = BigInt(requirement.maxAmountRequired);

      const domain = {
        name: requirement.extra?.name ?? "USD Coin",
        version: requirement.extra?.version ?? "2",
        chainId,
        verifyingContract: requirement.asset as Address,
      } as const;

      const message = {
        from: address,
        to: requirement.payTo as Address,
        value,
        validAfter,
        validBefore,
        nonce,
      };

      // 3. Sign
      const signature = await signTypedDataAsync({
        domain,
        types: EIP712_DOMAIN_TYPES,
        primaryType: "TransferWithAuthorization",
        message,
      });

      // 4. Construct Header
      const header: X402Header = {
        x402Version: X402_VERSION,
        scheme: "exact",
        network: requirement.network,
        payload: {
          signature,
          authorization: {
            from: address,
            to: requirement.payTo as Address,
            value: value.toString(),
            validAfter: validAfter.toString(),
            validBefore: validBefore.toString(),
            nonce,
          },
        },
      };

      const encodedHeader = encodeX402Header(header);

      // 5. Retry Chat
      // We pass the pending content and the new headers
      await sendChat(undefined, pendingMessageContent, {
        "X-Payment": encodedHeader,
      });

    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Payment failed");
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSend) {
        void sendChat();
      }
    }
  }

  function resetConversation() {
    setMessages([
      {
        id: randomId(),
        role: "assistant",
        content: "hello! how can I help you?",
      },
    ]);
    setError(null);
    setInput("");
    setPendingPayment(null);
    setPendingMessageContent(null);
    inputRef.current?.focus();
  }

  return (
    <div className="page">
      <header className="hero">
        <div className="flex justify-between items-start w-full">
          <div>
            <h1>Infra402</h1>
            <p className="lede">
              Chat with your agent to explore infra402 :D<br />
              Provision containers and pay using x402!
            </p>
            <div className="meta">
              <span>Base URL: {info?.base_url ?? "…"}</span>
              <span>Model: {info?.model_name ?? "…"}</span>
            </div>
          </div>
          <div className="wallet-container">
            <Wallet>
              <ConnectWallet>
                <Avatar className="h-6 w-6" />
                <Name />
              </ConnectWallet>
              <WalletDropdown>
                <Identity className="px-4 pt-3 pb-2" hasCopyAddressOnClick>
                  <Avatar />
                  <Name />
                  <Address />
                  <EthBalance />
                </Identity>
                <WalletDropdownDisconnect />
              </WalletDropdown>
            </Wallet>
          </div>
        </div>
        <div className="hero-actions">
          <button className="ghost" onClick={resetConversation}>
            Reset chat
          </button>
        </div>
      </header>

      <main className="chat-shell">
        <section className="messages" ref={messagesRef}>
          {messages.map((msg) => (
            <article key={msg.id} className={`message ${msg.role}`}>
              <div className="avatar">
                {msg.role === "user" ? "You" : "i402"}
              </div>
              <div className="bubble">
                <div className="markdown">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={markdownComponents}
                  >
                    {msg.content}
                  </ReactMarkdown>
                </div>
              </div>
            </article>
          ))}

          {pendingPayment && (
            <article className="message assistant payment-request">
              <div className="avatar">i402</div>
              <div className="bubble payment-bubble">
                <p><strong>Payment Required</strong></p>
                <p>This action requires a micropayment.</p>
                {!isConnected ? (
                  <p className="text-sm mt-2 text-yellow-400">Please connect your wallet first.</p>
                ) : (
                  <button
                    className="pay-button"
                    onClick={handlePayment}
                    disabled={loading}
                  >
                    {loading ? "Processing..." : "Sign & Pay"}
                  </button>
                )}
              </div>
            </article>
          )}

          {loading && !pendingPayment && (
            <div className="typing">Model is thinking…</div>
          )}
        </section>

        <form className="composer" onSubmit={(e) => sendChat(e)}>
          <textarea
            ref={inputRef}
            placeholder="Ask something..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={3}
            disabled={!!pendingPayment}
          />
          <div className="composer-actions">
            {error && <div className="error">{error}</div>}
            <button type="submit" disabled={!canSend}>
              {loading ? "Sending…" : "Send"}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}

export default App;
