import pandas as pd
import numpy as np
from traincli.utils.display import header, info, warn, profile_table


def _is_id_column(col: str, series: pd.Series) -> bool:
    """
    True only if column is very likely a meaningless identifier.
    Uniqueness alone is not enough — needs multiple signals.
    """
    n = len(series)
    nunique = series.nunique()
    
    if nunique < n:
        return False  # not even fully unique
    
    signals = 0
    sample = series.dropna().astype(str)
    
    # Signal 1: name looks like an ID
    id_name_hints = ["id", "uuid", "guid", "key", "ref", "code", "no.", "num", "index", "serial"]
    if any(hint in col.lower() for hint in id_name_hints):
        signals += 2  # strong signal
    
    # Signal 2: looks like sequential integers
    try:
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().all():
            diffs = numeric.sort_values().diff().dropna()
            if len(diffs) > 0 and (diffs == 1).all():
                signals += 2  # perfectly sequential — almost certainly an ID
    except Exception:
        pass
    
    # Signal 3: looks like a UUID/hash pattern
    avg_len = sample.str.len().mean()
    if avg_len in range(32, 40):  # UUID length
        signals += 2
    
    # Signal 4: short and uniform length (like codes)
    len_std = sample.str.len().std()
    if len_std < 0.5 and avg_len < 10:
        signals += 1
    
    # Signal 5: column name is literally just "id" or ends with "_id"
    if col.lower() == "id" or col.lower().endswith("_id") or col.lower().endswith(" id"):
        signals += 3  # very strong signal
    
    # Need at least 2 signals to call it an ID
    return signals >= 2


def detect_leakage(df: pd.DataFrame, target: str) -> list:
    """
    Detect columns that are likely leaking target information.
    Checks correlation, name similarity, and linear transformations.
    """
    suspects = []
    target_series = df[target].dropna()

    # Only check numeric columns against numeric target
    if not pd.api.types.is_numeric_dtype(target_series):
        return suspects

    for col in df.columns:
        if col == target:
            continue

        # Check 1: column name is a direct variant of target
        # catches min_salary, max_salary when target is avg_salary
        # but NOT salary_estimate (which is a feature, not derived from target)
        target_root = target.lower().replace("avg_", "").replace("mean_", "").replace("total_", "").replace("_", "")
        col_root = col.lower().replace("_", "").replace(" ", "")
        # Only flag if column name starts with or is a direct variant of target
        # e.g. min_salary, max_salary → flag
        # e.g. salary_estimate → don't flag (it's a feature, not a derived target)
        direct_variants = [f"min_{target_root}", f"max_{target_root}",
                           f"{target_root}_min", f"{target_root}_max",
                           f"total_{target_root}", f"sum_{target_root}"]
        if any(variant.replace("_","") == col_root for variant in direct_variants):
            suspects.append({
                "col": col,
                "reason": f"column name is a direct variant of target '{target}'",
                "severity": "high",
            })
            continue  # no need to check further

        # Check 2: correlation too high
        if pd.api.types.is_numeric_dtype(df[col]):
            try:
                corr = abs(df[col].corr(target_series))
                if corr > 0.98:
                    suspects.append({
                        "col": col,
                        "reason": f"correlation with target is {corr:.3f} — suspiciously high",
                        "severity": "high",
                    })
                    continue
            except Exception:
                pass

        # Check 3: linear transformation of target
        # Only flag if BOTH conditions hold:
        # - ratio is almost perfectly constant (std < 0.001)
        # - correlation is extremely high (> 0.999)
        if pd.api.types.is_numeric_dtype(df[col]):
            try:
                corr = abs(df[col].corr(target_series))
                if corr > 0.999:
                    ratio = (target_series / df[col].replace(0, float("nan"))).dropna()
                    if len(ratio) > 10 and ratio.std() < 0.001:
                        suspects.append({
                            "col": col,
                            "reason": "appears to be a linear transformation of target",
                            "severity": "high",
                        })
            except Exception:
                pass

    return suspects


