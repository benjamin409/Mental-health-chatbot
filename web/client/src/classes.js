/**
 * classes.js
 * ----------
 * Presentation details for the four categories.
 *
 * The colours are the ones used in the Chapter Four figures, so a reader
 * moving between the written report and the running system sees the same
 * coding. The wording is deliberately descriptive rather than diagnostic: the
 * system reports what a person's words resemble, never what they have.
 */

export const CLASS_COLOURS = {
  Normal: "var(--normal)",
  Depression: "var(--depression)",
  Anxiety: "var(--anxiety)",
  Stress: "var(--stress)",
};

export const CLASS_ORDER = ["Normal", "Depression", "Anxiety", "Stress"];

export const CLASS_LABEL = {
  Normal: "No clear distress",
  Depression: "Low mood",
  Anxiety: "Worry",
  Stress: "Pressure",
};

export const formatWhen = (value) => {
  // SQLite returns "YYYY-MM-DD HH:MM:SS" in UTC.
  const parsed = new Date(value.replace(" ", "T") + "Z");
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString(undefined, {
    day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
  });
};
