**User:**

<task>
ill say whats going wrong, california house one is calling wrong row name
</task>
<environment_details>
# VSCode Visible Files
scripts\fetch_sklearn_datasets.py

# VSCode Open Tabs
traincli/exporter.py,traincli/core.py,traincli/meta_collector.py,scripts/fetch_sklearn_datasets.py,traincli/mcp_server.py,traincli/trainer.py,.env.example,traincli/config.py,traincli/profiler.py,traincli/llm.py,traincli/cli.py,.env,pyproject.toml,README.md

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:21:33.869Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.00

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>


# Current Workspace Directory (d:/Ewan/traincli) Files
.env
.env.example
pyproject.toml
README.md
tourdata.csv
scripts/
scripts/fetch_sklearn_datasets.py
traincli/
traincli/cleaner.py
traincli/cli.py
traincli/config.py
traincli/core.py
traincli/detector.py
traincli/exporter.py
traincli/llm.py
traincli/mcp_server.py
traincli/meta_collector.py
traincli/profiler.py
traincli/trainer.py
traincli/models/
traincli/models/registry.py
traincli/utils/
traincli/utils/display.py
traincli/utils/session.py
traincli.egg-info/
traincli.egg-info/dependency_links.txt
traincli.egg-info/entry_points.txt
traincli.egg-info/PKG-INFO
traincli.egg-info/requires.txt
traincli.egg-info/SOURCES.txt
traincli.egg-info/top_level.txt
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

I'll help you fix the issue with the California housing dataset calling the wrong row name. Let me first examine the relevant files to understand the problem.

<read_file>
<args>
<file>
<path>scripts/fetch_sklearn_datasets.py</path>
</file>
<file>
<path>traincli/core.py</path>
</file>
<file>
<path>traincli/trainer.py</path>
</file>
</args>
</read_file>

---

**User:**

[read_file for 'scripts/fetch_sklearn_datasets.py', 'traincli/core.py', 'traincli/trainer.py'] Result:
<files>
<file><path>scripts/fetch_sklearn_datasets.py</path>
<content lines="1-256">
  1 | 
  2 | import subprocess
  3 | import os
  4 | import pandas as pd
  5 | import numpy as np
  6 | from pathlib import Path
  7 | 
  8 | # Output directory for temp CSVs
  9 | TEMP_DIR = Path("temp_meta_datasets")
 10 | TEMP_DIR.mkdir(exist_ok=True)
 11 | 
 12 | 
 13 | def save_and_train(df: pd.DataFrame, name: str, target: str):
 14 |     csv_path = TEMP_DIR / f"{name}.csv"
 15 |     df.to_csv(csv_path, index=False)
 16 |     print(f"\n{'─'*50}")
 17 |     print(f"Running: {name} → target: {target}")
 18 |     print(f"Shape: {df.shape}")
 19 | 
 20 |     result = subprocess.run([
 21 |         "train",
 22 |         "--data", str(csv_path),
 23 |         "--target", target,
 24 |         "--auto",
 25 |         "--meta",
 26 |         "--no-llm",  # skip LLM calls — saves API quota
 27 |         "--out", str(TEMP_DIR / f"output_{name}"),
 28 |     ], capture_output=False)
 29 | 
 30 |     if result.returncode != 0:
 31 |         print(f"⚠ Failed on {name}")
 32 |     else:
 33 |         print(f"✓ Done: {name}")
 34 | 
 35 | 
 36 | def main():
 37 |     from sklearn import datasets
 38 | 
 39 |     # ── CLASSIFICATION DATASETS ──────────────────────────────
 40 | 
 41 |     # 1. Iris — small, clean, multiclass
 42 |     data = datasets.load_iris(as_frame=True)
 43 |     df = data.frame
 44 |     df["target"] = data.target_names[data.target]
 45 |     save_and_train(df, "iris", "target")
 46 | 
 47 |     # 2. Wine — small, multiclass
 48 |     data = datasets.load_wine(as_frame=True)
 49 |     df = data.frame
 50 |     df["target"] = data.target_names[data.target]
 51 |     save_and_train(df, "wine", "target")
 52 | 
 53 |     # 3. Breast cancer — binary, medium
 54 |     data = datasets.load_breast_cancer(as_frame=True)
 55 |     df = data.frame
 56 |     df["target"] = data.target_names[data.target]
 57 |     save_and_train(df, "breast_cancer", "target")
 58 | 
 59 |     # 4. Digits — multiclass, larger
 60 |     data = datasets.load_digits(as_frame=True)
 61 |     df = data.frame
 62 |     save_and_train(df, "digits", "target")
 63 | 
 64 |     # 5. Synthetic binary — many features
 65 |     X, y = datasets.make_classification(
 66 |         n_samples=500, n_features=20, n_informative=10,
 67 |         n_redundant=5, random_state=42
 68 |     )
 69 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(20)])
 70 |     df["target"] = y
 71 |     save_and_train(df, "synth_classification_500", "target")
 72 | 
 73 |     # 6. Synthetic binary — small
 74 |     X, y = datasets.make_classification(
 75 |         n_samples=150, n_features=10, n_informative=5,
 76 |         random_state=7
 77 |     )
 78 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(10)])
 79 |     df["target"] = y
 80 |     save_and_train(df, "synth_classification_150", "target")
 81 | 
 82 |     # 7. Synthetic multiclass
 83 |     X, y = datasets.make_classification(
 84 |         n_samples=400, n_features=15, n_classes=4,
 85 |         n_informative=10, n_redundant=3, random_state=99
 86 |     )
 87 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(15)])
 88 |     df["target"] = y
 89 |     save_and_train(df, "synth_multiclass_400", "target")
 90 | 
 91 |     # 8. Make moons — non-linear boundary
 92 |     X, y = datasets.make_moons(n_samples=300, noise=0.2, random_state=42)
 93 |     df = pd.DataFrame(X, columns=["x1", "x2"])
 94 |     df["target"] = y
 95 |     save_and_train(df, "moons_300", "target")
 96 | 
 97 |     # 9. Make circles
 98 |     X, y = datasets.make_circles(n_samples=300, noise=0.1, random_state=42)
 99 |     df = pd.DataFrame(X, columns=["x1", "x2"])
