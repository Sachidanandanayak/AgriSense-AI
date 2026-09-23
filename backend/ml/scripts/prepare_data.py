"""Data preparation pipeline script for AgriSense AI.

Performs:
1. Stratified Train / Validation / Test split (70% / 15% / 15%)
2. Verification of split stratification and mutual exclusivity (zero leakage)
3. Optional calculation of agronomic interaction features (N/P, N/K, P/K, Rain/Temp)
4. Export to backend/data/processed/
5. Generation of dataset metadata manifest
"""

import json
from pathlib import Path
import sys
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit

RANDOM_STATE = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15


def add_engineered_features(df: pd.DataFrame, epsilon: float = 1e-5) -> pd.DataFrame:
    """Compute domain-specific agronomic ratio features."""
    df_feat = df.copy()
    df_feat["N_P_ratio"] = df_feat["N"] / (df_feat["P"] + epsilon)
    df_feat["N_K_ratio"] = df_feat["N"] / (df_feat["K"] + epsilon)
    df_feat["P_K_ratio"] = df_feat["P"] / (df_feat["K"] + epsilon)
    df_feat["rain_temp_ratio"] = df_feat["rainfall"] / (df_feat["temperature"] + epsilon)
    return df_feat


def prepare_data(
    input_file: Path,
    output_dir: Path,
    engineer_features: bool = True,
    random_state: int = RANDOM_STATE,
) -> dict:
    """Execute stratified split and data preparation."""
    print(f"--> Ingesting raw dataset: {input_file}")
    df = pd.read_csv(input_file)

    target_col = "label"
    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Total 2,200 rows -> 1,540 train (70 per crop), 330 val (15 per crop), 330 test (15 per crop)
    n_total = len(df)
    n_test = int(round(n_total * TEST_RATIO))
    n_val = int(round(n_total * VAL_RATIO))
    n_temp = n_val + n_test

    # First split: Train (1,540) vs Temp (660)
    split_1 = StratifiedShuffleSplit(
        n_splits=1,
        test_size=n_temp,
        random_state=random_state,
    )
    train_idx, temp_idx = next(split_1.split(X, y))

    # Second split: Temp (660) into Val (330) and Test (330)
    X_temp = X.iloc[temp_idx]
    y_temp = y.iloc[temp_idx]

    split_2 = StratifiedShuffleSplit(
        n_splits=1,
        test_size=n_test,
        random_state=random_state,
    )
    val_rel_idx, test_rel_idx = next(split_2.split(X_temp, y_temp))

    val_idx = temp_idx[val_rel_idx]
    test_idx = temp_idx[test_rel_idx]

    # Verify zero leakage (no overlapping indices)
    train_set = set(train_idx)
    val_set = set(val_idx)
    test_set = set(test_idx)

    assert len(train_set & val_set) == 0, "Error: Data leakage between Train and Val sets!"
    assert len(train_set & test_set) == 0, "Error: Data leakage between Train and Test sets!"
    assert len(val_set & test_set) == 0, "Error: Data leakage between Val and Test sets!"
    assert len(train_set) + len(val_set) + len(test_set) == len(df), "Error: Row count mismatch in splits!"

    train_df = df.iloc[train_idx].copy().reset_index(drop=True)
    val_df = df.iloc[val_idx].copy().reset_index(drop=True)
    test_df = df.iloc[test_idx].copy().reset_index(drop=True)

    if engineer_features:
        print("--> Generating domain-specific agronomic ratio features...")
        train_df = add_engineered_features(train_df)
        val_df = add_engineered_features(val_df)
        test_df = add_engineered_features(test_df)

    output_dir.mkdir(parents=True, exist_ok=True)
    train_path = output_dir / "train.csv"
    val_path = output_dir / "val.csv"
    test_path = output_dir / "test.csv"
    metadata_path = output_dir / "dataset_metadata.json"

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    metadata = {
        "source_dataset": str(input_file.name),
        "total_records": len(df),
        "train_records": len(train_df),
        "val_records": len(val_df),
        "test_records": len(test_df),
        "train_ratio": TRAIN_RATIO,
        "val_ratio": VAL_RATIO,
        "test_ratio": TEST_RATIO,
        "classes_count": int(df[target_col].nunique()),
        "classes": sorted(df[target_col].unique().tolist()),
        "features_raw": [c for c in df.columns if c != target_col],
        "features_engineered": [
            c for c in train_df.columns if c not in df.columns and c != target_col
        ],
        "all_feature_columns": [c for c in train_df.columns if c != target_col],
        "target_column": target_col,
        "random_state": random_state,
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"[OK] Data preparation complete. Files saved to: {output_dir}")
    print(f"  - Train split: {len(train_df)} rows -> {train_path.name}")
    print(f"  - Val split:   {len(val_df)} rows -> {val_path.name}")
    print(f"  - Test split:  {len(test_df)} rows -> {test_path.name}")
    print(f"  - Metadata:    {metadata_path.name}")
    return metadata


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parents[2]
    raw_csv = base_dir / "data" / "raw" / "Crop_recommendation.csv"
    processed_dir = base_dir / "data" / "processed"

    prepare_data(raw_csv, processed_dir)
