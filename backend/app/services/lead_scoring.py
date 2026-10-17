"""XGBoost lead-intent scoring trained on explicitly synthetic chat examples.

This is a demo prioritization signal, not an admissions decision or a validated
conversion probability. Never use it to deny service or determine eligibility.
"""
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "data" / "synthetic_chat_enquiries.csv"
FEATURE_NAMES = [
    "has_message", "asks_fee", "asks_schedule", "asks_syllabus", "asks_demo",
    "near_term_timeline", "decision_signal", "requests_followup",
    "positive_intent", "objection_or_delay", "language_en", "language_hi", "language_mr",
]


def _has(text: str, *terms: str) -> bool:
    lowered = text.casefold()
    return any(term.casefold() in lowered for term in terms)


def extract_features(transcript: str, language: str = "unknown") -> list[float]:
    text = transcript.strip()
    return [
        float(bool(text)),
        float(_has(text, "fee", "fees", "budget", "फीस", "फी", "बजट")),
        float(_has(text, "schedule", "batch", "weekend", "timing", "when", "बॅच", "वेळ", "कब", "वीकेंड")),
        float(_has(text, "syllabus", "course outline", "अभ्यासक्रम", "सिलेबस")),
        float(_has(text, "demo", "डेमो")),
        float(_has(text, "next month", "this week", "tomorrow", "कल", "अगले महीने", "या आठवड्यात", "पुढच्या महिन्यात", "उद्या")),
        float(_has(text, "family", "decide", "ready to enroll", "दाखिला", "प्रवेश", "निर्णय")),
        float(_has(text, "call", "कॉल", "फोन")),
        float(_has(text, "join", "book", "ready to enroll", "दाखिला लेना", "प्रवेश घ्यायचा", "बुक")),
        float(_has(text, "comparing", "cannot decide", "later", "next year", "तुलना", "नंतर", "अगले साल")),
        float(language.lower() == "en"),
        float(language.lower() == "hi"),
        float(language.lower() == "mr"),
    ]


def _dataset_rows() -> tuple[list[list[float]], list[int]]:
    x: list[list[float]] = []
    y: list[int] = []
    with DATASET.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            x.append(extract_features(row["transcript"], row["language"]))
            y.append(int(row["converted"]))
    if len(x) < 30 or len(set(y)) < 2:
        raise RuntimeError("Synthetic training data must contain at least 30 examples and both labels.")
    return x, y


@lru_cache(maxsize=1)
def _model():
    try:
        from xgboost import XGBClassifier
    except ImportError as exc:
        raise RuntimeError("XGBoost is not installed. Install requirements.txt to enable lead scoring.") from exc
    x, y = _dataset_rows()
    model = XGBClassifier(
        n_estimators=80, max_depth=3, learning_rate=0.06,
        subsample=0.9, colsample_bytree=0.9, reg_lambda=1.0,
        objective="binary:logistic", eval_metric="logloss",
        random_state=42, n_jobs=1,
    )
    model.fit(x, y)
    return model


def score_transcript(transcript: str, language: str = "unknown") -> dict:
    if not transcript.strip():
        raise ValueError("transcript must not be empty")
    model = _model()
    features = extract_features(transcript, language)
    probability = float(model.predict_proba([features])[0][1])
    return {
        "score": round(probability * 100),
        "intent_probability": round(probability, 4),
        "band": "high" if probability >= 0.7 else "medium" if probability >= 0.4 else "low",
        "model": "XGBoost",
        "training_data": "synthetic_demo_only",
        "feature_names": FEATURE_NAMES,
        "disclaimer": "Experimental enquiry-priority estimate trained on synthetic data; not validated on real admissions outcomes and not suitable for eligibility, rejection, or automated high-impact decisions.",
    }


def training_summary() -> dict:
    x, y = _dataset_rows()
    return {"examples": len(y), "positive_labels": sum(y), "negative_labels": len(y) - sum(y), "features": len(FEATURE_NAMES), "labels_are_synthetic": True}
