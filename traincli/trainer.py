import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score, classification_report,
    r2_score, mean_absolute_error, mean_squared_error
)
from traincli.utils.display import header, success, info, warn, blank, metrics_table, model_picker_table
from traincli.utils.session import Session
from traincli.models.registry import get_model, get_default, REGISTRY


def select_model_interactive(problem_type: str) -> dict:
    """Show the interactive model picker and return selected model entry."""
    import click
    from rich.console import Console
    console = Console()

    models = REGISTRY[problem_type]
    default = get_default(problem_type)

    blank()
    console.print(f"[bold]Available models for {problem_type}:[/bold]")
    blank()
    model_picker_table(models, default["key"])

    choice = click.prompt(
        f"  Pick a model [1-{len(models)}] or press Enter for recommended",
        default="",
        show_default=False,
    )

    if choice.strip() == "":
        return default

    try:
        idx = int(choice.strip()) - 1
        if 0 <= idx < len(models):
            return models[idx]
    except ValueError:
        pass

    warn("Invalid choice — using recommended model")
    return default


def train(
    df: pd.DataFrame,
    target: str,
    problem_type: str,
    session: Session,
    model_key: str = None,
    interactive: bool = True,
    profile: dict = None,
) -> dict:
    """
    Build pipeline, train model, evaluate, return results dict.
    """
    from rich.console import Console
    console = Console()

    header("Training")

    # ── FEATURES & TARGET ────────────────────────────────────
    X = df.drop(columns=[target])
    y = df[target].copy()

    # Encode categorical features
    label_encoders = {}
    for col in X.select_dtypes(include="object").columns:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        label_encoders[col] = le

    # Encode target if classification and object dtype
    target_encoder = None
    if problem_type == "classification" and y.dtype == object:
        le = LabelEncoder()
        y = pd.Series(le.fit_transform(y), name=target)
        target_encoder = le

    # ── MODEL SELECTION ──────────────────────────────────────
    model_entry = None

    if model_key == "?":
        if not interactive:
            model_entry = get_default(problem_type)
            session.set_model(model_entry["key"], model_entry["label"], "auto_default")
        else:
            model_entry = select_model_interactive(problem_type)
            session.set_model(model_entry["key"], model_entry["label"], "user_interactive")

    elif model_key is not None:
        model_entry = get_model(problem_type, model_key)

        if model_entry is None:
            # Check wrong problem type
            other = "classification" if problem_type == "regression" else "regression"
            wrong_entry = get_model(other, model_key)
            if wrong_entry:
                warn(f"'{model_key}' is a {other} model but your problem is {problem_type}.")
                if interactive:
                    import click
                    proceed = click.confirm("  Proceed anyway?", default=False)
                    if not proceed:
                        model_entry = get_default(problem_type)
                        warn(f"Using recommended: {model_entry['label']}")
                    else:
                        model_entry = wrong_entry
                else:
                    model_entry = get_default(problem_type)
            else:
                warn(f"Unknown model '{model_key}' — using recommended default")
                model_entry = get_default(problem_type)

        session.set_model(model_entry["key"], model_entry["label"], "user_flag")

    else:
        info("No model specified — running candidates and picking best...")
        model_entry = _auto_select(X, y, problem_type, session)

    info(f"Model: [bold]{model_entry['label']}[/bold]")

    # ── PIPELINE ─────────────────────────────────────────────
    pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", model_entry["class"](**model_entry["params"])),
    ])

    # ── TRAIN / TEST SPLIT ───────────────────────────────────
    try:
        stratify = y if problem_type == "classification" else None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify
        )
    except ValueError:
        # Stratify can fail if some classes have < 2 samples
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

    # ── CROSS VALIDATION ─────────────────────────────────────
    info("Running 3-fold cross-validation...")
    try:
        cv_scores = cross_val_score(pipeline, X_train, y_train, cv=3)
    except Exception as e:
        warn(f"CV failed ({e}) — skipping")
        cv_scores = np.array([0.0, 0.0, 0.0])

    info(f"CV score: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # ── FIT ───────────────────────────────────────────────────
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    # ── METRICS ──────────────────────────────────────────────
    blank()
    header("Evaluation")

    if problem_type == "classification":
        metrics = {
            "Accuracy": f"{accuracy_score(y_test, y_pred):.4f}",
            "CV Mean":  f"{cv_scores.mean():.4f}",
            "CV Std":   f"{cv_scores.std():.4f}",
        }
    else:
        metrics = {
            "R²":      f"{r2_score(y_test, y_pred):.4f}",
            "MAE":     f"{mean_absolute_error(y_test, y_pred):.4f}",
            "RMSE":    f"{np.sqrt(mean_squared_error(y_test, y_pred)):.4f}",
            "CV Mean": f"{cv_scores.mean():.4f}",
            "CV Std":  f"{cv_scores.std():.4f}",
        }

    metrics_table(metrics, problem_type)
    session.set_metrics(metrics)

    # ── CONFIDENCE ───────────────────────────────────────────
    confidence, reasons = _confidence(df, cv_scores, problem_type, y)
    blank()
    _print_confidence(confidence, reasons, console)

    # ── LLM INTERPRETATION ───────────────────────────────────
    interpretation = None
    try:
        from traincli.llm import interpret_results
        interpretation = interpret_results(
            metrics=metrics,
            problem_type=problem_type,
            model_label=model_entry["label"],
            confidence=confidence,
            confidence_reasons=reasons,
            feature_names=list(X.columns),
            profile=profile or {"rows": len(df)},
        )
        if interpretation:
            blank()
            console.print("[bold dim]── Interpretation[/bold dim]")
            console.print(f"[dim]{interpretation}[/dim]")
    except Exception:
        pass  # LLM is optional — never break the pipeline

    return {
        "pipeline":           pipeline,
        "model_entry":        model_entry,
        "metrics":            metrics,
        "cv_scores":          cv_scores,
        "confidence":         confidence,
        "confidence_reasons": reasons,
        "interpretation":     interpretation,
        "feature_names":      list(X.columns),
        "label_encoders":     label_encoders,
        "target_encoder":     target_encoder,
        "problem_type":       problem_type,
        "X_train":            X_train,
    }


def improve(model_path: str, new_data_path: str, target: str, session: Session) -> dict:
    """
    Load an existing model, retrain on new data, compare metrics.
    """
    header("Improve mode")

    # Load existing model
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    with open(path, "rb") as f:
        old_pipeline = pickle.load(f)

    info(f"Loaded existing model from {model_path}")

    # Load new data
    df_new = pd.read_csv(new_data_path)
    if target not in df_new.columns:
        raise ValueError(f"Target '{target}' not found in new data")

    info(f"New data: {len(df_new):,} rows")

    X_new = df_new.drop(columns=[target])
    y_new = df_new[target]

    # Encode categoricals
    for col in X_new.select_dtypes(include="object").columns:
        le = LabelEncoder()
        X_new[col] = le.fit_transform(X_new[col].astype(str))

    if y_new.dtype == object:
        le = LabelEncoder()
        y_new = pd.Series(le.fit_transform(y_new))

    X_train, X_test, y_train, y_test = train_test_split(
        X_new, y_new, test_size=0.2, random_state=42
    )

    # Score old model on new data
    try:
        old_score = old_pipeline.score(X_test, y_test)
        info(f"Old model score on new data: {old_score:.4f}")
    except Exception:
        old_score = None
        warn("Could not score old model on new data — feature mismatch likely")

    # Retrain
    info("Retraining on new data...")
    old_pipeline.fit(X_train, y_train)
    new_score = old_pipeline.score(X_test, y_test)
    info(f"New model score after retraining: {new_score:.4f}")

    if old_score is not None:
        delta = new_score - old_score
        color = "green" if delta >= 0 else "red"
        from rich.console import Console
        Console().print(f"  Change: [{color}]{delta:+.4f}[/{color}]")

    session.set_metrics({
        "score_before": f"{old_score:.4f}" if old_score else "N/A",
        "score_after":  f"{new_score:.4f}",
    })

    return {
        "pipeline":     old_pipeline,
        "score_before": old_score,
        "score_after":  new_score,
    }


# ── INTERNAL HELPERS ─────────────────────────────────────────

def _meta_predict(X: pd.DataFrame, problem_type: str) -> str | None:
    """
    Use the bundled meta-model to recommend a model
    based on dataset characteristics.
    Returns model key or None if meta-model unavailable.
    """
    try:
        meta_path = Path(__file__).parent / "meta_model.pkl"
        if not meta_path.exists():
            return None

        with open(meta_path, "rb") as f:
            meta_model = pickle.load(f)

        features = pd.DataFrame([{
            "rows":              len(X),
            "cols":              len(X.columns),
            "null_pct":          0.0,
            "numeric_ratio":     len(X.select_dtypes(include="number").columns) / max(len(X.columns), 1),
            "categorical_ratio": len(X.select_dtypes(include="object").columns) / max(len(X.columns), 1),
            "target_nunique":    0,
            "target_is_float":   0,
            "target_range":      0.0,
            "problem_type":      0 if problem_type == "classification" else 1,
            "cv_mean":           0.0,
            "cv_std":            0.0,
        }])

        prediction = meta_model.predict(features)[0]

        # Decode numeric prediction back to model name
        # LabelEncoder sorts alphabetically:
        # 0=gradient_boosting, 1=random_forest, 2=xgboost
        label_map = {0: "gradient_boosting", 1: "random_forest", 2: "xgboost"}
        if isinstance(prediction, (int, np.integer)):
            return label_map.get(int(prediction))

        return str(prediction)

    except Exception:
        return None


def _auto_select(X, y, problem_type: str, session: Session) -> dict:
    """Use meta-model recommendation first, confirm with CV."""

    # Ask the meta-model first
    meta_rec = _meta_predict(X, problem_type)
    if meta_rec:
        info(f"Meta-model recommends: [bold]{meta_rec}[/bold]")

    candidates_keys = ["random_forest", "gradient_boosting", "xgboost"]
    best_score = -np.inf
    best_entry = None

    for key in candidates_keys:
        entry = get_model(problem_type, key)
        if entry is None:
            continue
        pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", entry["class"](**entry["params"])),
        ])
        try:
            scores = cross_val_score(pipeline, X, y, cv=3)
            mean = scores.mean()
            info(f"  {entry['label']}: CV={mean:.3f}")
            if mean > best_score:
                best_score = mean
                best_entry = entry
        except Exception as e:
            warn(f"  {entry['label']}: failed ({e})")

    if best_entry is None:
        best_entry = get_default(problem_type)

    # Compare meta recommendation vs CV winner
    if meta_rec and best_entry["key"] == meta_rec:
        success(f"Selected: {best_entry['label']} (CV={best_score:.3f}) — meta-model confirmed ✓")
    elif meta_rec:
        info(f"Meta-model suggested {meta_rec} but CV picked {best_entry['label']} — using CV result")
    else:
        success(f"Selected: {best_entry['label']} (CV={best_score:.3f})")

    session.set_model(best_entry["key"], best_entry["label"], "auto_cv")
    return best_entry


def _confidence(df, cv_scores, problem_type, y) -> tuple:
    reasons = []
    score = 3

    if len(df) < 500:
        score -= 1
        reasons.append(f"Small dataset ({len(df):,} rows) — predictions may not generalize well")

    if cv_scores.std() > 0.05:
        score -= 1
        reasons.append(f"High variance across CV folds (±{cv_scores.std():.3f}) — model is sensitive to data splits")

    if problem_type == "classification":
        try:
            class_balance = pd.Series(y).value_counts(normalize=True)
            if class_balance.min() < 0.15:
                score -= 1
                reasons.append(f"Class imbalance detected (minority: {class_balance.min():.0%}) — model may underperform on rare class")
        except Exception:
            pass

    if score >= 3:
        return "High", reasons
    elif score == 2:
        return "Medium", reasons
    else:
        return "Low", reasons


def _print_confidence(confidence: str, reasons: list, console):
    colors = {"High": "green", "Medium": "yellow", "Low": "red"}
    color = colors.get(confidence, "white")
    console.print(f"Confidence: [bold {color}]{confidence}[/bold {color}]")
    for r in reasons:
        console.print(f"  [dim]→[/dim] {r}")