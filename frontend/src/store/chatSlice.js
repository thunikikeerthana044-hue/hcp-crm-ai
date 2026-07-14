import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { api } from "../api/api";

export const sendChatMessage = createAsyncThunk(
  "chat/sendMessage",
  async ({ message, hcpId }, { getState }) => {
    const { sessionId } = getState().chat;
    const res = await api.sendChatMessage(
      { session_id: sessionId, message, rep_id: "demo-rep" },
      hcpId
    );
    return res.data;
  }
);

const chatSlice = createSlice({
  name: "chat",
  initialState: {
    sessionId: null,
    messages: [], // { role: 'user' | 'agent', text, toolCalls? }
    status: "idle",
    lastSavedInteraction: null,
  },
  reducers: {
    resetChat(state) {
      state.sessionId = null;
      state.messages = [];
      state.lastSavedInteraction = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state, action) => {
        state.status = "loading";
        state.messages.push({ role: "user", text: action.meta.arg.message });
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.sessionId = action.payload.session_id;
        state.messages.push({
          role: "agent",
          text: action.payload.reply,
          toolCalls: action.payload.tool_calls,
        });
        if (action.payload.interaction_saved) {
          state.lastSavedInteraction = action.payload.interaction_saved;
        }
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.status = "failed";
        state.messages.push({
          role: "agent",
          text: "Sorry, something went wrong reaching the assistant. Please try again.",
        });
      });
  },
});

export const { resetChat } = chatSlice.actions;
export default chatSlice.reducer;
