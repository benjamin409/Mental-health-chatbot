"""
train.py
--------
Modelling phase (CRISP-DM phase 4).

Three classical classifiers - Logistic Regression, Support Vector Machine and
Random Forest - are trained on identical TF-IDF features and on the same
train/test split so that their performance can be compared under exactly the
same conditions. Class weighting is applied to correct the imbalance in the
corpus. The fitted vectorizer and the best-performing classifier are persisted
to ``models/`` for use by the deployment layer.

Usage
-----
    python src/train.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.svm import LinearSVC

sys.path.append(str(Path(__file__).resolve().parent))

from config import (  # noqa: E402
    AUGMENT_TRAINING,
    BEST_MODEL_FILE,
    MODEL_DIR,
    MODEL_METADATA_FILE,
    RANDOM_STATE,
    RESULTS_DIR,
    SEGMENT_WINDOW,
    TARGET_CLASSES,
    TEST_FILE,
    TFIDF_PARAMS,
    TRAIN_AUGMENTED_FILE,
    TRAIN_FILE,
    VECTORIZER_FILE,
)


# --------------------------------------------------------------------------
# Model definitions
# --------------------------------------------------------------------------
def build_models() -> dict:
    """Return the three candidate classifiers.

    ``class_weight="balanced"`` is set on every model so that the minority
    classes (Anxiety and Stress) are not overwhelmed by the majority classes
    during fitting. LinearSVC does not expose ``predict_proba``; it is
    therefore wrapped in ``CalibratedClassifierCV`` so that the deployed system
    can report a confidence score for every prediction, as required by the
    database design.
    """
    return {
        # C = 1.0 was selected by src/tune_for_user_text.py, which scores each
        # configuration on user-style entries as well as on the corpus test
        # set. The stronger regularisation costs nothing on the benchmark and
        # improves real-entry accuracy substantially: a larger C lets the model
        # fit corpus-specific vocabulary that does not generalise to the short,
        # plainly worded text a user actually submits.
        "Logistic Regression": LogisticRegression(
            C=1.0,
            max_iter=2000,
            class_weight="balanced",
            solver="lbfgs",
            random_state=RANDOM_STATE,
        ),
        "Support Vector Machine": CalibratedClassifierCV(
            estimator=LinearSVC(
                C=1.0,
                class_weight="balanced",
                max_iter=5000,
                random_state=RANDOM_STATE,
            ),
            method="sigmoid",
            cv=3,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=1,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
    }


def evaluate_predictions(y_true, y_pred) -> dict:
    """Compute the four headline metrics, weighted and macro-averaged."""
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision_weighted": precision_score(y_true, y_pred, average="weighted",
                                              zero_division=0),
        "recall_weighted": recall_score(y_true, y_pred, average="weighted",
                                        zero_division=0),
        "f1_weighted": f1_score(y_true, y_pred, average="weighted",
                                zero_division=0),
        "precision_macro": precision_score(y_true, y_pred, average="macro",
                                           zero_division=0),
        "recall_macro": recall_score(y_true, y_pred, average="macro",
                                     zero_division=0),
        "f1_macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
    }


def train(run_cross_validation: bool = True,
          use_augmented: bool = AUGMENT_TRAINING,
          persist: bool = True) -> dict:
    started = time.time()
    print("=" * 74)
    print("MODELLING AND EVALUATION")
    print("=" * 74)

    # ------------------------------------------------------------ load data
    train_path = TRAIN_FILE
    if use_augmented:
        if TRAIN_AUGMENTED_FILE.exists():
            train_path = TRAIN_AUGMENTED_FILE
        else:
            print("  (augmented training set not found - falling back to the "
                  "unsegmented training set)")
            use_augmented = False

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(TEST_FILE)
    for frame in (train_df, test_df):
        frame["clean_text"] = frame["clean_text"].fillna("").astype(str)

    X_train_text, y_train = train_df["clean_text"], train_df["label"]
    X_test_text, y_test = test_df["clean_text"], test_df["label"]

    # A copy of the test set truncated to the first SEGMENT_WINDOW tokens. It
    # simulates the short entry a real user types, and is reported alongside
    # the full-length result so that the two are never confused.
    X_test_short = X_test_text.map(
        lambda t: " ".join(t.split()[:SEGMENT_WINDOW]))

    print(f"\nTraining set     : {train_path.name} ({len(train_df):,} records)")
    print(f"Length-bias correction (segmentation): "
          f"{'ENABLED' if use_augmented else 'DISABLED'}")
    print(f"Test records     : {len(test_df):,}")

    # ---------------------------------------------------- feature extraction
    print("\n[1] Fitting TF-IDF vectorizer")
    for key, value in TFIDF_PARAMS.items():
        print(f"      {key:<14} = {value}")
    vectorizer = TfidfVectorizer(**TFIDF_PARAMS)
    X_train = vectorizer.fit_transform(X_train_text)
    X_test = vectorizer.transform(X_test_text)
    X_test_short_vec = vectorizer.transform(X_test_short)
    print(f"      Feature matrix : {X_train.shape[0]:,} x {X_train.shape[1]:,}")
    print(f"      Sparsity       : "
          f"{100 * (1 - X_train.nnz / (X_train.shape[0] * X_train.shape[1])):.3f}% zeros")
    if persist:
        joblib.dump(vectorizer, VECTORIZER_FILE)

    # ------------------------------------------------------------- training
    models = build_models()
    results: dict[str, dict] = {}
    fitted: dict[str, object] = {}

    for name, model in models.items():
        print(f"\n[2] Training {name}")
        t0 = time.time()
        model.fit(X_train, y_train)
        train_time = time.time() - t0

        t0 = time.time()
        y_pred = model.predict(X_test)
        predict_time = time.time() - t0

        metrics = evaluate_predictions(y_test, y_pred)
        metrics["training_time_seconds"] = round(train_time, 2)
        metrics["prediction_time_seconds"] = round(predict_time, 3)
        metrics["per_class"] = classification_report(
            y_test, y_pred, labels=TARGET_CLASSES, output_dict=True,
            zero_division=0)
        metrics["confusion_matrix"] = confusion_matrix(
            y_test, y_pred, labels=TARGET_CLASSES).tolist()

        # Performance on the same test set truncated to a short entry.
        y_pred_short = model.predict(X_test_short_vec)
        metrics["short_entry"] = evaluate_predictions(y_test, y_pred_short)
        metrics["short_entry"]["confusion_matrix"] = confusion_matrix(
            y_test, y_pred_short, labels=TARGET_CLASSES).tolist()

        if run_cross_validation:
            cv = StratifiedKFold(n_splits=5, shuffle=True,
                                 random_state=RANDOM_STATE)
            scores = cross_val_score(model, X_train, y_train, cv=cv,
                                     scoring="f1_weighted", n_jobs=-1)
            metrics["cv_f1_mean"] = float(np.mean(scores))
            metrics["cv_f1_std"] = float(np.std(scores))
            print(f"      5-fold CV F1 : {np.mean(scores):.4f} "
                  f"(+/- {np.std(scores):.4f})")

        results[name] = metrics
        fitted[name] = model

        print(f"      Accuracy     : {metrics['accuracy']:.4f}")
        print(f"      Precision (w): {metrics['precision_weighted']:.4f}")
        print(f"      Recall (w)   : {metrics['recall_weighted']:.4f}")
        print(f"      F1-score (w) : {metrics['f1_weighted']:.4f}")
        print(f"      F1-score (m) : {metrics['f1_macro']:.4f}")
        print(f"      F1 on short entries (<= {SEGMENT_WINDOW} tokens): "
              f"{metrics['short_entry']['f1_weighted']:.4f}")
        print(f"      Fitted in {train_time:.1f}s")

    # -------------------------------------------------------- model selection
    best_name = max(results, key=lambda n: results[n]["f1_weighted"])
    best_model = fitted[best_name]

    print("\n" + "=" * 74)
    print("MODEL COMPARISON")
    print("=" * 74)
    comparison = pd.DataFrame({
        "Model": list(results),
        "Accuracy": [results[n]["accuracy"] for n in results],
        "Precision": [results[n]["precision_weighted"] for n in results],
        "Recall": [results[n]["recall_weighted"] for n in results],
        "F1-score": [results[n]["f1_weighted"] for n in results],
        "F1 (macro)": [results[n]["f1_macro"] for n in results],
        "F1 (short entry)": [results[n]["short_entry"]["f1_weighted"]
                             for n in results],
        "Training time (s)": [results[n]["training_time_seconds"] for n in results],
    }).round(4)
    print(comparison.to_string(index=False))
    if persist:
        comparison.to_csv(RESULTS_DIR / "model_comparison.csv", index=False)

    print(f"\nBest performing model: {best_name} "
          f"(weighted F1 = {results[best_name]['f1_weighted']:.4f})")
    print("\nPer-class report for the selected model:")
    print(classification_report(
        y_test, best_model.predict(X_test), labels=TARGET_CLASSES,
        zero_division=0))

    metadata = {
        "best_model": best_name,
        "classes": TARGET_CLASSES,
        "augmented_training": bool(use_augmented),
        "training_file": train_path.name,
        "tfidf_params": {k: list(v) if isinstance(v, tuple) else v
                         for k, v in TFIDF_PARAMS.items()},
        "vocabulary_size": int(len(vectorizer.vocabulary_)),
        "train_records": int(len(train_df)),
        "test_records": int(len(test_df)),
        "random_state": RANDOM_STATE,
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "results": results,
    }

    if persist:
        joblib.dump(best_model, BEST_MODEL_FILE, compress=3)
        for name, model in fitted.items():
            # A fitted Random Forest on a sparse TF-IDF matrix serialises to
            # roughly a gigabyte, so it is only written to disk when it is the
            # selected model. Its metrics are recorded either way, and the
            # model itself is reproducible by re-running this script.
            if name == "Random Forest" and name != best_name:
                print("  (Random Forest not persisted - see note in train.py; "
                      "its metrics are recorded in model_metadata.json)")
                continue
            slug = name.lower().replace(" ", "_")
            joblib.dump(model, MODEL_DIR / f"model_{slug}.pkl", compress=3)
        with open(MODEL_METADATA_FILE, "w") as fh:
            json.dump(metadata, fh, indent=2)
        with open(RESULTS_DIR / "metrics.json", "w") as fh:
            json.dump(metadata, fh, indent=2)
        print(f"\nArtefacts written to {MODEL_DIR} and {RESULTS_DIR}")
    else:
        suffix = "augmented" if use_augmented else "baseline"
        with open(RESULTS_DIR / f"metrics_{suffix}.json", "w") as fh:
            json.dump(metadata, fh, indent=2)
        print(f"\nMetrics written to {RESULTS_DIR}/metrics_{suffix}.json "
              f"(models not persisted)")

    print(f"Total runtime: {time.time() - started:.1f}s")
    print("=" * 74)
    return metadata


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Train and compare the three classifiers.")
    parser.add_argument("--no-augment", action="store_true",
                        help="train on the unsegmented training set "
                             "(reproduces the length-biased baseline)")
    parser.add_argument("--no-cv", action="store_true",
                        help="skip 5-fold cross-validation (much faster)")
    parser.add_argument("--no-save", action="store_true",
                        help="do not overwrite the persisted model artefacts")
    args = parser.parse_args()

    train(run_cross_validation=not args.no_cv,
          use_augmented=not args.no_augment,
          persist=not args.no_save)
