"""
LoadMoveGH — ML Model Training Pipeline
========================================

Trains a Gradient Boosted Tree (LightGBM) pricing model using either:
  (a) Real historical data from the database (preferred)
  (b) Synthetic data generated from Ghana freight market parameters

MODEL CHOICE RATIONALE
──────────────────────
LightGBM (Gradient Boosted Decision Trees) chosen because:
  • Handles mixed feature types (continuous, categorical, binary) natively
  • Robust to missing values and outliers
  • Fast training on tabular data (minutes, not hours)
  • Built-in feature importance for explainability
  • Production-proven for pricing/ranking at scale
  • No GPU required — runs on commodity servers
  • Quantile regression support → confidence intervals for free

TRAINING APPROACH
─────────────────
1. Generate synthetic dataset from Ghana freight parameters (cold start)
   OR query real completed trips from the database
2. Feature engineering via features.py
3. Train/validation split (80/20, time-based if enough data)
4. Train LightGBM with 3 objectives:
   - regression (point estimate)
   - quantile(0.15) (low bound)
   - quantile(0.85) (high bound)
5. Evaluate: MAE, RMSE, MAPE, R²
6. Serialize model to disk
7. Register model version in database
"""

from __future__ import annotations

import json
import math
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import numpy as np

from app.ml.features import (
    CARGO_RISK,
    CORRIDOR_MULTIPLIER,
    DIESEL_PRICE_PER_LITRE,
    FUEL_CONSUMPTION,
    REGION_DEMAND_INDEX,
    URGENCY_MULTIPLIER,
    VEHICLE_MAX_WEIGHT,
    extract_features,
    features_to_array,
    get_feature_names,
    rule_based_price,
)

# Model artifact directory
MODEL_DIR = Path(__file__).parent.parent.parent / "ml_models"


# ═══════════════════════════════════════════════════════════════
#  SYNTHETIC DATA GENERATION
# ═══════════════════════════════════════════════════════════════

# Representative Ghana city coordinates
GHANA_CITIES: dict[str, tuple[float, float, str]] = {
    "Accra":      (5.6037, -0.1870, "Greater Accra"),
    "Tema":       (5.6698, -0.0166, "Greater Accra"),
    "Kumasi":     (6.6885, -1.6244, "Ashanti"),
    "Takoradi":   (4.8986, -1.7614, "Western"),
    "Cape Coast": (5.1036, -1.2466, "Central"),
    "Tamale":     (9.4008, -0.8393, "Northern"),
    "Sunyani":    (7.3399, -2.3266, "Bono"),
    "Ho":         (6.6001, 0.4710,  "Volta"),
    "Bolgatanga": (10.7855, -0.8514, "Upper East"),
    "Wa":         (10.0601, -2.5099, "Upper West"),
    "Koforidua":  (6.0941, -0.2619, "Eastern"),
    "Techiman":   (7.5829, -1.9340, "Bono East"),
}

CARGO_TYPES = list(CARGO_RISK.keys())
VEHICLE_TYPES = list(FUEL_CONSUMPTION.keys())
URGENCY_LEVELS = list(URGENCY_MULTIPLIER.keys())


