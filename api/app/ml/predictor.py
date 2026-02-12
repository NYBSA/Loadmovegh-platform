"""
LoadMoveGH — Pricing Prediction Service
========================================

Singleton service that loads a trained LightGBM model and serves
price predictions with confidence intervals and explainability.

DEPLOYMENT STRATEGY
───────────────────
1. Model artifacts stored in `ml_models/{version}/` on disk
   (or S3/GCS in production)
2. On startup, loads the latest ACTIVE model version
3. Predictions are served synchronously (LightGBM is fast: <5ms)
4. Model can be hot-reloaded via admin endpoint (no restart)
5. Every prediction is logged to ai_pricing_runs for monitoring
6. If no ML model is available, falls back to rule-based estimator

SCALING
───────
- LightGBM prediction is CPU-only, thread-safe, <1ms per sample
- At 1000 RPS, a single process handles predictions comfortably
- For higher throughput: deploy model behind a separate service
  (e.g., BentoML, MLflow Serving, or a simple FastAPI sidecar)
- Model file is ~2MB; loads in <100ms
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from threading import Lock
from typing import Optional

import numpy as np

from app.ml.features import (
    extract_features,
    features_to_array,
    get_feature_names,
    rule_based_price,
)

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent.parent.parent / "ml_models"


class PricingPredictor:
    """
    Thread-safe singleton that holds the loaded pricing model
    and serves predictions.
    """

    _instance: Optional["PricingPredictor"] = None
    _lock = Lock()

    def __new__(cls) -> "PricingPredictor":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self.model_mid = None
        self.model_low = None
        self.model_high = None
        self.feature_names: list[str] = get_feature_names()
        self.version: str = "rule_based_v1"
        self.is_ml_loaded: bool = False
        self._model_lock = Lock()

        # Try to load latest model on init
        self._try_load_latest()

    def _try_load_latest(self) -> bool:
        """Attempt to load the most recent model from disk."""
        if not MODEL_DIR.exists():
            logger.info("No ml_models directory found; using rule-based fallback")
            return False

        # Find the latest version directory
        versions = sorted(
            [d for d in MODEL_DIR.iterdir() if d.is_dir()],
            key=lambda d: d.name,
            reverse=True,
        )
        if not versions:
            logger.info("No model versions found; using rule-based fallback")
            return False

        return self.load_model(str(versions[0]))

    def load_model(self, artifact_path: str) -> bool:
        """Load a model from a specific artifact directory."""
        try:
            import lightgbm as lgb
        except ImportError:
            logger.warning("LightGBM not installed; using rule-based fallback")
            return False

        path = Path(artifact_path)
        mid_path = path / "model_mid.lgb"
        low_path = path / "model_low.lgb"
        high_path = path / "model_high.lgb"
        names_path = path / "feature_names.json"

        if not all(p.exists() for p in [mid_path, low_path, high_path]):
            logger.warning(f"Model artifacts missing in {artifact_path}")
            return False

        with self._model_lock:
            self.model_mid = lgb.Booster(model_file=str(mid_path))
            self.model_low = lgb.Booster(model_file=str(low_path))
            self.model_high = lgb.Booster(model_file=str(high_path))

            if names_path.exists():
                with open(names_path) as f:
                    self.feature_names = json.load(f)

            self.version = path.name
            self.is_ml_loaded = True

        logger.info(f"Loaded pricing model: {self.version}")
        return True

    def predict(
        self,
        features: dict[str, float],
    ) -> dict:
        """
        Generate a price prediction with confidence interval.

        Returns:
            {
                "price_low": float,
                "price_mid": float,
                "price_high": float,
                "confidence": float (0-1),
                "model_version": str,
                "method": "ml" | "rule_based",
                "feature_importance": [...top 10 features...],
                "features_used": dict,
            }
        """
        feature_array = np.array(
            [features.get(n, 0.0) for n in self.feature_names],
            dtype=np.float64,
        ).reshape(1, -1)

        # Rule-based fallback prices (always computed for sanity check)
        rb_low, rb_mid, rb_high = rule_based_price(features)

        if self.is_ml_loaded:
            with self._model_lock:
                ml_mid = float(self.model_mid.predict(feature_array)[0])
                ml_low = float(self.model_low.predict(feature_array)[0])
                ml_high = float(self.model_high.predict(feature_array)[0])

            # Sanity check: ML prediction should be within 3× of rule-based
            if ml_mid <= 0 or ml_mid > rb_mid * 3 or ml_mid < rb_mid / 3:
                logger.warning(
                    f"ML prediction ({ml_mid:.2f}) far from rule-based ({rb_mid:.2f}); "
                    f"blending with rule-based"
                )
                ml_mid = 0.7 * ml_mid + 0.3 * rb_mid
                ml_low = 0.7 * ml_low + 0.3 * rb_low
                ml_high = 0.7 * ml_high + 0.3 * rb_high

            # Ensure ordering: low <= mid <= high
            ml_low = min(ml_low, ml_mid)
            ml_high = max(ml_high, ml_mid)

            # Floor
            ml_mid = max(ml_mid, 15.0)
            ml_low = max(ml_low, 10.0)
            ml_high = max(ml_high, ml_mid * 1.05)

            # Confidence based on interval width relative to mid
            interval_ratio = (ml_high - ml_low) / max(ml_mid, 1.0)
            confidence = max(0.0, min(1.0, 1.0 - interval_ratio))

            # Feature importance for this prediction (top 10)
            importance = self._get_feature_importance(features)

            return {
                "price_low": round(ml_low, 2),
                "price_mid": round(ml_mid, 2),
                "price_high": round(ml_high, 2),
                "confidence": round(confidence, 3),
                "model_version": self.version,
                "method": "ml",
                "feature_importance": importance,
                "features_used": features,
            }
        else:
            # Rule-based fallback
            interval_ratio = (rb_high - rb_low) / max(rb_mid, 1.0)
            confidence = max(0.0, min(1.0, 0.6 - interval_ratio * 0.5))

            return {
                "price_low": rb_low,
                "price_mid": rb_mid,
                "price_high": rb_high,
                "confidence": round(confidence, 3),
                "model_version": self.version,
                "method": "rule_based",
                "feature_importance": self._rule_based_importance(features),
                "features_used": features,
            }

    def _get_feature_importance(self, features: dict[str, float]) -> list[dict]:
        """Get feature importance from the loaded ML model."""
        if not self.is_ml_loaded or self.model_mid is None:
            return []

        importances = self.model_mid.feature_importance(importance_type="gain")
        pairs = list(zip(self.feature_names, importances.tolist()))
        pairs.sort(key=lambda x: x[1], reverse=True)

        result = []
        for name, imp in pairs[:10]:
            value = features.get(name, 0.0)
            result.append({
                "feature": name,
                "importance": round(imp, 2),
                "value": round(value, 4),
            })
        return result

    def _rule_based_importance(self, features: dict[str, float]) -> list[dict]:
        """Approximate feature importance for rule-based predictions."""
        key_features = [
            ("distance_km", 0.25),
            ("fuel_cost_estimate", 0.20),
            ("weight_kg", 0.12),
            ("urgency_multiplier", 0.10),
            ("cargo_risk", 0.08),
            ("corridor_multiplier", 0.07),
            ("supply_imbalance", 0.05),
            ("is_rainy_season", 0.04),
            ("near_holiday", 0.03),
            ("hist_avg_price", 0.06),
        ]
        result = []
        for name, imp in key_features:
            value = features.get(name, 0.0)
            result.append({
                "feature": name,
                "importance": imp,
                "value": round(value, 4),
            })
        return result

    @property
    def status(self) -> dict:
        """Return current model status."""
        return {
            "version": self.version,
            "is_ml_loaded": self.is_ml_loaded,
            "feature_count": len(self.feature_names),
            "model_dir": str(MODEL_DIR),
        }


# ── Module-level singleton accessor ─────────────────────────

def get_predictor() -> PricingPredictor:
    """Get or create the singleton predictor instance."""
    return PricingPredictor()
