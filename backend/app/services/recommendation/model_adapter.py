"""Model adapter for trained Crop Recommendation Random Forest model.

Provides a safe, schema-validated inference wrapper around the Phase 3 trained
model artifact (`crop_recommendation_model.joblib`). Enforces exact training feature
order, validates feature completeness, prevents silent imputation, and returns
deterministic top-K recommendations with model probability estimates.
"""

from __future__ import annotations

import logging
from pathlib import Path
import threading
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.services.recommendation.exceptions import (
    IncompatibleFeatureSchemaError,
    MissingModelInputError,
    ModelPredictionError,
    ModelUnavailableError,
)
from app.services.recommendation.schemas import (
    AgriculturalInput,
    CropRecommendationItem,
)

logger = logging.getLogger(__name__)

# Exact 11 feature columns and ordering expected by the trained Random Forest model
EXPECTED_MODEL_FEATURES: list[str] = [
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
    "N_P_ratio",
    "N_K_ratio",
    "P_K_ratio",
    "rain_temp_ratio",
]

DEFAULT_MODEL_PATH: Path = (
    Path(__file__).resolve().parents[3]
    / "ml"
    / "models"
    / "crop_recommendation_model.joblib"
)


class CropModelAdapter:
    """Safe, thread-safe inference adapter for the benchmark crop recommendation model."""

    def __init__(self, model_path: Path | str | None = None) -> None:
        """Initialize adapter. Model is loaded lazily on first prediction or explicit call.

        Args:
            model_path: Optional custom path to model artifact (defaults to project artifact).
        """
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self._model: Any | None = None
        self._classes: list[str] | None = None
        self._feature_names: list[str] | None = None
        self._model_metadata: dict[str, Any] = {}
        self._lock = threading.Lock()

    @property
    def is_loaded(self) -> bool:
        """Return True if model is loaded and ready."""
        return self._model is not None

    @property
    def classes(self) -> list[str]:
        """Return list of supported crop class labels."""
        self.load_model()
        assert self._classes is not None
        return list(self._classes)

    @property
    def feature_names(self) -> list[str]:
        """Return exact feature column names in training order."""
        self.load_model()
        assert self._feature_names is not None
        return list(self._feature_names)

    def load_model(self) -> None:
        """Load and validate model artifact from disk in a thread-safe manner.

        Raises:
            ModelUnavailableError: If model file does not exist or payload is corrupted.
            IncompatibleFeatureSchemaError: If artifact features do not match expected 11 features.
        """
        if self._model is not None:
            return

        with self._lock:
            if self._model is not None:
                return

            if not self.model_path.exists():
                logger.error("Trained model artifact not found at: %s", self.model_path)
                raise ModelUnavailableError(
                    f"Crop recommendation model artifact not found at: {self.model_path}"
                )

            try:
                package = joblib.load(self.model_path)
            except Exception as exc:
                logger.error("Failed to load model artifact from %s: %s", self.model_path, exc)
                raise ModelUnavailableError(
                    f"Failed to deserialize model artifact at {self.model_path}: {exc}"
                ) from exc

            if not isinstance(package, dict):
                raise ModelUnavailableError(
                    "Model artifact is malformed; expected a dictionary payload."
                )

            model = package.get("model")
            feature_names = package.get("feature_names")
            classes = package.get("classes")

            if model is None or not hasattr(model, "predict_proba"):
                raise ModelUnavailableError(
                    "Model artifact missing valid classifier supporting predict_proba()."
                )

            if not feature_names or not isinstance(feature_names, list):
                raise IncompatibleFeatureSchemaError(
                    "Model artifact missing valid 'feature_names' list."
                )

            if feature_names != EXPECTED_MODEL_FEATURES:
                raise IncompatibleFeatureSchemaError(
                    f"Model feature schema mismatch. "
                    f"Expected: {EXPECTED_MODEL_FEATURES}, Found: {feature_names}"
                )

            if not classes or not isinstance(classes, list):
                raise ModelUnavailableError(
                    "Model artifact missing valid 'classes' list."
                )

            self._model = model
            self._feature_names = feature_names
            self._classes = [str(c) for c in classes]
            self._model_metadata = {
                "created_at": package.get("created_at"),
                "model_type": package.get("model_type", "RandomForestClassifier"),
                "n_estimators": package.get("n_estimators", 100),
            }
            logger.info(
                "Successfully loaded crop recommendation model from %s (%d classes)",
                self.model_path,
                len(self._classes),
            )

    def adapt_agricultural_inputs(
        self,
        agri: AgriculturalInput | dict[str, Any],
        epsilon: float = 1e-5,
    ) -> dict[str, float]:
        """Adapt raw agricultural inputs into the exact 11-feature vector for the model.

        Calculates domain interaction ratios:
        - N_P_ratio = N / (P + 1e-5)
        - N_K_ratio = N / (K + 1e-5)
        - P_K_ratio = P / (K + 1e-5)
        - rain_temp_ratio = rainfall / (temperature + 1e-5)

        Args:
            agri: AgriculturalInput model or dictionary of values.
            epsilon: Small constant to avoid zero division (consistent with data prep).

        Returns:
            Dictionary containing exactly the 11 expected features in proper order.

        Raises:
            MissingModelInputError: If any required parameter is missing or None.
        """
        def _get(key_primary: str, key_alias: str | None = None) -> float:
            val = None
            if isinstance(agri, dict):
                val = agri.get(key_primary)
                if val is None and key_alias:
                    val = agri.get(key_alias)
            else:
                val = getattr(agri, key_primary, None)
                if val is None and key_alias:
                    val = getattr(agri, key_alias, None)

            if val is None:
                raise MissingModelInputError(
                    f"Missing required model input feature '{key_primary}'. "
                    "Silent imputation is strictly prohibited."
                )
            try:
                return float(val)
            except (ValueError, TypeError) as exc:
                raise MissingModelInputError(
                    f"Feature '{key_primary}' must be a numeric value, got: {val}"
                ) from exc

        n_val = _get("nitrogen", "N")
        p_val = _get("phosphorus", "P")
        k_val = _get("potassium", "K")
        temp_val = _get("temperature")
        hum_val = _get("humidity")
        ph_val = _get("ph")
        rain_val = _get("rainfall")

        # Compute domain ratio interactions
        n_p = n_val / (p_val + epsilon)
        n_k = n_val / (k_val + epsilon)
        p_k = p_val / (k_val + epsilon)
        rain_temp = rain_val / (temp_val + epsilon)

        # Assemble exact 11-feature dictionary
        feature_dict: dict[str, float] = {
            "N": round(n_val, 4),
            "P": round(p_val, 4),
            "K": round(k_val, 4),
            "temperature": round(temp_val, 4),
            "humidity": round(hum_val, 4),
            "ph": round(ph_val, 4),
            "rainfall": round(rain_val, 4),
            "N_P_ratio": round(n_p, 4),
            "N_K_ratio": round(n_k, 4),
            "P_K_ratio": round(p_k, 4),
            "rain_temp_ratio": round(rain_temp, 4),
        }

        return feature_dict

    def adapt_from_multisource_observation(
        self,
        observation: Any,
    ) -> dict[str, float]:
        """Adapt a Phase 7 MultiSourceObservation into the benchmark model's 11-feature schema.

        Isolates model input features (A) from environmental context features (B).

        Args:
            observation: MultiSourceObservation instance.

        Returns:
            Dictionary containing the 11 model input features.

        Raises:
            MissingModelInputError: If any required agricultural feature is missing.
        """
        agri = getattr(observation, "agricultural", None)
        if agri is None:
            raise MissingModelInputError(
                "MultiSourceObservation is missing agricultural features block."
            )

        n_val = getattr(agri, "nitrogen", None)
        p_val = getattr(agri, "phosphorus", None)
        k_val = getattr(agri, "potassium", None)
        temp_val = getattr(agri, "historical_temperature", None)
        hum_val = getattr(agri, "historical_humidity", None)
        ph_val = getattr(agri, "historical_ph", None)
        rain_val = getattr(agri, "historical_rainfall", None)

        missing = []
        if n_val is None:
            missing.append("nitrogen")
        if p_val is None:
            missing.append("phosphorus")
        if k_val is None:
            missing.append("potassium")
        if temp_val is None:
            missing.append("historical_temperature")
        if hum_val is None:
            missing.append("historical_humidity")
        if ph_val is None:
            missing.append("historical_ph")
        if rain_val is None:
            missing.append("historical_rainfall")

        if missing:
            raise MissingModelInputError(
                f"Missing required model input features in observation: {missing}. "
                "Silent imputation of missing critical inputs is strictly prohibited."
            )

        agri_dict = {
            "nitrogen": n_val,
            "phosphorus": p_val,
            "potassium": k_val,
            "temperature": temp_val,
            "humidity": hum_val,
            "ph": ph_val,
            "rainfall": rain_val,
        }
        return self.adapt_agricultural_inputs(agri_dict)

    def predict_top_k(
        self,
        features: dict[str, float],
        k: int = 3,
    ) -> list[CropRecommendationItem]:
        """Execute model inference and return top-K ranked recommendations with probability estimates.

        Args:
            features: Dictionary containing all 11 EXPECTED_MODEL_FEATURES.
            k: Number of recommendations to return (default: 3).

        Returns:
            Deterministic ordered list of CropRecommendationItem instances.

        Raises:
            ModelUnavailableError: If model cannot be loaded.
            IncompatibleFeatureSchemaError: If features dictionary is incomplete or has mismatched keys.
            ModelPredictionError: If inference execution fails.
        """
        self.load_model()
        assert self._model is not None
        assert self._classes is not None
        assert self._feature_names is not None

        # 1. Validate feature schema completeness
        missing_keys = [feat for feat in self._feature_names if feat not in features]
        if missing_keys:
            raise IncompatibleFeatureSchemaError(
                f"Input feature vector is missing required columns: {missing_keys}"
            )

        none_keys = [feat for feat in self._feature_names if features.get(feat) is None]
        if none_keys:
            raise MissingModelInputError(
                f"Features contain None values for required columns: {none_keys}. "
                "Silent imputation is strictly prohibited."
            )

        # 2. Construct 1-row DataFrame preserving exact training feature order
        try:
            df = pd.DataFrame([features])[self._feature_names]
        except Exception as exc:
            raise IncompatibleFeatureSchemaError(
                f"Failed to align features to model input schema: {exc}"
            ) from exc

        # 3. Predict class probability distribution
        try:
            probabilities = self._model.predict_proba(df)[0]
        except Exception as exc:
            logger.error("Model prediction failed: %s", exc)
            raise ModelPredictionError(f"Model inference failed: {exc}") from exc

        # 4. Deterministic sorting: sort by probability descending, tie-break by crop name ascending
        scored_crops: list[tuple[str, float]] = []
        for idx, prob in enumerate(probabilities):
            crop_name = self._classes[idx]
            scored_crops.append((crop_name, float(prob)))

        # Sort key: (-probability, crop_name) ensures deterministic tie-breaking
        scored_crops.sort(key=lambda x: (-x[1], x[0]))

        top_k_crops = scored_crops[:k]

        results: list[CropRecommendationItem] = []
        for rank, (crop, prob) in enumerate(top_k_crops, start=1):
            clamped_prob = max(0.0, min(1.0, prob))
            results.append(
                CropRecommendationItem(
                    crop=crop,
                    rank=rank,
                    probability_estimate=round(clamped_prob, 4),
                    confidence_percentage=f"{clamped_prob * 100:.2f}%",
                )
            )

        return results


# Global singleton instance for application reuse
crop_model_adapter = CropModelAdapter()
