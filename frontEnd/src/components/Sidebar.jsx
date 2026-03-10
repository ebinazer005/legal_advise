import Logo from "./Logo";
import { NAV_ITEMS } from "./constants";
import "../styles/Sidebar.css";

export default function Sidebar({ active, onSelect }) {
  return (
    <aside className="sidebar">
      <Logo />
      <nav className="nav-list">
        {NAV_ITEMS.map(item => (
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
