"use client";

import { useCallback, useMemo, useState } from "react";
import { wrapFetchWithPayment } from "x402-fetch";

import {
  type Fetcher,
  PaymentRequiredError,
  requestInfrastructureLease,
  sendChatMessage,
} from "@/lib/api";
import { TARGET_CHAIN, TARGET_NETWORK_LABEL, API_BASE_URL } from "@/lib/config";
import { buildStubbedChatReply, buildStubbedLeaseMessage } from "@/lib/stubs";
import { useBrowserWallet } from "@/hooks/useBrowserWallet";

type ChatRole = "assistant" | "user" | "system";

type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
};

type InfraAction = {
  id: string;
  title: string;
  description: string;
  sku: string;
  runtimeMinutes: number;
  price: string;
  badge: string;
  path: string;
};

const initialMessages: ChatMessage[] = [
  {
    id: "assistant-hello",
    role: "assistant",
    content:
      "Hello from the infra steward. Ask me to scale containers, schedule new VMs, or plan GPU jobs. I will raise x402 payments whenever a lease is required.",
    timestamp: new Date().toISOString(),
  },
];

const infraActions: InfraAction[] = [
  {
    id: "container-surge",
    title: "Burst Containers",
    description: "2 vCPU / 4 GB RAM containers for CI or short-lived jobs.",
    sku: "container-burst-2vcpu",
    runtimeMinutes: 15,
    price: "$0.02 / min",
    badge: "Ephemeral",
    path: "/leases/container",
  },
  {
    id: "vm-memory",
    title: "Memory-Heavy VM",
    description: "8 vCPU / 32 GB RAM VM pinned near the build cluster.",
    sku: "vm-memory-8x32",
    runtimeMinutes: 60,
    price: "$0.07 / min",
    badge: "Persistent",
    path: "/leases/vm",
  },
  {
    id: "gpu-rig",
    title: "A100 GPU Rig",
    description: "Single A100 with 80 GB VRAM for training bursts.",
    sku: "gpu-a100",
    runtimeMinutes: 30,
    price: "$0.65 / min",
    badge: "Premium",
    path: "/leases/gpu",
  },
];

const messageAccent: Record<ChatRole, string> = {
  assistant: "border-l-4 border-orange-500 bg-orange-50",
  user: "border-l-4 border-slate-300 bg-white",
  system: "border-l-4 border-slate-500 bg-slate-50",
};

