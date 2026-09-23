"""Unit tests for trained AgriSense AI baseline model artifact and inference."""

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import json
import unittest
import joblib
import numpy as np
import pandas as pd

from ml.scripts.train_model import get_top_k_recommendations
MODEL_PATH = BASE_DIR / "ml" / "models" / "crop_recommendation_model.joblib"
METRICS_PATH = BASE_DIR / "ml" / "models" / "metrics.json"
TEST_DATA_PATH = BASE_DIR / "data" / "processed" / "test.csv"


class TestModelArtifactsAndInference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Ensure test dataset exists before running tests."""
        if not TEST_DATA_PATH.exists():
            raise unittest.SkipTest(f"Test dataset not found at {TEST_DATA_PATH}")

    def test_01_model_artifact_exists(self):
        """1. Verify model artifact exists after training."""
        self.assertTrue(MODEL_PATH.exists(), f"Model file missing at {MODEL_PATH}")
        self.assertTrue(METRICS_PATH.exists(), f"Metrics file missing at {METRICS_PATH}")

    def test_02_model_can_be_loaded(self):
        """2. Verify model can be loaded from disk."""
        package = joblib.load(MODEL_PATH)
        self.assertIsInstance(package, dict)
        self.assertIn("model", package)
        self.assertIn("feature_names", package)
        self.assertIn("classes", package)
        self.assertIsNotNone(package["model"])

    def test_03_model_predicts_valid_crop(self):
        """3. Verify loaded model can predict a valid crop name."""
        package = joblib.load(MODEL_PATH)
        model = package["model"]
        feature_names = package["feature_names"]
        classes = package["classes"]

        test_df = pd.read_csv(TEST_DATA_PATH)
        sample_x = test_df[feature_names].iloc[0:1]

        prediction = model.predict(sample_x)[0]
        self.assertIsInstance(prediction, str)
        self.assertIn(prediction, classes)

    def test_04_predict_proba_returns_probabilities(self):
        """4. Verify predict_proba() returns probabilities for all classes."""
        package = joblib.load(MODEL_PATH)
        model = package["model"]
        feature_names = package["feature_names"]

        test_df = pd.read_csv(TEST_DATA_PATH)
        sample_x = test_df[feature_names].iloc[0:1]

        probs = model.predict_proba(sample_x)
        self.assertIsInstance(probs, np.ndarray)
        self.assertEqual(probs.shape[0], 1)
        self.assertEqual(probs.shape[1], len(model.classes_))

    def test_05_probability_values_are_valid(self):
        """5. Verify probability values are non-negative and sum to 1.0."""
        package = joblib.load(MODEL_PATH)
        model = package["model"]
        feature_names = package["feature_names"]

        test_df = pd.read_csv(TEST_DATA_PATH)
        sample_x = test_df[feature_names].iloc[0:5]

        probs = model.predict_proba(sample_x)
        # All probabilities between 0 and 1
        self.assertTrue(np.all(probs >= 0.0))
        self.assertTrue(np.all(probs <= 1.0))
        # Sum of probabilities per sample equals 1.0 (within float precision)
        sums = np.sum(probs, axis=1)
        np.testing.assert_allclose(sums, np.ones(5), rtol=1e-5)

    def test_06_number_of_classes_matches_class_list(self):
        """6. Verify number of model classes matches the 22 trained classes."""
        package = joblib.load(MODEL_PATH)
        model = package["model"]
        classes = package["classes"]

        self.assertEqual(len(classes), 22)
        self.assertEqual(len(model.classes_), 22)
        self.assertEqual(sorted(classes), sorted(list(model.classes_)))

    def test_07_top_k_recommendation_helper(self):
        """7. Verify Top-K recommendation helper returns sorted unique predictions."""
        package = joblib.load(MODEL_PATH)
        model = package["model"]
        feature_names = package["feature_names"]
        classes = package["classes"]

        test_df = pd.read_csv(TEST_DATA_PATH)
        sample_x = test_df[feature_names].iloc[0]

        top3 = get_top_k_recommendations(model, sample_x, classes, k=3)
        self.assertEqual(len(top3), 3)

        # Ensure monotonically decreasing confidence
        self.assertGreaterEqual(top3[0]["confidence_estimate"], top3[1]["confidence_estimate"])
        self.assertGreaterEqual(top3[1]["confidence_estimate"], top3[2]["confidence_estimate"])

        # Ensure all 3 crops are unique
        crop_names = [item["crop"] for item in top3]
        self.assertEqual(len(set(crop_names)), 3)


if __name__ == "__main__":
    unittest.main()
