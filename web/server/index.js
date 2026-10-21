/**
 * index.js
 * --------
 * Presentation layer for the Logistic Regression Based Mental Health
 * Monitoring System.
 *
 * Express serves the React interface and exposes a small JSON API to it. It
 * owns the session token and the SQLite database of submissions; it asks the
 * Python inference service for classifications and stores what comes back.
 *
 * Run
 * ---
 *     npm run dev      development: Express on 3000, Vite on 5173
 *     npm run build && npm start     one process on 3000, serving the built
 *                                    interface
 */

import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

import cookieParser from "cookie-parser";
import express from "express";

import {
  HOST, KEEP_COOKIE, LOW_CONFIDENCE_THRESHOLD, PORT, ROOT,
  SESSION_COOKIE, SESSION_MAX_AGE_MS,
} from "./config.js";
import { classify, health, info, ClassifierError } from "./classifier.js";
import {
  countSubmissions, deleteHistory, deleteSubmission, getHistory, saveSubmission,
} from "./db.js";

const app = express();
app.use(express.json({ limit: "64kb" }));
app.use(cookieParser());

// --------------------------------------------------------------------------
// Session
// --------------------------------------------------------------------------
// A random token in a cookie, so a person can see their own previous entries.
// It is not an account. Nothing is asked of the user and nothing identifies
// them; the token can be discarded at any time from the interface.
//
// The cookie's lifetime follows the person's answer to the keep-or-clear
// question. Until they say they want their entries kept, it is a session
// cookie, so it goes when the browser does; only when they opt in does it
// outlive the visit. The two therefore cannot disagree: there is no state in
// which entries are being stored but the cookie that reaches them has expired,
// nor one in which a long-lived cookie survives entries that were never kept.
const keepCookieOptions = (keep) => ({
  httpOnly: true,
  sameSite: "lax",
  ...(keep ? { maxAge: SESSION_MAX_AGE_MS } : {}),
});

app.use((req, res, next) => {
  const answer = req.cookies?.[KEEP_COOKIE];
  req.keepChosen = answer === "1" || answer === "0";
  req.keepEntries = answer === "1";

  let token = req.cookies?.[SESSION_COOKIE];
  if (!token || !/^[a-f0-9]{32}$/.test(token)) {
    token = crypto.randomBytes(16).toString("hex");
    res.cookie(SESSION_COOKIE, token, keepCookieOptions(req.keepEntries));
  }
  req.sessionToken = token;
  next();
});

const fail = (res, status, code, message) =>
  res.status(status).json({ ok: false, error: { code, message } });

// --------------------------------------------------------------------------
// API
// --------------------------------------------------------------------------
app.post("/api/classify", async (req, res) => {
  const text = req.body?.text;
  if (typeof text !== "string" || text.trim() === "") {
    return fail(res, 400, "empty", "Please write something first.");
  }

  let result;
  try {
    // Sent raw. No cleaning happens here - see classifier.js.
    result = await classify(text);
  } catch (error) {
    if (error instanceof ClassifierError) {
      return res.status(error.status).json({
        ok: false,
        error: {
          code: error.code,
          message: error.userFacing
            ? error.message
            : "The classifier is not available at the moment. Your entry has not been saved.",
        },
      });
    }
    console.error(error);
    return fail(res, 500, "server_error", "Something went wrong on our side.");
  }

  const uncertain =
    result.low_confidence || result.confidence < LOW_CONFIDENCE_THRESHOLD;

  // The entry is written to the database only if the person has asked for
  // their entries to be kept. Until then it never leaves the browser tab it
  // was typed in; the interface holds it for the visit and lets it go.
  let submissionId = null;
  if (req.keepEntries) {
    try {
      submissionId = saveSubmission({
        sessionToken: req.sessionToken,
        // The entry as written, so that the person is shown their own words
        // back rather than the lemmatised form the classifier works on.
        text: text.trim(),
        predictedClass: result.predicted_class,
        confidence: result.confidence,
      });
    } catch (error) {
      // A failure to record the entry must not deny the user their result.
      console.error("Could not save submission:", error.message);
    }
  }

  res.json({
    ok: true,
    result: {
      submissionId,
      predictedClass: result.predicted_class,
      confidence: result.confidence,
      probabilities: result.probabilities,
      headline: result.headline,
      message: result.message,
      refer: result.refer,
      referralNote: result.referral_note,
      uncertain,
      modelUsed: result.model_used,
      // The interface needs this to decide whether to hold the entry itself.
      kept: submissionId !== null,
    },
  });
});

