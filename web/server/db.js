/**
 * db.js
 * -----
 * Data layer: the SQLite database of submissions.
 *
 * The schema is exactly the one specified in Chapter Three, §3.3.6. The
 * presentation layer owns this database; the inference service is stateless
 * and stores nothing.
 *
 * On the driver: Node.js ships SQLite in its standard library as `node:sqlite`
 * from version 22.5 onwards. Using it means the project has no native
 * dependency to compile, which matters on Windows, where building one requires
 * the Visual Studio C++ toolchain. On older versions of Node the module is
 * absent and the code falls back to `better-sqlite3` if it happens to be
 * installed. Either way the rest of the application sees the same interface.
 *
 * Note on what is stored: `submitted_text` holds the entry AS THE PERSON WROTE
 * IT. An earlier version stored the cleaned, lemmatised form instead, on the
 * reasoning that keeping less of what someone wrote is the safer default for a
 * system asking people to disclose distress. That reasoning was sound and the
 * result was still wrong: the entries page then showed a person their own words
 * back as "not sleep properly nothing interest me anymore feel empty", which
 * reads as a fault in the software and undermines exactly the trust the
 * interface is built to earn.
 *
 * The privacy guarantee does not rest on mangling the text. It rests on there
 * being no account, no name and no identifier of any kind beyond an opaque
 * session token, and on every entry being deletable by the person who wrote it,
 * individually or all at once. Those hold whichever form is stored.
 */

import { DATABASE_FILE } from "./config.js";

// --------------------------------------------------------------------------
// Driver selection
// --------------------------------------------------------------------------
async function openDatabase() {
  try {
    const { DatabaseSync } = await import("node:sqlite");
    const handle = new DatabaseSync(DATABASE_FILE);
    return { handle, driver: "node:sqlite" };
  } catch {
    try {
      const { default: Database } = await import("better-sqlite3");
      return { handle: new Database(DATABASE_FILE), driver: "better-sqlite3" };
    } catch {
      throw new Error(
        "No SQLite driver available. Use Node.js 22.5 or later, which " +
        "includes SQLite in its standard library, or install better-sqlite3."
      );
    }
  }
}

const { handle: db, driver } = await openDatabase();
export const DB_DRIVER = driver;

db.exec("PRAGMA journal_mode = WAL");

db.exec(`
  CREATE TABLE IF NOT EXISTS submissions (
    submission_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    session_token    TEXT    NOT NULL,
    submitted_text   TEXT    NOT NULL,
    predicted_class  TEXT    NOT NULL,
    confidence_score REAL    NOT NULL,
    timestamp        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
  );

  CREATE INDEX IF NOT EXISTS idx_submissions_session
    ON submissions (session_token, submission_id DESC);
`);

// Positional parameters are used throughout: both drivers support them
// identically, whereas named-parameter syntax differs between them.
const insertStatement = db.prepare(`
  INSERT INTO submissions
    (session_token, submitted_text, predicted_class, confidence_score, timestamp)
  VALUES (?, ?, ?, ?, datetime('now'))
`);

const historyStatement = db.prepare(`
  SELECT submission_id, submitted_text, predicted_class, confidence_score,
         timestamp
    FROM submissions
   WHERE session_token = ?
   ORDER BY submission_id DESC
   LIMIT ?
`);

const countStatement = db.prepare(
  `SELECT COUNT(*) AS n FROM submissions WHERE session_token = ?`
);

const deleteAllStatement = db.prepare(
  `DELETE FROM submissions WHERE session_token = ?`
);

const deleteOneStatement = db.prepare(
  `DELETE FROM submissions WHERE session_token = ? AND submission_id = ?`
);

export function saveSubmission({ sessionToken, text, predictedClass,
                                 confidence }) {
  const result = insertStatement.run(
    sessionToken, text, predictedClass, confidence
  );
  return Number(result.lastInsertRowid);
}

export function getHistory(sessionToken, limit = 50) {
  // node:sqlite returns null-prototype objects; spread them into plain ones so
  // downstream code and JSON serialisation behave predictably.
  return historyStatement.all(sessionToken, limit).map((row) => ({ ...row }));
}

export function countSubmissions(sessionToken) {
  return Number(countStatement.get(sessionToken).n);
}

/** Delete every entry belonging to this session. */
export function deleteHistory(sessionToken) {
  return Number(deleteAllStatement.run(sessionToken).changes);
}

/** Delete a single entry belonging to this session. */
export function deleteSubmission(sessionToken, submissionId) {
  return Number(deleteOneStatement.run(sessionToken, submissionId).changes);
}

export default db;
