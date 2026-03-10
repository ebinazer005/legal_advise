import "../styles/Controls.css";

export default function SliderControl({ label, value, min, max, step, onChange, tooltip }) {
  const pct = ((value - min) / (max - min)) * 100;

  return (
    <div className="slider-wrapper">
      <div className="param-label-row">
        <div className="param-label">
          <span>{label}</span>
          <span className="tooltip-icon" title={tooltip}>?</span>
        </div>
        <span className="param-value">{value.toFixed(2)}</span>
      </div>

      <div className="slider-track">
        <div className="slider-fill" style={{ width: `${pct}%` }} />
        <input
          className="slider-input"
          type="range"
          min={min} max={max} step={step} value={value}
          onChange={e => onChange(parseFloat(e.target.value))}
        />
        <div className="slider-thumb" style={{ left: `${pct}%` }} />
      </div>

      <div className="slider-range-labels">
        <span className="slider-range-label">{min.toFixed(2)}</span>
        <span className="slider-range-label">{max.toFixed(2)}</span>
      </div>
    </div>
  );
}
