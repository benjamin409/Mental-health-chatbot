"""
test_system.py
--------------
Verification script for the classification pipeline.

Runs three checks:

  1. Pre-processing - the pipeline produces the expected cleaned output and
     handles empty, numeric and noisy input without failing.
  2. Guard conditions - submissions that are too short are rejected.
  3. Sanity classification - a set of hand-written entries, none of which come
     from the corpus, is classified and the outcome recorded.

Check 3 is a sanity check, not a formal evaluation: the reported figures in
Chapter Four come from the held-out test set in ``train.py``.

Usage
-----
    python src/test_system.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from predict import InsufficientTextError, MentalHealthClassifier  # noqa: E402
from preprocess import TextPreprocessor  # noqa: E402

# Hand-written entries with the class a human reader would expect.
SANITY_CASES = [
    ("I woke up early, had breakfast with my roommate and we walked to campus "
     "together. Lectures went fine and I am meeting friends later.", "Normal"),
    ("Just finished my assignment and submitted it before the deadline. "
     "Planning to watch a film tonight and rest properly.", "Normal"),
    ("Nothing brings me joy anymore. I stay in bed all day, I have stopped "
     "answering my friends and I feel completely empty inside.", "Depression"),
    ("I feel worthless and tired of everything. There is no point to any of "
     "this and I have lost interest in the things I used to love.", "Depression"),
    ("My chest keeps tightening and my heart races for no reason. I cannot "
     "stop worrying that something terrible is about to happen.", "Anxiety"),
    ("I am always on edge, my hands shake before I speak to anyone and I "
     "panic about things that have not even happened yet.", "Anxiety"),
    ("I have three deadlines this week, my supervisor keeps adding work and I "
     "am completely overwhelmed. There is too much pressure on me.", "Stress"),
    ("Between exams, my job and family demands I am stretched far too thin. "
     "The workload is crushing and I cannot keep up with all of it.", "Stress"),
]

# Expected outputs reflect the documented behaviour of the pipeline: URLs,
# digits and punctuation are stripped; elongated spellings are collapsed to two
# characters; tokens are lemmatised as verbs and then as nouns; and the
# intensity and negation markers deliberately retained in NEGATION_KEEP (such
# as "now", "not", "very") survive stop-word removal.
PREPROCESS_CASES = [
    ("Check this out https://example.com/page NOW!!!", "check out now"),
    ("", ""),
    ("12345 6789", ""),
    ("I'm feeling sooooo tired today", "feel soo tire today"),
    ("I can't sleep and I don't want to talk to ANYONE.",
     "not sleep not want talk anyone"),
    # Regression check: part-of-speech-aware lemmatization must leave
    # predicative participles intact. The earlier verb-then-noun approach
    # rewrote these to "stick", "stress" and "worry".
    ("I have been stuck in traffic and I am stressed and worried",
     "stuck traffic stressed worried"),
]


def test_preprocessing() -> int:
    print("=" * 74)
    print("TEST 1: PRE-PROCESSING")
    print("=" * 74)
    pre = TextPreprocessor()
    failures = 0
    for raw, expected in PREPROCESS_CASES:
        result = pre.clean(raw)
        ok = result == expected
        failures += 0 if ok else 1
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {raw!r:<50} -> {result!r}")
        if not ok:
            print(f"         expected {expected!r}")
    return failures


def test_guards(classifier: MentalHealthClassifier) -> int:
    print("\n" + "=" * 74)
    print("TEST 2: INPUT GUARD CONDITIONS")
    print("=" * 74)
    failures = 0
    for text in ["", "sad", "I am fine", "   "]:
        try:
            classifier.predict(text)
            print(f"  [FAIL] {text!r} was accepted but should have been rejected")
            failures += 1
        except InsufficientTextError:
            print(f"  [PASS] {text!r} correctly rejected as too short")
    return failures


def test_sanity(classifier: MentalHealthClassifier) -> int:
    print("\n" + "=" * 74)
    print("TEST 3: SANITY CLASSIFICATION ON UNSEEN, HAND-WRITTEN ENTRIES")
    print("=" * 74)
    correct = 0
    for text, expected in SANITY_CASES:
        result = classifier.predict(text)
        ok = result.predicted_class == expected
        correct += int(ok)
        status = "PASS" if ok else "MISS"
        print(f"  [{status}] expected {expected:<11} got "
              f"{result.predicted_class:<11} ({result.confidence:.1%})  "
              f"\"{text[:52]}...\"")
    print(f"\n  {correct}/{len(SANITY_CASES)} hand-written entries classified "
          f"as a human reader would expect.")
    return len(SANITY_CASES) - correct


def main() -> None:
    classifier = MentalHealthClassifier()
    print(f"Model under test: {classifier.model_name}\n")

    hard_failures = test_preprocessing()
    hard_failures += test_guards(classifier)
    misses = test_sanity(classifier)

    print("\n" + "=" * 74)
    if hard_failures:
        print(f"RESULT: {hard_failures} functional test(s) FAILED.")
    else:
        print("RESULT: all functional tests passed.")
    print(f"        {misses} sanity case(s) did not match the expected class "
          f"(informational only).")
    print("=" * 74)
    sys.exit(1 if hard_failures else 0)


if __name__ == "__main__":
    main()
