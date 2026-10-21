"""
evaluate.py
-----------
Evaluation phase (CRISP-DM phase 5) - figure and table generation.

Reads the metrics produced by ``train.py`` and renders the figures and tables
required for Chapter Four: the class distribution of the corpus, the
model-comparison chart, the confusion matrix of the selected model, the
per-class F1 comparison, and the most informative terms learned for each class.

Usage
-----
    python src/evaluate.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

sys.path.append(str(Path(__file__).resolve().parent))

from config import (  # noqa: E402
    BEST_MODEL_FILE,
    CLEAN_DATA_FILE,
    FIGURES_DIR,
    MODEL_METADATA_FILE,
    RESULTS_DIR,
    TARGET_CLASSES,
    VECTORIZER_FILE,
)

# --------------------------------------------------------------------------
# Figure styling
# --------------------------------------------------------------------------
# A colour-blind-safe categorical set (Okabe-Ito), assigned to classes in a
# fixed order so that a class keeps the same colour in every figure.
CLASS_COLOURS = {
    "Normal": "#0072B2",
    "Depression": "#E69F00",
    "Anxiety": "#009E73",
    "Stress": "#CC79A7",
}
MODEL_COLOURS = ["#0072B2", "#E69F00", "#009E73"]
INK = "#1A1A1A"
MUTED = "#6B6B6B"
GRID = "#DDDDDD"

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
})

SEQUENTIAL = LinearSegmentedColormap.from_list(
    "thesis_blues", ["#FFFFFF", "#C9DFF0", "#7FB6DC", "#3384BE", "#0B4F80"])


def _load_metrics() -> dict:
    with open(MODEL_METADATA_FILE) as fh:
        return json.load(fh)


# --------------------------------------------------------------------------
# Figure 4.1 - class distribution
# --------------------------------------------------------------------------
def plot_class_distribution() -> None:
    df = pd.read_csv(CLEAN_DATA_FILE)
    counts = df["label"].value_counts().reindex(TARGET_CLASSES)

    fig, ax = plt.subplots(figsize=(7, 4.2))
    bars = ax.bar(counts.index, counts.values, width=0.6,
                  color=[CLASS_COLOURS[c] for c in counts.index])
    for bar, value in zip(bars, counts.values):
        pct = value / counts.sum() * 100
        ax.text(bar.get_x() + bar.get_width() / 2, value + counts.max() * 0.015,
                f"{value:,}\n({pct:.1f}%)", ha="center", va="bottom",
                fontsize=9, color=INK)

    ax.set_ylabel("Number of records")
    ax.set_title("Class distribution of the cleaned corpus")
    ax.set_ylim(0, counts.max() * 1.20)
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    fig.savefig(FIGURES_DIR / "fig_4_1_class_distribution.png")
    plt.close(fig)
    print("  fig_4_1_class_distribution.png")


# --------------------------------------------------------------------------
# Figure 4.2 - model comparison
# --------------------------------------------------------------------------
def plot_model_comparison(meta: dict) -> None:
    results = meta["results"]
    models = list(results)
    metrics = [("accuracy", "Accuracy"),
               ("precision_weighted", "Precision"),
               ("recall_weighted", "Recall"),
               ("f1_weighted", "F1-score")]

    x = np.arange(len(metrics))
    width = 0.26

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    for i, model in enumerate(models):
        values = [results[model][key] for key, _ in metrics]
        offset = (i - (len(models) - 1) / 2) * width
        bars = ax.bar(x + offset, values, width * 0.92, label=model,
                      color=MODEL_COLOURS[i % len(MODEL_COLOURS)])
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.008,
                    f"{value:.3f}", ha="center", va="bottom", fontsize=7.5,
                    color=INK)

    ax.set_xticks(x, [label for _, label in metrics])
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.set_title("Comparative performance of the three classifiers")
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, ncol=3, loc="lower center",
              bbox_to_anchor=(0.5, -0.22))
    fig.savefig(FIGURES_DIR / "fig_4_2_model_comparison.png")
    plt.close(fig)
    print("  fig_4_2_model_comparison.png")


# --------------------------------------------------------------------------
# Figure 4.3 - confusion matrix of the selected model
# --------------------------------------------------------------------------
def plot_confusion_matrix(meta: dict) -> None:
    best = meta["best_model"]
    cm = np.array(meta["results"][best]["confusion_matrix"])
    cm_pct = cm / cm.sum(axis=1, keepdims=True) * 100

    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    im = ax.imshow(cm_pct, cmap=SEQUENTIAL, vmin=0, vmax=100)

    ax.set_xticks(range(len(TARGET_CLASSES)), TARGET_CLASSES, rotation=20,
                  ha="right")
    ax.set_yticks(range(len(TARGET_CLASSES)), TARGET_CLASSES)
    ax.set_xlabel("Predicted class")
    ax.set_ylabel("Actual class")
    ax.set_title(f"Confusion matrix - {best}")

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            colour = "#FFFFFF" if cm_pct[i, j] > 55 else INK
            ax.text(j, i, f"{cm[i, j]:,}\n{cm_pct[i, j]:.1f}%", ha="center",
                    va="center", fontsize=9, color=colour)

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(TARGET_CLASSES), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(TARGET_CLASSES), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)

    cbar = fig.colorbar(im, ax=ax, shrink=0.82)
    cbar.set_label("Percentage of actual class", color=MUTED)
    cbar.outline.set_visible(False)

    fig.savefig(FIGURES_DIR / "fig_4_3_confusion_matrix.png")
    plt.close(fig)
    print("  fig_4_3_confusion_matrix.png")


# --------------------------------------------------------------------------
# Figure 4.4 - per-class F1 across the three models
# --------------------------------------------------------------------------
def plot_per_class_f1(meta: dict) -> None:
    results = meta["results"]
    models = list(results)
    x = np.arange(len(TARGET_CLASSES))
    width = 0.26

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    for i, model in enumerate(models):
        values = [results[model]["per_class"][c]["f1-score"]
                  for c in TARGET_CLASSES]
        offset = (i - (len(models) - 1) / 2) * width
        bars = ax.bar(x + offset, values, width * 0.92, label=model,
                      color=MODEL_COLOURS[i % len(MODEL_COLOURS)])
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.008,
                    f"{value:.2f}", ha="center", va="bottom", fontsize=7.5,
                    color=INK)

    ax.set_xticks(x, TARGET_CLASSES)
    ax.set_ylabel("F1-score")
    ax.set_ylim(0, 1.05)
    ax.set_title("Per-class F1-score by classifier")
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, ncol=3, loc="lower center",
              bbox_to_anchor=(0.5, -0.22))
    fig.savefig(FIGURES_DIR / "fig_4_4_per_class_f1.png")
    plt.close(fig)
    print("  fig_4_4_per_class_f1.png")


# --------------------------------------------------------------------------
# Figure 4.5 - most informative terms per class
# --------------------------------------------------------------------------
def plot_top_features(top_n: int = 12) -> None:
    """Plot the highest-weighted TF-IDF terms for each class.

    Uses the Logistic Regression model, whose coefficients are directly
    interpretable, regardless of which classifier was finally selected.
    """
    lr_path = BEST_MODEL_FILE.parent / "model_logistic_regression.pkl"
    if not lr_path.exists():
        print("  (logistic regression model not found - skipping top features)")
        return

    model = joblib.load(lr_path)
    vectorizer = joblib.load(VECTORIZER_FILE)
    feature_names = np.array(vectorizer.get_feature_names_out())

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    rows = []
    for ax, cls in zip(axes.ravel(), TARGET_CLASSES):
        idx = list(model.classes_).index(cls)
        coefs = model.coef_[idx]
        top_idx = np.argsort(coefs)[-top_n:]
        terms = feature_names[top_idx]
        weights = coefs[top_idx]

        ax.barh(range(len(terms)), weights, color=CLASS_COLOURS[cls],
                height=0.72)
        ax.set_yticks(range(len(terms)), terms, fontsize=8.5)
        ax.set_title(cls, color=INK)
        ax.set_xlabel("Model coefficient")
        ax.xaxis.grid(True)
        ax.set_axisbelow(True)

        for rank, (term, weight) in enumerate(zip(terms[::-1], weights[::-1]), 1):
            rows.append({"class": cls, "rank": rank, "term": term,
                         "coefficient": round(float(weight), 4)})

    fig.suptitle("Most informative terms learned for each class "
                 "(Logistic Regression)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_4_5_top_features.png")
    plt.close(fig)
    pd.DataFrame(rows).to_csv(RESULTS_DIR / "top_features_per_class.csv",
                              index=False)
    print("  fig_4_5_top_features.png")


# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------
def write_tables(meta: dict) -> None:
    """Write the Chapter Four results tables in CSV and Markdown form."""
    results = meta["results"]
    best = meta["best_model"]

    comparison = pd.DataFrame({
        "Model": list(results),
        "Accuracy": [results[m]["accuracy"] for m in results],
        "Precision": [results[m]["precision_weighted"] for m in results],
        "Recall": [results[m]["recall_weighted"] for m in results],
        "F1-score": [results[m]["f1_weighted"] for m in results],
        "Macro F1": [results[m]["f1_macro"] for m in results],
        "CV F1 (5-fold)": [results[m].get("cv_f1_mean", float("nan"))
                           for m in results],
        "Training time (s)": [results[m]["training_time_seconds"]
                              for m in results],
    }).round(4)
    comparison.to_csv(RESULTS_DIR / "table_4_1_model_comparison.csv",
                      index=False)

    per_class = pd.DataFrame([
        {
            "Class": c,
            "Precision": round(results[best]["per_class"][c]["precision"], 4),
            "Recall": round(results[best]["per_class"][c]["recall"], 4),
            "F1-score": round(results[best]["per_class"][c]["f1-score"], 4),
            "Support": int(results[best]["per_class"][c]["support"]),
        }
        for c in TARGET_CLASSES
    ])
    per_class.to_csv(RESULTS_DIR / "table_4_2_per_class_metrics.csv",
                     index=False)

    with open(RESULTS_DIR / "results_tables.md", "w") as fh:
        fh.write("# Chapter Four - Results Tables\n\n")
        fh.write(f"Selected model: **{best}**\n\n")
        fh.write("## Table 4.1: Comparative performance of the three classifiers\n\n")
        fh.write(comparison.to_markdown(index=False))
        fh.write(f"\n\n## Table 4.2: Per-class performance of the {best}\n\n")
        fh.write(per_class.to_markdown(index=False))
        fh.write("\n\n## Table 4.3: Confusion matrix (counts)\n\n")
        cm = pd.DataFrame(results[best]["confusion_matrix"],
                          index=[f"Actual {c}" for c in TARGET_CLASSES],
                          columns=[f"Predicted {c}" for c in TARGET_CLASSES])
        fh.write(cm.to_markdown())
        fh.write("\n")
    print("  results_tables.md, table_4_1_*.csv, table_4_2_*.csv")


# --------------------------------------------------------------------------
# Figure 4.6 and Table 4.4 - effect of the length-bias correction
# --------------------------------------------------------------------------
def plot_length_bias_ablation(meta: dict) -> None:
    """Compare the corrected model against the length-biased baseline.

    Requires ``metrics_baseline.json``, produced by
    ``python src/train.py --no-augment --no-save``.
    """
    baseline_path = RESULTS_DIR / "metrics_baseline.json"
    if not baseline_path.exists():
        print("  (metrics_baseline.json not found - skipping the ablation; run "
              "'python src/train.py --no-augment --no-save' to produce it)")
        return

    with open(baseline_path) as fh:
        baseline = json.load(fh)

    models = [m for m in meta["results"] if m in baseline["results"]]
    rows = []
    for model in models:
        rows.append({
            "Model": model,
            "Full text, baseline": baseline["results"][model]["f1_weighted"],
            "Full text, corrected": meta["results"][model]["f1_weighted"],
            "Short entry, baseline":
                baseline["results"][model]["short_entry"]["f1_weighted"],
            "Short entry, corrected":
                meta["results"][model]["short_entry"]["f1_weighted"],
        })
    table = pd.DataFrame(rows).round(4)
    table.to_csv(RESULTS_DIR / "table_4_4_length_bias_ablation.csv", index=False)

    # Grouped bars: two conditions, two training variants.
    labels = ["Full-length\ntest entries", "Short\ntest entries"]
    best = meta["best_model"]
    baseline_vals = [baseline["results"][best]["f1_weighted"],
                     baseline["results"][best]["short_entry"]["f1_weighted"]]
    corrected_vals = [meta["results"][best]["f1_weighted"],
                      meta["results"][best]["short_entry"]["f1_weighted"]]

    x = np.arange(len(labels))
    width = 0.32
    fig, ax = plt.subplots(figsize=(7, 4.4))
    for i, (vals, label, colour) in enumerate([
            (baseline_vals, "Trained without correction", "#6B6B6B"),
            (corrected_vals, "Trained with segmentation", "#0072B2")]):
        offset = (i - 0.5) * width
        bars = ax.bar(x + offset, vals, width * 0.92, label=label, color=colour)
        for bar, value in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.008,
                    f"{value:.3f}", ha="center", va="bottom", fontsize=9,
                    color=INK)

    ax.set_xticks(x, labels)
    ax.set_ylabel("Weighted F1-score")
    ax.set_ylim(0, 1.02)
    ax.set_title(f"Effect of the length-bias correction ({best})")
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.26),
              ncol=2)
    fig.savefig(FIGURES_DIR / "fig_4_6_length_bias_ablation.png")
    plt.close(fig)

    with open(RESULTS_DIR / "results_tables.md", "a") as fh:
        fh.write("\n\n## Table 4.4: Effect of the length-bias correction "
                 "(weighted F1)\n\n")
        fh.write(table.to_markdown(index=False))
        fh.write("\n\nThe corrected model gives up a little accuracy on "
                 "full-length documents in exchange for a substantial gain on "
                 "short entries, which is the condition under which the "
                 "deployed system actually operates.\n")
    print("  fig_4_6_length_bias_ablation.png, "
          "table_4_4_length_bias_ablation.csv")


def main() -> None:
    meta = _load_metrics()
    print("=" * 74)
    print(f"GENERATING EVALUATION ARTEFACTS (best model: {meta['best_model']})")
    print("=" * 74)
    plot_class_distribution()
    plot_model_comparison(meta)
    plot_confusion_matrix(meta)
    plot_per_class_f1(meta)
    plot_top_features()
    write_tables(meta)
    plot_length_bias_ablation(meta)
    print(f"\nFigures written to {FIGURES_DIR}")
    print("=" * 74)


if __name__ == "__main__":
    main()
