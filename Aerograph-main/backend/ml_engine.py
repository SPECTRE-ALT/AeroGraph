"""Hazard probability model used by the dispatch API."""

from functools import lru_cache

import numpy as np
from xgboost import XGBRegressor

FEATURE_NAMES = ("insar_phase_shift", "rainfall_rate", "terrain_slope", "soil_moisture")


@lru_cache(maxsize=1)
def get_hazard_model() -> XGBRegressor:
    generator = np.random.default_rng(2026)
    count = 2400
    insar, rainfall = generator.uniform(0, 50, count), generator.uniform(0, 150, count)
    slope, soil = generator.uniform(0, 40, count), generator.uniform(0, 1, count)
    features = np.column_stack((insar, rainfall, slope, soil))
    risk = 0.02 + 0.16 * insar / 50 + 0.24 * rainfall / 150 + 0.25 * slope / 40 + 0.30 * soil + 0.22 * rainfall / 150 * soil + 0.16 * insar / 50 * slope / 40 + generator.normal(0, 0.02, count)
    model = XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.07, objective="reg:squarederror", n_jobs=1, random_state=2026)
    model.fit(features, np.clip(risk, 0, 1))
    return model


HAZARD_MODEL = get_hazard_model()


def predict_edge_hazards(features_matrix: np.ndarray) -> np.ndarray:
    """Return a clipped failure probability for every supplied feature row."""
    values = np.asarray(features_matrix, dtype=float)
    if values.ndim != 2 or values.shape[1] != len(FEATURE_NAMES):
        raise ValueError("features_matrix must have shape (n, 4)")
    return np.clip(HAZARD_MODEL.predict(values), 0.0, 1.0)
