"""
service/app.py
--------------
Inference service for the Logistic Regression Based Mental Health Monitoring
System.

This is the middle layer of the three-layer architecture described in Chapter
Three. It exposes the trained classifier over HTTP as a small JSON API so that
the presentation layer - an Express/Node application - can obtain a
classification without needing to load a scikit-learn model itself.

Design rules enforced here:

  1. The model and vectorizer are loaded ONCE, at start-up, not per request.
  2. ALL text pre-processing happens inside this service. The client sends raw
     text and nothing else. Any cleaning performed on the client would break
     the correspondence between training and inference and silently degrade
     every prediction.
  3. The service is stateless. It stores nothing. Session tokens, submission
     history and the SQLite database are the responsibility of the
     presentation layer.
  4. Every response - success or failure - is JSON with a consistent shape, so
     the client never has to parse an HTML error page.

Run
---
    python service/app.py                 # 127.0.0.1:5001
    HOST=0.0.0.0 PORT=8000 python service/app.py

For anything beyond local development, run it behind a WSGI server:

    gunicorn --workers 1 --bind 127.0.0.1:5001 service.app:app

One worker is sufficient and is deliberate: each worker loads its own copy of
the model into memory.
"""

from __future__ import annotations

import logging
import os
import sys
import time
import uuid
from pathlib import Path

from flask import Flask, g, jsonify, request

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "src"))

from config import LOW_CONFIDENCE_THRESHOLD, MIN_WORDS_FOR_PREDICTION, TARGET_CLASSES  # noqa: E402
from predict import InsufficientTextError, MentalHealthClassifier  # noqa: E402

API_VERSION = "1.0"
MAX_TEXT_LENGTH = 10_000        # characters accepted in a single submission
MAX_BATCH_SIZE = 50

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("mhms.service")

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# --------------------------------------------------------------------------
# Start-up: load the model once
# --------------------------------------------------------------------------
classifier: MentalHealthClassifier | None = None
startup_error: str | None = None

try:
    _t0 = time.time()
    classifier = MentalHealthClassifier()
    log.info("Model loaded: %s (%.2fs)", classifier.model_name, time.time() - _t0)
    log.info("Classes: %s", ", ".join(classifier.classes))
    if classifier.version_warning:
        log.warning(classifier.version_warning)
except Exception as exc:                                  # pragma: no cover
    startup_error = str(exc)
    log.error("Model could not be loaded: %s", exc)
    log.error("Run 'python src/prepare_data.py' then 'python src/train.py' first.")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def error(code: str, message: str, status: int, **extra):
    """Build the single error shape used by every failure path."""
    payload = {"ok": False, "error": {"code": code, "message": message}}
    if extra:
        payload["error"].update(extra)
    return jsonify(payload), status


def require_model():
    """Return an error response if the model is unavailable, else None."""
    if classifier is None:
        return error(
            "model_unavailable",
            "The classification model is not loaded on the server.",
            503,
            detail=startup_error or "unknown",
        )
    return None


def extract_text(payload) -> str:
    """Pull the 'text' field out of a JSON body, raising ValueError if absent."""
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")
    if "text" not in payload:
        raise ValueError("Request body must contain a 'text' field.")
    text = payload["text"]
    if not isinstance(text, str):
        raise ValueError("The 'text' field must be a string.")
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(
            f"The 'text' field exceeds the {MAX_TEXT_LENGTH:,}-character limit.")
    return text


# --------------------------------------------------------------------------
# Request logging
# --------------------------------------------------------------------------
@app.before_request
def _start_timer():
    g.request_id = uuid.uuid4().hex[:8]
    g.started = time.time()


@app.after_request
def _log_request(response):
    if request.path != "/health":                # health checks are noisy
        log.info("%s  %s %s -> %s  (%.0f ms)",
                 getattr(g, "request_id", "--------"),
                 request.method, request.path, response.status_code,
                 (time.time() - getattr(g, "started", time.time())) * 1000)
    return response


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------
@app.get("/health")
def health():
    """Liveness probe. The Node layer calls this at start-up and before demos."""
    return jsonify({
        "ok": classifier is not None,
        "status": "ready" if classifier is not None else "model_unavailable",
        "api_version": API_VERSION,
    }), (200 if classifier is not None else 503)


@app.get("/info")
def info():
    """Describe the deployed model. Useful for the appendix and for the UI."""
    guard = require_model()
    if guard:
        return guard

    meta = classifier.metadata
    results = meta.get("results", {}).get(classifier.model_name, {})
    return jsonify({
        "ok": True,
        "api_version": API_VERSION,
        "model": {
            "name": classifier.model_name,
            "classes": classifier.classes,
            "trained_at": meta.get("trained_at"),
            "vocabulary_size": meta.get("vocabulary_size"),
            "train_records": meta.get("train_records"),
            "test_records": meta.get("test_records"),
            "length_bias_correction": meta.get("augmented_training"),
            "test_accuracy": round(results.get("accuracy", 0), 4) or None,
            "test_f1_weighted": round(results.get("f1_weighted", 0), 4) or None,
        },
        "constraints": {
            "min_words": MIN_WORDS_FOR_PREDICTION,
            "max_characters": MAX_TEXT_LENGTH,
            "max_batch_size": MAX_BATCH_SIZE,
            "low_confidence_threshold": LOW_CONFIDENCE_THRESHOLD,
        },
    })


