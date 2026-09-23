"""Data validation script for AgriSense AI.

Validates schema, data types, value boundaries, null values,
and class balance for the Crop Recommendation dataset.
"""

from pathlib import Path
import sys
import pandas as pd

REQUIRED_COLUMNS = [
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
    "label",
]

EXPECTED_CLASSES = 22
EXPECTED_SAMPLES_PER_CLASS = 100
EXPECTED_TOTAL_ROWS = EXPECTED_CLASSES * EXPECTED_SAMPLES_PER_CLASS

# Agronomically realistic boundaries for input parameters
FEATURE_BOUNDS = {
    "N": (0, 300),
    "P": (0, 300),
    "K": (0, 300),
    "temperature": (-10.0, 60.0),
    "humidity": (0.0, 100.0),
    "ph": (0.0, 14.0),
    "rainfall": (0.0, 1000.0),
}


def validate_dataset(filepath: Path) -> bool:
    """Validate dataset integrity and report detailed diagnostic metrics."""
    print(f"--> Validating dataset at: {filepath}")

    if not filepath.exists():
        print(f"Error: Dataset file not found at {filepath}")
        return False

    df = pd.read_csv(filepath)

    # 1. Row count check
    if len(df) != EXPECTED_TOTAL_ROWS:
        print(
            f"Error: Expected {EXPECTED_TOTAL_ROWS} rows, found {len(df)}."
        )
        return False

    # 2. Column presence and order
    actual_columns = list(df.columns)
    if actual_columns != REQUIRED_COLUMNS:
        print(
            f"Error: Column mismatch. Expected {REQUIRED_COLUMNS}, found {actual_columns}."
        )
        return False

    # 3. Missing values check
    null_counts = df.isnull().sum()
    if null_counts.any():
        print(f"Error: Missing values detected:\n{null_counts[null_counts > 0]}")
        return False

    # 4. Data types check
    for col in REQUIRED_COLUMNS[:-1]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            print(f"Error: Feature '{col}' is not numeric.")
            return False

    if not pd.api.types.is_string_dtype(df["label"]) and not pd.api.types.is_object_dtype(df["label"]):
        print("Error: Target 'label' is not string/object dtype.")
        return False

    # 5. Boundary assertions
    for col, (min_val, max_val) in FEATURE_BOUNDS.items():
        out_of_bounds = df[(df[col] < min_val) | (df[col] > max_val)]
        if not out_of_bounds.empty:
            print(
                f"Error: Feature '{col}' contains {len(out_of_bounds)} values out of bounds [{min_val}, {max_val}]."
            )
            return False

    # 6. Target class cardinality & balance
    class_counts = df["label"].value_counts()
    if len(class_counts) != EXPECTED_CLASSES:
        print(
            f"Error: Expected {EXPECTED_CLASSES} unique classes, found {len(class_counts)}."
        )
        return False

    unbalanced = class_counts[class_counts != EXPECTED_SAMPLES_PER_CLASS]
    if not unbalanced.empty:
        print(f"Error: Unbalanced classes detected:\n{unbalanced}")
        return False

    print("[OK] Dataset integrity validation passed:")
    print(f"  - Total records: {len(df)}")
    print(f"  - Features verified: {REQUIRED_COLUMNS[:-1]}")
    print(f"  - Unique target classes: {len(class_counts)} (100 samples each)")
    print(f"  - Nulls: 0 across all columns")
    print(f"  - All feature values fall within realistic agronomic bounds.")
    return True


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parents[2]
    default_path = base_dir / "data" / "raw" / "Crop_recommendation.csv"

    dataset_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path

    is_valid = validate_dataset(dataset_path)
    sys.exit(0 if is_valid else 1)
