"""
config.py
---------
Central configuration for the Logistic Regression Based Mental Health
Monitoring System.

All paths, class definitions and model hyper-parameters used across the
data-preparation, training, evaluation and deployment scripts are declared
here so that the pipeline can be reproduced exactly from a single place.
"""

from pathlib import Path

# --------------------------------------------------------------------------
# 1. Project paths
# --------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

MODEL_DIR = BASE_DIR / "models"
RESULTS_DIR = BASE_DIR / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
NLTK_DATA_DIR = BASE_DIR / "nltk_data"

RAW_DATA_FILE = RAW_DATA_DIR / "data.csv"
CLEAN_DATA_FILE = PROCESSED_DATA_DIR / "clean_dataset.csv"
TRAIN_FILE = PROCESSED_DATA_DIR / "train.csv"
TRAIN_AUGMENTED_FILE = PROCESSED_DATA_DIR / "train_augmented.csv"
TEST_FILE = PROCESSED_DATA_DIR / "test.csv"

VECTORIZER_FILE = MODEL_DIR / "tfidf_vectorizer.pkl"
BEST_MODEL_FILE = MODEL_DIR / "best_model.pkl"
MODEL_METADATA_FILE = MODEL_DIR / "model_metadata.json"

DATABASE_FILE = BASE_DIR / "app" / "submissions.db"

for _d in (RAW_DATA_DIR, PROCESSED_DATA_DIR, MODEL_DIR, RESULTS_DIR, FIGURES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# 2. Target classes
# --------------------------------------------------------------------------
TARGET_CLASSES = ["Normal", "Depression", "Anxiety", "Stress"]

# Minimum number of words a submission must contain before the system will
# attempt a classification. Very short strings carry too little lexical
# evidence for a TF-IDF model to classify reliably.
MIN_WORDS_FOR_PREDICTION = 5

# Rows shorter than this are dropped from the training corpus.
MIN_WORDS_IN_TRAINING_SAMPLE = 3

# --------------------------------------------------------------------------
# 2b. Lemmatization strategy
# --------------------------------------------------------------------------
# When True, each token is tagged for part of speech and lemmatised once under
# the word class it actually occupies. When False, the fallback lemmatises
# every token first as a verb and then as a noun, which needs no tagger but
# rewrites participles destructively: "tired" becomes "tire", "stressed"
# becomes "stress" and "stuck" becomes "stick", losing precisely the words
# that carry emotional signal in this domain.
POS_AWARE_LEMMATIZATION = True

# --------------------------------------------------------------------------
# 3. Feature extraction (TF-IDF)
# --------------------------------------------------------------------------
TFIDF_PARAMS = {
    "max_features": 15000,
    "ngram_range": (1, 2),
    "min_df": 3,
    "max_df": 0.85,
    "sublinear_tf": True,
}

# --------------------------------------------------------------------------
# 4. Experiment control
# --------------------------------------------------------------------------
RANDOM_STATE = 42
TEST_SIZE = 0.20

# --------------------------------------------------------------------------
# 4b. Length-bias correction (training-set segmentation)
# --------------------------------------------------------------------------
# In the source corpus the Normal class consists of very short statements
# (median 7 informative tokens) whereas the three distress classes are
# long-form posts (median 46-62 tokens). Left uncorrected, a classifier learns
# document length as a proxy for the label and assigns "Normal" to almost any
# short entry - precisely the kind of entry a user of the deployed system
# types. Long TRAINING documents are therefore also represented as overlapping
# short windows that inherit the parent label, so that every class is seen at
# short lengths. The test set is never segmented, so evaluation remains honest.
AUGMENT_TRAINING = True
SEGMENT_WINDOW = 25          # tokens per window
SEGMENT_STRIDE = 18          # step between successive windows
MAX_SEGMENTS_PER_DOC = 4     # cap so that long posts do not dominate

# --------------------------------------------------------------------------
# 5. Interpretation shown to the user for each predicted class
# --------------------------------------------------------------------------
CLASS_INTERPRETATION = {
    "Normal": {
        "headline": "No clear signs of distress detected",
        "message": (
            "The language in your entry resembles that of everyday, non-distressed "
            "writing. This is not a clean bill of health, only a reading of the words "
            "you submitted on this occasion."
        ),
        "refer": False,
        "colour": "normal",
    },
    "Depression": {
        "headline": "Language consistent with depressive expression",
        "message": (
            "Your entry contains wording commonly associated with low mood, loss of "
            "interest, hopelessness or exhaustion. This is a language pattern, not a "
            "diagnosis."
        ),
        "refer": True,
        "colour": "depression",
    },
    "Anxiety": {
        "headline": "Language consistent with anxious expression",
        "message": (
            "Your entry contains wording commonly associated with worry, restlessness, "
            "fear or physical tension. This is a language pattern, not a diagnosis."
        ),
        "refer": True,
        "colour": "anxiety",
    },
    "Stress": {
        "headline": "Language consistent with stress",
        "message": (
            "Your entry contains wording commonly associated with pressure, overload or "
            "being unable to cope with demands. This is a language pattern, not a "
            "diagnosis."
        ),
        "refer": True,
        "colour": "stress",
    },
}

REFERRAL_NOTE = (
    "Consider speaking with someone you trust, or with a mental health professional. "
    "This system is a first-pass screening aid and does not provide a clinical diagnosis."
)

# Confidence below this value is reported to the user as a low-confidence result.
LOW_CONFIDENCE_THRESHOLD = 0.45
