"""
prepare_data.py
---------------
Data Understanding and Data Preparation phases (CRISP-DM phases 2 and 3).

The script loads the raw labelled corpus, restricts it to the four target
classes, removes unusable records, applies the pre-processing pipeline defined
in ``preprocess.py`` and writes a stratified train/test split to
``data/processed``. It also writes a short data profile to ``results`` so that
the class distribution reported in Chapter Four is reproducible.

Usage
-----
    python src/prepare_data.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.append(str(Path(__file__).resolve().parent))

from config import (  # noqa: E402
    AUGMENT_TRAINING,
    CLEAN_DATA_FILE,
    MAX_SEGMENTS_PER_DOC,
    MIN_WORDS_IN_TRAINING_SAMPLE,
    RANDOM_STATE,
    RAW_DATA_FILE,
    RESULTS_DIR,
    SEGMENT_STRIDE,
    SEGMENT_WINDOW,
    TARGET_CLASSES,
    TEST_FILE,
    TEST_SIZE,
    TRAIN_AUGMENTED_FILE,
    TRAIN_FILE,
)
from preprocess import TextPreprocessor  # noqa: E402


def load_raw_data(path: Path = RAW_DATA_FILE) -> pd.DataFrame:
    """Load the raw corpus and standardise its column names."""
    if not path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at {path}. See data/raw/SOURCE.md for the "
            f"download instructions."
        )
    df = pd.read_csv(path, index_col=0)
    df = df.rename(columns={"statement": "text", "status": "label"})
    return df[["text", "label"]]


def profile(df: pd.DataFrame, stage: str) -> dict:
    """Return a small profile of the corpus at a given stage."""
    counts = df["label"].value_counts().to_dict()
    return {
        "stage": stage,
        "records": int(len(df)),
        "class_counts": {k: int(v) for k, v in counts.items()},
    }


def segment_document(text: str,
                     window: int = SEGMENT_WINDOW,
                     stride: int = SEGMENT_STRIDE,
                     max_windows: int = MAX_SEGMENTS_PER_DOC) -> list[str]:
    """Split a long cleaned document into overlapping fixed-length windows.

    Documents at or below ``window`` tokens produce no windows, since they are
    already short. See the note on length bias in ``config.py``.
    """
    tokens = str(text).split()
    if len(tokens) <= window:
        return []
    windows = []
    for start in range(0, len(tokens) - window + 1, stride):
        windows.append(" ".join(tokens[start:start + window]))
        if len(windows) >= max_windows:
            break
    return windows


def build_augmented_training_set(train_df: pd.DataFrame) -> pd.DataFrame:
    """Return the training set plus short windows cut from its long documents."""
    rows = []
    for text, label in zip(train_df["clean_text"], train_df["label"]):
        for window in segment_document(text):
            rows.append({"text": "", "clean_text": window, "label": label,
                         "token_count": len(window.split()),
                         "source": "segment"})
    original = train_df[["text", "clean_text", "label", "token_count"]].copy()
    original["source"] = "original"
    return pd.concat([original, pd.DataFrame(rows)], ignore_index=True)


def prepare() -> None:
    started = time.time()
    print("=" * 74)
    print("DATA UNDERSTANDING AND PREPARATION")
    print("=" * 74)

    profiles = []

    # ---------------------------------------------------------------- load
    df = load_raw_data()
    print(f"\n[1] Raw corpus loaded          : {len(df):,} records")
    print(df["label"].value_counts().to_string())
    profiles.append(profile(df, "raw"))

    # ------------------------------------------------ restrict to 4 classes
    df = df[df["label"].isin(TARGET_CLASSES)].copy()
    print(f"\n[2] Restricted to target classes: {len(df):,} records")
    profiles.append(profile(df, "four_classes"))

    # ------------------------------------------------------------- cleaning
    before = len(df)
    df = df.dropna(subset=["text"])
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"] != ""]
    print(f"[3] Null / empty entries removed: {before - len(df):,} dropped")

    before = len(df)
    df = df.drop_duplicates(subset=["text"])
    print(f"[4] Duplicate entries removed   : {before - len(df):,} dropped")

    # -------------------------------------------------------- preprocessing
    print("\n[5] Applying the pre-processing pipeline "
          "(lowercasing, noise removal, tokenization, stop-word removal, "
          "lemmatization)...")
    pre = TextPreprocessor()
    df["clean_text"] = pre.clean_series(df["text"])

    before = len(df)
    df["token_count"] = df["clean_text"].str.split().str.len().fillna(0)
    df = df[df["token_count"] >= MIN_WORDS_IN_TRAINING_SAMPLE]
    print(f"    Records with fewer than {MIN_WORDS_IN_TRAINING_SAMPLE} "
          f"informative tokens removed: {before - len(df):,}")

    before = len(df)
    df = df.drop_duplicates(subset=["clean_text"])
    print(f"    Duplicates after cleaning removed: {before - len(df):,}")

    df = df.reset_index(drop=True)
    profiles.append(profile(df, "cleaned"))

    print(f"\n[6] Final cleaned corpus        : {len(df):,} records")
    dist = df["label"].value_counts()
    for label in TARGET_CLASSES:
        n = int(dist.get(label, 0))
        print(f"      {label:<12} {n:>7,}  ({n / len(df) * 100:5.2f}%)")
    imbalance = dist.max() / dist.min()
    print(f"    Imbalance ratio (largest:smallest) = {imbalance:.2f} : 1")
    print("    Class weighting will be applied during training to correct for this.")

    df[["text", "clean_text", "label", "token_count"]].to_csv(
        CLEAN_DATA_FILE, index=False)

    # ---------------------------------------------------------------- split
    train_df, test_df = train_test_split(
        df,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=df["label"],
    )
    train_df.to_csv(TRAIN_FILE, index=False)
    test_df.to_csv(TEST_FILE, index=False)

    print(f"\n[7] Stratified split ({int((1 - TEST_SIZE) * 100)}/"
          f"{int(TEST_SIZE * 100)}, random_state={RANDOM_STATE})")
    print(f"      Training set : {len(train_df):,} records")
    print(f"      Test set     : {len(test_df):,} records")

    # ------------------------------------------- length-bias correction
    median_by_class = (df.assign(n=df["clean_text"].str.split().str.len())
                         .groupby("label")["n"].median())
    print("\n[8] Median informative tokens per class (length-bias check)")
    for label in TARGET_CLASSES:
        print(f"      {label:<12} {median_by_class.get(label, 0):>6.0f}")

    augmented_records = 0
    if AUGMENT_TRAINING:
        aug_df = build_augmented_training_set(train_df)
        aug_df.to_csv(TRAIN_AUGMENTED_FILE, index=False)
        augmented_records = int(len(aug_df))
        print(f"\n[9] Training documents segmented into overlapping windows "
              f"(window={SEGMENT_WINDOW}, stride={SEGMENT_STRIDE}, "
              f"max={MAX_SEGMENTS_PER_DOC})")
        print(f"      Augmented training set : {augmented_records:,} records "
              f"({augmented_records - len(train_df):,} windows added)")
        print("      The test set is NOT segmented, so evaluation is unaffected.")

    summary = {
        "median_tokens_by_class": {k: float(v) for k, v in
                                   median_by_class.items()},
        "augment_training": AUGMENT_TRAINING,
        "segment_window": SEGMENT_WINDOW,
        "segment_stride": SEGMENT_STRIDE,
        "max_segments_per_doc": MAX_SEGMENTS_PER_DOC,
        "augmented_train_records": augmented_records,
        "profiles": profiles,
        "imbalance_ratio": round(float(imbalance), 3),
        "train_records": int(len(train_df)),
        "test_records": int(len(test_df)),
        "train_class_counts": {k: int(v) for k, v in
                               train_df["label"].value_counts().items()},
        "test_class_counts": {k: int(v) for k, v in
                              test_df["label"].value_counts().items()},
        "mean_tokens_after_cleaning": round(float(df["token_count"].mean()), 2),
        "median_tokens_after_cleaning": float(df["token_count"].median()),
        "random_state": RANDOM_STATE,
        "test_size": TEST_SIZE,
    }
    with open(RESULTS_DIR / "data_profile.json", "w") as fh:
        json.dump(summary, fh, indent=2)

    print(f"\nCompleted in {time.time() - started:.1f}s")
    print(f"Artefacts written to {CLEAN_DATA_FILE.parent}")
    print("=" * 74)


if __name__ == "__main__":
    prepare()
