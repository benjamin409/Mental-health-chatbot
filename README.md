# A Logistic Regression Based Mental Health Monitoring System

Machine-learning component of the BSc project submitted to the Department of
Computer Science, University of Nigeria, Nsukka.

The system classifies a piece of free-text writing into one of four categories
— **Normal, Depression, Anxiety, Stress** — using a classical supervised
text-classification pipeline: NLP pre-processing, TF-IDF feature extraction,
and a comparison of three classifiers (Logistic Regression, Support Vector
Machine, Random Forest).

> The system reports a **language pattern**, not a clinical diagnosis. Where a
> distress class is returned, the user is prompted to speak to someone they
> trust or to a mental health professional.

---

## 1. Project structure

```
mhms/
├── data/
│   ├── raw/
│   │   ├── data.csv                  raw labelled corpus (53,043 records)
│   │   └── SOURCE.md                 dataset provenance and ethics note
│   └── processed/
│       ├── clean_dataset.csv         cleaned 4-class corpus (34,425 records)
│       ├── train.csv                 80% stratified training split
│       ├── train_augmented.csv       training split + short windows
│       └── test.csv                  20% stratified held-out test split
├── models/
│   ├── tfidf_vectorizer.pkl          fitted TF-IDF vectorizer
│   ├── best_model.pkl                selected classifier
│   ├── model_*.pkl                   all three trained classifiers
│   └── model_metadata.json           full metrics and configuration
├── results/
│   ├── figures/                      Chapter Four figures (PNG, 300 dpi)
│   ├── metrics.json                  every metric produced by training
│   ├── results_tables.md             Chapter Four tables
│   ├── table_4_*.csv                 the same tables as CSV
│   ├── data_profile.json             corpus profile
│   └── train_log*.txt                raw training console output
├── nltk_data/                        bundled NLTK corpora (runs offline)
├── src/
│   ├── config.py                     all paths, parameters and constants
│   ├── preprocess.py                 the NLP pre-processing pipeline
│   ├── prepare_data.py               data understanding and preparation
│   ├── train.py                      modelling and evaluation
│   ├── evaluate.py                   figures and results tables
│   ├── predict.py                    the classification service
│   ├── ablation_length_bias.py       the length-bias diagnostic experiment
│   └── test_system.py                verification script
├── service/
│   ├── app.py                        Flask inference API (the middle layer)
│   ├── API.md                        interface specification for the frontend
│   └── test_api.py                   40-check API verification suite
├── SETUP.md                          Windows + VS Code setup guide
└── requirements.txt
```

## 2. Installation

**Windows users: follow `SETUP.md` instead** — it is a step-by-step guide with
a verification check after every stage, plus troubleshooting for the problems
Windows actually throws up.

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

scikit-learn, numpy and scipy are pinned in `requirements.txt` because the
model in `models/` was serialised with those versions. If you install different
ones the model still loads, but it reports a version-mismatch note; retraining
with `python src/train.py --no-cv` regenerates the files for your versions.

No NLTK download is required — the `stopwords` and `wordnet` corpora are
bundled in `nltk_data/` so the system runs without an internet connection.

## 3. Reproducing the pipeline

```bash
python src/prepare_data.py     # clean, split and segment the corpus  (~35 s)
python src/train.py            # train and compare the three models   (~15 min)
python src/evaluate.py         # regenerate all figures and tables    (~10 s)
python src/test_system.py      # verification suite
```

Useful flags:

```bash
python src/train.py --no-cv                 # skip 5-fold cross-validation
python src/train.py --no-augment --no-save  # reproduce the length-biased baseline
python src/ablation_length_bias.py          # the full segmentation ablation
```

Every run is seeded with `random_state = 42`, so the reported figures are
reproducible.

## 4. Classifying text

```bash
python src/predict.py "I have not been sleeping and nothing interests me anymore"
python src/predict.py                        # interactive mode
```

From Python:

```python
from src.predict import MentalHealthClassifier

classifier = MentalHealthClassifier()
result = classifier.predict("I feel overwhelmed by everything I have to do")
print(result.predicted_class, result.confidence, result.probabilities)
```

## 5. The pipeline in brief

**Pre-processing** (`preprocess.py`): lowercasing → contraction expansion →
removal of URLs, mark-up, mentions, digits and punctuation → tokenization
(Treebank) → stop-word removal → lemmatization (WordNet).

Two deliberate departures from the textbook recipe are documented in the code:
negation and first-person markers (`not`, `never`, `no one`, `i`, `my`) are
**retained** rather than removed as stop words, because in mental-health text
they carry the signal; and elongated spellings (`sooooo`) are collapsed rather
than discarded.

**Feature extraction**: TF-IDF over unigrams and bigrams, 15,000 features,
`min_df = 3`, `max_df = 0.85`, sublinear term frequency.