100 |     df["target"] = y
101 |     save_and_train(df, "circles_300", "target")
102 | 
103 |     # ── REGRESSION DATASETS ───────────────────────────────────
104 | 
105 |     # 10. Diabetes — small regression
106 |     data = datasets.load_diabetes(as_frame=True)
107 |     df = data.frame
108 |     save_and_train(df, "diabetes", "target")
109 | 
110 |     # 11. California housing — large regression
111 |     try:
112 |         data = datasets.fetch_california_housing(as_frame=True)
113 |         df = data.frame.sample(500, random_state=42)  # sample to keep it fast
114 |         save_and_train(df, "california_housing_500", "median_house_value")
115 |     except Exception as e:
116 |         print(f"Skipping california housing: {e}")
117 | 
118 |     # 12. Synthetic regression — linear
119 |     X, y = datasets.make_regression(
120 |         n_samples=300, n_features=10, noise=10, random_state=42
121 |     )
122 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(10)])
123 |     df["target"] = y
124 |     save_and_train(df, "synth_regression_linear_300", "target")
125 | 
126 |     # 13. Synthetic regression — nonlinear (Friedman)
127 |     X, y = datasets.make_friedman1(n_samples=300, random_state=42)
128 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(10)])
129 |     df["target"] = y
130 |     save_and_train(df, "synth_regression_friedman_300", "target")
131 | 
132 |     # 14. Synthetic regression — large
133 |     X, y = datasets.make_regression(
134 |         n_samples=800, n_features=20, noise=20, random_state=99
135 |     )
136 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(20)])
137 |     df["target"] = y
138 |     save_and_train(df, "synth_regression_large_800", "target")
139 | 
140 |     # 15. Synthetic regression — small noisy
141 |     X, y = datasets.make_regression(
142 |         n_samples=100, n_features=5, noise=50, random_state=7
143 |     )
144 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(5)])
145 |     df["target"] = y
146 |     save_and_train(df, "synth_regression_small_100", "target")
147 | 
148 |     # ── ADDITIONAL CLASSIFICATION DATASETS ────────────────────
149 | 
150 |     # 16. Synthetic binary — high dimensional
151 |     X, y = datasets.make_classification(
152 |         n_samples=200, n_features=30, n_informative=15,
153 |         n_redundant=10, random_state=123
154 |     )
155 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(30)])
156 |     df["target"] = y
157 |     save_and_train(df, "synth_classification_highdim_200", "target")
158 | 
159 |     # 17. Synthetic binary — imbalanced
160 |     X, y = datasets.make_classification(
161 |         n_samples=300, n_features=10, n_informative=5,
162 |         weights=[0.9, 0.1], random_state=456
163 |     )
164 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(10)])
165 |     df["target"] = y
166 |     save_and_train(df, "synth_classification_imbalanced_300", "target")
167 | 
168 |     # 18. Synthetic multiclass — 5 classes
169 |     X, y = datasets.make_classification(
170 |         n_samples=500, n_features=12, n_classes=5,
171 |         n_informative=8, random_state=789
172 |     )
173 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(12)])
174 |     df["target"] = y
175 |     save_and_train(df, "synth_multiclass_5class_500", "target")
176 | 
177 |     # 19. Synthetic binary — very small
178 |     X, y = datasets.make_classification(
179 |         n_samples=50, n_features=5, n_informative=3,
180 |         random_state=111
181 |     )
182 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(5)])
183 |     df["target"] = y
184 |     save_and_train(df, "synth_classification_tiny_50", "target")
185 | 
186 |     # 20. Synthetic binary — large
187 |     X, y = datasets.make_classification(
188 |         n_samples=1000, n_features=15, n_informative=10,
189 |         random_state=222
190 |     )
191 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(15)])
192 |     df["target"] = y
193 |     save_and_train(df, "synth_classification_large_1000", "target")
194 | 
195 |     # 21-25. More moons/circles variations
196 |     for i, (noise, seed) in enumerate([(0.1, 333), (0.3, 444), (0.15, 555), (0.25, 666), (0.05, 777)], start=21):
197 |         X, y = datasets.make_moons(n_samples=250, noise=noise, random_state=seed)
198 |         df = pd.DataFrame(X, columns=["x1", "x2"])
199 |         df["target"] = y
200 |         save_and_train(df, f"moons_var{i-20}_250", "target")
201 | 
202 |     # 26-30. More circles variations
203 |     for i, (noise, seed) in enumerate([(0.05, 888), (0.15, 999), (0.2, 1111), (0.08, 1222), (0.12, 1333)], start=26):
204 |         X, y = datasets.make_circles(n_samples=250, noise=noise, random_state=seed)
205 |         df = pd.DataFrame(X, columns=["x1", "x2"])
206 |         df["target"] = y
207 |         save_and_train(df, f"circles_var{i-25}_250", "target")
208 | 
209 |     # ── ADDITIONAL REGRESSION DATASETS ────────────────────────
210 | 
211 |     # 31. Synthetic regression — medium noise
212 |     X, y = datasets.make_regression(
213 |         n_samples=400, n_features=15, noise=30, random_state=1444
214 |     )
215 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(15)])
216 |     df["target"] = y
217 |     save_and_train(df, "synth_regression_medium_400", "target")
218 | 
219 |     # 32. Synthetic regression — low noise
220 |     X, y = datasets.make_regression(
221 |         n_samples=200, n_features=8, noise=5, random_state=1555
222 |     )
223 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(8)])
224 |     df["target"] = y
225 |     save_and_train(df, "synth_regression_lownoise_200", "target")
226 | 
227 |     # 33. Friedman #2
228 |     X, y = datasets.make_friedman2(n_samples=300, random_state=1666)
229 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(4)])
230 |     df["target"] = y
231 |     save_and_train(df, "synth_regression_friedman2_300", "target")
232 | 
233 |     # 34. Friedman #3
234 |     X, y = datasets.make_friedman3(n_samples=300, random_state=1777)
235 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(4)])
236 |     df["target"] = y
237 |     save_and_train(df, "synth_regression_friedman3_300", "target")
238 | 
239 |     # 35. Synthetic regression — high dimensional
240 |     X, y = datasets.make_regression(
241 |         n_samples=600, n_features=25, noise=15, random_state=1888
242 |     )
243 |     df = pd.DataFrame(X, columns=[f"f{i}" for i in range(25)])
244 |     df["target"] = y
245 |     save_and_train(df, "synth_regression_highdim_600", "target")
246 | 
247 |     print(f"\n{'═'*50}")
248 |     print("✓ All datasets processed")
249 |     print(f"Meta dataset should now have 35 rows")
250 |     print(f"Check: ~/.traincli/meta_dataset.csv")
251 |     print(f"\nNext step:")
252 |     print(f"  train --data ~/.traincli/meta_dataset.csv --target best_model --auto")
253 | 
254 | 
255 | if __name__ == "__main__":
256 |     main()
</content>
</file>
<file><path>traincli/core.py</path>
<content lines="1-196">
  1 | """
  2 | Core pipeline logic — used by both CLI and MCP server.
  3 | """
  4 | import pandas as pd
  5 | from pathlib import Path
  6 | from traincli.utils.session import Session
  7 | from traincli.profiler import profile
  8 | from traincli.cleaner import clean
  9 | from traincli.detector import detect
 10 | from traincli.trainer import train
 11 | from traincli.exporter import export
 12 | 
 13 | 
 14 | def run_pipeline(
 15 |     data_path: str,
 16 |     target: str,
 17 |     model_key: str = None,
 18 |     task: str = None,
 19 |     out: str = "./output",
 20 |     auto: bool = True,
 21 |     drop: str = None,
 22 | ) -> dict:
 23 |     """
 24 |     Core ML pipeline — loads data, profiles, cleans, trains, exports.
 25 |     
 26 |     Args:
 27 |         data_path: Path to CSV file
 28 |         target: Target column name
 29 |         model_key: Model to use (None = auto-select)
 30 |         task: Problem type override ("classification" or "regression")
 31 |         out: Output directory
 32 |         auto: Skip interactive prompts
 33 |         drop: Comma-separated columns to drop
 34 |     
 35 |     Returns:
 36 |         dict with keys: results, df_clean, profile, output_dir
 37 |     """
 38 |     # Load
 39 |     path = Path(data_path)
 40 |     if not path.exists():
 41 |         raise FileNotFoundError(f"File not found: {data_path}")
 42 |     
 43 |     try:
 44 |         df = pd.read_csv(path)
 45 |     except Exception as e:
 46 |         raise ValueError(f"Could not read CSV: {e}")
 47 |     
 48 |     if target not in df.columns:
 49 |         raise ValueError(f"Target '{target}' not found. Available: {list(df.columns)}")
 50 |     
 51 |     session = Session(data_path, target)
 52 |     
 53 |     # Profile
 54 |     prof = profile(df, target)
 55 |     session.set_profile({
 56 |         "rows": prof["rows"],
 57 |         "cols": prof["cols"],
 58 |         "null_pct": prof["null_pct"],
 59 |         "issues_found": len(prof["issues"]),
 60 |     })
 61 |     
 62 |     # Drop columns if requested
 63 |     if drop:
 64 |         cols_to_drop = [c.strip() for c in drop.split(",")]
 65 |         cols_to_drop = [c for c in cols_to_drop if c in df.columns and c != target]
 66 |         if cols_to_drop:
 67 |             df = df.drop(columns=cols_to_drop)
 68 |     
 69 |     # Clean
 70 |     df_clean = clean(df, prof, session, auto=auto)
 71 |     
 72 |     # Detect problem type
 73 |     if task:
 74 |         session.set_problem(task, "user_flag")
 75 |         problem_type = task
 76 |     else:
 77 |         problem_type = detect(df_clean, target, session)
 78 |     
 79 |     # Train
 80 |     results = train(
 81 |         df=df_clean,
 82 |         target=target,
 83 |         problem_type=problem_type,
 84 |         session=session,
 85 |         model_key=model_key,
 86 |         interactive=not auto,
 87 |         profile=prof,
 88 |     )
 89 |     
 90 |     # Export
 91 |     output_dir = Path(out)
 92 |     export(results, df_clean, target, data_path, output_dir, session)
 93 |     
 94 |     return {
 95 |         "results": results,
 96 |         "df_clean": df_clean,
 97 |         "profile": prof,
 98 |         "output_dir": str(output_dir.resolve()),
 99 |         "session": session,
100 |     }
101 | 
102 | 
103 | def profile_dataset(data_path: str, target: str = None) -> dict:
104 |     """
105 |     Profile a dataset without training.
106 |     
107 |     Args:
108 |         data_path: Path to CSV file
109 |         target: Optional target column (for leakage detection)
110 |     
111 |     Returns:
112 |         Profile dict with dataset statistics
113 |     """
114 |     path = Path(data_path)
115 |     if not path.exists():
116 |         raise FileNotFoundError(f"File not found: {data_path}")
117 |     
118 |     try:
119 |         df = pd.read_csv(path)
120 |     except Exception as e:
121 |         raise ValueError(f"Could not read CSV: {e}")
122 |     
123 |     # If no target specified, use first column
124 |     if not target:
125 |         target = df.columns[0]
126 |     
127 |     if target not in df.columns:
128 |         raise ValueError(f"Target '{target}' not found. Available: {list(df.columns)}")
129 |     
130 |     prof = profile(df, target)
131 |     return prof
132 | 
133 | 
134 | def suggest_target(data_path: str) -> dict:
135 |     """
136 |     Suggest the best target column for a dataset.
137 |     
138 |     Args:
139 |         data_path: Path to CSV file
140 |     
141 |     Returns:
142 |         dict with suggested target and reasoning
143 |     """
144 |     path = Path(data_path)
145 |     if not path.exists():
146 |         raise FileNotFoundError(f"File not found: {data_path}")
147 |     
148 |     try:
149 |         df = pd.read_csv(path)
150 |     except Exception as e:
151 |         raise ValueError(f"Could not read CSV: {e}")
152 |     
153 |     # Heuristics for target selection:
154 |     # 1. Column named "target", "label", "y", "outcome"
155 |     # 2. Last column (common convention)
156 |     # 3. Column with moderate cardinality (not ID, not free text)
157 |     
158 |     target_keywords = ["target", "label", "y", "outcome", "class", "prediction"]
159 |     
160 |     for col in df.columns:
161 |         if col.lower() in target_keywords:
162 |             return {
163 |                 "suggested_target": col,
164 |                 "reason": f"Column name '{col}' suggests it's the target",
165 |                 "confidence": "high"
166 |             }
167 |     
168 |     # Check last column
169 |     last_col = df.columns[-1]
170 |     nunique = df[last_col].nunique()
171 |     total = len(df)
172 |     
173 |     if 2 <= nunique <= total * 0.5:
174 |         return {
175 |             "suggested_target": last_col,
176 |             "reason": f"Last column with {nunique} unique values (common convention)",
177 |             "confidence": "medium"
178 |         }
179 |     
180 |     # Fallback: find column with reasonable cardinality
181 |     for col in df.columns:
182 |         nunique = df[col].nunique()
183 |         if 2 <= nunique <= total * 0.5:
184 |             return {
185 |                 "suggested_target": col,
186 |                 "reason": f"Column has {nunique} unique values (suitable for prediction)",
187 |                 "confidence": "low"
188 |             }
189 |     
190 |     return {
191 |         "suggested_target": df.columns[-1],
192 |         "reason": "No clear target found — defaulting to last column",
193 |         "confidence": "very_low"
194 |     }
195 | 
196 | # Made with Bob
</content>
</file>
<file><path>traincli/trainer.py</path>
<content lines="1-365">
  1 | import pandas as pd
  2 | import numpy as np
  3 | import pickle
  4 | from pathlib import Path
  5 | from sklearn.model_selection import train_test_split, cross_val_score
  6 | from sklearn.pipeline import Pipeline
  7 | from sklearn.impute import SimpleImputer
  8 | from sklearn.preprocessing import StandardScaler, LabelEncoder
  9 | from sklearn.metrics import (
 10 |     accuracy_score, classification_report,
 11 |     r2_score, mean_absolute_error, mean_squared_error
 12 | )
 13 | from traincli.utils.display import header, success, info, warn, blank, metrics_table, model_picker_table
 14 | from traincli.utils.session import Session
 15 | from traincli.models.registry import get_model, get_default, REGISTRY
 16 | 
 17 | 
 18 | def select_model_interactive(problem_type: str) -> dict:
 19 |     """Show the interactive model picker and return selected model entry."""
 20 |     import click
 21 |     from rich.console import Console
 22 |     console = Console()
 23 | 
 24 |     models = REGISTRY[problem_type]
 25 |     default = get_default(problem_type)
 26 | 
 27 |     blank()
 28 |     console.print(f"[bold]Available models for {problem_type}:[/bold]")
 29 |     blank()
 30 |     model_picker_table(models, default["key"])
 31 | 
 32 |     choice = click.prompt(
 33 |         f"  Pick a model [1-{len(models)}] or press Enter for recommended",
 34 |         default="",
 35 |         show_default=False,
 36 |     )
 37 | 
 38 |     if choice.strip() == "":
 39 |         return default
 40 | 
 41 |     try:
 42 |         idx = int(choice.strip()) - 1
 43 |         if 0 <= idx < len(models):
 44 |             return models[idx]
 45 |     except ValueError:
 46 |         pass
 47 | 
 48 |     warn("Invalid choice — using recommended model")
 49 |     return default
 50 | 
 51 | 
 52 | def train(
 53 |     df: pd.DataFrame,
 54 |     target: str,
 55 |     problem_type: str,
 56 |     session: Session,
 57 |     model_key: str = None,
 58 |     interactive: bool = True,
 59 |     profile: dict = None,
 60 | ) -> dict:
 61 |     """
 62 |     Build pipeline, train model, evaluate, return results dict.
 63 |     """
 64 |     from rich.console import Console
 65 |     console = Console()
 66 | 
 67 |     header("Training")
 68 | 
 69 |     # ── FEATURES & TARGET ────────────────────────────────────
 70 |     X = df.drop(columns=[target])
 71 |     y = df[target].copy()
 72 | 
 73 |     # Encode categorical features
 74 |     label_encoders = {}
 75 |     for col in X.select_dtypes(include="object").columns:
 76 |         le = LabelEncoder()
 77 |         X[col] = le.fit_transform(X[col].astype(str))
 78 |         label_encoders[col] = le
 79 | 
 80 |     # Encode target if classification and object dtype
 81 |     target_encoder = None
 82 |     if problem_type == "classification" and y.dtype == object:
 83 |         le = LabelEncoder()
 84 |         y = pd.Series(le.fit_transform(y), name=target)
 85 |         target_encoder = le
 86 | 
 87 |     # ── MODEL SELECTION ──────────────────────────────────────
 88 |     model_entry = None
 89 | 
 90 |     if model_key == "?":
 91 |         if not interactive:
 92 |             model_entry = get_default(problem_type)
 93 |             session.set_model(model_entry["key"], model_entry["label"], "auto_default")
 94 |         else:
 95 |             model_entry = select_model_interactive(problem_type)
 96 |             session.set_model(model_entry["key"], model_entry["label"], "user_interactive")
 97 | 
 98 |     elif model_key is not None:
 99 |         model_entry = get_model(problem_type, model_key)