def generate_synthetic_dataset(
    n_samples: int = 10_000,
    seed: int = 42,
    noise_level: float = 0.12,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Generate a synthetic freight pricing dataset calibrated to the
    Ghana market.

    Returns:
        X: feature matrix (n_samples, n_features)
        y: target prices in GHS (n_samples,)
        feature_names: ordered feature names
    """
    rng = random.Random(seed)
    np_rng = np.random.RandomState(seed)

    cities = list(GHANA_CITIES.keys())
    feature_names = get_feature_names()
    X_rows: list[np.ndarray] = []
    y_values: list[float] = []

    for _ in range(n_samples):
        # Random pickup/delivery
        pickup_city = rng.choice(cities)
        delivery_city = rng.choice([c for c in cities if c != pickup_city])
        p_lat, p_lng, p_region = GHANA_CITIES[pickup_city]
        d_lat, d_lng, d_region = GHANA_CITIES[delivery_city]

        # Add jitter to coordinates (simulate different addresses in city)
        p_lat += rng.gauss(0, 0.02)
        p_lng += rng.gauss(0, 0.02)
        d_lat += rng.gauss(0, 0.02)
        d_lng += rng.gauss(0, 0.02)

        # Calculate distance
        R = 6371.0
        dlat = math.radians(d_lat - p_lat)
        dlon = math.radians(d_lng - p_lng)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(p_lat))
            * math.cos(math.radians(d_lat))
            * math.sin(dlon / 2) ** 2
        )
        distance = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        # Road distance ≈ 1.3× straight line in Ghana
        distance *= rng.uniform(1.2, 1.4)

        # Random load attributes
        cargo_type = rng.choice(CARGO_TYPES)
        vehicle_type = rng.choice(VEHICLE_TYPES)
        max_w = VEHICLE_MAX_WEIGHT.get(vehicle_type, 5000)
        weight_kg = rng.uniform(50, max_w * 0.9)
        urgency = rng.choices(
            URGENCY_LEVELS, weights=[0.60, 0.25, 0.15], k=1
        )[0]

        # Random timestamp (past 12 months)
        days_ago = rng.randint(0, 365)
        hour = rng.randint(5, 22)
        request_time = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=rng.randint(0, 12))
        request_time = request_time.replace(hour=hour, minute=rng.randint(0, 59))

        # Historical price (simulate)
        hist_count = rng.randint(0, 50)
        hist_avg = 0.0

        # Diesel price variation (±10%)
        diesel = DIESEL_PRICE_PER_LITRE * rng.uniform(0.90, 1.10)

        # Extract features
        feat = extract_features(
            distance_km=distance,
            pickup_lat=p_lat,
            pickup_lng=p_lng,
            delivery_lat=d_lat,
            delivery_lng=d_lng,
            pickup_city=pickup_city,
            delivery_city=delivery_city,
            pickup_region=p_region,
            delivery_region=d_region,
            weight_kg=weight_kg,
            cargo_type=cargo_type,
            vehicle_type=vehicle_type,
            urgency=urgency,
            request_time=request_time,
            diesel_price=diesel,
            historical_avg_price=hist_avg,
            historical_price_count=hist_count,
        )

        # Generate "true" price using the rule-based model + noise
        _, mid_price, _ = rule_based_price(feat)

        # Add realistic noise (log-normal for price data)
        noise_factor = np_rng.lognormal(0, noise_level)
        true_price = mid_price * noise_factor
        true_price = max(true_price, 15.0)  # Floor

        X_rows.append(features_to_array(feat))
        y_values.append(round(true_price, 2))

    X = np.vstack(X_rows)
    y = np.array(y_values, dtype=np.float64)

    return X, y, feature_names


# ═══════════════════════════════════════════════════════════════
#  MODEL TRAINING
# ═══════════════════════════════════════════════════════════════

def train_pricing_model(
    X: Optional[np.ndarray] = None,
    y: Optional[np.ndarray] = None,
    feature_names: Optional[list[str]] = None,
    n_synthetic: int = 15_000,
    version_tag: Optional[str] = None,
) -> dict:
    """
    Train the LightGBM pricing model.

    If X/y not provided, generates synthetic data.

    Returns a dict with:
      - model_mid, model_low, model_high: trained boosters
      - feature_names: ordered feature list
      - metrics: evaluation metrics
      - version: version string
      - artifact_path: where model is saved
    """
    try:
        import lightgbm as lgb
    except ImportError:
        raise RuntimeError(
            "LightGBM is required for model training. "
            "Install with: pip install lightgbm"
        )

    # Generate synthetic data if none provided
    if X is None or y is None:
        X, y, feature_names = generate_synthetic_dataset(n_samples=n_synthetic)

    if feature_names is None:
        feature_names = get_feature_names()

    n = len(y)
    split_idx = int(n * 0.8)

    # Shuffle before split (for synthetic data; use time-based for real data)
    indices = np.random.permutation(n)
    X = X[indices]
    y = y[indices]

    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]

    # Common parameters
    base_params = {
        "n_estimators": 500,
        "learning_rate": 0.05,
        "max_depth": 7,
        "num_leaves": 63,
        "min_child_samples": 20,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "random_state": 42,
        "verbose": -1,
        "n_jobs": -1,
    }

    # 1. Point estimate (regression)
    model_mid = lgb.LGBMRegressor(
        objective="regression",
        metric="mae",
        **base_params,
    )
    model_mid.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="mae",
        callbacks=[lgb.early_stopping(50, verbose=False)],
    )

    # 2. Low bound (15th percentile)
    model_low = lgb.LGBMRegressor(
        objective="quantile",
        alpha=0.15,
        metric="quantile",
        **base_params,
    )
    model_low.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        callbacks=[lgb.early_stopping(50, verbose=False)],
    )

    # 3. High bound (85th percentile)
    model_high = lgb.LGBMRegressor(
        objective="quantile",
        alpha=0.85,
        metric="quantile",
        **base_params,
    )
    model_high.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        callbacks=[lgb.early_stopping(50, verbose=False)],
    )

    # Evaluate on validation set
    y_pred_mid = model_mid.predict(X_val)
    y_pred_low = model_low.predict(X_val)
    y_pred_high = model_high.predict(X_val)

    mae = float(np.mean(np.abs(y_val - y_pred_mid)))
    rmse = float(np.sqrt(np.mean((y_val - y_pred_mid) ** 2)))
    mape = float(np.mean(np.abs((y_val - y_pred_mid) / np.maximum(y_val, 1.0))) * 100)
    ss_res = np.sum((y_val - y_pred_mid) ** 2)
    ss_tot = np.sum((y_val - np.mean(y_val)) ** 2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Coverage: what fraction of true prices fall within [low, high]
    coverage = float(np.mean((y_val >= y_pred_low) & (y_val <= y_pred_high)))
    interval_width = float(np.mean(y_pred_high - y_pred_low))

    # Feature importance
    importance = model_mid.feature_importances_
    imp_pairs = sorted(
        zip(feature_names, importance.tolist()),
        key=lambda x: x[1],
        reverse=True,
    )
    top_features = imp_pairs[:15]

    metrics = {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2),
        "r2_score": round(r2, 4),
        "coverage_85": round(coverage, 4),
        "avg_interval_width": round(interval_width, 2),
        "training_samples": split_idx,
        "validation_samples": n - split_idx,
        "top_features": top_features,
    }

    # Save model artifacts
    version = version_tag or datetime.now(timezone.utc).strftime("v%Y%m%d_%H%M%S")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    artifact_dir = MODEL_DIR / version
    artifact_dir.mkdir(parents=True, exist_ok=True)

    model_mid.booster_.save_model(str(artifact_dir / "model_mid.lgb"))
    model_low.booster_.save_model(str(artifact_dir / "model_low.lgb"))
    model_high.booster_.save_model(str(artifact_dir / "model_high.lgb"))

    with open(artifact_dir / "feature_names.json", "w") as f:
        json.dump(feature_names, f)
    with open(artifact_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    return {
        "model_mid": model_mid,
        "model_low": model_low,
        "model_high": model_high,
        "feature_names": feature_names,
        "metrics": metrics,
        "version": version,
        "artifact_path": str(artifact_dir),
    }
