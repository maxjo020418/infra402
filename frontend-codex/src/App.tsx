import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

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
        "Hi! Ask me anything. I'll call the local /chat endpoint on submit.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<Info | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  const canSend = useMemo(
    () => Boolean(input.trim()) && !loading,
    [input, loading],
  );

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

  async function sendChat(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const content = input.trim();
    if (!content) return;
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

  function resetConversation() {
    setMessages([
      {
        id: randomId(),
        role: "assistant",
        content:
          "Starting fresh. Ask me anything and I'll call the configured OpenAI-compatible /chat endpoint.",
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
          <p className="eyebrow">x402 / Vite</p>
          <h1>Chat with your LLM</h1>
          <p className="lede">
            The UI calls your local FastAPI chat endpoint with{" "}
            <code>VITE_CHAT_API_BASE</code> (defaults to http://localhost:8000).
            It also fetches model info from <code>/info</code>.
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
        <section className="messages">
          {messages.map((msg) => (
            <article key={msg.id} className={`message ${msg.role}`}>
              <div className="avatar">{msg.role === "user" ? "You" : "LLM"}</div>
              <div className="bubble">
                {msg.content.split("\n").map((line, idx) => (
                  <p key={idx}>{line}</p>
                ))}
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
