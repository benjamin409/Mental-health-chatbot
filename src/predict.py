"""
predict.py
----------
Classification service (CRISP-DM phase 6 - deployment logic).

Loads the fitted TF-IDF vectorizer and the selected classifier and exposes a
single ``MentalHealthClassifier`` class that takes raw user text and returns a
predicted class, a confidence score, the full probability distribution and the
interpretation shown to the user. The web layer, when added, calls this class;
it can also be run directly from the command line for testing.

Usage
-----
    python src/predict.py "I have not been able to sleep and I feel hopeless"
    python src/predict.py            # interactive mode
"""

from __future__ import annotations

import json
import sys
import warnings
from dataclasses import dataclass, asdict
from pathlib import Path

import joblib

sys.path.append(str(Path(__file__).resolve().parent))

from config import (  # noqa: E402
    BEST_MODEL_FILE,
    CLASS_INTERPRETATION,
    LOW_CONFIDENCE_THRESHOLD,
    MIN_WORDS_FOR_PREDICTION,
    MODEL_METADATA_FILE,
    REFERRAL_NOTE,
    VECTORIZER_FILE,
)
from preprocess import TextPreprocessor  # noqa: E402


@dataclass
class Prediction:
    """The result returned for a single submission."""
    text: str
    clean_text: str
    predicted_class: str
    confidence: float
    probabilities: dict
    headline: str
    message: str
    refer: bool
    low_confidence: bool
    referral_note: str | None
    model_used: str

    def to_dict(self) -> dict:
        return asdict(self)


class InsufficientTextError(ValueError):
    """Raised when a submission is too short to be classified reliably."""


class MentalHealthClassifier:
    """Wraps the trained artefacts behind a single ``predict`` method."""

    def __init__(self,
                 model_path: Path = BEST_MODEL_FILE,
                 vectorizer_path: Path = VECTORIZER_FILE,
                 metadata_path: Path = MODEL_METADATA_FILE) -> None:
        if not model_path.exists() or not vectorizer_path.exists():
            raise FileNotFoundError(
                "Trained artefacts not found. Run 'python src/prepare_data.py' "
                "followed by 'python src/train.py' first."
            )
        # scikit-learn emits an InconsistentVersionWarning for every estimator
        # in a pickle written by a different version of the library. The
        # warning is worth heeding but not worth printing three times over a
        # user's screen, so it is collected here and re-reported once, in
        # plain language, as self.version_warning.
        self.version_warning: str | None = None
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self.model = joblib.load(model_path)
            self.vectorizer = joblib.load(vectorizer_path)

        mismatched = {
            getattr(w.message, "original_sklearn_version", None)
            for w in caught
            if w.category.__name__ == "InconsistentVersionWarning"
        } - {None}
        if mismatched:
            import sklearn
            self.version_warning = (
                f"This model was trained with scikit-learn "
                f"{sorted(mismatched)[0]} but you are running "
                f"{sklearn.__version__}. It has loaded and will work, but if "
                f"results look wrong, retrain with "
                f"'python src/train.py --no-cv' to regenerate the model files "
                f"for your installed version."
            )
        for w in caught:                      # do not swallow anything else
            if w.category.__name__ != "InconsistentVersionWarning":
                warnings.warn(w.message, w.category)

        self.preprocessor = TextPreprocessor()

        self.metadata = {}
        if metadata_path.exists():
            with open(metadata_path) as fh:
                self.metadata = json.load(fh)
        self.model_name = self.metadata.get("best_model", "trained model")
        self.classes = list(self.model.classes_)

    # ------------------------------------------------------------------
    def predict(self, text: str) -> Prediction:
        """Classify a single free-text submission."""
        raw = (text or "").strip()
        if len(raw.split()) < MIN_WORDS_FOR_PREDICTION:
            raise InsufficientTextError(
                f"Please write at least {MIN_WORDS_FOR_PREDICTION} words so the "
                f"system has enough to work with."
            )

        clean = self.preprocessor.clean(raw)
        if not clean:
            raise InsufficientTextError(
                "No usable words were found in the submission after cleaning."
            )

        features = self.vectorizer.transform([clean])
        label = str(self.model.predict(features)[0])

        probabilities = {}
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(features)[0]
            probabilities = {str(c): round(float(p), 4)
                             for c, p in zip(self.classes, probs)}
            confidence = float(max(probs))
        else:                                    # pragma: no cover - fallback
            confidence = 1.0
            probabilities = {label: 1.0}

        info = CLASS_INTERPRETATION[label]
        low_conf = confidence < LOW_CONFIDENCE_THRESHOLD

        return Prediction(
            text=raw,
            clean_text=clean,
            predicted_class=label,
            confidence=round(confidence, 4),
            probabilities=dict(sorted(probabilities.items(),
                                      key=lambda kv: kv[1], reverse=True)),
            headline=info["headline"],
            message=info["message"],
            refer=bool(info["refer"]),
            low_confidence=low_conf,
            referral_note=REFERRAL_NOTE if info["refer"] else None,
            model_used=self.model_name,
        )

    def predict_batch(self, texts: list[str]) -> list[Prediction]:
        return [self.predict(t) for t in texts]


# --------------------------------------------------------------------------
# Command-line interface
# --------------------------------------------------------------------------
def _report(prediction: Prediction) -> None:
    print("-" * 70)
    print(f"INPUT      : {prediction.text}")
    print(f"CLEANED    : {prediction.clean_text}")
    print(f"PREDICTION : {prediction.predicted_class} "
          f"(confidence {prediction.confidence:.2%})")
    dist = ", ".join(f"{k} {v:.1%}" for k, v in prediction.probabilities.items())
    print(f"DISTRIBUTION: {dist}")
    print(f"HEADLINE   : {prediction.headline}")
    if prediction.low_confidence:
        print("NOTE       : Low confidence - the entry does not clearly match "
              "any single class.")
    if prediction.referral_note:
        print(f"REFERRAL   : {prediction.referral_note}")
    print("-" * 70)


def main() -> None:
    classifier = MentalHealthClassifier()
    print(f"Model in use: {classifier.model_name}")
    if classifier.version_warning:
        print(f"Note: {classifier.version_warning}")

    if len(sys.argv) > 1:
        _report(classifier.predict(" ".join(sys.argv[1:])))
        return

    print("Enter a piece of text (blank line to quit).\n")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            break
        try:
            _report(classifier.predict(text))
        except InsufficientTextError as exc:
            print(f"  {exc}")


if __name__ == "__main__":
    main()
