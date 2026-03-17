export default function HelpTip({ label, text, className = "" }) {
  return (
    <span className={`help-tip ${className}`.trim()}>
      <button className="help-tip__button" type="button" aria-label={label}>
        ?
      </button>
      <span className="help-tip__bubble" role="tooltip">
        {text}
      </span>
    </span>
  );
}
