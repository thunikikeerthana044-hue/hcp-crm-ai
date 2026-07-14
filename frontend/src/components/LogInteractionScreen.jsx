import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchInteractions, selectHcp } from "../store/interactionSlice";
import StructuredForm from "./StructuredForm";
import ChatInterface from "./ChatInterface";
import InteractionList from "./InteractionList";
import AddHCPModal from "./AddHCPModal";

export default function LogInteractionScreen() {
  const dispatch = useDispatch();
  const { hcps, selectedHcpId } = useSelector((s) => s.interactions);
  const [mode, setMode] = useState("form"); // "form" | "chat"
  const [isAddingHCP, setIsAddingHCP] = useState(false);

  useEffect(() => {
    if (selectedHcpId) dispatch(fetchInteractions(selectedHcpId));
  }, [dispatch, selectedHcpId]);

  const selectedHcp = hcps.find((h) => h.id === selectedHcpId);

  return (
    <div className="screen">
      <aside className="hcp-sidebar">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
          <div className="hcp-sidebar-label" style={{ marginBottom: 0 }}>Your HCPs</div>
          <button className="btn-primary small" onClick={() => setIsAddingHCP(true)} style={{ padding: "4px 8px", fontSize: "11px" }}>+ Add</button>
        </div>
        <ul className="hcp-list">
          {hcps.map((h) => (
            <li key={h.id}>
              <button
                className={`hcp-list-item ${h.id === selectedHcpId ? "active" : ""}`}
                onClick={() => dispatch(selectHcp(h.id))}
              >
                <span className="hcp-list-name">{h.name}</span>
                <span className="hcp-list-meta">{h.specialty}</span>
              </button>
            </li>
          ))}
          {hcps.length === 0 && (
            <li className="hcp-list-empty">No HCPs yet. Run seed.py in the backend.</li>
          )}
        </ul>
      </aside>

      <main className="screen-main">
        {selectedHcp ? (
          <>
            <div className="hcp-banner">
              <div>
                <h1>{selectedHcp.name}</h1>
                <p className="hcp-banner-sub">
                  {selectedHcp.specialty} &middot; {selectedHcp.institution} &middot; Prefers{" "}
                  {selectedHcp.preferred_channel}
                </p>
              </div>
            </div>

            <div className="mode-switch" role="tablist" aria-label="Log interaction mode">
              <button
                role="tab"
                aria-selected={mode === "form"}
                className={`mode-tab ${mode === "form" ? "active" : ""}`}
                onClick={() => setMode("form")}
              >
                Structured Form
              </button>
              <button
                role="tab"
                aria-selected={mode === "chat"}
                className={`mode-tab ${mode === "chat" ? "active" : ""}`}
                onClick={() => setMode("chat")}
              >
                Chat with Nova (AI)
              </button>
            </div>

            <div className="mode-panel">
              {mode === "form" ? (
                <StructuredForm hcpId={selectedHcp.id} />
              ) : (
                <ChatInterface hcpId={selectedHcp.id} />
              )}
            </div>

            <InteractionList hcpId={selectedHcp.id} />
          </>
        ) : (
          <div className="empty-state">Select an HCP to log an interaction.</div>
        )}
      </main>

      {isAddingHCP && <AddHCPModal onClose={() => setIsAddingHCP(false)} />}
    </div>
  );
}