def profile(df: pd.DataFrame, target: str) -> dict:
    """
    Analyze a dataframe and return a structured profile.
    No LLM involved — pure pandas.
    """
    header("Profiling dataset")

    rows, cols = df.shape
    null_count = int(df.isnull().sum().sum())
    null_pct = (null_count / (rows * cols)) * 100

    col_profiles = {}
    issues = []

    for col in df.columns:
        series = df[col]
        col_info = {
            "dtype": str(series.dtype),
            "null_count": int(series.isnull().sum()),
            "null_pct": round(series.isnull().sum() / len(series) * 100, 2),
            "nunique": int(series.nunique()),
            "is_target": col == target,
        }

        # Numeric columns
        if pd.api.types.is_numeric_dtype(series):
            col_info["type"] = "numeric"
            col_info["min"] = float(series.min()) if not series.isnull().all() else None
            col_info["max"] = float(series.max()) if not series.isnull().all() else None
            col_info["mean"] = float(series.mean()) if not series.isnull().all() else None

            # Detect impossible values by column name heuristics
            if col.lower() in ["age", "years"] and col_info["min"] is not None:
                if col_info["min"] < 0 or col_info["max"] > 150:
                    issues.append({
                        "col": col,
                        "type": "impossible_values",
                        "detail": f"values outside plausible range ({col_info['min']} to {col_info['max']})",
                        "auto_fixable": False,
                    })

        # Object columns — check for mixed numeric/text
        elif series.dtype == object:
            numeric_parseable = pd.to_numeric(series.dropna(), errors="coerce").notna().sum()
            total_non_null = series.dropna().shape[0]

            if total_non_null > 0:
                numeric_ratio = numeric_parseable / total_non_null
                if 0.5 < numeric_ratio < 1.0:
                    col_info["type"] = "mixed_numeric"
                    issues.append({
                        "col": col,
                        "type": "mixed_type",
                        "detail": f"{int((1 - numeric_ratio) * total_non_null)} non-numeric values in what looks like a numeric column",
                        "auto_fixable": False,
                    })
                elif _is_id_column(col, series):
                    col_info["type"] = "id_like"
                    issues.append({
                        "col": col,
                        "type": "id_column",
                        "detail": "likely an ID column — not useful as a feature",
                        "auto_fixable": True,
                    })
                elif col_info["nunique"] <= 2 and col == target:
                    col_info["type"] = "binary_target"
                else:
                    col_info["type"] = "categorical"

        # Datetime columns
        elif pd.api.types.is_datetime64_any_dtype(series):
            col_info["type"] = "datetime"

        # Check for date-like strings
        if series.dtype == object and col.lower() in ["date", "created_at", "updated_at", "joined", "date_joined", "timestamp", "time", "datetime"]:
            col_info["likely_date"] = True
            issues.append({
                "col": col,
                "type": "date_string",
                "detail": "looks like a date column stored as text",
                "auto_fixable": True,
            })

        # High null warning
        if col_info["null_pct"] > 40 and col != target:
            issues.append({
                "col": col,
                "type": "high_nulls",
                "detail": f"{col_info['null_pct']:.0f}% missing values",
                "auto_fixable": False,
            })

        # Mixed target encoding (yes/no/1/0/True)
        if col == target and series.dtype == object:
            unique_vals = set(series.dropna().str.lower().unique())
            bool_variants = {"yes", "no", "true", "false", "1", "0", "y", "n"}
            if unique_vals.issubset(bool_variants):
                issues.append({
                    "col": col,
                    "type": "mixed_target_encoding",
                    "detail": f"target has mixed encodings: {list(series.unique()[:5])}",
                    "auto_fixable": True,
                })

        col_profiles[col] = col_info

    # Free text detection (high avg string length, object dtype, not target)
    for col in df.select_dtypes(include="object").columns:
        if col == target:
            continue
        avg_len = df[col].dropna().astype(str).str.len().mean()
        if avg_len > 50:
            issues.append({
                "col": col,
                "type": "free_text",
                "detail": f"looks like free text (avg {avg_len:.0f} chars) — low signal for tabular ML",
                "auto_fixable": True,
            })

    # Leakage detection
    leakage = detect_leakage(df, target)
    
    result = {
        "rows": rows,
        "cols": cols,
        "target": target,
        "null_count": null_count,
        "null_pct": round(null_pct, 2),
        "columns": col_profiles,
        "issues": issues,
        "leakage": leakage,
    }

    if leakage:
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        leaky_cols = [s["col"] for s in leakage]
        drop_str = ",".join(leaky_cols)
        lines = [f"  → [bold]{s['col']}[/bold]: {s['reason']}" for s in leakage]
        console.print(Panel(
            "\n".join([
                "[bold yellow]⚠ DATA LEAKAGE DETECTED[/bold yellow]",
                "",
                "These columns will cause artificially perfect results:",
                "",
                *lines,
                "",
                "[bold]Suggested fix:[/bold]",
                f"  train --data ... --target {target}",
                f"        --drop {drop_str}",
            ]),
            border_style="yellow"
        ))

    profile_table(result)

    if issues:
        warn(f"Found {len(issues)} issue(s) in your dataset")
    else:
        info("No obvious issues detected")

    return result