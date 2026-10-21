"""
user_text_eval.py
-----------------
An evaluation set of realistic user entries, and the harness that scores a
model against it.

The held-out test set in ``train.py`` is drawn from the same Reddit corpus as
the training data: long posts written by people who use explicit clinical
vocabulary. It measures how well the model reproduces that corpus. It does not
measure how well the system serves a person typing a few sentences into a text
box, which is what the deployed system actually has to do.

This module supplies the missing instrument. Every entry below is short, of the
kind a user would actually write, and deliberately varied along the dimensions
where the model has been observed to fail:

  * with, and without, explicit distress vocabulary
  * standard English, Nigerian English, and Nigerian Pidgin
  * feelings named directly, and circumstances described instead

IMPORTANT: these sentences were drafted by the developer, not collected from
users. They are a working instrument, not validated ground truth. Before any
figure derived from them is reported as a finding, they should be replaced or
confirmed by sentences written and labelled independently by Nigerian speakers.

Usage
-----
    python src/user_text_eval.py                 # score the deployed model
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

# (text, expected label, variety, uses explicit distress vocabulary?)
USER_TEXT_EVAL = [
    # ---------------- Normal -------------------------------------------
    ("I woke up early, had breakfast with my roommate and we walked to campus together",
     "Normal", "standard", False),
    ("Just finished my assignment and submitted it before the deadline, planning to rest tonight",
     "Normal", "standard", False),
    ("My exams went well by God grace, I am waiting for the result",
     "Normal", "nigerian", False),
    ("I went to church on Sunday and after that I visited my friend, we enjoyed",
     "Normal", "nigerian", False),
    ("Today na my birthday, my guys dey come house, we go chop well",
     "Normal", "pidgin", False),
    ("I go see my people for village last weekend, everybody happy",
     "Normal", "pidgin", False),
    ("Work was busy today but I finished everything and I am watching a film now",
     "Normal", "standard", False),
    ("We played football in the evening and I am about to sleep, it was a good day",
     "Normal", "standard", False),

    # ---------------- Depression ---------------------------------------
    ("Nothing brings me joy anymore, I stay in bed all day and I have stopped answering my friends",
     "Depression", "standard", True),
    ("I feel worthless and empty, there is no point to any of this",
     "Depression", "standard", True),
    ("I have not felt like myself in weeks, I just lie down and stare at the wall",
     "Depression", "standard", False),
    ("I have been feeling somehow lately, my spirit is down and I am not myself",
     "Depression", "nigerian", False),
    ("Things are not working for me at all, I am just managing life anyhow",
     "Depression", "nigerian", False),
    ("I don tire for this life, nothing dey work for me again",
     "Depression", "pidgin", False),
    ("E don do me, I no get strength again, I just dey cry every night",
     "Depression", "pidgin", False),
    ("I stopped going out, I do not enjoy anything I used to enjoy and I sleep all day",
     "Depression", "standard", False),

    # ---------------- Anxiety ------------------------------------------
    ("My chest keeps tightening and my heart races for no reason at all",
     "Anxiety", "standard", False),
    ("I cannot stop worrying that something terrible is about to happen to my family",
     "Anxiety", "standard", True),
    ("I am always on edge, my hands shake before I speak to anyone",
     "Anxiety", "standard", False),
    ("My mind is not at rest, I keep fearing that something will happen",
     "Anxiety", "nigerian", False),
    ("I am always worried, my heart will just be beating anyhow",
     "Anxiety", "nigerian", True),
    ("My mind no dey settle at all, e be like say something bad go happen",
     "Anxiety", "pidgin", False),
    ("My body dey shake, I dey fear wetin go happen tomorrow",
     "Anxiety", "pidgin", False),
    ("I keep checking my phone and panicking about things that have not happened",
     "Anxiety", "standard", True),

    # ---------------- Stress -------------------------------------------
    ("I have three deadlines this week and my supervisor keeps adding more work",
     "Stress", "standard", False),
    ("I am so stressed, the workload is too much and I cannot cope with the pressure",
     "Stress", "standard", True),
    ("Between exams, my job and family demands I am stretched far too thin",
     "Stress", "standard", False),
    ("This school work is too much, my head is full, I cannot cope again",
     "Stress", "nigerian", False),
    ("Work is stressing me seriously, I am tired of everything",
     "Stress", "nigerian", True),
    ("This work don tire me, everything just dey scatter my head",
     "Stress", "pidgin", False),
    ("Too much things dey my head, I no fit rest at all",
     "Stress", "pidgin", False),
    ("I am under constant pressure and I never get time to rest or relax",
     "Stress", "standard", True),
]


def score(classifier, verbose: bool = True) -> dict:
    """Score a classifier against the user-text evaluation set."""
    from predict import InsufficientTextError

    correct = 0
    rejected = 0
    by_variety: Counter = Counter()
    total_by_variety: Counter = Counter()
    by_vocab = {True: [0, 0], False: [0, 0]}     # [correct, total]
    rows = []

    for text, expected, variety, has_vocab in USER_TEXT_EVAL:
        total_by_variety[variety] += 1
        by_vocab[has_vocab][1] += 1
        try:
            prediction = classifier.predict(text)
            got, confidence = prediction.predicted_class, prediction.confidence
        except InsufficientTextError:
            got, confidence = "REJECTED", 0.0
            rejected += 1

        hit = got == expected
        correct += hit
        by_variety[variety] += hit
        by_vocab[has_vocab][0] += hit
        rows.append((hit, expected, got, confidence, variety, has_vocab, text))

    total = len(USER_TEXT_EVAL)

    if verbose:
        print("=" * 92)
        print("USER-TEXT EVALUATION")
        print("=" * 92)
        for hit, expected, got, confidence, variety, has_vocab, text in rows:
            mark = "  " if hit else " X"
            print(f"{mark} {variety:<9}{expected:<11}-> {got:<11}{confidence:>5.0%}  "
                  f"{text[:52]}")
        print("-" * 92)
        print(f"  Overall            : {correct}/{total} = {correct / total:.1%}")
        for variety in ("standard", "nigerian", "pidgin"):
            n = total_by_variety[variety]
            print(f"  {variety.capitalize():<19}: {by_variety[variety]}/{n} "
                  f"= {by_variety[variety] / n:.0%}")
        for label, key in (("With distress words", True), ("Without them", False)):
            c, n = by_vocab[key]
            print(f"  {label:<19}: {c}/{n} = {c / n:.0%}")
        if rejected:
            print(f"  Rejected as too short: {rejected}")
        print("=" * 92)

    return {
        "correct": correct,
        "total": total,
        "accuracy": correct / total,
        "by_variety": {v: (by_variety[v], total_by_variety[v])
                       for v in total_by_variety},
        "with_vocab": tuple(by_vocab[True]),
        "without_vocab": tuple(by_vocab[False]),
    }


if __name__ == "__main__":
    from predict import MentalHealthClassifier
    score(MentalHealthClassifier())
