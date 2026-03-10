import "../styles/TopBar.css";

const ACTIONS = [
  { icon: "↻", label: "Refresh" },
  { icon: "⤢", label: "Expand"  },
  { icon: "⋮", label: "More"    },
];

export default function TopBar({ onRefresh }) {
  const handlers = { Refresh: onRefresh, Expand: () => {}, More: () => {} };

  return (
    <div className="top-bar">
      {ACTIONS.map(({ icon, label }) => (
        <button
          key={label}
          className="top-bar-btn"
          title={label}
          onClick={handlers[label]}
        >
          {icon}
        </button>
      ))}
    </div>
  );
}
