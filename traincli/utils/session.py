import json
from datetime import datetime
from pathlib import Path


class Session:
    """
    Tracks all decisions made during a TrainCLI run.
    Saved as session.json in the output directory.
    """

    def __init__(self, data_path: str, target: str):
        self.data = {
            "traincli_version": "0.1.0",
            "started_at": datetime.now().isoformat(),
            "input": {
                "data_path": str(data_path),
                "target": target,
            },
            "profile": {},
            "cleaning": {
                "auto_fixes": [],
                "user_decisions": [],
                "rows_dropped": 0,
                "cols_dropped": [],
            },
            "problem_type": None,
            "problem_source": None,  # "heuristic" or "llm"
            "model": {
                "key": None,
                "label": None,
                "source": None,  # "user", "auto", "llm"
            },
            "metrics": {},
            "output_files": [],
            "completed_at": None,
        }

    def set_profile(self, profile: dict):
        self.data["profile"] = profile

    def add_auto_fix(self, description: str):
        self.data["cleaning"]["auto_fixes"].append(description)

    def add_user_decision(self, issue: str, choice: str):
        self.data["cleaning"]["user_decisions"].append({
            "issue": issue,
            "choice": choice
        })

    def set_rows_dropped(self, n: int):
        self.data["cleaning"]["rows_dropped"] = n

    def add_col_dropped(self, col: str, reason: str):
        self.data["cleaning"]["cols_dropped"].append({
            "col": col,
            "reason": reason
        })

    def set_problem(self, problem_type: str, source: str):
        self.data["problem_type"] = problem_type
        self.data["problem_source"] = source

    def set_model(self, key: str, label: str, source: str):
        self.data["model"] = {"key": key, "label": label, "source": source}

    def set_metrics(self, metrics: dict):
        self.data["metrics"] = metrics

    def add_output_file(self, path: str):
        self.data["output_files"].append(path)

    def complete(self):
        self.data["completed_at"] = datetime.now().isoformat()

    def save(self, output_dir: Path):
        path = output_dir / "session.json"
        with open(path, "w") as f:
            json.dump(self.data, f, indent=2)
        return path