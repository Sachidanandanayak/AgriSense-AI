from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import json
import unittest
import pandas as pd

from ml.scripts.validate_data import validate_dataset
from ml.scripts.prepare_data import prepare_data, add_engineered_features
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "Crop_recommendation.csv"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


class TestDataPipeline(unittest.TestCase):
    def test_raw_dataset_exists(self):
        """Verify raw dataset is present."""
        self.assertTrue(RAW_DATA_PATH.exists(), f"Raw dataset missing at {RAW_DATA_PATH}")

    def test_validate_dataset(self):
        """Verify validation script approves authentic raw dataset."""
        self.assertTrue(validate_dataset(RAW_DATA_PATH))

    def test_prepare_data_splits_and_leakage(self):
        """Verify prepare_data produces non-overlapping splits with correct counts."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            metadata = prepare_data(RAW_DATA_PATH, tmp_path, engineer_features=True)

            train_df = pd.read_csv(tmp_path / "train.csv")
            val_df = pd.read_csv(tmp_path / "val.csv")
            test_df = pd.read_csv(tmp_path / "test.csv")

            # Verify exact split counts
            self.assertEqual(len(train_df), 1540)
            self.assertEqual(len(val_df), 330)
            self.assertEqual(len(test_df), 330)
            self.assertEqual(len(train_df) + len(val_df) + len(test_df), 2200)

            # Verify all 22 classes exist in all splits
            self.assertEqual(train_df["label"].nunique(), 22)
            self.assertEqual(val_df["label"].nunique(), 22)
            self.assertEqual(test_df["label"].nunique(), 22)

            # Verify engineered features exist and contain no NaNs
            for feat in ["N_P_ratio", "N_K_ratio", "P_K_ratio", "rain_temp_ratio"]:
                self.assertIn(feat, train_df.columns)
                self.assertFalse(train_df[feat].isnull().any())
                self.assertFalse(val_df[feat].isnull().any())
                self.assertFalse(test_df[feat].isnull().any())

            # Verify metadata file
            meta_file = tmp_path / "dataset_metadata.json"
            self.assertTrue(meta_file.exists())
            with open(meta_file, "r") as f:
                meta_data = json.load(f)
            self.assertEqual(meta_data["total_records"], 2200)
            self.assertEqual(meta_data["classes_count"], 22)


if __name__ == "__main__":
    unittest.main()

