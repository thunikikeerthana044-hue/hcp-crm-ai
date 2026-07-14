import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { api } from "../api/api";

export const fetchHCPs = createAsyncThunk("interactions/fetchHCPs", async () => {
  const res = await api.listHCPs();
  return res.data;
});

export const createHCP = createAsyncThunk("interactions/createHCP", async (data) => {
  const res = await api.createHCP(data);
  return res.data;
});

export const fetchInteractions = createAsyncThunk(
  "interactions/fetchInteractions",
  async (hcpId) => {
    const res = await api.listInteractions(hcpId);
    return res.data;
  }
);

export const createInteraction = createAsyncThunk(
  "interactions/createInteraction",
  async (data) => {
    const res = await api.createInteraction(data);
    return res.data;
  }
);

export const updateInteraction = createAsyncThunk(
  "interactions/updateInteraction",
  async ({ id, data }) => {
    const res = await api.updateInteraction(id, data);
    return res.data;
  }
);

export const deleteInteraction = createAsyncThunk(
  "interactions/deleteInteraction",
  async (id) => {
    await api.deleteInteraction(id);
    return id;
  }
);

const interactionSlice = createSlice({
  name: "interactions",
  initialState: {
    hcps: [],
    selectedHcpId: null,
    interactions: [],
    status: "idle", // idle | loading | succeeded | failed
    error: null,
  },
  reducers: {
    selectHcp(state, action) {
      state.selectedHcpId = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchHCPs.fulfilled, (state, action) => {
        state.hcps = action.payload;
        if (!state.selectedHcpId && action.payload.length > 0) {
          state.selectedHcpId = action.payload[0].id;
        }
      })
      .addCase(createHCP.fulfilled, (state, action) => {
        state.hcps.push(action.payload);
        // Automatically select the newly created HCP and sort the list alphabetically
        state.hcps.sort((a, b) => a.name.localeCompare(b.name));
        state.selectedHcpId = action.payload.id;
      })
      .addCase(fetchInteractions.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.interactions = action.payload;
      })
      .addCase(fetchInteractions.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
      })
      .addCase(createInteraction.fulfilled, (state, action) => {
        state.interactions.unshift(action.payload);
      })
      .addCase(updateInteraction.fulfilled, (state, action) => {
        const idx = state.interactions.findIndex((i) => i.id === action.payload.id);
        if (idx !== -1) state.interactions[idx] = action.payload;
      })
      .addCase(deleteInteraction.fulfilled, (state, action) => {
        state.interactions = state.interactions.filter((i) => i.id !== action.payload);
      });
  },
});

export const { selectHcp } = interactionSlice.actions;
export default interactionSlice.reducer;
