import pandas as pd
import numpy as np
import click
from traincli.utils.display import header, success, warn, info, blank
from traincli.utils.session import Session


# Mappings for standardizing boolean-like target columns
BOOL_MAP = {
    "yes": 1, "no": 0,
    "true": 1, "false": 0,
    "y": 1, "n": 0,
    "1": 1, "0": 0,
}


def _convert_currency_columns(df: pd.DataFrame, session: Session) -> pd.DataFrame:
    """
    Detect and convert currency/number strings to numeric.
    e.g. '$1,234,567' → 1234567.0
    """
    for col in df.select_dtypes(include="object").columns:
        sample = df[col].dropna().astype(str).head(10)
        
        if len(sample) == 0:
            continue
        
        # Check if it looks like a formatted number
        looks_numeric = sample.str.replace(
            r'[$£€,\s%()]', '', regex=True
        ).str.replace(r'^\-?\d+\.?\d*$', 'match', regex=True)
        
        match_ratio = (looks_numeric == 'match').mean()
        
        if match_ratio >= 0.7:  # 70%+ look numeric after stripping symbols
            converted = pd.to_numeric(
                df[col].astype(str)
                .str.replace(r'[$£€,\s%]', '', regex=True)
                .str.replace(r'\((\d+)\)', r'-\1', regex=True),  # (123) → -123
                errors='coerce'
            )
            if converted.notna().mean() >= 0.7:
                df[col] = converted
                session.add_auto_fix(
                    f"Converted '{col}' from formatted string to numeric"
                )
    
    return df


