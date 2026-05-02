import os
import json
from pathlib import Path
from dotenv import load_dotenv
from traincli.utils.display import info, warn

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")


def _available() -> bool:
    if os.getenv("TRAINCLI_NO_LLM") == "1":
        return False
    return bool(GROQ_API_KEY or (
        os.getenv("WATSONX_API_KEY") and os.getenv("WATSONX_PROJECT_ID")
    ))


def _call(prompt: str, system: str = None, max_tokens: int = 800) -> str:
    """
    Make a single Groq API call. Returns response text.
    Falls back gracefully if API key not set.
    """
    if not _available():
        return None

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.2,  # low temp for consistency
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        warn(f"LLM call failed: {e} — falling back to deterministic output")
        return None


def _parse_json(text: str) -> dict | None:
    """Safely parse JSON from LLM response, stripping markdown fences."""
    if not text:
        return None
    try:
        clean = text.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        return json.loads(clean.strip())
    except Exception:
        return None


# ── CALL 1: PROBLEM INFERENCE ─────────────────────────────────
def infer_problem(profile: dict, heuristic_result: str) -> dict:
    """
    Used when heuristic confidence is low.
    Returns: {"problem_type": "regression"|"classification", "reason": str}
    """
    if not _available():
        return {"problem_type": heuristic_result, "reason": "LLM unavailable — used heuristic", "source": "heuristic"}

    info("Consulting LLM for problem type confirmation...")

    # Build compact profile summary — keep tokens low
    cols_summary = []
    for col, info_dict in profile.get("columns", {}).items():
        cols_summary.append({
            "name": col,
            "type": info_dict.get("type", info_dict.get("dtype")),
            "nunique": info_dict.get("nunique"),
            "is_target": info_dict.get("is_target", False),
        })

    prompt = f"""Given this dataset profile, determine the ML problem type.

Dataset:
- Rows: {profile['rows']}
- Target column: {profile['target']}
- Columns: {json.dumps(cols_summary, indent=2)}

Heuristic guess: {heuristic_result}

Respond ONLY with valid JSON, no explanation outside it:
{{"problem_type": "regression" or "classification", "reason": "one sentence explanation"}}"""

    response = _call(prompt, max_tokens=150)
    parsed = _parse_json(response)

    if parsed and "problem_type" in parsed:
        parsed["source"] = "llm"
        return parsed

    # Fallback
    return {"problem_type": heuristic_result, "reason": "LLM response unclear — used heuristic", "source": "heuristic"}


# ── CALL 2: RESULT INTERPRETATION ────────────────────────────
def interpret_results(metrics: dict, problem_type: str, model_label: str,
                      confidence: str, confidence_reasons: list,
                      feature_names: list, profile: dict) -> str:
    """
    Generate a plain-English interpretation of training results.
    Returns a 3-5 sentence summary string.
    """
    if not _available():
        return _fallback_interpretation(metrics, problem_type, model_label, confidence)

    info("Generating result interpretation...")

    prompt = f"""You are a data scientist explaining ML results to a developer who is not an ML expert.

Model trained: {model_label}
Problem type: {problem_type}
Metrics: {json.dumps(metrics)}
Confidence level: {confidence}
Confidence reasons: {confidence_reasons}
Features used: {feature_names}
Dataset rows: {profile.get('rows', 'unknown')}

Write a plain-English interpretation in exactly 3-5 sentences. Cover:
1. How well the model performed and what that means practically
2. The most important thing to know about these results
3. One actionable suggestion to improve if confidence is Medium or Low

Do NOT use bullet points. Write in flowing sentences. No jargon."""

    response = _call(prompt, max_tokens=300)

    if response:
        return response

    return _fallback_interpretation(metrics, problem_type, model_label, confidence)


def _fallback_interpretation(metrics, problem_type, model_label, confidence) -> str:
    if problem_type == "classification":
        acc = metrics.get("Accuracy", "unknown")
        return (
            f"The {model_label} achieved an accuracy of {acc}. "
            f"Confidence is {confidence} — check the report for details on what may be limiting performance. "
            f"Review the generated train.py for the full pipeline and consider gathering more data if accuracy is low."
        )
    else:
        r2 = metrics.get("R²", "unknown")
        return (
            f"The {model_label} achieved an R² of {r2}. "
            f"Confidence is {confidence} — check the report for details. "
            f"Review train.py for the full pipeline."
        )


# ── CALL 3: TRAIN.PY GENERATION ──────────────────────────────
def generate_train_py(pipeline_config: dict, session_data: dict) -> str | None:
    """
    Generate the comments and explanatory sections of train.py.
    Returns a dict of comment strings to inject, or None if LLM unavailable.

    We don't ask LLM to write the whole file — just the explanatory comments.
    This keeps tokens low and ensures the code is always correct.
    """
    if not _available():
        return None

    info("Generating code explanations...")

    model_label = pipeline_config.get("model_label")
    problem_type = pipeline_config.get("problem_type")
    metrics = pipeline_config.get("metrics", {})
    features = pipeline_config.get("features", [])
    confidence = pipeline_config.get("confidence")

    prompt = f"""You are writing comments for a machine learning training script.

Context:
- Model: {model_label}
- Problem: {problem_type}
- Metrics: {json.dumps(metrics)}
- Features: {features}
- Confidence: {confidence}

Write SHORT, educational comments for these 3 sections. Each comment should be 1-2 sentences max.
Respond ONLY with valid JSON:

{{
  "model_choice_comment": "Why {model_label} was a good choice for this data",
  "preprocessing_comment": "Why we use median imputation and standard scaling here",
  "results_comment": "What these metrics mean in plain English for this specific result"
}}"""

    response = _call(prompt, max_tokens=300)
    parsed = _parse_json(response)
    return parsed