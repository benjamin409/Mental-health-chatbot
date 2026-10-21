"""
experiment_segmentation.py
--------------------------
Diagnostic experiment: length bias in the corpus.

The 'Normal' class in the source corpus consists of very short statements
(median 7 informative tokens) while the three distress classes are long-form
posts (median 46-62 tokens). A classifier trained on this corpus can therefore
learn document length as a proxy for the label, and will tend to assign 'Normal'
to any short entry - which is exactly the kind of entry a user of the deployed
system types.

This script quantifies the problem and tests one remedy: segmenting long
training documents into overlapping short windows that inherit the parent
label, so that every class is represented at short lengths.

Usage
-----
    python src/experiment_segmentation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score

sys.path.append(str(Path(__file__).resolve().parent))

from config import RANDOM_STATE, TARGET_CLASSES, TEST_FILE, TFIDF_PARAMS, TRAIN_FILE  # noqa: E402
from preprocess import TextPreprocessor  # noqa: E402
from test_system import SANITY_CASES  # noqa: E402


def segment(text: str, window: int, stride: int, max_windows: int) -> list[str]:
    tokens = text.split()
    if len(tokens) <= window:
        return []
    out = []
    for start in range(0, len(tokens) - window + 1, stride):
        out.append(" ".join(tokens[start:start + window]))
        if len(out) >= max_windows:
            break
    return out


def augment(df: pd.DataFrame, window: int = 25, stride: int = 18,
            max_windows: int = 4) -> pd.DataFrame:
    rows = []
    for text, label in zip(df["clean_text"], df["label"]):
        for chunk in segment(str(text), window, stride, max_windows):
            rows.append({"clean_text": chunk, "label": label})
    extra = pd.DataFrame(rows)
    return pd.concat([df[["clean_text", "label"]], extra], ignore_index=True)


def truncate(text: str, n: int = 25) -> str:
    return " ".join(str(text).split()[:n])


def fit_eval(train_df: pd.DataFrame, test_df: pd.DataFrame, tag: str,
             pre: TextPreprocessor) -> dict:
    vec = TfidfVectorizer(**TFIDF_PARAMS)
    X = vec.fit_transform(train_df["clean_text"].fillna(""))
    model = LogisticRegression(C=5.0, max_iter=2000, class_weight="balanced",
                               solver="lbfgs", random_state=RANDOM_STATE)
    model.fit(X, train_df["label"])

    # full-length held-out test set
    Xt = vec.transform(test_df["clean_text"].fillna(""))
    pred = model.predict(Xt)
    f1_full = f1_score(test_df["label"], pred, average="weighted", zero_division=0)
    f1_macro_full = f1_score(test_df["label"], pred, average="macro", zero_division=0)

    # the same test set truncated to 25 tokens, simulating a short user entry
    short = test_df["clean_text"].fillna("").map(lambda t: truncate(t, 25))
    pred_short = model.predict(vec.transform(short))
    f1_short = f1_score(test_df["label"], pred_short, average="weighted",
                        zero_division=0)
    f1_macro_short = f1_score(test_df["label"], pred_short, average="macro",
                              zero_division=0)

    # hand-written entries
    hand_clean = [pre.clean(t) for t, _ in SANITY_CASES]
    hand_true = [lbl for _, lbl in SANITY_CASES]
    hand_pred = model.predict(vec.transform(hand_clean))
    hand_correct = int(sum(p == t for p, t in zip(hand_pred, hand_true)))

    print(f"\n--- {tag} ---")
    print(f"  training rows            : {len(train_df):,}")
    print(f"  weighted F1 (full test)  : {f1_full:.4f}   "
          f"macro F1: {f1_macro_full:.4f}")
    print(f"  weighted F1 (short test) : {f1_short:.4f}   "
          f"macro F1: {f1_macro_short:.4f}")
    print(f"  hand-written entries     : {hand_correct}/{len(SANITY_CASES)}")
    for (text, true), p in zip(SANITY_CASES, hand_pred):
        flag = " " if p == true else "*"
        print(f"     {flag} {true:<11} -> {p}")
    print("  per-class F1 on short test:")
    print(classification_report(test_df["label"], pred_short,
                                labels=TARGET_CLASSES, zero_division=0))
    return {"tag": tag, "f1_full": f1_full, "f1_short": f1_short,
            "hand": hand_correct}


def main() -> None:
    pre = TextPreprocessor()
    train_df = pd.read_csv(TRAIN_FILE)
    test_df = pd.read_csv(TEST_FILE)
    train_df["clean_text"] = train_df["clean_text"].fillna("").astype(str)
    test_df["clean_text"] = test_df["clean_text"].fillna("").astype(str)

    print("Token counts by class (training set):")
    print(train_df.assign(n=train_df["clean_text"].str.split().str.len())
          .groupby("label")["n"].median().to_string())

    results = [fit_eval(train_df, test_df, "Baseline (no segmentation)", pre)]

    for window, stride, max_windows in [(25, 18, 4), (20, 12, 6), (30, 20, 5)]:
        aug = augment(train_df, window, stride, max_windows)
        results.append(fit_eval(
            aug, test_df,
            f"Segmented (window={window}, stride={stride}, max={max_windows})",
            pre))

    print("\n" + "=" * 74)
    print("SUMMARY")
    print("=" * 74)
    print(pd.DataFrame(results).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
