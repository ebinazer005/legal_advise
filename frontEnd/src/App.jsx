import { useState } from "react";
import Sidebar from "./components/Sidebar";
import RetrievalPanel   from "./components/RetrievalPanel";
import IngestionPanel   from "./components/IngestionPanel";
import HearingPanel from "./components/HearingPanel";
import "./styles/global.css";

export default function App() {
  const [activeNav, setActiveNav] = useState("Retrieval");

  const panels = {
    Retrieval:   <RetrievalPanel />,
    Ingestion:   <IngestionPanel />,
    Client_details : <HearingPanel /> 

  };

  return (
    <div className="app">
      <Sidebar active={activeNav} onSelect={setActiveNav} />
      <div className="main-content">
        {panels[activeNav]}
      </div>
    </div>
  );
}
