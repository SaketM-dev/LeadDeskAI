"""Train and evaluate the demo XGBoost model on synthetic chat data.

Run from the repository root: python scripts/train_lead_scoring.py
Metrics are only a sanity check because the labels and examples are synthetic.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.lead_scoring import DATASET, _dataset_rows, extract_features, FEATURE_NAMES

from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split


def main():
    x, y = _dataset_rows()
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y
    )
    model = XGBClassifier(
        n_estimators=80, max_depth=3, learning_rate=0.06,
        subsample=0.9, colsample_bytree=0.9, reg_lambda=1.0,
        objective="binary:logistic", eval_metric="logloss",
        random_state=42, n_jobs=1,
    )
    model.fit(x_train, y_train)
    probabilities = model.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    report = {
        "dataset": str(DATASET.relative_to(ROOT)),
        "examples": len(y),
        "features": FEATURE_NAMES,
        "test_accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "test_roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4) if len(set(y_test)) > 1 else None,
        "warning": "Synthetic-only evaluation; not evidence of real-world admissions prediction performance.",
    }
    output = ROOT / "artifacts" / "lead_intent_xgboost.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(output)
    (ROOT / "artifacts" / "lead_intent_training_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps({**report, "model_path": str(output.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