const formatTimestamp = (timestamp: string) =>
  new Date(timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

export default function InfraChatApp() {
  const {
    address,
    chain,
    walletClient,
    connectWallet,
    disconnectWallet,
    isConnecting,
    error: walletError,
    shortAddress,
  } = useBrowserWallet(TARGET_CHAIN);

  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [pendingLeaseId, setPendingLeaseId] = useState<string | null>(null);
  const [leaseStatus, setLeaseStatus] = useState<string | null>(null);
  const [sessionId] = useState(
    () =>
      (typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `session-${Date.now().toString(36)}`) as string
  );

  const fetcher: Fetcher = useMemo(() => {
    if (!walletClient) {
      return fetch;
    }
    return wrapFetchWithPayment(fetch, walletClient) as Fetcher;
  }, [walletClient]);

  const setSystemMessage = useCallback((content: string) => {
    setMessages((prev) => [
      ...prev,
      {
        id: `system-${Date.now()}`,
        role: "system",
        content,
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);

  const handleSendMessage = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    const newMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmed,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInput("");
    setIsSending(true);

    try {
      const response = await sendChatMessage(
        { message: trimmed, sessionId },
        fetcher
      );
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response.reply,
          timestamp: new Date().toISOString(),
        },
      ]);
      if (response.steps?.length) {
        setSystemMessage(
          `Planned steps: ${response.steps.map((s) => `• ${s}`).join(" ")}`
        );
      }
    } catch (error) {
      if (error instanceof PaymentRequiredError) {
        setSystemMessage(
          "The backend responded with HTTP 402. Connect your wallet so x402-fetch can settle the lease automatically."
        );
      } else {
        setSystemMessage(buildStubbedChatReply(trimmed));
      }
      console.warn("Chat request failed", error);
    } finally {
      setIsSending(false);
    }
  }, [fetcher, input, isSending, sessionId, setSystemMessage]);

  const handleLease = useCallback(
    async (action: InfraAction) => {
      if (pendingLeaseId) return;

      setPendingLeaseId(action.id);
      setLeaseStatus(`Requesting ${action.title}...`);

      try {
        const response = await requestInfrastructureLease(
          {
            sku: action.sku,
            runtimeMinutes: action.runtimeMinutes,
            path: action.path,
            payload: { notes: action.description },
            walletAddress: address,
          },
          fetcher
        );

        setLeaseStatus(
          `Lease ${response.leaseId} is ${response.status}${
            response.expiresAt ? ` until ${response.expiresAt}` : ""
          }.`
        );
      } catch (error) {
        if (error instanceof PaymentRequiredError) {
          setLeaseStatus(
            "Lease requires payment. Approve the wallet request or connect a wallet."
          );
        } else {
          setLeaseStatus(buildStubbedLeaseMessage(action.title));
        }
        console.warn("Lease request failed", error);
      } finally {
        setPendingLeaseId(null);
      }
    },
    [address, fetcher, pendingLeaseId]
  );

  return (
    <div className="min-h-screen bg-white text-slate-900">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-6 py-10">
        <header className="flex flex-wrap items-start justify-between gap-4 border-b border-orange-100 pb-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-orange-500">
              infra402 // chatbot control plane
            </p>
            <h1 className="text-3xl font-semibold text-slate-900">
              Manage Compute with Chat & x402
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              Backend target: {API_BASE_URL}. Network target:{" "}
              {chain?.name || TARGET_NETWORK_LABEL}.
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            {address && (
              <p className="text-xs font-mono text-slate-500">
                {shortAddress}
              </p>
            )}
            <button
              onClick={address ? disconnectWallet : connectWallet}
              className="rounded-full border border-orange-400 px-5 py-2 text-sm font-semibold text-orange-600 transition hover:bg-orange-50 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isConnecting}
            >
              {address
                ? "Disconnect Wallet"
                : isConnecting
                  ? "Connecting..."
                  : "Connect Wallet"}
            </button>
            {walletError && (
              <p className="text-right text-xs text-red-500">{walletError}</p>
            )}
          </div>
        </header>

        <div className="grid flex-1 gap-8 lg:grid-cols-[1.8fr,1fr]">
          <section className="flex flex-col rounded-2xl border border-orange-100 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-orange-50 px-6 py-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">
                  Chat with the infra steward
                </h2>
                <p className="text-sm text-slate-500">
                  Payments are settled automatically when the backend responds
                  with HTTP 402.
                </p>
              </div>
              <span className="rounded-full bg-orange-100 px-3 py-1 text-xs font-semibold text-orange-600">
                x402 ready
              </span>
            </div>
            <div className="flex-1 space-y-4 overflow-y-auto px-6 py-6">
              {messages.map((message) => (
                <article
                  key={message.id}
                  className={`rounded-xl border border-slate-100 px-4 py-3 text-sm shadow-sm ${messageAccent[message.role]}`}
                >
                  <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
                    <span className="font-semibold uppercase tracking-wide text-slate-700">
                      {message.role}
                    </span>
                    <span>{formatTimestamp(message.timestamp)}</span>
                  </div>
                  <p className="text-slate-800">{message.content}</p>
                </article>
              ))}
            </div>
            <div className="border-t border-orange-50 px-6 py-4">
              <label className="mb-2 block text-sm font-medium text-slate-600">
                Message
              </label>
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="ex: scale the build containers by 3x for 30 minutes"
                rows={3}
                className="w-full rounded-xl border border-orange-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none ring-orange-400 placeholder:text-slate-400 focus:ring-2"
              />
              <div className="mt-3 flex items-center justify-between text-sm text-slate-500">
                <p>
                  Session {sessionId.slice(0, 8)} ·{" "}
                  {address ? "wallet attached" : "wallet not connected"}
                </p>
                <button
                  onClick={handleSendMessage}
                  disabled={isSending || !input.trim()}
                  className="rounded-full bg-orange-500 px-6 py-2 font-semibold text-white transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:bg-orange-200"
                >
                  {isSending ? "Sending…" : "Send"}
                </button>
              </div>
            </div>
          </section>

          <aside className="flex flex-col rounded-2xl border border-orange-100 bg-orange-50/60 p-6 shadow-inner">
            <h2 className="text-lg font-semibold text-slate-900">
              Lease infrastructure
            </h2>
            <p className="mb-4 text-sm text-slate-600">
              Buttons will call your configured backend and allow it to return a
              402 so payments can flow through x402-fetch.
            </p>
            <div className="space-y-4">
              {infraActions.map((action) => (
                <div
                  key={action.id}
                  className="rounded-2xl border border-orange-200 bg-white p-4 shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-base font-semibold text-slate-900">
                        {action.title}
                      </p>
                      <p className="text-sm text-slate-500">
                        {action.description}
                      </p>
                    </div>
                    <span className="rounded-full bg-orange-100 px-3 py-1 text-xs font-semibold text-orange-600">
                      {action.badge}
                    </span>
                  </div>
                  <p className="mt-3 text-sm font-medium text-slate-700">
                    {action.price}
                  </p>
                  <button
                    onClick={() => handleLease(action)}
                    disabled={pendingLeaseId === action.id}
                    className="mt-4 w-full rounded-full bg-orange-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:bg-orange-200"
                  >
                    {pendingLeaseId === action.id
                      ? "Processing…"
                      : "Lease capacity"}
                  </button>
                </div>
              ))}
            </div>
            {leaseStatus && (
              <p className="mt-6 rounded-xl bg-white px-4 py-3 text-sm text-slate-600">
                {leaseStatus}
              </p>
            )}
          </aside>
        </div>
      </div>
    </div>
  );
}