@app.post("/classify")
def classify():
    """Classify a single free-text submission.

    Request : {"text": "..."}
    Response: {"ok": true, "result": {...}}
    """
    guard = require_model()
    if guard:
        return guard

    try:
        text = extract_text(request.get_json(silent=True))
    except ValueError as exc:
        return error("bad_request", str(exc), 400)

    try:
        prediction = classifier.predict(text)
    except InsufficientTextError as exc:
        return error("text_too_short", str(exc), 422,
                     min_words=MIN_WORDS_FOR_PREDICTION)
    except Exception as exc:                              # pragma: no cover
        log.exception("Classification failed")
        return error("classification_failed",
                     "The server could not classify this submission.", 500,
                     detail=str(exc))

    result = prediction.to_dict()
    # The raw text is echoed back by predict(); the client already has it and
    # is responsible for storing it, so it is dropped from the response to
    # keep the payload small.
    result.pop("text", None)

    return jsonify({
        "ok": True,
        "api_version": API_VERSION,
        "request_id": g.request_id,
        "result": result,
    })


@app.post("/classify/batch")
def classify_batch():
    """Classify several submissions in one call.

    Request : {"texts": ["...", "..."]}
    Response: {"ok": true, "results": [{index, ok, result | error}, ...]}

    Individual failures do not fail the batch; each item reports its own
    outcome so the client can handle them one by one.
    """
    guard = require_model()
    if guard:
        return guard

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or "texts" not in payload:
        return error("bad_request",
                     "Request body must contain a 'texts' array.", 400)

    texts = payload["texts"]
    if not isinstance(texts, list):
        return error("bad_request", "The 'texts' field must be an array.", 400)
    if len(texts) > MAX_BATCH_SIZE:
        return error("batch_too_large",
                     f"A batch may contain at most {MAX_BATCH_SIZE} items.", 400)

    results = []
    for index, item in enumerate(texts):
        if not isinstance(item, str):
            results.append({"index": index, "ok": False,
                            "error": {"code": "bad_request",
                                      "message": "Each item must be a string."}})
            continue
        try:
            prediction = classifier.predict(item)
            result = prediction.to_dict()
            result.pop("text", None)
            results.append({"index": index, "ok": True, "result": result})
        except InsufficientTextError as exc:
            results.append({"index": index, "ok": False,
                            "error": {"code": "text_too_short",
                                      "message": str(exc)}})
        except Exception as exc:                          # pragma: no cover
            results.append({"index": index, "ok": False,
                            "error": {"code": "classification_failed",
                                      "message": str(exc)}})

    return jsonify({
        "ok": True,
        "api_version": API_VERSION,
        "request_id": g.request_id,
        "count": len(results),
        "results": results,
    })


@app.get("/")
def root():
    """Human-readable index, so an accidental browser visit is not a 404."""
    return jsonify({
        "service": "Mental Health Classification API",
        "api_version": API_VERSION,
        "endpoints": {
            "GET /health": "liveness probe",
            "GET /info": "deployed model description and constraints",
            "POST /classify": "classify one submission",
            "POST /classify/batch": "classify up to "
                                    f"{MAX_BATCH_SIZE} submissions",
        },
        "note": "This service performs all text pre-processing. Send raw, "
                "uncleaned text.",
    })


# --------------------------------------------------------------------------
# Error handlers - keep every response JSON
# --------------------------------------------------------------------------
@app.errorhandler(404)
def _not_found(_):
    return error("not_found", "No such endpoint. See GET / for the list.", 404)


@app.errorhandler(405)
def _method_not_allowed(_):
    return error("method_not_allowed",
                 "That endpoint does not accept this HTTP method.", 405)


@app.errorhandler(413)
def _payload_too_large(_):
    return error("payload_too_large", "The request body is too large.", 413)


@app.errorhandler(500)
def _server_error(_):                                     # pragma: no cover
    return error("server_error", "An unexpected server error occurred.", 500)


# --------------------------------------------------------------------------
if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5001"))
    debug = os.environ.get("DEBUG", "").lower() in {"1", "true", "yes"}

    if host != "127.0.0.1":
        log.warning("Binding to %s exposes this service beyond the local "
                    "machine. It has no authentication.", host)

    log.info("Classes served: %s", ", ".join(TARGET_CLASSES))
    log.info("Listening on http://%s:%d", host, port)
    # use_reloader is off so the model is not loaded twice.
    app.run(host=host, port=port, debug=debug, use_reloader=False,
            threaded=True)