// --------------------------------------------------------------------------
// Keeping or clearing
// --------------------------------------------------------------------------
// `keep` is true, false, or null when the question has not yet been put. The
// interface asks once, after a person has written enough for the question to
// mean something, and can be changed from the entries page at any time.
app.get("/api/session", (req, res) => {
  res.json({
    ok: true,
    keep: req.keepChosen ? req.keepEntries : null,
    stored: req.keepEntries ? countSubmissions(req.sessionToken) : 0,
  });
});

app.post("/api/preferences", (req, res) => {
  const keep = req.body?.keep;
  if (typeof keep !== "boolean") {
    return fail(res, 400, "bad_request", "Unknown preference.");
  }

  res.cookie(KEEP_COOKIE, keep ? "1" : "0", keepCookieOptions(keep));
  res.cookie(SESSION_COOKIE, req.sessionToken, keepCookieOptions(keep));

  // Choosing to keep adopts the entries already written during this visit,
  // which the interface has been holding. A person who says "keep these" means
  // these, not merely the ones they write next.
  let adopted = 0;
  if (keep && Array.isArray(req.body.adopt)) {
    for (const item of req.body.adopt.slice(0, 50)) {
      const text = typeof item?.text === "string" ? item.text.trim() : "";
      const predictedClass = item?.predictedClass;
      const confidence = Number(item?.confidence);
      const known = ["Normal", "Depression", "Anxiety", "Stress"];
      if (!text || text.length > 10000 || !known.includes(predictedClass)
          || !Number.isFinite(confidence) || confidence < 0 || confidence > 1) {
        continue;
      }
      try {
        saveSubmission({
          sessionToken: req.sessionToken, text, predictedClass, confidence,
        });
        adopted += 1;
      } catch (error) {
        console.error("Could not adopt entry:", error.message);
      }
    }
  }

  // Choosing not to keep removes anything already stored. The answer applies
  // to what has been written, not only to what comes next.
  const removed = keep ? 0 : deleteHistory(req.sessionToken);

  res.json({ ok: true, keep, adopted, removed });
});

app.get("/api/history", (req, res) => {
  // Nothing is stored for a person who has not opted in, so there is nothing
  // to return. The interface shows what it is holding for the visit instead.
  if (!req.keepEntries) {
    return res.json({ ok: true, keep: false, count: 0, entries: [] });
  }
  const rows = getHistory(req.sessionToken, 50);
  res.json({
    ok: true,
    keep: true,
    count: countSubmissions(req.sessionToken),
    entries: rows.map((row) => ({
      id: row.submission_id,
      text: row.submitted_text,
      predictedClass: row.predicted_class,
      confidence: row.confidence_score,
      // The stored class is whatever scored highest, but an entry the system
      // declined to call at the time must not be listed here as though it had
      // been called. The same threshold decides both, so the history cannot
      // contradict the reading the person was actually shown.
      uncertain: row.confidence_score < LOW_CONFIDENCE_THRESHOLD,
      timestamp: row.timestamp,
    })),
  });
});

app.delete("/api/history", (req, res) => {
  const removed = deleteHistory(req.sessionToken);
  res.json({ ok: true, removed });
});

app.delete("/api/history/:id", (req, res) => {
  const id = Number(req.params.id);
  if (!Number.isInteger(id)) {
    return fail(res, 400, "bad_request", "Unknown entry.");
  }
  const removed = deleteSubmission(req.sessionToken, id);
  res.json({ ok: true, removed });
});

app.get("/api/health", async (_req, res) => {
  const classifierHealth = await health();
  res.json({ ok: true, classifier: classifierHealth });
});

app.get("/api/info", async (_req, res) => {
  try {
    const details = await info();
    res.json({ ok: true, ...details });
  } catch (error) {
    fail(res, 503, "service_unreachable",
      "The classifier is not available at the moment.");
  }
});

// --------------------------------------------------------------------------
// Static interface (production build)
// --------------------------------------------------------------------------
const distDir = path.join(ROOT, "dist");
if (fs.existsSync(distDir)) {
  app.use(express.static(distDir));
  app.get("*", (_req, res) => res.sendFile(path.join(distDir, "index.html")));
} else {
  app.get("/", (_req, res) =>
    res.type("text/plain").send(
      "The interface has not been built yet.\n\n" +
      "  Development : npm run dev   (then open http://localhost:5173)\n" +
      "  Built        : npm run build && npm start\n"
    ));
}

app.listen(PORT, HOST, async () => {
  console.log(`\n  Dashboard        http://${HOST}:${PORT}`);
  const classifierHealth = await health();
  if (classifierHealth.ready) {
    console.log("  Classifier       ready");
  } else {
    console.log("  Classifier       NOT REACHABLE");
    console.log("                   Start it first:  python service/app.py");
  }
  console.log();
});
