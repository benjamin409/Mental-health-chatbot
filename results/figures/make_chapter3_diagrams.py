"""
make_chapter3_diagrams.py
-------------------------
Draws the two Chapter Three figures affected by the two-process architecture:

  Figure 3.3  Sequence diagram (revised)  - the Express dashboard owns the
              database; the Flask service is stateless.
  Figure 3.5  Deployment architecture     - the three layers and the process
              boundary between Node.js and Python.

Both are drawn in a plain, monochrome academic style suitable for printing.

    python results/figures/make_chapter3_diagrams.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

OUT = Path(__file__).resolve().parent

INK = "#111111"
MUTED = "#666666"
LIFELINE = "#999999"
FILL_NODE = "#EAF2F8"
FILL_PY = "#FDF0E3"
FILL_DATA = "#EDEDED"
EDGE = "#333333"

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "font.family": "DejaVu Sans",
    "text.color": INK,
})


# ==========================================================================
# Figure 3.3 - Sequence diagram
# ==========================================================================
def sequence_diagram() -> None:
    participants = [
        ("User", None),
        ("Dashboard\n(Express / Node.js)", "Presentation layer"),
        ("Classification Service\n(Flask / Python)", "Middle layer"),
        ("Trained Model\n(TF-IDF + classifier)", "Middle layer"),
        ("Database\n(SQLite)", "Data layer"),
    ]

    # (from, to, label, is_return, is_self)
    messages = [
        (0, 1, "1: submits text entry", False, False),
        (1, 2, "2: POST /classify  { raw text }", False, False),
        (2, 2, "3: pre-process\n(tokenize, remove stop words, lemmatize)", False, True),
        (2, 3, "4: transform to TF-IDF vector, request prediction", False, False),
        (3, 2, "5: predicted class + confidence score", True, False),
        (2, 1, "6: JSON result  { class, confidence, probabilities }", True, False),
        (1, 4, "7: store submission record", False, False),
        (4, 1, "8: acknowledgement", True, False),
        (1, 0, "9: display result (with referral prompt if not Normal)", True, False),
    ]

    x = [0, 2.55, 5.5, 8.3, 10.9]
    box_w = [1.15, 1.95, 2.10, 2.05, 1.35]
    top = 0.0
    row_h = 1.0
    first_row = -1.35

    fig, ax = plt.subplots(figsize=(13.6, 8.4))

    # Participant boxes and lifelines
    for i, (name, layer) in enumerate(participants):
        w = box_w[i]
        ax.add_patch(FancyBboxPatch(
            (x[i] - w / 2, top - 0.42), w, 0.84,
            boxstyle="round,pad=0.02,rounding_size=0.06",
            facecolor="white", edgecolor=EDGE, linewidth=1.3, zorder=3))
        ax.text(x[i], top, name, ha="center", va="center", fontsize=9.5,
                fontweight="bold", zorder=4)
        if layer:
            ax.text(x[i], top + 0.66, layer, ha="center", va="center",
                    fontsize=8, style="italic", color=MUTED)
        ax.plot([x[i], x[i]], [top - 0.42, first_row - len(messages) * row_h + 0.35],
                linestyle=(0, (4, 4)), color=LIFELINE, linewidth=1.0, zorder=1)

    # Activation bars
    def activation(i, start_row, end_row, offset=0.0):
        y0 = first_row - end_row * row_h - 0.22
        y1 = first_row - start_row * row_h + 0.22
        ax.add_patch(Rectangle((x[i] - 0.075 + offset, y0), 0.15, y1 - y0,
                               facecolor="white", edgecolor=EDGE,
                               linewidth=1.0, zorder=2))

    activation(1, 0, 8)      # dashboard active throughout
    activation(2, 1, 5)      # service
    activation(3, 3, 4)      # model
    activation(4, 6, 7)      # database

    # Messages
    for row, (src, dst, label, is_return, is_self) in enumerate(messages):
        y = first_row - row * row_h

        if is_self:
            xs = x[src] + 0.075
            ax.add_patch(FancyArrowPatch(
                (xs, y + 0.14), (xs, y - 0.30),
                connectionstyle="bar,fraction=0.55",
                arrowstyle="-|>", mutation_scale=11,
                linewidth=1.2, color=EDGE, zorder=5))
            ax.text(xs + 0.62, y - 0.10, label, ha="left", va="center",
                    fontsize=8.4, color=INK, zorder=6,
                    bbox=dict(boxstyle="round,pad=0.20", facecolor="white",
                              edgecolor="none"))
            continue

        x0, x1 = x[src], x[dst]
        pad = 0.085 if src != 0 else 0.0
        x0 = x0 + pad if x1 > x0 else x0 - pad
        x1 = x1 - pad if x1 > x0 else x1 + pad

        ax.annotate(
            "", xy=(x1, y), xytext=(x0, y),
            arrowprops=dict(
                arrowstyle="-|>" if not is_return else "->",
                linewidth=1.2, color=EDGE,
                linestyle="--" if is_return else "-",
                shrinkA=0, shrinkB=0, mutation_scale=13),
            zorder=5)
        ax.text((x0 + x1) / 2, y + 0.19, label, ha="center", va="bottom",
                fontsize=8.4, color=INK, zorder=6,
                bbox=dict(boxstyle="round,pad=0.20", facecolor="white",
                          edgecolor="none"))

    # Note on statelessness
    note_y = first_row - len(messages) * row_h - 0.15
    ax.text(6.4, note_y,
            "Note: the classification service stores nothing. The submission "
            "record (steps 7-8) is written by the\ndashboard, which also owns "
            "the session token. The service receives raw text and performs all "
            "pre-processing itself.",
            ha="center", va="top", fontsize=8.2, color=MUTED, style="italic")

    ax.set_xlim(-1.0, 12.2)
    ax.set_ylim(note_y - 0.9, 1.35)
    ax.axis("off")
    fig.savefig(OUT / "fig_3_3_sequence_diagram_revised.png")
    plt.close(fig)
    print("  fig_3_3_sequence_diagram_revised.png")


# ==========================================================================
# Figure 3.5 - Deployment architecture
# ==========================================================================
def architecture_diagram() -> None:
    fig, ax = plt.subplots(figsize=(11.6, 8.6))

    def box(cx, cy, w, h, title, lines, fill, bold_title=True, fontsize=9.5):
        ax.add_patch(FancyBboxPatch(
            (cx - w / 2, cy - h / 2), w, h,
            boxstyle="round,pad=0.03,rounding_size=0.10",
            facecolor=fill, edgecolor=EDGE, linewidth=1.4, zorder=3))
        ax.text(cx, cy + h / 2 - 0.30, title, ha="center", va="center",
                fontsize=fontsize,
                fontweight="bold" if bold_title else "normal", zorder=4)
        for k, line in enumerate(lines):
            ax.text(cx, cy + h / 2 - 0.66 - k * 0.29, line, ha="center",
                    va="center", fontsize=8.3, color=INK, zorder=4)

    # ---- process boundaries and layer captions --------------------------
    ax.add_patch(Rectangle((0.45, 3.95), 4.45, 2.60, facecolor="none",
                           edgecolor=MUTED, linewidth=1.1,
                           linestyle=(0, (6, 4)), zorder=1))
    ax.text(0.45, 6.68, "Presentation layer  ·  Node.js process",
            ha="left", va="bottom", fontsize=8.8, style="italic", color=MUTED)

    ax.add_patch(Rectangle((6.20, 3.95), 4.45, 2.60, facecolor="none",
                           edgecolor=MUTED, linewidth=1.1,
                           linestyle=(0, (6, 4)), zorder=1))
    ax.text(10.65, 6.68, "Middle layer  ·  Python process",
            ha="right", va="bottom", fontsize=8.8, style="italic", color=MUTED)

    ax.text(0.45, 2.72, "Data layer", ha="left", va="bottom", fontsize=8.8,
            style="italic", color=MUTED)

    # ---- boxes ----------------------------------------------------------
    box(2.67, 8.15, 3.40, 1.20, "Web Browser",
        ["text entry form, result display,", "submission history"], "white")

    box(2.67, 5.25, 3.85, 1.95, "Express Application",
        ["routes and page rendering",
         "session token (cookie)",
         "submission persistence",
         "referral prompt logic"], FILL_NODE)

    box(8.42, 5.25, 3.85, 1.95, "Flask Inference Service",
        ["POST /classify, /health, /info",
         "text pre-processing pipeline",
         "TF-IDF vectorization",
         "classification, stateless"], FILL_PY)

    box(2.67, 1.60, 3.40, 1.45, "SQLite Database",
        ["submissions table:", "text, class, confidence,",
         "session token, timestamp"], FILL_DATA)

    box(8.42, 1.60, 3.40, 1.45, "Model Artefacts",
        ["tfidf_vectorizer.pkl", "best_model.pkl",
         "loaded once at start-up"], FILL_DATA)

    # ---- arrows ---------------------------------------------------------
    def arrow(p0, p1, label, label_xy, ha="center", va="center", fontsize=8.4):
        ax.annotate("", xy=p1, xytext=p0,
                    arrowprops=dict(arrowstyle="-|>", linewidth=1.4,
                                    color=EDGE, shrinkA=2, shrinkB=2,
                                    mutation_scale=13),
                    zorder=5)
        ax.text(label_xy[0], label_xy[1], label, ha=ha, va=va,
                fontsize=fontsize, color=INK, zorder=6,
                bbox=dict(boxstyle="round,pad=0.22", facecolor="white",
                          edgecolor="none"))

    arrow((2.67, 7.55), (2.67, 6.28),
          "HTTP\n(page requests, form posts)", (2.92, 7.18), ha="left")

    # Request and response drawn separately so neither label sits on a line.
    arrow((4.62, 5.72), (6.47, 5.72),
          "POST /classify   { raw text }", (5.55, 6.06))
    arrow((6.47, 4.78), (4.62, 4.78),
          "{ class, confidence, probabilities }", (5.55, 4.44), fontsize=8.2)
    ax.text(5.55, 5.25, "HTTP + JSON", ha="center", va="center", fontsize=8.4,
            style="italic", color=MUTED, zorder=6,
            bbox=dict(boxstyle="round,pad=0.20", facecolor="white",
                      edgecolor="none"))

    arrow((2.67, 4.27), (2.67, 2.36), "read / write", (2.90, 3.32), ha="left")
    arrow((8.42, 4.27), (8.42, 2.36), "loaded at start-up", (8.65, 3.32),
          ha="left")

    # ---- caption note ---------------------------------------------------
    ax.text(5.55, 0.42,
            "The model is a Python object and can only be loaded by Python; the "
            "presentation layer requires no Python at all.\nAll text "
            "pre-processing occurs inside the inference service, so that text "
            "submitted at run time is transformed\nexactly as the training "
            "corpus was. The service holds no state.",
            ha="center", va="center", fontsize=8.3, color=MUTED, style="italic")

    ax.set_xlim(-0.15, 11.1)
    ax.set_ylim(-0.15, 9.05)
    ax.axis("off")
    fig.savefig(OUT / "fig_3_5_system_architecture.png")
    plt.close(fig)
    print("  fig_3_5_system_architecture.png")


if __name__ == "__main__":
    print("Drawing Chapter Three figures")
    sequence_diagram()
    architecture_diagram()
    print(f"Written to {OUT}")
