"""
Core pipeline logic — used by both CLI and MCP server.
"""
import pandas as pd
from pathlib import Path
from traincli.utils.session import Session
from traincli.profiler import profile
from traincli.cleaner import clean
from traincli.detector import detect
from traincli.trainer import train
from traincli.exporter import export


def run_pipeline(
    data_path: str,
    target: str,
    model_key: str = None,
    task: str = None,
    out: str = "./output",
    auto: bool = True,
    drop: str = None,
) -> dict:
    """
    Core ML pipeline — loads data, profiles, cleans, trains, exports.
    
    Args:
        data_path: Path to CSV file
        target: Target column name
        model_key: Model to use (None = auto-select)
        task: Problem type override ("classification" or "regression")
        out: Output directory
        auto: Skip interactive prompts
        drop: Comma-separated columns to drop
    
    Returns:
        dict with keys: results, df_clean, profile, output_dir
    """
    # Load
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {data_path}")
    
    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise ValueError(f"Could not read CSV: {e}")
    
    if target not in df.columns:
        raise ValueError(f"Target '{target}' not found. Available: {list(df.columns)}")
    
    session = Session(data_path, target)
    
    # Profile
    prof = profile(df, target)
    session.set_profile({
        "rows": prof["rows"],
        "cols": prof["cols"],
        "null_pct": prof["null_pct"],
        "issues_found": len(prof["issues"]),
    })
    
    # Drop columns if requested
    if drop:
        cols_to_drop = [c.strip() for c in drop.split(",")]
        cols_to_drop = [c for c in cols_to_drop if c in df.columns and c != target]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
    
    # Clean
    df_clean = clean(df, prof, session, auto=auto)
    
    # Detect problem type
    if task:
        session.set_problem(task, "user_flag")
        problem_type = task
    else:
        problem_type = detect(df_clean, target, session)
    
    # Train
    results = train(
        df=df_clean,
        target=target,
        problem_type=problem_type,
        session=session,
        model_key=model_key,
        interactive=not auto,
        profile=prof,
    )
    
    # Export
    output_dir = Path(out)
    export(results, df_clean, target, data_path, output_dir, session)
    
    return {
        "results": results,
        "df_clean": df_clean,
        "profile": prof,
        "output_dir": str(output_dir.resolve()),
        "session": session,
    }


def profile_dataset(data_path: str, target: str = None) -> dict:
    """
    Profile a dataset without training.
    
    Args:
        data_path: Path to CSV file
        target: Optional target column (for leakage detection)
    
    Returns:
        Profile dict with dataset statistics
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {data_path}")
    
    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise ValueError(f"Could not read CSV: {e}")
    
    # If no target specified, use first column
    if not target:
        target = df.columns[0]
    
    if target not in df.columns:
        raise ValueError(f"Target '{target}' not found. Available: {list(df.columns)}")
    
    prof = profile(df, target)
    return prof


def suggest_target(data_path: str) -> dict:
    """
    Suggest the best target column for a dataset.
    
    Args:
        data_path: Path to CSV file
    
    Returns:
        dict with suggested target and reasoning
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {data_path}")
    
    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise ValueError(f"Could not read CSV: {e}")
    
    # Heuristics for target selection:
    # 1. Column named "target", "label", "y", "outcome"
    # 2. Last column (common convention)
    # 3. Column with moderate cardinality (not ID, not free text)
    
    target_keywords = ["target", "label", "y", "outcome", "class", "prediction"]
    
    for col in df.columns:
        if col.lower() in target_keywords:
            return {
                "suggested_target": col,
                "reason": f"Column name '{col}' suggests it's the target",
                "confidence": "high"
            }
    
    # Check last column
    last_col = df.columns[-1]
    nunique = df[last_col].nunique()
    total = len(df)
    
    if 2 <= nunique <= total * 0.5:
        return {
            "suggested_target": last_col,
            "reason": f"Last column with {nunique} unique values (common convention)",
            "confidence": "medium"
        }
    
    # Fallback: find column with reasonable cardinality
    for col in df.columns:
        nunique = df[col].nunique()
        if 2 <= nunique <= total * 0.5:
            return {
                "suggested_target": col,
                "reason": f"Column has {nunique} unique values (suitable for prediction)",
                "confidence": "low"
            }
    
    return {
        "suggested_target": df.columns[-1],
        "reason": "No clear target found — defaulting to last column",
        "confidence": "very_low"
    }

# Made with Bob
