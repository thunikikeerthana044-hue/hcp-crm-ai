import React, { useState, useRef, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { sendChatMessage, resetChat } from "../store/chatSlice";
import { fetchInteractions } from "../store/interactionSlice";

export default function ChatInterface({ hcpId }) {
  const dispatch = useDispatch();
  const { messages, status } = useSelector((s) => s.chat);
  const [input, setInput] = useState("");
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    const text = input;
    setInput("");
    await dispatch(sendChatMessage({ message: text, hcpId })).unwrap();
    dispatch(fetchInteractions(hcpId));
  };

  return (
    <div className="chat-panel">
      <div className="chat-intro">
        Tell Nova what happened in plain language — e.g. <em>"Just met Dr. Rao, discussed
        CardioFlex 10mg dosing, she was positive and I dropped 5 samples. Follow up in 2 weeks."</em>
      </div>

      <div className="chat-window">
        {messages.length === 0 && (
          <div className="chat-empty">Start typing below to log this interaction conversationally.</div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble-row ${m.role}`}>
            <div className={`chat-bubble ${m.role}`}>
              {m.text}
              {m.toolCalls && m.toolCalls.length > 0 && (
                <div className="chat-tool-tags">
                  {m.toolCalls.map((tc, j) => (
                    <span className="tool-tag" key={j}>🛠 {tc.tool}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {status === "loading" && (
          <div className="chat-bubble-row agent">
            <div className="chat-bubble agent typing">Nova is thinking…</div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form className="chat-input-row" onSubmit={handleSend}>
        <input
          type="text"
          placeholder="Describe the interaction..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" className="btn-primary" disabled={status === "loading"}>
          Send
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => dispatch(resetChat())}
        >
          New chat
        </button>
      </form>
    </div>
  );
}
