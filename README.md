# TrainCLI

#Created for IBM Dev Day: Bob Edition Hackathon
**Train ML models from a single command — no code required.**

TrainCLI is a command-line tool that automates the entire machine learning pipeline: data profiling, cleaning, model selection, training, and export. Perfect for rapid prototyping, baseline models, or learning ML workflows.

## Features

- 🚀 **One-command training** — `train --data data.csv --target column`
- 🤖 **Auto model selection** — Cross-validation picks the best algorithm
- 🧹 **Smart data cleaning** — Handles missing values, outliers, encoding
- 📊 **Data profiling** — Detects issues before training
- 🔍 **Leakage detection** — Warns about suspiciously correlated features
- 🧠 **LLM-powered insights** — Optional AI explanations (watsonx.ai)
- 📦 **Export everything** — model.pkl, train.py, report.md, metrics.json
- 🔧 **Reproducible** — Generated train.py is standalone

## Installation

```bash
pip install traincli
```

## Quick Start

### 1. Initialize (first time only)

```bash
train init
```

This sets up your API keys for LLM features (optional — works offline too).

### 2. Train a model

```bash
train --data sales.csv --target revenue
```

That's it! TrainCLI will:
- Profile your data
- Clean it automatically (or ask for input)
- Detect if it's classification or regression
- Try multiple models via cross-validation
- Pick the best one
- Export everything to `./output/`

### 3. Use your model

```python
import pickle
import pandas as pd

with open("output/model.pkl", "rb") as f:
    model = pickle.load(f)

new_data = pd.DataFrame([{"feature1": 10, "feature2": "A"}])
prediction = model.predict(new_data)
```

Or run the generated `train.py` to retrain from scratch.

## Commands

| Command | Description |
|---------|-------------|
| `train --data <file> --target <col>` | Train a model on a CSV file |
| `train --dir <folder> --target <col>` | Train on all CSVs in a folder |
| `train --model <name>` | Use a specific model (e.g., `random_forest`) |
| `train --model ?` | Pick model interactively |
| `train --task classification` | Override problem type detection |
| `train --drop col1,col2` | Drop columns (e.g., to fix leakage) |
| `train --preview` | Profile data without training |
| `train --auto` | Skip all prompts (for CI/CD) |
| `train init` | Configure API keys |

## Examples

### Basic training
```bash
train --data customers.csv --target churn
```

### Force a specific model
```bash
train --data sales.csv --target price --model gradient_boosting
```

### Interactive model selection
```bash
train --data data.csv --target label --model ?
```

### Drop leaky columns
```bash
train --data jobs.csv --target salary --drop min_salary,max_salary
```

### Batch processing
```bash
train --dir ./datasets/ --target outcome --auto
```

### Preview mode
```bash
train --data data.csv --target col --preview
```

## Output Files

After training, you'll get:

- **model.pkl** — Trained scikit-learn pipeline (ready to use)
- **train.py** — Standalone script to retrain the model
- **report.md** — Human-readable summary with metrics
- **metrics.json** — Machine-readable metrics
- **session.json** — Full training session metadata

## Supported Models

TrainCLI includes:

**Classification:**
- Logistic Regression
- Random Forest
- Gradient Boosting (XGBoost)
- Support Vector Machine
- K-Nearest Neighbors

**Regression:**
- Linear Regression
- Ridge Regression
- Random Forest
- Gradient Boosting (XGBoost)
- Support Vector Regression

## LLM Features (Optional)

TrainCLI can use IBM watsonx.ai to:
- Explain model results in plain English
- Suggest improvements
- Generate educational comments in train.py

To enable:
```bash
train init
# Choose "watsonx" and enter your API key
```

Works offline if no API key is configured.

## Data Leakage Detection

TrainCLI automatically checks for:
- Features with >0.98 correlation to target
- Column names containing the target name
- Linear transformations of the target

Example warning:
```
⚠ Leakage suspected:
  → min_salary: correlation with target is 0.999 — suspiciously high
  
  Suggested fix: train --drop min_salary ...
```

## Requirements

- Python 3.9+
- pandas, scikit-learn, xgboost
- Optional: ibm-watsonx-ai (for LLM features)

## Development

```bash
git clone https://github.com/yourusername/traincli
cd traincli
pip install -e .
```

## License

MIT

## Contributing

Contributions welcome! Open an issue or PR.

## MCP Server (Claude Code Integration)

TrainCLI includes an MCP server that lets Claude Code train models directly:

### Setup

1. Install TrainCLI:
```bash
pip install traincli
```

2. Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):
```json
{
  "mcpServers": {
    "traincli": {
      "command": "traincli-mcp"
    }
  }
}
```

3. Restart Claude Desktop

### Available Tools

- **train_model** — Train a model on a CSV file
- **profile_dataset** — Profile data without training
- **suggest_target** — Suggest the best target column

### Example Usage in Claude

```
User: Train a model on sales.csv to predict revenue

Claude: [calls train_model tool]
✓ Model trained: Gradient Boosting
✓ R² = 0.847
✓ Files saved to ./output/
```

## Roadmap

- [ ] Meta-model for smarter algorithm selection
- [ ] More preprocessing options
- [ ] Feature engineering suggestions
- [ ] Hyperparameter tuning

---

**Made with ❤️ for developers who want ML without the boilerplate.**
