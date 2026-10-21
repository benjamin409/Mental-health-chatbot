import { useState } from "react";

/**
 * The entry form.
 *
 * The prompt wording does two jobs at once. It invites a person to write about
 * how they feel rather than what happened to them, which is what the interface
 * is for; and it happens to be what the classifier needs, since the model reads
 * emotional vocabulary and a narrative of events gives it very little to work
 * with. Design and accuracy point the same way here.
 */
export default function EntryForm({ onResult, onError, busy, setBusy }) {
  const [text, setText] = useState("");
  const [notice, setNotice] = useState(null);

  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  const tooShort = words > 0 && words < 5;

  async function submit(event) {
    event.preventDefault();
    if (!text.trim() || busy) return;

    setNotice(null);
    onError(null);
    setBusy(true);
    try {
      const response = await fetch("/api/classify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),   // raw, exactly as written
      });
      const payload = await response.json();

      if (!payload.ok) {
        const fixable = ["text_too_short", "bad_request", "empty"]
          .includes(payload.error.code);
        if (fixable) setNotice(payload.error.message);
        else onError(payload.error.message);
        return;
      }
      // The text is handed back alongside the result because the response
      // deliberately does not echo it. When entries are not being kept, the
      // interface is the only thing holding what was written.
      onResult(payload.result, text.trim());
    } catch {
      onError("Could not reach the server. Is it still running?");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <p className="prompt">How have you been feeling lately?</p>
      <p className="prompt-help">
        Write it however it comes out. There is no right way to say it.
      </p>

      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="Some days I..."
        aria-label="How have you been feeling lately?"
        maxLength={10000}
      />

      <div className="form-foot">
        <span className="wordcount">
          {words === 0
            ? "A few sentences is plenty"
            : tooShort
              ? `${words} word${words === 1 ? "" : "s"} — a little more helps`
              : `${words} words`}
        </span>
        <button className="primary" type="submit" disabled={busy || !text.trim()}>
          {busy && <span className="spinner" />}
          {busy ? "Reading" : "See what it says"}
        </button>
      </div>

      {notice && <div className="notice">{notice}</div>}
    </form>
  );
}
