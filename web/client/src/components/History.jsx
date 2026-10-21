import { useEffect, useState } from "react";

import { CLASS_COLOURS, formatWhen } from "../classes.js";
import {
  clearVisitEntries, listVisitEntries, removeVisitEntry,
} from "../visitStore.js";

/**
 * Previous entries.
 *
 * They come from one of two places depending on what the person has asked for.
 * If they have chosen to have their entries kept, the list is read from the
 * database. If they have not, or have not been asked yet, nothing was ever
 * written and the list is the one the browser tab is holding for this visit.
 * The distinction is stated on the page rather than hidden, because a person
 * deciding whether to write honestly is entitled to know which of the two they
 * are looking at.
 *
 * Every entry can be removed, and all of them can be removed at once. Control
 * over what is kept is part of what makes a person willing to write honestly in
 * the first place; a record they cannot delete is a reason not to write.
 *
 * Entries are shown as they were written. Because an entry may run to several
 * paragraphs, a long one is clamped with the rest behind a control, so the list
 * stays readable without hiding anything.
 */
const CLAMP_AT = 220;

export default function History({
  refreshKey, keep, onChangeKeep, savingChoice, onVisitChange,
}) {
  const [entries, setEntries] = useState(null);
  const [confirming, setConfirming] = useState(false);
  const [expanded, setExpanded] = useState(() => new Set());

  const kept = keep === true;

  function toggleExpanded(id) {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function load() {
    if (!kept) {
      setEntries(listVisitEntries());
      return;
    }
    try {
      const response = await fetch("/api/history");
      const payload = await response.json();
      setEntries(payload.ok ? payload.entries : []);
    } catch {
      setEntries([]);
    }
  }

  useEffect(() => { load(); }, [refreshKey, keep]);

  async function removeOne(id) {
    if (kept) await fetch(`/api/history/${id}`, { method: "DELETE" });
    else { removeVisitEntry(id); onVisitChange?.(); }
    load();
  }

  async function removeAll() {
    if (kept) await fetch("/api/history", { method: "DELETE" });
    else { clearVisitEntries(); onVisitChange?.(); }
    setConfirming(false);
    load();
  }

  // The choice is reversible from here, in both directions, at any time. A
  // decision made once after two entries should not bind someone who later
  // moves to a shared computer, or who decides a month of entries would be
  // worth having after all.
  const preference = (
    <p className="history-pref">
      {kept ? (
        <>
          These are saved on this computer.{" "}
          <button
            className="linky"
            disabled={savingChoice}
            onClick={() => onChangeKeep(false)}
          >
            Stop keeping them and delete what is saved
          </button>
        </>
      ) : (
        <>
          Nothing here has been saved anywhere.{" "}
          <button
            className="linky"
            disabled={savingChoice}
            onClick={() => onChangeKeep(true)}
          >
            Keep entries on this computer instead
          </button>
        </>
      )}
    </p>
  );

  if (entries === null) {
    return <div className="card"><div className="empty">Loading…</div></div>;
  }

  if (entries.length === 0) {
    return (
      <div className="card">
        <div className="empty">
          Nothing here yet.<br />
          Anything you write will appear here.
        </div>
        {preference}
      </div>
    );
  }

  return (
    <div className="card">
      {entries.map((entry) => (
        <div className="entry" key={entry.id}>
          <div className="entry-top">
            <span className="chip">
              <span
                className="dot"
                style={{
                  background: entry.uncertain
                    ? "var(--ink-faint)"
                    : CLASS_COLOURS[entry.predictedClass],
                }}
              />
              {entry.uncertain ? "No clear reading" : entry.predictedClass}
              <span style={{ color: "var(--ink-faint)", fontWeight: 400 }}>
                {(entry.confidence * 100).toFixed(0)}%
              </span>
            </span>
            <span className="entry-when">{formatWhen(entry.timestamp)}</span>
          </div>
          <p className="entry-text">
            {entry.text.length > CLAMP_AT && !expanded.has(entry.id)
              ? `${entry.text.slice(0, CLAMP_AT).trimEnd()}…`
              : entry.text}
          </p>
          <div className="entry-actions">
            {entry.text.length > CLAMP_AT && (
              <button className="linky" onClick={() => toggleExpanded(entry.id)}>
                {expanded.has(entry.id) ? "Show less" : "Show all of it"}
              </button>
            )}
            <button className="linky" onClick={() => removeOne(entry.id)}>
              Remove this entry
            </button>
          </div>
        </div>
      ))}

      <div className="history-foot">
        <span className="entry-when">
          {entries.length} {entries.length === 1 ? "entry" : "entries"},{" "}
          {kept
            ? "kept on this computer"
            : "held in this tab and cleared when you close the browser"}
        </span>
        {confirming ? (
          <span style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button className="quiet" onClick={() => setConfirming(false)}>
              Keep them
            </button>
            <button className="quiet" onClick={removeAll}>
              Yes, delete everything
            </button>
          </span>
        ) : (
          <button className="quiet" onClick={() => setConfirming(true)}>
            Delete all entries
          </button>
        )}
      </div>

      {preference}
    </div>
  );
}
