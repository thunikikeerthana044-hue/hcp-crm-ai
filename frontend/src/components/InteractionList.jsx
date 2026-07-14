import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { updateInteraction, deleteInteraction } from "../store/interactionSlice";

function SentimentPill({ sentiment }) {
  const cls = sentiment === "Positive" ? "pos" : sentiment === "Negative" ? "neg" : "neu";
  return <span className={`pill ${cls}`}>{sentiment || "Neutral"}</span>;
}

export default function InteractionList() {
  const dispatch = useDispatch();
  const { interactions } = useSelector((s) => s.interactions);
  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState("");

  const startEdit = (interaction) => {
    setEditingId(interaction.id);
    setEditText(interaction.key_takeaways || "");
  };

  const saveEdit = async (id) => {
    await dispatch(
      updateInteraction({ id, data: { key_takeaways: editText, edit_reason: "Quick edit from history list" } })
    );
    setEditingId(null);
  };

  return (
    <section className="history">
      <h2>Interaction History</h2>
      {interactions.length === 0 && <div className="empty-state small">No interactions logged yet.</div>}
      <ul className="history-list">
        {interactions.map((i) => (
          <li key={i.id} className="history-item">
            <div className="history-item-head">
              <span className="history-type">{i.interaction_type}</span>
              <SentimentPill sentiment={i.sentiment} />
              {i.compliance_flag && <span className="pill flag">⚠ Compliance review</span>}
              <span className="history-date">
                {i.interaction_date ? new Date(i.interaction_date).toLocaleString() : ""}
              </span>
              <span className={`source-tag ${i.source}`}>{i.source === "chat" ? "via Nova" : "via form"}</span>
            </div>

            {i.products_discussed && (
              <p className="history-line"><strong>Products:</strong> {i.products_discussed}</p>
            )}
            {i.ai_summary && <p className="history-line"><strong>AI summary:</strong> {i.ai_summary}</p>}

            {editingId === i.id ? (
              <div className="edit-row">
                <textarea value={editText} onChange={(e) => setEditText(e.target.value)} rows={2} />
                <button className="btn-primary small" onClick={() => saveEdit(i.id)}>Save</button>
                <button className="btn-secondary small" onClick={() => setEditingId(null)}>Cancel</button>
              </div>
            ) : (
              <p className="history-line"><strong>Key takeaways:</strong> {i.key_takeaways}</p>
            )}

            <div className="history-actions">
              {editingId !== i.id && (
                <button className="link-btn" onClick={() => startEdit(i)}>Edit</button>
              )}
              <button className="link-btn danger" onClick={() => dispatch(deleteInteraction(i.id))}>Delete</button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
