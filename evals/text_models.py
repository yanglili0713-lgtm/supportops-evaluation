from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from rag.retriever import tokenize


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    shared = set(left) & set(right)
    if not shared:
        return 0.0
    numerator = sum(left[token] * right[token] for token in shared)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


class TfidfVectorizer:
    def __init__(self, max_features: int = 5000, min_df: int = 1) -> None:
        self.max_features = max_features
        self.min_df = min_df
        self.vocabulary_: dict[str, int] = {}
        self.idf_: dict[str, float] = {}

    def fit(self, texts: list[str]) -> "TfidfVectorizer":
        df: Counter[str] = Counter()
        for text in texts:
            df.update(set(tokenize(text)))

        terms = [term for term, freq in df.items() if freq >= self.min_df]
        terms.sort(key=lambda term: (-df[term], term))
        terms = terms[: self.max_features]

        total_docs = max(1, len(texts))
        self.vocabulary_ = {term: idx for idx, term in enumerate(terms)}
        self.idf_ = {
            term: math.log((1 + total_docs) / (1 + df[term])) + 1.0 for term in terms
        }
        return self

    def transform(self, text: str) -> dict[str, float]:
        tokens = tokenize(text)
        counts = Counter(tokens)
        total = sum(counts.values()) or 1
        vector: dict[str, float] = {}
        for token, count in counts.items():
            if token not in self.vocabulary_:
                continue
            tf = count / total
            vector[token] = tf * self.idf_.get(token, 1.0)
        return vector

    def fit_transform(self, texts: list[str]) -> list[dict[str, float]]:
        self.fit(texts)
        return [self.transform(text) for text in texts]


@dataclass
class LogisticRegressionResult:
    label: str
    score: float


class SparseMulticlassLogisticRegression:
    def __init__(
        self,
        max_features: int = 5000,
        learning_rate: float = 0.4,
        epochs: int = 8,
        l2: float = 1e-4,
        seed: int = 13,
    ) -> None:
        self.vectorizer = TfidfVectorizer(max_features=max_features)
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.l2 = l2
        self.seed = seed
        self.labels_: list[str] = []
        self.weights_: dict[str, dict[str, float]] = {}
        self.bias_: dict[str, float] = {}

    def fit(self, texts: list[str], labels: list[str]) -> "SparseMulticlassLogisticRegression":
        if len(texts) != len(labels):
            raise ValueError("texts and labels must have the same length")
        self.vectorizer.fit(texts)
        features = [self.vectorizer.transform(text) for text in texts]
        self.labels_ = sorted(set(labels))
        self.weights_ = {label: defaultdict(float) for label in self.labels_}
        self.bias_ = {label: 0.0 for label in self.labels_}

        indices = list(range(len(texts)))
        rng = random.Random(self.seed)

        for _ in range(self.epochs):
            rng.shuffle(indices)
            for idx in indices:
                x = features[idx]
                gold = labels[idx]
                logits = {label: self._score_label(label, x) for label in self.labels_}
                probs = _softmax(logits)
                for label in self.labels_:
                    target = 1.0 if label == gold else 0.0
                    error = probs[label] - target
                    self.bias_[label] -= self.learning_rate * error
                    weights = self.weights_[label]
                    for token, value in x.items():
                        gradient = error * value + self.l2 * weights[token]
                        weights[token] -= self.learning_rate * gradient
        return self

    def predict(self, texts: list[str]) -> list[str]:
        return [self.predict_one(text).label for text in texts]

    def predict_one(self, text: str) -> LogisticRegressionResult:
        x = self.vectorizer.transform(text)
        logits = {label: self._score_label(label, x) for label in self.labels_}
        if not logits:
            return LogisticRegressionResult(label="", score=0.0)
        label = max(logits, key=logits.get)
        return LogisticRegressionResult(label=label, score=logits[label])

    def predict_proba(self, texts: list[str]) -> list[dict[str, float]]:
        results = []
        for text in texts:
            x = self.vectorizer.transform(text)
            logits = {label: self._score_label(label, x) for label in self.labels_}
            results.append(_softmax(logits))
        return results

    def _score_label(self, label: str, x: dict[str, float]) -> float:
        score = self.bias_.get(label, 0.0)
        weights = self.weights_.get(label, {})
        for token, value in x.items():
            score += weights.get(token, 0.0) * value
        return score


def _softmax(logits: dict[str, float]) -> dict[str, float]:
    if not logits:
        return {}
    max_logit = max(logits.values())
    exp_values = {label: math.exp(value - max_logit) for label, value in logits.items()}
    total = sum(exp_values.values()) or 1.0
    return {label: value / total for label, value in exp_values.items()}
