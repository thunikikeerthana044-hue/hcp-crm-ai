import React, { useEffect } from "react";
import { useDispatch } from "react-redux";
import { fetchHCPs } from "./store/interactionSlice";
import LogInteractionScreen from "./components/LogInteractionScreen";

export default function App() {
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(fetchHCPs());
  }, [dispatch]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-brand">
          <span className="app-header-mark">HCP</span>
          <span className="app-header-title">Field CRM &middot; Log Interaction</span>
        </div>
        <div className="app-header-rep">Demo Rep &middot; Hyderabad Central</div>
      </header>
      <LogInteractionScreen />
    </div>
  );
}
