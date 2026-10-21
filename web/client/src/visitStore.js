/**
 * visitStore.js
 * -------------
 * Where entries live before a person has asked for them to be kept.
 *
 * The default in this system is that nothing is stored. That is implemented
 * literally: until someone opts in, their entries are never sent to the
 * database and exist only in the browser tab in front of them. The claim that
 * they are gone when the browser closes is therefore true by construction, not
 * by a promise to delete something later.
 *
 * `sessionStorage` is used rather than a variable in memory so that a refresh
 * or an accidental navigation does not lose what someone has written. It is
 * scoped to the tab and the browser clears it when the tab closes, which is
 * exactly the lifetime wanted. It never leaves the machine.
 *
 * Every access is guarded: private-browsing modes and browsers configured to
 * block site data throw on access rather than returning empty, and an entry
 * being lost is not a reason for the page to break.
 */

const KEY = "mhms_visit_entries";
const LIMIT = 50;

function read() {
  try {
    const raw = sessionStorage.getItem(KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function write(entries) {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(entries.slice(0, LIMIT)));
  } catch {
    // Storage unavailable or full. The entry is lost when the page reloads,
    // which is the same outcome the person has already been promised.
  }
}

/** SQLite's format, so that one date formatter serves both stores. */
function stamp() {
  return new Date().toISOString().slice(0, 19).replace("T", " ");
}

let counter = 0;

export function listVisitEntries() {
  return read();
}

export function addVisitEntry({ text, predictedClass, confidence, uncertain }) {
  counter += 1;
  const entry = {
    id: `visit-${Date.now()}-${counter}`,
    text,
    predictedClass,
    confidence,
    uncertain,
    timestamp: stamp(),
  };
  write([entry, ...read()]);
  return entry;
}

export function removeVisitEntry(id) {
  write(read().filter((entry) => entry.id !== id));
}

export function clearVisitEntries() {
  try {
    sessionStorage.removeItem(KEY);
  } catch {
    // Nothing to do; see write().
  }
}

/** The payload sent when a person chooses to keep what they have written. */
export function entriesToAdopt() {
  return read().map(({ text, predictedClass, confidence }) => ({
    text, predictedClass, confidence,
  }));
}
