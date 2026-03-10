import "../styles/StatusBadge.css";

export default function StatusBadge({ running = true }) {
  return (
    <div className="status-badge">
      <div className={`status-dot ${running ? "running" : "stopped"}`} />
      <span className="status-text">{running ? "Running" : "Stopped"}</span>
    </div>
  );
}
