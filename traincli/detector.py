import pandas as pd
import numpy as np
from traincli.utils.display import header, success, info, warn
from traincli.utils.session import Session


def detect(df: pd.DataFrame, target: str, session: Session) -> str:
    """
    Detect problem type using heuristics first, LLM as fallback.
    Returns: "regression" or "classification"
    """
    header("Detecting problem type")

    series = df[target].dropna()
    nunique = series.nunique()
    dtype = series.dtype

    problem_type = None
    confidence = "high"
    reason = None

    # Rule 1: object/string dtype
    if dtype == object or pd.api.types.is_string_dtype(series):
        problem_type = "classification"
        reason = f"target is text/categorical with {nunique} unique values: {_sample_vals(series)}"

    # Rule 2: boolean
    elif pd.api.types.is_bool_dtype(series):
        problem_type = "classification"
        reason = "target is boolean"

    # Rule 3: exactly 2 unique numeric values
    elif nunique == 2:
        problem_type = "classification"
        reason = f"target has exactly 2 unique values {sorted(series.unique().tolist())}"

    # Rule 4: float dtype
    elif pd.api.types.is_float_dtype(series):
        unique_vals = set(series.unique())
        if unique_vals.issubset({0.0, 1.0}):
            problem_type = "classification"
            reason = "target is float but only contains 0.0 and 1.0"
        else:
            problem_type = "regression"
            reason = f"target is float with {nunique} unique values (range: {series.min():.2f}–{series.max():.2f})"

    # Rule 5: integer dtype
    elif pd.api.types.is_integer_dtype(series):
        min_val = int(series.min())
        max_val = int(series.max())

        if set(series.unique()).issubset({0, 1}):
            problem_type = "classification"
            reason = "target contains only 0 and 1"

        elif nunique <= 15:
            sorted_unique = sorted(series.unique())
            max_gap = max(b - a for a, b in zip(sorted_unique, sorted_unique[1:])) if len(sorted_unique) > 1 else 0

            if max_gap > 10 and nunique > 5:
                problem_type = "regression"
                confidence = "medium"
                reason = f"integer target with {nunique} unique values but large gaps (max gap: {max_gap}) — treating as regression"
            else:
                problem_type = "classification"
                reason = f"integer target with only {nunique} unique values {_sample_vals(series)}"

        else:
            problem_type = "regression"
            reason = f"integer target with {nunique} unique values (range: {min_val}–{max_val})"

    else:
        problem_type = "classification"
        confidence = "low"
        reason = "could not determine — defaulting to classification"
        warn("Problem type unclear — defaulting to classification. Use --task to override.")

    session.set_problem(problem_type, "heuristic")

    color = "green" if confidence == "high" else "yellow" if confidence == "medium" else "red"
    success(f"Problem type: [bold]{problem_type}[/bold]  [dim](confidence: [{color}]{confidence}[/{color}])[/dim]")
    info(f"Reason: {reason}")

    return problem_type


def _sample_vals(series: pd.Series, n: int = 5) -> list:
    vals = series.dropna().unique()[:n].tolist()
    return [str(v) for v in vals]