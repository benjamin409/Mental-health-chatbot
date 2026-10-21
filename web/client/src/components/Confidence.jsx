import { CLASS_COLOURS, CLASS_ORDER } from "../classes.js";

/**
 * Shows the model's probability across all four categories rather than only
 * the winning one. A person is entitled to see that a result was 51/49 rather
 * than certain, and an examiner is entitled to see that the system does not
 * hide its uncertainty.
 */
export default function Confidence({ probabilities }) {
  if (!probabilities) return null;

  const rows = CLASS_ORDER
    .map((name) => ({ name, value: probabilities[name] ?? 0 }))
    .sort((a, b) => b.value - a.value);

  return (
    <div className="bars">
      <div className="bars-title">How the reading was distributed</div>
      {rows.map(({ name, value }) => (
        <div className="bar-row" key={name}>
          <div className="bar-label">{name}</div>
          <div
            className="bar-track"
            role="img"
            aria-label={`${name}: ${(value * 100).toFixed(1)} percent`}
          >
            <div
              className="bar-fill"
              style={{
                width: `${Math.max(value * 100, value > 0 ? 1.5 : 0)}%`,
                background: CLASS_COLOURS[name],
              }}
            />
          </div>
          <div className="bar-value">{(value * 100).toFixed(0)}%</div>
        </div>
      ))}
    </div>
  );
}
