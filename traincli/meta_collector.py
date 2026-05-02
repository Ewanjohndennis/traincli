import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


META_DIR = Path.home() / ".traincli"
META_CSV = META_DIR / "meta_dataset.csv"


def collect(df: pd.DataFrame, target: str, results: dict):
    """
    Extract metadata from a completed TrainCLI run and append to meta_dataset.csv.
    Called automatically when --meta flag is passed.
    """
    META_DIR.mkdir(exist_ok=True)

    row = _extract_features(df, target, results)

    # Load existing or create new
    if META_CSV.exists():
        existing = pd.read_csv(META_CSV)
        updated = pd.concat([existing, pd.DataFrame([row])], ignore_index=True)
    else:
        updated = pd.DataFrame([row])

    updated.to_csv(META_CSV, index=False)
    return row


def _extract_features(df: pd.DataFrame, target: str, results: dict) -> dict:
    """Extract all features needed for meta-model training."""

    target_series = df[target].dropna()
    n_rows, n_cols = df.shape

    # Column type ratios
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(include="object").columns.tolist()
    if target in numeric_cols:
        numeric_cols.remove(target)
    if target in categorical_cols:
        categorical_cols.remove(target)

    numeric_ratio = len(numeric_cols) / max(n_cols - 1, 1)
    categorical_ratio = len(categorical_cols) / max(n_cols - 1, 1)

    # Null stats
    null_pct = df.drop(columns=[target]).isnull().mean().mean() * 100

    # Target stats
    target_nunique = int(target_series.nunique())
    target_is_float = int(pd.api.types.is_float_dtype(target_series))
    problem_type = results.get("problem_type", "unknown")

    # Target range — 0 for classification, actual range for regression
    target_range = 0.0
    if pd.api.types.is_numeric_dtype(target_series) and problem_type == "regression":
        target_range = float(target_series.max() - target_series.min())

    # CV scores from auto-selection
    cv_scores = results.get("cv_scores", np.array([0.0]))
    cv_mean = float(cv_scores.mean()) if hasattr(cv_scores, "mean") else 0.0
    cv_std = float(cv_scores.std()) if hasattr(cv_scores, "std") else 0.0

    # Best model — this is our target label
    best_model = results.get("model_entry", {}).get("key", "random_forest")

    return {
        "rows":               n_rows,
        "cols":               n_cols - 1,  # exclude target
        "null_pct":           round(null_pct, 3),
        "numeric_ratio":      round(numeric_ratio, 3),
        "categorical_ratio":  round(categorical_ratio, 3),
        "target_nunique":     target_nunique,
        "target_is_float":    target_is_float,
        "target_range":       target_range,  # None for classification
        "problem_type":       problem_type,
        "cv_mean":            round(cv_mean, 4),
        "cv_std":             round(cv_std, 4),
        "best_model":         best_model,
        "timestamp":          datetime.now().isoformat(),
    }