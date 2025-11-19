"use client";

import { useState } from "react";
import { useX402Fetch } from "../hooks/useX402Fetch";

export default function Home() {
  const [messages, setMessages] = useState<
    { role: "user" | "assistant"; content: string }[]
  >([]);
  const [input, setInput] = useState("");
  const fetchWithPayment = useX402Fetch();

  const handleSend = async () => {
    if (input.trim() === "") return;

    const newMessages = [...messages, { role: "user" as const, content: input }];
    setMessages(newMessages);
    setInput("");

    // Mock assistant response
    setTimeout(() => {
      setMessages((prevMessages) => [
        ...prevMessages,
        { role: "assistant" as const, content: "This is a mock response." },
      ]);
    }, 1000);
  };

  const handleLease = async (tier: string) => {
    try {
      const response = await fetchWithPayment("http://localhost:4021/premium/content");
      if (response.ok) {
        const content = await response.text();
        console.log(`Successfully leased ${tier}:`, content);
        alert(`Successfully leased ${tier}! Check the console for content.`);
      } else {
        console.error(`Failed to lease ${tier}:`, response);
        alert(`Failed to lease ${tier}. Status: ${response.status}`);
      }
    } catch (error) {
      console.error(`Error leasing ${tier}:`, error);
      alert(`Error leasing ${tier}. See console for details.`);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-white text-gray-800">
      <header className="flex justify-between items-center p-4 border-b">
        <h1 className="text-2xl font-bold text-orange-500">Infra402</h1>
        <reown-button />
      </header>

      <main className="flex-1 flex flex-col p-4">
        <div className="flex-1 flex flex-col-reverse overflow-y-auto p-4 space-y-4 space-y-reverse bg-orange-50 rounded-lg">
          {messages.slice().reverse().map((msg, index) => (
            <div
              key={index}
              className={`p-2 rounded-lg ${
                msg.role === "user" ? "bg-orange-200 self-end" : "bg-orange-100 self-start"
              }`}
            >
              <p className="text-sm">{msg.content}</p>
            </div>
          ))}
        </div>
        <div className="mt-4 flex">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            className="flex-1 p-2 border rounded-l-lg focus:ring-orange-500 focus:border-orange-500"
            placeholder="Ask about infrastructure..."
          />
          <button
            onClick={handleSend}
            className="px-4 py-2 bg-orange-500 text-white rounded-r-lg hover:bg-orange-600"
          >
            Send
          </button>
        </div>
      </main>

      <section className="p-4 border-t">
        <h2 className="text-xl font-semibold mb-2 text-gray-800">Lease Infrastructure</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => handleLease("Small VM")}
            className="px-4 py-2 bg-white border border-orange-500 text-orange-500 rounded-lg hover:bg-orange-50"
          >
            Lease Small VM ($0.01)
          </button>
          <button
            onClick={() => handleLease("Large Container")}
            className="px-4 py-2 bg-white border border-orange-500 text-orange-500 rounded-lg hover:bg-orange-50"
          >
            Lease Large Container ($0.01)
          </button>
        </div>
      </section>
    </div>
  );
}
