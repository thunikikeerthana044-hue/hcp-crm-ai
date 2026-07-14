import React, { useState } from "react";
import { useDispatch } from "react-redux";
import { createInteraction, fetchInteractions } from "../store/interactionSlice";

const INTERACTION_TYPES = ["Visit", "Call", "Email", "Virtual Meeting", "Conference"];
const SENTIMENTS = ["Positive", "Neutral", "Negative"];

const emptyForm = {
  interaction_type: "Visit",
  channel: "In-Person",
  products_discussed: "",
  topics: "",
  sentiment: "Neutral",
  samples_dropped: "",
  key_takeaways: "",
  next_steps: "",
  raw_notes: "",
};

export default function StructuredForm({ hcpId }) {
  const dispatch = useDispatch();
  const [form, setForm] = useState(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const [savedMsg, setSavedMsg] = useState("");

  const handleChange = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setSavedMsg("");
    try {
      await dispatch(createInteraction({ hcp_id: hcpId, ...form })).unwrap();
      setForm(emptyForm);
      setSavedMsg("Interaction logged successfully.");
      dispatch(fetchInteractions(hcpId));
    } catch (err) {
      setSavedMsg("Something went wrong saving this interaction.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="log-form" onSubmit={handleSubmit}>
      <div className="form-grid">
        <label className="field">
          <span>Interaction type</span>
          <select value={form.interaction_type} onChange={handleChange("interaction_type")}>
            {INTERACTION_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Sentiment</span>
          <select value={form.sentiment} onChange={handleChange("sentiment")}>
            {SENTIMENTS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </label>

        <label className="field span-2">
          <span>Products discussed</span>
          <input
            type="text"
            placeholder="e.g. CardioFlex 10mg, CardioFlex 20mg"
            value={form.products_discussed}
            onChange={handleChange("products_discussed")}
          />
        </label>

        <label className="field span-2">
          <span>Topics covered</span>
          <input
            type="text"
            placeholder="e.g. dosing schedule, new trial data"
            value={form.topics}
            onChange={handleChange("topics")}
          />
        </label>

        <label className="field span-2">
          <span>Samples dropped</span>
          <input
            type="text"
            placeholder='e.g. [{"product":"CardioFlex 10mg","qty":5}]'
            value={form.samples_dropped}
            onChange={handleChange("samples_dropped")}
          />
        </label>

        <label className="field span-2">
          <span>Key takeaways</span>
          <textarea
            rows={2}
            placeholder="What did the HCP say or decide?"
            value={form.key_takeaways}
            onChange={handleChange("key_takeaways")}
          />
        </label>

        <label className="field span-2">
          <span>Next steps</span>
          <input
            type="text"
            placeholder="Agreed follow-up action"
            value={form.next_steps}
            onChange={handleChange("next_steps")}
          />
        </label>

        <label className="field span-2">
          <span>Additional notes (optional, fed to AI summary on review)</span>
          <textarea
            rows={3}
            placeholder="Free-text notes from the visit..."
            value={form.raw_notes}
            onChange={handleChange("raw_notes")}
          />
        </label>
      </div>

      <div className="form-actions">
        <button type="submit" disabled={submitting} className="btn-primary">
          {submitting ? "Saving..." : "Log Interaction"}
        </button>
        {savedMsg && <span className="form-status">{savedMsg}</span>}
      </div>
    </form>
  );
}
