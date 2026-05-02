import pickle
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from traincli.utils.display import header, success, blank
from traincli.utils.session import Session


def export(results: dict, df_cleaned, target: str, data_path: str, output_dir: Path, session: Session):
    header("Exporting outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    # model.pkl
    model_path = output_dir / "model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(results["pipeline"], f)
    success(f"model.pkl → {model_path}")
    session.add_output_file(str(model_path))

    # metrics.json
    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w", encoding='utf-8') as f:
        json.dump(results["metrics"], f, indent=2)
    success(f"metrics.json → {metrics_path}")
    session.add_output_file(str(metrics_path))

    # report.md
    report_path = output_dir / "report.md"
    report = _build_report(results, df_cleaned, target, data_path)
    with open(report_path, "w", encoding='utf-8') as f:
        f.write(report)
    success(f"report.md → {report_path}")
    session.add_output_file(str(report_path))

    # train.py — try LLM-enhanced first, fall back to static
    train_py_path = output_dir / "train.py"
    llm_comments = _fetch_llm_comments(results)
    train_py = _build_train_py(results, df_cleaned, target, data_path, session, llm_comments)
    with open(train_py_path, "w", encoding='utf-8') as f:
        f.write(train_py)
    success(f"train.py → {train_py_path}")
    session.add_output_file(str(train_py_path))

    # session.json
    session.complete()
    session_path = session.save(output_dir)
    success(f"session.json → {session_path}")
    blank()


def _fetch_llm_comments(results: dict) -> dict:
    """Try to get LLM-generated comments. Returns empty dict if unavailable."""
    try:
        from traincli.llm import generate_train_py
        comments = generate_train_py({
            "model_label":   results["model_entry"]["label"],
            "problem_type":  results["problem_type"],
            "metrics":       results["metrics"],
            "features":      results["feature_names"],
            "confidence":    results["confidence"],
        }, {})
        return comments or {}
    except Exception:
        return {}


def _build_report(results: dict, df, target: str, data_path: str) -> str:
    model_label  = results["model_entry"]["label"]
    problem_type = results["problem_type"]
    metrics      = results["metrics"]
    confidence   = results["confidence"]
    reasons      = results["confidence_reasons"]
    cv           = results["cv_scores"]
    interp       = results.get("interpretation", "")

    lines = [
        "# TrainCLI Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
        f"**Dataset:** `{data_path}`  ",
        f"**Target:** `{target}`  ",
        f"**Problem:** {problem_type.capitalize()}  ",
        f"**Model:** {model_label}  ",
        "",
        "---",
        "",
        "## Metrics",
        "",
    ]
    for k, v in metrics.items():
        lines.append(f"- **{k}:** {v}")

    if interp:
        lines += ["", "---", "", "## Interpretation", "", interp]

    lines += [
        "",
        "---",
        "",
        f"## Confidence: {confidence}",
        "",
    ]
    if reasons:
        for r in reasons:
            lines.append(f"- {r}")
    else:
        lines.append("- No major concerns detected.")

    lines += [
        "",
        "---",
        "",
        "## Dataset Summary",
        "",
        f"- **Rows (after cleaning):** {len(df):,}",
        f"- **Features used:** {', '.join(results['feature_names'])}",
        f"- **Cross-validation:** 3-fold, mean={cv.mean():.4f} ± {cv.std():.4f}",
        "",
        "---",
        "",
        "## How to Use This Model",
        "",
        "```python",
        "import pickle",
        "import pandas as pd",
        "from sklearn.preprocessing import LabelEncoder",
        "",
        "with open('model.pkl', 'rb') as f:",
        "    model = pickle.load(f)",
        "",
        "new_data = pd.DataFrame([{",
    ]
    for feat in results["feature_names"]:
        lines.append(f'    "{feat}": ...,')
    lines += [
        "}])",
        "",
        "# Encode categorical columns (same as training)",
        "for col in new_data.select_dtypes(include='object').columns:",
        "    le = LabelEncoder()",
        "    new_data[col] = le.fit_transform(new_data[col].astype(str))",
        "",
        "prediction = model.predict(new_data)",
        "print(prediction)",
        "```",
    ]
    return "\n".join(lines)


def _build_train_py(results: dict, df, target: str, data_path: str, session: Session, llm_comments: dict) -> str:
    model_entry  = results["model_entry"]
    model_class  = model_entry["class"]
    model_params = model_entry["params"]
    problem_type = results["problem_type"]
    features     = results["feature_names"]
    metrics      = results["metrics"]
    confidence   = results["confidence"]
    conf_reasons = results["confidence_reasons"]
    model_source = session.data["model"]["source"]

    params_str = ", ".join(f"{k}={repr(v)}" for k, v in model_params.items())
    module_path = model_class.__module__
    class_name  = model_class.__name__

    # LLM comments with static fallbacks
    model_comment   = llm_comments.get("model_choice_comment",
        f"{model_entry['label']} was selected — {model_entry['description']}")
    preproc_comment = llm_comments.get("preprocessing_comment",
        "Median imputation handles outliers better than mean. StandardScaler normalizes feature ranges.")
    results_comment = llm_comments.get("results_comment",
        f"Confidence is {confidence}. " + (conf_reasons[0] if conf_reasons else "Review metrics carefully."))

    # Source comment
    if model_source == "auto_cv":
        source_comment = "# Selected by TrainCLI via cross-validation — outperformed other candidates"
    elif model_source in ("user_flag", "user_interactive"):
        source_comment = "# Selected by user"
    else:
        source_comment = "# Selected automatically"

    # Cleaning notes
    auto_fixes    = session.data["cleaning"]["auto_fixes"]
    user_decisions = session.data["cleaning"]["user_decisions"]
    cleaning_lines = [f"# Auto: {f}" for f in auto_fixes] + \
                     [f"# User: {d['choice']} ({d['issue']})" for d in user_decisions]
    cleaning_block = "\n".join(cleaning_lines) if cleaning_lines else "# No cleaning actions taken"

    # Confidence block
    conf_lines = "\n".join(f"# - {r}" for r in conf_reasons) or "# No major concerns"

    # Stratify line
    stratify_line = "stratify=y," if problem_type == "classification" else "# stratify not used for regression"

    # Metrics block
    if problem_type == "classification":
        eval_line = "print(classification_report(y_test, y_pred))"
        eval_import = "from sklearn.metrics import accuracy_score, classification_report"
    else:
        eval_line = 'print(f"R²:   {r2_score(y_test, y_pred):.4f}")\nprint(f"MAE:  {mean_absolute_error(y_test, y_pred):.4f}")\nprint(f"RMSE: {np.sqrt(mean_squared_error(y_test, y_pred)):.4f}")'
        eval_import = "from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error"

    # Build usage block with dtype hints
    usage_lines = []
    for feat in features:
        # Determine dtype from cleaned dataframe
        if feat in df.columns:
            dtype = df[feat].dtype
            if pd.api.types.is_numeric_dtype(dtype):
                hint = "numeric"
            elif pd.api.types.is_object_dtype(dtype):
                hint = "categorical — will be encoded"
            else:
                hint = str(dtype)
        else:
            hint = "unknown"
        usage_lines.append(f'#     "{feat}": ...,  # {hint}')
    
    usage_block = "\n".join(usage_lines)

    return f'''# ============================================================
# TrainCLI — Generated Training Script
# Dataset  : {data_path}
# Target   : {target}
# Problem  : {problem_type.capitalize()}
# Model    : {model_entry["label"]}
# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# ============================================================
# Standalone script — modify and run without TrainCLI.
# ============================================================

import pandas as pd
import numpy as np
import pickle
import json
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, LabelEncoder
{eval_import}
from {module_path} import {class_name}


# ── 1. LOAD DATA ─────────────────────────────────────────────
df = pd.read_csv("{data_path}")


# ── 2. CLEANING ──────────────────────────────────────────────
# Changes made during TrainCLI run — replicate for new data:
{cleaning_block}


# ── 3. FEATURES & TARGET ─────────────────────────────────────
X = df.drop(columns=["{target}"])
y = df["{target}"]

# Encode categorical string columns to numeric
for col in X.select_dtypes(include="object").columns:
    le = LabelEncoder()
    X[col] = le.fit_transform(X[col].astype(str))

{"# Encode target (categorical detected)" + chr(10) + "le_target = LabelEncoder()" + chr(10) + "y = pd.Series(le_target.fit_transform(y))" if problem_type == "classification" else "# Target is numeric — no encoding needed"}


# ── 4. TRAIN / TEST SPLIT ────────────────────────────────────
# 80/20 split, stratified to preserve class balance
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    {stratify_line}
)


# ── 5. PIPELINE ──────────────────────────────────────────────
# {preproc_comment}
pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler",  StandardScaler()),

    # {model_comment}
    {source_comment}
    ("model", {class_name}({params_str})),
])


# ── 6. CROSS VALIDATION ──────────────────────────────────────
# 3-fold CV checks stability before committing to full fit
cv_scores = cross_val_score(pipeline, X_train, y_train, cv=3)
print(f"CV Score: {{cv_scores.mean():.3f}} ± {{cv_scores.std():.3f}}")


# ── 7. TRAIN ─────────────────────────────────────────────────
pipeline.fit(X_train, y_train)


# ── 8. EVALUATE ──────────────────────────────────────────────
# {results_comment}
y_pred = pipeline.predict(X_test)
print("\\n── Evaluation ──────────────────────────")
{eval_line}


# ── 9. CONFIDENCE NOTE ───────────────────────────────────────
# Confidence: {confidence}
{conf_lines}


# ── 10. SAVE MODEL ───────────────────────────────────────────
with open("model.pkl", "wb") as f:
    pickle.dump(pipeline, f)
print("\\n✓ Model saved to model.pkl")


# ── HOW TO USE ───────────────────────────────────────────────
# import pickle
# import pandas as pd
# from sklearn.preprocessing import LabelEncoder
#
# with open("model.pkl", "rb") as f:
#     model = pickle.load(f)
#
# new_data = pd.DataFrame([{{
{usage_block}
# }}])
#
# # Required: encode categoricals the same way as training
# for col in new_data.select_dtypes(include='object').columns:
#     le = LabelEncoder()
#     new_data[col] = le.fit_transform(new_data[col].astype(str))
#
# print(model.predict(new_data))
'''