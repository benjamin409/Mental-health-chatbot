/**
 * config.js
 * ---------
 * Configuration for the presentation layer.
 *
 * Every value can be overridden by an environment variable, so the same code
 * runs in development and on a demonstration machine without editing.
 */

import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));

export const ROOT = path.resolve(here, "..");

export const PORT = Number(process.env.PORT || 3000);
export const HOST = process.env.HOST || "127.0.0.1";

// The Python inference service. It must be running before this server can
// classify anything; see service/API.md.
export const CLASSIFIER_URL =
  process.env.CLASSIFIER_URL || "http://127.0.0.1:5001";

// How long to wait for a classification before giving up. The service
// normally answers in a few milliseconds; a long wait means it is not there.
export const CLASSIFIER_TIMEOUT_MS = Number(
  process.env.CLASSIFIER_TIMEOUT_MS || 10000
);

export const DATABASE_FILE =
  process.env.DATABASE_FILE || path.join(ROOT, "submissions.db");

// Below this confidence the interface declines to name a single category.
// Kept in step with LOW_CONFIDENCE_THRESHOLD in src/config.py.
export const LOW_CONFIDENCE_THRESHOLD = Number(
  process.env.LOW_CONFIDENCE_THRESHOLD || 0.45
);

// The session token is stored in a cookie so that a person's own entries can
// be shown back to them. It identifies a browser, not a human being: there is
// no account, no name, no email address, and no way to trace a token to a
// person. That is a deliberate design decision, discussed in Chapter Three.
export const SESSION_COOKIE = "mhms_session";
export const SESSION_MAX_AGE_MS = 1000 * 60 * 60 * 24 * 30; // 30 days

// Whether this person has asked for their entries to be kept.
//
// Unset means they have not been asked yet, and the system behaves as though
// the answer were no. That is the safe direction for the default to fail in:
// someone who never reads the question, or who closes the page before it is
// put to them, has nothing written to the database at all.
//
// "Not keeping" is implemented as NOT STORING, rather than as storing and
// deleting later. Nothing is written, so there is nothing to sweep up, nothing
// to leak and nothing to recover — the claim that the entries are gone when the
// browser closes is true by construction rather than by promise. While a person
// has not opted in, their entries exist only in the browser tab in front of
// them.
export const KEEP_COOKIE = "mhms_keep";
