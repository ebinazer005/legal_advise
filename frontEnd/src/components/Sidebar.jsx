import "../styles/Sidebar.css";

export default function Sidebar({ active, onSelect }) {
const navItems = ["Ingestion", "Retrieval" , "Client_details"];

  return (
    <aside className="sidebar">
        <div className="logo">
    <span className="logo-text">legal Advisor </span>
    </div>
      <nav className="nav-list">
        {navItems.map(item => (
          <div
            key={item}
            className={`nav-item ${active === item ? "active" : ""}`}
            onClick={() => onSelect(item)}
          >
            {item}
          </div>
        ))}
      </nav>
    </aside>
  );
}
