import axios from "axios";

const client = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

export const api = {
  // HCPs
  listHCPs: () => client.get("/api/hcps/"),
  createHCP: (data) => client.post("/api/hcps/", data),

  // Interactions
  listInteractions: (hcpId) =>
    client.get("/api/interactions/", { params: hcpId ? { hcp_id: hcpId } : {} }),
  createInteraction: (data) => client.post("/api/interactions/", data),
  updateInteraction: (id, data) => client.put(`/api/interactions/${id}`, data),
  deleteInteraction: (id) => client.delete(`/api/interactions/${id}`),

  // Chat agent
  sendChatMessage: (payload, hcpId) =>
    client.post("/api/chat/message", payload, { params: hcpId ? { hcp_id: hcpId } : {} }),
};

export default client;
