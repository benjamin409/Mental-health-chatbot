import { useEffect, useState } from "react";

import About from "./components/About.jsx";
import EntryForm from "./components/EntryForm.jsx";
import History from "./components/History.jsx";
import KeepChoice from "./components/KeepChoice.jsx";
import Landing from "./components/Landing.jsx";
import Result from "./components/Result.jsx";
import {
  addVisitEntry, clearVisitEntries, entriesToAdopt, listVisitEntries,
} from "./visitStore.js";

const LockIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
       stroke="currentColor" strokeWidth="2" strokeLinecap="round"
       strokeLinejoin="round" aria-hidden="true">
    <rect x="3" y="11" width="18" height="11" rx="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

// How many entries someone writes before the keep-or-clear question is put to
// them. Asked on arrival it is an abstraction; asked now it is about entries
// they can see.
const ASK_AFTER = 2;

export default function App() {
  const [view, setView] = useState("landing");
  const [tab, setTab] = useState("write");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // null while the question has not been answered, and while it is being
  // fetched. Not keeping is what happens in the meantime.
  const [keep, setKeep] = useState(null);
  const [askLater, setAskLater] = useState(false);
  const [savingChoice, setSavingChoice] = useState(false);
  const [visitCount, setVisitCount] = useState(() => listVisitEntries().length);

  useEffect(() => {
    fetch("/api/session")
      .then((response) => response.json())
      .then((payload) => { if (payload.ok) setKeep(payload.keep); })
      .catch(() => { /* the default, not keeping, already applies */ });
  }, []);

  function handleResult(next, submittedText) {
    setResult(next);
    // An entry the server did not store is held here for the visit instead.
    if (!next.kept) {
      addVisitEntry({
        text: submittedText,
        predictedClass: next.predictedClass,
        confidence: next.confidence,
        uncertain: next.uncertain,
      });
      setVisitCount(listVisitEntries().length);
    }
    setRefreshKey((key) => key + 1);
  }

  async function chooseKeep(value) {
    setSavingChoice(true);
    try {
      const response = await fetch("/api/preferences", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          keep: value,
          // Saying "keep these" means these, not merely the ones that follow.
          adopt: value ? entriesToAdopt() : undefined,
        }),
      });
      const payload = await response.json();
      if (!payload.ok) throw new Error(payload.error?.message);

      setKeep(value);
      if (value) {
        // They are in the database now; the visit copy would only duplicate.
        clearVisitEntries();
        setVisitCount(0);
      }
      setRefreshKey((key) => key + 1);
    } catch {
      setError("Could not save that choice. Nothing has been kept.");
    } finally {
      setSavingChoice(false);
    }
  }

  const askNow = keep === null && !askLater && visitCount >= ASK_AFTER;

  if (view === "landing") {
    return (
      <Landing
        onStart={() => {
          setView("app");
          window.scrollTo({ top: 0, behavior: "smooth" });
        }}
      />
    );
  }

  return (
    <div className="app">
      <header className="masthead">
        <h1>A quiet place to check in</h1>
        <p>
          Write a little about how you have been. You will get a reading of what
          your words suggest, nothing more, and nothing kept from you.
        </p>

        <div className="tabs" role="tablist">
          {[
            ["write", "Write"],
            ["history", "Your entries"],
            ["about", "About this"],
          ].map(([key, label]) => (
            <button
              key={key}
              className="tab"
              role="tab"
              aria-selected={tab === key}
              onClick={() => setTab(key)}
            >
              {label}
            </button>
          ))}
        </div>
      </header>

      {tab === "write" && (
        <>
          <div className="privacy">
            <LockIcon />
            <span>
              <strong>No name, no sign-in, no one watching.</strong>{" "}
              {keep
                ? "Your entries are kept on this computer only, and you can delete them whenever you like."
                : "Nothing you write is saved anywhere — it goes when you close the browser."}
            </span>
          </div>

          <EntryForm
            onResult={handleResult}
            onError={setError}
            busy={busy}
            setBusy={setBusy}
          />

          {error && <div className="notice calm">{error}</div>}
          <Result result={result} />

          {askNow && (
            <KeepChoice
              count={visitCount}
              busy={savingChoice}
              onChoose={chooseKeep}
              onDismiss={() => setAskLater(true)}
            />
          )}
        </>
      )}

      {tab === "history" && (
        <History
          refreshKey={refreshKey}
          keep={keep}
          onChangeKeep={chooseKeep}
          savingChoice={savingChoice}
          onVisitChange={() => setVisitCount(listVisitEntries().length)}
        />
      )}
      {tab === "about" && <About />}

      <footer className="foot">
        This is a screening aid, not a diagnosis.<br />
        If you are struggling, please talk to someone you trust or a health
        professional.{" "}
        <button className="linky" onClick={() => setTab("about")}>
          See who you can call
        </button>
      </footer>
    </div>
  );
}
