/**
 * classifier.js
 * -------------
 * Client for the Python inference service.
 *
 * This is the only place in the presentation layer that knows the service
 * exists. Two rules are enforced here:
 *
 *   1. The text is sent RAW. It is not trimmed, lowercased, stripped or
 *      cleaned in any way. All pre-processing happens inside the service,
 *      using the identical pipeline that produced the training features. Any
 *      cleaning performed here would break that correspondence and quietly
 *      degrade every prediction.
 *
 *   2. Errors are translated into two kinds: those the user can act on (their
 *      entry was too short) and those they cannot (the service is down). The
 *      interface shows the first as written and the second as a neutral
 *      notice, never a stack trace.
 */

import { CLASSIFIER_TIMEOUT_MS, CLASSIFIER_URL } from "./config.js";

export class ClassifierError extends Error {
  constructor(message, { code, status, userFacing }) {
    super(message);
    this.name = "ClassifierError";
    this.code = code;
    this.status = status;
    this.userFacing = userFacing;
  }
}

const USER_FIXABLE = new Set(["text_too_short", "bad_request"]);

async function call(pathname, { method = "GET", body } = {}) {
  let response;
  try {
    response = await fetch(`${CLASSIFIER_URL}${pathname}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(CLASSIFIER_TIMEOUT_MS),
    });
  } catch (cause) {
    throw new ClassifierError(
      "The classifier is not responding. It may not be running.",
      { code: "service_unreachable", status: 503, userFacing: false }
    );
  }

  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new ClassifierError("The classifier returned an unreadable response.",
      { code: "bad_response", status: 502, userFacing: false });
  }

  if (!payload.ok) {
    const code = payload.error?.code ?? "classification_failed";
    throw new ClassifierError(
      payload.error?.message ?? "The classifier could not handle that entry.",
      { code, status: response.status, userFacing: USER_FIXABLE.has(code) }
    );
  }

  return payload;
}

/** Classify one entry. `text` must be exactly what the user typed. */
export async function classify(text) {
  const payload = await call("/classify", { method: "POST", body: { text } });
  return payload.result;
}

/** Ask the service whether it is up. Used at start-up and by /api/health. */
export async function health() {
  try {
    const response = await fetch(`${CLASSIFIER_URL}/health`, {
      signal: AbortSignal.timeout(3000),
    });
    const payload = await response.json();
    return { reachable: true, ready: payload.ok === true, status: payload.status };
  } catch {
    return { reachable: false, ready: false, status: "unreachable" };
  }
}

/** Describe the deployed model, for the "about this system" page. */
export async function info() {
  const payload = await call("/info");
  return { model: payload.model, constraints: payload.constraints };
}