100 | 
101 |         if model_entry is None:
102 |             # Check wrong problem type
103 |             other = "classification" if problem_type == "regression" else "regression"
104 |             wrong_entry = get_model(other, model_key)
105 |             if wrong_entry:
106 |                 warn(f"'{model_key}' is a {other} model but your problem is {problem_type}.")
107 |                 if interactive:
108 |                     import click
109 |                     proceed = click.confirm("  Proceed anyway?", default=False)
110 |                     if not proceed:
111 |                         model_entry = get_default(problem_type)
112 |                         warn(f"Using recommended: {model_entry['label']}")
113 |                     else:
114 |                         model_entry = wrong_entry
115 |                 else:
116 |                     model_entry = get_default(problem_type)
117 |             else:
118 |                 warn(f"Unknown model '{model_key}' — using recommended default")
119 |                 model_entry = get_default(problem_type)
120 | 
121 |         session.set_model(model_entry["key"], model_entry["label"], "user_flag")
122 | 
123 |     else:
124 |         info("No model specified — running candidates and picking best...")
125 |         model_entry = _auto_select(X, y, problem_type, session)
126 | 
127 |     info(f"Model: [bold]{model_entry['label']}[/bold]")
128 | 
129 |     # ── PIPELINE ─────────────────────────────────────────────
130 |     pipeline = Pipeline([
131 |         ("imputer", SimpleImputer(strategy="median")),
132 |         ("scaler", StandardScaler()),
133 |         ("model", model_entry["class"](**model_entry["params"])),
134 |     ])
135 | 
136 |     # ── TRAIN / TEST SPLIT ───────────────────────────────────
137 |     try:
138 |         stratify = y if problem_type == "classification" else None
139 |         X_train, X_test, y_train, y_test = train_test_split(
140 |             X, y, test_size=0.2, random_state=42, stratify=stratify
141 |         )
142 |     except ValueError:
143 |         # Stratify can fail if some classes have < 2 samples
144 |         X_train, X_test, y_train, y_test = train_test_split(
145 |             X, y, test_size=0.2, random_state=42
146 |         )
147 | 
148 |     # ── CROSS VALIDATION ─────────────────────────────────────
149 |     info("Running 3-fold cross-validation...")
150 |     try:
151 |         cv_scores = cross_val_score(pipeline, X_train, y_train, cv=3)
152 |     except Exception as e:
153 |         warn(f"CV failed ({e}) — skipping")
154 |         cv_scores = np.array([0.0, 0.0, 0.0])
155 | 
156 |     info(f"CV score: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
157 | 
158 |     # ── FIT ───────────────────────────────────────────────────
159 |     pipeline.fit(X_train, y_train)
160 |     y_pred = pipeline.predict(X_test)
161 | 
162 |     # ── METRICS ──────────────────────────────────────────────
163 |     blank()
164 |     header("Evaluation")
165 | 
166 |     if problem_type == "classification":
167 |         metrics = {
168 |             "Accuracy": f"{accuracy_score(y_test, y_pred):.4f}",
169 |             "CV Mean":  f"{cv_scores.mean():.4f}",
170 |             "CV Std":   f"{cv_scores.std():.4f}",
171 |         }
172 |     else:
173 |         metrics = {
174 |             "R²":      f"{r2_score(y_test, y_pred):.4f}",
175 |             "MAE":     f"{mean_absolute_error(y_test, y_pred):.4f}",
176 |             "RMSE":    f"{np.sqrt(mean_squared_error(y_test, y_pred)):.4f}",
177 |             "CV Mean": f"{cv_scores.mean():.4f}",
178 |             "CV Std":  f"{cv_scores.std():.4f}",
179 |         }
180 | 
181 |     metrics_table(metrics, problem_type)
182 |     session.set_metrics(metrics)
183 | 
184 |     # ── CONFIDENCE ───────────────────────────────────────────
185 |     confidence, reasons = _confidence(df, cv_scores, problem_type, y)
186 |     blank()
187 |     _print_confidence(confidence, reasons, console)
188 | 
189 |     # ── LLM INTERPRETATION ───────────────────────────────────
190 |     interpretation = None
191 |     try:
192 |         from traincli.llm import interpret_results
193 |         interpretation = interpret_results(
194 |             metrics=metrics,
195 |             problem_type=problem_type,
196 |             model_label=model_entry["label"],
197 |             confidence=confidence,
198 |             confidence_reasons=reasons,
199 |             feature_names=list(X.columns),
200 |             profile=profile or {"rows": len(df)},
201 |         )
202 |         if interpretation:
203 |             blank()
204 |             console.print("[bold dim]── Interpretation[/bold dim]")
205 |             console.print(f"[dim]{interpretation}[/dim]")
206 |     except Exception:
207 |         pass  # LLM is optional — never break the pipeline
208 | 
209 |     return {
210 |         "pipeline":           pipeline,
211 |         "model_entry":        model_entry,
212 |         "metrics":            metrics,
213 |         "cv_scores":          cv_scores,
214 |         "confidence":         confidence,
215 |         "confidence_reasons": reasons,
216 |         "interpretation":     interpretation,
217 |         "feature_names":      list(X.columns),
218 |         "label_encoders":     label_encoders,
219 |         "target_encoder":     target_encoder,
220 |         "problem_type":       problem_type,
221 |         "X_train":            X_train,
222 |     }
223 | 
224 | 
225 | def improve(model_path: str, new_data_path: str, target: str, session: Session) -> dict:
226 |     """
227 |     Load an existing model, retrain on new data, compare metrics.
228 |     """
229 |     header("Improve mode")
230 | 
231 |     # Load existing model
232 |     path = Path(model_path)
233 |     if not path.exists():
234 |         raise FileNotFoundError(f"Model not found: {model_path}")
235 | 
236 |     with open(path, "rb") as f:
237 |         old_pipeline = pickle.load(f)
238 | 
239 |     info(f"Loaded existing model from {model_path}")
240 | 
241 |     # Load new data
242 |     df_new = pd.read_csv(new_data_path)
243 |     if target not in df_new.columns:
244 |         raise ValueError(f"Target '{target}' not found in new data")
245 | 
246 |     info(f"New data: {len(df_new):,} rows")
247 | 
248 |     X_new = df_new.drop(columns=[target])
249 |     y_new = df_new[target]
250 | 
251 |     # Encode categoricals
252 |     for col in X_new.select_dtypes(include="object").columns:
253 |         le = LabelEncoder()
254 |         X_new[col] = le.fit_transform(X_new[col].astype(str))
255 | 
256 |     if y_new.dtype == object:
257 |         le = LabelEncoder()
258 |         y_new = pd.Series(le.fit_transform(y_new))
259 | 
260 |     X_train, X_test, y_train, y_test = train_test_split(
261 |         X_new, y_new, test_size=0.2, random_state=42
262 |     )
263 | 
264 |     # Score old model on new data
265 |     try:
266 |         old_score = old_pipeline.score(X_test, y_test)
267 |         info(f"Old model score on new data: {old_score:.4f}")
268 |     except Exception:
269 |         old_score = None
270 |         warn("Could not score old model on new data — feature mismatch likely")
271 | 
272 |     # Retrain
273 |     info("Retraining on new data...")
274 |     old_pipeline.fit(X_train, y_train)
275 |     new_score = old_pipeline.score(X_test, y_test)
276 |     info(f"New model score after retraining: {new_score:.4f}")
277 | 
278 |     if old_score is not None:
279 |         delta = new_score - old_score
280 |         color = "green" if delta >= 0 else "red"
281 |         from rich.console import Console
282 |         Console().print(f"  Change: [{color}]{delta:+.4f}[/{color}]")
283 | 
284 |     session.set_metrics({
285 |         "score_before": f"{old_score:.4f}" if old_score else "N/A",
286 |         "score_after":  f"{new_score:.4f}",
287 |     })
288 | 
289 |     return {
290 |         "pipeline":     old_pipeline,
291 |         "score_before": old_score,
292 |         "score_after":  new_score,
293 |     }
294 | 
295 | 
296 | # ── INTERNAL HELPERS ─────────────────────────────────────────
297 | 
298 | def _auto_select(X, y, problem_type: str, session: Session) -> dict:
299 |     """Run top 3 candidates, return the one with best CV score."""
300 |     candidates_keys = ["random_forest", "gradient_boosting", "xgboost"]
301 |     best_score = -np.inf
302 |     best_entry = None
303 | 
304 |     for key in candidates_keys:
305 |         entry = get_model(problem_type, key)
306 |         if entry is None:
307 |             continue
308 |         pipeline = Pipeline([
309 |             ("imputer", SimpleImputer(strategy="median")),
310 |             ("scaler", StandardScaler()),
311 |             ("model", entry["class"](**entry["params"])),
312 |         ])
313 |         try:
314 |             scores = cross_val_score(pipeline, X, y, cv=3)
315 |             mean = scores.mean()
316 |             info(f"  {entry['label']}: CV={mean:.3f}")
317 |             if mean > best_score:
318 |                 best_score = mean
319 |                 best_entry = entry
320 |         except Exception as e:
321 |             warn(f"  {entry['label']}: failed ({e})")
322 | 
323 |     if best_entry is None:
324 |         best_entry = get_default(problem_type)
325 | 
326 |     session.set_model(best_entry["key"], best_entry["label"], "auto_cv")
327 |     success(f"Selected: {best_entry['label']} (CV={best_score:.3f})")
328 |     return best_entry
329 | 
330 | 
331 | def _confidence(df, cv_scores, problem_type, y) -> tuple:
332 |     reasons = []
333 |     score = 3
334 | 
335 |     if len(df) < 500:
336 |         score -= 1
337 |         reasons.append(f"Small dataset ({len(df):,} rows) — predictions may not generalize well")
338 | 
339 |     if cv_scores.std() > 0.05:
340 |         score -= 1
341 |         reasons.append(f"High variance across CV folds (±{cv_scores.std():.3f}) — model is sensitive to data splits")
342 | 
343 |     if problem_type == "classification":
344 |         try:
345 |             class_balance = pd.Series(y).value_counts(normalize=True)
346 |             if class_balance.min() < 0.15:
347 |                 score -= 1
348 |                 reasons.append(f"Class imbalance detected (minority: {class_balance.min():.0%}) — model may underperform on rare class")
349 |         except Exception:
350 |             pass
351 | 
352 |     if score >= 3:
353 |         return "High", reasons
354 |     elif score == 2:
355 |         return "Medium", reasons
356 |     else:
357 |         return "Low", reasons
358 | 
359 | 
360 | def _print_confidence(confidence: str, reasons: list, console):
361 |     colors = {"High": "green", "Medium": "yellow", "Low": "red"}
362 |     color = colors.get(confidence, "white")
363 |     console.print(f"Confidence: [bold {color}]{confidence}[/bold {color}]")
364 |     for r in reasons:
365 |         console.print(f"  [dim]→[/dim] {r}")
</content>
</file>
</files>
<environment_details>
# VSCode Visible Files
scripts\fetch_sklearn_datasets.py

# VSCode Open Tabs
traincli/exporter.py,traincli/core.py,traincli/meta_collector.py,scripts/fetch_sklearn_datasets.py,traincli/mcp_server.py,traincli/trainer.py,.env.example,traincli/config.py,traincli/profiler.py,traincli/llm.py,traincli/cli.py,.env,pyproject.toml,README.md

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:21:40.563Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.01

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

I can see the issue! In the `fetch_sklearn_datasets.py` script on line 114, the California housing dataset is using `"median_house_value"` as the target column name, but the actual column name in the sklearn dataset is `"MedHouseVal"` (or similar).

Let me check what the actual column name is by looking at the sklearn documentation pattern:

<search_files>
<path>scripts</path>
<regex>california.*target|MedHouseVal|median_house</regex>
</search_files>