def clean(df: pd.DataFrame, profile: dict, session: Session, auto: bool = False) -> pd.DataFrame:
    """
    Clean a dataframe based on its profile.
    Auto-fixes obvious issues, asks user about ambiguous ones.

    Args:
        df:      raw dataframe
        profile: output from profiler.profile()
        session: session tracker
        auto:    if True, skip interactive prompts (use safe defaults)
    """
    header("Cleaning dataset")

    original_rows = len(df)
    
    # Convert currency/formatted number strings first
    df = _convert_currency_columns(df, session)
    
    issues = profile["issues"]
    target = profile["target"]

    auto_fixes = []
    needs_input = []

    for issue in issues:
        if issue["auto_fixable"]:
            auto_fixes.append(issue)
        else:
            needs_input.append(issue)

    # ── AUTO FIXES ────────────────────────────────────────────
    if auto_fixes:
        info("Auto-fixing the following:")
        blank()

    for issue in auto_fixes:
        col = issue["col"]
        itype = issue["type"]

        if itype == "id_column":
            df = df.drop(columns=[col])
            session.add_col_dropped(col, "unique identifier — not a feature")
            session.add_auto_fix(f"Dropped '{col}' (ID column)")
            success(f"Dropped '{col}' — unique identifier, not useful as a feature")

        elif itype == "date_string":
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                df[f"{col}_month"] = df[col].dt.month
                df[f"{col}_dayofweek"] = df[col].dt.dayofweek
                df[f"{col}_year"] = df[col].dt.year
                df = df.drop(columns=[col])
                session.add_auto_fix(f"Parsed '{col}' → month, dayofweek, year features")
                success(f"Parsed '{col}' → extracted month, day_of_week, year as features")
            except Exception:
                warn(f"Could not parse '{col}' as date — leaving as-is")

        elif itype == "mixed_target_encoding":
            df[col] = df[col].astype(str).str.lower().str.strip().map(BOOL_MAP)
            session.add_auto_fix(f"Standardized target '{col}' encoding → 0/1")
            success(f"Standardized target '{col}' → 0/1")

        elif itype == "free_text":
            df = df.drop(columns=[col])
            session.add_col_dropped(col, "free text column — low signal for tabular ML")
            session.add_auto_fix(f"Dropped '{col}' (free text)")
            success(f"Dropped '{col}' — free text column, not useful for tabular ML")

    # ── USER INPUT REQUIRED ───────────────────────────────────
    if needs_input and not auto:
        blank()
        info("The following need your input:")
        blank()

    for issue in needs_input:
        col = issue["col"]
        itype = issue["type"]

        if itype == "mixed_type":
            warn(f"'{col}': {issue['detail']}")

            if auto:
                # Safe default: drop bad rows
                df[col] = pd.to_numeric(df[col], errors="coerce")
                bad_rows = df[col].isnull().sum()
                df = df.dropna(subset=[col])
                session.add_user_decision(f"'{col}' mixed types", "auto: dropped bad rows")
                success(f"Dropped {bad_rows} unrecoverable rows in '{col}'")
            else:
                choice = click.prompt(
                    "  Non-numeric values found. What should I do?\n"
                    "  [1] Drop rows with bad values\n"
                    "  [2] Impute with column median\n"
                    "  Choice",
                    type=click.Choice(["1", "2"]),
                    default="1",
                    show_choices=False,
                )
                df[col] = pd.to_numeric(df[col], errors="coerce")
                if choice == "1":
                    bad_rows = df[col].isnull().sum()
                    df = df.dropna(subset=[col])
                    session.add_user_decision(f"'{col}' mixed types", "dropped bad rows")
                    success(f"Dropped {bad_rows} rows with non-numeric values in '{col}'")
                else:
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val)
                    session.add_user_decision(f"'{col}' mixed types", f"imputed with median ({median_val:.2f})")
                    success(f"Imputed '{col}' missing values with median ({median_val:.2f})")

        elif itype == "impossible_values":
            warn(f"'{col}': {issue['detail']}")

            if auto:
                df[col] = df[col].clip(lower=0)
                session.add_user_decision(f"'{col}' impossible values", "auto: clipped to 0")
                success(f"Clipped '{col}' to minimum 0")
            else:
                choice = click.prompt(
                    "  Impossible values detected. What should I do?\n"
                    "  [1] Drop affected rows\n"
                    "  [2] Clip to plausible range\n"
                    "  Choice",
                    type=click.Choice(["1", "2"]),
                    default="2",
                    show_choices=False,
                )
                if choice == "1":
                    before = len(df)
                    df = df[df[col] >= 0]
                    session.add_user_decision(f"'{col}' impossible values", "dropped affected rows")
                    success(f"Dropped {before - len(df)} rows with impossible values in '{col}'")
                else:
                    df[col] = df[col].clip(lower=0)
                    session.add_user_decision(f"'{col}' impossible values", "clipped to 0")
                    success(f"Clipped '{col}' values to minimum 0")

        elif itype == "high_nulls":
            warn(f"'{col}': {issue['detail']}")

            if auto:
                df = df.drop(columns=[col])
                session.add_user_decision(f"'{col}' high nulls", "auto: dropped column")
                session.add_col_dropped(col, f"too many nulls ({issue['detail']})")
                success(f"Dropped '{col}' — too many missing values")
            else:
                choice = click.prompt(
                    f"  '{col}' has {issue['detail']}. What should I do?\n"
                    "  [1] Drop the column\n"
                    "  [2] Keep and impute with median/mode\n"
                    "  Choice",
                    type=click.Choice(["1", "2"]),
                    default="1",
                    show_choices=False,
                )
                if choice == "1":
                    df = df.drop(columns=[col])
                    session.add_col_dropped(col, f"too many nulls ({issue['detail']})")
                    session.add_user_decision(f"'{col}' high nulls", "dropped column")
                    success(f"Dropped '{col}'")
                else:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        df[col] = df[col].fillna(df[col].median())
                        session.add_user_decision(f"'{col}' high nulls", "imputed with median")
                    else:
                        df[col] = df[col].fillna(df[col].mode()[0])
                        session.add_user_decision(f"'{col}' high nulls", "imputed with mode")
                    success(f"Imputed '{col}' missing values")

    # ── REMAINING NULLS — handled silently ───────────────────
    # At this point impute remaining nulls with safe defaults
    for col in df.columns:
        if col == target:
            continue
        null_count = df[col].isnull().sum()
        if null_count > 0:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].median())
                session.add_auto_fix(f"Imputed {null_count} nulls in '{col}' with median")
            else:
                df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else "unknown")
                session.add_auto_fix(f"Imputed {null_count} nulls in '{col}' with mode")

    # Drop rows where target is null
    before = len(df)
    df = df.dropna(subset=[target])
    if len(df) < before:
        dropped = before - len(df)
        session.add_auto_fix(f"Dropped {dropped} rows with null target values")
        warn(f"Dropped {dropped} rows with missing target values")

    # ── SUMMARY ───────────────────────────────────────────────
    rows_dropped = original_rows - len(df)
    session.set_rows_dropped(rows_dropped)

    blank()
    info(f"Dataset after cleaning: {len(df):,} rows × {len(df.columns)} columns")
    if rows_dropped > 0:
        info(f"{rows_dropped} rows dropped from original {original_rows:,}")

    return df