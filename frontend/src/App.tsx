import { FormEvent, KeyboardEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { sdk } from "@farcaster/miniapp-sdk";

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
  (import.meta.env.VITE_CHAT_API_BASE as string | undefined)?.replace(/\/$/, "") ||
  "http://localhost:8000";

function randomId() {
  return Math.random().toString(36).slice(2, 10);
}

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: randomId(),
      role: "assistant",
      content:
        "hello! how can I help you?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<Info | null>(null);
  const [isMiniApp, setIsMiniApp] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const messagesRef = useRef<HTMLElement | null>(null);

  const canSend = useMemo(
    () => Boolean(input.trim()) && !loading,
    [input, loading],
  );

  // Initialize Farcaster MiniApp SDK
  // This must be called as soon as possible to hide the splash screen
  useEffect(() => {
    const initMiniApp = async () => {
      try {
        // Check if running inside a Farcaster client
        if (sdk.isInMiniApp()) {
          setIsMiniApp(true);
          // Signal to the client that the app is ready to be displayed
          await sdk.actions.ready();
        }
      } catch (err) {
        console.warn("MiniApp SDK initialization failed:", err);
      }
    };
    initMiniApp();
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
        // ignore; UI will just show placeholders
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [chatApiBase]);

  useEffect(() => {
    if (!messagesRef.current) return;
    messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
  }, [messages, loading]);

  async function sendChat(event?: FormEvent) {
    event?.preventDefault();
    setError(null);
    const content = input.trim();
    if (!content) return;
    if (loading) return;
    const userMessage: ChatMessage = {
      id: randomId(),
      role: "user",
      content,
    };
    const historyForRequest = [...messages, userMessage].map(
      ({ role, content: text }) => ({ role, content: text }),
    );
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${chatApiBase}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: content, history: historyForRequest }),
      });

      if (!response.ok) {
        const body = await response.text();
        throw new Error(`Request failed: ${response.status} ${body}`);
      }

      const data = await response.json();
      const reply = data?.reply ?? "No content returned from the model.";

      const assistantMessage: ChatMessage = {
        id: randomId(),
        role: "assistant",
        content: reply,
      };

      setMessages((prev) => [...prev, assistantMessage]);
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
      inputRef.current?.focus();
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
        content:
          "hello! how can I help you?",
      },
    ]);
    setError(null);
    setInput("");
    inputRef.current?.focus();
  }

  return (
    <div className="page">
      <header className="hero">
        <div>
          <h1>
            Infra402
            {isMiniApp && <span className="miniapp-badge">MiniApp</span>}
          </h1>
          <p className="lede">
            Chat with your agent to explore infra402 :D<br></br>Provision containers and pay using x402! Cheap and accessible~
          </p>
          <div className="meta">
            <span>Base URL: {info?.base_url ?? "…"}</span>
            <span>Model: {info?.model_name ?? "…"}</span>
            <span>API Key: {info?.api_key ?? "…"}</span>
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
              <div className="avatar">{msg.role === "user" ? "You" : "i402"}</div>
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
          {loading && <div className="typing">Model is thinking…</div>}
        </section>

        <form className="composer" onSubmit={sendChat}>
          <textarea
            ref={inputRef}
            placeholder="Ask something..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={3}
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
