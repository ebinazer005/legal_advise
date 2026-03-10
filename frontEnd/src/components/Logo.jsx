import "../styles/Logo.css";

export default function Logo() {
  return (
    <div className="logo">
      <div className="logo-icon">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
            stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          />
        </svg>
      </div>
      <span className="logo-text">Legal Adviser</span>
    </div>
  );
}
