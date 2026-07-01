# TrainCLI

**Train ML models from a single command — no code required.**

TrainCLI automates the entire machine learning pipeline: data profiling, cleaning, model selection, training, and export. Go from a CSV to a production-ready model in one command.

```bash
train --data sales.csv --target revenue
```

---

## Installation

```bash
pip install traincli
```

**Requirements:** Python 3.9+, `pandas`, `scikit-learn`

Extra dependencies (e.g. `xgboost`) are installed on demand when you first use a model that needs them.

---

## Quick Start

### 1. Train a model

```bash
train --data sales.csv --target revenue
```

TrainCLI will profile your data, clean it automatically, detect whether it's a classification or regression problem, run cross-validation across multiple algorithms, pick the best one, and export everything to `./output/`.

### 2. Use your model

```python
import pickle, pandas as pd

with open("output/model.pkl", "rb") as f:
    model = pickle.load(f)

prediction = model.predict(pd.DataFrame([{"feature1": 10, "feature2": "A"}]))
```

Or re-run the generated `train.py` to retrain from scratch at any time.

---

## Features

**One-command training**
No boilerplate. Point it at a CSV and a target column.

**Automatic model selection**
Cross-validation across a full candidate pool — classification and regression. A bundled meta-model narrows the search based on dataset characteristics before confirming via CV.

**Smart data cleaning**
Auto-handles ID columns, date parsing, currency strings, boolean encoding, and high-null columns. Prompts you only when a decision is genuinely ambiguous.

**Leakage detection**
Scans for features with >0.98 correlation to the target, name-based hints, and linear transformations. Flags them before training, not after.

**Full reproducibility**
Every training run exports a standalone `train.py` and a `session.json` audit trail. Re-run, share, or customize without touching TrainCLI again.



---

## Architecture

```
CSV Input
   │
   ▼
Profiler ─────────────────────────────┐
   │  (type detection, leakage scan)   │
   ▼                                   │
Cleaner                               LLM Insights
   │  (auto-fix + interactive)         │  (optional)
   ▼                                   │
Detector ◄────────────────────────────┘
   │  (classification vs regression)
   ▼
Trainer
   │  (cross-validation, meta-model, selection)
   ▼
Exporter
   │
   ├── model.pkl
   ├── train.py
   ├── report.md
   ├── metrics.json
   └── session.json
```

**Module responsibilities:**

| Module | Role |
|--------|------|
| `profiler.py` | Column type detection, data quality issues, leakage analysis |
| `cleaner.py` | Auto-fixes and interactive prompts for ambiguous cases |
| `detector.py` | Heuristic problem-type detection with LLM fallback |
| `trainer.py` | Model selection, cross-validation, meta-model integration |
| `exporter.py` | Output generation — pkl, scripts, reports, metadata |
| `mcp_server.py` | MCP server exposing TrainCLI to Claude Desktop |
| `core.py` | Shared pipeline logic used by both CLI and MCP |

---

## Commands

| Command | Description |
|---------|-------------|
| `train --data <file> --target <col>` | Train a model on a CSV |
| `train --dir <folder> --target <col>` | Train on all CSVs in a folder |
| `train --model <name>` | Use a specific algorithm (e.g. `random_forest`) |
| `train --model ?` | Pick a model interactively from a ranked table |
| `train --task classification` | Override auto-detected problem type |
| `train --drop col1,col2` | Drop columns before training (leakage fix) |
| `train --preview` | Profile data without training |
| `train --auto` | Skip all prompts — useful in CI/CD |


**Examples:**

```bash
# Force a specific model
train --data sales.csv --target price --model gradient_boosting

# Interactive model picker
train --data data.csv --target label --model ?

# Drop leaky columns
train --data jobs.csv --target salary --drop min_salary,max_salary

# Batch processing, no prompts
train --dir ./datasets/ --target outcome --auto

# Preview only
train --data data.csv --target col --preview
```

---

## Supported Models

TrainCLI keeps the base install light — only `pandas` and `scikit-learn` are required. XGBoost is supported but not bundled; if cross-validation picks it as the best model for your data, TrainCLI will prompt you to install it before proceeding.

**Classification:** Logistic Regression, Random Forest, Gradient Boosting, SVM, K-Nearest Neighbors, XGBoost*

**Regression:** Linear Regression, Ridge Regression, Random Forest, Gradient Boosting, Support Vector Regression, XGBoost*

*\* Requires `pip install xgboost`. TrainCLI will prompt you if it's needed.*

---

## Output Files

| File | Contents |
|------|----------|
| `model.pkl` | Trained scikit-learn pipeline, ready to use |
| `train.py` | Standalone retraining script with educational comments |
| `report.md` | Human-readable summary — metrics, interpretation, decisions |
| `metrics.json` | Machine-readable metrics for downstream tooling |
| `session.json` | Full audit trail: every decision the pipeline made |

---



## MCP Server (Claude Desktop Integration)

TrainCLI ships with an MCP server so Claude Desktop can train models directly.

**Setup:**

```bash
pip install traincli
```

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "traincli": {
      "command": "traincli-mcp"
    }
  }
}
```

Restart Claude Desktop.

**Available tools:**

| Tool | Description |
|------|-------------|
| `train_model` | Run the full pipeline on a CSV |
| `profile_dataset` | Analyze data without training |
| `suggest_target` | Recommend the best target column |

**Example:**

```
User: Train a model on sales.csv to predict revenue

Claude: [calls train_model]
✓ Model trained: Gradient Boosting
✓ R² = 0.847
✓ Files saved to ./output/
```

---

## Development

```bash
git clone https://github.com/yourusername/traincli
cd traincli
pip install -e .
```

---



## License

MIT

## Contributing

Open an issue or PR — contributions welcome.

---

*Built for the IBM Dev Day: Bob Edition Hackathon.*
