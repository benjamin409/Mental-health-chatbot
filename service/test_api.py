"""
service/test_api.py
-------------------
Verification suite for the inference service.

Starts nothing itself - the service must already be running. It exercises every
endpoint and every documented failure path, and checks that the response shape
the Node presentation layer depends on is actually delivered.

Usage
-----
    python service/app.py            # in one terminal
    python service/test_api.py       # in another

    BASE_URL=http://127.0.0.1:8000 python service/test_api.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5001")

passed = 0
failed = 0


def call(method: str, path: str, body=None):
    """Perform a request and return (status_code, parsed_json)."""
    url = BASE_URL + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"_raw": raw.decode(errors="replace")}
    except urllib.error.URLError as exc:
        print(f"\nCannot reach {BASE_URL} - is the service running?  ({exc})")
        sys.exit(2)


def check(label: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {label}")
    else:
        failed += 1
        print(f"  [FAIL] {label}" + (f"\n         {detail}" if detail else ""))


def section(title: str) -> None:
    print("\n" + "=" * 74)
    print(title)
    print("=" * 74)


# --------------------------------------------------------------------------
def test_health():
    section("HEALTH AND SERVICE DESCRIPTION")
    status, body = call("GET", "/health")
    check("GET /health returns 200", status == 200, f"got {status}")
    check("health reports ready", body.get("status") == "ready", str(body))

    status, body = call("GET", "/")
    check("GET / lists the endpoints", status == 200 and "endpoints" in body)

    status, body = call("GET", "/info")
    check("GET /info returns 200", status == 200, f"got {status}")
    model = body.get("model", {})
    check("info names the model", bool(model.get("name")), str(body))
    check("info lists exactly four classes",
          len(model.get("classes", [])) == 4, str(model.get("classes")))
    check("info states the minimum word count",
          isinstance(body.get("constraints", {}).get("min_words"), int))
    print(f"         model: {model.get('name')}, "
          f"trained {model.get('trained_at')}, "
          f"test F1 {model.get('test_f1_weighted')}")


def test_classify():
    section("POST /classify - SUCCESSFUL CLASSIFICATION")
    text = ("I have not been able to sleep for weeks, nothing interests me "
            "anymore and I feel like a burden to everyone around me.")
    status, body = call("POST", "/classify", {"text": text})

    check("returns 200", status == 200, f"got {status}: {body}")
    check("ok flag is true", body.get("ok") is True)
    result = body.get("result", {})

    required = ["predicted_class", "confidence", "probabilities", "headline",
                "message", "refer", "low_confidence", "referral_note",
                "model_used", "clean_text"]
    missing = [field for field in required if field not in result]
    check("result carries every field the client needs", not missing,
          f"missing: {missing}")

    check("predicted class is one of the four",
          result.get("predicted_class") in
          {"Normal", "Depression", "Anxiety", "Stress"},
          str(result.get("predicted_class")))
    check("confidence is a probability",
          isinstance(result.get("confidence"), (int, float))
          and 0 <= result["confidence"] <= 1,
          str(result.get("confidence")))
    probs = result.get("probabilities", {})
    check("probabilities cover all four classes", len(probs) == 4, str(probs))
    check("probabilities sum to 1",
          abs(sum(probs.values()) - 1.0) < 0.01, str(sum(probs.values())))
    check("raw text is not echoed back", "text" not in result)
    check("a distress class sets the referral flag",
          result.get("refer") is True if
          result.get("predicted_class") != "Normal" else True)

    print(f"         predicted: {result.get('predicted_class')} "
          f"({result.get('confidence'):.1%})")


def test_normal_case():
    section("POST /classify - NON-DISTRESS SUBMISSION")
    text = ("I woke up early, had breakfast with my roommate and we walked to "
            "campus together. Lectures went fine and I am meeting friends later.")
    status, body = call("POST", "/classify", {"text": text})
    result = body.get("result", {})
    check("returns 200", status == 200, f"got {status}")
    check("classified as Normal", result.get("predicted_class") == "Normal",
          str(result.get("predicted_class")))
    check("no referral prompt for a Normal result",
          result.get("refer") is False and result.get("referral_note") is None,
          str(result.get("referral_note")))


def test_validation():
    section("VALIDATION AND ERROR HANDLING")

    status, body = call("POST", "/classify", {"text": "sad"})
    check("text under the word minimum returns 422", status == 422, f"got {status}")
    check("  and names the error", body.get("error", {}).get("code") ==
          "text_too_short", str(body))
    check("  and states the minimum",
          isinstance(body.get("error", {}).get("min_words"), int), str(body))

    status, body = call("POST", "/classify", {})
    check("missing 'text' field returns 400", status == 400, f"got {status}")
    check("  and names the error",
          body.get("error", {}).get("code") == "bad_request", str(body))

    status, body = call("POST", "/classify", {"text": 12345})
    check("non-string 'text' returns 400", status == 400, f"got {status}")

    status, body = call("POST", "/classify", {"text": "x" * 10_001})
    check("oversized 'text' returns 400", status == 400, f"got {status}")

    status, body = call("GET", "/classify")
    check("wrong HTTP method returns 405", status == 405, f"got {status}")

    status, body = call("GET", "/nonexistent")
    check("unknown path returns 404", status == 404, f"got {status}")
    check("  and the 404 body is JSON, not HTML",
          body.get("error", {}).get("code") == "not_found", str(body)[:120])

    status, body = call("POST", "/classify", {"text": "     "})
    check("whitespace-only text is rejected", status == 422, f"got {status}")


def test_batch():
    section("POST /classify/batch")
    texts = [
        "Nothing brings me joy anymore, I stay in bed all day and I have "
        "stopped answering my friends.",
        "My chest keeps tightening and my heart races for no reason at all.",
        "no",                                     # too short - must fail alone
        "Just finished my assignment and submitted it before the deadline.",
    ]
    status, body = call("POST", "/classify/batch", {"texts": texts})
    check("returns 200", status == 200, f"got {status}")
    results = body.get("results", [])
    check("one entry per submitted item", len(results) == len(texts),
          f"got {len(results)}")
    check("items keep their submitted order",
          [r["index"] for r in results] == list(range(len(texts))))
    check("valid items succeed",
          all(results[i]["ok"] for i in (0, 1, 3)), str(results))
    check("an invalid item fails alone without failing the batch",
          results[2]["ok"] is False
          and results[2]["error"]["code"] == "text_too_short",
          str(results[2]))

    for r in results:
        if r["ok"]:
            print(f"         [{r['index']}] {r['result']['predicted_class']} "
                  f"({r['result']['confidence']:.1%})")
        else:
            print(f"         [{r['index']}] rejected: {r['error']['code']}")

    status, body = call("POST", "/classify/batch", {"texts": ["ok"] * 51})
    check("oversized batch returns 400", status == 400, f"got {status}")

    status, body = call("POST", "/classify/batch", {"texts": "not an array"})
    check("non-array 'texts' returns 400", status == 400, f"got {status}")


def test_consistency():
    section("DETERMINISM")
    text = ("I have three deadlines this week, my supervisor keeps adding work "
            "and I am completely overwhelmed by the pressure.")
    first = call("POST", "/classify", {"text": text})[1]["result"]
    second = call("POST", "/classify", {"text": text})[1]["result"]
    check("the same input yields the same class",
          first["predicted_class"] == second["predicted_class"])
    check("the same input yields the same confidence",
          first["confidence"] == second["confidence"])

    # Pre-processing must happen server-side: text the client has NOT cleaned
    # and the same text with incidental noise should agree.
    noisy = call("POST", "/classify",
                 {"text": text.upper() + "   !!!"})[1]["result"]
    check("case and punctuation noise do not change the class",
          noisy["predicted_class"] == first["predicted_class"],
          f"{first['predicted_class']} vs {noisy['predicted_class']}")


def main():
    print(f"Testing the inference service at {BASE_URL}")
    test_health()
    test_classify()
    test_normal_case()
    test_validation()
    test_batch()
    test_consistency()

    print("\n" + "=" * 74)
    print(f"RESULT: {passed} passed, {failed} failed")
    print("=" * 74)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
