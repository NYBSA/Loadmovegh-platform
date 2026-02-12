"""
LoadMoveGH — Feature Engineering for Freight Pricing
=====================================================

Transforms raw listing/route data into a rich feature vector that captures
Ghana-specific market dynamics for the pricing model.

FEATURE CATEGORIES
──────────────────
1. Route features      — distance, coordinates, region pair encoding
2. Load features       — weight, dimensions, cargo type risk, vehicle type
3. Temporal features   — day of week, hour, month, public holidays, rainy season
4. Market features     — regional demand index, route corridor popularity
5. Fuel/cost features  — current diesel price, fuel cost estimate
6. Urgency features    — urgency level, time pressure encoding
7. Historical features — rolling avg price for route/cargo type

Total: ~35 engineered features from ~10 raw inputs.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional

import numpy as np


# ═══════════════════════════════════════════════════════════════
#  GHANA MARKET CONSTANTS
# ═══════════════════════════════════════════════════════════════

# Average diesel price (GHS per litre) — updated periodically
DIESEL_PRICE_PER_LITRE: float = 15.50

# Fuel consumption (litres per km) by vehicle type
FUEL_CONSUMPTION: dict[str, float] = {
    "motorcycle": 0.03,
    "van": 0.10,
    "box_truck": 0.15,
    "flatbed": 0.18,
    "refrigerated": 0.22,
    "heavy_truck": 0.25,
    "any": 0.15,
}

# Cargo type risk multipliers (higher = more expensive to transport)
CARGO_RISK: dict[str, float] = {
    "general": 1.00,
    "textiles": 1.00,
    "furniture": 1.10,
    "construction": 1.15,
    "livestock": 1.20,
    "electronics": 1.30,
    "perishables": 1.40,
    "chemicals": 1.50,
    "medical": 1.60,
}

# Ghana regional demand indices (higher = more freight activity/competition)
# Based on economic output and logistics hub status
REGION_DEMAND_INDEX: dict[str, float] = {
    "Greater Accra": 1.00,    # Baseline — highest volume
    "Ashanti": 0.85,
    "Western": 0.70,
    "Central": 0.55,
    "Eastern": 0.55,
    "Volta": 0.45,
    "Northern": 0.40,
    "Bono": 0.40,
    "Bono East": 0.35,
    "Ahafo": 0.30,
    "Oti": 0.30,
    "Savannah": 0.25,
    "North East": 0.25,
    "Upper East": 0.30,
    "Upper West": 0.25,
    "Western North": 0.30,
}

# Major route corridors (city-pair) with traffic multipliers
CORRIDOR_MULTIPLIER: dict[tuple[str, str], float] = {
    ("Accra", "Kumasi"): 0.90,       # Very popular — competitive pricing
    ("Kumasi", "Accra"): 0.90,
    ("Accra", "Tema"): 0.85,         # Port corridor — high volume
    ("Tema", "Accra"): 0.85,
    ("Accra", "Takoradi"): 0.92,
    ("Takoradi", "Accra"): 0.92,
    ("Accra", "Cape Coast"): 0.93,
    ("Kumasi", "Tamale"): 1.05,      # Northern route — fewer couriers
    ("Tamale", "Kumasi"): 1.05,
    ("Accra", "Tamale"): 1.10,       # Long distance north — premium
    ("Tamale", "Accra"): 1.10,
    ("Accra", "Ho"): 0.95,
    ("Tema", "Kumasi"): 0.92,
    ("Tema", "Takoradi"): 0.95,
}

# Ghana public holidays (month, day) — demand spikes
GHANA_HOLIDAYS: list[tuple[int, int]] = [
    (1, 1),    # New Year's Day
    (1, 7),    # Constitution Day
    (3, 6),    # Independence Day
    (5, 1),    # May Day
    (5, 25),   # Africa Day
    (7, 1),    # Republic Day
    (9, 21),   # Kwame Nkrumah Memorial Day
    (12, 1),   # Farmers' Day (first Friday of Dec, approximate)
    (12, 25),  # Christmas
    (12, 26),  # Boxing Day
]

# Rainy seasons in Ghana: April–July (major), September–November (minor)
RAINY_MONTHS: set[int] = {4, 5, 6, 7, 9, 10, 11}

# Urgency multipliers
URGENCY_MULTIPLIER: dict[str, float] = {
    "standard": 1.00,
    "express": 1.25,
    "urgent": 1.60,
}

# Vehicle capacity weight thresholds (kg)
VEHICLE_MAX_WEIGHT: dict[str, float] = {
    "motorcycle": 100,
    "van": 1500,
    "box_truck": 5000,
    "flatbed": 15000,
    "refrigerated": 8000,
    "heavy_truck": 30000,
    "any": 5000,
}


# ═══════════════════════════════════════════════════════════════
#  HAVERSINE
# ═══════════════════════════════════════════════════════════════

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ═══════════════════════════════════════════════════════════════
#  FEATURE EXTRACTION
# ═══════════════════════════════════════════════════════════════

def extract_features(
    # Route
    distance_km: float,
    pickup_lat: Optional[float] = None,
    pickup_lng: Optional[float] = None,
    delivery_lat: Optional[float] = None,
    delivery_lng: Optional[float] = None,
    pickup_city: str = "",
    delivery_city: str = "",
    pickup_region: str = "",
    delivery_region: str = "",
    # Load
    weight_kg: float = 0.0,
    cargo_type: str = "general",
    vehicle_type: str = "any",
    dimensions_volume_cm3: Optional[float] = None,
    # Urgency
    urgency: str = "standard",
    # Temporal (defaults to now)
    request_time: Optional[datetime] = None,
    # Market overrides
    diesel_price: Optional[float] = None,
    region_demand_override: Optional[dict[str, float]] = None,
    # Historical
    historical_avg_price: Optional[float] = None,
    historical_price_count: int = 0,
    route_avg_price: Optional[float] = None,
    route_price_count: int = 0,
) -> dict[str, float]:
    """
    Extract a complete feature vector from raw freight listing inputs.
    Returns a dict of feature_name → float value.

    All features are designed to be numerically stable for gradient
    boosting models (no need for scaling, handles missing values as 0).
    """

    if request_time is None:
        request_time = datetime.now(timezone.utc)

    fuel_price = diesel_price or DIESEL_PRICE_PER_LITRE
    demand_map = region_demand_override or REGION_DEMAND_INDEX

    features: dict[str, float] = {}

    # ── 1. ROUTE FEATURES ────────────────────────────────────

    features["distance_km"] = distance_km
    features["distance_log"] = math.log1p(distance_km)
    features["distance_sq"] = distance_km ** 2 / 10000  # Scaled quadratic

    # Coordinate features (for capturing spatial patterns)
    if pickup_lat is not None and pickup_lng is not None:
        features["pickup_lat"] = pickup_lat
        features["pickup_lng"] = pickup_lng
    else:
        features["pickup_lat"] = 0.0
        features["pickup_lng"] = 0.0

    if delivery_lat is not None and delivery_lng is not None:
        features["delivery_lat"] = delivery_lat
        features["delivery_lng"] = delivery_lng
    else:
        features["delivery_lat"] = 0.0
        features["delivery_lng"] = 0.0

    # North-south indicator (northern Ghana = more expensive)
    features["route_north_south"] = (
        (features["delivery_lat"] - features["pickup_lat"])
        if features["pickup_lat"] != 0 else 0.0
    )

    # Corridor multiplier
    city_pair = (pickup_city.strip().title(), delivery_city.strip().title())
    features["corridor_multiplier"] = CORRIDOR_MULTIPLIER.get(city_pair, 1.00)

    # ── 2. LOAD FEATURES ─────────────────────────────────────

    features["weight_kg"] = weight_kg
    features["weight_log"] = math.log1p(weight_kg)
    features["weight_tonnes"] = weight_kg / 1000.0

    # Capacity utilisation (how full is the truck)
    max_weight = VEHICLE_MAX_WEIGHT.get(vehicle_type, 5000)
    features["capacity_utilisation"] = min(weight_kg / max_weight, 2.0)

    # Volume (if provided)
    features["volume_cm3"] = dimensions_volume_cm3 or 0.0
    features["volume_m3"] = (dimensions_volume_cm3 or 0.0) / 1_000_000

    # Cargo risk
    features["cargo_risk"] = CARGO_RISK.get(cargo_type, 1.0)

    # Cargo type one-hot (tree models handle this well)
    for ct in CARGO_RISK:
        features[f"cargo_is_{ct}"] = 1.0 if cargo_type == ct else 0.0

    # Vehicle type one-hot
    for vt in FUEL_CONSUMPTION:
        features[f"vehicle_is_{vt}"] = 1.0 if vehicle_type == vt else 0.0

    # ── 3. TEMPORAL FEATURES ─────────────────────────────────

    features["hour_of_day"] = float(request_time.hour)
    features["day_of_week"] = float(request_time.weekday())  # 0=Mon
    features["month"] = float(request_time.month)
    features["is_weekend"] = 1.0 if request_time.weekday() >= 5 else 0.0

    # Peak business hours (8am–6pm)
    features["is_business_hours"] = (
        1.0 if 8 <= request_time.hour <= 18 else 0.0
    )

    # Rainy season
    features["is_rainy_season"] = (
        1.0 if request_time.month in RAINY_MONTHS else 0.0
    )

    # Holiday proximity (within 3 days of a holiday)
    features["near_holiday"] = 0.0
    for h_month, h_day in GHANA_HOLIDAYS:
        try:
            holiday = request_time.replace(month=h_month, day=h_day)
            delta = abs((request_time - holiday).days)
            if delta <= 3:
                features["near_holiday"] = 1.0
                break
        except ValueError:
            pass

    # ── 4. MARKET FEATURES ───────────────────────────────────

    pickup_demand = demand_map.get(pickup_region, 0.40)
    delivery_demand = demand_map.get(delivery_region, 0.40)
    features["pickup_region_demand"] = pickup_demand
    features["delivery_region_demand"] = delivery_demand
    features["demand_avg"] = (pickup_demand + delivery_demand) / 2
    features["demand_diff"] = delivery_demand - pickup_demand

    # Supply imbalance: moving TO a low-demand area = harder to find return load
    features["supply_imbalance"] = max(0, pickup_demand - delivery_demand)

    # ── 5. FUEL/COST FEATURES ────────────────────────────────

    consumption_rate = FUEL_CONSUMPTION.get(vehicle_type, 0.15)
    fuel_cost = distance_km * consumption_rate * fuel_price
    features["fuel_cost_estimate"] = fuel_cost
    features["fuel_price_per_litre"] = fuel_price
    features["fuel_consumption_rate"] = consumption_rate

    # Cost per kg per km (unit economics)
    if weight_kg > 0 and distance_km > 0:
        features["cost_per_kg_km"] = fuel_cost / (weight_kg * distance_km) * 1000
    else:
        features["cost_per_kg_km"] = 0.0

    # ── 6. URGENCY FEATURES ──────────────────────────────────

    features["urgency_multiplier"] = URGENCY_MULTIPLIER.get(urgency, 1.0)
    features["is_express"] = 1.0 if urgency == "express" else 0.0
    features["is_urgent"] = 1.0 if urgency == "urgent" else 0.0

    # ── 7. HISTORICAL FEATURES ───────────────────────────────

    features["hist_avg_price"] = historical_avg_price or 0.0
    features["hist_price_count"] = float(historical_price_count)
    features["hist_has_data"] = 1.0 if historical_price_count > 0 else 0.0

    features["route_avg_price"] = route_avg_price or 0.0
    features["route_price_count"] = float(route_price_count)
    features["route_has_data"] = 1.0 if route_price_count > 0 else 0.0

    return features


# ═══════════════════════════════════════════════════════════════
#  FEATURE NAMES (ordered, for model input)
# ═══════════════════════════════════════════════════════════════

def get_feature_names() -> list[str]:
    """Return the ordered list of feature names the model expects."""
    sample = extract_features(distance_km=100.0, weight_kg=1000.0)
    return sorted(sample.keys())


def features_to_array(features: dict[str, float]) -> np.ndarray:
    """Convert feature dict to numpy array in canonical order."""
    names = get_feature_names()
    return np.array([features.get(n, 0.0) for n in names], dtype=np.float64)


# ═══════════════════════════════════════════════════════════════
#  RULE-BASED FALLBACK ESTIMATOR
# ═══════════════════════════════════════════════════════════════

def rule_based_price(features: dict[str, float]) -> tuple[float, float, float]:
    """
    Simple formula-based estimator used as:
    1. Fallback when no ML model is loaded
    2. Sanity-check baseline for ML predictions
    3. Cold-start pricing before enough data is collected

    Returns (low, mid, high) price in GHS.
    """
    distance = features.get("distance_km", 50)
    fuel_cost = features.get("fuel_cost_estimate", 100)
    weight = features.get("weight_kg", 500)
    cargo_risk = features.get("cargo_risk", 1.0)
    urgency_mult = features.get("urgency_multiplier", 1.0)
    corridor_mult = features.get("corridor_multiplier", 1.0)
    supply_imbalance = features.get("supply_imbalance", 0.0)
    is_rainy = features.get("is_rainy_season", 0.0)
    near_holiday = features.get("near_holiday", 0.0)

    # Base: fuel cost + per-km margin + weight surcharge
    base = fuel_cost * 1.4                        # 40% margin over fuel
    base += distance * 0.50                        # GHS 0.50/km overhead
    base += (weight / 1000) * 15.0                # GHS 15 per tonne
    base *= cargo_risk                             # Cargo risk premium
    base *= urgency_mult                           # Urgency premium
    base *= corridor_mult                          # Corridor adjustment

    # Supply/demand adjustment
    base *= (1.0 + supply_imbalance * 0.15)

    # Weather/seasonal
    if is_rainy > 0:
        base *= 1.08  # 8% rainy season surcharge
    if near_holiday > 0:
        base *= 1.05  # 5% holiday surcharge

    # Minimum price floor
    base = max(base, 20.0)

    # Historical anchor blending
    hist_price = features.get("hist_avg_price", 0.0)
    hist_count = features.get("hist_price_count", 0.0)
    if hist_count >= 5 and hist_price > 0:
        # Blend: 60% formula, 40% historical
        base = 0.6 * base + 0.4 * hist_price

    mid = round(base, 2)
    low = round(base * 0.85, 2)
    high = round(base * 1.20, 2)

    return low, mid, high