**Classification**: Logistic Regression, a calibrated Linear SVM and a Random
Forest, all fitted on identical features and the same split, all with class
weighting to correct the 6.58 : 1 imbalance between the largest and smallest
class.

## 6. The length-bias correction

In the source corpus the `Normal` class consists of very short statements
(median **7** informative tokens) while the three distress classes are
long-form posts (median **46–62**). A model trained on the corpus as supplied
therefore learns document length as a proxy for the label and returns `Normal`
for almost any short entry — which is exactly what a user of the deployed
system types.

The remedy implemented here segments **training** documents into overlapping
25-token windows that inherit the parent label, so every class is represented
at short lengths. The **test set is never segmented**, so the reported
evaluation remains honest. `src/ablation_length_bias.py` reproduces the
comparison; the trade-off it measures is reported in Chapter Four.

## 7. The inference service

The model is served to the presentation layer over HTTP by a small Flask
application, so that the Node/Express frontend never has to load a scikit-learn
model.

```bash
python service/app.py         # 127.0.0.1:5001
python service/test_api.py    # 40 checks, in a second terminal
```

| Endpoint               | Purpose |
|------------------------|---------|
| `GET /health`          | Liveness probe |
| `GET /info`            | Deployed model description and input constraints |
| `POST /classify`       | Classify one submission |
| `POST /classify/batch` | Classify up to 50 submissions |

```bash
curl -X POST http://127.0.0.1:5001/classify \
     -H "Content-Type: application/json" \
     -d '{"text":"I keep worrying about everything and my heart races"}'
```

The full interface specification — request and response schemas, every error
code, and the Express client code — is in **`service/API.md`**, written so it
can go into the appendices as it stands.

Three rules govern the split, and they are worth being able to state at
defence:

- **The client sends raw text.** All pre-processing happens server-side, using
  the identical pipeline that produced the training features. Cleaning text in
  JavaScript before sending it would break the correspondence between training
  and inference and degrade every prediction silently.
- **The service is stateless.** Session tokens, submission history and the
  SQLite database belong to the Node layer.
- **The model loads once**, at start-up. Run the service with a single worker;
  each worker holds its own copy of the model.

## 8. Results obtained

Held-out test set: 6,881 records, never seen during training.

| Model                  | Accuracy | Precision | Recall | F1 (weighted) | F1 (macro) |
|------------------------|---------:|----------:|-------:|--------------:|-----------:|
| **Logistic Regression**|   0.8493 |    0.8558 | 0.8493 |    **0.8516** |     0.7610 |
| Support Vector Machine |   0.8391 |    0.8427 | 0.8391 |        0.8304 |     0.7247 |
| Random Forest          |   0.8166 |    0.8399 | 0.8166 |        0.7924 |     0.6242 |

**Logistic Regression** is selected: it obtains the highest weighted and macro
F1, trains in 12 seconds against the Random Forest's 419, and its coefficients
are directly interpretable (see `fig_4_5_top_features.png`).

Per class, the selected model reaches F1 = 0.91 (Normal), 0.88 (Depression),
0.77 (Anxiety) and 0.49 (Stress).

## 9. Known limitations

These are stated plainly because they are the questions an examiner will ask.

1. **Stress is the weak class.** With only 2,285 records (6.6% of the corpus)
   and heavy lexical overlap with Depression and Anxiety, it reaches F1 = 0.49;
   36% of true Stress entries are predicted as Depression. Class weighting and
   segmentation both improve it, but it remains the ceiling on macro F1.
2. **The corpus is a compilation, and it shows.** The `Normal` class is drawn
   from a different source domain than the three distress classes — shorter,
   partly machine-translated messages. Some of its most informative terms are
   therefore platform artefacts rather than psychological signal: `wa`
   (WhatsApp), `twitter`, `doe` (slang for "though"), `ha` (laughter) and `le`
   (a Spanish fragment) all survive cleaning because they are genuine tokens in
   the source text, not pre-processing errors. HTML entities (`&quot;`) and
   URLs are removed; residual non-English fragments are not.
3. **The labels are not clinical.** They were assigned by dataset compilers on
   the basis of the community a post came from, not by a clinician. The system
   accordingly reports a language pattern and its confidence, never a diagnosis.
4. **English only.** Nigerian Pidgin and code-switched text are not represented
   in the training corpus and should not be expected to classify correctly.
5. **No temporal or per-user modelling.** Each submission is classified
   independently; the system does not track change in a person's writing over
   time, which is the natural next step identified in Chapter Five.

## 10. Ethical position

The corpus contains publicly posted text released for research use, and its
labels are community- or dataset-assigned rather than clinically assigned. The
system is a first-pass screening aid: it reports a language pattern, states its
confidence, refuses submissions too short to classify, and directs users
towards human support rather than towards a diagnosis.
