import "../styles/Controls.css";

export default function NumberStepper({ label, value, onChange, tooltip }) {
  return (
    <div className="stepper-wrapper">
      <div className="param-label-row">
        <div className="param-label">
          <span>{label}</span>
          <span className="tooltip-icon" title={tooltip}>?</span>
        </div>
      </div>
      <div className="stepper-control">
        <span className="stepper-value">{value}</span>
        <button className="stepper-btn" onClick={() => onChange(Math.max(1, value - 1))}>−</button>
        <button className="stepper-btn" onClick={() => onChange(value + 1)}>+</button>
      </div>
    </div>
  );
}
