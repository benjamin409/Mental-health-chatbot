/**
 * Landing.jsx
 * -----------
 * The entry point a visitor sees before interacting with the classification
 * interface.
 *
 * The existing app drops the user straight into the text-entry form, which
 * works once someone knows what the system is, but gives a first-time visitor
 * nothing to orient by. This page fills that gap: it explains what the system
 * does, how it works, what it detects, and what it does not store, in the same
 * warm, non-clinical tone the rest of the interface uses.
 *
 * Every section is designed with a defence demo in mind — an examiner reading
 * the screen should be able to see the architecture, the four classes, the
 * privacy model and the headline metrics without opening a terminal.
 */

import { CLASS_COLOURS } from "../classes.js";

const STEPS = [
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"
           strokeLinejoin="round" aria-hidden="true">
        <path d="M12 20h9" />
        <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z" />
      </svg>
    ),
    title: "Write",
    text: "Describe how you have been feeling, in whatever words come naturally. There is no right or wrong way to say it.",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"
           strokeLinejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z" />
      </svg>
    ),
    title: "Analyse",
    text: "Your words are processed using natural language processing and classified by a trained Logistic Regression model.",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"
           strokeLinejoin="round" aria-hidden="true">
        <line x1="9" y1="18" x2="15" y2="18" />
        <line x1="10" y1="22" x2="14" y2="22" />
        <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14" />
      </svg>
    ),
    title: "Understand",
    text: "You receive a reading of what your words suggest, a language pattern, never a diagnosis, along with its confidence.",
  },
];

const CATEGORIES = [
  {
    name: "Normal",
    label: "No clear distress",
    description: "Your writing resembles everyday, non-distressed language.",
    colour: "var(--normal)",
  },
  {
    name: "Depression",
    label: "Low mood",
    description: "Patterns associated with low mood, hopelessness or loss of interest.",
    colour: "var(--depression)",
  },
  {
    name: "Anxiety",
    label: "Worry",
    description: "Patterns associated with worry, restlessness or fear.",
    colour: "var(--anxiety)",
  },
  {
    name: "Stress",
    label: "Pressure",
    description: "Patterns associated with pressure, overload or difficulty coping.",
    colour: "var(--stress)",
  },
];

const MODEL_STATS = [
  { label: "Classifier", value: "Logistic Regression" },
  { label: "Trained on", value: "67,000+ examples" },
  { label: "Tested on", value: "6,881 unseen records" },
  { label: "Accuracy", value: "84.93%" },
  { label: "F1 Score", value: "0.8516 (weighted)" },
];

export default function Landing({ onStart }) {
  return (
    <div className="landing">
      {/* ---------------------------------------------------------- hero */}
      <section className="landing-hero">
        {/* <p className="landing-badge">
          BSc Project · Computer Science · University of Nigeria, Nsukka
        </p> */}
        <h1 className="landing-title">A quiet place to check&nbsp;in</h1>
        <p className="landing-subtitle">
          Write about how you have been feeling. A machine-learning model reads
          the patterns in your words and tells you what it sees honestly,
          privately.
        </p>
        <button className="primary landing-cta" onClick={onStart}>
          Begin
        </button>
        <p className="landing-note">
          No sign-in. No name. Nothing saved unless saved by you.
        </p>
      </section>

      {/* -------------------------------------------------- how it works */}
      <section className="landing-section">
        <h2 className="landing-heading">How it works</h2>
        <div className="landing-steps">
          {STEPS.map((step, i) => (
            <div className="landing-step" key={step.title}>
              <div className="landing-step-icon">{step.icon}</div>
              <div className="landing-step-number">Step {i + 1}</div>
              <h3 className="landing-step-title">{step.title}</h3>
              <p className="landing-step-text">{step.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ------------------------------------------------- what it reads */}
      <section className="landing-section">
        <h2 className="landing-heading">What it detects</h2>
        <p className="landing-section-intro">
          The model classifies your writing into one of four language patterns.
          It reports what your words resemble, never what you have.
        </p>
        <div className="landing-categories">
          {CATEGORIES.map((cat) => (
            <div
              className="landing-category"
              key={cat.name}
              style={{ borderLeftColor: cat.colour }}
            >
              <div className="landing-category-head">
                <span className="dot" style={{ background: cat.colour }} />
                <span className="landing-category-name">{cat.name}</span>
                <span className="landing-category-label">{cat.label}</span>
              </div>
              <p className="landing-category-desc">{cat.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ------------------------------------------------ privacy & trust */}
      <section className="landing-section">
        <div className="landing-privacy-card">
          <div className="landing-privacy-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"
                 strokeLinejoin="round" aria-hidden="true">
              <rect x="3" y="11" width="18" height="11" rx="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </div>
          <h2 className="landing-heading" style={{ marginTop: 0 }}>
            Built for honesty, not surveillance
          </h2>
          <ul className="landing-privacy-list">
            <li>No account, no sign-in, no name collected</li>
            <li>
              Nothing is saved by default. Entries exist only in your browser
              tab and go when you close it
            </li>
            <li>
              You choose whether to keep entries, and you can delete them at any
              time
            </li>
          </ul>
        </div>
      </section>

      {/* ------------------------------------------------ about the model */}
      <section className="landing-section">
        <h2 className="landing-heading">About the model</h2>
        <div className="landing-stats-card">
          <dl className="landing-stats">
            {MODEL_STATS.map(({ label, value }) => (
              <div className="landing-stat" key={label}>
                <dt>{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
          <p className="landing-stats-note">
            The model reads emotional vocabulary. It is not a diagnosis. Where it
            detects distress, it will suggest speaking to someone you trust.
          </p>
        </div>
      </section>

      {/* ------------------------------------------------------ bottom CTA */}
      <section className="landing-section landing-bottom-cta">
        <h2 className="landing-heading">Ready to check in?</h2>
        <button className="primary landing-cta" onClick={onStart}>
          Begin
        </button>
        <p className="landing-note">
          This takes a few minutes. Everything happens on this device.
        </p>
      </section>

      {/* --------------------------------------------------------- footer */}
      <footer className="landing-footer">
        {/* <p>
          A BSc project submitted to the Department of Computer Science,
          <br />
          University of Nigeria, Nsukka.
        </p> */}
        <p>This is a screening aid, not a diagnosis.</p>
      </footer>
    </div>
  );
}
