"""
tune_for_user_text.py
---------------------
Model selection driven by user-style text rather than by the corpus test set.

The standard approach tunes hyper-parameters to maximise performance on a
held-out split of the training corpus. That split is long-form Reddit prose, so
tuning against it optimises the model for text no user will ever type. This
script instead reports both numbers for every configuration:

    corpus F1     - weighted F1 on the held-out Reddit test set
    user-text acc - accuracy on the user-style evaluation set

and selects on the second while watching the first, so that gains for real
users are not bought with a collapse on the benchmark.

Configurations explored:

  * word features only (the current baseline) versus word + character n-grams,
    the latter chosen because character features are robust to the spelling
    variation of informal and Pidgin text ("dey" / "de")
  * regularisation strength C
  * additional weight on the Stress class, which the baseline under-detects

Usage
-----
    python src/tune_for_user_text.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import FeatureUnion
from sklearn.utils.class_weight import compute_class_weight

sys.path.append(str(Path(__file__).resolve().parent))

from config import (  # noqa: E402
    RANDOM_STATE, RESULTS_DIR, SEGMENT_WINDOW, TARGET_CLASSES,
    TEST_FILE, TRAIN_AUGMENTED_FILE,
)
from preprocess import TextPreprocessor  # noqa: E402
from user_text_eval import USER_TEXT_EVAL  # noqa: E402

WORD_PARAMS = dict(max_features=15000, ngram_range=(1, 2), min_df=3,
                   max_df=0.85, sublinear_tf=True)
CHAR_PARAMS = dict(analyzer="char_wb", ngram_range=(3, 5), max_features=30000,
                   min_df=3, sublinear_tf=True)


def build_vectorizer(use_char: bool):
    word = TfidfVectorizer(**WORD_PARAMS)
    if not use_char:
        return word
    return FeatureUnion([("word", word),
                         ("char", TfidfVectorizer(**CHAR_PARAMS))])


def class_weights(y, stress_boost: float) -> dict:
    classes = np.array(sorted(set(y)))
    weights = compute_class_weight("balanced", classes=classes, y=y)
    mapping = dict(zip(classes, weights))
    mapping["Stress"] *= stress_boost
    return mapping


def evaluate_user_text(model, vectorizer, pre) -> tuple[float, dict]:
    texts = [t for t, _, _, _ in USER_TEXT_EVAL]
    truth = [lbl for _, lbl, _, _ in USER_TEXT_EVAL]
    cleaned = [pre.clean(t) for t in texts]
    predicted = model.predict(vectorizer.transform(cleaned))

    hits = sum(p == t for p, t in zip(predicted, truth))
    per_class = {}
    for cls in TARGET_CLASSES:
        idx = [i for i, t in enumerate(truth) if t == cls]
        per_class[cls] = (sum(predicted[i] == truth[i] for i in idx), len(idx))
    return hits / len(truth), per_class


def run() -> None:
    pre = TextPreprocessor()
    train_df = pd.read_csv(TRAIN_AUGMENTED_FILE)
    test_df = pd.read_csv(TEST_FILE)
    for frame in (train_df, test_df):
        frame["clean_text"] = frame["clean_text"].fillna("").astype(str)

    y_train, y_test = train_df["label"], test_df["label"]
    short_test = test_df["clean_text"].map(
        lambda t: " ".join(t.split()[:SEGMENT_WINDOW]))

    configurations = []
    for use_char in (False, True):
        for C in (1.0, 5.0, 10.0):
            for boost in (1.0, 2.0, 3.0):
                configurations.append((use_char, C, boost))

    print(f"Evaluating {len(configurations)} configurations")
    print(f"{'char':<6}{'C':>6}{'stress':>8}{'corpusF1':>10}"
          f"{'shortF1':>9}{'userAcc':>9}   per-class on user text")
    print("-" * 96)

    results = []
    cache: dict[bool, tuple] = {}

    for use_char, C, boost in configurations:
        if use_char not in cache:
            vec = build_vectorizer(use_char)
            Xtr = vec.fit_transform(train_df["clean_text"])
            cache[use_char] = (vec, Xtr, vec.transform(test_df["clean_text"]),
                               vec.transform(short_test))
        vec, X_train, X_test, X_short = cache[use_char]

        model = LogisticRegression(
            C=C, max_iter=2000, solver="lbfgs", random_state=RANDOM_STATE,
            class_weight=class_weights(y_train, boost))
        model.fit(X_train, y_train)

        corpus_f1 = f1_score(y_test, model.predict(X_test),
                             average="weighted", zero_division=0)
        short_f1 = f1_score(y_test, model.predict(X_short),
                            average="weighted", zero_division=0)
        user_acc, per_class = evaluate_user_text(model, vec, pre)

        summary = "  ".join(f"{c[:4]} {v}/{n}" for c, (v, n) in per_class.items())
        print(f"{str(use_char):<6}{C:>6}{boost:>8}{corpus_f1:>10.4f}"
              f"{short_f1:>9.4f}{user_acc:>9.1%}   {summary}")

        results.append({"use_char": use_char, "C": C, "stress_boost": boost,
                        "corpus_f1": corpus_f1, "short_f1": short_f1,
                        "user_accuracy": user_acc,
                        "user_per_class": {c: list(v) for c, v in per_class.items()}})

    print("-" * 96)
    ranked = sorted(results,
                    key=lambda r: (round(r["user_accuracy"], 4),
                                   round(r["corpus_f1"], 4)),
                    reverse=True)
    best = ranked[0]
    baseline = next(r for r in results
                    if not r["use_char"] and r["C"] == 5.0
                    and r["stress_boost"] == 1.0)

    print(f"Baseline (word only, C=5, no boost): "
          f"user {baseline['user_accuracy']:.1%}, corpus F1 {baseline['corpus_f1']:.4f}")
    print(f"Best on user text                  : char={best['use_char']}, "
          f"C={best['C']}, stress_boost={best['stress_boost']} -> "
          f"user {best['user_accuracy']:.1%}, corpus F1 {best['corpus_f1']:.4f}")

    with open(RESULTS_DIR / "user_text_tuning.json", "w") as fh:
        json.dump({"results": results, "best": best, "baseline": baseline},
                  fh, indent=2)
    print(f"\nWritten to {RESULTS_DIR / 'user_text_tuning.json'}")


if __name__ == "__main__":
    started = time.time()
    run()
    print(f"Total {time.time() - started:.0f}s")
