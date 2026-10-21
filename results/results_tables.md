# Chapter Four - Results Tables

Selected model: **Logistic Regression**

## Table 4.1: Comparative performance of the three classifiers

| Model                  |   Accuracy |   Precision |   Recall |   F1-score |   Macro F1 |   CV F1 (5-fold) |   Training time (s) |
|:-----------------------|-----------:|------------:|---------:|-----------:|-----------:|-----------------:|--------------------:|
| Logistic Regression    |     0.8485 |      0.8589 |   0.8485 |     0.8527 |     0.7568 |           0.8272 |                7.34 |
| Support Vector Machine |     0.8396 |      0.8418 |   0.8396 |     0.8302 |     0.7198 |           0.845  |                7.34 |
| Random Forest          |     0.8175 |      0.8428 |   0.8175 |     0.793  |     0.6257 |           0.7776 |              392.02 |

## Table 4.2: Per-class performance of the Logistic Regression

| Class      |   Precision |   Recall |   F1-score |   Support |
|:-----------|------------:|---------:|-----------:|----------:|
| Normal     |      0.932  |   0.8811 |     0.9059 |      2692 |
| Depression |      0.8929 |   0.8765 |     0.8846 |      3005 |
| Anxiety    |      0.7095 |   0.8073 |     0.7553 |       711 |
| Stress     |      0.4367 |   0.5361 |     0.4813 |       457 |

## Table 4.3: Confusion matrix (counts)

|                   |   Predicted Normal |   Predicted Depression |   Predicted Anxiety |   Predicted Stress |
|:------------------|-------------------:|-----------------------:|--------------------:|-------------------:|
| Actual Normal     |               2372 |                    128 |                  61 |                131 |
| Actual Depression |                118 |                   2634 |                 116 |                137 |
| Actual Anxiety    |                 31 |                     58 |                 574 |                 48 |
| Actual Stress     |                 24 |                    130 |                  58 |                245 |


## Table 4.4: Effect of the length-bias correction (weighted F1)

| Model                  |   Full text, baseline |   Full text, corrected |   Short entry, baseline |   Short entry, corrected |
|:-----------------------|----------------------:|-----------------------:|------------------------:|-------------------------:|
| Logistic Regression    |                0.8622 |                 0.8527 |                  0.7721 |                   0.8173 |
| Support Vector Machine |                0.8553 |                 0.8302 |                  0.7684 |                   0.8187 |
| Random Forest          |                0.7901 |                 0.793  |                  0.7253 |                   0.7874 |

The corrected model gives up a little accuracy on full-length documents in exchange for a substantial gain on short entries, which is the condition under which the deployed system actually operates.
