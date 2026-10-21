"""
preprocess.py
-------------
Text pre-processing module for the Logistic Regression Based Mental Health
Monitoring System.

This module implements the data-preparation stage described in Chapter Three:
lowercasing, noise and punctuation removal, tokenization, stop-word removal
and lemmatization. It is imported by the training script and, later, by the
deployment layer, so that text submitted by a user at run time is transformed
by exactly the same procedure as the text used to train the classifier.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import TreebankWordTokenizer

sys.path.append(str(Path(__file__).resolve().parent))
from config import NLTK_DATA_DIR, POS_AWARE_LEMMATIZATION  # noqa: E402

# The corpora required by this module (stopwords and WordNet) are shipped with
# the project so that it runs without an internet connection.
if str(NLTK_DATA_DIR) not in nltk.data.path:
    nltk.data.path.insert(0, str(NLTK_DATA_DIR))


# --------------------------------------------------------------------------
# Regular expressions used for noise removal
# --------------------------------------------------------------------------
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
HTML_PATTERN = re.compile(r"<.*?>")
MENTION_PATTERN = re.compile(r"[@#]\w+")
NUMBER_PATTERN = re.compile(r"\b\d+\b")
NON_ALPHA_PATTERN = re.compile(r"[^a-z\s']")
MULTISPACE_PATTERN = re.compile(r"\s+")
REPEATED_CHAR_PATTERN = re.compile(r"(.)\1{2,}")

# Negation and first-person markers are deliberately retained. In mental-health
# text they carry the signal ("i can't", "no one", "not able to") that a generic
# stop-word list would otherwise discard.
# Mark-up and platform residue left behind by the scraping of the source
# corpus. These carry no psychological signal and are removed outright.
WEB_NOISE_TOKENS = {
    "quot", "amp", "nbsp", "lt", "gt", "apos", "http", "https", "www", "rt",
    "via", "retweet",
}

NEGATION_KEEP = {
    "no", "not", "nor", "never", "none", "cannot", "can't", "won't", "don't",
    "doesn't", "didn't", "isn't", "wasn't", "aren't", "weren't", "shouldn't",
    "couldn't", "wouldn't", "i", "me", "my", "myself", "am", "very", "too",
    "own", "against", "off", "out", "down", "under", "again", "more", "most",
    "only", "just", "should", "now", "why", "how",
}

# Clitics are matched without a leading word boundary, because the character
# preceding them ("do" in "don't") is itself a word character.
CLITICS = {
    "n't": " not", "'re": " are", "'s": " is", "'d": " would",
    "'ll": " will", "'ve": " have", "'m": " am",
}

CONTRACTIONS = {
    "can't": "cannot", "won't": "will not", "shan't": "shall not",
    "im": "i am", "ive": "i have", "dont": "do not", "cant": "cannot",
    "wont": "will not", "didnt": "did not", "doesnt": "does not",
    "isnt": "is not", "wasnt": "was not", "couldnt": "could not",
    "shouldnt": "should not", "wouldnt": "would not", "havent": "have not",
    "hasnt": "has not", "aint": "is not", "u": "you", "ur": "your",
    "abt": "about", "bc": "because", "rn": "right now", "idk": "i do not know",
}


class TextPreprocessor:
    """Applies the full pre-processing pipeline to a raw text string.

    The pipeline follows the sequence specified in the system design:

        raw text
          -> lowercasing
          -> expansion of contractions
          -> removal of URLs, mark-up, mentions, digits and punctuation
          -> tokenization
          -> stop-word removal (negation markers retained)
          -> lemmatization
          -> cleaned token string

    The class is deliberately stateless apart from its lexical resources so
    that a single instance can be reused for the whole corpus and, at
    deployment, for every incoming user submission.
    """

    def __init__(self, remove_stopwords: bool = True, lemmatize: bool = True,
                 min_token_length: int = 2,
                 pos_aware: bool = POS_AWARE_LEMMATIZATION) -> None:
        self.remove_stopwords = remove_stopwords
        self.lemmatize = lemmatize
        self.min_token_length = min_token_length
        self.pos_aware = pos_aware and lemmatize

        self.tokenizer = TreebankWordTokenizer()
        self.lemmatizer = WordNetLemmatizer() if lemmatize else None

        if self.pos_aware:
            try:                       # confirm the tagger data is present
                nltk.pos_tag(["test"])
            except LookupError:        # pragma: no cover - fallback path
                self.pos_aware = False

        base_stopwords = set(stopwords.words("english"))
        self.stop_words = base_stopwords - NEGATION_KEEP

    # ------------------------------------------------------------------
    # Individual stages
    # ------------------------------------------------------------------
    @staticmethod
    def normalise(text: str) -> str:
        """Lowercase the text and strip URLs, mark-up, mentions and digits."""
        text = html.unescape(html.unescape(str(text))).lower()
        text = URL_PATTERN.sub(" ", text)
        text = HTML_PATTERN.sub(" ", text)
        text = MENTION_PATTERN.sub(" ", text)
        text = REPEATED_CHAR_PATTERN.sub(r"\1\1", text)   # "sooooo" -> "soo"
        for short, long in CONTRACTIONS.items():
            text = re.sub(rf"\b{re.escape(short)}\b", long, text)
        for clitic, long in CLITICS.items():
            text = re.sub(rf"{re.escape(clitic)}\b", long, text)
        text = NUMBER_PATTERN.sub(" ", text)
        text = NON_ALPHA_PATTERN.sub(" ", text)
        text = MULTISPACE_PATTERN.sub(" ", text)
        return text.strip()

    def tokenize(self, text: str) -> list[str]:
        """Split normalised text into word tokens."""
        return self.tokenizer.tokenize(text)

    def filter_tokens(self, tokens: list[str]) -> list[str]:
        """Drop stop words, residual punctuation and very short tokens."""
        cleaned = []
        for token in tokens:
            token = token.strip("'")
            if len(token) < self.min_token_length:
                continue
            if token in WEB_NOISE_TOKENS:
                continue
            if self.remove_stopwords and token in self.stop_words:
                continue
            cleaned.append(token)
        return cleaned

    @staticmethod
    def wordnet_pos(penn_tag: str) -> str | None:
        """Map a Penn Treebank tag onto the WordNet part of speech to use.

        One case is treated deliberately rather than mechanically. A past
        participle (``VBN``) is mapped to the ADJECTIVE sense rather than the
        verb sense, because in this domain participles almost always appear
        predicatively - "I am tired", "I feel stressed", "I was overwhelmed",
        "stuck in traffic" - where they describe a state rather than an action.
        Lemmatising them as verbs rewrites "tired" to "tire", "stressed" to
        "stress" and "stuck" to "stick", which destroys exactly the words that
        carry the emotional signal.
        """
        if penn_tag.startswith("VBN") or penn_tag.startswith("JJ"):
            return "a"
        if penn_tag.startswith("VB"):
            return "v"
        if penn_tag.startswith("NN"):
            return "n"
        if penn_tag.startswith("RB"):
            return "r"
        return None                    # leave every other word class alone

    def lemmatize_tokens(self, tokens: list[str]) -> list[str]:
        """Reduce tokens to their dictionary form.

        With part-of-speech tagging available, each token is lemmatised once,
        under the word class it actually occupies in the sentence. Without it,
        the fallback applies the verb sense and then the noun sense, which
        collapses inflected forms without a tagger but mangles irregular
        participles.
        """
        if not self.lemmatize:
            return tokens

        if self.pos_aware:
            lemmatised = []
            for token, tag in nltk.pos_tag(tokens):
                pos = self.wordnet_pos(tag)
                lemmatised.append(
                    self.lemmatizer.lemmatize(token, pos=pos) if pos else token)
            return lemmatised

        lemmatised = []
        for token in tokens:
            token = self.lemmatizer.lemmatize(token, pos="v")
            token = self.lemmatizer.lemmatize(token, pos="n")
            lemmatised.append(token)
        return lemmatised

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def clean(self, text: str) -> str:
        """Run the complete pipeline and return the cleaned token string."""
        if text is None:
            return ""
        normalised = self.normalise(text)
        if not normalised:
            return ""
        tokens = self.tokenize(normalised)
        # Lemmatization comes before stop-word removal: the tagger needs the
        # full word sequence to assign parts of speech correctly, and removing
        # function words first would strip away the context it depends on.
        tokens = self.lemmatize_tokens(tokens)
        tokens = self.filter_tokens(tokens)
        tokens = [t for t in tokens if len(t) >= self.min_token_length]
        return " ".join(tokens)

    def clean_series(self, series) -> "object":
        """Apply :meth:`clean` to every element of a pandas Series."""
        return series.astype(str).map(self.clean)

    # Allows the object to be used directly as a callable, e.g. in a
    # scikit-learn FunctionTransformer.
    def __call__(self, text: str) -> str:
        return self.clean(text)


def demo() -> None:
    """Small demonstration used during development and in the appendices."""
    samples = [
        "I've been feeling so down lately, I can't get out of bed and nothing matters anymore.",
        "My heart won't stop racing and I keep worrying about everything, I can't relax at all.",
        "Work is piling up, deadlines everywhere, I'm completely overwhelmed and running on empty.",
        "Had a great day at school today, met up with friends and watched a movie afterwards.",
    ]
    pre = TextPreprocessor()
    for s in samples:
        print(f"RAW    : {s}")
        print(f"CLEANED: {pre.clean(s)}\n")


if __name__ == "__main__":
    demo()
