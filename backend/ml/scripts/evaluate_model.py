"""Standalone evaluation script for trained AgriSense AI models.

Loads a saved model artifact, executes inference against a specified dataset
partition, and outputs performance diagnostics and top-k predictions.
"""

import argparse
from pathlib import Path
import sys

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
)
from ml.scripts.train_model import get_top_k_recommendations


def evaluate_saved_model(model_path: Path, data_path: Path, top_k: int = 3):
    """Load model artifact and evaluate on target dataset."""
    print(f"--> Loading model from: {model_path}")
    if not model_path.exists():
        print(f"Error: Model file does not exist at {model_path}")
        return False

    package = joblib.load(model_path)
    model = package["model"]
    feature_names = package["feature_names"]
    classes = package["classes"]

    print(f"--> Loading dataset from: {data_path}")
    if not data_path.exists():
        print(f"Error: Dataset does not exist at {data_path}")
        return False

    df = pd.read_csv(data_path)
    target_col = "label"

    X = df[feature_names]
    y = df[target_col]

    preds = model.predict(X)
    probs = model.predict_proba(X)

    acc = accuracy_score(y, preds)
    macro_f1 = f1_score(y, preds, average="macro")
    weighted_f1 = f1_score(y, preds, average="weighted")
    macro_prec = precision_score(y, preds, average="macro", zero_division=0)
    macro_rec = recall_score(y, preds, average="macro", zero_division=0)
    loss = log_loss(y, probs, labels=model.classes_)

    print("[OK] Evaluation Summary:")
    print(f"  - Dataset:          {data_path.name} ({len(df)} samples)")
    print(f"  - Accuracy:         {acc:.4f} ({acc * 100:.2f}%)")
    print(f"  - Macro F1:         {macro_f1:.4f}")
    print(f"  - Weighted F1:      {weighted_f1:.4f}")
    print(f"  - Macro Precision:  {macro_prec:.4f}")
    print(f"  - Macro Recall:     {macro_rec:.4f}")
    print(f"  - Multi-class Loss: {loss:.4f}")

    # Top-K Demo on first sample
    sample_feat = X.iloc[0]
    sample_true = y.iloc[0]
    top_recs = get_top_k_recommendations(model, sample_feat, classes, feature_names=feature_names, k=top_k)

    print(f"\n--> Top-{top_k} Prediction on Sample #0 (Actual: {sample_true}):")
    for item in top_recs:
        print(f"    Rank {item['rank']}: {item['crop']} - {item['confidence_percentage']} (model confidence estimate)")

    return True


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parents[2]
    default_model = base_dir / "ml" / "models" / "crop_recommendation_model.joblib"
    default_data = base_dir / "data" / "processed" / "test.csv"

    parser = argparse.ArgumentParser(description="Evaluate trained AgriSense AI model.")
    parser.add_argument("--model", type=Path, default=default_model, help="Path to saved model (.joblib)")
    parser.add_argument("--data", type=Path, default=default_data, help="Path to evaluation dataset (.csv)")
    parser.add_argument("--top_k", type=int, default=3, help="Number of top predictions to display")

    args = parser.parse_args()
    success = evaluate_saved_model(args.model, args.data, args.top_k)
    sys.exit(0 if success else 1)
