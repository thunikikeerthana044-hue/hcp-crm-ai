import React, { useState } from "react";
import { useDispatch } from "react-redux";
import { createHCP } from "../store/interactionSlice";

export default function AddHCPModal({ onClose }) {
  const dispatch = useDispatch();
  const [form, setForm] = useState({
    name: "",
    specialty: "",
    institution: "",
    email: "",
    phone: "",
    territory: "",
    preferred_channel: "In-Person",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) {
      setError("Name is required");
      return;
    }
    
    setSubmitting(true);
    setError(null);
    try {
      await dispatch(createHCP(form)).unwrap();
      onClose();
    } catch (err) {
      setError("Failed to create HCP. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Add New HCP</h2>
        <form className="log-form" onSubmit={handleSubmit}>
          <div className="form-grid">
            <label className="field span-2">
              <span>Name *</span>
              <input
                type="text"
                placeholder="e.g. Dr. Sarah Jenkins"
                value={form.name}
                onChange={handleChange("name")}
                required
              />
            </label>
            
            <label className="field">
              <span>Specialty</span>
              <input
                type="text"
                placeholder="e.g. Neurology"
                value={form.specialty}
                onChange={handleChange("specialty")}
              />
            </label>
            
            <label className="field">
              <span>Institution</span>
              <input
                type="text"
                placeholder="e.g. City General"
                value={form.institution}
                onChange={handleChange("institution")}
              />
            </label>
            
            <label className="field">
              <span>Email</span>
              <input
                type="email"
                placeholder="doctor@example.com"
                value={form.email}
                onChange={handleChange("email")}
              />
            </label>
            
            <label className="field">
              <span>Phone</span>
              <input
                type="tel"
                placeholder="555-0123"
                value={form.phone}
                onChange={handleChange("phone")}
              />
            </label>
            
            <label className="field">
              <span>Territory</span>
              <input
                type="text"
                placeholder="e.g. North West"
                value={form.territory}
                onChange={handleChange("territory")}
              />
            </label>
            
            <label className="field">
              <span>Preferred Channel</span>
              <select value={form.preferred_channel} onChange={handleChange("preferred_channel")}>
                <option value="In-Person">In-Person</option>
                <option value="Virtual">Virtual</option>
                <option value="Phone">Phone</option>
                <option value="Email">Email</option>
              </select>
            </label>
          </div>
          
          {error && <div className="form-status">{error}</div>}
          
          <div className="form-actions" style={{ justifyContent: "flex-end", marginTop: "24px" }}>
            <button type="button" className="btn-secondary" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? "Saving..." : "Add HCP"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
