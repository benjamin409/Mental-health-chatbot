# Dataset provenance

**File:** `data/raw/data.csv`

**Name:** Sentiment Analysis for Mental Health (also distributed as
"Combined Data.csv")

**Original publisher:** Suchintika Sarkar, published on Kaggle at
<https://www.kaggle.com/datasets/suchintikasarkar/sentiment-analysis-for-mental-health>

**Copy used in this project:** the mirror published in the public GitHub
repository `emirgocen03/mental-health-text-classification`, retrieved from

```
https://raw.githubusercontent.com/emirgocen03/mental-health-text-classification/main/data.csv
```

The Kaggle original requires an account; the GitHub mirror is byte-identical in
content and was used so that the pipeline can be reproduced without
authentication.

## Structure

Two columns:

| Column      | Description                                        |
|-------------|----------------------------------------------------|
| `statement` | A free-text English-language post or statement      |
| `status`    | The mental-health label assigned to that statement  |

## Composition as retrieved

53,043 records across seven labels:

| Label                | Records |
|----------------------|---------|
| Normal               | 16,351  |
| Depression           | 15,404  |
| Suicidal             | 10,653  |
| Anxiety              | 3,888   |
| Bipolar              | 2,877   |
| Stress               | 2,669   |
| Personality disorder | 1,201   |

The dataset is itself a compilation of several publicly released mental-health
text collections drawn from social-media platforms (principally Reddit and
Twitter) and from Kaggle datasets on depression and student stress.

## Use in this project

Only the four labels named in the project objectives are retained: **Normal,
Depression, Anxiety and Stress** (38,312 records before cleaning; 34,425 after
the removal of null entries, duplicates and records too short to carry usable
lexical evidence). The Suicidal, Bipolar and Personality-disorder classes are
excluded because they fall outside the scope defined in Chapter One.

## Ethical note

The corpus consists of text that was posted publicly and released for research
use; no identifying information is present in the `statement` column, and no
attempt is made in this project to re-identify any author. The labels are
community- or dataset-assigned and are **not** clinical diagnoses, which is why
the deployed system reports its output as a language pattern rather than as a
diagnostic result.
