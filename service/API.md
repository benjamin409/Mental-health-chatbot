# Classification API — interface specification

Version 1.0 · Middle layer of the system architecture described in Chapter
Three, §3.2.2.

The presentation layer (Node/Express) obtains classifications from this service
over HTTP. It does not load the model, and it does not process text.

```
  Browser  ──►  Express (Node)  ──►  Flask inference service (Python)
                    │                          │
                    │                          └─ TF-IDF vectorizer
                    │                             Logistic Regression model
                    └─ SQLite: sessions, submission history
```

**Base URL (development):** `http://127.0.0.1:5001`

---

## Contract rules

These are the guarantees each side relies on. They should be quoted in the
system-implementation section of Chapter Four.

1. **The client sends raw text.** All lowercasing, noise removal,
   tokenization, stop-word removal and lemmatization happen inside this
   service, using the identical pipeline that produced the training features.
   If the client cleans text before sending it, training and inference stop
   corresponding and every prediction silently degrades.
2. **The service is stateless.** It stores nothing and issues no session
   identifiers. Session tokens, submission history and the SQLite database
   belong to the presentation layer.
3. **Every response is JSON**, including every error. The client never has to
   parse an HTML error page.
4. **The model loads once**, at service start-up, not per request.
5. **Predictions are deterministic.** The same text always yields the same
   class and the same confidence.

---

## Endpoints

### `GET /health`

Liveness probe. Call it at start-up, and before a demonstration.

**200**
```json
{ "ok": true, "status": "ready", "api_version": "1.0" }
```

**503** — the model failed to load; `status` is `"model_unavailable"`.

---

### `GET /info`

Describes the deployed model. Useful for an "About this system" page and as an
appendix screenshot.

**200**
```json
{
  "ok": true,
  "api_version": "1.0",
  "model": {
    "name": "Logistic Regression",
    "classes": ["Anxiety", "Depression", "Normal", "Stress"],
    "trained_at": "2026-08-20 08:36:01",
    "vocabulary_size": 15000,
    "train_records": 67343,
    "test_records": 6881,
    "length_bias_correction": true,
    "test_accuracy": 0.8493,
    "test_f1_weighted": 0.8516
  },
  "constraints": {
    "min_words": 5,
    "max_characters": 10000,
    "max_batch_size": 50,
    "low_confidence_threshold": 0.45
  }
}
```

---

### `POST /classify`

Classify a single submission.

**Request**
```json
{ "text": "I keep worrying about everything and my heart races whenever my phone rings" }
```

**200**
```json
{
  "ok": true,
  "api_version": "1.0",
  "request_id": "644d6606",
  "result": {
    "clean_text": "keep worry everything my heart race whenever my phone ring",
    "predicted_class": "Anxiety",
    "confidence": 0.9742,
    "probabilities": {
      "Anxiety": 0.9742,
      "Stress": 0.0122,
      "Depression": 0.0106,
      "Normal": 0.0029
    },
    "headline": "Language consistent with anxious expression",
    "message": "Your entry contains wording commonly associated with worry, restlessness, fear or physical tension. This is a language pattern, not a diagnosis.",
    "refer": true,
    "low_confidence": false,
    "referral_note": "Consider speaking with someone you trust, or with a mental health professional. This system is a first-pass screening aid and does not provide a clinical diagnosis.",
    "model_used": "Logistic Regression"
  }
}
```

#### Result fields

| Field             | Type            | Meaning |
|-------------------|-----------------|---------|
| `predicted_class` | string          | One of `Normal`, `Depression`, `Anxiety`, `Stress` |
| `confidence`      | float 0–1       | Probability of the predicted class. Store in `confidence_score` |
| `probabilities`   | object          | All four classes, highest first. Sums to 1. Drives the confidence display |
| `clean_text`      | string          | The text after pre-processing — what the model actually read. The client stores the raw entry in `submitted_text`, not this |
| `headline`        | string          | Short heading to show the user |
| `message`         | string          | One-paragraph explanation of the result |
| `refer`           | boolean         | `true` for any distress class — show the referral prompt |
| `low_confidence`  | boolean         | `true` when confidence < 0.45; the entry matches no class clearly |
| `referral_note`   | string \| null  | Referral wording, or `null` when `refer` is `false` |
| `model_used`      | string          | Name of the selected classifier |
| `request_id`      | string          | Correlates a client log line with a server log line |

The raw submitted text is **not** echoed back. The client already holds it and
is responsible for storing it.

#### Failures

| Status | `error.code`            | Cause |
|-------:|-------------------------|-------|
| 400    | `bad_request`           | `text` missing, not a string, or over 10,000 characters |
| 422    | `text_too_short`        | Fewer than 5 words. Response includes `min_words` |
| 500    | `classification_failed` | Unexpected server-side failure |
| 503    | `model_unavailable`     | The model is not loaded |

All errors share one shape:

```json
{ "ok": false, "error": { "code": "text_too_short", "message": "Please write at least 5 words so the system has enough to work with.", "min_words": 5 } }
```

The client should surface `error.message` directly — the wording is written for
the end user, not for a developer.

---

### `POST /classify/batch`

Classify up to 50 submissions in one call. Used for demonstrations and for the
evaluation table in Chapter Four, not by the normal user flow.

**Request**
```json
{ "texts": ["first entry ...", "second entry ..."] }
```

**200** — one entry per item, in the order submitted. An invalid item fails on
its own without failing the batch.

```json
{
  "ok": true,
  "count": 2,
  "results": [
    { "index": 0, "ok": true,  "result": { "predicted_class": "Depression", "confidence": 0.822, "...": "..." } },
    { "index": 1, "ok": false, "error": { "code": "text_too_short", "message": "..." } }
  ]
}
```

Batches over 50 items return **400** `batch_too_large`.

---

## Calling the service from Express

```js
const SERVICE_URL = process.env.CLASSIFIER_URL || "http://127.0.0.1:5001";

async function classify(text) {
  const response = await fetch(`${SERVICE_URL}/classify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),          // raw text — never pre-cleaned
    signal: AbortSignal.timeout(10000)
  });

  const body = await response.json();
  if (!body.ok) {
    const err = new Error(body.error.message);
    err.code = body.error.code;
    err.status = response.status;
    throw err;                                // 422 → show to the user
  }                                           // 503 → "service unavailable"
  return body.result;
}
```

Map `error.code` onto the interface as follows: `text_too_short` and
`bad_request` are the user's to fix and their `message` should be displayed as
written; `model_unavailable` and `classification_failed` are the system's fault
and should produce a neutral "the classifier is not responding" notice rather
than a stack trace.

---

## Running the service

```bash
python service/app.py                    # 127.0.0.1:5001
PORT=8000 python service/app.py          # different port
```

For a more realistic deployment:

```bash
gunicorn --workers 1 --bind 127.0.0.1:5001 service.app:app
```

One worker is deliberate — each worker loads its own copy of the model.

**Bind to `127.0.0.1`, not `0.0.0.0`.** The service has no authentication; it
is meant to be reachable only by the Express process on the same machine.

### Verification

```bash
python service/app.py         # terminal 1
python service/test_api.py    # terminal 2
```

40 checks covering every endpoint, every documented error path, batch
behaviour and determinism. All pass as of 20 August 2026.
